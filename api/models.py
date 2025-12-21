"""API response models."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

from src.models.property import PropertyType, PropertyStatus
from src.models.deal import DealPipeline, InvestmentStrategy
from src.models.market import MarketTrend


# Base response models
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Any
    message: Optional[str] = None
    errors: list[str] = Field(default_factory=list)


# Market response models
class MarketSummary(BaseModel):
    """Summarized market data for list views."""
    id: str
    name: str
    state: str
    metro: str
    population: Optional[int] = None
    median_home_price: Optional[float] = None
    median_rent: Optional[float] = None
    rent_to_price_ratio: Optional[float] = None
    price_change_1yr: Optional[float] = None
    job_growth_1yr: Optional[float] = None
    overall_score: float
    cash_flow_score: float
    growth_score: float
    rank: Optional[int] = None


class MarketDetail(MarketSummary):
    """Full market data."""
    region: Optional[str] = None
    population_growth_1yr: Optional[float] = None
    population_growth_5yr: Optional[float] = None
    unemployment_rate: Optional[float] = None
    major_employers: list[str] = Field(default_factory=list)
    median_household_income: Optional[float] = None
    price_change_5yr: Optional[float] = None
    rent_change_1yr: Optional[float] = None
    months_of_inventory: Optional[float] = None
    days_on_market_avg: Optional[int] = None
    price_trend: str
    rent_trend: str
    landlord_friendly: bool
    property_tax_rate: Optional[float] = None
    insurance_risk: Optional[str] = None
    affordability_score: float
    stability_score: float
    liquidity_score: float


class MarketsResponse(BaseModel):
    """Response for markets list."""
    markets: list[MarketSummary]
    total: int


# Property response models
class PropertySummary(BaseModel):
    """Summarized property data."""
    id: str
    address: str
    city: str
    state: str
    zip_code: str
    list_price: float
    estimated_rent: Optional[float] = None
    bedrooms: int
    bathrooms: float
    sqft: Optional[int] = None
    property_type: str
    days_on_market: int
    price_per_sqft: Optional[float] = None


class PropertyDetail(PropertySummary):
    """Full property data."""
    full_address: str
    year_built: Optional[int] = None
    lot_size_sqft: Optional[int] = None
    stories: Optional[int] = None
    units: int
    status: str
    source: str
    source_url: Optional[str] = None
    annual_taxes: Optional[float] = None
    hoa_fee: Optional[float] = None
    original_price: Optional[float] = None
    price_reduction_pct: Optional[float] = None
    gross_rent_multiplier: Optional[float] = None
    features: list[str] = Field(default_factory=list)


# Financial response models
class FinancialSummary(BaseModel):
    """Key financial metrics."""
    monthly_cash_flow: float
    annual_cash_flow: float
    cash_on_cash_return: float
    cap_rate: float
    gross_rent_multiplier: float
    rent_to_price_ratio: float
    total_cash_invested: float
    break_even_occupancy: float
    dscr: Optional[float] = None


class FinancialDetail(FinancialSummary):
    """Complete financial breakdown."""
    purchase_price: float
    down_payment: float
    loan_amount: float
    closing_costs: float
    monthly_mortgage: float
    monthly_taxes: float
    monthly_insurance: float
    monthly_hoa: float
    monthly_maintenance: float
    monthly_capex: float
    monthly_vacancy_reserve: float
    monthly_property_management: float
    total_monthly_expenses: float
    net_operating_income: float
    interest_rate: float
    down_payment_pct: float


# Deal response models
class DealScore(BaseModel):
    """Deal scoring breakdown."""
    overall_score: float
    financial_score: float
    market_score: float
    risk_score: float
    liquidity_score: float
    rank: Optional[int] = None
    percentile: Optional[float] = None
    strategy_scores: dict[str, float] = Field(default_factory=dict)


class DealSummary(BaseModel):
    """Summarized deal for list views."""
    id: str
    property: PropertySummary
    score: Optional[DealScore] = None
    financials: Optional[FinancialSummary] = None
    market_name: Optional[str] = None
    pipeline_status: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)


class DealDetail(BaseModel):
    """Full deal analysis."""
    id: str
    property: PropertyDetail
    score: Optional[DealScore] = None
    financials: Optional[FinancialDetail] = None
    market: Optional[MarketDetail] = None
    pipeline_status: str
    strategy: Optional[str] = None
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    first_seen: datetime
    last_analyzed: Optional[datetime] = None


class DealsResponse(BaseModel):
    """Response for deals search."""
    deals: list[DealSummary]
    total: int
    filters_applied: dict = Field(default_factory=dict)


# Analysis response models
class SensitivityResult(BaseModel):
    """Stress test results."""
    base_cash_flow: float
    base_coc: float
    base_cap_rate: float

    rate_increase_1pct: float
    rate_increase_2pct: float
    break_even_rate: Optional[float] = None

    vacancy_10pct: float
    vacancy_15pct: float
    break_even_vacancy: Optional[float] = None

    rent_decrease_5pct: float
    rent_decrease_10pct: float
    break_even_rent: Optional[float] = None

    moderate_stress: float
    severe_stress: float
    survives_moderate: bool
    survives_severe: bool
    risk_rating: str


class AnalysisRequest(BaseModel):
    """Request for property analysis."""
    purchase_price: float = Field(..., gt=0)
    monthly_rent: float = Field(..., ge=0)
    down_payment_pct: float = Field(default=0.25, ge=0, le=1)
    interest_rate: float = Field(default=0.07, ge=0, le=0.25)
    property_tax_rate: float = Field(default=0.012, ge=0)
    insurance_rate: float = Field(default=0.005, ge=0)
    vacancy_rate: float = Field(default=0.08, ge=0, le=1)
    maintenance_rate: float = Field(default=0.01, ge=0)
    property_management_rate: float = Field(default=0.10, ge=0, le=1)
    hoa_monthly: float = Field(default=0, ge=0)


class AnalysisResponse(BaseModel):
    """Response for property analysis."""
    financials: FinancialDetail
    sensitivity: SensitivityResult
    verdict: str
    recommendations: list[str]


# Search parameters
class SearchParams(BaseModel):
    """Deal search parameters."""
    markets: Optional[list[str]] = None
    strategy: str = "cash_flow"
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_beds: int = 2
    max_beds: Optional[int] = None
    min_cash_flow: Optional[float] = None
    min_coc: Optional[float] = None
    min_cap_rate: Optional[float] = None
    limit: int = 20
    down_payment_pct: float = 0.25
    interest_rate: float = 0.07
