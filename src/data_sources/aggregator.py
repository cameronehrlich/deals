"""
Data aggregator that combines multiple data sources.

Provides unified interface for:
- Market data (Redfin + FRED + HUD)
- Rent estimates (RentCast + HUD FMR fallback)
- Property import (URL parser + rent enrichment)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.models.property import Property
from src.models.market import Market, MarketTrend
from src.models.deal import Deal
from src.data_sources.redfin import RedfinDataCenter, RedfinMarketData
from src.data_sources.fred import FredClient
from src.data_sources.hud_fmr import HudFmrLoader
from src.data_sources.rentcast import RentCastClient
from src.data_sources.url_parser import PropertyUrlParser, parse_property_url
from src.data_sources.bls import BLSClient


@dataclass
class EnrichedMarketData:
    """Market data enriched from multiple sources."""

    market_id: str
    name: str
    state: str

    # From Redfin
    median_sale_price: Optional[float] = None
    median_list_price: Optional[float] = None
    price_per_sqft: Optional[float] = None
    price_change_yoy: Optional[float] = None
    homes_sold: Optional[int] = None
    inventory: Optional[int] = None
    months_of_supply: Optional[float] = None
    days_on_market: Optional[int] = None
    sale_to_list_ratio: Optional[float] = None

    # From FRED
    mortgage_rate_30yr: Optional[float] = None
    mortgage_rate_15yr: Optional[float] = None
    unemployment_rate: Optional[float] = None

    # From BLS
    job_growth_yoy: Optional[float] = None
    metro_unemployment_rate: Optional[float] = None

    # From HUD
    fmr_1br: Optional[int] = None
    fmr_2br: Optional[int] = None
    fmr_3br: Optional[int] = None

    # Calculated
    rent_to_price_ratio: Optional[float] = None
    cap_rate_estimate: Optional[float] = None

    # Metadata
    data_sources: list[str] = None
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = []

    def to_market(self) -> Market:
        """Convert to Market model."""
        # Calculate rent-to-price ratio
        if self.fmr_2br and self.median_sale_price:
            rent_to_price = (self.fmr_2br / self.median_sale_price) * 100
        else:
            rent_to_price = None

        # Determine trends
        price_trend = MarketTrend.STABLE
        if self.price_change_yoy:
            if self.price_change_yoy > 5:
                price_trend = MarketTrend.STRONG_GROWTH
            elif self.price_change_yoy > 0:
                price_trend = MarketTrend.MODERATE_GROWTH
            elif self.price_change_yoy < -5:
                price_trend = MarketTrend.STRONG_DECLINE
            elif self.price_change_yoy < 0:
                price_trend = MarketTrend.MODERATE_DECLINE

        return Market(
            id=self.market_id,
            name=self.name,
            metro=self.name,
            state=self.state,
            median_home_price=self.median_sale_price,
            median_price_per_sqft=self.price_per_sqft,
            price_change_1yr=self.price_change_yoy,
            median_rent=self.fmr_2br,
            avg_rent_to_price=rent_to_price,
            months_of_inventory=self.months_of_supply,
            days_on_market_avg=self.days_on_market,
            # Prefer metro-specific unemployment from BLS over national from FRED
            unemployment_rate=(
                self.metro_unemployment_rate / 100 if self.metro_unemployment_rate
                else self.unemployment_rate / 100 if self.unemployment_rate
                else None
            ),
            job_growth_1yr=self.job_growth_yoy,
            price_trend=price_trend,
            landlord_friendly=True,  # Would need additional data source
            data_sources=self.data_sources,
            last_updated=self.last_updated or datetime.utcnow(),
        )


class DataAggregator:
    """
    Aggregates data from multiple sources.

    Usage:
        aggregator = DataAggregator()

        # Get enriched market data
        market = await aggregator.get_market_data("Indianapolis", "IN")

        # Import property from URL
        deal = await aggregator.import_from_url("https://zillow.com/...")

        # Get rent estimate
        rent = await aggregator.get_rent_estimate(
            address="123 Main St",
            city="Indianapolis",
            state="IN",
            zip_code="46201",
            bedrooms=3,
        )
    """

    def __init__(
        self,
        fred_api_key: Optional[str] = None,
        rentcast_api_key: Optional[str] = None,
        bls_api_key: Optional[str] = None,
    ):
        self.redfin = RedfinDataCenter()
        self.fred = FredClient(api_key=fred_api_key)
        self.hud = HudFmrLoader()
        self.rentcast = RentCastClient(api_key=rentcast_api_key)
        self.url_parser = PropertyUrlParser()
        self.bls = BLSClient(api_key=bls_api_key)

    async def close(self):
        """Close all clients."""
        await self.redfin.close()
        await self.fred.close()
        await self.hud.close()
        await self.rentcast.close()
        await self.url_parser.close()
        await self.bls.close()

    async def get_market_data(self, city: str, state: str) -> Optional[EnrichedMarketData]:
        """
        Get enriched market data from all sources.

        Combines:
        - Redfin: Prices, inventory, days on market
        - FRED: Mortgage rates, unemployment
        - HUD: Fair market rents
        """
        market_id = f"{city.lower().replace(' ', '_')}_{state.lower()}"
        data_sources = []

        # Initialize result
        result = EnrichedMarketData(
            market_id=market_id,
            name=city,
            state=state,
            last_updated=datetime.utcnow(),
        )

        # Get Redfin data
        try:
            redfin_data = await self.redfin.get_metro_data(f"{city}, {state}")
            if redfin_data:
                result.median_sale_price = redfin_data.median_sale_price
                result.median_list_price = redfin_data.median_list_price
                result.price_per_sqft = redfin_data.median_ppsf
                result.price_change_yoy = (
                    redfin_data.median_sale_price_yoy * 100
                    if redfin_data.median_sale_price_yoy else None
                )
                result.homes_sold = redfin_data.homes_sold
                result.inventory = redfin_data.inventory
                result.months_of_supply = redfin_data.months_of_supply
                result.days_on_market = redfin_data.median_dom
                result.sale_to_list_ratio = redfin_data.avg_sale_to_list
                data_sources.append("redfin")
        except Exception as e:
            print(f"Redfin data fetch failed: {e}")

        # Get FRED data
        try:
            macro = await self.fred.get_macro_summary()
            result.mortgage_rate_30yr = macro.get("mortgage_30yr")
            result.mortgage_rate_15yr = macro.get("mortgage_15yr")
            result.unemployment_rate = macro.get("unemployment")
            data_sources.append("fred")
        except Exception as e:
            print(f"FRED data fetch failed: {e}")

        # Get HUD FMR data
        try:
            fmr = self.hud.get_fmr(market_id)
            if not fmr:
                fmr = await self.hud.lookup_fmr(state=state, city=city)

            if fmr:
                result.fmr_1br = fmr.fmr_1br
                result.fmr_2br = fmr.fmr_2br
                result.fmr_3br = fmr.fmr_3br
                data_sources.append("hud")
        except Exception as e:
            print(f"HUD FMR fetch failed: {e}")

        # Get BLS employment data
        try:
            bls_data = await self.bls.get_metro_employment(market_id)
            if bls_data:
                result.job_growth_yoy = bls_data.employment_growth
                result.metro_unemployment_rate = bls_data.unemployment_rate
                data_sources.append("bls")
        except Exception as e:
            print(f"BLS data fetch failed: {e}")

        # Calculate derived metrics
        if result.fmr_2br and result.median_sale_price:
            result.rent_to_price_ratio = (result.fmr_2br / result.median_sale_price) * 100

            # Rough cap rate estimate (NOI / price)
            annual_rent = result.fmr_2br * 12
            expenses = annual_rent * 0.45  # ~45% expense ratio
            noi = annual_rent - expenses
            result.cap_rate_estimate = (noi / result.median_sale_price) * 100

        result.data_sources = data_sources
        return result

    async def get_rent_estimate(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        bedrooms: int = 3,
        bathrooms: float = 2,
        sqft: Optional[int] = None,
    ) -> Optional[float]:
        """
        Get rent estimate using RentCast with HUD fallback.

        Returns the estimated monthly rent.
        """
        # Try RentCast first
        estimate = await self.rentcast.get_rent_estimate(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            sqft=sqft,
        )

        if estimate:
            return estimate.rent_estimate

        # Fallback to HUD
        market_id = f"{city.lower().replace(' ', '_')}_{state.lower()}"
        return self.hud.get_rent_estimate(market_id, bedrooms)

    async def import_from_url(self, url: str) -> Optional[Deal]:
        """
        Import a property from a listing URL and create a Deal.

        Steps:
        1. Parse the URL to extract property data
        2. Enrich with rent estimate
        3. Get market data
        4. Create and analyze Deal
        """
        from src.models.deal import Deal

        # Parse URL
        parsed = await self.url_parser.parse_url(url)
        if not parsed:
            raise ValueError(f"Could not parse URL: {url}")

        # Convert to Property
        property = parsed.to_property()

        # Enrich with rent estimate if not available
        if not property.estimated_rent:
            rent = await self.get_rent_estimate(
                address=property.address,
                city=property.city,
                state=property.state,
                zip_code=property.zip_code,
                bedrooms=property.bedrooms,
                bathrooms=property.bathrooms,
                sqft=property.sqft,
            )
            if rent:
                property.estimated_rent = rent

        # Get market data
        market_data = await self.get_market_data(property.city, property.state)
        market = market_data.to_market() if market_data else None

        # Create and analyze deal
        deal = Deal(
            id=f"imported_{property.id}",
            property=property,
            market=market,
        )

        # Run analysis
        deal.analyze()

        return deal

    async def enrich_property(self, property: Property) -> Property:
        """
        Enrich a property with additional data.

        - Adds rent estimate if missing
        - Updates with current market context
        """
        # Add rent estimate
        if not property.estimated_rent:
            rent = await self.get_rent_estimate(
                address=property.address,
                city=property.city,
                state=property.state,
                zip_code=property.zip_code,
                bedrooms=property.bedrooms,
                bathrooms=property.bathrooms,
                sqft=property.sqft,
            )
            if rent:
                property.estimated_rent = rent

        return property

    async def get_current_rates(self) -> dict:
        """Get current mortgage rates and macro indicators."""
        return await self.fred.get_macro_summary()


# Convenience function
async def import_property_from_url(
    url: str,
    rentcast_api_key: Optional[str] = None,
) -> Optional[Deal]:
    """
    Import a property from URL and return analyzed Deal.

    Usage:
        deal = await import_property_from_url("https://zillow.com/...")
        print(f"Cash flow: ${deal.financial_metrics.monthly_cash_flow}/mo")
    """
    aggregator = DataAggregator(rentcast_api_key=rentcast_api_key)
    try:
        return await aggregator.import_from_url(url)
    finally:
        await aggregator.close()
