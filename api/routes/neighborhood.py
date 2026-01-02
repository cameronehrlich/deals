"""
Phase 6.2: Neighborhood Scoring API.

Calculates composite neighborhood scores based on multiple data sources.
"""

from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/neighborhood", tags=["neighborhood"])


# ==================== Models ====================

class LocationScore(BaseModel):
    """Individual location score component."""
    score: Optional[int] = Field(None, ge=0, le=100)
    weight: float = Field(default=0.0)
    description: Optional[str] = None
    raw_value: Optional[float] = None


class SchoolSummary(BaseModel):
    """Summary of nearby schools."""
    count: int = 0
    avg_rating: Optional[float] = None
    top_rated: Optional[str] = None
    public_count: int = 0
    private_count: int = 0


class NeighborhoodScore(BaseModel):
    """Composite neighborhood score."""
    # Overall score (0-100)
    overall_score: Optional[int] = Field(None, ge=0, le=100)
    grade: str = Field("N/A", description="A, B, C, D, F grade")

    # Component scores
    walkability: LocationScore = Field(default_factory=LocationScore)
    transit: LocationScore = Field(default_factory=LocationScore)
    bikeability: LocationScore = Field(default_factory=LocationScore)
    schools: LocationScore = Field(default_factory=LocationScore)
    safety: LocationScore = Field(default_factory=LocationScore)  # Inverted noise score
    flood_risk: LocationScore = Field(default_factory=LocationScore)

    # School details
    school_summary: SchoolSummary = Field(default_factory=SchoolSummary)

    # Location info
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    # Data quality
    data_sources_used: list[str] = Field(default_factory=list)
    data_completeness: float = Field(0.0, description="% of data sources available")


# ==================== Scoring Logic ====================

def calculate_school_score(schools: list[dict]) -> tuple[Optional[int], SchoolSummary]:
    """Calculate school score from school data."""
    if not schools:
        return None, SchoolSummary()

    ratings = [s.get("rating") for s in schools if s.get("rating") is not None]
    public_count = sum(1 for s in schools if s.get("type", "").lower() == "public")
    private_count = sum(1 for s in schools if s.get("type", "").lower() == "private")

    # Find top-rated school
    top_rated = None
    if ratings:
        max_rating = max(ratings)
        for s in schools:
            if s.get("rating") == max_rating:
                top_rated = s.get("name")
                break

    summary = SchoolSummary(
        count=len(schools),
        avg_rating=sum(ratings) / len(ratings) if ratings else None,
        top_rated=top_rated,
        public_count=public_count,
        private_count=private_count,
    )

    # Convert rating (1-10) to score (0-100)
    if summary.avg_rating is not None:
        score = int(summary.avg_rating * 10)
        return min(100, max(0, score)), summary

    return None, summary


def calculate_safety_score(noise_data: Optional[dict]) -> Optional[int]:
    """
    Calculate safety score from noise data.
    Lower noise = higher safety score (inverted).
    """
    if not noise_data or noise_data.get("noise_score") is None:
        return None

    noise_score = noise_data["noise_score"]
    # Invert: 100 noise = 0 safety, 0 noise = 100 safety
    safety = 100 - noise_score
    return max(0, min(100, safety))


def calculate_flood_score(flood_zone) -> Optional[int]:
    """Calculate flood risk score from FEMA zone."""
    if not flood_zone:
        return None

    # Handle dict format (e.g., {"zone": "X"}) or string
    if isinstance(flood_zone, dict):
        zone_str = flood_zone.get("zone") or flood_zone.get("flood_zone")
        if not zone_str:
            return None
    else:
        zone_str = str(flood_zone)

    # FEMA zones: X = minimal, A/AE/AH/AO/AR = high, V/VE = very high
    zone_upper = zone_str.upper()

    if zone_upper.startswith("X") or zone_upper in ["B", "C"]:
        return 100  # Minimal risk
    elif zone_upper.startswith("D"):
        return 70  # Undetermined
    elif zone_upper.startswith("A"):
        return 30  # High risk
    elif zone_upper.startswith("V"):
        return 10  # Very high risk (coastal)

    return 50  # Unknown


