"""
Census Bureau API client for population and demographic data.

Census Bureau provides free access to population data including:
- Population estimates (annual)
- Population change
- Median household income (by metro/county)

API docs: https://www.census.gov/data/developers.html
No API key required for basic access, but recommended for higher limits.
Register at: https://api.census.gov/data/key_signup.html
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import httpx


# Census API base URLs
CENSUS_BASE_URL = "https://api.census.gov/data"

# Metro area CBSA codes (Core Based Statistical Area)
# These map to the same metros in BLS but use different identifiers
METRO_CBSA_CODES = {
    "indianapolis_in": "26900",
    "cleveland_oh": "17460",
    "memphis_tn": "32820",
    "birmingham_al": "13820",
    "kansas_city_mo": "28140",
    "tampa_fl": "45300",
    "phoenix_az": "38060",
    "austin_tx": "12420",
    "huntsville_al": "26620",
    "dallas_tx": "19100",
    "atlanta_ga": "12060",
    "denver_co": "19740",
    "nashville_tn": "34980",
    "charlotte_nc": "16740",
    "orlando_fl": "36740",
    "raleigh_nc": "39580",
    "san_antonio_tx": "41700",
    "jacksonville_fl": "27260",
    "columbus_oh": "18140",
    "cincinnati_oh": "17140",
    "los_angeles_ca": "31080",
    "san_francisco_ca": "41860",
    "san_diego_ca": "41740",
    "seattle_wa": "42660",
    "las_vegas_nv": "29820",
    "houston_tx": "26420",
    "miami_fl": "33100",
    "chicago_il": "16980",
    "new_york_ny": "35620",
    "boston_ma": "14460",
    "washington_dc": "47900",
    "detroit_mi": "19820",
    "minneapolis_mn": "33460",
    "portland_or": "38900",
    "sacramento_ca": "40900",
    "salt_lake_city_ut": "41620",
    "pittsburgh_pa": "38300",
    "st_louis_mo": "41180",
}


@dataclass
class MetroPopulationData:
    """Population data for a metro area."""

    metro_id: str
    metro_name: Optional[str] = None
    cbsa_code: Optional[str] = None

    # Population
    population: Optional[int] = None
    population_year: Optional[int] = None

    # Population change (calculated from multiple years)
    population_1yr_ago: Optional[int] = None
    population_5yr_ago: Optional[int] = None
    population_growth_1yr: Optional[float] = None  # Percentage
    population_growth_5yr: Optional[float] = None  # Percentage

    # Household income (from ACS)
    median_household_income: Optional[int] = None
    income_year: Optional[int] = None

    # Metadata
    last_updated: Optional[datetime] = None


class CensusClient:
    """
    Client for Census Bureau APIs.

    Usage:
        client = CensusClient()

        # Get metro population data
        data = await client.get_metro_population("phoenix_az")
        print(f"Population: {data.population:,}")
        print(f"Growth 1Y: {data.population_growth_1yr}%")

        # Get income data
        income = await client.get_metro_income("phoenix_az")
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("CENSUS_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=30.0)
        self._cache: dict[str, tuple[datetime, any]] = {}
        self._cache_ttl = 86400 * 7  # 7 days (Census data updates annually)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def _get_cache(self, key: str) -> Optional[any]:
        """Get cached value if not expired."""
        if key in self._cache:
            cached_time, cached_data = self._cache[key]
            age = (datetime.utcnow() - cached_time).total_seconds()
            if age < self._cache_ttl:
                return cached_data
        return None

    def _set_cache(self, key: str, data: any):
        """Set cache value."""
        self._cache[key] = (datetime.utcnow(), data)

    async def get_metro_population(self, metro_id: str) -> Optional[MetroPopulationData]:
        """
        Get population data for a metro area.

        Uses Census American Community Survey (ACS) 1-year estimates.
        ACS provides population (B01003_001E) and is more reliably available than PEP.
        """
        cbsa_code = METRO_CBSA_CODES.get(metro_id.lower())
        if not cbsa_code:
            print(f"Unknown metro for Census: {metro_id}")
            return MetroPopulationData(metro_id=metro_id)

        cache_key = f"census_pop_{metro_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        result = MetroPopulationData(
            metro_id=metro_id,
            cbsa_code=cbsa_code,
            last_updated=datetime.utcnow(),
        )

        try:
            current_year = datetime.utcnow().year
            # ACS 1-year data typically has 1-2 year lag
            # B01003_001E = total population

            # Try to get current population from ACS
            for estimate_year in [current_year - 1, current_year - 2]:
                url = f"{CENSUS_BASE_URL}/{estimate_year}/acs/acs1"
                params = {
                    "get": "NAME,B01003_001E",
                    "for": f"metropolitan statistical area/micropolitan statistical area:{cbsa_code}",
                }
                if self.api_key:
                    params["key"] = self.api_key

                response = await self._client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    # Response: [["NAME", "B01003_001E", "..."], ["Metro Name", "1234567", "..."]]
                    if len(data) > 1 and data[1][1]:
                        result.metro_name = data[1][0]
                        result.population = int(data[1][1])
                        result.population_year = estimate_year
                        break

            # Get historical data for growth calculation (1 year ago)
            if result.population_year:
                hist_year = result.population_year - 1
                try:
                    hist_url = f"{CENSUS_BASE_URL}/{hist_year}/acs/acs1"
                    hist_response = await self._client.get(hist_url, params={
                        "get": "B01003_001E",
                        "for": f"metropolitan statistical area/micropolitan statistical area:{cbsa_code}",
                        **({"key": self.api_key} if self.api_key else {}),
                    })
                    if hist_response.status_code == 200:
                        hist_data = hist_response.json()
                        if len(hist_data) > 1 and hist_data[1][0]:
                            result.population_1yr_ago = int(hist_data[1][0])
                except Exception:
                    pass

            # Get 5 year ago data
            if result.population_year:
                hist_year = result.population_year - 5
                try:
                    hist_url = f"{CENSUS_BASE_URL}/{hist_year}/acs/acs1"
                    hist_response = await self._client.get(hist_url, params={
                        "get": "B01003_001E",
                        "for": f"metropolitan statistical area/micropolitan statistical area:{cbsa_code}",
                        **({"key": self.api_key} if self.api_key else {}),
                    })
                    if hist_response.status_code == 200:
                        hist_data = hist_response.json()
                        if len(hist_data) > 1 and hist_data[1][0]:
                            result.population_5yr_ago = int(hist_data[1][0])
                except Exception:
                    pass

            # Calculate growth rates
            if result.population and result.population_1yr_ago:
                result.population_growth_1yr = round(
                    ((result.population - result.population_1yr_ago) / result.population_1yr_ago) * 100,
                    2
                )
            if result.population and result.population_5yr_ago:
                result.population_growth_5yr = round(
                    ((result.population - result.population_5yr_ago) / result.population_5yr_ago) * 100,
                    2
                )

        except Exception as e:
            print(f"Error fetching Census population data for {metro_id}: {e}")

        self._set_cache(cache_key, result)
        return result

    async def get_metro_income(self, metro_id: str) -> Optional[int]:
        """
        Get median household income for a metro area.

        Uses American Community Survey (ACS) 1-year estimates.
        """
        cbsa_code = METRO_CBSA_CODES.get(metro_id.lower())
        if not cbsa_code:
            return None

        cache_key = f"census_income_{metro_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        try:
            # ACS 1-year estimates - B19013_001E is median household income
            current_year = datetime.utcnow().year
            acs_year = current_year - 1  # Usually 1 year lag

            url = f"{CENSUS_BASE_URL}/{acs_year}/acs/acs1"
            params = {
                "get": "NAME,B19013_001E",
                "for": f"metropolitan statistical area/micropolitan statistical area:{cbsa_code}",
            }
            if self.api_key:
                params["key"] = self.api_key

            response = await self._client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                if len(data) > 1 and data[1][1]:
                    income = int(data[1][1])
                    self._set_cache(cache_key, income)
                    return income

        except Exception as e:
            print(f"Error fetching Census income data for {metro_id}: {e}")

        return None

    async def get_metro_demographics(self, metro_id: str) -> MetroPopulationData:
        """
        Get comprehensive demographic data for a metro area.

        Combines population and income data.
        """
        result = await self.get_metro_population(metro_id)
        if result:
            income = await self.get_metro_income(metro_id)
            if income:
                result.median_household_income = income

        return result or MetroPopulationData(metro_id=metro_id)
