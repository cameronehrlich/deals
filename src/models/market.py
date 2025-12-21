"""Market data model for metro/regional analysis."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MarketTrend(str, Enum):
    """Market trend direction."""

    STRONG_GROWTH = "strong_growth"
    MODERATE_GROWTH = "moderate_growth"
    STABLE = "stable"
    MODERATE_DECLINE = "moderate_decline"
    STRONG_DECLINE = "strong_decline"


class Market(BaseModel):
    """Market/metro area data model."""

    id: str = Field(..., description="Market identifier (e.g., 'austin_tx')")
    name: str = Field(..., description="Display name")
    metro: str = Field(..., description="Metro area name")
    state: str = Field(..., max_length=2)
    region: Optional[str] = Field(None, description="Geographic region")

    # Population metrics
    population: Optional[int] = Field(None, ge=0)
    population_growth_1yr: Optional[float] = Field(None, description="YoY population growth %")
    population_growth_5yr: Optional[float] = Field(None, description="5-year population growth %")

    # Employment
    unemployment_rate: Optional[float] = Field(None, ge=0, le=1)
    job_growth_1yr: Optional[float] = Field(None, description="YoY job growth %")
    major_employers: list[str] = Field(default_factory=list)

    # Income
    median_household_income: Optional[float] = Field(None, ge=0)
    income_growth_1yr: Optional[float] = Field(None)

    # Housing market
    median_home_price: Optional[float] = Field(None, ge=0)
    median_price_per_sqft: Optional[float] = Field(None, ge=0)
    price_change_1yr: Optional[float] = Field(None, description="YoY price change %")
    price_change_5yr: Optional[float] = Field(None, description="5-year price change %")

    # Rental market
    median_rent: Optional[float] = Field(None, ge=0)
    rent_change_1yr: Optional[float] = Field(None, description="YoY rent change %")
    avg_rent_to_price: Optional[float] = Field(None, description="Avg rent/price ratio")

    # Supply/demand
    months_of_inventory: Optional[float] = Field(None, ge=0)
    days_on_market_avg: Optional[int] = Field(None, ge=0)
    homes_sold_1yr: Optional[int] = Field(None, ge=0)
    new_listings_1yr: Optional[int] = Field(None, ge=0)
    absorption_rate: Optional[float] = Field(None, description="Sales / listings ratio")

    # Trends
    price_trend: MarketTrend = Field(default=MarketTrend.STABLE)
    rent_trend: MarketTrend = Field(default=MarketTrend.STABLE)
    demand_trend: MarketTrend = Field(default=MarketTrend.STABLE)

    # Qualitative factors
    landlord_friendly: bool = Field(default=True, description="Landlord-friendly regulations")
    property_tax_rate: Optional[float] = Field(None, description="Avg property tax rate")
    insurance_risk: Optional[str] = Field(None, description="Natural disaster risk level")
    notes: Optional[str] = None

    # Metadata
    data_sources: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class MarketMetrics(BaseModel):
    """Calculated market quality metrics for ranking."""

    market_id: str

    # Composite scores (0-100)
    overall_score: float = Field(..., ge=0, le=100)
    growth_score: float = Field(..., ge=0, le=100, description="Population + job growth")
    affordability_score: float = Field(..., ge=0, le=100, description="Price vs income")
    cash_flow_score: float = Field(..., ge=0, le=100, description="Rent to price potential")
    stability_score: float = Field(..., ge=0, le=100, description="Market volatility")
    liquidity_score: float = Field(..., ge=0, le=100, description="Ease of buying/selling")

    # Risk factors
    appreciation_risk: float = Field(..., ge=0, le=1, description="Downside price risk")
    vacancy_risk: float = Field(..., ge=0, le=1, description="Vacancy risk level")
    regulatory_risk: float = Field(..., ge=0, le=1, description="Landlord regulation risk")

    @classmethod
    def from_market(cls, market: Market) -> "MarketMetrics":
        """Calculate metrics from market data."""
        # Growth score (pop growth + job growth weighted)
        pop_growth = market.population_growth_1yr or 0
        job_growth = market.job_growth_1yr or 0
        growth_score = min(100, max(0, 50 + (pop_growth * 10) + (job_growth * 15)))

        # Affordability score (price to income ratio)
        if market.median_household_income and market.median_home_price:
            price_to_income = market.median_home_price / market.median_household_income
            # Lower ratio = more affordable = higher score
            affordability_score = min(100, max(0, 100 - (price_to_income - 3) * 15))
        else:
            affordability_score = 50

        # Cash flow score (rent to price ratio)
        if market.avg_rent_to_price:
            # 1% rule = 100, 0.5% = 50
            cash_flow_score = min(100, max(0, market.avg_rent_to_price * 100))
        elif market.median_rent and market.median_home_price:
            ratio = market.median_rent / market.median_home_price
            cash_flow_score = min(100, max(0, ratio * 10000))
        else:
            cash_flow_score = 50

        # Stability score (inverse of volatility)
        price_change = abs(market.price_change_1yr or 0)
        stability_score = min(100, max(0, 100 - price_change * 3))

        # Liquidity score (days on market, inventory)
        dom = market.days_on_market_avg or 45
        liquidity_score = min(100, max(0, 100 - (dom - 20) * 1.5))

        # Overall weighted score
        overall_score = (
            growth_score * 0.25
            + affordability_score * 0.20
            + cash_flow_score * 0.30
            + stability_score * 0.15
            + liquidity_score * 0.10
        )

        # Risk factors
        appreciation_risk = 0.3 if (market.price_change_5yr or 0) > 50 else 0.15
        vacancy_risk = 0.1 if market.unemployment_rate and market.unemployment_rate < 0.05 else 0.2
        regulatory_risk = 0.1 if market.landlord_friendly else 0.4

        return cls(
            market_id=market.id,
            overall_score=overall_score,
            growth_score=growth_score,
            affordability_score=affordability_score,
            cash_flow_score=cash_flow_score,
            stability_score=stability_score,
            liquidity_score=liquidity_score,
            appreciation_risk=appreciation_risk,
            vacancy_risk=vacancy_risk,
            regulatory_risk=regulatory_risk,
        )
