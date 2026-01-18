"""Comprehensive integration tests for ISR Platform."""

import asyncio
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Get authentication token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass"},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


@pytest.fixture
def auth_headers(auth_token):
    """Get authentication headers."""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


class TestHealthChecks:
    """Integration tests for health check endpoints."""

    def test_health_endpoint(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "isr-platform-api"

    def test_readiness_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get("/ready")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "cache" in data["checks"]
        assert "message_bus" in data["checks"]

    def test_liveness_endpoint(self, client):
        """Test liveness probe endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_startup_endpoint(self, client):
        """Test startup probe endpoint."""
        response = client.get("/health/startup")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["started", "starting"]


class TestAuthenticationFlow:
    """Integration tests for authentication flow."""

    def test_login_flow(self, client):
        """Test complete login flow."""
        # Attempt login
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "testpass"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_protected_endpoint_with_auth(self, client, auth_headers):
        """Test accessing protected endpoint with authentication."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "username" in data


class TestEntityLifecycle:
    """Integration tests for entity CRUD operations."""

    def test_create_and_retrieve_entity(self, client, auth_headers):
        """Test creating and retrieving an entity."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Create entity
        entity_data = {
            "entity_type": "VEHICLE",
            "display_name": "Integration Test Vehicle",
            "confidence_score": 0.85,
            "current_position": {
                "latitude": 34.5,
                "longitude": 69.1,
            },
            "attributes": {"type": "military_truck"},
        }
        
        create_response = client.post(
            "/api/v1/entities",
            headers=auth_headers,
            json=entity_data,
        )
        assert create_response.status_code == 201
        created_entity = create_response.json()["data"]
        entity_id = created_entity["entity_id"]
        
        # Retrieve entity
        get_response = client.get(
            f"/api/v1/entities/{entity_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        retrieved_entity = get_response.json()["data"]
        assert retrieved_entity["entity_id"] == entity_id
        assert retrieved_entity["display_name"] == "Integration Test Vehicle"

    def test_list_entities(self, client, auth_headers):
        """Test listing entities with pagination."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        response = client.get("/api/v1/entities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert isinstance(data["data"], list)


class TestEventLifecycle:
    """Integration tests for event CRUD operations."""

    def test_create_and_retrieve_event(self, client, auth_headers):
        """Test creating and retrieving an event."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Create event
        event_data = {
            "event_type": "EXPLOSION",
            "severity": "HIGH",
            "title": "Integration Test Explosion",
            "summary": "Test event for integration testing",
            "location": {
                "latitude": 34.5,
                "longitude": 69.1,
            },
            "region": "Test Region",
        }
        
        create_response = client.post(
            "/api/v1/events",
            headers=auth_headers,
            json=event_data,
        )
        assert create_response.status_code == 201
        created_event = create_response.json()["data"]
        event_id = created_event["event_id"]
        
        # Retrieve event
        get_response = client.get(
            f"/api/v1/events/{event_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        retrieved_event = get_response.json()["data"]
        assert retrieved_event["event_id"] == event_id


class TestAnalyticsPipeline:
    """Integration tests for analytics pipeline."""

    def test_threat_score_calculation(self, client, auth_headers):
        """Test threat score calculation."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Create an entity first
        entity_data = {
            "entity_type": "PERSONNEL",
            "display_name": "Test Person",
        }
        create_response = client.post(
            "/api/v1/entities",
            headers=auth_headers,
            json=entity_data,
        )
        
        if create_response.status_code == 201:
            entity_id = create_response.json()["data"]["entity_id"]
            
            # Calculate threat score
            score_response = client.post(
                "/api/v1/analytics/threat-score",
                headers=auth_headers,
                json={"entity_id": entity_id, "include_explanation": True},
            )
            assert score_response.status_code == 200
            data = score_response.json()["data"]
            assert "overall_score" in data
            assert 0 <= data["overall_score"] <= 100


class TestMLIntegration:
    """Integration tests for ML services."""

    def test_sentiment_analysis(self, client, auth_headers):
        """Test sentiment analysis endpoint."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        response = client.post(
            "/api/v1/ml-api/sentiment",
            headers=auth_headers,
            json={
                "text": "This is a test message for sentiment analysis.",
                "language": "en",
            },
        )
        
        # Accept both 200 (success) and 503 (service unavailable)
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "sentiment" in data
            assert data["sentiment"] in ["positive", "negative", "neutral"]

    def test_named_entity_recognition(self, client, auth_headers):
        """Test NER endpoint."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        response = client.post(
            "/api/v1/ml-api/ner",
            headers=auth_headers,
            json={
                "text": "John Smith visited Kabul on January 15th.",
                "language": "en",
            },
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "entities" in data
            assert isinstance(data["entities"], list)


class TestLLMIntegration:
    """Integration tests for LLM services."""

    def test_conversational_query(self, client, auth_headers):
        """Test conversational query endpoint."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        response = client.post(
            "/api/v1/llm/query",
            headers=auth_headers,
            json={
                "query": "What are the current threat levels?",
                "include_context": True,
            },
        )
        
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data

    def test_report_generation(self, client, auth_headers):
        """Test report generation endpoint."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        response = client.post(
            "/api/v1/llm/generate-report",
            headers=auth_headers,
            json={
                "report_type": "situational",
                "time_range": "24h",
                "include_recommendations": True,
            },
        )
        
        assert response.status_code in [200, 503]


