"""
Data aggregator that combines multiple data sources.

Provides unified interface for:
- Market data (Redfin + FRED + HUD + Census + BLS + State data)
- Rent estimates (RentCast + HUD FMR fallback)
- Property import (URL parser + rent enrichment)

Data Sources:
- Redfin: Housing prices, inventory, days on market, price trends
- FRED: Mortgage rates, national unemployment
- BLS: Metro unemployment, job growth
- HUD: Fair market rents
- Census: Population, population growth, median income
- State Data: Landlord friendliness, property tax rates, insurance risk
"""

from dataclasses import dataclass, field
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
from src.data_sources.census import CensusClient
from src.data_sources.state_data import get_state_data, StateData


@dataclass
class EnrichedMarketData:
    """
    Market data enriched from multiple sources.

    This is the comprehensive data model for a fully enriched market.
    All fields are populated when adding a market to favorites.
    """

    market_id: str
    name: str
    state: str
    metro: Optional[str] = None
    region: Optional[str] = None

    # === From Redfin (Housing Market) ===
    median_sale_price: Optional[float] = None
    median_list_price: Optional[float] = None
    price_per_sqft: Optional[float] = None
    price_change_yoy: Optional[float] = None  # Percentage
    homes_sold: Optional[int] = None
    new_listings: Optional[int] = None
    inventory: Optional[int] = None
    months_of_supply: Optional[float] = None
    days_on_market: Optional[int] = None
    sale_to_list_ratio: Optional[float] = None
    pct_sold_above_list: Optional[float] = None
    pct_sold_below_list: Optional[float] = None

    # === From FRED (Macro/National) ===
    mortgage_rate_30yr: Optional[float] = None
    mortgage_rate_15yr: Optional[float] = None
    national_unemployment_rate: Optional[float] = None

    # === From BLS (Metro Employment) ===
    metro_unemployment_rate: Optional[float] = None
    job_growth_yoy: Optional[float] = None  # Percentage
    labor_force: Optional[int] = None
    employment: Optional[int] = None

    # === From HUD (Rent Data) ===
    fmr_0br: Optional[int] = None  # Studio
    fmr_1br: Optional[int] = None
    fmr_2br: Optional[int] = None
    fmr_3br: Optional[int] = None
    fmr_4br: Optional[int] = None

    # === From Census (Demographics) ===
    population: Optional[int] = None
    population_growth_1yr: Optional[float] = None  # Percentage
    population_growth_5yr: Optional[float] = None  # Percentage
    median_household_income: Optional[int] = None

    # === From State Data (Static) ===
    landlord_friendly: bool = True
    landlord_friendly_score: Optional[int] = None  # 1-10
    avg_property_tax_rate: Optional[float] = None  # Decimal (0.01 = 1%)
    has_state_income_tax: Optional[bool] = None
    insurance_risk: Optional[str] = None  # "low", "medium", "high"
    insurance_risk_factors: list[str] = field(default_factory=list)

    # === Calculated Metrics ===
    rent_to_price_ratio: Optional[float] = None  # Percentage
    cap_rate_estimate: Optional[float] = None  # Percentage
    price_to_income_ratio: Optional[float] = None
    rent_to_income_ratio: Optional[float] = None  # Percentage

    # === Metadata ===
    data_sources: list[str] = field(default_factory=list)
    last_updated: Optional[datetime] = None
    enrichment_errors: list[str] = field(default_factory=list)

    def to_market(self) -> Market:
        """Convert to Market model for scoring and persistence."""
        # Calculate rent-to-price ratio if not already set
        rent_to_price = self.rent_to_price_ratio
        if rent_to_price is None and self.fmr_2br and self.median_sale_price:
            rent_to_price = (self.fmr_2br / self.median_sale_price) * 100

        # Determine price trend
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

        # Determine rent trend (based on market conditions)
        rent_trend = MarketTrend.STABLE
        if self.months_of_supply:
            if self.months_of_supply < 2:
                rent_trend = MarketTrend.MODERATE_GROWTH
            elif self.months_of_supply > 6:
                rent_trend = MarketTrend.MODERATE_DECLINE

        # Prefer metro-specific unemployment from BLS over national from FRED
        unemployment = None
        if self.metro_unemployment_rate:
            unemployment = self.metro_unemployment_rate / 100
        elif self.national_unemployment_rate:
            unemployment = self.national_unemployment_rate / 100

        return Market(
            id=self.market_id,
            name=self.name,
            metro=self.metro or self.name,
            state=self.state,
            region=self.region,
            # Housing
            median_home_price=self.median_sale_price,
            median_price_per_sqft=self.price_per_sqft,
            price_change_1yr=self.price_change_yoy,
            # Rental
            median_rent=self.fmr_2br,
            avg_rent_to_price=rent_to_price,
            # Supply/Demand
            months_of_inventory=self.months_of_supply,
            days_on_market_avg=self.days_on_market,
            homes_sold_1yr=self.homes_sold,
            new_listings_1yr=self.new_listings,
            sale_to_list_ratio=self.sale_to_list_ratio,
            pct_sold_above_list=self.pct_sold_above_list,
            pct_sold_below_list=self.pct_sold_below_list,
            # Employment
            unemployment_rate=unemployment,
            job_growth_1yr=self.job_growth_yoy,
            labor_force=self.labor_force,
            # Demographics
            population=self.population,
            population_growth_1yr=self.population_growth_1yr,
            population_growth_5yr=self.population_growth_5yr,
            median_household_income=self.median_household_income,
            # Trends
            price_trend=price_trend,
            rent_trend=rent_trend,
            # Regulatory & Costs
            landlord_friendly=self.landlord_friendly,
            landlord_friendly_score=self.landlord_friendly_score,
            property_tax_rate=self.avg_property_tax_rate,
            has_state_income_tax=self.has_state_income_tax,
            insurance_risk=self.insurance_risk,
            insurance_risk_factors=self.insurance_risk_factors,
            # Metadata
            data_sources=self.data_sources,
            last_updated=self.last_updated or datetime.utcnow(),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        return {
            "market_id": self.market_id,
            "name": self.name,
            "state": self.state,
            "metro": self.metro,
            "region": self.region,
            # Housing
            "median_sale_price": self.median_sale_price,
            "median_list_price": self.median_list_price,
            "price_per_sqft": self.price_per_sqft,
            "price_change_yoy": self.price_change_yoy,
            "homes_sold": self.homes_sold,
            "new_listings": self.new_listings,
            "inventory": self.inventory,
            "months_of_supply": self.months_of_supply,
            "days_on_market": self.days_on_market,
            "sale_to_list_ratio": self.sale_to_list_ratio,
            # Macro
            "mortgage_rate_30yr": self.mortgage_rate_30yr,
            "mortgage_rate_15yr": self.mortgage_rate_15yr,
            # Employment
            "metro_unemployment_rate": self.metro_unemployment_rate,
            "national_unemployment_rate": self.national_unemployment_rate,
            "job_growth_yoy": self.job_growth_yoy,
            "labor_force": self.labor_force,
            "employment": self.employment,
            # Rent
            "fmr_0br": self.fmr_0br,
            "fmr_1br": self.fmr_1br,
            "fmr_2br": self.fmr_2br,
            "fmr_3br": self.fmr_3br,
            "fmr_4br": self.fmr_4br,
            # Demographics
            "population": self.population,
            "population_growth_1yr": self.population_growth_1yr,
            "population_growth_5yr": self.population_growth_5yr,
            "median_household_income": self.median_household_income,
            # State
            "landlord_friendly": self.landlord_friendly,
            "landlord_friendly_score": self.landlord_friendly_score,
            "avg_property_tax_rate": self.avg_property_tax_rate,
            "has_state_income_tax": self.has_state_income_tax,
            "insurance_risk": self.insurance_risk,
            "insurance_risk_factors": self.insurance_risk_factors,
            # Calculated
            "rent_to_price_ratio": self.rent_to_price_ratio,
            "cap_rate_estimate": self.cap_rate_estimate,
            "price_to_income_ratio": self.price_to_income_ratio,
            "rent_to_income_ratio": self.rent_to_income_ratio,
            # Metadata
            "data_sources": self.data_sources,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "enrichment_errors": self.enrichment_errors,
        }


class DataAggregator:
    """
    Aggregates data from multiple sources for comprehensive market enrichment.

    Data Sources:
    - Redfin: Housing prices, inventory, days on market (FREE)
    - FRED: Mortgage rates, national unemployment (FREE)
    - BLS: Metro unemployment, job growth (FREE)
    - HUD: Fair market rents (FREE, embedded)
    - Census: Population, income (FREE)
    - State Data: Landlord friendliness, taxes, risk (embedded)

    Usage:
        aggregator = DataAggregator()

        # Get fully enriched market data
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
        census_api_key: Optional[str] = None,
    ):
        self.redfin = RedfinDataCenter()
        self.fred = FredClient(api_key=fred_api_key)
        self.hud = HudFmrLoader()
        self.rentcast = RentCastClient(api_key=rentcast_api_key)
        self.url_parser = PropertyUrlParser()
        self.bls = BLSClient(api_key=bls_api_key)
        self.census = CensusClient(api_key=census_api_key)

    async def close(self):
        """Close all clients."""
        await self.redfin.close()
        await self.fred.close()
        await self.hud.close()
        await self.rentcast.close()
        await self.url_parser.close()
        await self.bls.close()
        await self.census.close()

    async def get_market_data(
        self,
        city: str,
        state: str,
        metro: Optional[str] = None,
    ) -> Optional[EnrichedMarketData]:
        """
        Get fully enriched market data from all available sources.

        This is the main enrichment routine called when adding a market.
        It fetches from all data sources in parallel where possible.

        Args:
            city: City name (e.g., "Indianapolis")
            state: Two-letter state code (e.g., "IN")
            metro: Optional metro area name for better matching

        Returns:
            EnrichedMarketData with all available fields populated
        """
        import asyncio

        market_id = f"{city.lower().replace(' ', '_')}_{state.lower()}"
        data_sources = []
        errors = []

        # Initialize result with basic info
        result = EnrichedMarketData(
            market_id=market_id,
            name=city,
            state=state,
            metro=metro,
            last_updated=datetime.utcnow(),
        )

        # === 1. Get State Data (instant, no API call) ===
        try:
            state_data = get_state_data(state)
            result.landlord_friendly = state_data.landlord_friendly
            result.landlord_friendly_score = state_data.landlord_friendly_score
            result.avg_property_tax_rate = state_data.avg_property_tax_rate
            result.has_state_income_tax = state_data.has_state_income_tax
            result.insurance_risk = state_data.insurance_risk
            result.insurance_risk_factors = state_data.risk_factors
            result.region = self._get_region(state)
            data_sources.append("state_data")
        except Exception as e:
            errors.append(f"State data: {e}")

        # === 2. Fetch external data in parallel ===
        redfin_task = self._fetch_redfin(city, state, metro)
        fred_task = self._fetch_fred()
        bls_task = self._fetch_bls(market_id)
        hud_task = self._fetch_hud(market_id, state, city)
        census_task = self._fetch_census(market_id)

        results = await asyncio.gather(
            redfin_task,
            fred_task,
            bls_task,
            hud_task,
            census_task,
            return_exceptions=True,
        )

        # === 3. Process Redfin results ===
        redfin_result = results[0]
        if isinstance(redfin_result, Exception):
            errors.append(f"Redfin: {redfin_result}")
        elif redfin_result:
            redfin_data, metro_name = redfin_result
            result.median_sale_price = redfin_data.median_sale_price
            result.median_list_price = redfin_data.median_list_price
            result.price_per_sqft = redfin_data.median_ppsf
            result.price_change_yoy = (
                redfin_data.median_sale_price_yoy * 100
                if redfin_data.median_sale_price_yoy else None
            )
            result.homes_sold = redfin_data.homes_sold
            result.new_listings = redfin_data.new_listings
            result.inventory = redfin_data.inventory
            result.months_of_supply = redfin_data.months_of_supply
            result.days_on_market = redfin_data.median_dom
            result.sale_to_list_ratio = redfin_data.avg_sale_to_list
            result.pct_sold_above_list = redfin_data.pct_sold_above_list
            result.pct_sold_below_list = redfin_data.pct_sold_below_list
            if metro_name and not result.metro:
                result.metro = metro_name
            data_sources.append("redfin")

        # === 4. Process FRED results ===
        fred_result = results[1]
        if isinstance(fred_result, Exception):
            errors.append(f"FRED: {fred_result}")
        elif fred_result:
            result.mortgage_rate_30yr = fred_result.get("mortgage_30yr")
            result.mortgage_rate_15yr = fred_result.get("mortgage_15yr")
            result.national_unemployment_rate = fred_result.get("unemployment")
            data_sources.append("fred")

        # === 5. Process BLS results ===
        bls_result = results[2]
        if isinstance(bls_result, Exception):
            errors.append(f"BLS: {bls_result}")
        elif bls_result:
            result.metro_unemployment_rate = bls_result.unemployment_rate
            result.job_growth_yoy = bls_result.employment_growth
            result.labor_force = bls_result.labor_force
            result.employment = bls_result.employment
            data_sources.append("bls")

        # === 6. Process HUD results ===
        hud_result = results[3]
        if isinstance(hud_result, Exception):
            errors.append(f"HUD: {hud_result}")
        elif hud_result:
            result.fmr_0br = hud_result.get("fmr_0br")
            result.fmr_1br = hud_result.get("fmr_1br")
            result.fmr_2br = hud_result.get("fmr_2br")
            result.fmr_3br = hud_result.get("fmr_3br")
            result.fmr_4br = hud_result.get("fmr_4br")
            data_sources.append("hud")

        # === 7. Process Census results ===
        census_result = results[4]
        if isinstance(census_result, Exception):
            errors.append(f"Census: {census_result}")
        elif census_result:
            result.population = census_result.population
            result.population_growth_1yr = census_result.population_growth_1yr
            result.population_growth_5yr = census_result.population_growth_5yr
            result.median_household_income = census_result.median_household_income
            if census_result.metro_name and not result.metro:
                result.metro = census_result.metro_name
            data_sources.append("census")

        # === 8. Calculate derived metrics ===
        self._calculate_derived_metrics(result)

        result.data_sources = data_sources
        result.enrichment_errors = errors

        return result

    async def _fetch_redfin(
        self,
        city: str,
        state: str,
        metro: Optional[str],
    ) -> Optional[tuple[RedfinMarketData, Optional[str]]]:
        """Fetch housing market data from Redfin."""
        try:
            # Try metro name first if provided
            search_term = metro if metro else f"{city}, {state}"
            redfin_data = await self.redfin.get_metro_data(search_term)

            if redfin_data:
                return (redfin_data, redfin_data.region_name)

            # Fallback to city, state
            if metro:
                redfin_data = await self.redfin.get_metro_data(f"{city}, {state}")
                if redfin_data:
                    return (redfin_data, redfin_data.region_name)

            return None
        except Exception as e:
            print(f"Redfin fetch error: {e}")
            raise

    async def _fetch_fred(self) -> Optional[dict]:
        """Fetch macro data from FRED."""
        try:
            return await self.fred.get_macro_summary()
        except Exception as e:
            print(f"FRED fetch error: {e}")
            raise

    async def _fetch_bls(self, market_id: str):
        """Fetch employment data from BLS."""
        try:
            return await self.bls.get_metro_employment(market_id)
        except Exception as e:
            print(f"BLS fetch error: {e}")
            raise

    async def _fetch_hud(self, market_id: str, state: str, city: str) -> Optional[dict]:
        """Fetch fair market rent data from HUD."""
        try:
            fmr = self.hud.get_fmr(market_id)
            if not fmr:
                fmr = await self.hud.lookup_fmr(state=state, city=city)

            if fmr:
                return {
                    "fmr_0br": getattr(fmr, "fmr_0br", None),
                    "fmr_1br": fmr.fmr_1br,
                    "fmr_2br": fmr.fmr_2br,
                    "fmr_3br": fmr.fmr_3br,
                    "fmr_4br": getattr(fmr, "fmr_4br", None),
                }
            return None
        except Exception as e:
            print(f"HUD fetch error: {e}")
            raise

    async def _fetch_census(self, market_id: str):
        """Fetch demographics from Census."""
        try:
            return await self.census.get_metro_demographics(market_id)
        except Exception as e:
            print(f"Census fetch error: {e}")
            raise

    def _calculate_derived_metrics(self, result: EnrichedMarketData):
        """Calculate derived metrics from raw data."""
        # Rent-to-price ratio
        if result.fmr_2br and result.median_sale_price:
            result.rent_to_price_ratio = (result.fmr_2br / result.median_sale_price) * 100

            # Cap rate estimate (NOI / price)
            annual_rent = result.fmr_2br * 12
            expenses = annual_rent * 0.45  # ~45% expense ratio assumption
            noi = annual_rent - expenses
            result.cap_rate_estimate = (noi / result.median_sale_price) * 100

        # Price-to-income ratio
        if result.median_sale_price and result.median_household_income:
            result.price_to_income_ratio = (
                result.median_sale_price / result.median_household_income
            )

        # Rent-to-income ratio
        if result.fmr_2br and result.median_household_income:
            monthly_income = result.median_household_income / 12
            result.rent_to_income_ratio = (result.fmr_2br / monthly_income) * 100

    def _get_region(self, state: str) -> Optional[str]:
        """Get geographic region for a state."""
        regions = {
            "Northeast": ["CT", "MA", "ME", "NH", "NJ", "NY", "PA", "RI", "VT"],
            "Southeast": ["AL", "FL", "GA", "KY", "MS", "NC", "SC", "TN", "VA", "WV"],
            "Midwest": ["IA", "IL", "IN", "KS", "MI", "MN", "MO", "ND", "NE", "OH", "SD", "WI"],
            "Southwest": ["AZ", "NM", "OK", "TX"],
            "West": ["AK", "CA", "CO", "HI", "ID", "MT", "NV", "OR", "UT", "WA", "WY"],
        }
        for region, states in regions.items():
            if state.upper() in states:
                return region
        return None

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
