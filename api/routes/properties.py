"""Property search endpoints using pluggable real estate providers."""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from src.data_sources.real_estate_providers import (
    get_provider,
    list_providers,
    PropertyListing,
    ProviderUsage,
)

router = APIRouter()


# Response Models
class PropertyListingResponse(BaseModel):
    """Property listing for API response."""
    property_id: str
    address: str
    city: str
    state: str
    zip_code: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: Optional[int] = None
    property_type: str
    days_on_market: Optional[int] = None
    photos: list[str] = Field(default_factory=list)
    primary_photo: Optional[str] = None
    source: str = "api"
    source_url: Optional[str] = None
    year_built: Optional[int] = None
    price_per_sqft: Optional[float] = None
    hoa_fee: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ApiUsageResponse(BaseModel):
    """API usage statistics."""
    provider: str
    requests_used: int
    requests_limit: int
    requests_remaining: int
    percent_used: float
    warning: Optional[str] = None
    period: str


class PropertySearchResponse(BaseModel):
    """Response for property search."""
    properties: list[PropertyListingResponse]
    total: int
    api_usage: ApiUsageResponse


class ProviderInfo(BaseModel):
    """Provider information."""
    name: str
    display_name: str
    configured: bool
    is_default: bool = False


class ProvidersResponse(BaseModel):
    """List of available providers."""
    providers: list[ProviderInfo]
    active: str


# Helper functions
def _listing_to_response(listing: PropertyListing) -> PropertyListingResponse:
    """Convert PropertyListing to response model."""
    return PropertyListingResponse(
        property_id=listing.property_id,
        address=listing.address,
        city=listing.city,
        state=listing.state,
        zip_code=listing.zip_code,
        price=listing.price,
        bedrooms=listing.bedrooms,
        bathrooms=listing.bathrooms,
        sqft=listing.sqft,
        property_type=listing.property_type,
        days_on_market=listing.days_on_market,
        photos=listing.photos,
        primary_photo=listing.primary_photo,
        source=listing.provider,
        source_url=listing.source_url,
        year_built=listing.year_built,
        price_per_sqft=listing.price_per_sqft,
        hoa_fee=listing.hoa_fee,
        latitude=listing.latitude,
        longitude=listing.longitude,
    )


def _usage_to_response(usage: ProviderUsage) -> ApiUsageResponse:
    """Convert ProviderUsage to response model."""
    return ApiUsageResponse(
        provider=usage.provider_name,
        requests_used=usage.requests_used,
        requests_limit=usage.requests_limit,
        requests_remaining=usage.requests_remaining,
        percent_used=round(usage.percent_used, 1),
        warning=usage.warning,
        period=usage.period,
    )


# Endpoints
@router.get("/search", response_model=PropertySearchResponse)
async def search_properties(
    location: str = Query(..., description="Location: 'City, ST' or zip code"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price"),
    min_price: Optional[int] = Query(None, ge=0, description="Minimum price"),
    min_beds: Optional[int] = Query(None, ge=0, description="Minimum bedrooms"),
    min_baths: Optional[int] = Query(None, ge=0, description="Minimum bathrooms"),
    property_type: Optional[str] = Query(None, description="Property type filter"),
    limit: int = Query(20, ge=1, le=42, description="Max results"),
):
    """
    Search for-sale properties.

    Uses the configured real estate provider to search listings.
    Location can be 'City, ST' format (e.g., 'Miami, FL') or a zip code.
    """
    provider = get_provider()

    if not provider.is_configured:
        raise HTTPException(
            status_code=503,
            detail=f"{provider.display_name} not configured. Set RAPIDAPI_KEY environment variable.",
        )

    usage = provider.get_usage()
    if usage.requests_remaining <= 0:
        return PropertySearchResponse(
            properties=[],
            total=0,
            api_usage=_usage_to_response(usage),
        )

    try:
        properties = await provider.search_properties(
            location=location,
            max_price=max_price,
            min_price=min_price,
            min_beds=min_beds,
            min_baths=min_baths,
            property_type=property_type,
            limit=limit,
        )

        usage = provider.get_usage()

        # Property types to exclude (mobile homes, manufactured, land)
        excluded_types = {"mobile_home", "manufactured", "land", "other"}

        # Minimum price to filter out obvious data errors (land lots, auction starting bids)
        min_valid_price = 10000

        # Filter out properties with missing required fields, excluded types, or suspiciously low prices
        valid_properties = [
            p for p in properties
            if p.address and p.city and p.state and p.zip_code
            and p.property_type not in excluded_types
            and p.price >= min_valid_price
        ]

        return PropertySearchResponse(
            properties=[_listing_to_response(p) for p in valid_properties],
            total=len(valid_properties),
            api_usage=_usage_to_response(usage),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await provider.close()


@router.get("/usage", response_model=ApiUsageResponse)
async def get_api_usage():
    """
    Get current API usage statistics.

    Returns request count, limits, and warning status.
    Does not consume an API request.
    """
    provider = get_provider()
    usage = provider.get_usage()
    return _usage_to_response(usage)


@router.get("/providers", response_model=ProvidersResponse)
async def get_providers():
    """
    List available real estate data providers.

    Returns all registered providers with their configuration status.
    """
    providers = list_providers()
    active_provider = get_provider()

    return ProvidersResponse(
        providers=[ProviderInfo(**p) for p in providers],
        active=active_provider.name,
    )
