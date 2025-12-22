"""
Property URL parser for Zillow and Redfin listings.

Extracts property data from listing URLs without requiring API access.
Uses web scraping with proper error handling.

Supported sites:
- Zillow (zillow.com)
- Redfin (redfin.com)
- Realtor.com (realtor.com)
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
import httpx

from src.models.property import Property, PropertyType, PropertyStatus


@dataclass
class ParsedProperty:
    """Property data extracted from a URL."""

    # Source
    url: str
    source: str  # zillow, redfin, realtor

    # Core data
    address: str
    city: str
    state: str
    zip_code: str

    # Pricing
    list_price: float
    original_price: Optional[float] = None

    # Property details
    bedrooms: int = 0
    bathrooms: float = 0
    sqft: Optional[int] = None
    lot_size_sqft: Optional[int] = None
    year_built: Optional[int] = None
    property_type: str = "single_family_home"

    # Listing info
    days_on_market: int = 0
    status: str = "active"

    # Estimates
    zestimate: Optional[float] = None
    rent_zestimate: Optional[float] = None
    redfin_estimate: Optional[float] = None

    # Taxes and fees
    annual_taxes: Optional[float] = None
    hoa_fee: Optional[float] = None

    # Geo
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Metadata
    description: Optional[str] = None
    features: list[str] = None
    images: list[str] = None

    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.images is None:
            self.images = []
        # Validate and sanitize values
        self._sanitize()

    def _sanitize(self):
        """Sanitize parsed values to catch obvious parsing errors."""
        # Bedrooms: typically 0-10 for residential
        if self.bedrooms < 0 or self.bedrooms > 20:
            self.bedrooms = 0

        # Bathrooms: typically 0.5-10 for residential
        # Common bug: "3.0" parsed as "30" - detect and fix
        if self.bathrooms > 10:
            # Likely a decimal parsing error (e.g., 30 should be 3.0)
            if self.bathrooms in [10, 15, 20, 25, 30, 35, 40, 45, 50]:
                self.bathrooms = self.bathrooms / 10
            else:
                self.bathrooms = 0  # Invalid, reset

        if self.bathrooms < 0:
            self.bathrooms = 0

        # Sqft: typically 200-20000 for residential
        if self.sqft is not None:
            if self.sqft < 100 or self.sqft > 50000:
                self.sqft = None

        # Year built: reasonable range
        if self.year_built is not None:
            if self.year_built < 1800 or self.year_built > 2030:
                self.year_built = None

        # Days on market: can't be negative
        if self.days_on_market < 0:
            self.days_on_market = 0

        # Price sanity check
        if self.list_price < 0:
            self.list_price = 0

    def to_property(self) -> Property:
        """Convert to Property model."""
        # Map property type
        type_mapping = {
            "single_family_home": PropertyType.SFH,
            "single_family": PropertyType.SFH,
            "house": PropertyType.SFH,
            "condo": PropertyType.CONDO,
            "condominium": PropertyType.CONDO,
            "townhouse": PropertyType.TOWNHOUSE,
            "townhome": PropertyType.TOWNHOUSE,
            "duplex": PropertyType.DUPLEX,
            "triplex": PropertyType.TRIPLEX,
            "fourplex": PropertyType.FOURPLEX,
            "multi_family": PropertyType.MULTI_FAMILY,
        }
        prop_type = type_mapping.get(
            self.property_type.lower().replace("-", "_").replace(" ", "_"),
            PropertyType.SFH
        )

        # Map status
        status_mapping = {
            "active": PropertyStatus.ACTIVE,
            "for_sale": PropertyStatus.ACTIVE,
            "pending": PropertyStatus.PENDING,
            "contingent": PropertyStatus.PENDING,
            "sold": PropertyStatus.SOLD,
            "off_market": PropertyStatus.OFF_MARKET,
        }
        status = status_mapping.get(
            self.status.lower().replace("-", "_").replace(" ", "_"),
            PropertyStatus.ACTIVE
        )

        # Generate ID from URL
        prop_id = f"{self.source}_{hash(self.url) % 1000000:06d}"

        return Property(
            id=prop_id,
            address=self.address,
            city=self.city,
            state=self.state,
            zip_code=self.zip_code,
            latitude=self.latitude,
            longitude=self.longitude,
            list_price=self.list_price,
            original_price=self.original_price,
            estimated_rent=self.rent_zestimate,
            rent_zestimate=self.rent_zestimate,
            property_type=prop_type,
            bedrooms=self.bedrooms,
            bathrooms=self.bathrooms,
            sqft=self.sqft,
            lot_size_sqft=self.lot_size_sqft,
            year_built=self.year_built,
            status=status,
            days_on_market=self.days_on_market,
            source=self.source,
            source_url=self.url,
            annual_taxes=self.annual_taxes,
            hoa_fee=self.hoa_fee,
            description=self.description,
            features=self.features,
            images=self.images[:10] if self.images else [],
        )


class PropertyUrlParser:
    """
    Parser for property listing URLs.

    Usage:
        parser = PropertyUrlParser()

        # Parse a Zillow URL
        property = await parser.parse_url(
            "https://www.zillow.com/homedetails/123-Main-St/12345_zpid/"
        )

        # Convert to Property model
        prop = property.to_property()
    """

    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            follow_redirects=True,
        )

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def detect_source(self, url: str) -> Optional[str]:
        """Detect which site the URL is from."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if "zillow.com" in domain:
            return "zillow"
        elif "redfin.com" in domain:
            return "redfin"
        elif "realtor.com" in domain:
            return "realtor"
        else:
            return None

    async def parse_url(self, url: str) -> Optional[ParsedProperty]:
        """
        Parse a property listing URL.

        Args:
            url: Full URL to a property listing

        Returns:
            ParsedProperty with extracted data, or None if parsing fails
        """
        source = self.detect_source(url)

        if not source:
            raise ValueError(f"Unsupported URL source: {url}")

        try:
            if source == "zillow":
                return await self._parse_zillow(url)
            elif source == "redfin":
                return await self._parse_redfin(url)
            elif source == "realtor":
                return await self._parse_realtor(url)
            else:
                return None
        except Exception as e:
            print(f"Error parsing {source} URL: {e}")
            return None

    async def _fetch_page(self, url: str) -> str:
        """Fetch page content."""
        response = await self._client.get(url)
        response.raise_for_status()
        return response.text

    async def _parse_zillow(self, url: str) -> Optional[ParsedProperty]:
        """Parse Zillow listing URL."""
        html = await self._fetch_page(url)

        # Try to find JSON-LD data first (most reliable)
        json_ld = self._extract_json_ld(html, "SingleFamilyResidence")
        if json_ld:
            result = self._parse_zillow_jsonld(url, json_ld)
            # JSON-LD often missing bathrooms - supplement with HTML parsing
            if result and result.bathrooms == 0:
                html_result = self._parse_zillow_html(url, html)
                if html_result:
                    result.bathrooms = html_result.bathrooms
                    if result.bedrooms == 0:
                        result.bedrooms = html_result.bedrooms
            return result

        # Fallback to regex parsing
        return self._parse_zillow_html(url, html)

    def _extract_json_ld(self, html: str, schema_type: str) -> Optional[dict]:
        """Extract JSON-LD structured data from HTML."""
        import json

        # Find all JSON-LD scripts
        pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                data = json.loads(match)
                # Handle array format
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == schema_type:
                            return item
                elif data.get("@type") == schema_type:
                    return data
                # Handle Zillow's nested structure: RealEstateListing -> offers -> itemOffered
                elif data.get("@type") == "RealEstateListing":
                    item_offered = data.get("offers", {}).get("itemOffered", {})
                    if item_offered.get("@type") == schema_type:
                        # Merge price from offers into itemOffered
                        item_offered["_price"] = data.get("offers", {}).get("price")
                        return item_offered
            except json.JSONDecodeError:
                continue

        return None

    def _parse_zillow_jsonld(self, url: str, data: dict) -> ParsedProperty:
        """Parse Zillow JSON-LD data."""
        address = data.get("address", {})

        # Parse price (check _price from nested structure first, then offers)
        price = data.get("_price") or data.get("offers", {}).get("price", 0)
        if isinstance(price, str):
            price = float(re.sub(r"[^\d.]", "", price) or 0)

        # Parse square footage
        sqft_str = str(data.get("floorSize", {}).get("value", ""))
        sqft = int(float(re.sub(r"[^\d.]", "", sqft_str) or 0)) or None

        # Get bedrooms - try numberOfBedrooms first (correct field), then numberOfRooms as fallback
        bedrooms = data.get("numberOfBedrooms") or data.get("numberOfRooms", 0)

        # Get bathrooms - Zillow often omits this from JSON-LD
        bathrooms = data.get("numberOfBathroomsTotal", 0)

        return ParsedProperty(
            url=url,
            source="zillow",
            address=address.get("streetAddress", ""),
            city=address.get("addressLocality", ""),
            state=address.get("addressRegion", ""),
            zip_code=address.get("postalCode", ""),
            list_price=price,
            bedrooms=int(bedrooms) if bedrooms else 0,
            bathrooms=float(bathrooms) if bathrooms else 0,
            sqft=sqft,
            latitude=float(data.get("geo", {}).get("latitude", 0)) or None,
            longitude=float(data.get("geo", {}).get("longitude", 0)) or None,
            description=data.get("description"),
        )

    def _parse_zillow_html(self, url: str, html: str) -> Optional[ParsedProperty]:
        """Parse Zillow HTML with regex fallback."""
        # Extract from page title
        title_match = re.search(r"<title>([^<]+)</title>", html)
        if not title_match:
            return None

        title = title_match.group(1)

        # Try to extract address from title (format: "123 Main St, City, ST 12345")
        addr_match = re.search(r"(.+?),\s*(.+?),\s*([A-Z]{2})\s*(\d{5})", title)
        if not addr_match:
            return None

        address = addr_match.group(1).strip()
        city = addr_match.group(2).strip()
        state = addr_match.group(3)
        zip_code = addr_match.group(4)

        # Extract price - look for price in structured data first
        price_match = re.search(r'\$[\d,]+', html)
        price = float(re.sub(r"[^\d]", "", price_match.group(0))) if price_match else 0

        # Extract beds/baths - use more specific patterns with word boundaries
        # Look for common formats: "3 bd", "3 beds", "3 Bed", "3bd"
        beds_match = re.search(r'\b(\d{1,2})\s*(?:bd|beds?|bdrm|BR)\b', html, re.IGNORECASE)

        # Look for bath patterns: "2 ba", "2.5 bath", "2 Baths", etc.
        # More restrictive: require 1-2 digits, optional decimal with 1 digit
        baths_match = re.search(r'\b(\d{1,2}(?:\.\d)?)\s*(?:ba|baths?|bathroom)\b', html, re.IGNORECASE)

        beds = int(beds_match.group(1)) if beds_match else 0
        baths = float(baths_match.group(1)) if baths_match else 0

        # Additional validation: if we got unreasonable values, try alternate patterns
        if beds == 0:
            # Try "X bedroom" format
            alt_beds = re.search(r'(\d{1,2})\s*bedroom', html, re.IGNORECASE)
            if alt_beds:
                beds = int(alt_beds.group(1))

        if baths == 0 or baths > 10:
            # Try more specific patterns like "X.X Ba" or "X Full Bath"
            alt_baths = re.search(r'(\d{1,2}(?:\.\d)?)\s*(?:full\s+)?bath', html, re.IGNORECASE)
            if alt_baths:
                baths = float(alt_baths.group(1))
            else:
                baths = 0

        # Extract sqft - require reasonable range (3-5 digits)
        sqft_match = re.search(r'\b([\d,]{3,6})\s*(?:sq\.?\s*ft\.?|sqft|square\s*feet?)\b', html, re.IGNORECASE)
        sqft = int(re.sub(r"[^\d]", "", sqft_match.group(1))) if sqft_match else None

        return ParsedProperty(
            url=url,
            source="zillow",
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            list_price=price,
            bedrooms=beds,
            bathrooms=baths,
            sqft=sqft,
        )

    async def _parse_redfin(self, url: str) -> Optional[ParsedProperty]:
        """Parse Redfin listing URL."""
        html = await self._fetch_page(url)

        # Redfin embeds property data in a script tag
        import json

        # Look for initial data script
        pattern = r'window\.__reactServerState\.InitialContext\s*=\s*({.+?});?\s*</script>'
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            # Try alternate pattern
            pattern = r'"propertyDetails"\s*:\s*({[^}]+})'
            match = re.search(pattern, html)

        if match:
            try:
                data = json.loads(match.group(1))
                return self._parse_redfin_json(url, data)
            except json.JSONDecodeError:
                pass

        # Fallback to HTML parsing
        return self._parse_redfin_html(url, html)

    def _parse_redfin_json(self, url: str, data: dict) -> ParsedProperty:
        """Parse Redfin JSON data."""
        prop_data = data.get("propertyDetails", data)

        return ParsedProperty(
            url=url,
            source="redfin",
            address=prop_data.get("streetAddress", ""),
            city=prop_data.get("city", ""),
            state=prop_data.get("state", ""),
            zip_code=prop_data.get("zip", ""),
            list_price=float(prop_data.get("listingPrice", 0)),
            bedrooms=int(prop_data.get("beds", 0)),
            bathrooms=float(prop_data.get("baths", 0)),
            sqft=prop_data.get("sqFt"),
            lot_size_sqft=prop_data.get("lotSqFt"),
            year_built=prop_data.get("yearBuilt"),
            property_type=prop_data.get("propertyType", "single_family_home"),
            days_on_market=prop_data.get("dom", 0),
            redfin_estimate=prop_data.get("redfinEstimate"),
            latitude=prop_data.get("latitude"),
            longitude=prop_data.get("longitude"),
        )

    def _parse_redfin_html(self, url: str, html: str) -> Optional[ParsedProperty]:
        """Parse Redfin HTML with regex fallback."""
        # Extract address from title
        title_match = re.search(r"<title>([^<]+)</title>", html)
        if not title_match:
            return None

        title = title_match.group(1)
        addr_match = re.search(r"(.+?),\s*(.+?),\s*([A-Z]{2})\s*(\d{5})", title)

        if not addr_match:
            return None

        # Extract price
        price_match = re.search(r'\$[\d,]+', html)
        price = float(re.sub(r"[^\d]", "", price_match.group(0))) if price_match else 0

        # Extract property details with word boundaries for accuracy
        beds_match = re.search(r'\b(\d{1,2})\s*(?:Beds?|BR|Bd)\b', html, re.IGNORECASE)
        baths_match = re.search(r'\b(\d{1,2}(?:\.\d)?)\s*(?:Baths?|BA)\b', html, re.IGNORECASE)
        sqft_match = re.search(r'\b([\d,]{3,6})\s*(?:Sq\.?\s*Ft\.?|SF)\b', html, re.IGNORECASE)

        beds = int(beds_match.group(1)) if beds_match else 0
        baths = float(baths_match.group(1)) if baths_match else 0

        return ParsedProperty(
            url=url,
            source="redfin",
            address=addr_match.group(1).strip(),
            city=addr_match.group(2).strip(),
            state=addr_match.group(3),
            zip_code=addr_match.group(4),
            list_price=price,
            bedrooms=beds,
            bathrooms=baths,
            sqft=int(re.sub(r"[^\d]", "", sqft_match.group(1))) if sqft_match else None,
        )

    async def _parse_realtor(self, url: str) -> Optional[ParsedProperty]:
        """Parse Realtor.com listing URL."""
        html = await self._fetch_page(url)

        # Try JSON-LD first
        json_ld = self._extract_json_ld(html, "SingleFamilyResidence")
        if json_ld:
            return self._parse_realtor_jsonld(url, json_ld)

        # Fallback to HTML parsing similar to Zillow
        return self._parse_zillow_html(url.replace("realtor", "zillow"), html)

    def _parse_realtor_jsonld(self, url: str, data: dict) -> ParsedProperty:
        """Parse Realtor.com JSON-LD data."""
        address = data.get("address", {})

        price_str = str(data.get("offers", {}).get("price", "0"))
        price = float(re.sub(r"[^\d.]", "", price_str) or 0)

        return ParsedProperty(
            url=url,
            source="realtor",
            address=address.get("streetAddress", ""),
            city=address.get("addressLocality", ""),
            state=address.get("addressRegion", ""),
            zip_code=address.get("postalCode", ""),
            list_price=price,
            bedrooms=int(data.get("numberOfRooms", 0)),
            bathrooms=float(data.get("numberOfBathroomsTotal", 0)),
            latitude=float(data.get("geo", {}).get("latitude", 0)) or None,
            longitude=float(data.get("geo", {}).get("longitude", 0)) or None,
        )


async def parse_property_url(url: str) -> Optional[Property]:
    """
    Convenience function to parse a URL and return a Property.

    Usage:
        property = await parse_property_url("https://www.zillow.com/...")
    """
    parser = PropertyUrlParser()
    try:
        parsed = await parser.parse_url(url)
        if parsed:
            return parsed.to_property()
        return None
    finally:
        await parser.close()
