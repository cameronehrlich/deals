"""Deal analyzer agent for evaluating properties."""

import asyncio
import time
from datetime import datetime
from typing import Optional

from src.agents.base import BaseAgent, AgentResult
from src.models.deal import Deal, DealPipeline, InvestmentStrategy
from src.models.financials import Financials, LoanTerms, OperatingExpenses
from src.models.market import Market, MarketMetrics
from src.models.property import Property
from src.analysis.ranking import RankingEngine, RankingConfig
from src.analysis.sensitivity import SensitivityAnalyzer


class DealAnalyzerAgent(BaseAgent):
    """Agent for analyzing and scoring individual deals."""

    agent_name = "deal_analyzer"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.ranking_config = RankingConfig(
            min_cash_on_cash=config.get("min_coc", 0.06) if config else 0.06,
            min_cap_rate=config.get("min_cap", 0.05) if config else 0.05,
            strategy=InvestmentStrategy(config.get("strategy", "cash_flow")) if config else InvestmentStrategy.CASH_FLOW,
        )
        self.ranking_engine = RankingEngine(self.ranking_config)
        self.sensitivity_analyzer = SensitivityAnalyzer()

    async def run(
        self,
        properties: list[Property],
        market: Optional[Market] = None,
        loan_terms: Optional[LoanTerms] = None,
        operating_expenses: Optional[OperatingExpenses] = None,
        run_sensitivity: bool = False,
    ) -> AgentResult:
        """
        Analyze a list of properties and return scored deals.

        Args:
            properties: Properties to analyze
            market: Market data for context
            loan_terms: Custom loan assumptions
            operating_expenses: Custom expense assumptions
            run_sensitivity: Whether to run stress tests

        Returns:
            AgentResult with analyzed and ranked deals
        """
        start_time = time.time()
        self.log(f"Analyzing {len(properties)} properties...")

        deals = []
        errors = []

        market_metrics = MarketMetrics.from_market(market) if market else None

        for prop in properties:
            try:
                deal = await self.analyze_property(
                    prop,
                    market=market,
                    loan_terms=loan_terms,
                    operating_expenses=operating_expenses,
                    run_sensitivity=run_sensitivity,
                )
                deals.append(deal)
            except Exception as e:
                errors.append(f"Error analyzing {prop.id}: {str(e)}")

        # Rank all deals
        ranked_deals = self.ranking_engine.rank_deals(
            deals,
            market_metrics=market_metrics,
            apply_filters=True,
        )

        duration_ms = int((time.time() - start_time) * 1000)
        self.log(f"Analyzed {len(ranked_deals)} deals in {duration_ms}ms")

        return AgentResult(
            success=len(errors) == 0 or len(ranked_deals) > 0,
            data={
                "deals": ranked_deals,
                "total_analyzed": len(properties),
                "passed_filters": len(ranked_deals),
                "filtered_out": len(properties) - len(ranked_deals),
            },
            message=f"Analyzed {len(properties)} properties, {len(ranked_deals)} passed filters",
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            errors=errors,
        )

    async def analyze_property(
        self,
        property: Property,
        market: Optional[Market] = None,
        loan_terms: Optional[LoanTerms] = None,
        operating_expenses: Optional[OperatingExpenses] = None,
        run_sensitivity: bool = False,
    ) -> Deal:
        """Analyze a single property and create a Deal."""
        # Create financials
        financials = Financials(
            property_id=property.id,
            purchase_price=property.list_price,
            estimated_rent=property.estimated_rent or 0,
            loan=loan_terms or LoanTerms(),
            expenses=operating_expenses or OperatingExpenses(),
        )

        # Apply property-specific overrides
        if property.hoa_fee:
            financials.expenses.hoa_monthly = property.hoa_fee
        if property.annual_taxes:
            financials.expenses.property_tax_rate = property.annual_taxes / property.list_price

        # Create deal
        deal = Deal(
            id=f"deal_{property.id}",
            property=property,
            financials=financials,
            market=market,
            pipeline_status=DealPipeline.NEW,
        )

        # Run analysis
        deal.analyze()

        # Run sensitivity analysis if requested
        if run_sensitivity and deal.financials:
            sensitivity = self.sensitivity_analyzer.analyze(deal)
            deal.sensitivity = sensitivity  # Store on deal for API response
            deal.notes.append(f"Risk rating: {sensitivity.risk_rating}")
            if not sensitivity.survives_moderate_stress:
                deal.red_flags.append("Does not survive moderate stress test")

        return deal

    async def quick_screen(
        self,
        properties: list[Property],
        min_rent_to_price: float = 0.007,  # 0.7%
        max_price: Optional[float] = None,
        min_beds: int = 2,
    ) -> list[Property]:
        """
        Quick pre-screen properties before full analysis.

        Returns properties that pass basic screens.
        """
        passed = []

        for prop in properties:
            # Price filter
            if max_price and prop.list_price > max_price:
                continue

            # Bedroom filter
            if prop.bedrooms < min_beds:
                continue

            # Rent-to-price ratio
            if prop.estimated_rent:
                ratio = prop.estimated_rent / prop.list_price
                if ratio < min_rent_to_price:
                    continue
            else:
                # No rent estimate, can't screen
                continue

            passed.append(prop)

        self.log(f"Quick screen: {len(passed)}/{len(properties)} passed")
        return passed

    def explain_deal(self, deal: Deal) -> dict:
        """Generate a detailed explanation for a deal."""
        return self.ranking_engine.explain_score(deal)

    def compare_deals(self, deal_a: Deal, deal_b: Deal) -> dict:
        """Compare two deals side by side."""
        if not deal_a.financial_metrics:
            deal_a.analyze()
        if not deal_b.financial_metrics:
            deal_b.analyze()

        return {
            "deal_a": {
                "address": deal_a.property.full_address,
                "price": deal_a.property.list_price,
                "rent": deal_a.property.estimated_rent,
                "score": deal_a.score.overall_score if deal_a.score else None,
                "cash_flow": deal_a.financial_metrics.monthly_cash_flow if deal_a.financial_metrics else None,
                "coc": deal_a.financial_metrics.cash_on_cash_return if deal_a.financial_metrics else None,
                "cap_rate": deal_a.financial_metrics.cap_rate if deal_a.financial_metrics else None,
            },
            "deal_b": {
                "address": deal_b.property.full_address,
                "price": deal_b.property.list_price,
                "rent": deal_b.property.estimated_rent,
                "score": deal_b.score.overall_score if deal_b.score else None,
                "cash_flow": deal_b.financial_metrics.monthly_cash_flow if deal_b.financial_metrics else None,
                "coc": deal_b.financial_metrics.cash_on_cash_return if deal_b.financial_metrics else None,
                "cap_rate": deal_b.financial_metrics.cap_rate if deal_b.financial_metrics else None,
            },
            "winner": deal_a.property.id if (deal_a.score and deal_b.score and deal_a.score.overall_score > deal_b.score.overall_score) else deal_b.property.id,
        }
