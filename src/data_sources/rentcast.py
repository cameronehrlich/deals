"""
RentCast API integration for rent estimates.

RentCast provides rent estimates, rental comps, and market data.
API docs: https://developers.rentcast.io/

Free tier: 50 API calls/month
Paid plans start at $50/month for 500 calls

Get API key at: https://app.rentcast.io/app/api
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import httpx

RENTCAST_BASE_URL = "https://api.rentcast.io/v1"


@dataclass
class RentEstimate:
    """Rent estimate from RentCast."""

    # Property info
    address: str
    city: str
    state: str
    zip_code: str
    bedrooms: int
    bathrooms: float
    sqft: Optional[int]
    property_type: str

    # Estimates
    rent_estimate: float
    rent_low: float
    rent_high: float

    # Comparables
    comp_count: int

    # Metadata
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_updated: Optional[datetime] = None


@dataclass
class RentalComp:
    """A comparable rental property."""

    address: str
    city: str
    state: str
    zip_code: str
    bedrooms: int
    bathrooms: float
    sqft: Optional[int]
    rent: float
    distance: float  # miles
    days_on_market: Optional[int] = None
    listed_date: Optional[datetime] = None


class RentCastClient:
    """
    Client for RentCast API.

    Usage:
        client = RentCastClient(api_key="your_key")

        # Get rent estimate
        estimate = await client.get_rent_estimate(
            address="123 Main St",
            city="Indianapolis",
            state="IN",
            zip_code="46201",
            bedrooms=3,
            bathrooms=2,
        )

        # Get rental comps
        comps = await client.get_rental_comps(
            address="123 Main St",
            city="Indianapolis",
            state="IN",
        )
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("RENTCAST_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=30.0)
        self._cache: dict[str, tuple[datetime, RentEstimate]] = {}
        self._cache_ttl = 86400  # 24 hours
        self._calls_remaining: Optional[int] = None

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    @property
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def get_rent_estimate(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        bedrooms: int = 3,
        bathrooms: float = 2,
        sqft: Optional[int] = None,
        property_type: str = "Single Family",
    ) -> Optional[RentEstimate]:
        """
        Get rent estimate for a property.

        Args:
            address: Street address
            city: City name
            state: Two-letter state code
            zip_code: ZIP code
            bedrooms: Number of bedrooms
            bathrooms: Number of bathrooms
            sqft: Square footage (optional but improves accuracy)
            property_type: Property type (Single Family, Condo, etc.)
        """
        # Check cache
        cache_key = f"{address}_{city}_{state}_{bedrooms}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if (datetime.utcnow() - cached_time).seconds < self._cache_ttl:
                return cached_data

        if not self.api_key:
            # Return fallback estimate using HUD FMR
            return await self._fallback_estimate(
                address, city, state, zip_code, bedrooms, bathrooms, sqft, property_type
            )

        try:
            url = f"{RENTCAST_BASE_URL}/avm/rent/long-term"
            params = {
                "address": address,
                "city": city,
                "state": state,
                "zipCode": zip_code,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "propertyType": property_type,
            }

            if sqft:
                params["squareFootage"] = sqft

            headers = {"X-Api-Key": self.api_key}

            response = await self._client.get(url, params=params, headers=headers)

            # Track rate limit
            self._calls_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))

            response.raise_for_status()
            data = response.json()

            result = RentEstimate(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                sqft=sqft,
                property_type=property_type,
                rent_estimate=data.get("rent", 0),
                rent_low=data.get("rentRangeLow", 0),
                rent_high=data.get("rentRangeHigh", 0),
                comp_count=data.get("comparables", 0),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                last_updated=datetime.utcnow(),
            )

            # Cache
            self._cache[cache_key] = (datetime.utcnow(), result)
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print("RentCast rate limit exceeded")
            else:
                print(f"RentCast API error: {e}")
            return await self._fallback_estimate(
                address, city, state, zip_code, bedrooms, bathrooms, sqft, property_type
            )
        except Exception as e:
            print(f"Error getting rent estimate: {e}")
            return await self._fallback_estimate(
                address, city, state, zip_code, bedrooms, bathrooms, sqft, property_type
            )

    async def get_rental_comps(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        bedrooms: Optional[int] = None,
        radius: float = 1.0,  # miles
        limit: int = 10,
    ) -> list[RentalComp]:
        """
        Get rental comparables near an address.

        Args:
            address: Street address
            city: City name
            state: Two-letter state code
            zip_code: ZIP code
            bedrooms: Filter by bedroom count
            radius: Search radius in miles
            limit: Maximum number of comps
        """
        if not self.api_key:
            return []

        try:
            url = f"{RENTCAST_BASE_URL}/listings/rental/long-term"
            params = {
                "address": address,
                "city": city,
                "state": state,
                "zipCode": zip_code,
                "radius": radius,
                "limit": limit,
                "status": "Active",
            }

            if bedrooms:
                params["bedrooms"] = bedrooms

            headers = {"X-Api-Key": self.api_key}

            response = await self._client.get(url, params=params, headers=headers)
            self._calls_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            response.raise_for_status()

            data = response.json()
            comps = []

            for listing in data:
                try:
                    comp = RentalComp(
                        address=listing.get("formattedAddress", ""),
                        city=listing.get("city", city),
                        state=listing.get("state", state),
                        zip_code=listing.get("zipCode", ""),
                        bedrooms=listing.get("bedrooms", 0),
                        bathrooms=listing.get("bathrooms", 0),
                        sqft=listing.get("squareFootage"),
                        rent=listing.get("price", 0),
                        distance=listing.get("distance", 0),
                        days_on_market=listing.get("daysOnMarket"),
                    )
                    comps.append(comp)
                except Exception:
                    continue

            return comps

        except Exception as e:
            print(f"Error getting rental comps: {e}")
            return []

    async def _fallback_estimate(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        bedrooms: int,
        bathrooms: float,
        sqft: Optional[int],
        property_type: str,
    ) -> RentEstimate:
        """
        Fallback rent estimate using HUD FMR data.

        This provides a baseline estimate when RentCast API is unavailable.
        """
        from src.data_sources.hud_fmr import HudFmrLoader

        loader = HudFmrLoader()

        # Try to find FMR for this location
        market_key = f"{city.lower().replace(' ', '_')}_{state.lower()}"
        fmr = loader.get_fmr(market_key)

        if not fmr:
            # Try lookup by state/city
            fmr = await loader.lookup_fmr(state=state, city=city)

        if fmr:
            base_rent = fmr.get_fmr(bedrooms)
        else:
            # National average fallback
            base_rents = {0: 900, 1: 1100, 2: 1300, 3: 1600, 4: 1900}
            base_rent = base_rents.get(bedrooms, 1400)

        # Adjust for bathrooms (rough estimate)
        if bathrooms > 2:
            base_rent = int(base_rent * 1.05)

        # Adjust for size if known
        if sqft:
            sqft_per_br = sqft / max(bedrooms, 1)
            if sqft_per_br > 600:  # Larger than average
                base_rent = int(base_rent * 1.1)
            elif sqft_per_br < 400:  # Smaller than average
                base_rent = int(base_rent * 0.9)

        return RentEstimate(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            sqft=sqft,
            property_type=property_type,
            rent_estimate=base_rent,
            rent_low=int(base_rent * 0.85),
            rent_high=int(base_rent * 1.15),
            comp_count=0,
            last_updated=datetime.utcnow(),
        )

    def get_calls_remaining(self) -> Optional[int]:
        """Get remaining API calls for this month."""
        return self._calls_remaining
