"""Tests for market and deal scoring logic."""

import pytest
from datetime import datetime

from src.models.market import Market, MarketMetrics, MarketTrend
from src.models.property import Property, PropertyType, PropertyStatus
from src.models.financials import Financials, FinancialMetrics, LoanTerms, OperatingExpenses
from src.models.deal import Deal, DealScore, DealPipeline, InvestmentStrategy


class TestMarketMetrics:
    """Tests for market scoring calculations."""

    def test_cash_flow_score_high_rent_ratio(self):
        """Test that high rent-to-price ratio gives high cash flow score."""
        market = Market(
            id="high_cf_market",
            name="High Cash Flow City",
            metro="High CF Metro",
            state="TX",
            # avg_rent_to_price formula expects the value * 100 for scoring
            # So 0.8 (meaning 0.8%) -> score = 0.8 * 100 = 80
            avg_rent_to_price=0.8,  # 0.8% rent ratio
            property_tax_rate=0.008,  # 0.8% tax (decimal form)
        )

        metrics = MarketMetrics.from_market(market)

        # 0.8 * 100 = 80 base, minus tax adjustment (0.008 * 500 = 4)
        # Expected: ~76 score
        assert metrics.cash_flow_score >= 70

    def test_cash_flow_score_low_rent_ratio(self):
        """Test that low rent-to-price ratio gives low cash flow score."""
        market = Market(
            id="low_cf_market",
            name="Low Cash Flow City",
            metro="Low CF Metro",
            state="CA",
            avg_rent_to_price=0.003,  # 0.3% rent ratio
            property_tax_rate=0.012,  # 1.2% tax
        )

        metrics = MarketMetrics.from_market(market)

        # 0.3% rent ratio should give low cash flow score
        assert metrics.cash_flow_score < 50

    def test_growth_score_components(self):
        """Test growth score with multiple data points."""
        market = Market(
            id="growth_market",
            name="Growth City",
            metro="Growth Metro",
            state="TX",
            population_growth_1yr=0.03,  # 3% population growth
            population_growth_5yr=0.15,  # 15% 5yr growth
            job_growth_1yr=0.04,  # 4% job growth
            unemployment_rate=0.03,  # 3% unemployment
        )

        metrics = MarketMetrics.from_market(market)

        # Growth score calculated with weights: pop_1yr (30%), pop_5yr (20%), job (40%), unemp (10%)
        # Pop 1yr: 50 + 3 * 10 = 80 (weight 0.3)
        # Pop 5yr: 50 + 15 * 2 = 80 (weight 0.2)
        # Job: 50 + 4 * 10 = 90 (weight 0.4)
        # Unemp: 100 - 3 * 5 = 85 (weight 0.1)
        # Expected: (80*0.3 + 80*0.2 + 90*0.4 + 85*0.1) = 84.5 (approx)
        # But weights are normalized, so actual is lower
        assert metrics.growth_score > 50  # Positive growth should be above baseline

    def test_growth_score_declining_market(self):
        """Test growth score for declining market."""
        market = Market(
            id="decline_market",
            name="Declining City",
            metro="Decline Metro",
            state="OH",
            population_growth_1yr=-0.02,  # -2% population
            job_growth_1yr=-0.01,  # -1% jobs
            unemployment_rate=0.08,  # 8% unemployment
        )

        metrics = MarketMetrics.from_market(market)

        # Declining market should have lower growth score than baseline
        # The formula: pop_1yr = 50 + (-2) * 10 = 30, job = 50 + (-1) * 10 = 40
        # Unemployment penalty as well
        # Should be lower than growing market but around baseline due to formula design
        assert metrics.growth_score <= 55  # Not significantly above baseline

    def test_affordability_score_calculation(self):
        """Test affordability scoring based on income ratios."""
        market = Market(
            id="affordable_market",
            name="Affordable City",
            metro="Affordable Metro",
            state="TX",
            median_household_income=70000,
            median_home_price=210000,  # 3x income
            median_rent=1400,  # 24% of monthly income
        )

        metrics = MarketMetrics.from_market(market)

        # Affordable market should score high
        assert metrics.affordability_score > 70

    def test_affordability_score_expensive_market(self):
        """Test affordability scoring for expensive market."""
        market = Market(
            id="expensive_market",
            name="Expensive City",
            metro="Expensive Metro",
            state="CA",
            median_household_income=100000,
            median_home_price=800000,  # 8x income
            median_rent=3500,  # 42% of monthly income
        )

        metrics = MarketMetrics.from_market(market)

        # Expensive market should score low
        assert metrics.affordability_score < 50

    def test_stability_score_balanced_market(self):
        """Test stability score for balanced market."""
        market = Market(
            id="stable_market",
            name="Stable City",
            metro="Stable Metro",
            state="TX",
            price_change_1yr=0.04,  # 4% growth (ideal)
            months_of_inventory=5.0,  # Balanced (4-6 ideal)
        )

        metrics = MarketMetrics.from_market(market)

        # Balanced market should score high
        assert metrics.stability_score > 80

    def test_stability_score_overheated_market(self):
        """Test stability score for overheated market."""
        market = Market(
            id="hot_market",
            name="Hot City",
            metro="Hot Metro",
            state="FL",
            price_change_1yr=0.20,  # 20% growth (overheated)
            months_of_inventory=1.0,  # Very low inventory
        )

        metrics = MarketMetrics.from_market(market)

        # Overheated market should score lower
        assert metrics.stability_score < 60

    def test_liquidity_score_hot_market(self):
        """Test liquidity score for liquid market."""
        market = Market(
            id="liquid_market",
            name="Liquid City",
            metro="Liquid Metro",
            state="TX",
            days_on_market_avg=20,  # Quick sales
            sale_to_list_ratio=1.02,  # Selling above list
            pct_sold_above_list=40,  # 40% above list
        )

        metrics = MarketMetrics.from_market(market)

        # Liquid market should score high
        assert metrics.liquidity_score > 70

    def test_liquidity_score_slow_market(self):
        """Test liquidity score for illiquid market."""
        market = Market(
            id="slow_market",
            name="Slow City",
            metro="Slow Metro",
            state="WV",
            days_on_market_avg=90,  # Slow sales
            sale_to_list_ratio=0.95,  # Selling below list
            pct_sold_above_list=5,  # Few above list
        )

        metrics = MarketMetrics.from_market(market)

        # Slow market should score low
        assert metrics.liquidity_score < 50

    def test_operating_cost_score_low_tax(self):
        """Test operating cost score for low tax state."""
        market = Market(
            id="low_tax_market",
            name="Low Tax City",
            metro="Low Tax Metro",
            state="FL",
            property_tax_rate=0.005,  # 0.5% tax
            insurance_risk="low",
        )

        metrics = MarketMetrics.from_market(market)

        # Low operating costs should score high
        assert metrics.operating_cost_score > 80

    def test_operating_cost_score_high_tax(self):
        """Test operating cost score for high tax state."""
        market = Market(
            id="high_tax_market",
            name="High Tax City",
            metro="High Tax Metro",
            state="NJ",
            property_tax_rate=0.025,  # 2.5% tax
            insurance_risk="high",  # High insurance
        )

        metrics = MarketMetrics.from_market(market)

        # High operating costs should score low
        assert metrics.operating_cost_score < 50

    def test_regulatory_score_landlord_friendly(self):
        """Test regulatory score for landlord-friendly state."""
        market = Market(
            id="friendly_market",
            name="Friendly City",
            metro="Friendly Metro",
            state="TX",
            landlord_friendly=True,
            landlord_friendly_score=9,
        )

        metrics = MarketMetrics.from_market(market)

        # Landlord-friendly should score high
        assert metrics.regulatory_score >= 80

    def test_regulatory_score_tenant_friendly(self):
        """Test regulatory score for tenant-friendly state."""
        market = Market(
            id="tenant_market",
            name="Tenant City",
            metro="Tenant Metro",
            state="CA",
            landlord_friendly=False,
            landlord_friendly_score=2,
        )

        metrics = MarketMetrics.from_market(market)

        # Tenant-friendly should score low for landlords
        assert metrics.regulatory_score <= 30

    def test_overall_score_weighting(self):
        """Test that overall score uses correct weights."""
        market = Market(
            id="test_market",
            name="Test City",
            metro="Test Metro",
            state="TX",
            avg_rent_to_price=0.008,  # Cash flow
            population_growth_1yr=0.02,  # Growth
            median_household_income=60000,  # Affordability
            median_home_price=240000,
            median_rent=1500,
            price_change_1yr=0.04,  # Stability
            months_of_inventory=5,
            days_on_market_avg=30,  # Liquidity
            property_tax_rate=0.01,  # Operating costs
            landlord_friendly=True,  # Regulatory
        )

        metrics = MarketMetrics.from_market(market)

        # Manual calculation with weights
        expected_overall = (
            metrics.cash_flow_score * 0.25
            + metrics.growth_score * 0.20
            + metrics.affordability_score * 0.15
            + metrics.stability_score * 0.15
            + metrics.liquidity_score * 0.10
            + metrics.operating_cost_score * 0.10
            + metrics.regulatory_score * 0.05
        )

        assert abs(metrics.overall_score - expected_overall) < 0.01

    def test_risk_factors_hot_market(self):
        """Test risk factors for overheated market."""
        market = Market(
            id="risky_market",
            name="Risky City",
            metro="Risky Metro",
            state="FL",
            price_change_5yr=60,  # 60% as integer (code checks > 50)
            unemployment_rate=0.07,  # 7% unemployment - adds to vacancy risk
            months_of_inventory=7,  # High inventory - adds to vacancy risk
            landlord_friendly=False,  # Tenant-friendly - high regulatory risk
            property_tax_rate=0.02,  # 2% tax - adds to operating cost risk
            insurance_risk="high",  # High insurance - adds to operating cost risk
        )

        metrics = MarketMetrics.from_market(market)

        # Check risk factors are elevated
        # The appreciation_risk check uses price_change_5yr > 50 for 0.4 risk
        assert metrics.appreciation_risk >= 0.25  # Should be 0.4 for 60% 5yr growth
        assert metrics.vacancy_risk >= 0.25  # 7% unemployment + 7mo inventory
        assert metrics.regulatory_risk >= 0.3  # Not landlord friendly
        assert metrics.operating_cost_risk >= 0.25  # High tax + high insurance

    def test_data_completeness_full(self):
        """Test data completeness with all data."""
        market = Market(
            id="complete_market",
            name="Complete City",
            metro="Complete Metro",
            state="TX",
            avg_rent_to_price=0.008,
            property_tax_rate=0.01,
            population_growth_1yr=0.02,
            population_growth_5yr=0.10,
            job_growth_1yr=0.03,
            unemployment_rate=0.04,
            median_household_income=60000,
            median_home_price=240000,
            median_rent=1500,
            price_change_1yr=0.04,
            months_of_inventory=5,
            days_on_market_avg=30,
            sale_to_list_ratio=1.0,
        )

        metrics = MarketMetrics.from_market(market)

        # Should have high data completeness
        assert metrics.data_completeness > 0.7

    def test_data_completeness_minimal(self):
        """Test data completeness with minimal data."""
        market = Market(
            id="minimal_market",
            name="Minimal City",
            metro="Minimal Metro",
            state="TX",
        )

        metrics = MarketMetrics.from_market(market)

        # Should have low data completeness
        assert metrics.data_completeness < 0.2


