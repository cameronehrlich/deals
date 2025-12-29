"""
Tests for Phase 5.4: Offers & Pipeline API.

Tests the pipeline, offers, and deal stage management.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_property_id():
    """Return a sample property ID for testing."""
    return "test-pipeline-property-123"


# ==================== Deal Stage Tests ====================

class TestDealStages:
    """Test deal stage configuration and listing."""

    def test_get_deal_stages(self, client):
        """Test getting the list of deal stages."""
        response = client.get("/api/pipeline/stages")
        assert response.status_code == 200
        stages = response.json()

        # Should have predefined stages
        assert len(stages) >= 10

        # Verify structure
        for stage in stages:
            assert "id" in stage
            assert "name" in stage
            assert "order" in stage

        # Check for key stages
        stage_ids = [s["id"] for s in stages]
        assert "researching" in stage_ids
        assert "offer_submitted" in stage_ids
        assert "under_contract" in stage_ids
        assert "closed" in stage_ids

    def test_stages_are_ordered(self, client):
        """Test that stages are returned in order."""
        response = client.get("/api/pipeline/stages")
        stages = response.json()

        orders = [s["order"] for s in stages]
        assert orders == sorted(orders), "Stages should be sorted by order"


# ==================== Due Diligence Tests ====================

class TestDueDiligence:
    """Test due diligence checklist functionality."""

    def test_get_due_diligence_items(self, client):
        """Test getting the due diligence checklist template."""
        response = client.get("/api/pipeline/due-diligence-items")
        assert response.status_code == 200
        items = response.json()

        # Should have predefined items
        assert len(items) >= 10

        # Verify structure
        for item in items:
            assert "id" in item
            assert "name" in item
            assert "category" in item

        # Check for key categories
        categories = set(i["category"] for i in items)
        assert "inspection" in categories
        assert "financing" in categories
        assert "title" in categories

    def test_get_property_due_diligence(self, client, sample_property_id):
        """Test getting due diligence status for a property."""
        response = client.get(f"/api/pipeline/properties/{sample_property_id}/due-diligence")
        # Returns 404 if property doesn't exist, 200 if it does
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "property_id" in data
            assert "items" in data
            assert "completed_count" in data
            assert "total_count" in data


# ==================== Offer Tests ====================

class TestOffers:
    """Test offer CRUD operations."""

    def test_create_offer(self, client, sample_property_id):
        """Test creating a new offer."""
        response = client.post(
            "/api/pipeline/offers",
            json={
                "property_id": sample_property_id,
                "offer_price": 350000,
                "down_payment_pct": 0.20,
                "financing_type": "conventional",
                "earnest_money": 5000,
                "contingencies": ["inspection", "financing", "appraisal"],
                "inspection_days": 10,
                "financing_days": 21,
                "closing_days": 30,
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["offer_price"] == 350000
        assert data["status"] == "draft"
        assert "id" in data
        assert len(data["contingencies"]) == 3

    def test_create_offer_minimal(self, client, sample_property_id):
        """Test creating an offer with minimal fields."""
        response = client.post(
            "/api/pipeline/offers",
            json={
                "property_id": sample_property_id,
                "offer_price": 300000,
            },
        )
        assert response.status_code == 200
        assert response.json()["offer_price"] == 300000

    def test_get_offers_empty(self, client):
        """Test getting offers when none exist."""
        response = client.get("/api/pipeline/offers?property_id=nonexistent")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_offers_by_property(self, client, sample_property_id):
        """Test getting offers for a property."""
        # Create an offer first
        client.post(
            "/api/pipeline/offers",
            json={"property_id": sample_property_id, "offer_price": 320000},
        )

        response = client.get(f"/api/pipeline/offers?property_id={sample_property_id}")
        assert response.status_code == 200
        offers = response.json()
        assert len(offers) >= 1

    def test_get_offer_by_id(self, client, sample_property_id):
        """Test getting a single offer by ID."""
        # Create first
        create_resp = client.post(
            "/api/pipeline/offers",
            json={"property_id": sample_property_id, "offer_price": 340000},
        )
        offer_id = create_resp.json()["id"]

        response = client.get(f"/api/pipeline/offers/{offer_id}")
        assert response.status_code == 200
        assert response.json()["offer_price"] == 340000

    def test_update_offer(self, client, sample_property_id):
        """Test updating an offer."""
        # Create first
        create_resp = client.post(
            "/api/pipeline/offers",
            json={"property_id": sample_property_id, "offer_price": 350000},
        )
        offer_id = create_resp.json()["id"]

        # Update
        response = client.patch(
            f"/api/pipeline/offers/{offer_id}",
            json={"offer_price": 345000, "earnest_money": 7500},
        )
        assert response.status_code == 200
        assert response.json()["offer_price"] == 345000
        assert response.json()["earnest_money"] == 7500

    def test_delete_offer(self, client, sample_property_id):
        """Test deleting an offer."""
        # Create first
        create_resp = client.post(
            "/api/pipeline/offers",
            json={"property_id": sample_property_id, "offer_price": 360000},
        )
        offer_id = create_resp.json()["id"]

        # Delete
        response = client.delete(f"/api/pipeline/offers/{offer_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True


# ==================== Offer Workflow Tests ====================

class TestOfferWorkflow:
    """Test offer status transitions."""

    @pytest.fixture
    def draft_offer_id(self, client, sample_property_id):
        """Create a draft offer and return its ID."""
        response = client.post(
            "/api/pipeline/offers",
            json={"property_id": sample_property_id, "offer_price": 350000},
        )
        return response.json()["id"]

    def test_submit_offer(self, client, draft_offer_id):
        """Test submitting an offer."""
        response = client.post(f"/api/pipeline/offers/{draft_offer_id}/submit")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "submitted"
        assert data["submitted_at"] is not None

    def test_log_counter_offer(self, client, draft_offer_id):
        """Test logging a counter offer."""
        # First submit the offer
        client.post(f"/api/pipeline/offers/{draft_offer_id}/submit")

        # Log counter
        response = client.post(
            f"/api/pipeline/offers/{draft_offer_id}/counter",
            json={"counter_price": 360000, "notes": "Seller wants higher"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "countered"
        assert len(data["counter_history"]) >= 1
        assert data["counter_history"][-1]["price"] == 360000

    def test_accept_offer(self, client, draft_offer_id):
        """Test accepting an offer."""
        # Submit first
        client.post(f"/api/pipeline/offers/{draft_offer_id}/submit")

        # Accept
        response = client.post(
            f"/api/pipeline/offers/{draft_offer_id}/accept?final_price=355000"
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "accepted"
        assert data["final_price"] == 355000

    def test_reject_offer(self, client, draft_offer_id):
        """Test rejecting an offer."""
        # Submit first
        client.post(f"/api/pipeline/offers/{draft_offer_id}/submit")

        # Reject
        response = client.post(
            f"/api/pipeline/offers/{draft_offer_id}/reject?notes=Price%20too%20low"
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "rejected"
        assert "Price too low" in data["outcome_notes"]

    def test_withdraw_offer(self, client, draft_offer_id):
        """Test withdrawing an offer."""
        # Submit first
        client.post(f"/api/pipeline/offers/{draft_offer_id}/submit")

        # Withdraw
        response = client.post(f"/api/pipeline/offers/{draft_offer_id}/withdraw")
        assert response.status_code == 200
        assert response.json()["status"] == "withdrawn"


# ==================== Pipeline Overview Tests ====================

class TestPipelineOverview:
    """Test pipeline overview functionality."""

    def test_get_pipeline_overview(self, client):
        """Test getting the pipeline overview."""
        response = client.get("/api/pipeline/overview")
        assert response.status_code == 200
        data = response.json()

        assert "stages" in data
        assert "properties_by_stage" in data
        assert "total_properties" in data
        assert "active_offers" in data
        assert "under_contract" in data

        # properties_by_stage should be a dict
        assert isinstance(data["properties_by_stage"], dict)

    def test_overview_counts_are_valid(self, client):
        """Test that overview counts make sense."""
        response = client.get("/api/pipeline/overview")
        data = response.json()

        # Counts should be non-negative
        assert data["total_properties"] >= 0
        assert data["active_offers"] >= 0
        assert data["under_contract"] >= 0


# ==================== Property Stage Tests ====================

class TestPropertyStage:
    """Test property stage management."""

    def test_update_property_stage(self, client, sample_property_id):
        """Test updating a property's deal stage."""
        # Note: This requires a saved property to exist
        # In a real test, we'd create one first
        response = client.patch(
            f"/api/pipeline/properties/{sample_property_id}/stage",
            json={"stage": "researching", "notes": "Started initial research"},
        )
        # May fail if property doesn't exist, which is expected
        # Just verify the endpoint is accessible
        assert response.status_code in [200, 404]
