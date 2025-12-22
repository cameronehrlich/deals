"""
Redfin Data Center integration.

Redfin publishes free market data at:
https://www.redfin.com/news/data-center/

Data includes:
- Median sale price
- Homes sold
- New listings
- Inventory
- Days on market
- Sale-to-list ratio
- Price drops
"""

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import httpx

# Redfin Data Center URLs
REDFIN_BASE_URL = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker"

# Data types available
DATA_TYPES = {
    "metro": "redfin_metro_market_tracker.tsv000.gz",
    "city": "city_market_tracker.tsv000.gz",
    "zip": "zip_code_market_tracker.tsv000.gz",
    "county": "county_market_tracker.tsv000.gz",
}


@dataclass
class RedfinMarketData:
    """Market data from Redfin Data Center."""

    region_name: str
    region_type: str
    state: str
    period_begin: datetime
    period_end: datetime

    # Pricing
    median_sale_price: Optional[float] = None
    median_sale_price_yoy: Optional[float] = None
    median_ppsf: Optional[float] = None
    median_ppsf_yoy: Optional[float] = None
    median_list_price: Optional[float] = None
    median_list_ppsf: Optional[float] = None

    # Volume
    homes_sold: Optional[int] = None
    homes_sold_yoy: Optional[float] = None
    new_listings: Optional[int] = None
    new_listings_yoy: Optional[float] = None
    inventory: Optional[int] = None
    inventory_yoy: Optional[float] = None
    months_of_supply: Optional[float] = None

    # Market dynamics
    median_dom: Optional[int] = None
    median_dom_yoy: Optional[float] = None
    avg_sale_to_list: Optional[float] = None
    pct_sold_above_list: Optional[float] = None
    pct_sold_below_list: Optional[float] = None
    price_drops: Optional[float] = None

    # Pending
    pending_sales: Optional[int] = None
    pending_sales_yoy: Optional[float] = None


