"""
Census Geocoder API client.

Free geocoding service for US addresses - no API key required.
https://geocoding.geo.census.gov/geocoder/

Rate limits: None specified, but be respectful.
"""

import httpx
from typing import Optional
from dataclasses import dataclass


@dataclass
class GeocodingResult:
    """Result from geocoding an address."""
    latitude: float
    longitude: float
    matched_address: str
    confidence: str  # "Exact", "Non_Exact", etc.


class CensusGeocoder:
    """
    US Census Bureau Geocoder client.

    Free service, no API key required. Only works for US addresses.
    """

    BASE_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

    def __init__(self, timeout: float = 10.0):
        self._client = httpx.AsyncClient(timeout=timeout)

    async def geocode(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: Optional[str] = None,
    ) -> Optional[GeocodingResult]:
        """
        Geocode a US address to lat/lon coordinates.

        Args:
            address: Street address (e.g., "123 Main St")
            city: City name
            state: State code (e.g., "AZ")
            zip_code: Optional ZIP code for better accuracy

        Returns:
            GeocodingResult with coordinates, or None if not found
        """
        # Build full address string
        full_address = f"{address}, {city}, {state}"
        if zip_code:
            full_address += f" {zip_code}"

        return await self.geocode_oneline(full_address)

    async def geocode_oneline(self, full_address: str) -> Optional[GeocodingResult]:
        """
        Geocode a full address string.

        Args:
            full_address: Complete address as single string

        Returns:
            GeocodingResult with coordinates, or None if not found
        """
        params = {
            "address": full_address,
            "benchmark": "Public_AR_Current",
            "format": "json",
        }

        try:
            response = await self._client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # Parse response
            result = data.get("result", {})
            matches = result.get("addressMatches", [])

            if not matches:
                print(f"Geocoder: No match found for '{full_address}'")
                return None

            # Use first (best) match
            match = matches[0]
            coords = match.get("coordinates", {})

            latitude = coords.get("y")
            longitude = coords.get("x")

            if latitude is None or longitude is None:
                print(f"Geocoder: Match found but no coordinates for '{full_address}'")
                return None

            return GeocodingResult(
                latitude=latitude,
                longitude=longitude,
                matched_address=match.get("matchedAddress", ""),
                confidence=match.get("tigerLine", {}).get("side", "Unknown"),
            )

        except httpx.TimeoutException:
            print(f"Geocoder: Timeout for '{full_address}'")
            return None
        except httpx.HTTPStatusError as e:
            print(f"Geocoder: HTTP error {e.response.status_code} for '{full_address}'")
            return None
        except Exception as e:
            print(f"Geocoder: Error geocoding '{full_address}': {e}")
            return None

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


# Singleton instance
_geocoder: Optional[CensusGeocoder] = None


def get_geocoder() -> CensusGeocoder:
    """Get or create the geocoder singleton."""
    global _geocoder
    if _geocoder is None:
        _geocoder = CensusGeocoder()
    return _geocoder
