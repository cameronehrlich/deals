"""Deal model combining property, financials, and market data."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.models.property import Property
from src.models.financials import Financials, FinancialMetrics
from src.models.market import Market, MarketMetrics


class DealPipeline(str, Enum):
    """Deal pipeline status."""

    NEW = "new"
    REVIEWING = "reviewing"
    ANALYZED = "analyzed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    PURSUING = "pursuing"
    UNDER_CONTRACT = "under_contract"
    CLOSED = "closed"


class InvestmentStrategy(str, Enum):
    """Investment strategy types."""

    CASH_FLOW = "cash_flow"
    APPRECIATION = "appreciation"
    VALUE_ADD = "value_add"
    DISTRESSED = "distressed"
    BRRRR = "brrrr"


class DealScore(BaseModel):
    """Composite deal scoring."""

    property_id: str

    # Component scores (0-100)
    financial_score: float = Field(..., ge=0, le=100)
    market_score: float = Field(..., ge=0, le=100)
    risk_score: float = Field(..., ge=0, le=100, description="Lower = more risky")
    liquidity_score: float = Field(..., ge=0, le=100)

    # Weighted composite
    overall_score: float = Field(..., ge=0, le=100)

    # Scoring weights used
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "financial": 0.40,
            "market": 0.30,
            "risk": 0.20,
            "liquidity": 0.10,
        }
    )

    # Strategy fit scores
    strategy_scores: dict[str, float] = Field(default_factory=dict)

    # Ranking
    rank: Optional[int] = None
    percentile: Optional[float] = None

    @classmethod
    def calculate(
        cls,
        property_id: str,
        financial_metrics: FinancialMetrics,
        market_metrics: MarketMetrics,
        weights: Optional[dict[str, float]] = None,
        location_data: Optional[dict] = None,
    ) -> "DealScore":
        """Calculate composite deal score.

        Args:
            property_id: Property identifier
            financial_metrics: Calculated financial metrics
            market_metrics: Market analysis metrics
            weights: Score component weights
            location_data: Optional location data (walk_score, flood_zone, noise, schools)
                          to incorporate into scoring
        """
        if weights is None:
            weights = {
                "financial": 0.40,
                "market": 0.30,
                "risk": 0.20,
                "liquidity": 0.10,
            }

        # Financial score (based on CoC, cap rate, cash flow)
        coc_score = min(100, max(0, financial_metrics.cash_on_cash_return * 500))  # 20% CoC = 100
        cap_score = min(100, max(0, financial_metrics.cap_rate * 1000))  # 10% cap = 100
        cf_positive = 100 if financial_metrics.monthly_cash_flow > 0 else 50
        dscr_score = 100 if (financial_metrics.debt_service_coverage_ratio or 0) >= 1.25 else 70
        financial_score = (coc_score * 0.4 + cap_score * 0.3 + cf_positive * 0.2 + dscr_score * 0.1)

        # Market score (from market metrics)
        market_score = market_metrics.overall_score

        # Risk score (inverse of risks)
        risk_factors = [
            1 - market_metrics.appreciation_risk,
            1 - market_metrics.vacancy_risk,
            1 - market_metrics.regulatory_risk,
            min(1, financial_metrics.break_even_occupancy * 1.2),  # Lower break-even = better
        ]

        # Incorporate location data into risk score if available
        location_risk_adjustment = 0
        if location_data:
            flood_zone = location_data.get("flood_zone", {})
            if flood_zone:
                risk_level = flood_zone.get("risk_level", "").lower()
                if risk_level == "high":
                    # High flood risk penalizes risk score significantly
                    location_risk_adjustment -= 15
                elif risk_level == "moderate":
                    location_risk_adjustment -= 5
                # Low risk gives no penalty

        risk_score = (sum(risk_factors) / len(risk_factors)) * 100 + location_risk_adjustment
        risk_score = max(0, min(100, risk_score))  # Clamp to 0-100

        # Liquidity score - incorporate walkability if available
        liquidity_score = market_metrics.liquidity_score
        if location_data:
            walk_score = location_data.get("walk_score")
            if walk_score is not None:
                # Higher walk score slightly boosts liquidity (more desirable properties sell faster)
                walk_boost = (walk_score - 50) / 100 * 5  # -2.5 to +2.5 adjustment
                liquidity_score = max(0, min(100, liquidity_score + walk_boost))

        # Overall weighted score
        overall_score = (
            financial_score * weights["financial"]
            + market_score * weights["market"]
            + risk_score * weights["risk"]
            + liquidity_score * weights["liquidity"]
        )

        # Strategy-specific scores
        strategy_scores = {
            InvestmentStrategy.CASH_FLOW.value: (
                coc_score * 0.5 + cap_score * 0.3 + cf_positive * 0.2
            ),
            InvestmentStrategy.APPRECIATION.value: (
                market_metrics.growth_score * 0.6 + market_score * 0.4
            ),
            InvestmentStrategy.VALUE_ADD.value: (
                market_score * 0.4 + liquidity_score * 0.3 + cap_score * 0.3
            ),
        }

        return cls(
            property_id=property_id,
            financial_score=financial_score,
            market_score=market_score,
            risk_score=risk_score,
            liquidity_score=liquidity_score,
            overall_score=overall_score,
            weights=weights,
            strategy_scores=strategy_scores,
        )


class Deal(BaseModel):
    """Complete deal analysis combining all components."""

    id: str = Field(..., description="Deal identifier")

    # Core data
    property: Property
    financials: Optional[Financials] = None
    financial_metrics: Optional[FinancialMetrics] = None
    market: Optional[Market] = None
    market_metrics: Optional[MarketMetrics] = None

    # Scoring
    score: Optional[DealScore] = None

    # Pipeline tracking
    pipeline_status: DealPipeline = Field(default=DealPipeline.NEW)
    strategy: Optional[InvestmentStrategy] = None

    # Notes and analysis
    notes: list[str] = Field(default_factory=list)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)

    # User actions
    is_favorite: bool = False
    user_rating: Optional[int] = Field(None, ge=1, le=5)

    # Timestamps
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_analyzed: Optional[datetime] = None
    status_updated: datetime = Field(default_factory=datetime.utcnow)

    def analyze(self) -> "Deal":
        """Run financial analysis and scoring."""
        if not self.financials:
            # Create financials from property data
            self.financials = Financials(
                property_id=self.property.id,
                purchase_price=self.property.list_price,
                estimated_rent=self.property.estimated_rent or 0,
            )
            if self.property.hoa_fee:
                self.financials.expenses.hoa_monthly = self.property.hoa_fee
            if self.property.annual_taxes:
                # Override tax rate with actual taxes
                self.financials.expenses.property_tax_rate = (
                    self.property.annual_taxes / self.property.list_price
                )

        # Calculate financials
        self.financials.calculate()
        self.financial_metrics = FinancialMetrics.from_financials(self.financials)

        # Calculate market metrics if market data available
        if self.market:
            self.market_metrics = MarketMetrics.from_market(self.market)

            # Calculate deal score
            self.score = DealScore.calculate(
                property_id=self.property.id,
                financial_metrics=self.financial_metrics,
                market_metrics=self.market_metrics,
            )

        # Generate pros/cons
        self._generate_analysis()

        self.last_analyzed = datetime.utcnow()
        self.pipeline_status = DealPipeline.ANALYZED

        return self

    def _generate_analysis(self) -> None:
        """Generate pros, cons, and red flags based on analysis."""
        self.pros = []
        self.cons = []
        self.red_flags = []

        if self.financial_metrics:
            # Cash flow analysis
            if self.financial_metrics.monthly_cash_flow > 200:
                self.pros.append(f"Strong cash flow: ${self.financial_metrics.monthly_cash_flow:.0f}/month")
            elif self.financial_metrics.monthly_cash_flow > 0:
                self.pros.append(f"Positive cash flow: ${self.financial_metrics.monthly_cash_flow:.0f}/month")
            else:
                self.cons.append(f"Negative cash flow: ${self.financial_metrics.monthly_cash_flow:.0f}/month")

            # Returns
            if self.financial_metrics.cash_on_cash_return >= 0.10:
                self.pros.append(f"Excellent CoC return: {self.financial_metrics.cash_on_cash_return:.1%}")
            elif self.financial_metrics.cash_on_cash_return >= 0.06:
                self.pros.append(f"Good CoC return: {self.financial_metrics.cash_on_cash_return:.1%}")
            elif self.financial_metrics.cash_on_cash_return < 0.04:
                self.cons.append(f"Low CoC return: {self.financial_metrics.cash_on_cash_return:.1%}")

            # Cap rate
            if self.financial_metrics.cap_rate >= 0.08:
                self.pros.append(f"High cap rate: {self.financial_metrics.cap_rate:.1%}")
            elif self.financial_metrics.cap_rate < 0.05:
                self.cons.append(f"Low cap rate: {self.financial_metrics.cap_rate:.1%}")

            # 1% rule
            if self.financial_metrics.rent_to_price_ratio >= 1.0:
                self.pros.append(f"Meets 1% rule: {self.financial_metrics.rent_to_price_ratio:.2f}%")
            elif self.financial_metrics.rent_to_price_ratio < 0.7:
                self.cons.append(f"Below 1% rule: {self.financial_metrics.rent_to_price_ratio:.2f}%")

            # DSCR
            if self.financial_metrics.debt_service_coverage_ratio:
                if self.financial_metrics.debt_service_coverage_ratio < 1.0:
                    self.red_flags.append("DSCR below 1.0 - debt service exceeds NOI")
                elif self.financial_metrics.debt_service_coverage_ratio < 1.2:
                    self.cons.append(f"Tight DSCR: {self.financial_metrics.debt_service_coverage_ratio:.2f}")

        # Property-specific
        if self.property.days_on_market > 90:
            self.pros.append(f"Stale listing ({self.property.days_on_market} days) - negotiation opportunity")

        if self.property.price_reduction_pct and self.property.price_reduction_pct > 5:
            self.pros.append(f"Price reduced {self.property.price_reduction_pct:.1f}% from original")

        if self.property.year_built and self.property.year_built < 1960:
            self.cons.append(f"Older property (built {self.property.year_built}) - higher maintenance risk")

        if self.market_metrics:
            if self.market_metrics.growth_score > 70:
                self.pros.append("Strong market growth indicators")
            if self.market_metrics.regulatory_risk > 0.3:
                self.cons.append("Landlord-unfriendly regulations")

    def add_location_insights(self, location_data: dict) -> None:
        """Add location-based pros and cons from location data.

        Args:
            location_data: Dict containing walk_score, transit_score, bike_score,
                          noise, schools, flood_zone
        """
        if not location_data:
            return

        # Walk Score insights
        walk_score = location_data.get("walk_score")
        walk_desc = location_data.get("walk_description", "")
        if walk_score is not None:
            if walk_score >= 70:
                self.pros.append(f"Highly walkable area ({walk_desc or 'Walk Score ' + str(walk_score)})")
            elif walk_score < 30:
                self.cons.append(f"Car-dependent area (Walk Score {walk_score})")

        # Transit Score
        transit_score = location_data.get("transit_score")
        if transit_score is not None and transit_score >= 70:
            self.pros.append(f"Excellent transit access (Transit Score {transit_score})")

        # Flood Zone insights
        flood_zone = location_data.get("flood_zone", {})
        if flood_zone:
            risk_level = flood_zone.get("risk_level", "").lower()
            zone = flood_zone.get("zone", "")
            requires_insurance = flood_zone.get("requires_insurance", False)

            if risk_level == "high":
                self.cons.append(f"High flood risk area (Zone {zone})")
                if requires_insurance:
                    self.red_flags.append("Flood insurance required - adds $1,500-3,000+/year")
            elif risk_level == "moderate":
                self.cons.append(f"Moderate flood risk (Zone {zone})")
            elif risk_level == "low":
                self.pros.append("Low flood risk area - no flood insurance required")

        # Noise insights
        noise = location_data.get("noise", {})
        if noise:
            noise_score = noise.get("noise_score")
            if noise_score is not None:
                if noise_score >= 80:
                    self.pros.append("Very quiet neighborhood")
                elif noise_score < 40:
                    self.cons.append("Noisy location - may affect tenant appeal")

        # School insights
        schools = location_data.get("schools", [])
        if schools:
            avg_rating = sum(s.get("rating", 0) for s in schools if s.get("rating")) / max(1, sum(1 for s in schools if s.get("rating")))
            if avg_rating >= 8:
                self.pros.append(f"Excellent nearby schools (avg rating {avg_rating:.1f}/10)")
            elif avg_rating >= 6:
                self.pros.append(f"Good nearby schools (avg rating {avg_rating:.1f}/10)")
            elif avg_rating < 4 and avg_rating > 0:
                self.cons.append(f"Below-average nearby schools (avg rating {avg_rating:.1f}/10)")
