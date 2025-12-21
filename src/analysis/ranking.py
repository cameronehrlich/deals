"""Deal ranking and scoring engine."""

from dataclasses import dataclass, field
from typing import Optional

from src.models.deal import Deal, DealScore, InvestmentStrategy
from src.models.financials import FinancialMetrics
from src.models.market import MarketMetrics


@dataclass
class RankingConfig:
    """Configuration for deal ranking."""

    # Score weights
    financial_weight: float = 0.40
    market_weight: float = 0.30
    risk_weight: float = 0.20
    liquidity_weight: float = 0.10

    # Minimum thresholds
    min_cash_on_cash: float = 0.06  # 6%
    min_cap_rate: float = 0.05  # 5%
    min_cash_flow: float = 0  # Break even
    max_price: Optional[float] = None
    min_price: Optional[float] = None

    # Strategy preference
    strategy: InvestmentStrategy = InvestmentStrategy.CASH_FLOW

    # Filters
    exclude_negative_cash_flow: bool = True
    exclude_high_risk: bool = False  # DSCR < 1.0
    require_1pct_rule: bool = False

    @property
    def weights(self) -> dict[str, float]:
        return {
            "financial": self.financial_weight,
            "market": self.market_weight,
            "risk": self.risk_weight,
            "liquidity": self.liquidity_weight,
        }


class RankingEngine:
    """Engine for ranking and filtering deals."""

    def __init__(self, config: Optional[RankingConfig] = None):
        self.config = config or RankingConfig()

    def score_deal(
        self,
        deal: Deal,
        market_metrics: Optional[MarketMetrics] = None,
    ) -> DealScore:
        """Calculate score for a single deal."""
        if not deal.financial_metrics:
            deal.analyze()

        assert deal.financial_metrics is not None

        # Use provided market metrics or deal's own
        mm = market_metrics or deal.market_metrics
        if not mm:
            # Create default market metrics if none available
            from src.models.market import Market
            default_market = Market(
                id="unknown",
                name="Unknown Market",
                metro="Unknown",
                state=deal.property.state,
            )
            mm = MarketMetrics.from_market(default_market)

        return DealScore.calculate(
            property_id=deal.property.id,
            financial_metrics=deal.financial_metrics,
            market_metrics=mm,
            weights=self.config.weights,
        )

    def filter_deals(self, deals: list[Deal]) -> list[Deal]:
        """Filter deals based on configuration thresholds."""
        filtered = []

        for deal in deals:
            if not deal.financial_metrics:
                deal.analyze()

            fm = deal.financial_metrics
            if not fm:
                continue

            # Apply filters
            if self.config.exclude_negative_cash_flow and fm.monthly_cash_flow < self.config.min_cash_flow:
                continue

            if fm.cash_on_cash_return < self.config.min_cash_on_cash:
                continue

            if fm.cap_rate < self.config.min_cap_rate:
                continue

            if self.config.require_1pct_rule and fm.rent_to_price_ratio < 1.0:
                continue

            if self.config.exclude_high_risk:
                if fm.debt_service_coverage_ratio and fm.debt_service_coverage_ratio < 1.0:
                    continue

            if self.config.max_price and deal.property.list_price > self.config.max_price:
                continue

            if self.config.min_price and deal.property.list_price < self.config.min_price:
                continue

            filtered.append(deal)

        return filtered

    def rank_deals(
        self,
        deals: list[Deal],
        market_metrics: Optional[MarketMetrics] = None,
        apply_filters: bool = True,
    ) -> list[Deal]:
        """Rank deals by score, optionally filtering first."""
        if apply_filters:
            deals = self.filter_deals(deals)

        # Score each deal
        for deal in deals:
            deal.score = self.score_deal(deal, market_metrics)

        # Sort by strategy-specific score if configured, else overall
        strategy_key = self.config.strategy.value
        if strategy_key:
            deals.sort(
                key=lambda d: d.score.strategy_scores.get(strategy_key, d.score.overall_score)
                if d.score else 0,
                reverse=True,
            )
        else:
            deals.sort(key=lambda d: d.score.overall_score if d.score else 0, reverse=True)

        # Assign ranks and percentiles
        total = len(deals)
        for i, deal in enumerate(deals):
            if deal.score:
                deal.score.rank = i + 1
                deal.score.percentile = ((total - i) / total) * 100 if total > 0 else 0

        return deals

    def get_top_deals(
        self,
        deals: list[Deal],
        n: int = 10,
        market_metrics: Optional[MarketMetrics] = None,
    ) -> list[Deal]:
        """Get top N deals after ranking."""
        ranked = self.rank_deals(deals, market_metrics)
        return ranked[:n]

    def explain_score(self, deal: Deal) -> dict:
        """Generate explanation for a deal's score."""
        if not deal.score or not deal.financial_metrics:
            deal.analyze()

        if not deal.score:
            return {"error": "Unable to score deal"}

        explanation = {
            "overall_score": f"{deal.score.overall_score:.1f}/100",
            "rank": deal.score.rank,
            "components": {
                "financial": {
                    "score": f"{deal.score.financial_score:.1f}/100",
                    "weight": f"{self.config.financial_weight:.0%}",
                    "contribution": f"{deal.score.financial_score * self.config.financial_weight:.1f}",
                    "details": {
                        "cash_on_cash": f"{deal.financial_metrics.cash_on_cash_return:.1%}",
                        "cap_rate": f"{deal.financial_metrics.cap_rate:.1%}",
                        "monthly_cash_flow": f"${deal.financial_metrics.monthly_cash_flow:.0f}",
                        "rent_to_price": f"{deal.financial_metrics.rent_to_price_ratio:.2f}%",
                    },
                },
                "market": {
                    "score": f"{deal.score.market_score:.1f}/100",
                    "weight": f"{self.config.market_weight:.0%}",
                    "contribution": f"{deal.score.market_score * self.config.market_weight:.1f}",
                },
                "risk": {
                    "score": f"{deal.score.risk_score:.1f}/100",
                    "weight": f"{self.config.risk_weight:.0%}",
                    "contribution": f"{deal.score.risk_score * self.config.risk_weight:.1f}",
                },
                "liquidity": {
                    "score": f"{deal.score.liquidity_score:.1f}/100",
                    "weight": f"{self.config.liquidity_weight:.0%}",
                    "contribution": f"{deal.score.liquidity_score * self.config.liquidity_weight:.1f}",
                },
            },
            "strategy_fit": {
                strategy: f"{score:.1f}/100"
                for strategy, score in deal.score.strategy_scores.items()
            },
            "pros": deal.pros,
            "cons": deal.cons,
            "red_flags": deal.red_flags,
        }

        return explanation
