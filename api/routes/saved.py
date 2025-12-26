"""API routes for saved properties and database operations."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from src.db import get_repository, SQLiteRepository

router = APIRouter()


# ==================== Response Models ====================

class MarketResponse(BaseModel):
    id: str
    name: str
    state: str
    metro: Optional[str] = None
    is_favorite: bool = False
    is_supported: bool = True
    api_support: Optional[dict] = None
    overall_score: float = 0
    cash_flow_score: float = 0
    growth_score: float = 0
    # Market data fields (from stored market_data)
    median_home_price: Optional[float] = None
    median_rent: Optional[float] = None
    rent_to_price_ratio: Optional[float] = None
    price_change_1yr: Optional[float] = None
    job_growth_1yr: Optional[float] = None
    unemployment_rate: Optional[float] = None
    days_on_market: Optional[int] = None
    months_of_inventory: Optional[float] = None


class SavedPropertyResponse(BaseModel):
    """
    Response model for saved properties.

    This is the "Enriched" tier - properties saved to the database with
    full analysis data, location insights, and user customizations.
    """
    id: str
    address: str
    city: str
    state: str
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Property details
    list_price: Optional[float] = None
    estimated_rent: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    property_type: Optional[str] = None
    year_built: Optional[int] = None
    days_on_market: Optional[int] = None

    # Source
    source: Optional[str] = None
    source_url: Optional[str] = None
    photos: Optional[List[str]] = None

    # All score dimensions (not just overall)
    overall_score: Optional[float] = None
    financial_score: Optional[float] = None
    market_score: Optional[float] = None
    risk_score: Optional[float] = None
    liquidity_score: Optional[float] = None

    # Financial metrics
    cash_flow: Optional[float] = None
    cash_on_cash: Optional[float] = None
    cap_rate: Optional[float] = None

    # Location insights (cached from external APIs)
    location_data: Optional[dict] = None  # walk_score, noise, schools, flood_zone

    # Custom scenarios
    custom_scenarios: Optional[List[dict]] = None

    # Full analysis data (financials, score, pros/cons)
    analysis_data: Optional[dict] = None

    # Pipeline
    pipeline_status: str = "analyzed"
    is_favorite: bool = False
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

    # Timestamps
    last_analyzed: Optional[datetime] = None
    location_data_fetched: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AddMarketRequest(BaseModel):
    name: str
    state: str
    metro: Optional[str] = None
    is_favorite: bool = False


class UpdatePropertyRequest(BaseModel):
    pipeline_status: Optional[str] = None
    is_favorite: Optional[bool] = None
    note: Optional[str] = None


class SavePropertyRequest(BaseModel):
    """
    Request to save an analyzed property to the database.

    This creates an "Enriched" tier property with full analysis data
    and location insights for long-term tracking.
    """
    # Required fields
    address: str
    city: str
    state: str
    list_price: float

    # Location
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Property details
    estimated_rent: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    property_type: Optional[str] = None
    year_built: Optional[int] = None
    days_on_market: Optional[int] = None

    # Source
    source: Optional[str] = None
    source_url: Optional[str] = None
    photos: Optional[List[str]] = None

    # All score dimensions
    overall_score: Optional[float] = None
    financial_score: Optional[float] = None
    market_score: Optional[float] = None
    risk_score: Optional[float] = None
    liquidity_score: Optional[float] = None

    # Financial metrics
    cash_flow: Optional[float] = None
    cash_on_cash: Optional[float] = None
    cap_rate: Optional[float] = None

    # Full analysis data (complete Deal model JSON)
    analysis_data: Optional[dict] = None

    # Location insights (if already fetched)
    location_data: Optional[dict] = None


class StatsResponse(BaseModel):
    total_saved_properties: int
    favorite_properties: int
    total_markets: int
    favorite_markets: int
    properties_by_status: dict
    cache: dict


class MetroSuggestion(BaseModel):
    name: str
    state: str
    metro: str
    median_price: Optional[float] = None
    median_rent: Optional[float] = None
    has_full_support: bool = False  # Has HUD rent data


# ==================== Helper Functions ====================

def build_property_response(p) -> SavedPropertyResponse:
    """Build SavedPropertyResponse from a SavedPropertyDB model."""
    return SavedPropertyResponse(
        id=p.id,
        address=p.address,
        city=p.city,
        state=p.state,
        zip_code=p.zip_code,
        latitude=getattr(p, 'latitude', None),
        longitude=getattr(p, 'longitude', None),
        list_price=p.list_price,
        estimated_rent=p.estimated_rent,
        bedrooms=p.bedrooms,
        bathrooms=p.bathrooms,
        sqft=p.sqft,
        property_type=p.property_type,
        year_built=getattr(p, 'year_built', None),
        days_on_market=getattr(p, 'days_on_market', None),
        source=p.source,
        source_url=p.source_url,
        photos=getattr(p, 'photos', None),
        overall_score=p.overall_score,
        financial_score=getattr(p, 'financial_score', None),
        market_score=getattr(p, 'market_score', None),
        risk_score=getattr(p, 'risk_score', None),
        liquidity_score=getattr(p, 'liquidity_score', None),
        cash_flow=p.cash_flow,
        cash_on_cash=p.cash_on_cash,
        cap_rate=p.cap_rate,
        location_data=getattr(p, 'location_data', None),
        custom_scenarios=getattr(p, 'custom_scenarios', None),
        analysis_data=getattr(p, 'analysis_data', None),
        pipeline_status=p.pipeline_status or "analyzed",
        is_favorite=p.is_favorite or False,
        notes=p.notes,
        tags=getattr(p, 'tags', None),
        last_analyzed=getattr(p, 'last_analyzed', None),
        location_data_fetched=getattr(p, 'location_data_fetched', None),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def build_market_response(m) -> MarketResponse:
    """Build MarketResponse from a MarketDB model, computing scores on-demand from market_data."""
    from src.models.market import Market, MarketMetrics, MarketTrend

    # Extract market data from stored JSON if available
    market_data = m.market_data or {}

    # Compute scores on-demand if we have market data
    overall_score = 0.0
    cash_flow_score = 0.0
    growth_score = 0.0

    if market_data:
        try:
            # Build Market model from stored data
            market = Market(
                id=m.id,
                name=m.name,
                state=m.state,
                metro=m.metro or market_data.get("metro", ""),
                region=market_data.get("region"),
                population=market_data.get("population"),
                population_growth_1yr=market_data.get("population_growth_1yr"),
                population_growth_5yr=market_data.get("population_growth_5yr"),
                unemployment_rate=market_data.get("unemployment_rate"),
                job_growth_1yr=market_data.get("job_growth_yoy") or market_data.get("job_growth_1yr"),
                labor_force=market_data.get("labor_force"),
                major_employers=market_data.get("major_employers", []),
                median_household_income=market_data.get("median_household_income"),
                median_home_price=market_data.get("median_sale_price") or market_data.get("median_home_price"),
                median_rent=market_data.get("fmr_2br") or market_data.get("median_rent"),
                avg_rent_to_price=market_data.get("rent_to_price_ratio") or market_data.get("avg_rent_to_price"),
                price_change_1yr=market_data.get("price_change_yoy") or market_data.get("price_change_1yr"),
                price_change_5yr=market_data.get("price_change_5yr"),
                rent_change_1yr=market_data.get("rent_change_1yr"),
                months_of_inventory=market_data.get("months_of_supply") or market_data.get("months_of_inventory"),
                days_on_market_avg=market_data.get("days_on_market") or market_data.get("days_on_market_avg"),
                sale_to_list_ratio=market_data.get("sale_to_list_ratio"),
                pct_sold_above_list=market_data.get("pct_sold_above_list"),
                pct_sold_below_list=market_data.get("pct_sold_below_list"),
                landlord_friendly=market_data.get("landlord_friendly", True),
                landlord_friendly_score=market_data.get("landlord_friendly_score"),
                property_tax_rate=market_data.get("avg_property_tax_rate") or market_data.get("property_tax_rate"),
                has_state_income_tax=market_data.get("has_state_income_tax"),
                insurance_risk=market_data.get("insurance_risk"),
                insurance_risk_factors=market_data.get("insurance_risk_factors", []),
                data_sources=market_data.get("data_sources", []),
            )
            # Compute scores on-demand
            metrics = MarketMetrics.from_market(market)
            overall_score = metrics.overall_score
            cash_flow_score = metrics.cash_flow_score
            growth_score = metrics.growth_score
        except Exception as e:
            # Fall back to stored scores if computation fails
            print(f"Score computation failed for {m.name}: {e}")
            overall_score = m.overall_score or 0
            cash_flow_score = m.cash_flow_score or 0
            growth_score = m.growth_score or 0

    return MarketResponse(
        id=m.id,
        name=m.name,
        state=m.state,
        metro=m.metro,
        is_favorite=m.is_favorite,
        is_supported=m.is_supported,
        api_support=m.api_support,
        overall_score=overall_score,
        cash_flow_score=cash_flow_score,
        growth_score=growth_score,
        # Market data fields
        median_home_price=market_data.get("median_home_price"),
        median_rent=market_data.get("median_rent"),
        rent_to_price_ratio=market_data.get("avg_rent_to_price"),
        price_change_1yr=market_data.get("price_change_1yr"),
        job_growth_1yr=market_data.get("job_growth_yoy") or market_data.get("job_growth_1yr"),
        unemployment_rate=market_data.get("metro_unemployment_rate") or market_data.get("unemployment_rate"),
        days_on_market=market_data.get("days_on_market_avg"),
        months_of_inventory=market_data.get("months_of_inventory"),
    )


# ==================== Market Routes ====================


@router.get("/markets/search", response_model=List[MetroSuggestion])
async def search_metros(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search for metros using local data for instant autocomplete."""
    from src.data_sources.metros import search_metros as local_search
    from src.data_sources.hud_fmr import EMBEDDED_FMR_DATA

    # Use local metro data - instant, no API call
    matches = local_search(q, limit=limit)

    # Build response with support indicators
    results = []
    for m in matches:
        # Check if this metro has HUD FMR data (full support)
        has_support = m.id in EMBEDDED_FMR_DATA or m.has_hud_data

        # Get rent estimate if available
        fmr_data = EMBEDDED_FMR_DATA.get(m.id)
        median_rent = fmr_data.fmr_2br if fmr_data else None

        results.append(MetroSuggestion(
            name=m.city,
            state=m.state,
            metro=m.metro_name,
            median_price=None,  # Would need live data
            median_rent=median_rent,
            has_full_support=has_support,
        ))

    return results