class RedfinDataCenter:
    """
    Client for Redfin Data Center public data.

    Usage:
        client = RedfinDataCenter()

        # Get metro-level data
        data = await client.get_metro_data("Indianapolis, IN")

        # Get all metros
        all_metros = await client.get_all_metros()

        # Search by state
        tx_metros = await client.search_metros(state="TX")
    """

    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[datetime, list]] = {}
        self._client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def _fetch_data(self, data_type: str = "metro") -> list[dict]:
        """Fetch and parse Redfin data."""
        cache_key = f"redfin_{data_type}"

        # Check cache
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if (datetime.utcnow() - cached_time).seconds < self.cache_ttl:
                return cached_data

        # Fetch data
        filename = DATA_TYPES.get(data_type, DATA_TYPES["metro"])
        url = f"{REDFIN_BASE_URL}/{filename}"

        try:
            response = await self._client.get(url)
            response.raise_for_status()

            # Decompress if gzipped
            import gzip
            content = gzip.decompress(response.content).decode("utf-8")

            # Parse TSV
            reader = csv.DictReader(io.StringIO(content), delimiter="\t")
            # Normalize column names to lowercase
            data = [{k.lower(): v for k, v in row.items()} for row in reader]

            # Cache
            self._cache[cache_key] = (datetime.utcnow(), data)
            return data

        except Exception as e:
            print(f"Error fetching Redfin data: {e}")
            return []

    def _parse_row(self, row: dict) -> Optional[RedfinMarketData]:
        """Parse a row from the TSV data."""
        try:
            def safe_float(val):
                try:
                    return float(val) if val and val != "" else None
                except (ValueError, TypeError):
                    return None

            def safe_int(val):
                try:
                    return int(float(val)) if val and val != "" else None
                except (ValueError, TypeError):
                    return None

            def parse_date(val):
                try:
                    return datetime.strptime(val, "%Y-%m-%d")
                except (ValueError, TypeError):
                    return datetime.utcnow()

            return RedfinMarketData(
                region_name=row.get("region", "") or row.get("region_name", ""),
                region_type=row.get("region_type", ""),
                state=row.get("state", "") or row.get("state_code", ""),
                period_begin=parse_date(row.get("period_begin")),
                period_end=parse_date(row.get("period_end")),
                median_sale_price=safe_float(row.get("median_sale_price")),
                median_sale_price_yoy=safe_float(row.get("median_sale_price_yoy")),
                median_ppsf=safe_float(row.get("median_ppsf")),
                median_ppsf_yoy=safe_float(row.get("median_ppsf_yoy")),
                median_list_price=safe_float(row.get("median_list_price")),
                median_list_ppsf=safe_float(row.get("median_list_ppsf")),
                homes_sold=safe_int(row.get("homes_sold")),
                homes_sold_yoy=safe_float(row.get("homes_sold_yoy")),
                new_listings=safe_int(row.get("new_listings")),
                new_listings_yoy=safe_float(row.get("new_listings_yoy")),
                inventory=safe_int(row.get("inventory")),
                inventory_yoy=safe_float(row.get("inventory_yoy")),
                months_of_supply=safe_float(row.get("months_of_supply")),
                median_dom=safe_int(row.get("median_dom")),
                median_dom_yoy=safe_float(row.get("median_dom_yoy")),
                avg_sale_to_list=safe_float(row.get("avg_sale_to_list")),
                pct_sold_above_list=safe_float(row.get("sold_above_list")),
                pct_sold_below_list=safe_float(row.get("sold_below_list")),
                price_drops=safe_float(row.get("price_drops")),
                pending_sales=safe_int(row.get("pending_sales")),
                pending_sales_yoy=safe_float(row.get("pending_sales_yoy")),
            )
        except Exception as e:
            print(f"Error parsing row: {e}")
            return None

    async def get_all_metros(self) -> list[RedfinMarketData]:
        """Get data for all metros."""
        data = await self._fetch_data("metro")

        # Get most recent data for each metro
        latest: dict[str, dict] = {}
        for row in data:
            region = row.get("region", "") or row.get("region_name", "")
            period = row.get("period_end", "")
            if region and (region not in latest or period > latest[region].get("period_end", "")):
                latest[region] = row

        results = []
        for row in latest.values():
            parsed = self._parse_row(row)
            if parsed:
                results.append(parsed)

        return results

    async def get_metro_data(self, metro_name: str) -> Optional[RedfinMarketData]:
        """Get data for a specific metro."""
        data = await self._fetch_data("metro")

        # Find matching metro (case-insensitive partial match)
        metro_lower = metro_name.lower()
        matches = [
            row for row in data
            if metro_lower in (row.get("region", "") or row.get("region_name", "")).lower()
        ]

        if not matches:
            return None

        # Get most recent
        matches.sort(key=lambda x: x.get("period_end", ""), reverse=True)
        return self._parse_row(matches[0])

    async def search_metros(
        self,
        state: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> list[RedfinMarketData]:
        """Search metros with filters."""
        all_metros = await self.get_all_metros()

        results = []
        for metro in all_metros:
            # State filter
            if state and metro.state.upper() != state.upper():
                continue

            # Price filters
            if min_price and metro.median_sale_price and metro.median_sale_price < min_price:
                continue
            if max_price and metro.median_sale_price and metro.median_sale_price > max_price:
                continue

            results.append(metro)

        return results

    async def get_market_trends(self, metro_name: str, months: int = 12) -> list[RedfinMarketData]:
        """Get historical trend data for a metro."""
        data = await self._fetch_data("metro")

        # Find matching metro
        metro_lower = metro_name.lower()
        matches = [
            row for row in data
            if metro_lower in row.get("region_name", "").lower()
        ]

        # Sort by date
        matches.sort(key=lambda x: x.get("period_end", ""), reverse=True)

        # Parse and return most recent N months
        results = []
        for row in matches[:months]:
            parsed = self._parse_row(row)
            if parsed:
                results.append(parsed)

        return results
