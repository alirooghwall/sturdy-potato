"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get authentication headers."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_login_success(self, client):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "", "password": ""},
        )
        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "roles" in data

    def test_unauthorized_without_token(self, client):
        """Test that endpoints require authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestEntityEndpoints:
    """Tests for entity management endpoints."""

    def test_list_entities(self, client, auth_headers):
        """Test listing entities."""
        response = client.get("/api/v1/entities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert isinstance(data["data"], list)

    def test_create_entity(self, client, auth_headers):
        """Test creating an entity."""
        entity_data = {
            "entity_type": "VEHICLE",
            "display_name": "Test Vehicle",
            "confidence_score": 0.8,
            "current_position": {
                "latitude": 34.5,
                "longitude": 69.1,
            },
            "attributes": {"type": "truck"},
        }

        response = client.post(
            "/api/v1/entities",
            headers=auth_headers,
            json=entity_data,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["entity_type"] == "VEHICLE"
        assert data["data"]["display_name"] == "Test Vehicle"
        assert "entity_id" in data["data"]

    def test_get_entity(self, client, auth_headers):
        """Test getting a specific entity."""
        # First create an entity
        entity_data = {
            "entity_type": "PERSONNEL",
            "display_name": "Test Person",
        }
        create_response = client.post(
            "/api/v1/entities",
            headers=auth_headers,
            json=entity_data,
        )
        entity_id = create_response.json()["data"]["entity_id"]

        # Then get it
        response = client.get(
            f"/api/v1/entities/{entity_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["entity_id"] == entity_id

    def test_entity_not_found(self, client, auth_headers):
        """Test getting non-existent entity."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/api/v1/entities/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestEventEndpoints:
    """Tests for event management endpoints."""

    def test_list_events(self, client, auth_headers):
        """Test listing events."""
        response = client.get("/api/v1/events", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_create_event(self, client, auth_headers):
        """Test creating an event."""
        event_data = {
            "event_type": "EXPLOSION",
            "severity": "HIGH",
            "title": "Test Explosion Event",
            "summary": "A test explosion event",
            "location": {
                "latitude": 34.5,
                "longitude": 69.1,
            },
            "region": "Kabul Province",
        }

        response = client.post(
            "/api/v1/events",
            headers=auth_headers,
            json=event_data,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["event_type"] == "EXPLOSION"
        assert data["data"]["severity"] == "HIGH"


class TestAlertEndpoints:
    """Tests for alert management endpoints."""

    def test_list_alerts(self, client, auth_headers):
        """Test listing alerts."""
        response = client.get("/api/v1/alerts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_alert_summary_by_severity(self, client, auth_headers):
        """Test getting alert summary by severity."""
        response = client.get(
            "/api/v1/alerts/summary/by-severity",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "CRITICAL" in data["data"]
        assert "HIGH" in data["data"]


class TestDashboardEndpoints:
    """Tests for dashboard endpoints."""

    def test_dashboard_overview(self, client, auth_headers):
        """Test getting dashboard overview."""
        response = client.get("/api/v1/dashboard/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "active_alerts" in data
        assert "threat_overview" in data
        assert "system_health" in data

    def test_situational_awareness(self, client, auth_headers):
        """Test getting situational awareness data."""
        response = client.get(
            "/api/v1/dashboard/situational-awareness",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "events" in data
        assert "alerts" in data

    def test_region_summary(self, client, auth_headers):
        """Test getting region summary."""
        response = client.get("/api/v1/dashboard/regions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "regions" in data
        assert "summary" in data


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints."""

    def test_threat_score_calculation(self, client, auth_headers):
        """Test threat score calculation."""
        request_data = {
            "entity_id": "00000000-0000-0000-0000-000000000001",
            "include_explanation": True,
        }

        response = client.post(
            "/api/v1/analytics/threat-score",
            headers=auth_headers,
            json=request_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "overall_score" in data["data"]
        assert "factor_scores" in data["data"]
        assert 0 <= data["data"]["overall_score"] <= 100

    def test_threat_trends(self, client, auth_headers):
        """Test getting threat trends."""
        response = client.get(
            "/api/v1/analytics/trends/threats",
            headers=auth_headers,
            params={"days": 7},
        )
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert "summary" in data
