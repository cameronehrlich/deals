"""
FRED (Federal Reserve Economic Data) API client.

FRED provides free access to economic data including:
- Mortgage rates (MORTGAGE30US, MORTGAGE15US)
- Unemployment (UNRATE)
- Inflation (CPIAUCSL)
- Housing starts (HOUST)
- Case-Shiller Index (CSUSHPINSA)

API docs: https://fred.stlouisfed.org/docs/api/fred/

Get free API key at: https://fred.stlouisfed.org/docs/api/api_key.html
"""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import httpx

FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Common series IDs
SERIES = {
    "mortgage_30yr": "MORTGAGE30US",
    "mortgage_15yr": "MORTGAGE15US",
    "unemployment": "UNRATE",
    "cpi": "CPIAUCSL",
    "housing_starts": "HOUST",
    "case_shiller": "CSUSHPINSA",
    "fed_funds": "FEDFUNDS",
    "treasury_10yr": "DGS10",
}


@dataclass
class FredObservation:
    """A single data observation from FRED."""

    series_id: str
    date: datetime
    value: float


@dataclass
class FredSeries:
    """A FRED data series with metadata."""

    series_id: str
    title: str
    frequency: str
    units: str
    last_updated: datetime
    observations: list[FredObservation]

    @property
    def latest_value(self) -> Optional[float]:
        if self.observations:
            return self.observations[-1].value
        return None

    @property
    def latest_date(self) -> Optional[datetime]:
        if self.observations:
            return self.observations[-1].date
        return None


class FredClient:
    """
    Client for FRED API.

    Usage:
        client = FredClient(api_key="your_key")

        # Get current 30-year mortgage rate
        rate = await client.get_mortgage_rate()

        # Get unemployment rate
        unemployment = await client.get_unemployment()

        # Get any series
        series = await client.get_series("CSUSHPINSA")
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("FRED_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=30.0)
        self._cache: dict[str, tuple[datetime, FredSeries]] = {}
        self._cache_ttl = 3600  # 1 hour

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def _fetch_series(
        self,
        series_id: str,
        start_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> Optional[FredSeries]:
        """Fetch a series from FRED."""
        # Check cache
        cache_key = f"{series_id}_{limit}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if (datetime.utcnow() - cached_time).seconds < self._cache_ttl:
                return cached_data

        if not self.api_key:
            # Return mock data if no API key
            return self._get_mock_data(series_id)

        try:
            # Get series info
            info_url = f"{FRED_BASE_URL}/series"
            info_params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
            }

            info_response = await self._client.get(info_url, params=info_params)
            info_response.raise_for_status()
            info_data = info_response.json()

            series_info = info_data.get("seriess", [{}])[0]

            # Get observations
            obs_url = f"{FRED_BASE_URL}/series/observations"
            obs_params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": limit,
            }

            if start_date:
                obs_params["observation_start"] = start_date.strftime("%Y-%m-%d")

            obs_response = await self._client.get(obs_url, params=obs_params)
            obs_response.raise_for_status()
            obs_data = obs_response.json()

            observations = []
            for obs in obs_data.get("observations", []):
                try:
                    value = float(obs["value"])
                    date = datetime.strptime(obs["date"], "%Y-%m-%d")
                    observations.append(FredObservation(
                        series_id=series_id,
                        date=date,
                        value=value,
                    ))
                except (ValueError, KeyError):
                    continue

            # Sort chronologically
            observations.sort(key=lambda x: x.date)

            result = FredSeries(
                series_id=series_id,
                title=series_info.get("title", series_id),
                frequency=series_info.get("frequency", ""),
                units=series_info.get("units", ""),
                last_updated=datetime.strptime(
                    series_info.get("last_updated", "2024-01-01 00:00:00"),
                    "%Y-%m-%d %H:%M:%S"
                ) if series_info.get("last_updated") else datetime.utcnow(),
                observations=observations,
            )

            # Cache
            self._cache[cache_key] = (datetime.utcnow(), result)
            return result

        except Exception as e:
            print(f"Error fetching FRED series {series_id}: {e}")
            return self._get_mock_data(series_id)

    def _get_mock_data(self, series_id: str) -> FredSeries:
        """Return mock data when API is unavailable."""
        mock_values = {
            "MORTGAGE30US": 6.95,
            "MORTGAGE15US": 6.25,
            "UNRATE": 4.1,
            "CPIAUCSL": 314.5,
            "HOUST": 1420,
            "CSUSHPINSA": 312.5,
            "FEDFUNDS": 5.33,
            "DGS10": 4.45,
        }

        value = mock_values.get(series_id, 0.0)
        now = datetime.utcnow()

        return FredSeries(
            series_id=series_id,
            title=f"Mock {series_id}",
            frequency="Monthly",
            units="Percent" if "RATE" in series_id or "MORTGAGE" in series_id else "Index",
            last_updated=now,
            observations=[
                FredObservation(series_id=series_id, date=now - timedelta(days=i*30), value=value * (1 + (i * 0.01)))
                for i in range(12, -1, -1)
            ],
        )

    async def get_series(self, series_id: str, limit: int = 100) -> Optional[FredSeries]:
        """Get a FRED series by ID."""
        return await self._fetch_series(series_id, limit=limit)

    async def get_mortgage_rate(self, term: int = 30) -> Optional[float]:
        """Get current mortgage rate."""
        series_id = SERIES["mortgage_30yr"] if term == 30 else SERIES["mortgage_15yr"]
        series = await self._fetch_series(series_id, limit=1)
        return series.latest_value if series else None

    async def get_unemployment(self) -> Optional[float]:
        """Get current unemployment rate."""
        series = await self._fetch_series(SERIES["unemployment"], limit=1)
        return series.latest_value if series else None

    async def get_fed_funds_rate(self) -> Optional[float]:
        """Get current federal funds rate."""
        series = await self._fetch_series(SERIES["fed_funds"], limit=1)
        return series.latest_value if series else None

    async def get_treasury_rate(self) -> Optional[float]:
        """Get 10-year treasury rate."""
        series = await self._fetch_series(SERIES["treasury_10yr"], limit=1)
        return series.latest_value if series else None

    async def get_housing_starts(self) -> Optional[float]:
        """Get housing starts (thousands of units)."""
        series = await self._fetch_series(SERIES["housing_starts"], limit=1)
        return series.latest_value if series else None

    async def get_case_shiller(self) -> Optional[float]:
        """Get Case-Shiller Home Price Index."""
        series = await self._fetch_series(SERIES["case_shiller"], limit=1)
        return series.latest_value if series else None

    async def get_macro_summary(self) -> dict:
        """Get summary of key macro indicators."""
        mortgage_30 = await self.get_mortgage_rate(30)
        mortgage_15 = await self.get_mortgage_rate(15)
        unemployment = await self.get_unemployment()
        fed_funds = await self.get_fed_funds_rate()
        treasury = await self.get_treasury_rate()

        return {
            "mortgage_30yr": mortgage_30,
            "mortgage_15yr": mortgage_15,
            "unemployment": unemployment,
            "fed_funds_rate": fed_funds,
            "treasury_10yr": treasury,
            "updated": datetime.utcnow().isoformat(),
        }
