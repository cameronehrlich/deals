"""
Walk Score API integration (official API).

Walk Score provides walkability, transit, and bike scores for locations.
API docs: https://www.walkscore.com/professional/api.php

Coverage: US, Canada, Australia, New Zealand
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import httpx

WALKSCORE_BASE_URL = "https://api.walkscore.com"


@dataclass
class WalkScoreResult:
    """Walk Score data for a location."""

    # Location
    address: str
    latitude: float
    longitude: float

    # Scores (0-100)
    walk_score: Optional[int] = None
    walk_description: Optional[str] = None

    transit_score: Optional[int] = None
    transit_description: Optional[str] = None

    bike_score: Optional[int] = None
    bike_description: Optional[str] = None

    # Metadata
    last_updated: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "walk_score": self.walk_score,
            "walk_description": self.walk_description,
            "transit_score": self.transit_score,
            "transit_description": self.transit_description,
            "bike_score": self.bike_score,
            "bike_description": self.bike_description,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


# Score descriptions based on Walk Score methodology
WALK_SCORE_DESCRIPTIONS = {
    (90, 100): "Walker's Paradise",
    (70, 89): "Very Walkable",
    (50, 69): "Somewhat Walkable",
    (25, 49): "Car-Dependent",
    (0, 24): "Almost All Errands Require a Car",
}

TRANSIT_SCORE_DESCRIPTIONS = {
    (90, 100): "Excellent Transit",
    (70, 89): "Excellent Transit",
    (50, 69): "Good Transit",
    (25, 49): "Some Transit",
    (0, 24): "Minimal Transit",
}

BIKE_SCORE_DESCRIPTIONS = {
    (90, 100): "Biker's Paradise",
    (70, 89): "Very Bikeable",
    (50, 69): "Bikeable",
    (0, 49): "Somewhat Bikeable",
}


def get_score_description(score: Optional[int], descriptions: dict) -> Optional[str]:
    """Get description for a score value."""
    if score is None:
        return None
    for (low, high), desc in descriptions.items():
        if low <= score <= high:
            return desc
    return None


class WalkScoreClient:
    """
    Client for Walk Score API (official).

    Usage:
        client = WalkScoreClient()

        # Get scores for a location
        result = await client.get_scores(
            address="123 Main St, Seattle, WA 98101",
            latitude=47.6062,
            longitude=-122.3321,
        )

        print(f"Walk Score: {result.walk_score} - {result.walk_description}")
        print(f"Transit Score: {result.transit_score}")
        print(f"Bike Score: {result.bike_score}")
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Walk Score client.

        Args:
            api_key: Walk Score API key. If not provided, uses WALKSCORE_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("WALKSCORE_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=30.0)
        self._cache: dict[str, tuple[datetime, WalkScoreResult]] = {}
        self._cache_ttl = 604800  # 7 days (Walk Scores rarely change)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    @property
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def _get_cache_key(self, latitude: float, longitude: float) -> str:
        """Generate cache key from coordinates (rounded for nearby hits)."""
        # Round to 4 decimal places (~11 meter precision)
        return f"{round(latitude, 4)}_{round(longitude, 4)}"

    async def get_scores(
        self,
        address: str,
        latitude: float,
        longitude: float,
    ) -> Optional[WalkScoreResult]:
        """
        Get Walk Score, Transit Score, and Bike Score for a location.

        Args:
            address: Full street address
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            WalkScoreResult with all available scores, or None if request fails
        """
        # Check cache
        cache_key = self._get_cache_key(latitude, longitude)
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            age = (datetime.utcnow() - cached_time).total_seconds()
            if age < self._cache_ttl:
                return cached_data

        if not self.api_key:
            print("Walk Score API key not configured (set WALKSCORE_API_KEY)")
            return self._fallback_result(address, latitude, longitude)

        try:
            url = f"{WALKSCORE_BASE_URL}/score"
            params = {
                "format": "json",
                "address": address,
                "lat": str(latitude),
                "lon": str(longitude),
                "transit": "1",
                "bike": "1",
                "wsapikey": self.api_key,
            }

            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Check for API error status
            if data.get("status") != 1:
                status_codes = {
                    2: "Score being calculated, try again later",
                    30: "Invalid latitude/longitude",
                    31: "Walk Score API internal error",
                    40: "Invalid API key or address",
                    41: "API quota exceeded",
                    42: "IP address blocked",
                }
                error_msg = status_codes.get(data.get("status"), f"Unknown error: status {data.get('status')}")
                print(f"Walk Score API error: {error_msg}")
                return self._fallback_result(address, latitude, longitude)

            # Parse response
            walk_score = data.get("walkscore")
            transit_score = data.get("transit", {}).get("score") if isinstance(data.get("transit"), dict) else None
            bike_score = data.get("bike", {}).get("score") if isinstance(data.get("bike"), dict) else None

            result = WalkScoreResult(
                address=address,
                latitude=latitude,
                longitude=longitude,
                walk_score=walk_score,
                walk_description=data.get("description") or get_score_description(walk_score, WALK_SCORE_DESCRIPTIONS),
                transit_score=transit_score,
                transit_description=get_score_description(transit_score, TRANSIT_SCORE_DESCRIPTIONS),
                bike_score=bike_score,
                bike_description=get_score_description(bike_score, BIKE_SCORE_DESCRIPTIONS),
                last_updated=datetime.utcnow(),
            )

            # Cache the result
            self._cache[cache_key] = (datetime.utcnow(), result)
            return result

        except httpx.HTTPStatusError as e:
            print(f"Walk Score API error: {e.response.status_code} - {e.response.text}")
            return self._fallback_result(address, latitude, longitude)
        except Exception as e:
            print(f"Error getting Walk Score: {e}")
            return self._fallback_result(address, latitude, longitude)

    def _fallback_result(
        self,
        address: str,
        latitude: float,
        longitude: float,
    ) -> WalkScoreResult:
        """Return empty result when API is unavailable."""
        return WalkScoreResult(
            address=address,
            latitude=latitude,
            longitude=longitude,
            walk_score=None,
            walk_description=None,
            transit_score=None,
            transit_description=None,
            bike_score=None,
            bike_description=None,
            last_updated=datetime.utcnow(),
        )

    async def get_scores_by_address(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: str,
    ) -> Optional[WalkScoreResult]:
        """
        Get Walk Scores by geocoding an address first.

        This method uses a geocoding service to convert the address to coordinates,
        then fetches the Walk Score. Requires the address to be geocodable.

        Args:
            address: Street address
            city: City name
            state: State code
            zip_code: ZIP code

        Returns:
            WalkScoreResult or None
        """
        # Build full address
        full_address = f"{address}, {city}, {state} {zip_code}"

        # For now, we need coordinates passed in
        # TODO: Add geocoding integration (e.g., via US Real Estate API or Google)
        print(f"get_scores_by_address requires lat/lon - use get_scores() instead")
        return None
