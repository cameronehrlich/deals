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
    """Build MarketResponse from a MarketDB model, extracting stored market_data."""
    # Extract market data from stored JSON if available
    market_data = m.market_data or {}

    return MarketResponse(
        id=m.id,
        name=m.name,
        state=m.state,
        metro=m.metro,
        is_favorite=m.is_favorite,
        is_supported=m.is_supported,
        api_support=m.api_support,
        overall_score=m.overall_score or 0,
        cash_flow_score=m.cash_flow_score or 0,
        growth_score=m.growth_score or 0,
        # Market data fields
        median_home_price=market_data.get("median_home_price"),
        median_rent=market_data.get("median_rent"),
        rent_to_price_ratio=market_data.get("avg_rent_to_price"),
        price_change_1yr=market_data.get("price_change_1yr"),
        job_growth_1yr=market_data.get("job_growth_1yr"),
        unemployment_rate=market_data.get("unemployment_rate"),
        days_on_market=market_data.get("days_on_market_avg"),
        months_of_inventory=market_data.get("months_of_inventory"),
    )


# ==================== Market Routes ====================

# Global cache for metro search to avoid re-fetching on every keystroke
_metro_cache: dict = {"data": None, "timestamp": None}
_METRO_CACHE_TTL = 3600  # 1 hour


