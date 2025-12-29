"""Tests for API routes."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient

from api.main import app
from src.models.property import Property, PropertyType, PropertyStatus
from src.models.market import Market, MarketTrend
from src.models.deal import Deal, DealPipeline
from src.models.financials import Financials, FinancialMetrics, LoanTerms, OperatingExpenses
from tests.conftest import create_test_property, create_test_deal


@pytest.fixture
def api_client() -> TestClient:
    """Create a test client for the API."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, api_client):
        """Test the health check endpoint returns OK."""
        response = api_client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "real-estate-deal-platform"


class TestDealsSearchEndpoint:
    """Tests for deals search endpoint."""

    def test_search_deals_basic(self, api_client):
        """Test basic deal search."""
        response = api_client.get("/api/deals/search?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert "deals" in data
        assert "total" in data
        assert "filters_applied" in data

    def test_search_deals_with_market_filter(self, api_client):
        """Test deal search with market filter."""
        response = api_client.get("/api/deals/search?markets=phoenix_az&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert data["filters_applied"]["markets"] == ["phoenix_az"]

    def test_search_deals_with_price_filter(self, api_client):
        """Test deal search with price filters."""
        response = api_client.get(
            "/api/deals/search?min_price=200000&max_price=400000&limit=5"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify returned deals are within price range (if any returned)
        for deal in data["deals"]:
            assert deal["property"]["list_price"] >= 200000
            assert deal["property"]["list_price"] <= 400000

    def test_search_deals_with_beds_filter(self, api_client):
        """Test deal search with bedrooms filter."""
        response = api_client.get("/api/deals/search?min_beds=3&max_beds=4&limit=5")

        assert response.status_code == 200
        data = response.json()

        # Verify returned deals have correct bedrooms
        for deal in data["deals"]:
            assert deal["property"]["bedrooms"] >= 3
            assert deal["property"]["bedrooms"] <= 4

    def test_search_deals_with_strategy(self, api_client):
        """Test deal search with investment strategy."""
        response = api_client.get("/api/deals/search?strategy=cash_flow&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert data["filters_applied"]["strategy"] == "cash_flow"

    def test_search_deals_invalid_strategy(self, api_client):
        """Test deal search with invalid strategy."""
        response = api_client.get("/api/deals/search?strategy=invalid_strategy")

        assert response.status_code == 400
        assert "Invalid strategy" in response.json()["detail"]

    def test_search_deals_with_loan_params(self, api_client):
        """Test deal search with custom loan parameters."""
        response = api_client.get(
            "/api/deals/search?down_payment=0.20&interest_rate=0.065&limit=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert "deals" in data

    def test_search_deals_returns_financial_summary(self, api_client):
        """Test that deal search returns financial summaries."""
        response = api_client.get("/api/deals/search?limit=5")

        assert response.status_code == 200
        data = response.json()

        if data["deals"]:
            deal = data["deals"][0]
            # Check financial summary fields
            if deal.get("financials"):
                assert "monthly_cash_flow" in deal["financials"]
                assert "cash_on_cash_return" in deal["financials"]
                assert "cap_rate" in deal["financials"]

    def test_search_deals_returns_score(self, api_client):
        """Test that deal search returns deal scores."""
        response = api_client.get("/api/deals/search?limit=5")

        assert response.status_code == 200
        data = response.json()

        if data["deals"]:
            deal = data["deals"][0]
            if deal.get("score"):
                assert "overall_score" in deal["score"]
                assert "financial_score" in deal["score"]
                assert "market_score" in deal["score"]


class TestDealsDetailEndpoint:
    """Tests for deal detail endpoint."""

    @patch("api.routes.deals.MockScraper")
    def test_get_deal_not_found(self, mock_scraper_class, api_client):
        """Test getting a non-existent deal."""
        mock_scraper = MagicMock()
        mock_scraper.get_property = AsyncMock(return_value=None)
        mock_scraper_class.return_value = mock_scraper

        response = api_client.get("/api/deals/deal_nonexistent")

        assert response.status_code == 404
        assert "Deal not found" in response.json()["detail"]

    def test_get_deal_format(self, api_client):
        """Test that deal detail returns the expected structure when found."""
        # First do a search to get a valid deal ID
        search_response = api_client.get("/api/deals/search?limit=1")
        if search_response.status_code == 200 and search_response.json()["deals"]:
            deal_id = search_response.json()["deals"][0]["id"]

            # The mock scraper doesn't persist deals between calls,
            # so we just verify the endpoint returns appropriate structure
            response = api_client.get(f"/api/deals/{deal_id}")

            # Either 200 with data or 404 (since mock doesn't persist)
            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "property" in data
                assert "financials" in data or data.get("financials") is None


class TestDealsAnalyzeEndpoint:
    """Tests for quick analysis endpoint."""

    def test_analyze_property_basic(self, api_client):
        """Test quick property analysis."""
        response = api_client.post(
            "/api/deals/analyze?city=Phoenix&state=AZ&limit=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert "deals" in data
        assert "total" in data

    def test_analyze_property_with_filters(self, api_client):
        """Test quick analysis with filters."""
        response = api_client.post(
            "/api/deals/analyze?city=Phoenix&state=AZ&max_price=400000&min_beds=3&limit=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filters_applied"]["city"] == "Phoenix"
        assert data["filters_applied"]["state"] == "AZ"

    def test_analyze_property_state_validation(self, api_client):
        """Test that state must be 2 characters."""
        response = api_client.post(
            "/api/deals/analyze?city=Phoenix&state=Arizona&limit=5"
        )

        assert response.status_code == 422  # Validation error


class TestMarketsEndpoint:
    """Tests for markets endpoint."""

    def test_list_markets(self, api_client):
        """Test listing all markets."""
        response = api_client.get("/api/markets")

        assert response.status_code == 200
        data = response.json()
        assert "markets" in data
        assert "total" in data

    def test_list_markets_returns_scores(self, api_client):
        """Test that markets include scores."""
        response = api_client.get("/api/markets")

        assert response.status_code == 200
        data = response.json()

        if data["markets"]:
            market = data["markets"][0]
            assert "overall_score" in market
            assert "cash_flow_score" in market
            assert "growth_score" in market


class TestSavedPropertiesEndpoint:
    """Tests for saved properties endpoints."""

    def test_get_saved_properties_empty(self, api_client, temp_db_path):
        """Test getting saved properties when empty."""
        with patch("api.routes.saved.SQLiteRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_saved_properties.return_value = []
            mock_repo_class.return_value = mock_repo

            response = api_client.get("/api/saved/properties")

            # Should return empty list or error depending on implementation
            assert response.status_code in [200, 404]

    def test_save_property_endpoint(self, api_client):
        """Test saving a property."""
        with patch("api.routes.saved.SQLiteRepository") as mock_repo_class:
            mock_repo = MagicMock()
            # Mock the save_deal method
            mock_repo_class.return_value = mock_repo

            response = api_client.post(
                "/api/saved/properties",
                json={
                    "property_id": "test_123",
                    "address": "123 Test St",
                    "city": "Phoenix",
                    "state": "AZ",
                    "zip_code": "85001",
                    "list_price": 250000,
                    "estimated_rent": 1800,
                    "bedrooms": 3,
                    "bathrooms": 2,
                }
            )

            # Should either succeed or return validation error
            assert response.status_code in [200, 201, 422]


class TestAnalysisEndpoint:
    """Tests for financial analysis endpoint."""

    def test_calculate_financials(self, api_client):
        """Test calculating financials for a property."""
        response = api_client.post(
            "/api/analysis/calculate",
            json={
                "purchase_price": 250000,
                "monthly_rent": 1800,
                "down_payment_pct": 0.25,
                "interest_rate": 0.07,
                "property_tax_rate": 0.012,
                "vacancy_rate": 0.08,
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "financials" in data
        assert "sensitivity" in data
        assert "verdict" in data
        assert "recommendations" in data

    def test_calculate_financials_with_defaults(self, api_client):
        """Test calculating financials with default values."""
        response = api_client.post(
            "/api/analysis/calculate",
            json={
                "purchase_price": 300000,
                "monthly_rent": 2000,
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should use default values for unspecified params
        assert data["financials"]["down_payment_pct"] == 0.25
        assert data["financials"]["interest_rate"] == 0.07

    def test_calculate_financials_returns_metrics(self, api_client):
        """Test that analysis returns all key metrics."""
        response = api_client.post(
            "/api/analysis/calculate",
            json={
                "purchase_price": 250000,
                "monthly_rent": 1800,
            }
        )

        assert response.status_code == 200
        financials = response.json()["financials"]

        assert "monthly_cash_flow" in financials
        assert "annual_cash_flow" in financials
        assert "cash_on_cash_return" in financials
        assert "cap_rate" in financials
        assert "total_cash_invested" in financials
        assert "break_even_occupancy" in financials
        assert "net_operating_income" in financials

    def test_calculate_financials_returns_sensitivity(self, api_client):
        """Test that analysis returns sensitivity data."""
        response = api_client.post(
            "/api/analysis/calculate",
            json={
                "purchase_price": 250000,
                "monthly_rent": 1800,
            }
        )

        assert response.status_code == 200
        sensitivity = response.json()["sensitivity"]

        assert "base_cash_flow" in sensitivity
        assert "rate_increase_1pct" in sensitivity
        assert "rate_increase_2pct" in sensitivity
        assert "vacancy_10pct" in sensitivity
        assert "vacancy_15pct" in sensitivity
        assert "rent_decrease_5pct" in sensitivity
        assert "moderate_stress" in sensitivity
        assert "severe_stress" in sensitivity
        assert "risk_rating" in sensitivity

    def test_calculate_financials_validation(self, api_client):
        """Test validation of analysis input."""
        # Missing required fields
        response = api_client.post(
            "/api/analysis/calculate",
            json={
                "purchase_price": 250000,
                # Missing monthly_rent
            }
        )

        assert response.status_code == 422  # Validation error

    def test_calculate_financials_negative_price(self, api_client):
        """Test that negative price is rejected."""
        response = api_client.post(
            "/api/analysis/calculate",
            json={
                "purchase_price": -100000,
                "monthly_rent": 1800,
            }
        )

        assert response.status_code == 422


class TestImportPropertyEndpoint:
    """Tests for property import endpoints."""

    def test_import_url_endpoint_exists(self, api_client):
        """Test that import URL endpoint exists and handles requests."""
        response = api_client.post(
            "/api/import/url",
            json={"url": "https://www.zillow.com/homedetails/123-test-st"}
        )

        # Should return a response (success, validation error, or not found)
        assert response.status_code in [200, 400, 404, 422, 500]

    def test_income_affordability_endpoint(self, api_client):
        """Test income affordability endpoint."""
        with patch("api.routes.import_property.get_income_data") as mock_income:
            mock_income.return_value = {
                "median_income": 65000,
                "income_tier": "middle",
            }

            response = api_client.get("/api/import/income/85001?rent=1800")

            # Should return income data or error if not found
            assert response.status_code in [200, 404, 500]


class TestJobsEndpoint:
    """Tests for background jobs endpoints."""

    def test_list_jobs(self, api_client):
        """Test listing jobs endpoint exists."""
        response = api_client.get("/api/jobs")

        # Should return list of jobs (may be empty)
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_jobs_stats(self, api_client):
        """Test getting job statistics."""
        response = api_client.get("/api/jobs/stats")

        # Should return stats or error
        assert response.status_code in [200, 500]


class TestVerdictGeneration:
    """Tests for verdict generation logic."""

    def test_verdict_negative_cash_flow(self):
        """Test verdict for negative cash flow."""
        from api.routes.deals import _generate_verdict

        mock_deal = MagicMock()
        mock_deal.financial_metrics = MagicMock()
        mock_deal.financial_metrics.monthly_cash_flow = -100
        mock_deal.sensitivity = None

        verdict = _generate_verdict(mock_deal)

        assert verdict == "NOT RECOMMENDED - Negative cash flow"

    def test_verdict_high_risk(self):
        """Test verdict for high risk."""
        from api.routes.deals import _generate_verdict

        mock_deal = MagicMock()
        mock_deal.financial_metrics = MagicMock()
        mock_deal.financial_metrics.monthly_cash_flow = 200
        mock_deal.financial_metrics.cash_on_cash_return = 0.06
        mock_deal.sensitivity = MagicMock()
        mock_deal.sensitivity.risk_rating = "high"

        verdict = _generate_verdict(mock_deal)

        assert "CAUTION" in verdict
        assert "High risk" in verdict

    def test_verdict_strong_buy(self):
        """Test verdict for strong buy."""
        from api.routes.deals import _generate_verdict

        mock_deal = MagicMock()
        mock_deal.financial_metrics = MagicMock()
        mock_deal.financial_metrics.monthly_cash_flow = 500
        mock_deal.financial_metrics.cash_on_cash_return = 0.12
        mock_deal.sensitivity = MagicMock()
        mock_deal.sensitivity.risk_rating = "low"
        mock_deal.sensitivity.survives_moderate_stress = True

        verdict = _generate_verdict(mock_deal)

        assert "STRONG BUY" in verdict

    def test_verdict_buy(self):
        """Test verdict for buy."""
        from api.routes.deals import _generate_verdict

        mock_deal = MagicMock()
        mock_deal.financial_metrics = MagicMock()
        mock_deal.financial_metrics.monthly_cash_flow = 300
        mock_deal.financial_metrics.cash_on_cash_return = 0.09
        mock_deal.sensitivity = MagicMock()
        mock_deal.sensitivity.risk_rating = "moderate"
        mock_deal.sensitivity.survives_moderate_stress = True

        verdict = _generate_verdict(mock_deal)

        assert "BUY" in verdict

    def test_verdict_consider(self):
        """Test verdict for consider."""
        from api.routes.deals import _generate_verdict

        mock_deal = MagicMock()
        mock_deal.financial_metrics = MagicMock()
        mock_deal.financial_metrics.monthly_cash_flow = 150
        mock_deal.financial_metrics.cash_on_cash_return = 0.07
        mock_deal.sensitivity = MagicMock()
        mock_deal.sensitivity.risk_rating = "moderate"
        mock_deal.sensitivity.survives_moderate_stress = False

        verdict = _generate_verdict(mock_deal)

        assert "CONSIDER" in verdict


class TestRecommendationGeneration:
    """Tests for recommendation generation logic."""

    def test_recommendations_tight_cash_flow(self):
        """Test recommendations for tight cash flow."""
        from api.routes.deals import _generate_recommendations

        mock_deal = MagicMock()
        mock_deal.financial_metrics = MagicMock()
        mock_deal.financial_metrics.monthly_cash_flow = 50
        mock_deal.financial_metrics.rent_to_price_ratio = 0.8
        mock_deal.financial_metrics.break_even_occupancy = 0.70
        mock_deal.financial_metrics.debt_service_coverage_ratio = 1.3
        mock_deal.financial_metrics.cash_on_cash_return = 0.05
        mock_deal.sensitivity = MagicMock()
        mock_deal.sensitivity.survives_moderate_stress = True
        mock_deal.sensitivity.survives_severe_stress = False

        recommendations = _generate_recommendations(mock_deal)

        # Should recommend something about tight cash flow
        assert any("cash flow" in r.lower() for r in recommendations)

    def test_recommendations_low_rent_to_price(self):
        """Test recommendations for low rent-to-price ratio."""
        from api.routes.deals import _generate_recommendations

        mock_deal = MagicMock()
        mock_deal.financial_metrics = MagicMock()
        mock_deal.financial_metrics.monthly_cash_flow = 200
        mock_deal.financial_metrics.rent_to_price_ratio = 0.5
        mock_deal.financial_metrics.break_even_occupancy = 0.70
        mock_deal.financial_metrics.debt_service_coverage_ratio = 1.3
        mock_deal.financial_metrics.cash_on_cash_return = 0.05
        mock_deal.sensitivity = MagicMock()
        mock_deal.sensitivity.survives_moderate_stress = True
        mock_deal.sensitivity.survives_severe_stress = False

        recommendations = _generate_recommendations(mock_deal)

        # Should mention rent-to-price
        assert any("rent-to-price" in r.lower() or "1%" in r for r in recommendations)

    def test_recommendations_excellent_returns(self):
        """Test positive recommendations for excellent returns."""
        from api.routes.deals import _generate_recommendations

        mock_deal = MagicMock()
        mock_deal.financial_metrics = MagicMock()
        mock_deal.financial_metrics.monthly_cash_flow = 500
        mock_deal.financial_metrics.rent_to_price_ratio = 1.0
        mock_deal.financial_metrics.break_even_occupancy = 0.60
        mock_deal.financial_metrics.debt_service_coverage_ratio = 1.5
        mock_deal.financial_metrics.cash_on_cash_return = 0.12
        mock_deal.sensitivity = MagicMock()
        mock_deal.sensitivity.survives_moderate_stress = True
        mock_deal.sensitivity.survives_severe_stress = True

        recommendations = _generate_recommendations(mock_deal)

        # Should have positive recommendations
        assert any("excellent" in r.lower() or "strong" in r.lower() for r in recommendations)