@router.get("/markets", response_model=List[MarketResponse])
async def get_markets(
    favorites_only: bool = Query(False, description="Only return favorite markets"),
):
    """Get all markets sorted by favorites first, then by score."""
    repo = get_repository()

    if favorites_only:
        markets = repo.get_favorite_markets()
    else:
        markets = repo.get_all_markets_sorted()

    return [build_market_response(m) for m in markets]


@router.get("/markets/favorites", response_model=List[MarketResponse])
async def get_favorite_markets():
    """Get user's favorite (researched) markets."""
    repo = get_repository()
    markets = repo.get_favorite_markets()
    return [build_market_response(m) for m in markets]


@router.post("/markets", response_model=MarketResponse)
async def add_market(request: AddMarketRequest):
    """
    Add a new market and fully enrich it with data from all sources.

    This endpoint:
    1. Creates the market record
    2. Fetches data from all sources in parallel (Redfin, BLS, Census, HUD, FRED)
    3. Calculates investment scores
    4. Persists all enriched data to the database

    The enrichment may take 10-30 seconds as it fetches from multiple APIs.
    """
    import asyncio
    from src.data_sources.aggregator import DataAggregator
    from src.models.market import MarketMetrics
    from src.db.models import MarketDB

    repo = get_repository()
    market = repo.add_market(
        name=request.name,
        state=request.state,
        metro=request.metro,
        is_favorite=request.is_favorite,
    )

    # Fully enrich market data from all external sources
    aggregator = DataAggregator()
    enrichment_errors = []

    try:
        # Use asyncio.wait_for to timeout after 60 seconds (increased for more API calls)
        try:
            enriched_data = await asyncio.wait_for(
                aggregator.get_market_data(
                    city=request.name,
                    state=request.state,
                    metro=request.metro,
                ),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            print(f"Timeout fetching market data for {request.name}, {request.state}")
            enriched_data = None
            enrichment_errors.append("Timeout fetching market data")

        if enriched_data:
            # Convert to Market model for scoring
            market_model = enriched_data.to_market()
            metrics = MarketMetrics.from_market(market_model)

            # Update database with ALL enriched data
            market_db = repo.session.query(MarketDB).filter_by(id=market.id).first()
            if market_db:
                # Store the full enriched data (includes all sources)
                market_db.market_data = enriched_data.to_dict()

                # Store metro name if we got a better one from Redfin/Census
                if enriched_data.metro:
                    market_db.metro = enriched_data.metro

                # Store calculated scores
                market_db.overall_score = metrics.overall_score
                market_db.cash_flow_score = metrics.cash_flow_score
                market_db.growth_score = metrics.growth_score

                market_db.updated_at = datetime.utcnow()
                repo.session.commit()

                # Log enrichment results
                sources = enriched_data.data_sources
                errors = enriched_data.enrichment_errors
                print(f"Market {request.name}, {request.state} enriched from: {sources}")
                if errors:
                    print(f"  Enrichment errors: {errors}")

                # Update return values
                market = market_db

    except Exception as e:
        print(f"Error enriching market data: {e}")
        enrichment_errors.append(str(e))
    finally:
        await aggregator.close()

    return build_market_response(market)


@router.post("/markets/{market_id}/favorite", response_model=MarketResponse)
async def toggle_market_favorite(market_id: str):
    """Toggle a market's favorite status."""
    repo = get_repository()
    market = repo.toggle_market_favorite(market_id)

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    return build_market_response(market)


@router.post("/markets/{market_id}/refresh", response_model=MarketResponse)
async def refresh_market_data(market_id: str):
    """
    Refresh market data from all sources.

    Re-fetches data from Redfin, BLS, Census, HUD, FRED and recalculates scores.
    Use this to get updated market conditions and scores.
    """
    import asyncio
    from src.data_sources.aggregator import DataAggregator
    from src.models.market import MarketMetrics

    repo = get_repository()

    # Find market in database
    from src.db.models import MarketDB
    market_db = repo.session.query(MarketDB).filter_by(id=market_id).first()

    if not market_db:
        raise HTTPException(status_code=404, detail="Market not found")

    aggregator = DataAggregator()
    try:
        # Fetch fresh data from all sources
        try:
            enriched_data = await asyncio.wait_for(
                aggregator.get_market_data(
                    city=market_db.name,
                    state=market_db.state,
                    metro=market_db.metro,
                ),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Timeout fetching market data. Please try again."
            )

        if enriched_data:
            # Convert to Market model for scoring
            market_model = enriched_data.to_market()
            metrics = MarketMetrics.from_market(market_model)

            # Update database with fresh data
            market_db.market_data = enriched_data.to_dict()
            if enriched_data.metro:
                market_db.metro = enriched_data.metro
            market_db.overall_score = metrics.overall_score
            market_db.cash_flow_score = metrics.cash_flow_score
            market_db.growth_score = metrics.growth_score
            market_db.updated_at = datetime.utcnow()
            repo.session.commit()

            # Log refresh results
            print(f"Market {market_db.name} refreshed from: {enriched_data.data_sources}")
            if enriched_data.enrichment_errors:
                print(f"  Errors: {enriched_data.enrichment_errors}")

    finally:
        await aggregator.close()

    return build_market_response(market_db)


@router.post("/markets/refresh-all")
async def refresh_all_markets():
    """
    Refresh data for all favorite markets.

    Fetches fresh data from all sources for each favorited market.
    This may take several minutes for many markets.
    """
    from src.data_sources.aggregator import DataAggregator
    from src.models.market import MarketMetrics
    from src.db.models import MarketDB

    repo = get_repository()
    markets = repo.get_favorite_markets()

    aggregator = DataAggregator()
    updated = 0
    errors = []
    results = []

    try:
        for market_db in markets:
            try:
                enriched_data = await aggregator.get_market_data(
                    city=market_db.name,
                    state=market_db.state,
                    metro=market_db.metro,
                )
                if enriched_data:
                    market_model = enriched_data.to_market()
                    metrics = MarketMetrics.from_market(market_model)

                    market_db.market_data = enriched_data.to_dict()
                    if enriched_data.metro:
                        market_db.metro = enriched_data.metro
                    market_db.overall_score = metrics.overall_score
                    market_db.cash_flow_score = metrics.cash_flow_score
                    market_db.growth_score = metrics.growth_score
                    market_db.updated_at = datetime.utcnow()
                    updated += 1

                    results.append({
                        "market": f"{market_db.name}, {market_db.state}",
                        "sources": enriched_data.data_sources,
                        "errors": enriched_data.enrichment_errors or None,
                    })
            except Exception as e:
                errors.append(f"{market_db.name}: {str(e)}")

        repo.session.commit()
    finally:
        await aggregator.close()

    return {
        "success": True,
        "updated": updated,
        "total": len(markets),
        "results": results,
        "errors": errors if errors else None,
    }


@router.delete("/markets/{market_id}")
async def delete_market(market_id: str):
    """Delete a market from the database."""
    from src.db.models import MarketDB

    repo = get_repository()
    market_db = repo.session.query(MarketDB).filter_by(id=market_id).first()

    if not market_db:
        raise HTTPException(status_code=404, detail="Market not found")

    repo.session.delete(market_db)
    repo.session.commit()

    return {"success": True, "message": f"Market {market_id} deleted"}


# ==================== Saved Property Routes ====================

@router.get("/properties", response_model=List[SavedPropertyResponse])
async def get_saved_properties(
    status: Optional[str] = Query(None, description="Filter by pipeline status"),
    favorites_only: bool = Query(False, description="Only return favorites"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get saved properties with filters."""
    repo = get_repository()
    properties = repo.get_saved_properties(
        status=status,
        is_favorite=True if favorites_only else None,
        limit=limit,
        offset=offset,
    )

    return [
        SavedPropertyResponse(
            id=p.id,
            address=p.address,
            city=p.city,
            state=p.state,
            zip_code=p.zip_code,
            list_price=p.list_price,
            estimated_rent=p.estimated_rent,
            bedrooms=p.bedrooms,
            bathrooms=p.bathrooms,
            sqft=p.sqft,
            property_type=p.property_type,
            source=p.source,
            source_url=p.source_url,
            overall_score=p.overall_score,
            cash_flow=p.cash_flow,
            cash_on_cash=p.cash_on_cash,
            cap_rate=p.cap_rate,
            pipeline_status=p.pipeline_status or "analyzed",
            is_favorite=p.is_favorite or False,
            notes=p.notes,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in properties
    ]


@router.post("/properties", response_model=SavedPropertyResponse)
async def save_property(request: SavePropertyRequest):
    """
    Save an analyzed property to the database (Enriched tier).

    This endpoint creates an enriched property with full analysis data,
    location insights, and all score dimensions for long-term tracking.
    """
    from src.db.models import SavedPropertyDB

    repo = get_repository()

    # Generate a unique ID for the property
    property_id = f"{request.source or 'manual'}_{hash(request.source_url or request.address) % 1000000:06d}"

    # Check if property already exists
    existing = repo.get_saved_property(property_id)
    if existing:
        # Update existing property with new data
        existing.list_price = request.list_price
        existing.estimated_rent = request.estimated_rent
        existing.latitude = request.latitude
        existing.longitude = request.longitude
        existing.year_built = request.year_built
        existing.days_on_market = request.days_on_market
        if request.photos:
            existing.photos = request.photos
        existing.overall_score = request.overall_score
        existing.financial_score = request.financial_score
        existing.market_score = request.market_score
        existing.risk_score = request.risk_score
        existing.liquidity_score = request.liquidity_score
        existing.cash_flow = request.cash_flow
        existing.cash_on_cash = request.cash_on_cash
        existing.cap_rate = request.cap_rate
        if request.analysis_data:
            existing.analysis_data = request.analysis_data
        if request.location_data:
            existing.location_data = request.location_data
            existing.location_data_fetched = datetime.utcnow()
        existing.last_analyzed = datetime.utcnow()
        existing.updated_at = datetime.utcnow()
        repo.session.commit()
        prop = existing
    else:
        # Create new enriched property
        prop = SavedPropertyDB(
            id=property_id,
            address=request.address,
            city=request.city,
            state=request.state,
            zip_code=request.zip_code,
            latitude=request.latitude,
            longitude=request.longitude,
            list_price=request.list_price,
            estimated_rent=request.estimated_rent,
            bedrooms=request.bedrooms,
            bathrooms=request.bathrooms,
            sqft=request.sqft,
            property_type=request.property_type,
            year_built=request.year_built,
            days_on_market=request.days_on_market,
            source=request.source,
            source_url=request.source_url,
            photos=request.photos,
            overall_score=request.overall_score,
            financial_score=request.financial_score,
            market_score=request.market_score,
            risk_score=request.risk_score,
            liquidity_score=request.liquidity_score,
            cash_flow=request.cash_flow,
            cash_on_cash=request.cash_on_cash,
            cap_rate=request.cap_rate,
            analysis_data=request.analysis_data,
            location_data=request.location_data,
            location_data_fetched=datetime.utcnow() if request.location_data else None,
            last_analyzed=datetime.utcnow(),
            pipeline_status="analyzed",
            is_favorite=False,
        )
        repo.session.add(prop)
        repo.session.commit()

    return build_property_response(prop)


@router.get("/properties/{property_id}", response_model=SavedPropertyResponse)
async def get_saved_property(property_id: str):
    """Get a saved property by ID (Enriched tier with full data)."""
    repo = get_repository()
    prop = repo.get_saved_property(property_id)

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    return build_property_response(prop)


@router.get("/properties/{property_id}/analysis")
async def get_property_analysis(property_id: str):
    """Get full analysis data for a saved property."""
    repo = get_repository()
    prop = repo.get_saved_property(property_id)

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if not prop.analysis_data:
        raise HTTPException(status_code=404, detail="No analysis data available")

    return prop.analysis_data


@router.patch("/properties/{property_id}", response_model=SavedPropertyResponse)
async def update_property(property_id: str, request: UpdatePropertyRequest):
    """Update a saved property's status, favorite, or add a note."""
    repo = get_repository()

    prop = repo.get_saved_property(property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if request.pipeline_status is not None:
        repo.update_property_status(property_id, request.pipeline_status)

    if request.is_favorite is not None:
        if prop.is_favorite != request.is_favorite:
            repo.toggle_property_favorite(property_id)

    if request.note:
        repo.add_property_note(property_id, request.note)

    # Fetch updated property
    prop = repo.get_saved_property(property_id)
    return build_property_response(prop)


@router.post("/properties/{property_id}/favorite", response_model=SavedPropertyResponse)
async def toggle_property_favorite(property_id: str):
    """Toggle a property's favorite status."""
    repo = get_repository()
    prop = repo.toggle_property_favorite(property_id)

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    return build_property_response(prop)


@router.delete("/properties/{property_id}")
async def delete_property(property_id: str):
    """Delete a saved property."""
    repo = get_repository()
    success = await repo.delete_deal(property_id)

    if not success:
        raise HTTPException(status_code=404, detail="Property not found")

    return {"success": True, "message": "Property deleted"}


# ==================== Re-analyze & Location Data ====================

@router.post("/properties/{property_id}/refresh-location", response_model=SavedPropertyResponse)
async def refresh_property_location_data(property_id: str):
    """
    Refresh location data (Walk Score, Noise, Schools, Flood Zone) for a saved property.

    This fetches fresh data from external APIs and updates the cached location_data.
    If the property doesn't have coordinates, it will try to geocode the address first.
    """
    import asyncio
    from src.data_sources.walkscore import WalkScoreClient
    from src.data_sources.us_real_estate import USRealEstateClient
    from src.data_sources.fema_flood import FEMAFloodClient
    from src.data_sources.geocoder import get_geocoder

    repo = get_repository()
    prop = repo.get_saved_property(property_id)

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # Get coordinates - geocode if missing
    latitude = getattr(prop, 'latitude', None)
    longitude = getattr(prop, 'longitude', None)

    if not latitude or not longitude:
        # Try to geocode the address
        try:
            geocoder = get_geocoder()
            geo_result = await geocoder.geocode(
                address=prop.address,
                city=prop.city,
                state=prop.state,
                zip_code=prop.zip_code,
            )
            if geo_result:
                latitude = geo_result.latitude
                longitude = geo_result.longitude
                # Persist the coordinates
                prop.latitude = latitude
                prop.longitude = longitude
                repo.session.commit()
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Could not geocode address. Please verify the address is correct."
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to geocode address: {str(e)}"
            )

    # Fetch all location data in parallel
    walkscore_client = WalkScoreClient()
    us_real_estate_client = USRealEstateClient()
    fema_client = FEMAFloodClient()

    try:
        full_address = f"{prop.address}, {prop.city}, {prop.state} {prop.zip_code or ''}"

        walkscore_task = walkscore_client.get_scores(full_address, latitude, longitude)
        location_insights_task = us_real_estate_client.get_location_insights(
            latitude, longitude, prop.zip_code
        )
        flood_task = fema_client.get_flood_zone(latitude, longitude)

        walkscore, location_insights, flood = await asyncio.gather(
            walkscore_task, location_insights_task, flood_task,
            return_exceptions=True
        )

        # Build location data object
        location_data = {}

        if walkscore and not isinstance(walkscore, Exception):
            location_data["walk_score"] = walkscore.walk_score
            location_data["walk_description"] = walkscore.walk_description
            location_data["transit_score"] = walkscore.transit_score
            location_data["transit_description"] = walkscore.transit_description
            location_data["bike_score"] = walkscore.bike_score
            location_data["bike_description"] = walkscore.bike_description

        if location_insights and not isinstance(location_insights, Exception):
            if location_insights.get("noise"):
                location_data["noise"] = location_insights["noise"]
            if location_insights.get("schools"):
                location_data["schools"] = location_insights["schools"]

        if flood and not isinstance(flood, Exception):
            location_data["flood_zone"] = {
                "zone": flood.flood_zone,
                "risk_level": flood.risk_level,
                "description": flood.description,
                "requires_insurance": flood.requires_insurance,
                "annual_chance": flood.annual_chance,
            }

        # Update property
        prop.location_data = location_data
        prop.location_data_fetched = datetime.utcnow()
        prop.updated_at = datetime.utcnow()
        repo.session.commit()

    finally:
        await walkscore_client.close()
        await us_real_estate_client.close()
        await fema_client.close()

    return build_property_response(prop)


@router.post("/properties/{property_id}/reanalyze", response_model=SavedPropertyResponse)
async def reanalyze_property(property_id: str):
    """
    Re-analyze a saved property with fresh market data and rates.

    This recalculates financials and scores using current market conditions.
    """
    from src.data_sources.aggregator import DataAggregator
    from src.models.property import Property, PropertyType, PropertyStatus
    from src.models.deal import Deal, DealPipeline
    from src.models.financials import Financials, LoanTerms

    repo = get_repository()
    prop = repo.get_saved_property(property_id)

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    aggregator = DataAggregator()

    try:
        # Rebuild property object
        type_mapping = {
            "single_family_home": PropertyType.SFH,
            "single_family": PropertyType.SFH,
            "condo": PropertyType.CONDO,
            "townhouse": PropertyType.TOWNHOUSE,
            "duplex": PropertyType.DUPLEX,
            "triplex": PropertyType.TRIPLEX,
            "fourplex": PropertyType.FOURPLEX,
            "multi_family": PropertyType.MULTI_FAMILY,
        }
        prop_type = type_mapping.get(
            (prop.property_type or "").lower().replace("-", "_").replace(" ", "_"),
            PropertyType.SFH
        )

        property_obj = Property(
            id=prop.id,
            address=prop.address,
            city=prop.city,
            state=prop.state,
            zip_code=prop.zip_code,
            list_price=prop.list_price or 0,
            property_type=prop_type,
            bedrooms=prop.bedrooms or 3,
            bathrooms=prop.bathrooms or 2.0,
            sqft=prop.sqft,
            latitude=getattr(prop, 'latitude', None),
            longitude=getattr(prop, 'longitude', None),
            status=PropertyStatus.ACTIVE,
            source=prop.source,
            source_url=prop.source_url,
        )

        # Fetch fresh rent estimate
        rent_estimate = await aggregator.rentcast.get_rent_estimate(
            address=prop.address,
            city=prop.city,
            state=prop.state,
            zip_code=prop.zip_code or "",
            bedrooms=prop.bedrooms or 3,
            bathrooms=prop.bathrooms or 2.0,
            sqft=prop.sqft,
        )

        if rent_estimate:
            property_obj.estimated_rent = rent_estimate.rent_estimate

        # Get fresh market data
        market_data = await aggregator.get_market_data(prop.city, prop.state)
        market = market_data.to_market() if market_data else None

        # Create deal and run analysis
        deal = Deal(
            id=f"reanalyzed_{prop.id}",
            property=property_obj,
            market=market,
            pipeline_status=DealPipeline.ANALYZED,
            first_seen=prop.created_at,
        )

        # Use existing loan terms if in analysis_data, otherwise defaults
        existing_analysis = prop.analysis_data or {}
        existing_financials = existing_analysis.get("financials", {})
        existing_loan = existing_financials.get("loan", {})

        deal.financials = Financials(
            property_id=property_obj.id,
            purchase_price=prop.list_price or 0,
            estimated_rent=property_obj.estimated_rent or 0,
            loan=LoanTerms(
                down_payment_pct=existing_loan.get("down_payment_pct", 0.25),
                interest_rate=existing_loan.get("interest_rate", 0.07),
            ),
        )

        deal.analyze()

        # Update the property with new analysis data
        prop.estimated_rent = property_obj.estimated_rent
        prop.overall_score = deal.score.overall_score if deal.score else None
        prop.financial_score = deal.score.financial_score if deal.score else None
        prop.market_score = deal.score.market_score if deal.score else None
        prop.risk_score = deal.score.risk_score if deal.score else None
        prop.liquidity_score = deal.score.liquidity_score if deal.score else None
        prop.cash_flow = deal.financials.monthly_cash_flow if deal.financials else None
        prop.cash_on_cash = deal.financial_metrics.cash_on_cash_return if deal.financial_metrics else None
        prop.cap_rate = deal.financial_metrics.cap_rate if deal.financial_metrics else None
        prop.analysis_data = deal.model_dump(mode='json')
        prop.last_analyzed = datetime.utcnow()
        prop.updated_at = datetime.utcnow()
        repo.session.commit()

    finally:
        await aggregator.close()

    return build_property_response(prop)


@router.post("/properties/{property_id}/reenrich", response_model=SavedPropertyResponse)
async def reenrich_property(property_id: str):
    """
    Fully re-enrich a saved property by re-fetching all data from source.

    This will:
    1. Re-fetch listing data from the original source (if available) to get fresh photos
    2. Refresh location data (Walk Score, flood zone, etc.)
    3. Re-run full analysis with current market data

    Use this when you want to refresh all data for a property.
    """
    from src.data_sources.aggregator import DataAggregator
    from src.data_sources.real_estate_providers import get_provider
    from src.data_sources.walkscore import WalkScoreClient
    from src.data_sources.fema_flood import FEMAFloodClient
    from src.models.property import Property, PropertyType, PropertyStatus
    from src.models.deal import Deal, DealPipeline
    from src.models.financials import Financials, LoanTerms
    import re

    repo = get_repository()
    prop = repo.get_saved_property(property_id)

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    aggregator = DataAggregator()
    errors = []

    try:
        # Step 1: Try to re-fetch listing data from source
        # Parse the property ID to extract the original listing ID
        # Format: us_real_estate_listings_679768 or imported_us_real_estate_listings_986033
        listing_id_match = re.search(r'us_real_estate_listings_(\d+)', property_id)

        if listing_id_match:
            original_listing_id = listing_id_match.group(1)
            try:
                provider = get_provider()
                if provider and provider.is_configured:
                    fresh_listing = await provider.get_property_detail(original_listing_id)
                    if fresh_listing:
                        # Update property with fresh data
                        if fresh_listing.photos:
                            prop.photos = fresh_listing.photos
                        if fresh_listing.price:
                            prop.list_price = fresh_listing.price
                        if fresh_listing.bedrooms:
                            prop.bedrooms = fresh_listing.bedrooms
                        if fresh_listing.bathrooms:
                            prop.bathrooms = fresh_listing.bathrooms
                        if fresh_listing.sqft:
                            prop.sqft = fresh_listing.sqft
                        if fresh_listing.source_url:
                            prop.source_url = fresh_listing.source_url
                        print(f"[Re-enrich] Refreshed listing data for {prop.address}")
            except Exception as e:
                errors.append(f"Failed to refresh listing: {str(e)}")
                print(f"[Re-enrich] Could not refresh listing data: {e}")

        # Step 2: Refresh location data
        location_data = prop.location_data or {}
        latitude = prop.latitude
        longitude = prop.longitude

        # Geocode if needed
        if not latitude or not longitude:
            from src.data_sources.geocoder import CensusGeocoder
            try:
                geocoder = CensusGeocoder()
                result = await geocoder.geocode(
                    address=prop.address,
                    city=prop.city,
                    state=prop.state,
                    zip_code=prop.zip_code,
                )
                if result:
                    latitude = result.get("latitude")
                    longitude = result.get("longitude")
                    prop.latitude = latitude
                    prop.longitude = longitude
            except Exception as e:
                errors.append(f"Geocoding failed: {str(e)}")

        # Walk Score
        if latitude and longitude:
            try:
                walkscore = WalkScoreClient()
                score_data = await walkscore.get_scores(
                    address=prop.address,
                    lat=latitude,
                    lon=longitude,
                )
                if score_data:
                    location_data["walk_score"] = score_data.get("walkscore")
                    location_data["walk_description"] = score_data.get("description")
                    location_data["transit_score"] = score_data.get("transit", {}).get("score")
                    location_data["transit_description"] = score_data.get("transit", {}).get("description")
                    location_data["bike_score"] = score_data.get("bike", {}).get("score")
                    location_data["bike_description"] = score_data.get("bike", {}).get("description")
            except Exception as e:
                errors.append(f"Walk Score failed: {str(e)}")

            # Flood zone
            try:
                flood_client = FEMAFloodClient()
                flood_data = await flood_client.get_flood_zone(latitude, longitude)
                if flood_data:
                    location_data["flood_zone"] = flood_data.get("zone")
                    location_data["flood_zone_description"] = flood_data.get("description")
                    location_data["in_flood_zone"] = flood_data.get("in_flood_zone", False)
            except Exception as e:
                errors.append(f"Flood zone failed: {str(e)}")

        prop.location_data = location_data

        # Step 3: Re-run full analysis
        type_mapping = {
            "single_family_home": PropertyType.SFH,
            "single_family": PropertyType.SFH,
            "condo": PropertyType.CONDO,
            "townhouse": PropertyType.TOWNHOUSE,
            "duplex": PropertyType.DUPLEX,
            "triplex": PropertyType.TRIPLEX,
            "fourplex": PropertyType.FOURPLEX,
            "multi_family": PropertyType.MULTI_FAMILY,
        }
        prop_type = type_mapping.get(
            (prop.property_type or "").lower().replace("-", "_").replace(" ", "_"),
            PropertyType.SFH
        )

        property_obj = Property(
            id=prop.id,
            address=prop.address,
            city=prop.city,
            state=prop.state,
            zip_code=prop.zip_code,
            list_price=prop.list_price or 0,
            property_type=prop_type,
            bedrooms=prop.bedrooms or 3,
            bathrooms=prop.bathrooms or 2.0,
            sqft=prop.sqft,
            latitude=latitude,
            longitude=longitude,
            status=PropertyStatus.ACTIVE,
            source=prop.source,
            source_url=prop.source_url,
        )

        # Fetch fresh rent estimate
        rent_estimate = await aggregator.rentcast.get_rent_estimate(
            address=prop.address,
            city=prop.city,
            state=prop.state,
            zip_code=prop.zip_code or "",
            bedrooms=prop.bedrooms or 3,
            bathrooms=prop.bathrooms or 2.0,
            sqft=prop.sqft,
        )

        if rent_estimate:
            property_obj.estimated_rent = rent_estimate.rent_estimate
            prop.estimated_rent = rent_estimate.rent_estimate

        # Get fresh market data
        market_data = await aggregator.get_market_data(prop.city, prop.state)
        market = market_data.to_market() if market_data else None

        # Create deal and run analysis
        deal = Deal(
            id=f"reenriched_{prop.id}",
            property=property_obj,
            market=market,
            pipeline_status=DealPipeline.ANALYZED,
            first_seen=prop.created_at,
        )

        # Use existing loan terms if available
        existing_analysis = prop.analysis_data or {}
        existing_financials = existing_analysis.get("financials", {})
        existing_loan = existing_financials.get("loan", {})

        deal.financials = Financials(
            property_id=property_obj.id,
            purchase_price=prop.list_price or 0,
            estimated_rent=property_obj.estimated_rent or 0,
            loan=LoanTerms(
                down_payment_pct=existing_loan.get("down_payment_pct", 0.25),
                interest_rate=existing_loan.get("interest_rate", 0.07),
            ),
        )

        deal.analyze()

        # Update property with analysis results
        prop.overall_score = deal.score.overall_score if deal.score else None
        prop.financial_score = deal.score.financial_score if deal.score else None
        prop.market_score = deal.score.market_score if deal.score else None
        prop.risk_score = deal.score.risk_score if deal.score else None
        prop.liquidity_score = deal.score.liquidity_score if deal.score else None
        prop.cash_flow = deal.financials.monthly_cash_flow if deal.financials else None
        prop.cash_on_cash = deal.financial_metrics.cash_on_cash_return if deal.financial_metrics else None
        prop.cap_rate = deal.financial_metrics.cap_rate if deal.financial_metrics else None
        prop.analysis_data = deal.model_dump(mode='json')
        prop.last_analyzed = datetime.utcnow()
        prop.updated_at = datetime.utcnow()

        # Store any errors encountered
        if errors:
            prop.analysis_data["reenrich_errors"] = errors

        repo.session.commit()
        print(f"[Re-enrich] Completed for {prop.address}, errors: {errors if errors else 'none'}")

    finally:
        await aggregator.close()

    return build_property_response(prop)


class CustomScenarioRequest(BaseModel):
    """Request to save a custom financing scenario (What Should I Offer)."""
    name: Optional[str] = None
    offer_price: float
    down_payment_pct: float = 0.25
    interest_rate: float = 0.07
    loan_term_years: int = 30


@router.post("/properties/{property_id}/scenarios", response_model=SavedPropertyResponse)
async def add_custom_scenario(property_id: str, request: CustomScenarioRequest):
    """
    Add a custom financing scenario to a saved property.

    Use this for "What Should I Offer" calculations - saving different
    offer prices and financing terms to compare.
    """
    from src.models.financials import Financials, LoanTerms

    repo = get_repository()
    prop = repo.get_saved_property(property_id)

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # Calculate financials for this scenario
    financials = Financials(
        property_id=prop.id,
        purchase_price=request.offer_price,
        estimated_rent=prop.estimated_rent or 0,
        loan=LoanTerms(
            down_payment_pct=request.down_payment_pct,
            interest_rate=request.interest_rate,
            loan_term_years=request.loan_term_years,
        ),
    )
    financials.calculate()

    # Calculate derived metrics
    cash_on_cash = (
        financials.annual_cash_flow / financials.total_cash_needed
        if financials.total_cash_needed and financials.total_cash_needed > 0
        else 0
    )
    cap_rate = (
        financials.net_operating_income / request.offer_price
        if request.offer_price > 0
        else 0
    )

    # Build scenario object
    scenario = {
        "name": request.name or f"Scenario at {request.offer_price:,.0f}",
        "offer_price": request.offer_price,
        "down_payment_pct": request.down_payment_pct,
        "interest_rate": request.interest_rate,
        "loan_term_years": request.loan_term_years,
        "monthly_cash_flow": financials.monthly_cash_flow,
        "cash_on_cash": cash_on_cash,
        "cap_rate": cap_rate,
        "total_cash_needed": financials.total_cash_needed,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Add to scenarios list
    scenarios = getattr(prop, 'custom_scenarios', None) or []
    scenarios.append(scenario)
    prop.custom_scenarios = scenarios
    prop.updated_at = datetime.utcnow()
    repo.session.commit()

    return build_property_response(prop)


# ==================== Stats & Cache Routes ====================

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get database and cache statistics."""
    repo = get_repository()
    stats = await repo.get_stats()
    return StatsResponse(**stats)


@router.post("/cache/cleanup")
async def cleanup_cache():
    """Clean up expired cache entries."""
    repo = get_repository()
    deleted = repo.cache.cleanup_expired()
    return {"success": True, "deleted_entries": deleted}


@router.delete("/cache")
async def clear_cache(
    provider: Optional[str] = Query(None, description="Clear cache for specific provider"),
):
    """Clear cache entries."""
    repo = get_repository()
    deleted = repo.cache.invalidate(provider=provider)
    return {"success": True, "deleted_entries": deleted}
