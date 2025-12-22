"""
Household Income by Zip Code API integration.

RapidAPI: https://rapidapi.com/return-data-return-data-default/api/household-income-by-zip-code
Free tier: 100 requests/month, 1 req/sec

Provides median household income data for investment analysis.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import httpx


USAGE_FILE = Path(__file__).parent.parent.parent / ".api_usage_income.json"


@dataclass
class IncomeData:
    """Income data for a zip code."""
    zip_code: str
    median_income: int

    @property
    def income_tier(self) -> str:
        """Categorize income level."""
        if self.median_income >= 100000:
            return "high"
        elif self.median_income >= 60000:
            return "middle"
        elif self.median_income >= 35000:
            return "low-middle"
        else:
            return "low"

    def rent_affordability(self, monthly_rent: float) -> dict:
        """
        Calculate rent affordability metrics.

        Standard guideline: rent should be <= 30% of monthly income.
        """
        monthly_income = self.median_income / 12
        rent_to_income_ratio = (monthly_rent / monthly_income) * 100 if monthly_income > 0 else 0
        affordable_rent = monthly_income * 0.30

        return {
            "monthly_income": round(monthly_income),
            "rent_to_income_pct": round(rent_to_income_ratio, 1),
            "affordable_rent": round(affordable_rent),
            "is_affordable": rent_to_income_ratio <= 30,
            "affordability_rating": (
                "excellent" if rent_to_income_ratio <= 20 else
                "good" if rent_to_income_ratio <= 25 else
                "fair" if rent_to_income_ratio <= 30 else
                "stretched" if rent_to_income_ratio <= 40 else
                "unaffordable"
            )
        }

    def to_dict(self) -> dict:
        return {
            "zip_code": self.zip_code,
            "median_income": self.median_income,
            "income_tier": self.income_tier,
        }


class IncomeDataClient:
    """
    Household Income API client via RapidAPI.

    Provides median household income by zip code for market analysis.
    """

    BASE_URL = "https://household-income-by-zip-code.p.rapidapi.com"
    HOST = "household-income-by-zip-code.p.rapidapi.com"
    MONTHLY_LIMIT = 100

    def __init__(
        self,
        api_key: Optional[str] = None,
        monthly_limit: int = MONTHLY_LIMIT,
    ):
        self.api_key = api_key or os.environ.get("RAPIDAPI_KEY", "")
        self.monthly_limit = monthly_limit
        self._client = httpx.AsyncClient(timeout=15.0)
        self._usage = self._load_usage()
        self._cache: dict[str, IncomeData] = {}

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    @property
    def _headers(self) -> dict:
        return {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.HOST,
        }

    # Usage tracking
    def _load_usage(self) -> dict:
        current_month = datetime.now().strftime("%Y-%m")
        if USAGE_FILE.exists():
            try:
                with open(USAGE_FILE) as f:
                    data = json.load(f)
                    if data.get("month") == current_month:
                        return data
            except Exception:
                pass
        return {"requests_used": 0, "requests_limit": self.monthly_limit, "month": current_month}

    def _save_usage(self):
        try:
            with open(USAGE_FILE, "w") as f:
                json.dump(self._usage, f)
        except Exception:
            pass

    def _increment_usage(self):
        current_month = datetime.now().strftime("%Y-%m")
        if self._usage.get("month") != current_month:
            self._usage = {"requests_used": 1, "requests_limit": self.monthly_limit, "month": current_month}
        else:
            self._usage["requests_used"] = self._usage.get("requests_used", 0) + 1
        self._save_usage()

    def get_usage(self) -> dict:
        return {
            "requests_used": self._usage.get("requests_used", 0),
            "requests_limit": self._usage.get("requests_limit", self.monthly_limit),
            "requests_remaining": max(0, self._usage.get("requests_limit", self.monthly_limit) - self._usage.get("requests_used", 0)),
        }

    async def get_income(self, zip_code: str) -> Optional[IncomeData]:
        """
        Get median household income for a zip code.

        Args:
            zip_code: 5-digit US zip code

        Returns:
            IncomeData object or None if not available
        """
        # Check in-memory cache first
        if zip_code in self._cache:
            return self._cache[zip_code]

        # Check persistent database cache
        try:
            from src.db import get_repository
            repo = get_repository()
            cached = repo.cache.get_income(zip_code)
            if cached:
                income_data = IncomeData(
                    zip_code=zip_code,
                    median_income=cached["median_income"],
                )
                self._cache[zip_code] = income_data
                return income_data
        except Exception:
            pass  # DB not available, continue to API

        if not self.is_configured:
            return None

        usage = self.get_usage()
        if usage["requests_remaining"] <= 0:
            return None

        try:
            url = f"{self.BASE_URL}/v1/Census/HouseholdIncomeByZip/{zip_code}"
            response = await self._client.get(url, headers=self._headers)
            self._increment_usage()

            data = response.json()

            if "medianIncome" in data:
                income_data = IncomeData(
                    zip_code=zip_code,
                    median_income=data["medianIncome"],
                )
                self._cache[zip_code] = income_data

                # Also persist to database cache
                try:
                    from src.db import get_repository
                    repo = get_repository()
                    repo.cache.set_income(
                        zip_code=zip_code,
                        median_income=data["medianIncome"],
                        income_tier=income_data.income_tier,
                        data=data
                    )
                except Exception:
                    pass  # DB not available

                return income_data

            return None

        except Exception as e:
            print(f"Income API error for {zip_code}: {e}")
            return None

    async def get_income_batch(self, zip_codes: list[str]) -> dict[str, Optional[IncomeData]]:
        """
        Get income data for multiple zip codes.

        Args:
            zip_codes: List of 5-digit zip codes

        Returns:
            Dict mapping zip code to IncomeData (or None)
        """
        results = {}
        for zip_code in zip_codes:
            results[zip_code] = await self.get_income(zip_code)
        return results

    async def close(self):
        await self._client.aclose()


# Singleton instance
_client: Optional[IncomeDataClient] = None

def get_income_client() -> IncomeDataClient:
    """Get or create the income data client."""
    global _client
    if _client is None:
        _client = IncomeDataClient()
    return _client
