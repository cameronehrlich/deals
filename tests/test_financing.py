"""
Tests for Phase 5.1: Financing Scenarios.

Tests the financing API routes and calculation logic.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routes.financing import (
    calculate_mortgage_payment,
    calculate_scenario,
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


# ==================== Unit Tests for Calculation Functions ====================

class TestMortgagePaymentCalculation:
    """Test mortgage payment calculation."""

    def test_standard_30yr_mortgage(self):
        """Test standard 30-year fixed mortgage calculation."""
        # $200,000 loan at 7% for 30 years
        payment = calculate_mortgage_payment(200000, 0.07, 30)
        # Should be approximately $1330.60
        assert 1330 < payment < 1332

    def test_15yr_mortgage(self):
        """Test 15-year fixed mortgage calculation."""
        # $200,000 loan at 6% for 15 years
        payment = calculate_mortgage_payment(200000, 0.06, 15)
        # Should be approximately $1687.71
        assert 1687 < payment < 1689

    def test_zero_principal(self):
        """Test with zero principal (cash purchase)."""
        payment = calculate_mortgage_payment(0, 0.07, 30)
        assert payment == 0

    def test_zero_interest(self):
        """Test with zero interest rate."""
        payment = calculate_mortgage_payment(120000, 0, 30)
        # Should be principal / total payments
        assert payment == 120000 / (30 * 12)

    def test_zero_term(self):
        """Test with zero term years."""
        payment = calculate_mortgage_payment(200000, 0.07, 0)
        assert payment == 0


class TestScenarioCalculation:
    """Test full scenario calculation."""

    def test_basic_scenario(self):
        """Test basic financing scenario calculation."""
        scenario = calculate_scenario(
            purchase_price=250000,
            monthly_rent=1800,
            down_payment_pct=0.25,
            interest_rate=0.07,
            loan_term_years=30,
        )

        # Check cash needed calculations
        assert scenario.down_payment == 62500  # 25% of 250k
        assert scenario.loan_amount == 187500  # 75% of 250k
        assert scenario.total_cash_needed > scenario.down_payment  # Includes closing

        # Check that monthly mortgage is calculated
        assert scenario.monthly_mortgage > 0

        # Check performance metrics
        assert scenario.cap_rate > 0
        assert scenario.gross_rent_multiplier > 0
        assert scenario.rent_to_price_ratio == 1800 / 250000

    def test_cash_purchase_scenario(self):
        """Test all-cash purchase scenario."""
        scenario = calculate_scenario(
            purchase_price=200000,
            monthly_rent=1500,
            down_payment_pct=1.0,  # 100% down = cash
            interest_rate=0,
            loan_term_years=0,
        )

        # No mortgage
        assert scenario.monthly_mortgage == 0
        assert scenario.loan_amount == 0
        assert scenario.down_payment == 200000

        # Cash flow should be positive (no P&I)
        assert scenario.monthly_cash_flow > 0

        # CoC should be lower than leveraged purchase
        assert scenario.cash_on_cash_return > 0

    def test_high_rent_property(self):
        """Test property with excellent rent-to-price ratio."""
        scenario = calculate_scenario(
            purchase_price=100000,
            monthly_rent=1200,  # 1.2% rent-to-price
            down_payment_pct=0.25,
            interest_rate=0.075,
            loan_term_years=30,
        )

        # Should have positive cash flow
        assert scenario.monthly_cash_flow > 0
        assert scenario.cash_on_cash_return > 0.05  # >5% CoC (realistic)

        # Should qualify for DSCR
        assert scenario.dscr >= 1.25
        assert scenario.qualifies_for_dscr is True
        assert scenario.dscr_status == "qualifies"

    def test_negative_cash_flow_property(self):
        """Test property that doesn't cash flow."""
        scenario = calculate_scenario(
            purchase_price=500000,
            monthly_rent=2000,  # 0.4% rent-to-price - very low
            down_payment_pct=0.20,
            interest_rate=0.08,
            loan_term_years=30,
        )

        # Should have negative cash flow
        assert scenario.monthly_cash_flow < 0
        assert scenario.cash_on_cash_return < 0

        # Should not qualify for DSCR
        assert scenario.dscr < 1.25
        assert scenario.qualifies_for_dscr is False

    def test_dscr_borderline(self):
        """Test property with borderline DSCR."""
        # Find parameters that give DSCR between 1.0 and 1.25
        scenario = calculate_scenario(
            purchase_price=200000,
            monthly_rent=1350,
            down_payment_pct=0.25,
            interest_rate=0.08,
            loan_term_years=30,
        )

        # Check DSCR status
        if 1.0 <= scenario.dscr < 1.25:
            assert scenario.dscr_status == "borderline"
        elif scenario.dscr >= 1.25:
            assert scenario.dscr_status == "qualifies"
        else:
            assert scenario.dscr_status == "does_not_qualify"

    def test_closing_costs_included(self):
        """Test that closing costs are included in total cash needed."""
        scenario = calculate_scenario(
            purchase_price=300000,
            monthly_rent=2000,
            down_payment_pct=0.25,
            interest_rate=0.07,
            loan_term_years=30,
            closing_cost_pct=0.03,
        )

        expected_down = 75000
        expected_closing = 9000  # 3% of 300k
        expected_total = expected_down + expected_closing

        assert scenario.down_payment == expected_down
        assert scenario.closing_costs == expected_closing
        assert scenario.total_cash_needed == expected_total

    def test_points_included(self):
        """Test that points are included in total cash needed."""
        scenario = calculate_scenario(
            purchase_price=200000,
            monthly_rent=1500,
            down_payment_pct=0.25,
            interest_rate=0.07,
            loan_term_years=30,
            points=2.0,  # 2 points
        )

        loan_amount = 150000  # 75% of 200k
        expected_points = loan_amount * 0.02  # 2% of loan

        assert scenario.points_cost == expected_points
        assert scenario.total_cash_needed == (
            scenario.down_payment + scenario.closing_costs + expected_points
        )


