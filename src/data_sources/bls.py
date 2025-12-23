"""
Bureau of Labor Statistics (BLS) API client.

BLS provides free access to employment data including:
- Metro area unemployment rates (LAUS)
- Metro area employment levels (SMT)
- Job growth calculations

API docs: https://www.bls.gov/developers/
No API key required for basic access (500 queries/day).
Register at https://data.bls.gov/registrationEngine/ for higher limits.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import httpx

BLS_BASE_URL = "https://api.bls.gov/publicAPI/v2"

# Metro area codes for our target markets
# Format: Series ID = LAU + ST + {area_code} + {measure}
# Measure codes: 03 = unemployment rate, 04 = unemployment, 05 = employment, 06 = labor force
METRO_AREA_CODES = {
    # Format: "city_state": (state_code, area_code, metro_name)
    "indianapolis_in": ("18", "26900", "Indianapolis-Carmel-Anderson, IN"),
    "cleveland_oh": ("39", "17460", "Cleveland-Elyria, OH"),
    "memphis_tn": ("47", "32820", "Memphis, TN-MS-AR"),
    "birmingham_al": ("01", "13820", "Birmingham-Hoover, AL"),
    "kansas_city_mo": ("29", "28140", "Kansas City, MO-KS"),
    "tampa_fl": ("12", "45300", "Tampa-St. Petersburg-Clearwater, FL"),
    "phoenix_az": ("04", "38060", "Phoenix-Mesa-Chandler, AZ"),
    "austin_tx": ("48", "12420", "Austin-Round Rock-Georgetown, TX"),
    "huntsville_al": ("01", "26620", "Huntsville, AL"),
    "dallas_tx": ("48", "19100", "Dallas-Fort Worth-Arlington, TX"),
    "atlanta_ga": ("13", "12060", "Atlanta-Sandy Springs-Alpharetta, GA"),
    "denver_co": ("08", "19740", "Denver-Aurora-Lakewood, CO"),
    "nashville_tn": ("47", "34980", "Nashville-Davidson--Murfreesboro--Franklin, TN"),
    "charlotte_nc": ("37", "16740", "Charlotte-Concord-Gastonia, NC-SC"),
    "orlando_fl": ("12", "36740", "Orlando-Kissimmee-Sanford, FL"),
    "raleigh_nc": ("37", "39580", "Raleigh-Cary, NC"),
    "san_antonio_tx": ("48", "41700", "San Antonio-New Braunfels, TX"),
    "jacksonville_fl": ("12", "27260", "Jacksonville, FL"),
    "columbus_oh": ("39", "18140", "Columbus, OH"),
    "cincinnati_oh": ("39", "17140", "Cincinnati, OH-KY-IN"),
    # Additional major metros
    "los_angeles_ca": ("06", "31080", "Los Angeles-Long Beach-Anaheim, CA"),
    "san_francisco_ca": ("06", "41860", "San Francisco-Oakland-Berkeley, CA"),
    "san_diego_ca": ("06", "41740", "San Diego-Chula Vista-Carlsbad, CA"),
    "seattle_wa": ("53", "42660", "Seattle-Tacoma-Bellevue, WA"),
    "las_vegas_nv": ("32", "29820", "Las Vegas-Henderson-Paradise, NV"),
    "houston_tx": ("48", "26420", "Houston-The Woodlands-Sugar Land, TX"),
    "miami_fl": ("12", "33100", "Miami-Fort Lauderdale-Pompano Beach, FL"),
    "chicago_il": ("17", "16980", "Chicago-Naperville-Elgin, IL-IN-WI"),
    "new_york_ny": ("36", "35620", "New York-Newark-Jersey City, NY-NJ-PA"),
    "boston_ma": ("25", "14460", "Boston-Cambridge-Newton, MA-NH"),
    "washington_dc": ("11", "47900", "Washington-Arlington-Alexandria, DC-VA-MD-WV"),
    "detroit_mi": ("26", "19820", "Detroit-Warren-Dearborn, MI"),
    "minneapolis_mn": ("27", "33460", "Minneapolis-St. Paul-Bloomington, MN-WI"),
    "portland_or": ("41", "38900", "Portland-Vancouver-Hillsboro, OR-WA"),
    "sacramento_ca": ("06", "40900", "Sacramento-Roseville-Folsom, CA"),
    "salt_lake_city_ut": ("49", "41620", "Salt Lake City, UT"),
    "pittsburgh_pa": ("42", "38300", "Pittsburgh, PA"),
    "st_louis_mo": ("29", "41180", "St. Louis, MO-IL"),
}


@dataclass
class MetroEmploymentData:
    """Employment data for a metro area."""

    metro_id: str
    metro_name: str

    # Unemployment
    unemployment_rate: Optional[float] = None
    unemployment_rate_year_ago: Optional[float] = None
    unemployment_change: Optional[float] = None

    # Employment
    employment: Optional[int] = None
    employment_year_ago: Optional[int] = None
    employment_growth: Optional[float] = None  # YoY percentage

    # Labor force
    labor_force: Optional[int] = None
    labor_force_growth: Optional[float] = None

    # Metadata
    period: Optional[str] = None
    last_updated: Optional[datetime] = None


class BLSClient:
    """
    Client for Bureau of Labor Statistics API.

    Usage:
        client = BLSClient()

        # Get metro employment data
        data = await client.get_metro_employment("phoenix_az")
        print(f"Unemployment: {data.unemployment_rate}%")
        print(f"Job Growth: {data.employment_growth}%")
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("BLS_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=30.0)
        self._cache: dict[str, tuple[datetime, dict]] = {}
        self._cache_ttl = 86400  # 24 hours (BLS data updates monthly)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def _build_laus_series_id(self, state_code: str, area_code: str, measure: str = "03") -> str:
        """
        Build a LAUS (Local Area Unemployment Statistics) series ID for metro areas.

        Measures:
            03 = Unemployment rate
            04 = Unemployment
            05 = Employment
            06 = Labor force

        Format: LAUMT{state_code}{area_code}000000{measure}
        Example: LAUMT124530000000003 (Tampa, FL unemployment rate)
        """
        return f"LAUMT{state_code}{area_code}000000{measure}"

    def _build_smu_series_id(self, state_code: str, area_code: str) -> str:
        """
        Build an SMU (State and Metro Employment) series ID.

        Returns total nonfarm employment for the metro area.
        Format: SMU{state_code}{area_code}0000000001
        Example: SMU12453000000000001 (Tampa, FL total employment)
        """
        return f"SMU{state_code}{area_code}0000000001"

    async def _fetch_series(self, series_ids: list[str], years: int = 2) -> dict:
        """Fetch multiple series from BLS."""
        cache_key = "_".join(sorted(series_ids))

        # Check cache
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            age = (datetime.utcnow() - cached_time).total_seconds()
            if age < self._cache_ttl:
                return cached_data

        try:
            current_year = datetime.utcnow().year
            start_year = current_year - years

            payload = {
                "seriesid": series_ids,
                "startyear": str(start_year),
                "endyear": str(current_year),
            }

            if self.api_key:
                payload["registrationkey"] = self.api_key

            response = await self._client.post(
                f"{BLS_BASE_URL}/timeseries/data/",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "REQUEST_SUCCEEDED":
                print(f"BLS API error: {data.get('message', 'Unknown error')}")
                return {}

            # Parse results
            results = {}
            for series in data.get("Results", {}).get("series", []):
                series_id = series.get("seriesID", "")
                observations = series.get("data", [])

                # Sort by year and period (most recent first)
                observations.sort(
                    key=lambda x: (x.get("year", ""), x.get("period", "")),
                    reverse=True
                )

                results[series_id] = observations

            # Cache
            self._cache[cache_key] = (datetime.utcnow(), results)
            return results

        except Exception as e:
            print(f"Error fetching BLS data: {e}")
            return {}

    async def get_metro_employment(self, metro_id: str) -> Optional[MetroEmploymentData]:
        """
        Get employment data for a metro area.

        Args:
            metro_id: Market ID like "phoenix_az"

        Returns:
            MetroEmploymentData with unemployment and employment metrics
        """
        metro_info = METRO_AREA_CODES.get(metro_id.lower())
        if not metro_info:
            print(f"Unknown metro: {metro_id}")
            return None

        state_code, area_code, metro_name = metro_info

        # Build series IDs for this metro
        # Use LAUS for unemployment rate and labor force, SMU for employment
        unemp_series = self._build_laus_series_id(state_code, area_code, "03")  # Unemployment rate
        lf_series = self._build_laus_series_id(state_code, area_code, "06")  # Labor force
        emp_series = self._build_smu_series_id(state_code, area_code)  # Employment

        series_ids = [unemp_series, lf_series, emp_series]

        data = await self._fetch_series(series_ids)

        if not data:
            return MetroEmploymentData(
                metro_id=metro_id,
                metro_name=metro_name,
            )

        result = MetroEmploymentData(
            metro_id=metro_id,
            metro_name=metro_name,
        )

        # Parse unemployment rate
        if unemp_series in data and data[unemp_series]:
            obs = data[unemp_series]
            if len(obs) >= 1:
                try:
                    result.unemployment_rate = float(obs[0].get("value", 0))
                    result.period = f"{obs[0].get('year')}-{obs[0].get('period', 'M12')}"
                except (ValueError, TypeError):
                    pass

            # Get year ago value for comparison
            if len(obs) >= 13:  # ~12 months ago
                try:
                    result.unemployment_rate_year_ago = float(obs[12].get("value", 0))
                    if result.unemployment_rate and result.unemployment_rate_year_ago:
                        result.unemployment_change = (
                            result.unemployment_rate - result.unemployment_rate_year_ago
                        )
                except (ValueError, TypeError):
                    pass

        # Parse employment from SMU series
        if emp_series in data and data[emp_series]:
            obs = data[emp_series]
            if len(obs) >= 1:
                try:
                    result.employment = int(float(obs[0].get("value", 0)) * 1000)  # In thousands
                except (ValueError, TypeError):
                    pass

            # Calculate YoY growth
            if len(obs) >= 13:
                try:
                    current = float(obs[0].get("value", 0))
                    year_ago = float(obs[12].get("value", 0))
                    result.employment_year_ago = int(year_ago * 1000)
                    if year_ago > 0:
                        result.employment_growth = ((current - year_ago) / year_ago) * 100
                except (ValueError, TypeError):
                    pass

        # Parse labor force
        if lf_series in data and data[lf_series]:
            obs = data[lf_series]
            if len(obs) >= 1:
                try:
                    result.labor_force = int(float(obs[0].get("value", 0)) * 1000)
                except (ValueError, TypeError):
                    pass

            if len(obs) >= 13:
                try:
                    current = float(obs[0].get("value", 0))
                    year_ago = float(obs[12].get("value", 0))
                    if year_ago > 0:
                        result.labor_force_growth = ((current - year_ago) / year_ago) * 100
                except (ValueError, TypeError):
                    pass

        result.last_updated = datetime.utcnow()
        return result

    async def get_all_metros(self) -> dict[str, MetroEmploymentData]:
        """Get employment data for all known metros."""
        results = {}

        # Batch all series requests
        all_series = []
        metro_series_map = {}

        for metro_id, (state_code, area_code, metro_name) in METRO_AREA_CODES.items():
            unemp_series = self._build_laus_series_id(state_code, area_code, "03")
            lf_series = self._build_laus_series_id(state_code, area_code, "06")
            emp_series = self._build_smu_series_id(state_code, area_code)

            series_ids = [unemp_series, lf_series, emp_series]
            all_series.extend(series_ids)
            metro_series_map[metro_id] = (state_code, area_code, metro_name, unemp_series, emp_series)

        # BLS API allows up to 50 series per request
        batch_size = 50
        all_data = {}

        for i in range(0, len(all_series), batch_size):
            batch = all_series[i:i + batch_size]
            batch_data = await self._fetch_series(batch)
            all_data.update(batch_data)

        # Parse results for each metro
        for metro_id, (state_code, area_code, metro_name, unemp_series, emp_series) in metro_series_map.items():
            result = MetroEmploymentData(
                metro_id=metro_id,
                metro_name=metro_name,
                last_updated=datetime.utcnow(),
            )

            # Parse unemployment rate
            if unemp_series in all_data and all_data[unemp_series]:
                obs = all_data[unemp_series]
                if obs:
                    try:
                        result.unemployment_rate = float(obs[0].get("value", 0))
                    except (ValueError, TypeError):
                        pass

                if len(obs) >= 13:
                    try:
                        result.unemployment_rate_year_ago = float(obs[12].get("value", 0))
                    except (ValueError, TypeError):
                        pass

            # Parse employment growth from SMU series
            if emp_series in all_data and all_data[emp_series]:
                obs = all_data[emp_series]
                if len(obs) >= 13:
                    try:
                        current = float(obs[0].get("value", 0))
                        year_ago = float(obs[12].get("value", 0))
                        if year_ago > 0:
                            result.employment_growth = ((current - year_ago) / year_ago) * 100
                    except (ValueError, TypeError):
                        pass

            results[metro_id] = result

        return results
