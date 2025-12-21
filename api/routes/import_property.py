"""API endpoints for property import and data enrichment."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl

from api.models import DealDetail, FinancialDetail, PropertyDetail
from api.routes.deals import (
    _property_to_detail,
    _financials_to_detail,
    _score_to_model,
)
from src.data_sources.aggregator import DataAggregator
from src.data_sources.url_parser import PropertyUrlParser
from src.models.market import MarketMetrics

router = APIRouter()


class ImportUrlRequest(BaseModel):
    """Request to import a property from URL."""

    url: str = Field(..., description="Zillow, Redfin, or Realtor.com listing URL")
    down_payment_pct: float = Field(default=0.25, ge=0.05, le=1.0)
    interest_rate: float = Field(default=0.07, ge=0.01, le=0.25)


class ImportUrlResponse(BaseModel):
    """Response from URL import."""

    success: bool
    deal: Optional[DealDetail] = None
    source: Optional[str] = None
    message: str
    warnings: list[str] = Field(default_factory=list)


class RentEstimateRequest(BaseModel):
    """Request for rent estimate."""

    address: str
    city: str
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str
    bedrooms: int = Field(default=3, ge=0, le=10)
    bathrooms: float = Field(default=2.0, ge=0, le=10)
    sqft: Optional[int] = Field(None, ge=100, le=50000)


class RentEstimateResponse(BaseModel):
    """Response with rent estimate."""

    estimate: float
    low: float
    high: float
    source: str
    comp_count: int = 0


class MacroDataResponse(BaseModel):
    """Current macro economic indicators."""

    mortgage_30yr: Optional[float]
    mortgage_15yr: Optional[float]
    unemployment: Optional[float]
    fed_funds_rate: Optional[float]
    treasury_10yr: Optional[float]
    updated: str


@router.post("/url", response_model=ImportUrlResponse)
async def import_from_url(request: ImportUrlRequest):
    """
    Import a property from a Zillow, Redfin, or Realtor.com URL.

    Parses the listing, enriches with rent estimate and market data,
    and returns a fully analyzed deal.
    """
    import asyncio

    aggregator = DataAggregator()
    warnings = []

    try:
        # Detect source
        parser = PropertyUrlParser()
        source = parser.detect_source(request.url)
        await parser.close()

        if not source:
            raise HTTPException(
                status_code=400,
                detail="Unsupported URL. Please use Zillow, Redfin, or Realtor.com URLs."
            )

        # Import and analyze with timeout (Vercel has 10s limit)
        try:
            deal = await asyncio.wait_for(
                aggregator.import_from_url(request.url),
                timeout=8.0
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408,
                detail="Import timed out. The listing site may be blocking requests. Please use manual entry instead."
            )

        if not deal:
            raise HTTPException(
                status_code=400,
                detail="Could not parse property from URL. Please check the URL and try again."
            )

        # Apply custom financing
        if deal.financials:
            deal.financials.loan.down_payment_pct = request.down_payment_pct
            deal.financials.loan.interest_rate = request.interest_rate
            deal.analyze()

        # Check for warnings
        if not deal.property.estimated_rent:
            warnings.append("Could not estimate rent. Using market average.")

        if not deal.market:
            warnings.append("Market data not available for this location.")

        # Build market detail if available
        market_detail = None
        if deal.market:
            from api.routes.markets import MarketDetail
            from src.models.market import MarketMetrics

            metrics = MarketMetrics.from_market(deal.market)
            market_detail = {
                "id": deal.market.id,
                "name": deal.market.name,
                "state": deal.market.state,
                "metro": deal.market.metro,
                "overall_score": metrics.overall_score,
                "cash_flow_score": metrics.cash_flow_score,
                "growth_score": metrics.growth_score,
            }

        # Build response
        deal_detail = DealDetail(
            id=deal.id,
            property=_property_to_detail(deal.property),
            score=_score_to_model(deal.score),
            financials=_financials_to_detail(deal),
            market=market_detail,
            pipeline_status=deal.pipeline_status.value,
            strategy=deal.strategy.value if deal.strategy else None,
            pros=deal.pros,
            cons=deal.cons,
            red_flags=deal.red_flags,
            notes=deal.notes,
            first_seen=deal.first_seen,
            last_analyzed=deal.last_analyzed,
        )

        return ImportUrlResponse(
            success=True,
            deal=deal_detail,
            source=source,
            message=f"Successfully imported property from {source}",
            warnings=warnings,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )
    finally:
        await aggregator.close()


@router.post("/rent-estimate", response_model=RentEstimateResponse)
async def get_rent_estimate(request: RentEstimateRequest):
    """
    Get rent estimate for a property.

    Uses RentCast API if available, falls back to HUD Fair Market Rents.
    """
    aggregator = DataAggregator()

    try:
        estimate = await aggregator.rentcast.get_rent_estimate(
            address=request.address,
            city=request.city,
            state=request.state,
            zip_code=request.zip_code,
            bedrooms=request.bedrooms,
            bathrooms=request.bathrooms,
            sqft=request.sqft,
        )

        if not estimate:
            raise HTTPException(
                status_code=404,
                detail="Could not estimate rent for this property"
            )

        return RentEstimateResponse(
            estimate=estimate.rent_estimate,
            low=estimate.rent_low,
            high=estimate.rent_high,
            source="rentcast" if aggregator.rentcast.has_api_key else "hud_fmr",
            comp_count=estimate.comp_count,
        )

    finally:
        await aggregator.close()


@router.get("/macro", response_model=MacroDataResponse)
async def get_macro_data():
    """
    Get current macro economic indicators.

    Includes mortgage rates, unemployment, and treasury yields.
    """
    aggregator = DataAggregator()

    try:
        data = await aggregator.get_current_rates()

        return MacroDataResponse(
            mortgage_30yr=data.get("mortgage_30yr"),
            mortgage_15yr=data.get("mortgage_15yr"),
            unemployment=data.get("unemployment"),
            fed_funds_rate=data.get("fed_funds_rate"),
            treasury_10yr=data.get("treasury_10yr"),
            updated=data.get("updated", ""),
        )

    finally:
        await aggregator.close()


@router.get("/market-data/{city}/{state}")
async def get_enriched_market_data(city: str, state: str):
    """
    Get enriched market data from all sources.

    Combines Redfin, FRED, and HUD data.
    """
    aggregator = DataAggregator()

    try:
        data = await aggregator.get_market_data(city, state)

        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No market data found for {city}, {state}"
            )

        return {
            "market_id": data.market_id,
            "name": data.name,
            "state": data.state,
            "pricing": {
                "median_sale_price": data.median_sale_price,
                "median_list_price": data.median_list_price,
                "price_per_sqft": data.price_per_sqft,
                "price_change_yoy": data.price_change_yoy,
            },
            "inventory": {
                "homes_sold": data.homes_sold,
                "inventory": data.inventory,
                "months_of_supply": data.months_of_supply,
                "days_on_market": data.days_on_market,
            },
            "rates": {
                "mortgage_30yr": data.mortgage_rate_30yr,
                "mortgage_15yr": data.mortgage_rate_15yr,
                "unemployment": data.unemployment_rate,
            },
            "rents": {
                "fmr_1br": data.fmr_1br,
                "fmr_2br": data.fmr_2br,
                "fmr_3br": data.fmr_3br,
            },
            "metrics": {
                "rent_to_price_ratio": data.rent_to_price_ratio,
                "cap_rate_estimate": data.cap_rate_estimate,
            },
            "data_sources": data.data_sources,
            "last_updated": data.last_updated.isoformat() if data.last_updated else None,
        }

    finally:
        await aggregator.close()
