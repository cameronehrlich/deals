"""
US Real Estate Listings API provider.

RapidAPI: https://rapidapi.com/apimaker/api/us-real-estate-listings
Free tier: 100 requests/month, 2 req/sec

This provider wraps Realtor.com data and provides reliable property search.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import httpx

from .base import BaseProvider, PropertyListing, PropertyDetail, ProviderUsage


# Usage tracking file
USAGE_FILE = Path(__file__).parent.parent.parent.parent / ".api_usage_listings.json"


class USRealEstateListingsProvider(BaseProvider):
    """
    US Real Estate Listings API provider via RapidAPI.

    Provides access to Realtor.com listings with good reliability.
    """

    name = "us_real_estate_listings"
    display_name = "US Real Estate Listings"

    BASE_URL = "https://us-real-estate-listings.p.rapidapi.com"
    DEFAULT_HOST = "us-real-estate-listings.p.rapidapi.com"
    MONTHLY_LIMIT = 100  # Free tier

    def __init__(
        self,
        api_key: Optional[str] = None,
        monthly_limit: int = MONTHLY_LIMIT,
    ):
        super().__init__()
        self.api_key = api_key or os.environ.get("RAPIDAPI_KEY", "")
        self.monthly_limit = monthly_limit
        self._client = httpx.AsyncClient(timeout=30.0)
        self._usage = self._load_usage()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    @property
    def _headers(self) -> dict:
        return {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.DEFAULT_HOST,
        }

    # -------------------------------------------------------------------------
    # Usage Tracking
    # -------------------------------------------------------------------------

    def _load_usage(self) -> dict:
        """Load usage from file or create new."""
        current_month = datetime.now().strftime("%Y-%m")

        if USAGE_FILE.exists():
            try:
                with open(USAGE_FILE) as f:
                    data = json.load(f)
                    if data.get("month") == current_month:
                        return data
            except Exception:
                pass

        return {
            "requests_used": 0,
            "requests_limit": self.monthly_limit,
            "month": current_month,
        }

    def _save_usage(self):
        """Persist usage to file."""
        try:
            with open(USAGE_FILE, "w") as f:
                json.dump(self._usage, f)
        except Exception as e:
            print(f"Warning: Could not save API usage: {e}")

    def _increment_usage(self):
        """Increment request counter."""
        current_month = datetime.now().strftime("%Y-%m")
        if self._usage.get("month") != current_month:
            self._usage = {
                "requests_used": 1,
                "requests_limit": self.monthly_limit,
                "month": current_month,
            }
        else:
            self._usage["requests_used"] = self._usage.get("requests_used", 0) + 1
        self._save_usage()

    def get_usage(self) -> ProviderUsage:
        return ProviderUsage(
            provider_name=self.display_name,
            requests_used=self._usage.get("requests_used", 0),
            requests_limit=self._usage.get("requests_limit", self.monthly_limit),
            period="monthly",
        )

    def _can_make_request(self) -> bool:
        usage = self.get_usage()
        return usage.requests_remaining > 0

    # -------------------------------------------------------------------------
    # API Methods
    # -------------------------------------------------------------------------

    async def _request(self, endpoint: str, params: dict) -> Optional[dict]:
        """Make API request with usage tracking."""
        if not self.is_configured:
            print(f"{self.display_name}: API key not configured")
            return None

        if not self._can_make_request():
            print(f"{self.display_name}: Monthly limit reached")
            return None

        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = await self._client.get(url, params=params, headers=self._headers)
            self._increment_usage()

            if response.status_code == 429:
                print(f"{self.display_name}: Rate limited (2 req/sec max)")
                return None

            data = response.json()

            # Check for API error in response
            if data.get("status") == "error":
                errors = data.get("errors", [])
                print(f"{self.display_name}: API error - {errors}")
                return None

            return data

        except httpx.ReadTimeout:
            print(f"{self.display_name}: Request timeout")
            return None
        except Exception as e:
            print(f"{self.display_name}: Request failed - {e}")
            return None

    async def search_properties(
        self,
        location: str,
        max_price: Optional[int] = None,
        min_price: Optional[int] = None,
        min_beds: Optional[int] = None,
        min_baths: Optional[int] = None,
        property_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[PropertyListing]:
        """Search for-sale properties."""
        params = {
            "location": location,
            "limit": str(min(limit, 42)),  # Free tier max is 42
        }

        if max_price:
            params["price_max"] = str(max_price)
        if min_price:
            params["price_min"] = str(min_price)
        if min_beds:
            params["beds_min"] = str(min_beds)
        if min_baths:
            params["baths_min"] = str(min_baths)
        if property_type:
            params["type"] = property_type

        data = await self._request("/for-sale", params)

        if not data:
            return []

        listings = data.get("listings", [])
        return [self._parse_listing(item) for item in listings]

    async def get_property_detail(
        self,
        property_id: str,
    ) -> Optional[PropertyDetail]:
        """Get property details by ID."""
        params = {"property_id": property_id}
        data = await self._request("/v2/property", params)

        if not data:
            return None

        return self._parse_detail(data)

    def _parse_listing(self, item: dict) -> PropertyListing:
        """Parse API response into PropertyListing."""
        location = item.get("location", {})
        address = location.get("address", {})
        desc = item.get("description", {})

        # Extract photos
        photos = []
        primary_photo = None
        if item.get("primary_photo", {}).get("href"):
            primary_photo = item["primary_photo"]["href"]
            photos.append(primary_photo)
        for photo in item.get("photos", [])[:10]:
            href = photo.get("href")
            if href and href not in photos:
                photos.append(href)

        price = item.get("list_price", 0) or 0
        sqft = desc.get("sqft")

        return PropertyListing(
            property_id=str(item.get("property_id", "")),
            address=address.get("line", ""),
            city=address.get("city", ""),
            state=address.get("state_code", ""),
            zip_code=address.get("postal_code", ""),
            price=price,
            bedrooms=desc.get("beds", 0) or 0,
            bathrooms=desc.get("baths", 0) or 0,
            sqft=sqft,
            property_type=desc.get("type", "single_family"),
            year_built=desc.get("year_built"),
            lot_sqft=desc.get("lot_sqft"),
            days_on_market=None,  # Not directly available
            photos=photos,
            primary_photo=primary_photo,
            source_url=item.get("href"),
            hoa_fee=item.get("hoa", {}).get("fee") if item.get("hoa") else None,
            price_per_sqft=round(price / sqft, 2) if sqft and price else None,
            provider=self.name,
        )

    def _parse_detail(self, data: dict) -> Optional[PropertyDetail]:
        """Parse API response into PropertyDetail."""
        # The detail endpoint returns similar structure
        # First parse as listing, then add detail fields
        listing = self._parse_listing(data)

        return PropertyDetail(
            **{k: v for k, v in listing.__dict__.items() if k != "raw_data"},
            description=data.get("description", {}).get("text"),
            features=data.get("tags", []),
            last_sold_date=data.get("last_sold_date"),
            last_sold_price=data.get("last_sold_price"),
            agent_name=None,  # Would need to parse advertisers
            agent_phone=None,
            broker_name=data.get("branding", [{}])[0].get("name") if data.get("branding") else None,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
