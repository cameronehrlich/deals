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


class SavedPropertyResponse(BaseModel):
    id: str
    address: str
    city: str
    state: str
    zip_code: Optional[str] = None
    list_price: Optional[float] = None
    estimated_rent: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    property_type: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    overall_score: Optional[float] = None
    cash_flow: Optional[float] = None
    cash_on_cash: Optional[float] = None
    cap_rate: Optional[float] = None
    pipeline_status: str = "analyzed"
    is_favorite: bool = False
    notes: Optional[str] = None
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


class StatsResponse(BaseModel):
    total_saved_properties: int
    favorite_properties: int
    total_markets: int
    favorite_markets: int
    properties_by_status: dict
    cache: dict


# ==================== Market Routes ====================

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
        markets = repo.session.query(repo.session.query.__self__.query(type(repo.get_favorite_markets()[0])).first().__class__).all() if repo.get_favorite_markets() else []

    return [
        MarketResponse(
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
        )
        for m in (repo.get_favorite_markets() if favorites_only else repo.get_supported_markets())
    ]


@router.get("/markets/favorites", response_model=List[MarketResponse])
async def get_favorite_markets():
    """Get user's favorite (researched) markets."""
    repo = get_repository()
    markets = repo.get_favorite_markets()

    return [
        MarketResponse(
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
        )
        for m in markets
    ]


@router.post("/markets", response_model=MarketResponse)
async def add_market(request: AddMarketRequest):
    """Add a new market."""
    repo = get_repository()
    market = repo.add_market(
        name=request.name,
        state=request.state,
        metro=request.metro,
        is_favorite=request.is_favorite,
    )

    return MarketResponse(
        id=market.id,
        name=market.name,
        state=market.state,
        metro=market.metro,
        is_favorite=market.is_favorite,
        is_supported=market.is_supported,
        api_support=market.api_support,
        overall_score=market.overall_score or 0,
        cash_flow_score=market.cash_flow_score or 0,
        growth_score=market.growth_score or 0,
    )


@router.post("/markets/{market_id}/favorite", response_model=MarketResponse)
async def toggle_market_favorite(market_id: str):
    """Toggle a market's favorite status."""
    repo = get_repository()
    market = repo.toggle_market_favorite(market_id)

    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    return MarketResponse(
        id=market.id,
        name=market.name,
        state=market.state,
        metro=market.metro,
        is_favorite=market.is_favorite,
        is_supported=market.is_supported,
        api_support=market.api_support,
        overall_score=market.overall_score or 0,
        cash_flow_score=market.cash_flow_score or 0,
        growth_score=market.growth_score or 0,
    )


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


@router.get("/properties/{property_id}", response_model=SavedPropertyResponse)
async def get_saved_property(property_id: str):
    """Get a saved property by ID."""
    repo = get_repository()
    prop = repo.get_saved_property(property_id)

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    return SavedPropertyResponse(
        id=prop.id,
        address=prop.address,
        city=prop.city,
        state=prop.state,
        zip_code=prop.zip_code,
        list_price=prop.list_price,
        estimated_rent=prop.estimated_rent,
        bedrooms=prop.bedrooms,
        bathrooms=prop.bathrooms,
        sqft=prop.sqft,
        property_type=prop.property_type,
        source=prop.source,
        source_url=prop.source_url,
        overall_score=prop.overall_score,
        cash_flow=prop.cash_flow,
        cash_on_cash=prop.cash_on_cash,
        cap_rate=prop.cap_rate,
        pipeline_status=prop.pipeline_status or "analyzed",
        is_favorite=prop.is_favorite or False,
        notes=prop.notes,
        created_at=prop.created_at,
        updated_at=prop.updated_at,
    )


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

    return SavedPropertyResponse(
        id=prop.id,
        address=prop.address,
        city=prop.city,
        state=prop.state,
        zip_code=prop.zip_code,
        list_price=prop.list_price,
        estimated_rent=prop.estimated_rent,
        bedrooms=prop.bedrooms,
        bathrooms=prop.bathrooms,
        sqft=prop.sqft,
        property_type=prop.property_type,
        source=prop.source,
        source_url=prop.source_url,
        overall_score=prop.overall_score,
        cash_flow=prop.cash_flow,
        cash_on_cash=prop.cash_on_cash,
        cap_rate=prop.cap_rate,
        pipeline_status=prop.pipeline_status or "analyzed",
        is_favorite=prop.is_favorite or False,
        notes=prop.notes,
        created_at=prop.created_at,
        updated_at=prop.updated_at,
    )


@router.post("/properties/{property_id}/favorite", response_model=SavedPropertyResponse)
async def toggle_property_favorite(property_id: str):
    """Toggle a property's favorite status."""
    repo = get_repository()
    prop = repo.toggle_property_favorite(property_id)

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    return SavedPropertyResponse(
        id=prop.id,
        address=prop.address,
        city=prop.city,
        state=prop.state,
        zip_code=prop.zip_code,
        list_price=prop.list_price,
        estimated_rent=prop.estimated_rent,
        bedrooms=prop.bedrooms,
        bathrooms=prop.bathrooms,
        sqft=prop.sqft,
        property_type=prop.property_type,
        source=prop.source,
        source_url=prop.source_url,
        overall_score=prop.overall_score,
        cash_flow=prop.cash_flow,
        cash_on_cash=prop.cash_on_cash,
        cap_rate=prop.cap_rate,
        pipeline_status=prop.pipeline_status or "analyzed",
        is_favorite=prop.is_favorite or False,
        notes=prop.notes,
        created_at=prop.created_at,
        updated_at=prop.updated_at,
    )


@router.delete("/properties/{property_id}")
async def delete_property(property_id: str):
    """Delete a saved property."""
    repo = get_repository()
    success = await repo.delete_deal(property_id)

    if not success:
        raise HTTPException(status_code=404, detail="Property not found")

    return {"success": True, "message": "Property deleted"}


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
