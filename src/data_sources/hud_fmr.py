"""
HUD Fair Market Rents (FMR) data loader.

HUD publishes Fair Market Rents annually for all counties and metro areas.
Data available at: https://www.huduser.gov/portal/datasets/fmr.html

FMRs represent the 40th percentile of gross rents for standard quality
rental units, including utilities.
"""

import csv
import io
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import httpx

# HUD FMR data URL (updates annually)
# FY25 URL - check https://www.huduser.gov/portal/datasets/fmr.html for updates
HUD_FMR_URL = "https://www.huduser.gov/portal/datasets/fmr/fmr2025/FY25_FMRs.csv"
# Fallback to FY24 if FY25 not available
HUD_FMR_URL_FALLBACK = "https://www.huduser.gov/portal/datasets/fmr/fmr2024/FY24_FMRs.csv"


@dataclass
class FairMarketRent:
    """Fair Market Rent data for a location."""

    # Location identifiers
    fips_code: str
    cbsa_code: Optional[str]  # Core Based Statistical Area
    metro_name: str
    county_name: str
    state: str

    # FMRs by bedroom count
    fmr_0br: int  # Efficiency
    fmr_1br: int
    fmr_2br: int
    fmr_3br: int
    fmr_4br: int

    # Metadata
    year: int

    @property
    def fmr_by_bedrooms(self) -> dict[int, int]:
        """Get FMR dict keyed by bedroom count."""
        return {
            0: self.fmr_0br,
            1: self.fmr_1br,
            2: self.fmr_2br,
            3: self.fmr_3br,
            4: self.fmr_4br,
        }

    def get_fmr(self, bedrooms: int) -> int:
        """Get FMR for specific bedroom count."""
        if bedrooms <= 0:
            return self.fmr_0br
        elif bedrooms == 1:
            return self.fmr_1br
        elif bedrooms == 2:
            return self.fmr_2br
        elif bedrooms == 3:
            return self.fmr_3br
        else:
            return self.fmr_4br


# Embedded FMR data for target markets (FY2024)
# This avoids external dependencies for core functionality
EMBEDDED_FMR_DATA = {
    # Indianapolis-Carmel-Anderson, IN
    "indianapolis_in": FairMarketRent(
        fips_code="18097",
        cbsa_code="26900",
        metro_name="Indianapolis-Carmel-Anderson",
        county_name="Marion",
        state="IN",
        fmr_0br=844,
        fmr_1br=941,
        fmr_2br=1098,
        fmr_3br=1398,
        fmr_4br=1585,
        year=2024,
    ),
    # Cleveland-Elyria, OH
    "cleveland_oh": FairMarketRent(
        fips_code="39035",
        cbsa_code="17460",
        metro_name="Cleveland-Elyria",
        county_name="Cuyahoga",
        state="OH",
        fmr_0br=721,
        fmr_1br=815,
        fmr_2br=977,
        fmr_3br=1247,
        fmr_4br=1355,
        year=2024,
    ),
    # Memphis, TN-MS-AR
    "memphis_tn": FairMarketRent(
        fips_code="47157",
        cbsa_code="32820",
        metro_name="Memphis",
        county_name="Shelby",
        state="TN",
        fmr_0br=781,
        fmr_1br=886,
        fmr_2br=988,
        fmr_3br=1239,
        fmr_4br=1500,
        year=2024,
    ),
    # Birmingham-Hoover, AL
    "birmingham_al": FairMarketRent(
        fips_code="01073",
        cbsa_code="13820",
        metro_name="Birmingham-Hoover",
        county_name="Jefferson",
        state="AL",
        fmr_0br=758,
        fmr_1br=858,
        fmr_2br=969,
        fmr_3br=1237,
        fmr_4br=1354,
        year=2024,
    ),
    # Kansas City, MO-KS
    "kansas_city_mo": FairMarketRent(
        fips_code="29095",
        cbsa_code="28140",
        metro_name="Kansas City",
        county_name="Jackson",
        state="MO",
        fmr_0br=830,
        fmr_1br=950,
        fmr_2br=1147,
        fmr_3br=1508,
        fmr_4br=1713,
        year=2024,
    ),
    # Tampa-St. Petersburg-Clearwater, FL
    "tampa_fl": FairMarketRent(
        fips_code="12057",
        cbsa_code="45300",
        metro_name="Tampa-St. Petersburg-Clearwater",
        county_name="Hillsborough",
        state="FL",
        fmr_0br=1221,
        fmr_1br=1376,
        fmr_2br=1653,
        fmr_3br=2206,
        fmr_4br=2664,
        year=2024,
    ),
    # Phoenix-Mesa-Chandler, AZ
    "phoenix_az": FairMarketRent(
        fips_code="04013",
        cbsa_code="38060",
        metro_name="Phoenix-Mesa-Chandler",
        county_name="Maricopa",
        state="AZ",
        fmr_0br=1098,
        fmr_1br=1195,
        fmr_2br=1425,
        fmr_3br=1985,
        fmr_4br=2392,
        year=2024,
    ),
    # Austin-Round Rock-Georgetown, TX
    "austin_tx": FairMarketRent(
        fips_code="48453",
        cbsa_code="12420",
        metro_name="Austin-Round Rock-Georgetown",
        county_name="Travis",
        state="TX",
        fmr_0br=1199,
        fmr_1br=1350,
        fmr_2br=1616,
        fmr_3br=2155,
        fmr_4br=2615,
        year=2024,
    ),
    # Nashville-Davidson-Murfreesboro-Franklin, TN
    "nashville_tn": FairMarketRent(
        fips_code="47037",
        cbsa_code="34980",
        metro_name="Nashville-Davidson-Murfreesboro-Franklin",
        county_name="Davidson",
        state="TN",
        fmr_0br=1108,
        fmr_1br=1232,
        fmr_2br=1401,
        fmr_3br=1807,
        fmr_4br=2100,
        year=2024,
    ),
    # Houston-The Woodlands-Sugar Land, TX
    "houston_tx": FairMarketRent(
        fips_code="48201",
        cbsa_code="26420",
        metro_name="Houston-The Woodlands-Sugar Land",
        county_name="Harris",
        state="TX",
        fmr_0br=979,
        fmr_1br=1098,
        fmr_2br=1308,
        fmr_3br=1742,
        fmr_4br=2143,
        year=2024,
    ),
    # Miami-Fort Lauderdale-Pompano Beach, FL
    "miami_fl": FairMarketRent(
        fips_code="12086",
        cbsa_code="33100",
        metro_name="Miami-Fort Lauderdale-Pompano Beach",
        county_name="Miami-Dade",
        state="FL",
        fmr_0br=1505,
        fmr_1br=1798,
        fmr_2br=2263,
        fmr_3br=2925,
        fmr_4br=3325,
        year=2024,
    ),
}


