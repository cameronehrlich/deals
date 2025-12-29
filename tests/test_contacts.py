"""
Tests for Phase 5.2: Contact & Outreach API.

Tests the contacts and communications API routes.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_property_id():
    """Return a sample property ID for testing."""
    return "test-property-123"


# ==================== Contact API Tests ====================

class TestContactsAPI:
    """Test contacts CRUD operations."""

    def test_create_contact(self, client, sample_property_id):
        """Test creating a new contact."""
        response = client.post(
            "/api/contacts",
            json={
                "name": "John Smith",
                "email": "john@example.com",
                "phone": "555-123-4567",
                "company": "ABC Realty",
                "contact_type": "listing_agent",
                "property_ids": [sample_property_id],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Smith"
        assert data["email"] == "john@example.com"
        assert data["contact_type"] == "listing_agent"
        assert "id" in data

    def test_create_contact_minimal(self, client):
        """Test creating a contact with minimal fields."""
        response = client.post(
            "/api/contacts",
            json={"name": "Jane Doe"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Jane Doe"

    def test_get_contacts_empty(self, client):
        """Test getting contacts when none exist for a property."""
        response = client.get("/api/contacts?property_id=nonexistent-property")
        assert response.status_code == 200
        # Should return empty list, not error
        assert isinstance(response.json(), list)

    def test_get_contacts_by_property(self, client, sample_property_id):
        """Test filtering contacts by property ID."""
        # First create a contact
        client.post(
            "/api/contacts",
            json={
                "name": "Property Agent",
                "property_ids": [sample_property_id],
            },
        )

        # Then fetch by property
        response = client.get(f"/api/contacts?property_id={sample_property_id}")
        assert response.status_code == 200
        contacts = response.json()
        # Should have at least the one we created
        assert len(contacts) >= 1

    def test_get_contact_by_id(self, client):
        """Test getting a single contact by ID."""
        # Create a contact first
        create_resp = client.post(
            "/api/contacts",
            json={"name": "Test Agent", "email": "test@example.com"},
        )
        contact_id = create_resp.json()["id"]

        # Fetch it
        response = client.get(f"/api/contacts/{contact_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Agent"

    def test_get_contact_not_found(self, client):
        """Test getting a nonexistent contact."""
        response = client.get("/api/contacts/nonexistent-id")
        assert response.status_code == 404

    def test_update_contact(self, client):
        """Test updating a contact."""
        # Create first
        create_resp = client.post(
            "/api/contacts",
            json={"name": "Original Name"},
        )
        contact_id = create_resp.json()["id"]

        # Update
        response = client.patch(
            f"/api/contacts/{contact_id}",
            json={"name": "Updated Name", "phone": "555-999-8888"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
        assert response.json()["phone"] == "555-999-8888"

    def test_delete_contact(self, client):
        """Test deleting a contact."""
        # Create first
        create_resp = client.post(
            "/api/contacts",
            json={"name": "To Delete"},
        )
        contact_id = create_resp.json()["id"]

        # Delete
        response = client.delete(f"/api/contacts/{contact_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify it's gone
        get_resp = client.get(f"/api/contacts/{contact_id}")
        assert get_resp.status_code == 404


# ==================== Communication API Tests ====================

class TestCommunicationsAPI:
    """Test communications logging."""

    @pytest.fixture
    def contact_id(self, client):
        """Create a contact and return its ID."""
        response = client.post(
            "/api/contacts",
            json={"name": "Comm Test Agent"},
        )
        return response.json()["id"]

    def test_create_communication(self, client, contact_id, sample_property_id):
        """Test logging a communication."""
        response = client.post(
            "/api/contacts/communications",
            json={
                "contact_id": contact_id,
                "property_id": sample_property_id,
                "comm_type": "email",
                "direction": "outbound",
                "subject": "Initial Inquiry",
                "content": "Hello, I'm interested in the property...",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["comm_type"] == "email"
        assert data["direction"] == "outbound"
        assert data["subject"] == "Initial Inquiry"

    def test_create_communication_minimal(self, client, contact_id):
        """Test logging a communication with minimal fields."""
        response = client.post(
            "/api/contacts/communications",
            json={
                "contact_id": contact_id,
                "comm_type": "call",
                "direction": "inbound",
            },
        )
        assert response.status_code == 200
        assert response.json()["comm_type"] == "call"

    def test_get_communications_by_property(self, client, contact_id, sample_property_id):
        """Test getting communications for a property."""
        # Log a communication first
        client.post(
            "/api/contacts/communications",
            json={
                "contact_id": contact_id,
                "property_id": sample_property_id,
                "comm_type": "email",
                "direction": "outbound",
            },
        )

        # Fetch communications
        response = client.get(f"/api/contacts/communications?property_id={sample_property_id}")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_communications_by_contact(self, client, contact_id):
        """Test getting communications for a contact."""
        # Log a communication
        client.post(
            "/api/contacts/communications",
            json={
                "contact_id": contact_id,
                "comm_type": "text",
                "direction": "outbound",
            },
        )

        # Fetch
        response = client.get(f"/api/contacts/communications?contact_id={contact_id}")
        assert response.status_code == 200
        assert len(response.json()) >= 1


# ==================== Email Template Tests ====================

class TestEmailTemplates:
    """Test email template functionality."""

    def test_get_templates(self, client):
        """Test getting available email templates."""
        response = client.get("/api/contacts/templates")
        assert response.status_code == 200
        templates = response.json()
        assert len(templates) >= 1
        # Verify template structure
        for template in templates:
            assert "id" in template
            assert "name" in template
            assert "subject" in template
            assert "body" in template

    def test_generate_email_initial_inquiry(self, client):
        """Test generating an initial inquiry email."""
        response = client.post(
            "/api/contacts/templates/initial_inquiry/generate",
            json={
                "template_id": "initial_inquiry",
                "variables": {
                    "agent_name": "John",
                    "address": "123 Main St",
                    "city": "Phoenix",
                    "list_price": "$350,000",
                    "sender_name": "Cameron",
                    "sender_email": "cameron@example.com",
                    "sender_phone": "555-123-4567",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "subject" in data
        assert "body" in data
        # Variables should be substituted
        assert "John" in data["body"]
        assert "123 Main St" in data["body"]

    def test_generate_email_missing_template(self, client):
        """Test generating email with nonexistent template."""
        response = client.post(
            "/api/contacts/templates/nonexistent/generate",
            json={"template_id": "nonexistent", "variables": {"agent_name": "Test"}},
        )
        assert response.status_code == 404


# ==================== Property Timeline Tests ====================

class TestPropertyTimeline:
    """Test property timeline aggregation."""

    def test_get_property_timeline(self, client, sample_property_id):
        """Test getting the full timeline for a property."""
        # Create a contact and communication
        contact_resp = client.post(
            "/api/contacts",
            json={
                "name": "Timeline Agent",
                "property_ids": [sample_property_id],
            },
        )
        contact_id = contact_resp.json()["id"]

        client.post(
            "/api/contacts/communications",
            json={
                "contact_id": contact_id,
                "property_id": sample_property_id,
                "comm_type": "email",
                "direction": "outbound",
            },
        )

        # Get timeline
        response = client.get(f"/api/contacts/properties/{sample_property_id}/timeline")
        assert response.status_code == 200
        data = response.json()
        assert "contacts" in data
        assert "communications" in data
        assert "total_contacts" in data
        assert "total_communications" in data
