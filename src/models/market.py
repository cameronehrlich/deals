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
    labor_force: Optional[int] = Field(None, ge=0, description="Total labor force")
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

    # Supply/demand indicators
    months_of_inventory: Optional[float] = Field(None, ge=0)
    days_on_market_avg: Optional[int] = Field(None, ge=0)
    homes_sold_1yr: Optional[int] = Field(None, ge=0)
    new_listings_1yr: Optional[int] = Field(None, ge=0)
    absorption_rate: Optional[float] = Field(None, description="Sales / listings ratio")
    sale_to_list_ratio: Optional[float] = Field(None, description="Avg sale price / list price")
    pct_sold_above_list: Optional[float] = Field(None, description="% homes sold above list")
    pct_sold_below_list: Optional[float] = Field(None, description="% homes sold below list")

    # Trends
    price_trend: MarketTrend = Field(default=MarketTrend.STABLE)
    rent_trend: MarketTrend = Field(default=MarketTrend.STABLE)
    demand_trend: MarketTrend = Field(default=MarketTrend.STABLE)

    # Regulatory & cost factors
    landlord_friendly: bool = Field(default=True, description="Landlord-friendly regulations")
    landlord_friendly_score: Optional[int] = Field(None, ge=1, le=10, description="1-10 score")
    property_tax_rate: Optional[float] = Field(None, description="Avg property tax rate (decimal)")
    has_state_income_tax: Optional[bool] = Field(None, description="State has income tax")
    insurance_risk: Optional[str] = Field(None, description="Natural disaster risk: low/medium/high")
    insurance_risk_factors: list[str] = Field(default_factory=list, description="Risk types")
    notes: Optional[str] = None

    # Metadata
    data_sources: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class MarketMetrics(BaseModel):
    """
    Calculated market quality metrics for ranking.

    Score Components:
    - Cash Flow (25%): Rent/price ratio, adjusted for operating costs
    - Growth (20%): Population + job growth, short and long term
    - Affordability (15%): Price/income ratio, rent/income ratio
    - Stability (15%): Price volatility, supply/demand balance
    - Liquidity (10%): Days on market, sale-to-list ratio
    - Operating Costs (10%): Property taxes, insurance risk
    - Regulatory (5%): Landlord friendliness

    Data Sources Used:
    - Redfin: prices, DOM, inventory, sale-to-list, % above/below list
    - BLS: unemployment, job growth
    - Census: population, population growth, income
    - HUD: fair market rents
    - State Data: taxes, landlord friendliness, insurance risk
    """

    market_id: str

    # Composite scores (0-100)
    overall_score: float = Field(..., ge=0, le=100)
    cash_flow_score: float = Field(..., ge=0, le=100, description="Rent/price + operating costs")
    growth_score: float = Field(..., ge=0, le=100, description="Population + job growth")
    affordability_score: float = Field(..., ge=0, le=100, description="Price & rent vs income")
    stability_score: float = Field(..., ge=0, le=100, description="Market volatility + supply")
    liquidity_score: float = Field(..., ge=0, le=100, description="Ease of buying/selling")
    operating_cost_score: float = Field(..., ge=0, le=100, description="Taxes + insurance")
    regulatory_score: float = Field(..., ge=0, le=100, description="Landlord friendliness")

    # Risk factors (0-1, lower is better)
    appreciation_risk: float = Field(..., ge=0, le=1, description="Downside price risk")
    vacancy_risk: float = Field(..., ge=0, le=1, description="Vacancy risk level")
    regulatory_risk: float = Field(..., ge=0, le=1, description="Landlord regulation risk")
    operating_cost_risk: float = Field(..., ge=0, le=1, description="Tax/insurance cost risk")

    # Data quality indicators
    data_completeness: float = Field(default=0, ge=0, le=1, description="% of data available")
    data_sources_used: list[str] = Field(default_factory=list)

    @classmethod
    def from_market(cls, market: Market) -> "MarketMetrics":
        """
        Calculate comprehensive metrics from market data.

        Uses all available data sources to compute scores.
        Missing data is handled gracefully with sensible defaults.
        """
        data_sources_used = []
        data_points_available = 0
        data_points_total = 15  # Total key metrics we track

        # === CASH FLOW SCORE (25% of overall) ===
        # Base: rent-to-price ratio (0.8% = 80, 1% = 100)
        if market.avg_rent_to_price:
            base_cash_flow = min(100, max(0, market.avg_rent_to_price * 100))
            data_points_available += 1
        elif market.median_rent and market.median_home_price:
            ratio = (market.median_rent / market.median_home_price) * 100
            base_cash_flow = min(100, max(0, ratio * 100))
            data_points_available += 1
        else:
            base_cash_flow = 50

        # Adjust for property taxes (reduces NOI)
        tax_adjustment = 0
        if market.property_tax_rate:
            # Higher taxes = lower score. 1% tax = -5 points, 2% = -10
            tax_adjustment = market.property_tax_rate * 500
            data_sources_used.append("state_data")
            data_points_available += 1

        cash_flow_score = min(100, max(0, base_cash_flow - tax_adjustment))

        # === GROWTH SCORE (20% of overall) ===
        growth_components = []

        # 1-year population growth (weight: 30%)
        if market.population_growth_1yr is not None:
            # 2% growth = 70, 3% = 80, 0% = 50
            pop_1yr = min(100, max(0, 50 + market.population_growth_1yr * 10))
            growth_components.append(("pop_1yr", pop_1yr, 0.30))
            data_sources_used.append("census")
            data_points_available += 1

        # 5-year population growth (weight: 20%) - long-term trend
        if market.population_growth_5yr is not None:
            # 10% 5yr growth = 70, 20% = 90
            pop_5yr = min(100, max(0, 50 + market.population_growth_5yr * 2))
            growth_components.append(("pop_5yr", pop_5yr, 0.20))
            data_points_available += 1

        # Job growth (weight: 40%)
        if market.job_growth_1yr is not None:
            # 3% job growth = 80, 0% = 50
            job = min(100, max(0, 50 + market.job_growth_1yr * 10))
            growth_components.append(("job", job, 0.40))
            data_sources_used.append("bls")
            data_points_available += 1

        # Low unemployment bonus (weight: 10%)
        if market.unemployment_rate is not None:
            # 3% unemployment = 85, 5% = 75, 7% = 65
            unemp = min(100, max(0, 100 - market.unemployment_rate * 100 * 5))
            growth_components.append(("unemp", unemp, 0.10))
            data_points_available += 1

        if growth_components:
            total_weight = sum(w for _, _, w in growth_components)
            growth_score = sum(s * w for _, s, w in growth_components) / total_weight
        else:
            growth_score = 50

        # === AFFORDABILITY SCORE (15% of overall) ===
        affordability_components = []

        # Price-to-income ratio (weight: 60%)
        if market.median_household_income and market.median_home_price:
            price_to_income = market.median_home_price / market.median_household_income
            # 3x income = 100, 5x = 70, 7x = 40
            pti_score = min(100, max(0, 130 - price_to_income * 15))
            affordability_components.append(("pti", pti_score, 0.60))
            data_points_available += 1

        # Rent-to-income ratio (weight: 40%) - tenant affordability
        if market.median_rent and market.median_household_income:
            monthly_income = market.median_household_income / 12
            rent_to_income = (market.median_rent / monthly_income) * 100
            # 25% = 90, 30% = 75, 40% = 50
            rti_score = min(100, max(0, 115 - rent_to_income * 1.5))
            affordability_components.append(("rti", rti_score, 0.40))
            data_sources_used.append("hud")

        if affordability_components:
            total_weight = sum(w for _, _, w in affordability_components)
            affordability_score = sum(s * w for _, s, w in affordability_components) / total_weight
        else:
            affordability_score = 50

        # === STABILITY SCORE (15% of overall) ===
        stability_components = []

        # Price volatility - prefer moderate, stable growth
        if market.price_change_1yr is not None:
            price_change = market.price_change_1yr
            # Ideal: 2-5% growth. Big swings (up or down) are risky
            if 2 <= price_change <= 5:
                vol_score = 90
            elif 0 <= price_change < 2 or 5 < price_change <= 8:
                vol_score = 75
            elif -3 <= price_change < 0 or 8 < price_change <= 12:
                vol_score = 60
            else:
                vol_score = max(0, 50 - abs(price_change - 3) * 3)
            stability_components.append(("vol", vol_score, 0.50))
            data_sources_used.append("redfin")
            data_points_available += 1

        # Months of inventory - market balance
        if market.months_of_inventory is not None:
            moi = market.months_of_inventory
            # Balanced market: 4-6 months. <2 = too hot, >8 = soft
            if 4 <= moi <= 6:
                moi_score = 90
            elif 3 <= moi < 4 or 6 < moi <= 7:
                moi_score = 75
            elif 2 <= moi < 3 or 7 < moi <= 8:
                moi_score = 60
            else:
                moi_score = max(0, 50 - abs(moi - 5) * 8)
            stability_components.append(("moi", moi_score, 0.50))
            data_points_available += 1

        if stability_components:
            total_weight = sum(w for _, _, w in stability_components)
            stability_score = sum(s * w for _, s, w in stability_components) / total_weight
        else:
            stability_score = 50

        # === LIQUIDITY SCORE (10% of overall) ===
        liquidity_components = []

        # Days on market
        if market.days_on_market_avg is not None:
            dom = market.days_on_market_avg
            # 20 days = 90, 45 days = 70, 90 days = 40
            dom_score = min(100, max(0, 100 - (dom - 15) * 1.2))
            liquidity_components.append(("dom", dom_score, 0.50))
            data_points_available += 1

        # Sale-to-list ratio - demand indicator
        if market.sale_to_list_ratio is not None:
            stl = market.sale_to_list_ratio
            # 1.0 = 80, 0.98 = 70, 1.02 = 90
            stl_score = min(100, max(0, 80 + (stl - 1.0) * 500))
            liquidity_components.append(("stl", stl_score, 0.30))
            data_points_available += 1

        # % sold above list - market heat
        if market.pct_sold_above_list is not None:
            pct_above = market.pct_sold_above_list or 0
            # 30% above list = 80, 50% = 90
            above_score = min(100, max(0, 50 + pct_above))
            liquidity_components.append(("above", above_score, 0.20))

        if liquidity_components:
            total_weight = sum(w for _, _, w in liquidity_components)
            liquidity_score = sum(s * w for _, s, w in liquidity_components) / total_weight
        else:
            liquidity_score = 50

        # === OPERATING COST SCORE (10% of overall) ===
        operating_components = []

        # Property tax rate
        if market.property_tax_rate is not None:
            tax_rate = market.property_tax_rate
            # 0.5% = 90, 1% = 75, 2% = 50, 2.5% = 25
            tax_score = min(100, max(0, 100 - tax_rate * 100 * 20))
            operating_components.append(("tax", tax_score, 0.60))

        # Insurance risk
        if market.insurance_risk:
            risk_scores = {"low": 90, "medium": 65, "high": 35}
            ins_score = risk_scores.get(market.insurance_risk.lower(), 50)
            operating_components.append(("ins", ins_score, 0.40))

        if operating_components:
            total_weight = sum(w for _, _, w in operating_components)
            operating_cost_score = sum(s * w for _, s, w in operating_components) / total_weight
        else:
            operating_cost_score = 50

        # === REGULATORY SCORE (5% of overall) ===
        # Use granular 1-10 score if available, otherwise binary
        if market.landlord_friendly_score is not None:
            # Score 1-10 maps to 10-100
            regulatory_score = market.landlord_friendly_score * 10
        elif market.landlord_friendly:
            regulatory_score = 80
        else:
            regulatory_score = 30

        # === OVERALL WEIGHTED SCORE ===
        overall_score = (
            cash_flow_score * 0.25
            + growth_score * 0.20
            + affordability_score * 0.15
            + stability_score * 0.15
            + liquidity_score * 0.10
            + operating_cost_score * 0.10
            + regulatory_score * 0.05
        )

        # === RISK FACTORS ===
        # Appreciation risk - overheated markets
        if market.price_change_5yr and market.price_change_5yr > 50:
            appreciation_risk = 0.4
        elif market.price_change_5yr and market.price_change_5yr > 30:
            appreciation_risk = 0.25
        else:
            appreciation_risk = 0.15

        # Vacancy risk - based on unemployment and market softness
        vacancy_risk = 0.15
        if market.unemployment_rate and market.unemployment_rate > 0.06:
            vacancy_risk += 0.1
        if market.months_of_inventory and market.months_of_inventory > 6:
            vacancy_risk += 0.1
        vacancy_risk = min(0.5, vacancy_risk)

        # Regulatory risk - inverse of landlord friendliness
        if market.landlord_friendly_score is not None:
            regulatory_risk = (10 - market.landlord_friendly_score) / 10 * 0.5
        else:
            regulatory_risk = 0.1 if market.landlord_friendly else 0.4

        # Operating cost risk - high taxes + high insurance
        operating_cost_risk = 0.1
        if market.property_tax_rate and market.property_tax_rate > 0.015:
            operating_cost_risk += 0.15
        if market.insurance_risk == "high":
            operating_cost_risk += 0.2
        operating_cost_risk = min(0.5, operating_cost_risk)

        # Data completeness
        data_completeness = data_points_available / data_points_total

        return cls(
            market_id=market.id,
            overall_score=overall_score,
            cash_flow_score=cash_flow_score,
            growth_score=growth_score,
            affordability_score=affordability_score,
            stability_score=stability_score,
            liquidity_score=liquidity_score,
            operating_cost_score=operating_cost_score,
            regulatory_score=regulatory_score,
            appreciation_risk=appreciation_risk,
            vacancy_risk=vacancy_risk,
            regulatory_risk=regulatory_risk,
            operating_cost_risk=operating_cost_risk,
            data_completeness=data_completeness,
            data_sources_used=list(set(data_sources_used)),
        )
