"""Test LLM API endpoints."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient
from src.api.main import create_app
from src.services.llm.llm_service import LLMProvider


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {
        "user_id": str(uuid4()),
        "username": "test_user",
        "permissions": ["llm:read", "llm:write", "admin"],
    }


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    mock = AsyncMock()
    mock.generate.return_value = "Generated LLM response"
    mock.generate_stream.return_value = async_generator_mock(["chunk1", "chunk2"])
    mock.config.provider.value = "openai"
    mock.default_model = "gpt-4"
    mock.config.temperature = 0.7
    mock.config.max_tokens = 2000
    return mock


async def async_generator_mock(items):
    """Helper for async generator mocking."""
    for item in items:
        yield item


class TestLLMConfiguration:
    """Test LLM configuration endpoints."""
    
    @patch("src.api.routers.llm.require_permission")
    @patch("src.api.routers.llm.set_llm_service")
    def test_configure_llm(self, mock_set_service, mock_auth, client, mock_user):
        """Test LLM configuration."""
        mock_auth.return_value = lambda: mock_user
        
        response = client.post(
            "/api/v1/llm/configure",
            json={
                "provider": "openai",
                "api_key": "test-key",
                "model": "gpt-4",
                "temperature": 0.7,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "configured"
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4"
        assert data["temperature"] == 0.7
    
    @patch("src.api.routers.llm.require_permission")
    @patch("src.api.routers.llm.get_llm_service")
    def test_get_llm_status(self, mock_get_service, mock_auth, client, mock_user, mock_llm_service):
        """Test getting LLM status."""
        mock_auth.return_value = lambda: mock_user
        mock_get_service.return_value = mock_llm_service
        
        response = client.get("/api/v1/llm/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is True
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4"


class TestConversationalQuery:
    """Test conversational query endpoints."""
    
    @patch("src.api.routers.llm.require_permission")
    @patch("src.api.routers.llm.get_conversational_query")
    async def test_conversational_query(self, mock_get_query, mock_auth, client, mock_user):
        """Test conversational query."""
        mock_auth.return_value = lambda: mock_user
        
        mock_query_service = AsyncMock()
        mock_query_service.query.return_value = {
            "response": "Test response",
            "conversation_id": str(uuid4()),
            "sources": [],
        }
        mock_get_query.return_value = mock_query_service
        
        response = client.post(
            "/api/v1/llm/query",
            json={
                "query": "What are the latest threats?",
                "context_data": {"region": "afghanistan"},
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
    
    @patch("src.api.routers.llm.require_permission")
    @patch("src.api.routers.llm.get_conversational_query")
    def test_query_error_handling(self, mock_get_query, mock_auth, client, mock_user):
        """Test query error handling."""
        mock_auth.return_value = lambda: mock_user
        
        mock_query_service = AsyncMock()
        mock_query_service.query.side_effect = Exception("LLM error")
        mock_get_query.return_value = mock_query_service
        
        response = client.post(
            "/api/v1/llm/query",
            json={"query": "Test query"},
        )
        
        assert response.status_code == 500
        assert "Query failed" in response.json()["detail"]


class TestReportGeneration:
    """Test report generation endpoints."""
    
    @patch("src.api.routers.llm.require_permission")
    @patch("src.api.routers.llm.get_report_generator")
    async def test_generate_report(self, mock_get_gen, mock_auth, client, mock_user):
        """Test report generation."""
        mock_auth.return_value = lambda: mock_user
        
        mock_generator = AsyncMock()
        mock_generator.generate_satellite_analysis_report.return_value = {
            "report_id": str(uuid4()),
            "content": "Test report content",
            "analysis_type": "deforestation",
        }
        mock_get_gen.return_value = mock_generator
        
        response = client.post(
            "/api/v1/llm/report/generate",
            json={
                "analysis_data": {
                    "detection_date": "2024-01-01",
                    "location": "Test Location",
                    "confidence": 0.95,
                },
                "analysis_type": "deforestation",
                "include_recommendations": True,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "report_id" in data
        assert data["analysis_type"] == "deforestation"
    
    @patch("src.api.routers.llm.require_permission")
    @patch("src.api.routers.llm.get_report_generator")
    async def test_generate_executive_briefing(self, mock_get_gen, mock_auth, client, mock_user):
        """Test executive briefing generation."""
        mock_auth.return_value = lambda: mock_user
        
        mock_generator = AsyncMock()
        mock_generator.generate_executive_briefing.return_value = {
            "briefing_id": str(uuid4()),
            "content": "Executive briefing content",
            "time_period": "24h",
        }
        mock_get_gen.return_value = mock_generator
        
        response = client.post(
            "/api/v1/llm/report/executive-briefing",
            json={
                "alerts": [
                    {"severity": "CRITICAL", "event_type": "Test Alert"}
                ],
                "key_events": [
                    {"timestamp": "2024-01-01T00:00:00", "description": "Test Event"}
                ],
                "time_period": "24h",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "briefing_id" in data
        assert data["time_period"] == "24h"


class TestInsightDiscovery:
    """Test insight discovery endpoints."""
    
    @patch("src.api.routers.llm.require_permission")
    @patch("src.api.routers.llm.get_insight_discovery")
    async def test_discover_insights(self, mock_get_insight, mock_auth, client, mock_user):
        """Test insight discovery."""
        mock_auth.return_value = lambda: mock_user
        
        mock_insight_service = AsyncMock()
        mock_insight = Mock()
        mock_insight.insight_id = uuid4()
        mock_insight.category = "correlation"
        mock_insight.title = "Test Insight"
        mock_insight.description = "Test description"
        mock_insight.confidence = 0.85
        mock_insight.importance = "high"
        mock_insight.evidence = ["evidence1", "evidence2"]
        mock_insight.recommendations = ["recommendation1"]
        
        mock_insight_service.discover_correlations.return_value = [mock_insight]
        mock_get_insight.return_value = mock_insight_service
        
        response = client.post(
            "/api/v1/llm/insights/discover",
            json={
                "satellite_alerts": [{"type": "deforestation"}],
                "narratives": [{"name": "test_narrative"}],
                "social_media_activity": [{"platform": "twitter"}],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["insights_found"] == 1
        assert len(data["insights"]) == 1
        assert data["insights"][0]["category"] == "correlation"


class TestAnomalyExplanation:
    """Test anomaly explanation endpoints."""
    
    @patch("src.api.routers.llm.require_permission")
    @patch("src.api.routers.llm.get_anomaly_explainer")
    async def test_explain_anomaly(self, mock_get_explainer, mock_auth, client, mock_user):
        """Test anomaly explanation."""
        mock_auth.return_value = lambda: mock_user
        
        mock_explainer = AsyncMock()
        mock_explainer.explain_anomaly.return_value = {
            "explanation_id": str(uuid4()),
            "explanation": "Test explanation",
            "confidence": 0.9,
        }
        mock_get_explainer.return_value = mock_explainer
        
        response = client.post(
            "/api/v1/llm/explain/anomaly",
            json={
                "anomaly_data": {
                    "type": "spike",
                    "magnitude": 5.2,
                    "timestamp": "2024-01-01T00:00:00",
                },
                "context": {"location": "test_region"},
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data


class TestPredictions:
    """Test prediction endpoints."""
    
    @patch("src.api.routers.llm.require_permission")
    @patch("src.api.routers.llm.get_prediction_service")
    async def test_predict_narrative_evolution(self, mock_get_pred, mock_auth, client, mock_user):
        """Test narrative evolution prediction."""
        mock_auth.return_value = lambda: mock_user
        
        mock_pred_service = AsyncMock()
        mock_pred_service.predict_narrative_evolution.return_value = {
            "prediction_id": str(uuid4()),
            "predicted_trajectory": "growing",
            "confidence": 0.75,
        }
        mock_get_pred.return_value = mock_pred_service
        
        response = client.post(
            "/api/v1/llm/predict",
            json={
                "prediction_type": "narrative_evolution",
                "data": {"narrative_name": "test"},
                "time_horizon": 48,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "prediction_id" in data
    
    @patch("src.api.routers.llm.require_permission")
    @patch("src.api.routers.llm.get_prediction_service")
    async def test_predict_event_likelihood(self, mock_get_pred, mock_auth, client, mock_user):
        """Test event likelihood prediction."""
        mock_auth.return_value = lambda: mock_user
        
        mock_pred_service = AsyncMock()
        mock_pred_service.predict_event_likelihood.return_value = {
            "prediction_id": str(uuid4()),
            "likelihood": 0.65,
            "timeframe": "72h",
        }
        mock_get_pred.return_value = mock_pred_service
        
        response = client.post(
            "/api/v1/llm/predict",
            json={
                "prediction_type": "event_likelihood",
                "data": {
                    "event_type": "conflict",
                    "indicators": {"tension": 0.8},
                    "precedents": [],
                },
                "time_horizon": 72,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "likelihood" in data
    
    @patch("src.api.routers.llm.require_permission")
    @patch("src.api.routers.llm.get_prediction_service")
    def test_invalid_prediction_type(self, mock_get_pred, mock_auth, client, mock_user):
        """Test invalid prediction type error."""
        mock_auth.return_value = lambda: mock_user
        mock_get_pred.return_value = AsyncMock()
        
        response = client.post(
            "/api/v1/llm/predict",
            json={
                "prediction_type": "invalid_type",
                "data": {},
                "time_horizon": 48,
            },
        )
        
        assert response.status_code == 400
        assert "Invalid prediction type" in response.json()["detail"]


class TestValidation:
    """Test input validation."""
    
    @patch("src.api.routers.llm.require_permission")
    def test_query_validation_min_length(self, mock_auth, client, mock_user):
        """Test query minimum length validation."""
        mock_auth.return_value = lambda: mock_user
        
        response = client.post(
            "/api/v1/llm/query",
            json={"query": ""},  # Empty query
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch("src.api.routers.llm.require_permission")
    def test_temperature_validation(self, mock_auth, client, mock_user):
        """Test temperature validation."""
        mock_auth.return_value = lambda: mock_user
        
        response = client.post(
            "/api/v1/llm/configure",
            json={
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 3.0,  # Out of range
            },
        )
        
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
