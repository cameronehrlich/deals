"""
US Real Estate API integration via RapidAPI.

Provides access to live property listings from Zillow, Redfin, Realtor, and OpenDoor.
API docs: https://rapidapi.com/datascraper/api/us-real-estate

Free tier: 300 requests/month
Paid tiers: Pro ($9/5k), Ultra ($29/40k), Mega ($99/200k)
"""

import os
import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
import httpx

BASE_URL = "https://us-real-estate.p.rapidapi.com"

# Cache TTLs in seconds
CACHE_TTL = {
    "property_search": 3600,      # 1 hour - listings change often
    "property_detail": 86400,     # 24 hours - details stable
    "home_estimate": 86400,       # 24 hours - estimates stable
    "sold_homes": 86400,          # 24 hours - historical data
    "rentals": 3600,              # 1 hour - rental market moves fast
}

# Usage tracking file
USAGE_FILE = Path(__file__).parent.parent.parent / ".api_usage.json"


@dataclass
class PropertyListing:
    """Property listing from US Real Estate API."""
    property_id: str
    address: str
    city: str
    state: str
    zip_code: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: Optional[int]
    property_type: str
    days_on_market: Optional[int]
    photos: list[str] = field(default_factory=list)
    source: str = "us_real_estate_api"
    source_url: Optional[str] = None
    year_built: Optional[int] = None
    lot_sqft: Optional[int] = None
    price_per_sqft: Optional[float] = None
    status: str = "for_sale"


@dataclass
class PropertyDetail:
    """Detailed property information."""
    property_id: str
    address: str
    city: str
    state: str
    zip_code: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: Optional[int]
    property_type: str
    year_built: Optional[int]
    lot_sqft: Optional[int]
    stories: Optional[int]
    description: Optional[str]
    features: list[str] = field(default_factory=list)
    photos: list[str] = field(default_factory=list)
    price_history: list[dict] = field(default_factory=list)
    tax_history: list[dict] = field(default_factory=list)
    schools: list[dict] = field(default_factory=list)
    estimated_rent: Optional[float] = None
    hoa_fee: Optional[float] = None
    annual_tax: Optional[float] = None


@dataclass
class RentalListing:
    """Rental listing for rent comps."""
    property_id: str
    address: str
    city: str
    state: str
    zip_code: str
    rent: float
    bedrooms: int
    bathrooms: float
    sqft: Optional[int]
    property_type: str
    days_on_market: Optional[int] = None


@dataclass
class SoldProperty:
    """Recently sold property for market analysis."""
    property_id: str
    address: str
    city: str
    state: str
    zip_code: str
    sold_price: float
    list_price: Optional[float]
    bedrooms: int
    bathrooms: float
    sqft: Optional[int]
    sold_date: Optional[str]
    days_on_market: Optional[int]


@dataclass
class ApiUsage:
    """API usage tracking."""
    requests_used: int
    requests_limit: int
    month: str  # YYYY-MM format
    last_request: Optional[str] = None

    @property
    def requests_remaining(self) -> int:
        return max(0, self.requests_limit - self.requests_used)

    @property
    def percent_used(self) -> float:
        return (self.requests_used / self.requests_limit) * 100 if self.requests_limit > 0 else 0

    @property
    def warning_level(self) -> Optional[str]:
        """Return warning level based on usage."""
        if self.percent_used >= 100:
            return "limit_reached"
        elif self.percent_used >= 80:
            return "approaching_limit"
        return None

    def to_dict(self) -> dict:
        return {
            "requests_used": self.requests_used,
            "requests_limit": self.requests_limit,
            "requests_remaining": self.requests_remaining,
            "percent_used": round(self.percent_used, 1),
            "warning": self.warning_level,
            "month": self.month,
        }