@router.get("/markets/search", response_model=List[MetroSuggestion])
async def search_metros(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search for metros from Redfin data for autocomplete."""
    from src.data_sources.redfin import RedfinDataCenter

    # Check if we have cached metro data
    now = datetime.utcnow()
    if (_metro_cache["data"] is not None and
        _metro_cache["timestamp"] is not None and
        (now - _metro_cache["timestamp"]).total_seconds() < _METRO_CACHE_TTL):
        all_metros = _metro_cache["data"]
    else:
        # Fetch fresh data
        redfin = RedfinDataCenter()
        try:
            all_metros = await redfin.get_all_metros()
            _metro_cache["data"] = all_metros
            _metro_cache["timestamp"] = now
        finally:
            await redfin.close()

    # Filter by search query (case-insensitive partial match)
    query_lower = q.lower()
    matches = [
        m for m in all_metros
        if query_lower in m.region_name.lower() or query_lower in m.state.lower()
    ]

    # Sort by relevance (starts with query first, then alphabetically)
    matches.sort(key=lambda m: (
        not m.region_name.lower().startswith(query_lower),
        m.region_name.lower()
    ))

    # Parse into response format
    results = []
    for m in matches[:limit]:
        # Extract city name from metro (e.g., "Tampa-St. Petersburg-Clearwater" -> "Tampa")
        city_name = m.region_name.split("-")[0].split(",")[0].strip()

        results.append(MetroSuggestion(
            name=city_name,
            state=m.state,
            metro=m.region_name,
            median_price=m.median_sale_price,
            median_rent=None,  # Would need HUD data
        ))

    return results

@router.get("/markets", response_model=List[MarketResponse])
async def get_markets(
    favorites_only: bool = Query(False, description="Only return favorite markets"),
    supported_only: bool = Query(True, description="Only return API-supported markets"),
):
    """Get all markets with optional filters."""
    repo = get_repository()

    if favorites_only:
        markets = repo.get_favorite_markets()
    elif supported_only:
        markets = repo.get_supported_markets()
    else:
        markets = repo.get_supported_markets()

    return [build_market_response(m) for m in markets]


@router.get("/markets/favorites", response_model=List[MarketResponse])
async def get_favorite_markets():
    """Get user's favorite (researched) markets."""
    repo = get_repository()
    markets = repo.get_favorite_markets()
    return [build_market_response(m) for m in markets]


@router.post("/markets", response_model=MarketResponse)
async def add_market(request: AddMarketRequest):
    """Add a new market and auto-populate its data."""
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

    # Auto-populate market data from external sources with timeout
    aggregator = DataAggregator()
    try:
        # Use asyncio.wait_for to timeout after 30 seconds
        try:
            market_data = await asyncio.wait_for(
                aggregator.get_market_data(request.name, request.state),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            print(f"Timeout fetching market data for {request.name}, {request.state}")
            market_data = None

        if market_data:
            market_model = market_data.to_market()
            metrics = MarketMetrics.from_market(market_model)

            # Update database with fetched data
            market_db = repo.session.query(MarketDB).filter_by(id=market.id).first()
            if market_db:
                market_db.market_data = market_model.model_dump(mode='json')
                market_db.overall_score = metrics.overall_score
                market_db.cash_flow_score = metrics.cash_flow_score
                market_db.growth_score = metrics.growth_score
                market_db.updated_at = datetime.utcnow()
                repo.session.commit()

                # Update return values
                market = market_db
    except Exception as e:
        print(f"Error fetching market data: {e}")
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
    """Fetch fresh market data and update scores."""
    from src.data_sources.aggregator import DataAggregator
    from src.models.market import Market, MarketMetrics

    repo = get_repository()

    # Find market in database
    from src.db.models import MarketDB
    market_db = repo.session.query(MarketDB).filter_by(id=market_id).first()

    if not market_db:
        raise HTTPException(status_code=404, detail="Market not found")

    aggregator = DataAggregator()
    try:
        # Fetch market data from external sources
        market_data = await aggregator.get_market_data(market_db.name, market_db.state)

        if market_data:
            # Convert to Market model for scoring
            market = market_data.to_market()

            # Calculate scores
            metrics = MarketMetrics.from_market(market)

            # Update database
            market_db.market_data = market.model_dump(mode='json')
            market_db.overall_score = metrics.overall_score
            market_db.cash_flow_score = metrics.cash_flow_score
            market_db.growth_score = metrics.growth_score
            market_db.updated_at = datetime.utcnow()
            repo.session.commit()
    finally:
        await aggregator.close()

    return build_market_response(market_db)


@router.post("/markets/refresh-all")
async def refresh_all_markets():
    """Refresh data for all favorite markets."""
    from src.data_sources.aggregator import DataAggregator
    from src.models.market import Market, MarketMetrics
    from src.db.models import MarketDB

    repo = get_repository()
    markets = repo.get_favorite_markets()

    aggregator = DataAggregator()
    updated = 0
    errors = []

    try:
        for market_db in markets:
            try:
                market_data = await aggregator.get_market_data(market_db.name, market_db.state)
                if market_data:
                    market = market_data.to_market()
                    metrics = MarketMetrics.from_market(market)

                    market_db.market_data = market.model_dump(mode='json')
                    market_db.overall_score = metrics.overall_score
                    market_db.cash_flow_score = metrics.cash_flow_score
                    market_db.growth_score = metrics.growth_score
                    market_db.updated_at = datetime.utcnow()
                    updated += 1
            except Exception as e:
                errors.append(f"{market_db.name}: {str(e)}")

        repo.session.commit()
    finally:
        await aggregator.close()

    return {
        "success": True,
        "updated": updated,
        "total": len(markets),
        "errors": errors if errors else None
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
    """
    import asyncio
    from src.data_sources.walkscore import WalkScoreClient
    from src.data_sources.us_real_estate import USRealEstateClient
    from src.data_sources.fema_flood import FEMAFloodClient

    repo = get_repository()
    prop = repo.get_saved_property(property_id)

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # Need coordinates to fetch location data
    latitude = getattr(prop, 'latitude', None)
    longitude = getattr(prop, 'longitude', None)

    if not latitude or not longitude:
        raise HTTPException(
            status_code=400,
            detail="Property doesn't have coordinates. Cannot fetch location data."
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
        prop.cash_on_cash = deal.financials.cash_on_cash_return if deal.financials else None
        prop.cap_rate = deal.financials.cap_rate if deal.financials else None
        prop.analysis_data = deal.model_dump(mode='json')
        prop.last_analyzed = datetime.utcnow()
        prop.updated_at = datetime.utcnow()
        repo.session.commit()

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

    # Build scenario object
    scenario = {
        "name": request.name or f"Scenario at {request.offer_price:,.0f}",
        "offer_price": request.offer_price,
        "down_payment_pct": request.down_payment_pct,
        "interest_rate": request.interest_rate,
        "loan_term_years": request.loan_term_years,
        "monthly_cash_flow": financials.monthly_cash_flow,
        "cash_on_cash": financials.cash_on_cash_return,
        "cap_rate": financials.cap_rate,
        "total_cash_needed": financials.total_cash_invested,
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