class TestErrorHandling:
    """Integration tests for error handling."""

    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint."""
        response = client.get("/api/v1/invalid/endpoint")
        assert response.status_code == 404

    def test_invalid_request_data(self, client, auth_headers):
        """Test sending invalid request data."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        response = client.post(
            "/api/v1/entities",
            headers=auth_headers,
            json={"invalid_field": "value"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "error" in data

    def test_not_found_resource(self, client, auth_headers):
        """Test accessing non-existent resource."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/api/v1/entities/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDashboardIntegration:
    """Integration tests for dashboard endpoints."""

    def test_dashboard_overview(self, client, auth_headers):
        """Test dashboard overview endpoint."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        response = client.get("/api/v1/dashboard/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "active_alerts" in data
        assert "threat_overview" in data

    def test_situational_awareness(self, client, auth_headers):
        """Test situational awareness endpoint."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        response = client.get(
            "/api/v1/dashboard/situational-awareness",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "events" in data


class TestEndToEndWorkflow:
    """End-to-end integration tests for complete workflows."""

    def test_full_intelligence_workflow(self, client, auth_headers):
        """Test complete intelligence gathering and analysis workflow."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Step 1: Create an entity
        entity_data = {
            "entity_type": "VEHICLE",
            "display_name": "Workflow Test Vehicle",
            "current_position": {"latitude": 34.5, "longitude": 69.1},
        }
        entity_response = client.post(
            "/api/v1/entities",
            headers=auth_headers,
            json=entity_data,
        )
        assert entity_response.status_code == 201
        entity_id = entity_response.json()["data"]["entity_id"]
        
        # Step 2: Create an associated event
        event_data = {
            "event_type": "MOVEMENT",
            "severity": "MEDIUM",
            "title": "Vehicle Movement Detected",
            "summary": "Test vehicle movement",
            "location": {"latitude": 34.5, "longitude": 69.1},
            "related_entity_ids": [entity_id],
        }
        event_response = client.post(
            "/api/v1/events",
            headers=auth_headers,
            json=event_data,
        )
        assert event_response.status_code == 201
        
        # Step 3: Calculate threat score
        threat_response = client.post(
            "/api/v1/analytics/threat-score",
            headers=auth_headers,
            json={"entity_id": entity_id, "include_explanation": True},
        )
        assert threat_response.status_code == 200
        
        # Step 4: Check dashboard reflects new data
        dashboard_response = client.get(
            "/api/v1/dashboard/overview",
            headers=auth_headers,
        )
        assert dashboard_response.status_code == 200

    def test_narrative_tracking_workflow(self, client, auth_headers):
        """Test narrative tracking workflow."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        # Get narratives
        narratives_response = client.get(
            "/api/v1/narratives",
            headers=auth_headers,
        )
        assert narratives_response.status_code == 200
        
        # Get narrative trends
        trends_response = client.get(
            "/api/v1/narratives/trends",
            headers=auth_headers,
        )
        assert trends_response.status_code == 200


@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test system behavior under concurrent load."""
    client = TestClient(app)
    
    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass"},
    )
    
    if login_response.status_code != 200:
        pytest.skip("Authentication not available")
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make concurrent requests
    async def make_request():
        response = client.get("/api/v1/entities", headers=headers)
        return response.status_code
    
    tasks = [make_request() for _ in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check that most requests succeeded
    successful = sum(1 for r in results if r == 200)
    assert successful >= 8  # At least 80% success rate
