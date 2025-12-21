"""Tests for analysis module."""

import pytest
from src.analysis.ranking import RankingEngine, RankingConfig
from src.analysis.sensitivity import SensitivityAnalyzer
from src.models.property import Property
from src.models.deal import Deal, InvestmentStrategy
from src.models.market import Market, MarketMetrics


class TestRankingEngine:
    """Tests for RankingEngine."""

    def _create_test_deal(self, price: float, rent: float, property_id: str) -> Deal:
        """Helper to create test deals."""
        prop = Property(
            id=property_id,
            address=f"123 Test St #{property_id}",
            city="Indianapolis",
            state="IN",
            zip_code="46201",
            list_price=price,
            estimated_rent=rent,
            bedrooms=3,
            bathrooms=2,
            source="test",
        )
        return Deal(id=f"deal_{property_id}", property=prop)

    def test_score_deal(self):
        """Test scoring a single deal."""
        deal = self._create_test_deal(200000, 1800, "score_test")
        deal.analyze()

        market = Market(
            id="test_market",
            name="Test",
            metro="Test Metro",
            state="IN",
            avg_rent_to_price=0.7,
        )
        market_metrics = MarketMetrics.from_market(market)

        engine = RankingEngine()
        score = engine.score_deal(deal, market_metrics)

        assert score is not None
        assert 0 <= score.overall_score <= 100
        assert 0 <= score.financial_score <= 100
        assert 0 <= score.market_score <= 100

    def test_rank_deals(self):
        """Test ranking multiple deals."""
        deals = [
            self._create_test_deal(200000, 2200, "high"),  # Good ratio
            self._create_test_deal(200000, 1400, "low"),  # Poor ratio
            self._create_test_deal(150000, 1500, "mid"),  # Mid ratio
        ]

        engine = RankingEngine()
        ranked = engine.rank_deals(deals, apply_filters=False)

        # Deals should be ranked
        for i, deal in enumerate(ranked):
            assert deal.score is not None
            assert deal.score.rank == i + 1

    def test_filter_deals(self):
        """Test filtering deals by thresholds."""
        deals = [
            self._create_test_deal(200000, 2500, "pass"),  # Should pass
            self._create_test_deal(500000, 1500, "fail"),  # Should fail (low ratio)
        ]

        for deal in deals:
            deal.analyze()

        config = RankingConfig(
            min_cash_on_cash=0.05,
            min_cap_rate=0.04,
        )
        engine = RankingEngine(config)
        filtered = engine.filter_deals(deals)

        # Only the good deal should pass
        assert len(filtered) == 1
        assert filtered[0].property.id == "pass"

    def test_strategy_scoring(self):
        """Test strategy-specific scoring."""
        deal = self._create_test_deal(180000, 1800, "strategy_test")
        deal.analyze()

        engine = RankingEngine()
        score = engine.score_deal(deal)

        # Should have strategy scores
        assert InvestmentStrategy.CASH_FLOW.value in score.strategy_scores
        assert InvestmentStrategy.APPRECIATION.value in score.strategy_scores


class TestSensitivityAnalyzer:
    """Tests for SensitivityAnalyzer."""

    def _create_test_deal(self) -> Deal:
        """Create a deal for sensitivity testing."""
        prop = Property(
            id="sens_test",
            address="100 Stress Test Way",
            city="Indianapolis",
            state="IN",
            zip_code="46201",
            list_price=200000,
            estimated_rent=1800,
            bedrooms=3,
            bathrooms=2,
            source="test",
        )
        deal = Deal(id="sens_deal", property=prop)
        deal.analyze()
        return deal

    def test_basic_sensitivity(self):
        """Test basic sensitivity analysis."""
        deal = self._create_test_deal()
        analyzer = SensitivityAnalyzer()
        result = analyzer.analyze(deal)

        # Should have all required fields
        assert result.base_cash_flow is not None
        assert result.rate_increase_1pct_cash_flow is not None
        assert result.vacancy_10pct_cash_flow is not None
        assert result.rent_decrease_5pct_cash_flow is not None
        assert result.risk_rating in ["low", "medium", "high"]

    def test_rate_sensitivity(self):
        """Test interest rate sensitivity."""
        deal = self._create_test_deal()
        analyzer = SensitivityAnalyzer()
        result = analyzer.analyze(deal)

        # Higher rates should mean lower cash flow
        assert result.rate_increase_1pct_cash_flow < result.base_cash_flow
        assert result.rate_increase_2pct_cash_flow < result.rate_increase_1pct_cash_flow

    def test_vacancy_sensitivity(self):
        """Test vacancy rate sensitivity."""
        deal = self._create_test_deal()
        analyzer = SensitivityAnalyzer()
        result = analyzer.analyze(deal)

        # Higher vacancy should mean lower cash flow
        assert result.vacancy_15pct_cash_flow < result.vacancy_10pct_cash_flow

    def test_stress_scenarios(self):
        """Test combined stress scenarios."""
        deal = self._create_test_deal()
        analyzer = SensitivityAnalyzer()
        result = analyzer.analyze(deal)

        # Severe stress should be worse than moderate
        assert result.severe_stress_cash_flow <= result.moderate_stress_cash_flow
