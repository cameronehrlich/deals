"""Tests for data models."""

import pytest
from src.models.property import Property, PropertyType, PropertyStatus
from src.models.financials import Financials, FinancialMetrics, LoanTerms, OperatingExpenses
from src.models.market import Market, MarketMetrics
from src.models.deal import Deal, DealScore


class TestProperty:
    """Tests for Property model."""

    def test_property_creation(self):
        """Test basic property creation."""
        prop = Property(
            id="test_001",
            address="123 Main St",
            city="Indianapolis",
            state="IN",
            zip_code="46201",
            list_price=200000,
            estimated_rent=1500,
            bedrooms=3,
            bathrooms=2,
            sqft=1500,
            source="test",
        )

        assert prop.id == "test_001"
        assert prop.list_price == 200000
        assert prop.full_address == "123 Main St, Indianapolis, IN 46201"

    def test_price_per_sqft_calculation(self):
        """Test automatic price per sqft calculation."""
        prop = Property(
            id="test_002",
            address="456 Oak Ave",
            city="Cleveland",
            state="OH",
            zip_code="44102",
            list_price=150000,
            bedrooms=3,
            bathrooms=1.5,
            sqft=1200,
            source="test",
        )

        assert prop.price_per_sqft == 125  # 150000 / 1200

    def test_gross_rent_multiplier(self):
        """Test GRM calculation."""
        prop = Property(
            id="test_003",
            address="789 Elm St",
            city="Memphis",
            state="TN",
            zip_code="38103",
            list_price=120000,
            estimated_rent=1200,
            bedrooms=3,
            bathrooms=2,
            source="test",
        )

        assert prop.gross_rent_multiplier == pytest.approx(8.33, rel=0.01)

    def test_price_reduction_percentage(self):
        """Test price reduction calculation."""
        prop = Property(
            id="test_004",
            address="101 Pine Rd",
            city="Tampa",
            state="FL",
            zip_code="33602",
            list_price=270000,
            original_price=300000,
            bedrooms=4,
            bathrooms=2,
            source="test",
        )

        assert prop.price_reduction_pct == pytest.approx(10.0, rel=0.01)


class TestFinancials:
    """Tests for Financials model."""

    def test_basic_calculation(self):
        """Test basic financial calculations."""
        fin = Financials(
            property_id="test_001",
            purchase_price=200000,
            estimated_rent=1800,
        )
        fin.calculate()

        # Down payment (25% default)
        assert fin.down_payment == 50000

        # Loan amount
        assert fin.loan_amount == 150000

        # Closing costs (3% default)
        assert fin.closing_costs == 6000

        # Total cash needed
        assert fin.total_cash_needed == 56000

        # Mortgage should be positive
        assert fin.monthly_mortgage > 0

    def test_cash_flow_calculation(self):
        """Test cash flow is calculated correctly."""
        fin = Financials(
            property_id="test_002",
            purchase_price=150000,
            estimated_rent=1500,
            loan=LoanTerms(
                down_payment_pct=0.25,
                interest_rate=0.07,
            ),
            expenses=OperatingExpenses(
                vacancy_rate=0.08,
                property_management_rate=0.10,
            ),
        )
        fin.calculate()

        # Monthly cash flow should be calculated
        assert fin.monthly_cash_flow is not None
        # Annual cash flow = monthly * 12
        assert fin.annual_cash_flow == pytest.approx(fin.monthly_cash_flow * 12, rel=0.01)

    def test_financial_metrics(self):
        """Test financial metrics calculation."""
        fin = Financials(
            property_id="test_003",
            purchase_price=200000,
            estimated_rent=2000,
        )
        fin.calculate()

        metrics = FinancialMetrics.from_financials(fin)

        # CoC should be calculated
        assert metrics.cash_on_cash_return is not None

        # Cap rate should be NOI / price
        assert metrics.cap_rate > 0

        # Rent to price ratio (1% rule check)
        assert metrics.rent_to_price_ratio == pytest.approx(1.0, rel=0.01)  # 2000/200000 = 1%


class TestMarket:
    """Tests for Market model."""

    def test_market_metrics_calculation(self):
        """Test market metrics scoring."""
        market = Market(
            id="test_market",
            name="Test City",
            metro="Test Metro",
            state="TX",
            population=1000000,
            population_growth_1yr=2.0,
            job_growth_1yr=3.0,
            median_household_income=60000,
            median_home_price=250000,
            median_rent=1500,
            avg_rent_to_price=0.72,
            days_on_market_avg=30,
            landlord_friendly=True,
        )

        metrics = MarketMetrics.from_market(market)

        # All scores should be in valid range
        assert 0 <= metrics.overall_score <= 100
        assert 0 <= metrics.growth_score <= 100
        assert 0 <= metrics.cash_flow_score <= 100
        assert 0 <= metrics.stability_score <= 100
        assert 0 <= metrics.liquidity_score <= 100


class TestDeal:
    """Tests for Deal model."""

    def test_deal_analysis(self):
        """Test complete deal analysis."""
        prop = Property(
            id="deal_test_001",
            address="100 Investment Way",
            city="Indianapolis",
            state="IN",
            zip_code="46201",
            list_price=180000,
            estimated_rent=1600,
            bedrooms=3,
            bathrooms=2,
            sqft=1400,
            year_built=1990,
            days_on_market=45,
            source="test",
        )

        deal = Deal(id="deal_001", property=prop)
        deal.analyze()

        # Financials should be calculated
        assert deal.financials is not None
        assert deal.financial_metrics is not None

        # Should have pros/cons generated
        assert len(deal.pros) > 0 or len(deal.cons) > 0