def calculate_overall_score(scores: dict[str, Optional[int]], weights: dict[str, float]) -> Optional[int]:
    """Calculate weighted average of available scores."""
    total_weight = 0.0
    weighted_sum = 0.0

    for key, score in scores.items():
        if score is not None:
            weight = weights.get(key, 0.0)
            weighted_sum += score * weight
            total_weight += weight

    if total_weight == 0:
        return None

    return int(weighted_sum / total_weight)


def score_to_grade(score: Optional[int]) -> str:
    """Convert score to letter grade."""
    if score is None:
        return "N/A"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


# ==================== Endpoints ====================

@router.get("/score/{property_id}", response_model=NeighborhoodScore)
async def get_neighborhood_score_for_property(property_id: str):
    """
    Get neighborhood score for a saved property.

    Uses cached location data when available.
    """
    from src.db import get_repository

    repo = get_repository()

    # Get the saved property
    saved_property = repo.get_saved_property(property_id)
    if not saved_property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Access attributes directly (SavedPropertyDB is a SQLAlchemy model, not a dict)
    address = saved_property.address
    city = saved_property.city
    state = saved_property.state
    zip_code = saved_property.zip_code
    location_data = saved_property.location_data or {}

    # Extract available data
    walk_score = location_data.get("walk_score")
    transit_score = location_data.get("transit_score")
    bike_score = location_data.get("bike_score")
    noise_data = location_data.get("noise")
    schools = location_data.get("schools", [])
    flood_zone = location_data.get("flood_zone")

    # Calculate component scores
    school_score, school_summary = calculate_school_score(schools)
    safety_score = calculate_safety_score(noise_data)
    flood_score = calculate_flood_score(flood_zone)

    # Collect all scores
    scores = {
        "walkability": walk_score,
        "transit": transit_score,
        "bikeability": bike_score,
        "schools": school_score,
        "safety": safety_score,
        "flood_risk": flood_score,
    }

    # Weights for overall score
    weights = {
        "walkability": 0.15,
        "transit": 0.10,
        "bikeability": 0.05,
        "schools": 0.25,
        "safety": 0.20,
        "flood_risk": 0.25,
    }

    overall = calculate_overall_score(scores, weights)

    # Track data sources
    data_sources = []
    if walk_score is not None:
        data_sources.append("Walk Score")
    if transit_score is not None:
        data_sources.append("Transit Score")
    if bike_score is not None:
        data_sources.append("Bike Score")
    if schools:
        data_sources.append("Schools")
    if noise_data:
        data_sources.append("Noise Score")
    if flood_zone:
        data_sources.append("FEMA Flood")

    completeness = len(data_sources) / 6 * 100  # 6 possible sources

    return NeighborhoodScore(
        overall_score=overall,
        grade=score_to_grade(overall),
        walkability=LocationScore(
            score=walk_score,
            weight=weights["walkability"],
            description=location_data.get("walk_description"),
        ),
        transit=LocationScore(
            score=transit_score,
            weight=weights["transit"],
            description=location_data.get("transit_description"),
        ),
        bikeability=LocationScore(
            score=bike_score,
            weight=weights["bikeability"],
            description=location_data.get("bike_description"),
        ),
        schools=LocationScore(
            score=school_score,
            weight=weights["schools"],
            description=f"{school_summary.count} schools, avg rating {school_summary.avg_rating:.1f}/10" if school_summary.avg_rating else None,
            raw_value=school_summary.avg_rating,
        ),
        safety=LocationScore(
            score=safety_score,
            weight=weights["safety"],
            description=noise_data.get("description") if noise_data else None,
            raw_value=noise_data.get("noise_score") if noise_data else None,
        ),
        flood_risk=LocationScore(
            score=flood_score,
            weight=weights["flood_risk"],
            description=f"FEMA Zone {flood_zone.get('zone', flood_zone) if isinstance(flood_zone, dict) else flood_zone}" if flood_zone else None,
            raw_value=None,
        ),
        school_summary=school_summary,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        data_sources_used=data_sources,
        data_completeness=completeness,
    )


