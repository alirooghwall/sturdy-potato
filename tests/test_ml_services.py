"""Tests for ML services."""

import pytest


@pytest.mark.asyncio
async def test_ner_service():
    """Test NER service."""
    from src.services.ml import get_ner_service
    
    ner = get_ner_service()
    
    text = "Taliban forces entered Kabul yesterday."
    entities = ner.extract_entities(text, min_confidence=0.5)
    
    assert len(entities) > 0
    assert any(e["entity_type"] in ["ORGANIZATION", "ORG"] for e in entities)
    assert any(e["entity_type"] in ["LOCATION", "GPE"] for e in entities)


@pytest.mark.asyncio
async def test_sentiment_service():
    """Test sentiment analysis."""
    from src.services.ml import get_sentiment_service
    
    sentiment = get_sentiment_service()
    
    # Positive text
    result = sentiment.analyze("Peace agreement brings hope for the future.")
    assert result["sentiment"] == "positive"
    
    # Negative text
    result = sentiment.analyze("Attack kills dozens in explosion.")
    assert result["sentiment"] == "negative"


@pytest.mark.asyncio
async def test_classification_service():
    """Test classification service."""
    from src.services.ml import get_classification_service
    
    classifier = get_classification_service()
    
    text = "Military operation near border"
    topics = classifier.classify_isr_topic(text, top_k=3)
    
    assert len(topics) > 0
    assert all("category" in t and "score" in t for t in topics)


@pytest.mark.asyncio
async def test_threat_detection():
    """Test threat detection."""
    from src.services.ml import get_threat_detection_service
    
    threat = get_threat_detection_service()
    
    # High threat text
    result = threat.detect_threats("IED attack reported in Kandahar", include_details=True)
    assert result["threat_detected"] == True
    assert result["threat_score"] > 0.5
    assert result["threat_level"] in ["medium", "high", "critical"]
    
    # Low threat text
    result = threat.detect_threats("Aid distribution scheduled for next week")
    assert result["threat_score"] < 0.5


@pytest.mark.asyncio
async def test_embedding_service():
    """Test embedding and similarity."""
    from src.services.ml import get_embedding_service
    
    embeddings = get_embedding_service()
    
    # Similar texts
    sim = embeddings.similarity(
        "Military forces deploy to region",
        "Armed forces sent to area"
    )
    assert sim > 0.6
    
    # Different texts
    sim = embeddings.similarity(
        "Military operation",
        "Economic development"
    )
    assert sim < 0.6


@pytest.mark.asyncio
async def test_model_manager():
    """Test model manager."""
    from src.services.ml import get_model_manager
    
    manager = get_model_manager()
    
    # Check memory usage
    memory = manager.get_memory_usage()
    assert "device" in memory
    assert "models_loaded" in memory