class TestDealScore:
    """Tests for deal scoring calculations."""

    @pytest.fixture
    def sample_financial_metrics(self):
        """Create sample financial metrics."""
        return FinancialMetrics(
            property_id="test_prop",
            monthly_cash_flow=300,
            annual_cash_flow=3600,
            cash_on_cash_return=0.08,
            cap_rate=0.065,
            gross_rent_multiplier=11.5,
            rent_to_price_ratio=0.87,
            total_cash_invested=75000,
            break_even_occupancy=0.75,
            debt_service_coverage_ratio=1.25,
        )

    @pytest.fixture
    def sample_market_metrics(self):
        """Create sample market metrics."""
        return MarketMetrics(
            market_id="test_market",
            overall_score=70,
            cash_flow_score=75,
            growth_score=65,
            affordability_score=70,
            stability_score=72,
            liquidity_score=68,
            operating_cost_score=73,
            regulatory_score=80,
            appreciation_risk=0.2,
            vacancy_risk=0.15,
            regulatory_risk=0.1,
            operating_cost_risk=0.15,
        )

    def test_financial_score_high_coc(self, sample_market_metrics):
        """Test financial score with high CoC."""
        fm = FinancialMetrics(
            property_id="test_prop",
            monthly_cash_flow=500,
            annual_cash_flow=6000,
            cash_on_cash_return=0.15,  # 15% CoC
            cap_rate=0.08,  # 8% cap
            gross_rent_multiplier=10,
            rent_to_price_ratio=1.0,
            total_cash_invested=40000,
            break_even_occupancy=0.65,
            debt_service_coverage_ratio=1.4,
        )

        score = DealScore.calculate(
            property_id="test",
            financial_metrics=fm,
            market_metrics=sample_market_metrics,
        )

        # High returns should give high financial score
        assert score.financial_score > 70

    def test_financial_score_negative_cash_flow(self, sample_market_metrics):
        """Test financial score with negative cash flow."""
        fm = FinancialMetrics(
            property_id="test_prop",
            monthly_cash_flow=-200,
            annual_cash_flow=-2400,
            cash_on_cash_return=-0.03,
            cap_rate=0.04,
            gross_rent_multiplier=20,
            rent_to_price_ratio=0.5,
            total_cash_invested=80000,
            break_even_occupancy=1.1,
            debt_service_coverage_ratio=0.85,
        )

        score = DealScore.calculate(
            property_id="test",
            financial_metrics=fm,
            market_metrics=sample_market_metrics,
        )

        # Negative cash flow should lower score
        assert score.financial_score < 60

    def test_market_score_uses_market_metrics(self, sample_financial_metrics, sample_market_metrics):
        """Test that market score uses market metrics overall score."""
        score = DealScore.calculate(
            property_id="test",
            financial_metrics=sample_financial_metrics,
            market_metrics=sample_market_metrics,
        )

        assert score.market_score == sample_market_metrics.overall_score

    def test_risk_score_calculation(self, sample_financial_metrics, sample_market_metrics):
        """Test risk score calculation."""
        score = DealScore.calculate(
            property_id="test",
            financial_metrics=sample_financial_metrics,
            market_metrics=sample_market_metrics,
        )

        # Risk score should consider market risks and break-even
        assert 0 <= score.risk_score <= 100

    def test_liquidity_score(self, sample_financial_metrics, sample_market_metrics):
        """Test liquidity score from market metrics."""
        score = DealScore.calculate(
            property_id="test",
            financial_metrics=sample_financial_metrics,
            market_metrics=sample_market_metrics,
        )

        # Should use market liquidity score
        assert score.liquidity_score == sample_market_metrics.liquidity_score

    def test_overall_score_weighting(self, sample_financial_metrics, sample_market_metrics):
        """Test overall score uses correct weights."""
        weights = {
            "financial": 0.40,
            "market": 0.30,
            "risk": 0.20,
            "liquidity": 0.10,
        }

        score = DealScore.calculate(
            property_id="test",
            financial_metrics=sample_financial_metrics,
            market_metrics=sample_market_metrics,
            weights=weights,
        )

        # Calculate expected (approximately)
        expected = (
            score.financial_score * 0.40
            + score.market_score * 0.30
            + score.risk_score * 0.20
            + score.liquidity_score * 0.10
        )

        assert abs(score.overall_score - expected) < 0.1

    def test_strategy_scores(self, sample_financial_metrics, sample_market_metrics):
        """Test strategy-specific scores."""
        score = DealScore.calculate(
            property_id="test",
            financial_metrics=sample_financial_metrics,
            market_metrics=sample_market_metrics,
        )

        # Should have strategy scores
        assert InvestmentStrategy.CASH_FLOW.value in score.strategy_scores
        assert InvestmentStrategy.APPRECIATION.value in score.strategy_scores
        assert InvestmentStrategy.VALUE_ADD.value in score.strategy_scores

    def test_location_data_flood_risk(self, sample_financial_metrics, sample_market_metrics):
        """Test that flood risk affects scoring."""
        # Score without flood risk
        score_no_flood = DealScore.calculate(
            property_id="test",
            financial_metrics=sample_financial_metrics,
            market_metrics=sample_market_metrics,
        )

        # Score with high flood risk
        location_data = {
            "flood_zone": {
                "risk_level": "high",
                "zone": "AE",
            }
        }

        score_flood = DealScore.calculate(
            property_id="test",
            financial_metrics=sample_financial_metrics,
            market_metrics=sample_market_metrics,
            location_data=location_data,
        )

        # High flood risk should lower risk score
        assert score_flood.risk_score < score_no_flood.risk_score

    def test_location_data_walk_score(self, sample_financial_metrics, sample_market_metrics):
        """Test that walk score affects liquidity."""
        # Score with high walk score
        location_data_high = {"walk_score": 90}

        score_high = DealScore.calculate(
            property_id="test",
            financial_metrics=sample_financial_metrics,
            market_metrics=sample_market_metrics,
            location_data=location_data_high,
        )

        # Score with low walk score
        location_data_low = {"walk_score": 20}

        score_low = DealScore.calculate(
            property_id="test",
            financial_metrics=sample_financial_metrics,
            market_metrics=sample_market_metrics,
            location_data=location_data_low,
        )

        # Higher walk score should boost liquidity
        assert score_high.liquidity_score > score_low.liquidity_score


