"""
FEMA National Flood Hazard Layer (NFHL) API integration.

Uses the FEMA NFHL ArcGIS REST API to get flood zone data for locations.
API docs: https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer

Free, no API key required, unlimited requests.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import httpx

FEMA_NFHL_BASE_URL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer"
FLOOD_HAZARD_ZONES_LAYER = 28


# Flood zone risk levels and descriptions
FLOOD_ZONE_INFO = {
    # High-risk zones (Special Flood Hazard Areas - SFHA)
    "A": {
        "risk": "high",
        "description": "High-risk area (100-year flood zone)",
        "requires_insurance": True,
        "annual_chance": "1%",
    },
    "AE": {
        "risk": "high",
        "description": "High-risk area with base flood elevation",
        "requires_insurance": True,
        "annual_chance": "1%",
    },
    "AH": {
        "risk": "high",
        "description": "High-risk shallow flooding (1-3 feet)",
        "requires_insurance": True,
        "annual_chance": "1%",
    },
    "AO": {
        "risk": "high",
        "description": "High-risk shallow flooding (sheet flow)",
        "requires_insurance": True,
        "annual_chance": "1%",
    },
    "AR": {
        "risk": "high",
        "description": "High-risk area (restoration zone)",
        "requires_insurance": True,
        "annual_chance": "1%",
    },
    "A99": {
        "risk": "high",
        "description": "High-risk area (levee under construction)",
        "requires_insurance": True,
        "annual_chance": "1%",
    },
    "V": {
        "risk": "high",
        "description": "High-risk coastal zone (wave action)",
        "requires_insurance": True,
        "annual_chance": "1%",
    },
    "VE": {
        "risk": "high",
        "description": "High-risk coastal zone with base flood elevation",
        "requires_insurance": True,
        "annual_chance": "1%",
    },
    # Moderate-risk zones
    "B": {
        "risk": "moderate",
        "description": "Moderate-risk area (500-year flood zone)",
        "requires_insurance": False,
        "annual_chance": "0.2%",
    },
    "X (shaded)": {
        "risk": "moderate",
        "description": "Moderate-risk area (500-year flood zone)",
        "requires_insurance": False,
        "annual_chance": "0.2%",
    },
    "X500": {
        "risk": "moderate",
        "description": "Moderate-risk area (500-year flood zone)",
        "requires_insurance": False,
        "annual_chance": "0.2%",
    },
    # Low-risk zones
    "C": {
        "risk": "low",
        "description": "Low-risk area (minimal flood hazard)",
        "requires_insurance": False,
        "annual_chance": "<0.2%",
    },
    "X": {
        "risk": "low",
        "description": "Low-risk area (minimal flood hazard)",
        "requires_insurance": False,
        "annual_chance": "<0.2%",
    },
    "X (unshaded)": {
        "risk": "low",
        "description": "Low-risk area (minimal flood hazard)",
        "requires_insurance": False,
        "annual_chance": "<0.2%",
    },
    # Undetermined
    "D": {
        "risk": "undetermined",
        "description": "Area with possible but undetermined flood hazards",
        "requires_insurance": False,
        "annual_chance": "unknown",
    },
}


@dataclass
class FloodZoneResult:
    """Flood zone data for a location."""

    latitude: float
    longitude: float

    # Zone info
    flood_zone: Optional[str] = None
    zone_subtype: Optional[str] = None
    risk_level: Optional[str] = None  # high, moderate, low, undetermined
    description: Optional[str] = None

    # Details
    requires_insurance: bool = False
    annual_chance: Optional[str] = None
    base_flood_elevation: Optional[float] = None
    static_bfe: Optional[float] = None

    # Source data
    firm_panel: Optional[str] = None
    effective_date: Optional[str] = None
    source_citation: Optional[str] = None

    # Metadata
    last_updated: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "flood_zone": self.flood_zone,
            "zone_subtype": self.zone_subtype,
            "risk_level": self.risk_level,
            "description": self.description,
            "requires_insurance": self.requires_insurance,
            "annual_chance": self.annual_chance,
            "base_flood_elevation": self.base_flood_elevation,
            "static_bfe": self.static_bfe,
            "firm_panel": self.firm_panel,
            "effective_date": self.effective_date,
            "source_citation": self.source_citation,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class FEMAFloodClient:
    """
    Client for FEMA National Flood Hazard Layer (NFHL) API.

    Uses the ArcGIS REST API to query flood zones by coordinates.
    Free, no API key required.

    Usage:
        client = FEMAFloodClient()

        # Get flood zone for a location
        result = await client.get_flood_zone(
            latitude=40.7128,
            longitude=-74.0060,
        )

        print(f"Flood Zone: {result.flood_zone}")
        print(f"Risk Level: {result.risk_level}")
        print(f"Requires Insurance: {result.requires_insurance}")
    """

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        self._cache: dict[str, tuple[datetime, FloodZoneResult]] = {}
        self._cache_ttl = 2592000  # 30 days (flood zones rarely change)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def _get_cache_key(self, latitude: float, longitude: float) -> str:
        """Generate cache key from coordinates (rounded for nearby hits)."""
        # Round to 5 decimal places (~1 meter precision)
        return f"{round(latitude, 5)}_{round(longitude, 5)}"

    def _get_zone_info(self, zone_code: str) -> dict:
        """Get zone information from zone code."""
        # Normalize zone code
        zone_upper = zone_code.upper().strip() if zone_code else ""

        # Check for exact match
        if zone_upper in FLOOD_ZONE_INFO:
            return FLOOD_ZONE_INFO[zone_upper]

        # Check for zone prefix (e.g., "AE" matches "AE-FW")
        for key, info in FLOOD_ZONE_INFO.items():
            if zone_upper.startswith(key.upper()):
                return info

        # Default for unknown zones
        return {
            "risk": "unknown",
            "description": f"Flood zone {zone_code}",
            "requires_insurance": False,
            "annual_chance": "unknown",
        }

    async def get_flood_zone(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[FloodZoneResult]:
        """
        Get flood zone data for a location.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            FloodZoneResult with zone info, or None if request fails
        """
        # Check in-memory cache
        cache_key = self._get_cache_key(latitude, longitude)
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            age = (datetime.utcnow() - cached_time).total_seconds()
            if age < self._cache_ttl:
                return cached_data

        try:
            # Query the Flood Hazard Zones layer (28)
            url = f"{FEMA_NFHL_BASE_URL}/{FLOOD_HAZARD_ZONES_LAYER}/query"
            params = {
                "geometry": f"{longitude},{latitude}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",  # WGS84
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json",
            }

            response = await self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Check for error
            if "error" in data:
                print(f"FEMA NFHL API error: {data['error']}")
                return self._fallback_result(latitude, longitude)

            # Parse features
            features = data.get("features", [])
            if not features:
                # No flood data available - likely minimal risk area
                result = FloodZoneResult(
                    latitude=latitude,
                    longitude=longitude,
                    flood_zone="X",
                    risk_level="low",
                    description="No flood hazard data available (likely minimal risk)",
                    requires_insurance=False,
                    annual_chance="<0.2%",
                    last_updated=datetime.utcnow(),
                )
                self._cache[cache_key] = (datetime.utcnow(), result)
                return result

            # Use the first feature (most specific zone)
            attrs = features[0].get("attributes", {})

            # Extract zone code
            zone_code = attrs.get("FLD_ZONE") or attrs.get("ZONE_SUBTY") or ""
            zone_subtype = attrs.get("ZONE_SUBTY")

            # Get zone info
            zone_info = self._get_zone_info(zone_code)

            # Extract additional data (filter out -9999 no-data values)
            base_flood_elev = attrs.get("BFE_REVERT") or attrs.get("STATIC_BFE")
            if base_flood_elev and base_flood_elev < -1000:
                base_flood_elev = None
            static_bfe = attrs.get("STATIC_BFE")
            if static_bfe and static_bfe < -1000:
                static_bfe = None

            result = FloodZoneResult(
                latitude=latitude,
                longitude=longitude,
                flood_zone=zone_code,
                zone_subtype=zone_subtype,
                risk_level=zone_info["risk"],
                description=zone_info["description"],
                requires_insurance=zone_info["requires_insurance"],
                annual_chance=zone_info["annual_chance"],
                base_flood_elevation=float(base_flood_elev) if base_flood_elev else None,
                static_bfe=float(static_bfe) if static_bfe else None,
                firm_panel=attrs.get("FIRM_PAN"),
                effective_date=attrs.get("EFF_DATE"),
                source_citation=attrs.get("SOURCE_CIT"),
                last_updated=datetime.utcnow(),
            )

            # Cache the result
            self._cache[cache_key] = (datetime.utcnow(), result)
            return result

        except httpx.HTTPStatusError as e:
            print(f"FEMA NFHL API error: {e.response.status_code}")
            return self._fallback_result(latitude, longitude)
        except Exception as e:
            print(f"Error getting flood zone: {e}")
            return self._fallback_result(latitude, longitude)

    def _fallback_result(
        self,
        latitude: float,
        longitude: float,
    ) -> FloodZoneResult:
        """Return empty result when API is unavailable."""
        return FloodZoneResult(
            latitude=latitude,
            longitude=longitude,
            flood_zone=None,
            risk_level="unknown",
            description="Flood zone data unavailable",
            last_updated=datetime.utcnow(),
        )

    async def get_flood_risk_summary(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:
        """
        Get a simplified flood risk summary for UI display.

        Returns a dict with:
        - zone: Flood zone code
        - risk: Risk level (high/moderate/low/unknown)
        - color: Suggested display color
        - insurance_required: Whether flood insurance is required
        - description: Human-readable description
        """
        result = await self.get_flood_zone(latitude, longitude)

        if not result or not result.flood_zone:
            return {
                "zone": "Unknown",
                "risk": "unknown",
                "color": "gray",
                "insurance_required": False,
                "description": "Flood zone data not available",
            }

        # Map risk to color
        risk_colors = {
            "high": "red",
            "moderate": "yellow",
            "low": "green",
            "undetermined": "gray",
            "unknown": "gray",
        }

        return {
            "zone": result.flood_zone,
            "risk": result.risk_level,
            "color": risk_colors.get(result.risk_level, "gray"),
            "insurance_required": result.requires_insurance,
            "description": result.description,
            "annual_chance": result.annual_chance,
        }