@router.get("/score", response_model=NeighborhoodScore)
async def get_neighborhood_score_by_location(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    zip_code: Optional[str] = Query(None, description="ZIP code for fallback data"),
):
    """
    Get neighborhood score for a location (not a saved property).

    Fetches fresh data from APIs.
    """
    from src.data_sources.walkscore import WalkScoreClient
    from src.data_sources.us_real_estate import USRealEstateClient
    from src.data_sources.fema_flood import FEMAFloodClient
    import asyncio

    walkscore_client = WalkScoreClient()
    us_real_estate_client = USRealEstateClient()
    fema_client = FEMAFloodClient()

    # Fetch all data in parallel
    try:
        walkscore_task = walkscore_client.get_scores("", latitude, longitude)
        location_task = us_real_estate_client.get_location_insights(latitude, longitude, zip_code)
        flood_task = fema_client.get_flood_zone(latitude, longitude)

        walkscore_result, location_result, flood_result = await asyncio.gather(
            walkscore_task, location_task, flood_task,
            return_exceptions=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch location data: {str(e)}")

    # Parse results
    walk_score = None
    transit_score = None
    bike_score = None
    walk_description = None
    transit_description = None
    bike_description = None

    if walkscore_result and not isinstance(walkscore_result, Exception):
        walk_score = walkscore_result.walk_score
        transit_score = walkscore_result.transit_score
        bike_score = walkscore_result.bike_score
        walk_description = walkscore_result.walk_description
        transit_description = walkscore_result.transit_description
        bike_description = walkscore_result.bike_description

    noise_data = None
    schools = []
    if location_result and not isinstance(location_result, Exception):
        noise_data = location_result.get("noise")
        schools = location_result.get("schools", [])

    flood_zone = None
    if flood_result and not isinstance(flood_result, Exception):
        flood_zone = flood_result.get("zone")

    # Calculate scores
    school_score, school_summary = calculate_school_score(schools)
    safety_score = calculate_safety_score(noise_data)
    flood_score = calculate_flood_score(flood_zone)

    scores = {
        "walkability": walk_score,
        "transit": transit_score,
        "bikeability": bike_score,
        "schools": school_score,
        "safety": safety_score,
        "flood_risk": flood_score,
    }

    weights = {
        "walkability": 0.15,
        "transit": 0.10,
        "bikeability": 0.05,
        "schools": 0.25,
        "safety": 0.20,
        "flood_risk": 0.25,
    }

    overall = calculate_overall_score(scores, weights)

    data_sources = []
    if walk_score is not None:
        data_sources.append("Walk Score")
    if transit_score is not None:
        data_sources.append("Transit Score")
    if bike_score is not None:
        data_sources.append("Bike Score")
    if schools:
        data_sources.append("Schools")
    if noise_data:
        data_sources.append("Noise Score")
    if flood_zone:
        data_sources.append("FEMA Flood")

    completeness = len(data_sources) / 6 * 100

    return NeighborhoodScore(
        overall_score=overall,
        grade=score_to_grade(overall),
        walkability=LocationScore(
            score=walk_score,
            weight=weights["walkability"],
            description=walk_description,
        ),
        transit=LocationScore(
            score=transit_score,
            weight=weights["transit"],
            description=transit_description,
        ),
        bikeability=LocationScore(
            score=bike_score,
            weight=weights["bikeability"],
            description=bike_description,
        ),
        schools=LocationScore(
            score=school_score,
            weight=weights["schools"],
            description=f"{school_summary.count} schools, avg rating {school_summary.avg_rating:.1f}/10" if school_summary.avg_rating else None,
            raw_value=school_summary.avg_rating,
        ),
        safety=LocationScore(
            score=safety_score,
            weight=weights["safety"],
            description=noise_data.get("description") if noise_data else None,
            raw_value=noise_data.get("noise_score") if noise_data else None,
        ),
        flood_risk=LocationScore(
            score=flood_score,
            weight=weights["flood_risk"],
            description=f"FEMA Zone {flood_zone}" if flood_zone else None,
        ),
        school_summary=school_summary,
        data_sources_used=data_sources,
        data_completeness=completeness,
    )