# ==================== API Integration Tests ====================

class TestLoanProductsAPI:
    """Test loan products API endpoints."""

    def test_get_loan_products(self, client):
        """Test getting all loan products."""
        response = client.get("/api/financing/loan-products")
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)
        # Should have default products seeded
        assert len(products) >= 1

    def test_get_default_loan_products(self, client):
        """Test getting only default loan products."""
        response = client.get("/api/financing/loan-products?defaults_only=true")
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)
        # All should be defaults
        for product in products:
            assert product["is_default"] is True

    def test_create_loan_product(self, client):
        """Test creating a new loan product."""
        data = {
            "name": "Test Product",
            "description": "Test loan product",
            "down_payment_pct": 0.30,
            "interest_rate": 0.065,
            "loan_term_years": 30,
            "loan_type": "conventional",
            "is_default": False,
        }
        response = client.post("/api/financing/loan-products", json=data)
        assert response.status_code == 200
        product = response.json()
        assert product["name"] == "Test Product"
        assert product["down_payment_pct"] == 0.30
        assert product["id"] is not None

    def test_update_loan_product(self, client):
        """Test updating a loan product."""
        # First create a product
        data = {
            "name": "Product to Update",
            "down_payment_pct": 0.25,
            "interest_rate": 0.07,
            "loan_term_years": 30,
        }
        create_response = client.post("/api/financing/loan-products", json=data)
        assert create_response.status_code == 200
        product_id = create_response.json()["id"]

        # Update it
        update_data = {"interest_rate": 0.075}
        update_response = client.patch(
            f"/api/financing/loan-products/{product_id}",
            json=update_data
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["interest_rate"] == 0.075

    def test_delete_loan_product(self, client):
        """Test deleting a loan product."""
        # First create a product
        data = {
            "name": "Product to Delete",
            "down_payment_pct": 0.25,
            "interest_rate": 0.07,
            "loan_term_years": 30,
        }
        create_response = client.post("/api/financing/loan-products", json=data)
        assert create_response.status_code == 200
        product_id = create_response.json()["id"]

        # Delete it
        delete_response = client.delete(f"/api/financing/loan-products/{product_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] is True

        # Verify it's gone
        get_response = client.get(f"/api/financing/loan-products/{product_id}")
        assert get_response.status_code == 404


class TestFinancingCalculateAPI:
    """Test financing calculation API endpoints."""

    def test_calculate_scenario(self, client):
        """Test calculating a financing scenario."""
        data = {
            "purchase_price": 250000,
            "monthly_rent": 1800,
            "down_payment_pct": 0.25,
            "interest_rate": 0.07,
            "loan_term_years": 30,
        }
        response = client.post("/api/financing/calculate", json=data)
        assert response.status_code == 200
        result = response.json()

        assert result["purchase_price"] == 250000
        assert result["monthly_rent"] == 1800
        assert result["down_payment"] == 62500
        assert result["loan_amount"] == 187500
        assert "monthly_cash_flow" in result
        assert "cash_on_cash_return" in result
        assert "dscr" in result

    def test_compare_scenarios(self, client):
        """Test comparing multiple financing scenarios."""
        data = {
            "purchase_price": 200000,
            "monthly_rent": 1500,
        }
        response = client.post("/api/financing/compare", json=data)
        assert response.status_code == 200
        scenarios = response.json()

        assert isinstance(scenarios, list)
        assert len(scenarios) >= 1  # At least one default product

        # Each scenario should have all required fields
        for scenario in scenarios:
            assert "monthly_cash_flow" in scenario
            assert "cash_on_cash_return" in scenario
            assert "dscr" in scenario

    def test_break_even_analysis(self, client):
        """Test break-even analysis."""
        data = {
            "purchase_price": 250000,
            "monthly_rent": 1800,
            "down_payment_pct": 0.25,
            "interest_rate": 0.07,
            "loan_term_years": 30,
            "target_cash_on_cash": 0.10,
            "target_cash_flow": 300,
        }
        response = client.post("/api/financing/break-even", json=data)
        assert response.status_code == 200
        result = response.json()

        assert "current_cash_flow" in result
        assert "current_coc" in result
        assert "break_even_rate" in result
        assert "break_even_vacancy" in result

    def test_dscr_check(self, client):
        """Test DSCR check endpoint."""
        response = client.get(
            "/api/financing/dscr-check",
            params={
                "purchase_price": 200000,
                "monthly_rent": 1500,
                "down_payment_pct": 0.25,
                "interest_rate": 0.075,
            }
        )
        assert response.status_code == 200
        result = response.json()

        assert "dscr" in result
        assert "qualifies" in result
        assert "status" in result
        assert "suggestions" in result


# ==================== Edge Cases ====================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_low_rent(self, client):
        """Test with very low rent (negative cash flow)."""
        data = {
            "purchase_price": 500000,
            "monthly_rent": 1000,
            "down_payment_pct": 0.20,
            "interest_rate": 0.08,
        }
        response = client.post("/api/financing/calculate", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["monthly_cash_flow"] < 0

    def test_very_high_down_payment(self, client):
        """Test with very high down payment."""
        data = {
            "purchase_price": 200000,
            "monthly_rent": 1500,
            "down_payment_pct": 0.50,  # 50% down
            "interest_rate": 0.07,
        }
        response = client.post("/api/financing/calculate", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["down_payment"] == 100000
        assert result["loan_amount"] == 100000

    def test_short_term_loan(self, client):
        """Test with short loan term (hard money style)."""
        data = {
            "purchase_price": 200000,
            "monthly_rent": 1500,
            "down_payment_pct": 0.25,
            "interest_rate": 0.12,  # 12% hard money rate
            "loan_term_years": 1,
            "points": 2.0,
        }
        response = client.post("/api/financing/calculate", json=data)
        assert response.status_code == 200
        result = response.json()
        # Higher monthly payment due to short term
        assert result["monthly_mortgage"] > 10000

    def test_missing_product_404(self, client):
        """Test 404 for missing loan product."""
        response = client.get("/api/financing/loan-products/nonexistent-id")
        assert response.status_code == 404