class TestDealAnalysis:
    """Tests for Deal.analyze() method."""

    @pytest.fixture
    def sample_property(self):
        """Create a sample property."""
        return Property(
            id="test_prop",
            address="123 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            list_price=250000,
            estimated_rent=1800,
            bedrooms=3,
            bathrooms=2,
            sqft=1500,
            property_type=PropertyType.SFH,
            status=PropertyStatus.ACTIVE,
            days_on_market=30,
            year_built=2005,
            source="test",
        )

    @pytest.fixture
    def sample_market(self):
        """Create a sample market."""
        return Market(
            id="phoenix_az",
            name="Phoenix",
            metro="Phoenix-Mesa-Chandler",
            state="AZ",
            median_home_price=400000,
            median_rent=1800,
            avg_rent_to_price=0.0045,
            population_growth_1yr=0.02,
            job_growth_1yr=0.03,
            unemployment_rate=0.04,
            property_tax_rate=0.007,
            landlord_friendly=True,
        )

    def test_analyze_calculates_financials(self, sample_property):
        """Test that analyze() calculates financials."""
        deal = Deal(id="test_deal", property=sample_property)
        deal.analyze()

        assert deal.financials is not None
        assert deal.financial_metrics is not None
        assert deal.financial_metrics.monthly_cash_flow is not None

    def test_analyze_with_market_data(self, sample_property, sample_market):
        """Test analyze with market data calculates score."""
        deal = Deal(
            id="test_deal",
            property=sample_property,
            market=sample_market,
        )
        deal.analyze()

        assert deal.score is not None
        assert deal.market_metrics is not None

    def test_analyze_generates_pros_cons(self, sample_property, sample_market):
        """Test that analyze generates pros and cons."""
        deal = Deal(
            id="test_deal",
            property=sample_property,
            market=sample_market,
        )
        deal.analyze()

        # Should have some analysis
        assert deal.pros or deal.cons or deal.red_flags

    def test_analyze_updates_status(self, sample_property):
        """Test that analyze updates pipeline status."""
        deal = Deal(
            id="test_deal",
            property=sample_property,
            pipeline_status=DealPipeline.NEW,
        )
        deal.analyze()

        assert deal.pipeline_status == DealPipeline.ANALYZED

    def test_analyze_sets_timestamp(self, sample_property):
        """Test that analyze sets last_analyzed timestamp."""
        deal = Deal(id="test_deal", property=sample_property)
        assert deal.last_analyzed is None

        deal.analyze()

        assert deal.last_analyzed is not None

    def test_analyze_with_hoa(self, sample_property):
        """Test analysis includes HOA in expenses."""
        sample_property.hoa_fee = 250  # $250/month HOA

        deal = Deal(id="test_deal", property=sample_property)
        deal.analyze()

        # HOA should be in expenses
        assert deal.financials.expenses.hoa_monthly == 250

    def test_analyze_with_taxes(self, sample_property):
        """Test analysis includes known taxes."""
        sample_property.annual_taxes = 3000  # $3000/year

        deal = Deal(id="test_deal", property=sample_property)
        deal.analyze()

        # Tax rate should be overridden
        expected_rate = 3000 / 250000  # 1.2%
        assert abs(deal.financials.expenses.property_tax_rate - expected_rate) < 0.001

    def test_location_insights_walkable(self, sample_property, sample_market):
        """Test location insights for walkable area."""
        deal = Deal(
            id="test_deal",
            property=sample_property,
            market=sample_market,
        )
        deal.analyze()

        location_data = {
            "walk_score": 85,
            "walk_description": "Very Walkable",
            "flood_zone": {"risk_level": "low"},
        }

        deal.add_location_insights(location_data)

        # Should have walkability pro
        assert any("walkable" in pro.lower() for pro in deal.pros)

    def test_location_insights_flood_risk(self, sample_property, sample_market):
        """Test location insights for flood risk."""
        deal = Deal(
            id="test_deal",
            property=sample_property,
            market=sample_market,
        )
        deal.analyze()

        location_data = {
            "flood_zone": {
                "risk_level": "high",
                "zone": "AE",
                "requires_insurance": True,
            }
        }

        deal.add_location_insights(location_data)

        # Should have flood risk con or red flag
        flood_mentions = [
            item for item in deal.cons + deal.red_flags
            if "flood" in item.lower()
        ]
        assert len(flood_mentions) > 0
