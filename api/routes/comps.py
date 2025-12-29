"""
Phase 6.1: Comparable Sales Analysis API.

Fetches and analyzes comparable sales (comps) for properties.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/comps", tags=["comps"])


# ==================== Models ====================

class ComparableSale(BaseModel):
    """A comparable sale property."""
    property_id: str
    address: str
    city: str
    state: str
    zip_code: str
    sold_price: float
    list_price: Optional[float] = None
    bedrooms: int
    bathrooms: float
    sqft: Optional[int] = None
    sold_date: Optional[str] = None
    days_on_market: Optional[int] = None
    price_per_sqft: Optional[float] = None
    distance_miles: Optional[float] = None


class CompsAnalysis(BaseModel):
    """Analysis of comparable sales."""
    subject_price: float
    subject_sqft: Optional[int] = None
    subject_price_per_sqft: Optional[float] = None

    # Comp statistics
    comp_count: int
    median_sold_price: Optional[float] = None
    median_price_per_sqft: Optional[float] = None
    avg_sold_price: Optional[float] = None
    avg_price_per_sqft: Optional[float] = None
    min_sold_price: Optional[float] = None
    max_sold_price: Optional[float] = None

    # Comparison to market
    price_vs_median: Optional[float] = Field(None, description="% difference from median")
    price_vs_median_psf: Optional[float] = Field(None, description="% difference from median $/sqft")
    price_position: str = Field("unknown", description="above_market, below_market, at_market")

    # Individual comps
    comparables: list[ComparableSale] = []


class CompsRequest(BaseModel):
    """Request for comparable sales."""
    city: str
    state_code: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    sqft_tolerance: float = Field(0.2, description="% tolerance for sqft matching")
    subject_price: Optional[float] = None
    max_results: int = Field(20, ge=1, le=50)


# ==================== Helper Functions ====================

def calculate_median(values: list[float]) -> Optional[float]:
    """Calculate median of a list of values."""
    if not values:
        return None
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n % 2 == 0:
        return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    return sorted_vals[n // 2]


def analyze_comps(
    comps: list[ComparableSale],
    subject_price: float,
    subject_sqft: Optional[int] = None,
) -> CompsAnalysis:
    """Analyze comparable sales and compare to subject property."""
    if not comps:
        return CompsAnalysis(
            subject_price=subject_price,
            subject_sqft=subject_sqft,
            comp_count=0,
            price_position="unknown",
        )

    # Calculate subject price per sqft
    subject_psf = None
    if subject_sqft and subject_sqft > 0:
        subject_psf = subject_price / subject_sqft

    # Extract values for analysis
    sold_prices = [c.sold_price for c in comps if c.sold_price > 0]
    price_per_sqfts = [c.price_per_sqft for c in comps if c.price_per_sqft and c.price_per_sqft > 0]

    # Calculate statistics
    median_price = calculate_median(sold_prices)
    median_psf = calculate_median(price_per_sqfts)
    avg_price = sum(sold_prices) / len(sold_prices) if sold_prices else None
    avg_psf = sum(price_per_sqfts) / len(price_per_sqfts) if price_per_sqfts else None

    # Calculate position relative to market
    price_vs_median = None
    price_vs_median_psf = None
    price_position = "unknown"

    if median_price and median_price > 0:
        price_vs_median = ((subject_price - median_price) / median_price) * 100
        if price_vs_median < -5:
            price_position = "below_market"
        elif price_vs_median > 5:
            price_position = "above_market"
        else:
            price_position = "at_market"

    if subject_psf and median_psf and median_psf > 0:
        price_vs_median_psf = ((subject_psf - median_psf) / median_psf) * 100

    return CompsAnalysis(
        subject_price=subject_price,
        subject_sqft=subject_sqft,
        subject_price_per_sqft=subject_psf,
        comp_count=len(comps),
        median_sold_price=median_price,
        median_price_per_sqft=median_psf,
        avg_sold_price=avg_price,
        avg_price_per_sqft=avg_psf,
        min_sold_price=min(sold_prices) if sold_prices else None,
        max_sold_price=max(sold_prices) if sold_prices else None,
        price_vs_median=round(price_vs_median, 1) if price_vs_median else None,
        price_vs_median_psf=round(price_vs_median_psf, 1) if price_vs_median_psf else None,
        price_position=price_position,
        comparables=comps,
    )


# ==================== Endpoints ====================

@router.get("/sold", response_model=CompsAnalysis)
async def get_comparable_sales(
    city: str = Query(..., description="City name"),
    state_code: str = Query(..., description="Two-letter state code"),
    subject_price: float = Query(..., description="Subject property price"),
    subject_sqft: Optional[int] = Query(None, description="Subject property sqft"),
    bedrooms: Optional[int] = Query(None, description="Filter by bedrooms"),
    min_sqft: Optional[int] = Query(None, description="Minimum sqft"),
    max_sqft: Optional[int] = Query(None, description="Maximum sqft"),
    max_results: int = Query(20, ge=1, le=50),
):
    """
    Get comparable sales for a property.

    Fetches recently sold properties in the same city and calculates
    statistics to help evaluate the subject property's price.
    """
    from src.data_sources.us_real_estate import USRealEstateClient

    client = USRealEstateClient()

    try:
        # Fetch sold homes from API
        sold_homes = await client.get_sold_homes(
            city=city,
            state_code=state_code,
            limit=max_results,
        )

        if not sold_homes:
            return CompsAnalysis(
                subject_price=subject_price,
                subject_sqft=subject_sqft,
                comp_count=0,
                price_position="unknown",
                comparables=[],
            )

        # Convert to ComparableSale models and filter
        comps = []
        for home in sold_homes:
            # Apply filters
            if bedrooms and home.bedrooms != bedrooms:
                continue
            if min_sqft and home.sqft and home.sqft < min_sqft:
                continue
            if max_sqft and home.sqft and home.sqft > max_sqft:
                continue

            # Calculate price per sqft
            price_per_sqft = None
            if home.sqft and home.sqft > 0 and home.sold_price > 0:
                price_per_sqft = round(home.sold_price / home.sqft, 2)

            comp = ComparableSale(
                property_id=home.property_id,
                address=home.address,
                city=home.city,
                state=home.state,
                zip_code=home.zip_code,
                sold_price=home.sold_price,
                list_price=home.list_price,
                bedrooms=home.bedrooms,
                bathrooms=home.bathrooms,
                sqft=home.sqft,
                sold_date=home.sold_date,
                days_on_market=home.days_on_market,
                price_per_sqft=price_per_sqft,
            )
            comps.append(comp)

        # Analyze comps
        analysis = analyze_comps(comps, subject_price, subject_sqft)
        return analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch comps: {str(e)}")


@router.get("/property/{property_id}", response_model=CompsAnalysis)
async def get_comps_for_property(
    property_id: str,
    max_results: int = Query(20, ge=1, le=50),
):
    """
    Get comparable sales for a saved property.

    Automatically uses the saved property's details to find and filter comps.
    """
    from src.db import get_repository
    from src.data_sources.us_real_estate import USRealEstateClient

    repo = get_repository()

    # Get the saved property
    property_data = repo.get_saved_property(property_id)
    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    city = property_data.get("city")
    state = property_data.get("state")
    list_price = property_data.get("list_price")
    sqft = property_data.get("sqft")
    bedrooms = property_data.get("bedrooms")

    if not city or not state:
        raise HTTPException(
            status_code=400,
            detail="Property missing city/state information"
        )

    if not list_price:
        raise HTTPException(
            status_code=400,
            detail="Property missing price information"
        )

    # Calculate sqft tolerance for filtering
    min_sqft = None
    max_sqft = None
    if sqft:
        tolerance = 0.25  # 25% tolerance
        min_sqft = int(sqft * (1 - tolerance))
        max_sqft = int(sqft * (1 + tolerance))

    client = USRealEstateClient()

    try:
        sold_homes = await client.get_sold_homes(
            city=city,
            state_code=state,
            limit=50,  # Fetch more to allow filtering
        )

        if not sold_homes:
            return CompsAnalysis(
                subject_price=list_price,
                subject_sqft=sqft,
                comp_count=0,
                price_position="unknown",
                comparables=[],
            )

        # Convert and filter
        comps = []
        for home in sold_homes:
            # Filter by similarity
            if bedrooms and abs(home.bedrooms - bedrooms) > 1:
                continue
            if min_sqft and home.sqft and home.sqft < min_sqft:
                continue
            if max_sqft and home.sqft and home.sqft > max_sqft:
                continue

            price_per_sqft = None
            if home.sqft and home.sqft > 0 and home.sold_price > 0:
                price_per_sqft = round(home.sold_price / home.sqft, 2)

            comp = ComparableSale(
                property_id=home.property_id,
                address=home.address,
                city=home.city,
                state=home.state,
                zip_code=home.zip_code,
                sold_price=home.sold_price,
                list_price=home.list_price,
                bedrooms=home.bedrooms,
                bathrooms=home.bathrooms,
                sqft=home.sqft,
                sold_date=home.sold_date,
                days_on_market=home.days_on_market,
                price_per_sqft=price_per_sqft,
            )
            comps.append(comp)

            if len(comps) >= max_results:
                break

        # Sort by sold date (most recent first)
        comps.sort(key=lambda x: x.sold_date or "", reverse=True)

        # Analyze
        analysis = analyze_comps(comps, list_price, sqft)
        return analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch comps: {str(e)}")