class USRealEstateClient:
    """
    US Real Estate API client via RapidAPI.

    Features:
    - Request tracking and rate limit enforcement
    - Response caching (1-24hr TTL)
    - Graceful error handling
    - Usage statistics

    Usage:
        client = USRealEstateClient()

        # Search for properties
        properties = await client.search_properties(
            city="Indianapolis",
            state_code="IN",
            max_price=300000,
            min_beds=3
        )

        # Get property details
        detail = await client.get_property_detail(property_id="12345")

        # Check usage
        usage = client.get_usage()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_host: Optional[str] = None,
        monthly_limit: int = 300,
    ):
        self.api_key = api_key or os.environ.get("RAPIDAPI_KEY", "")
        self.api_host = api_host or os.environ.get("RAPIDAPI_HOST", "us-real-estate.p.rapidapi.com")
        self.monthly_limit = monthly_limit
        self._client = httpx.AsyncClient(timeout=30.0)
        self._cache: dict[str, tuple[datetime, any]] = {}
        self._usage = self._load_usage()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    @property
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    @property
    def headers(self) -> dict:
        """Request headers for RapidAPI."""
        return {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host,
        }

    # -------------------------------------------------------------------------
    # Usage Tracking
    # -------------------------------------------------------------------------

    def _load_usage(self) -> ApiUsage:
        """Load usage from file or create new."""
        current_month = datetime.now().strftime("%Y-%m")

        if USAGE_FILE.exists():
            try:
                with open(USAGE_FILE) as f:
                    data = json.load(f)
                    # Reset if new month
                    if data.get("month") != current_month:
                        return ApiUsage(
                            requests_used=0,
                            requests_limit=self.monthly_limit,
                            month=current_month,
                        )
                    return ApiUsage(
                        requests_used=data.get("requests_used", 0),
                        requests_limit=data.get("requests_limit", self.monthly_limit),
                        month=data.get("month", current_month),
                        last_request=data.get("last_request"),
                    )
            except Exception:
                pass

        return ApiUsage(
            requests_used=0,
            requests_limit=self.monthly_limit,
            month=current_month,
        )

    def _save_usage(self):
        """Persist usage to file."""
        try:
            with open(USAGE_FILE, "w") as f:
                json.dump({
                    "requests_used": self._usage.requests_used,
                    "requests_limit": self._usage.requests_limit,
                    "month": self._usage.month,
                    "last_request": self._usage.last_request,
                }, f)
        except Exception as e:
            print(f"Warning: Could not save API usage: {e}")

    def _increment_usage(self):
        """Increment request counter."""
        current_month = datetime.now().strftime("%Y-%m")
        if self._usage.month != current_month:
            # New month, reset counter
            self._usage = ApiUsage(
                requests_used=1,
                requests_limit=self.monthly_limit,
                month=current_month,
                last_request=datetime.now().isoformat(),
            )
        else:
            self._usage.requests_used += 1
            self._usage.last_request = datetime.now().isoformat()
        self._save_usage()

    def get_usage(self) -> ApiUsage:
        """Get current usage statistics."""
        return self._usage

    def can_make_request(self) -> bool:
        """Check if we can make another request."""
        return self._usage.requests_remaining > 0

    # -------------------------------------------------------------------------
    # Caching
    # -------------------------------------------------------------------------

    def _cache_key(self, endpoint: str, params: dict) -> str:
        """Generate cache key from endpoint and params."""
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(f"{endpoint}:{param_str}".encode()).hexdigest()

    def _get_cached(self, key: str, ttl_type: str) -> Optional[any]:
        """Get cached response if still valid."""
        if key not in self._cache:
            return None

        cached_time, data = self._cache[key]
        ttl = CACHE_TTL.get(ttl_type, 3600)

        if datetime.now() - cached_time < timedelta(seconds=ttl):
            return data
        else:
            del self._cache[key]
            return None

    def _set_cached(self, key: str, data: any):
        """Cache a response."""
        self._cache[key] = (datetime.now(), data)

    # -------------------------------------------------------------------------
    # API Methods
    # -------------------------------------------------------------------------

    async def _request(
        self,
        endpoint: str,
        params: dict,
        cache_type: str,
    ) -> Optional[dict]:
        """Make API request with caching and usage tracking."""
        if not self.has_api_key:
            print("US Real Estate API key not configured")
            return None

        # Check cache
        cache_key = self._cache_key(endpoint, params)
        cached = self._get_cached(cache_key, cache_type)
        if cached is not None:
            return cached

        # Check rate limit
        if not self.can_make_request():
            print(f"US Real Estate API limit reached ({self._usage.requests_used}/{self._usage.requests_limit})")
            return None

        try:
            url = f"{BASE_URL}{endpoint}"
            response = await self._client.get(url, params=params, headers=self.headers)
            self._increment_usage()

            if response.status_code == 429:
                print("US Real Estate API rate limited")
                return None

            response.raise_for_status()
            data = response.json()

            # Check for error status in response body (RapidAPI quirk)
            if isinstance(data, dict):
                status = data.get("status")
                if status and status != 200:
                    msg = data.get("message", "Unknown error")
                    print(f"US Real Estate API error (status {status}): {msg[:100]}")
                    return None

            # Cache successful response
            self._set_cached(cache_key, data)
            return data

        except httpx.HTTPStatusError as e:
            print(f"US Real Estate API error: {e.response.status_code}")
            return None
        except Exception as e:
            print(f"US Real Estate API request failed: {e}")
            return None

    async def search_properties(
        self,
        city: str,
        state_code: str,
        max_price: Optional[int] = None,
        min_price: Optional[int] = None,
        min_beds: Optional[int] = None,
        min_baths: Optional[int] = None,
        property_type: Optional[str] = None,
        sort: str = "newest",
        limit: int = 20,
        offset: int = 0,
    ) -> list[PropertyListing]:
        """
        Search for-sale properties in a market.

        Args:
            city: City name (e.g., "Indianapolis")
            state_code: Two-letter state code (e.g., "IN")
            max_price: Maximum listing price
            min_price: Minimum listing price
            min_beds: Minimum bedrooms
            min_baths: Minimum bathrooms
            property_type: "single_family", "multi_family", "condo", "townhouse"
            sort: "newest", "price_low", "price_high"
            limit: Max results (up to 50)
            offset: Pagination offset

        Returns:
            List of PropertyListing objects
        """
        params = {
            "city": city,
            "state_code": state_code,
            "sort": sort,
            "limit": min(limit, 50),
            "offset": offset,
        }

        if max_price:
            params["price_max"] = max_price
        if min_price:
            params["price_min"] = min_price
        if min_beds:
            params["beds_min"] = min_beds
        if min_baths:
            params["baths_min"] = min_baths
        if property_type:
            params["property_type"] = property_type

        data = await self._request("/v3/for-sale", params, "property_search")

        if not data:
            return []

        properties = []
        home_search = data.get("data", {}).get("home_search")
        if not home_search:
            print("US Real Estate API returned no home_search data")
            return []
        results = home_search.get("results", [])

        for item in results:
            try:
                location = item.get("location", {})
                address = location.get("address", {})
                description = item.get("description", {})

                prop = PropertyListing(
                    property_id=str(item.get("property_id", "")),
                    address=address.get("line", ""),
                    city=address.get("city", city),
                    state=address.get("state_code", state_code),
                    zip_code=address.get("postal_code", ""),
                    price=item.get("list_price", 0),
                    bedrooms=description.get("beds", 0) or 0,
                    bathrooms=description.get("baths", 0) or 0,
                    sqft=description.get("sqft"),
                    property_type=description.get("type", "single_family"),
                    days_on_market=item.get("list_date_dom"),
                    photos=[p.get("href", "") for p in item.get("photos", [])[:5]],
                    year_built=description.get("year_built"),
                    lot_sqft=description.get("lot_sqft"),
                    price_per_sqft=item.get("price_per_sqft"),
                    source_url=item.get("permalink"),
                )
                properties.append(prop)
            except Exception as e:
                print(f"Error parsing property: {e}")
                continue

        return properties

    async def get_property_detail(self, property_id: str) -> Optional[PropertyDetail]:
        """
        Get full property details.

        Args:
            property_id: Property ID from search results

        Returns:
            PropertyDetail object or None
        """
        params = {"property_id": property_id}
        data = await self._request("/v3/property-detail", params, "property_detail")

        if not data:
            return None

        try:
            home = data.get("data", {}).get("home", {})
            location = home.get("location", {})
            address = location.get("address", {})
            description = home.get("description", {})

            # Extract features
            features = []
            for feature_group in description.get("features", []):
                features.extend(feature_group.get("text", []))

            # Extract price history
            price_history = []
            for event in home.get("property_history", []):
                if event.get("event_name") in ["Listed", "Sold", "Price Changed"]:
                    price_history.append({
                        "date": event.get("date"),
                        "event": event.get("event_name"),
                        "price": event.get("price"),
                    })

            # Extract tax history
            tax_history = []
            for tax in home.get("tax_history", []):
                tax_history.append({
                    "year": tax.get("year"),
                    "tax": tax.get("tax"),
                    "assessment": tax.get("assessment", {}).get("total"),
                })

            return PropertyDetail(
                property_id=property_id,
                address=address.get("line", ""),
                city=address.get("city", ""),
                state=address.get("state_code", ""),
                zip_code=address.get("postal_code", ""),
                price=home.get("list_price", 0),
                bedrooms=description.get("beds", 0) or 0,
                bathrooms=description.get("baths", 0) or 0,
                sqft=description.get("sqft"),
                property_type=description.get("type", ""),
                year_built=description.get("year_built"),
                lot_sqft=description.get("lot_sqft"),
                stories=description.get("stories"),
                description=description.get("text"),
                features=features[:20],  # Limit features
                photos=[p.get("href", "") for p in home.get("photos", [])[:10]],
                price_history=price_history[:10],
                tax_history=tax_history[:5],
                hoa_fee=home.get("hoa", {}).get("fee"),
                annual_tax=tax_history[0].get("tax") if tax_history else None,
            )

        except Exception as e:
            print(f"Error parsing property detail: {e}")
            return None

    async def get_home_estimate(self, property_id: str) -> Optional[float]:
        """
        Get estimated home value (like Zestimate).

        Args:
            property_id: Property ID

        Returns:
            Estimated value or None
        """
        params = {"property_id": property_id}
        data = await self._request("/for-sale/home-estimate-value", params, "home_estimate")

        if not data:
            return None

        try:
            return data.get("data", {}).get("home", {}).get("estimate", {}).get("estimate")
        except Exception:
            return None

    async def search_rentals(
        self,
        city: str,
        state_code: str,
        min_beds: Optional[int] = None,
        max_beds: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        limit: int = 20,
    ) -> list[RentalListing]:
        """
        Search rental listings for rent comps.

        Args:
            city: City name
            state_code: Two-letter state code
            min_beds: Minimum bedrooms
            max_beds: Maximum bedrooms
            min_price: Minimum rent
            max_price: Maximum rent
            limit: Max results

        Returns:
            List of RentalListing objects
        """
        params = {
            "city": city,
            "state_code": state_code,
            "limit": min(limit, 50),
        }

        if min_beds:
            params["beds_min"] = min_beds
        if max_beds:
            params["beds_max"] = max_beds
        if min_price:
            params["price_min"] = min_price
        if max_price:
            params["price_max"] = max_price

        data = await self._request("/v3/for-rent", params, "rentals")

        if not data:
            return []

        rentals = []
        home_search = data.get("data", {}).get("home_search")
        if not home_search:
            print("US Real Estate API returned no rental data")
            return []
        results = home_search.get("results", [])

        for item in results:
            try:
                location = item.get("location", {})
                address = location.get("address", {})
                description = item.get("description", {})

                rental = RentalListing(
                    property_id=str(item.get("property_id", "")),
                    address=address.get("line", ""),
                    city=address.get("city", city),
                    state=address.get("state_code", state_code),
                    zip_code=address.get("postal_code", ""),
                    rent=item.get("list_price", 0),
                    bedrooms=description.get("beds", 0) or 0,
                    bathrooms=description.get("baths", 0) or 0,
                    sqft=description.get("sqft"),
                    property_type=description.get("type", ""),
                    days_on_market=item.get("list_date_dom"),
                )
                rentals.append(rental)
            except Exception:
                continue

        return rentals

    async def get_sold_homes(
        self,
        city: str,
        state_code: str,
        max_sold_days: int = 90,
        limit: int = 20,
    ) -> list[SoldProperty]:
        """
        Get recently sold properties for market analysis.

        Args:
            city: City name
            state_code: Two-letter state code
            max_sold_days: Maximum days since sold
            limit: Max results

        Returns:
            List of SoldProperty objects
        """
        params = {
            "city": city,
            "state_code": state_code,
            "limit": min(limit, 50),
        }

        data = await self._request("/sold-homes", params, "sold_homes")

        if not data:
            return []

        sold = []
        home_search = data.get("data", {}).get("home_search")
        if not home_search:
            print("US Real Estate API returned no sold homes data")
            return []
        results = home_search.get("results", [])

        for item in results:
            try:
                location = item.get("location", {})
                address = location.get("address", {})
                description = item.get("description", {})

                prop = SoldProperty(
                    property_id=str(item.get("property_id", "")),
                    address=address.get("line", ""),
                    city=address.get("city", city),
                    state=address.get("state_code", state_code),
                    zip_code=address.get("postal_code", ""),
                    sold_price=description.get("sold_price", 0),
                    list_price=item.get("list_price"),
                    bedrooms=description.get("beds", 0) or 0,
                    bathrooms=description.get("baths", 0) or 0,
                    sqft=description.get("sqft"),
                    sold_date=description.get("sold_date"),
                    days_on_market=item.get("list_date_dom"),
                )
                sold.append(prop)
            except Exception:
                continue

        return sold

    async def estimate_rent_from_comps(
        self,
        city: str,
        state_code: str,
        bedrooms: int,
    ) -> Optional[dict]:
        """
        Estimate rent based on rental comps.

        Args:
            city: City name
            state_code: State code
            bedrooms: Number of bedrooms

        Returns:
            Dict with estimate, low, high, comp_count
        """
        rentals = await self.search_rentals(
            city=city,
            state_code=state_code,
            min_beds=bedrooms,
            max_beds=bedrooms,
            limit=20,
        )

        if not rentals:
            return None

        rents = [r.rent for r in rentals if r.rent > 0]
        if not rents:
            return None

        rents.sort()
        median = rents[len(rents) // 2]

        return {
            "estimate": median,
            "low": rents[0],
            "high": rents[-1],
            "comp_count": len(rents),
            "source": "us_real_estate_api",
        }

    # -------------------------------------------------------------------------
    # Location Data Methods
    # -------------------------------------------------------------------------

    async def get_noise_score(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[dict]:
        """
        Get noise assessment for a location.

        Args:
            latitude: Property latitude
            longitude: Property longitude

        Returns:
            Dict with noise_score (0-100), noise_categories, description
        """
        params = {
            "lat": latitude,
            "lng": longitude,
        }

        data = await self._request("/location/noise-score", params, "property_detail")

        if not data:
            return None

        try:
            noise_data = data.get("data", {})

            # Extract noise scores by category
            categories = {}
            overall_score = None

            for category in noise_data.get("noise_categories", []):
                cat_name = category.get("type", "unknown")
                cat_score = category.get("score")
                categories[cat_name] = cat_score

            overall_score = noise_data.get("noise_score")

            # Determine description based on score
            description = "Unknown"
            if overall_score is not None:
                if overall_score >= 80:
                    description = "Very Quiet"
                elif overall_score >= 60:
                    description = "Quiet"
                elif overall_score >= 40:
                    description = "Moderate"
                elif overall_score >= 20:
                    description = "Noisy"
                else:
                    description = "Very Noisy"

            return {
                "noise_score": overall_score,
                "description": description,
                "categories": categories,
                "latitude": latitude,
                "longitude": longitude,
            }
        except Exception as e:
            print(f"Error parsing noise score: {e}")
            return None

    async def get_schools(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float = 5.0,
    ) -> list[dict]:
        """
        Get schools near a location.

        Args:
            latitude: Property latitude
            longitude: Property longitude
            radius_miles: Search radius in miles

        Returns:
            List of school dicts with name, rating, distance, grades, type
        """
        params = {
            "lat": latitude,
            "lng": longitude,
            "radius": radius_miles,
        }

        data = await self._request("/location/schools", params, "property_detail")

        if not data:
            return []

        try:
            schools_data = data.get("data", {}).get("schools", [])
            schools = []

            for school in schools_data[:10]:  # Limit to 10 schools
                schools.append({
                    "name": school.get("name", "Unknown"),
                    "rating": school.get("rating"),  # Usually 1-10
                    "distance_miles": school.get("distance"),
                    "grades": school.get("grades", {}).get("range", ""),
                    "type": school.get("funding_type", ""),  # public/private
                    "student_count": school.get("student_count"),
                })

            return schools
        except Exception as e:
            print(f"Error parsing schools: {e}")
            return []

    async def get_schools_by_zip(self, zip_code: str) -> list[dict]:
        """
        Get schools by postal code.

        Args:
            zip_code: ZIP code

        Returns:
            List of school dicts
        """
        params = {"postal_code": zip_code}
        data = await self._request("/location/schools-by-postal-code", params, "property_detail")

        if not data:
            return []

        try:
            schools_data = data.get("data", {}).get("schools", [])
            schools = []

            for school in schools_data[:10]:
                schools.append({
                    "name": school.get("name", "Unknown"),
                    "rating": school.get("rating"),
                    "grades": school.get("grades", {}).get("range", ""),
                    "type": school.get("funding_type", ""),
                    "student_count": school.get("student_count"),
                })

            return schools
        except Exception as e:
            print(f"Error parsing schools by zip: {e}")
            return []

    async def get_commute_time(
        self,
        from_address: str,
        to_address: str,
        transportation_type: str = "driving",
    ) -> Optional[dict]:
        """
        Calculate commute time between two addresses.

        Args:
            from_address: Starting address
            to_address: Destination address
            transportation_type: "driving", "transit", "walking", "cycling"

        Returns:
            Dict with duration_minutes, distance_miles, transportation_type
        """
        params = {
            "from_address": from_address,
            "to_address": to_address,
            "transportation_type": transportation_type,
        }

        data = await self._request("/location/commute-time", params, "property_detail")

        if not data:
            return None

        try:
            commute_data = data.get("data", {})

            return {
                "duration_minutes": commute_data.get("duration_minutes"),
                "distance_miles": commute_data.get("distance_miles"),
                "transportation_type": transportation_type,
                "from_address": from_address,
                "to_address": to_address,
            }
        except Exception as e:
            print(f"Error parsing commute time: {e}")
            return None

    async def get_location_insights(
        self,
        latitude: float,
        longitude: float,
        zip_code: Optional[str] = None,
    ) -> dict:
        """
        Get comprehensive location insights (noise + schools).

        Args:
            latitude: Property latitude
            longitude: Property longitude
            zip_code: Optional ZIP code for school lookup fallback

        Returns:
            Dict with noise_score, schools
        """
        import asyncio

        # Fetch noise and schools in parallel
        noise_task = self.get_noise_score(latitude, longitude)
        schools_task = self.get_schools(latitude, longitude)

        noise_result, schools_result = await asyncio.gather(
            noise_task, schools_task, return_exceptions=True
        )

        # Handle exceptions
        noise_data = noise_result if not isinstance(noise_result, Exception) else None
        schools_data = schools_result if not isinstance(schools_result, Exception) else []

        # Fallback to ZIP code for schools if coordinate lookup failed
        if not schools_data and zip_code:
            schools_data = await self.get_schools_by_zip(zip_code)

        return {
            "noise": noise_data,
            "schools": schools_data,
        }