class HudFmrLoader:
    """
    Loader for HUD Fair Market Rent data.

    Usage:
        loader = HudFmrLoader()

        # Get FMR for a market
        fmr = loader.get_fmr("indianapolis_in")
        rent_3br = fmr.get_fmr(3)

        # Get FMR by state and county
        fmr = await loader.lookup_fmr(state="IN", county="Marion")

        # Use as rent baseline
        baseline_rent = fmr.get_fmr(bedrooms=3)
    """

    def __init__(self):
        self._fmr_data: dict[str, FairMarketRent] = dict(EMBEDDED_FMR_DATA)
        self._loaded = False
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def get_fmr(self, market_id: str) -> Optional[FairMarketRent]:
        """Get FMR for a market by ID."""
        return self._fmr_data.get(market_id.lower())

    def get_rent_estimate(self, market_id: str, bedrooms: int = 3) -> Optional[int]:
        """Get FMR rent estimate for a market and bedroom count."""
        fmr = self.get_fmr(market_id)
        if fmr:
            return fmr.get_fmr(bedrooms)
        return None

    def get_all_markets(self) -> list[FairMarketRent]:
        """Get all loaded FMR data."""
        return list(self._fmr_data.values())

    async def load_from_hud(self) -> bool:
        """
        Load additional FMR data from HUD website.

        Returns True if successful.
        """
        if self._loaded:
            return True

        # Try primary URL first, then fallback
        urls_to_try = [HUD_FMR_URL, HUD_FMR_URL_FALLBACK]

        for url in urls_to_try:
            try:
                response = await self._client.get(url)
                response.raise_for_status()

                content = response.text
                reader = csv.DictReader(io.StringIO(content))

                for row in reader:
                    try:
                        # Parse the row
                        fmr = self._parse_hud_row(row)
                        if fmr:
                            # Create market key
                            market_key = self._make_market_key(fmr)
                            if market_key:
                                self._fmr_data[market_key] = fmr
                    except Exception:
                        continue

                self._loaded = True
                print(f"Loaded HUD FMR data from {url}")
                return True

            except Exception as e:
                print(f"Failed to load HUD FMR from {url}: {e}")
                continue

        # If all URLs failed, we still have embedded data
        # Mark as loaded to prevent infinite recursion on retry
        self._loaded = True
        print("Could not load HUD FMR data from any URL, using embedded data only")
        return False

    def _parse_hud_row(self, row: dict) -> Optional[FairMarketRent]:
        """Parse a row from HUD CSV."""
        try:
            def safe_int(val):
                try:
                    return int(float(val)) if val else 0
                except (ValueError, TypeError):
                    return 0

            return FairMarketRent(
                fips_code=row.get("fips2010", "") or row.get("fips", ""),
                cbsa_code=row.get("cbsa", "") or row.get("cbsasub", ""),
                metro_name=row.get("metro_name", "") or row.get("areaname", ""),
                county_name=row.get("countyname", "") or row.get("county_name", ""),
                state=row.get("state", "") or row.get("state_alpha", ""),
                fmr_0br=safe_int(row.get("fmr_0", 0) or row.get("fmr0", 0)),
                fmr_1br=safe_int(row.get("fmr_1", 0) or row.get("fmr1", 0)),
                fmr_2br=safe_int(row.get("fmr_2", 0) or row.get("fmr2", 0)),
                fmr_3br=safe_int(row.get("fmr_3", 0) or row.get("fmr3", 0)),
                fmr_4br=safe_int(row.get("fmr_4", 0) or row.get("fmr4", 0)),
                year=2024,
            )
        except Exception:
            return None

    def _make_market_key(self, fmr: FairMarketRent) -> Optional[str]:
        """Create a market key from FMR data."""
        if fmr.metro_name and fmr.state:
            # Extract city name from metro name
            city = fmr.metro_name.split("-")[0].split(",")[0].strip()
            city = city.lower().replace(" ", "_")
            state = fmr.state.lower()
            return f"{city}_{state}"
        return None

    async def lookup_fmr(
        self,
        state: str,
        county: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Optional[FairMarketRent]:
        """
        Look up FMR by location.

        Args:
            state: Two-letter state code
            county: County name (optional)
            city: City name (optional)
        """
        # First try embedded data
        for fmr in self._fmr_data.values():
            if fmr.state.upper() != state.upper():
                continue
            if county and county.lower() not in fmr.county_name.lower():
                continue
            if city and city.lower() not in fmr.metro_name.lower():
                continue
            return fmr

        # Try loading from HUD if not found
        if not self._loaded:
            await self.load_from_hud()
            return await self.lookup_fmr(state, county, city)

        return None
