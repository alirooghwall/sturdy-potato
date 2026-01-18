"""ML API endpoints for ISR Platform.

Provides REST API access to ML models and services.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# Request/Response Models
class TextInput(BaseModel):
    """Single text input."""
    text: str = Field(..., description="Input text to analyze")


class BatchTextInput(BaseModel):
    """Multiple texts input."""
    texts: List[str] = Field(..., description="List of texts to analyze")


class NERRequest(BaseModel):
    """NER request."""
    text: str = Field(..., description="Text for entity extraction")
    min_confidence: float = Field(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold")


class SentimentRequest(BaseModel):
    """Sentiment analysis request."""
    text: str = Field(..., description="Text for sentiment analysis")


class ClassificationRequest(BaseModel):
    """Classification request."""
    text: str = Field(..., description="Text to classify")
    labels: List[str] = Field(..., description="Candidate labels")
    multi_label: bool = Field(False, description="Allow multiple labels")


class ThreatDetectionRequest(BaseModel):
    """Threat detection request."""
    text: str = Field(..., description="Text to analyze for threats")
    include_details: bool = Field(True, description="Include detailed analysis")


class SimilarityRequest(BaseModel):
    """Similarity request."""
    text1: str = Field(..., description="First text")
    text2: str = Field(..., description="Second text")


class SemanticSearchRequest(BaseModel):
    """Semantic search request."""
    query: str = Field(..., description="Search query")
    documents: List[str] = Field(..., description="Documents to search")
    top_k: int = Field(5, ge=1, le=100, description="Number of results")


# ==================== Named Entity Recognition ====================

@router.post("/ner/extract")
async def extract_entities(request: NERRequest) -> Dict[str, Any]:
    """Extract named entities from text.
    
    Extracts persons, organizations, locations, and other entities using
    transformer-based NER models.
    """
    try:
        from src.services.ml import get_ner_service
        
        ner_service = get_ner_service()
        entities = ner_service.extract_entities(request.text, request.min_confidence)
        
        return {
            "entities": entities,
            "count": len(entities),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NER failed: {str(e)}")


@router.post("/ner/by-type")
async def extract_entities_by_type(
    text: str,
    entity_type: str,
    min_confidence: float = 0.5,
) -> Dict[str, Any]:
    """Extract entities of a specific type.
    
    Types: PERSON, ORGANIZATION, LOCATION, GPE, DATE, etc.
    """
    try:
        from src.services.ml import get_ner_service
        
        ner_service = get_ner_service()
        entities = ner_service.extract_entities_by_type(text, entity_type, min_confidence)
        
        return {
            "entity_type": entity_type,
            "entities": entities,
            "count": len(entities),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NER failed: {str(e)}")


@router.post("/ner/locations")
async def extract_locations(request: TextInput) -> Dict[str, Any]:
    """Extract location entities from text."""
    try:
        from src.services.ml import get_ner_service
        
        ner_service = get_ner_service()
        locations = ner_service.extract_locations(request.text)
        
        return {
            "locations": locations,
            "count": len(locations),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Location extraction failed: {str(e)}")


@router.post("/ner/organizations")
async def extract_organizations(request: TextInput) -> Dict[str, Any]:
    """Extract organization entities from text."""
    try:
        from src.services.ml import get_ner_service
        
        ner_service = get_ner_service()
        organizations = ner_service.extract_organizations(request.text)
        
        return {
            "organizations": organizations,
            "count": len(organizations),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Organization extraction failed: {str(e)}")


# ==================== Sentiment Analysis ====================

@router.post("/sentiment/analyze")
async def analyze_sentiment(request: SentimentRequest) -> Dict[str, Any]:
    """Analyze sentiment of text.
    
    Returns sentiment (positive/negative/neutral) with confidence score.
    """
    try:
        from src.services.ml import get_sentiment_service
        
        sentiment_service = get_sentiment_service()
        result = sentiment_service.analyze(request.text)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")


@router.post("/sentiment/batch")
async def analyze_sentiment_batch(request: BatchTextInput) -> Dict[str, Any]:
    """Analyze sentiment for multiple texts."""
    try:
        from src.services.ml import get_sentiment_service
        
        sentiment_service = get_sentiment_service()
        results = sentiment_service.analyze_batch(request.texts)
        
        return {
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch sentiment analysis failed: {str(e)}")


@router.post("/sentiment/statistics")
async def get_sentiment_statistics(request: BatchTextInput) -> Dict[str, Any]:
    """Get sentiment statistics for a collection of texts."""
    try:
        from src.services.ml import get_sentiment_service
        
        sentiment_service = get_sentiment_service()
        stats = sentiment_service.get_sentiment_statistics(request.texts)
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment statistics failed: {str(e)}")


# ==================== Text Classification ====================

@router.post("/classify")
async def classify_text(request: ClassificationRequest) -> Dict[str, Any]:
    """Classify text into candidate labels using zero-shot classification.
    
    No training required - works with any custom labels.
    """
    try:
        from src.services.ml import get_classification_service
        
        classification_service = get_classification_service()
        result = classification_service.classify(
            request.text,
            request.labels,
            request.multi_label,
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/classify/isr-topic")
async def classify_isr_topic(request: TextInput, top_k: int = 3) -> Dict[str, Any]:
    """Classify text into ISR-related topics.
    
    Topics include: security threat, military operations, terrorism, etc.
    """
    try:
        from src.services.ml import get_classification_service
        
        classification_service = get_classification_service()
        topics = classification_service.classify_isr_topic(request.text, top_k)
        
        return {
            "topics": topics,
            "count": len(topics),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topic classification failed: {str(e)}")


@router.post("/classify/threat-level")
async def classify_threat_level(request: TextInput) -> Dict[str, Any]:
    """Classify threat level of text."""
    try:
        from src.services.ml import get_classification_service
        
        classification_service = get_classification_service()
        result = classification_service.classify_threat_level(request.text)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Threat level classification failed: {str(e)}")


@router.post("/classify/afghanistan-relevance")
async def check_afghanistan_relevance(request: TextInput, threshold: float = 0.5) -> Dict[str, Any]:
    """Determine if text is relevant to Afghanistan."""
    try:
        from src.services.ml import get_classification_service
        
        classification_service = get_classification_service()
        result = classification_service.is_relevant_to_afghanistan(request.text, threshold)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Relevance check failed: {str(e)}")


# ==================== Threat Detection ====================

@router.post("/threat/detect")
async def detect_threats(request: ThreatDetectionRequest) -> Dict[str, Any]:
    """Detect security threats in text using ensemble ML models.
    
    Combines keyword detection, sentiment analysis, NER, and classification
    to provide comprehensive threat assessment.
    """
    try:
        from src.services.ml import get_threat_detection_service
        
        threat_service = get_threat_detection_service()
        result = threat_service.detect_threats(request.text, request.include_details)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Threat detection failed: {str(e)}")


@router.post("/threat/batch")
async def detect_threats_batch(request: BatchTextInput, include_details: bool = False) -> Dict[str, Any]:
    """Detect threats in multiple texts."""
    try:
        from src.services.ml import get_threat_detection_service
        
        threat_service = get_threat_detection_service()
        results = threat_service.batch_detect(request.texts, include_details)
        
        return {
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch threat detection failed: {str(e)}")


@router.post("/threat/summary")
async def get_threat_summary(request: BatchTextInput) -> Dict[str, Any]:
    """Get threat summary statistics for a collection of texts."""
    try:
        from src.services.ml import get_threat_detection_service
        
        threat_service = get_threat_detection_service()
        summary = threat_service.get_threat_summary(request.texts)
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Threat summary failed: {str(e)}")


# ==================== Embeddings & Similarity ====================

@router.post("/similarity")
async def compute_similarity(request: SimilarityRequest) -> Dict[str, Any]:
    """Compute semantic similarity between two texts.
    
    Returns similarity score (0-1), where higher is more similar.
    """
    try:
        from src.services.ml import get_embedding_service
        
        embedding_service = get_embedding_service()
        similarity = embedding_service.similarity(request.text1, request.text2)
        
        return {
            "similarity": similarity,
            "text1_preview": request.text1[:100],
            "text2_preview": request.text2[:100],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity computation failed: {str(e)}")


@router.post("/search")
async def semantic_search(request: SemanticSearchRequest) -> Dict[str, Any]:
    """Perform semantic search over documents.
    
    Finds most similar documents to the query based on meaning, not just keywords.
    """
    try:
        from src.services.ml import get_embedding_service
        
        embedding_service = get_embedding_service()
        results = embedding_service.semantic_search(
            request.query,
            request.documents,
            request.top_k,
        )
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@router.post("/duplicates")
async def find_duplicates(request: BatchTextInput, threshold: float = 0.85) -> Dict[str, Any]:
    """Find duplicate or near-duplicate texts."""
    try:
        from src.services.ml import get_embedding_service
        
        embedding_service = get_embedding_service()
        duplicates = embedding_service.find_duplicates(request.texts, threshold)
        
        return {
            "duplicates": [
                {
                    "index1": d[0],
                    "index2": d[1],
                    "similarity": d[2],
                    "text1": request.texts[d[0]][:100],
                    "text2": request.texts[d[1]][:100],
                }
                for d in duplicates
            ],
            "count": len(duplicates),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duplicate detection failed: {str(e)}")


# ==================== Model Management ====================

@router.get("/models/status")
async def get_models_status() -> Dict[str, Any]:
    """Get status of ML models and memory usage."""
    try:
        from src.services.ml import get_model_manager
        
        model_manager = get_model_manager()
        memory = model_manager.get_memory_usage()
        
        return {
            "status": "online",
            "device": memory["device"],
            "models_loaded": memory["models_loaded"],
            "memory": memory,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/models/registry")
async def get_model_registry() -> Dict[str, Any]:
    """Get list of available models."""
    try:
        from src.services.ml import get_model_manager
        
        model_manager = get_model_manager()
        
        return {
            "models": model_manager.models,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registry fetch failed: {str(e)}")


@router.post("/models/clear-cache")
async def clear_model_cache() -> Dict[str, Any]:
    """Clear ML model cache to free memory."""
    try:
        from src.services.ml import get_model_manager
        
        model_manager = get_model_manager()
        model_manager.clear_cache()
        
        return {
            "status": "success",
            "message": "Model cache cleared",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


# ==================== Summarization ====================

@router.post("/summarize")
async def summarize_text(
    text: str,
    max_length: int = 130,
    min_length: int = 30,
) -> Dict[str, Any]:
    """Generate summary of text.
    
    Creates an abstractive summary using transformer models.
    """
    try:
        from src.services.ml import get_summarization_service
        
        summarization = get_summarization_service()
        result = summarization.summarize(text, max_length, min_length)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@router.post("/summarize/extractive")
async def extractive_summary(
    text: str,
    num_sentences: int = 3,
) -> Dict[str, Any]:
    """Generate extractive summary by selecting key sentences."""
    try:
        from src.services.ml import get_summarization_service
        
        summarization = get_summarization_service()
        result = summarization.extractive_summary(text, num_sentences)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extractive summarization failed: {str(e)}")


@router.post("/summarize/news")
async def summarize_news_article(
    title: str,
    content: str,
    max_length: int = 100,
) -> Dict[str, Any]:
    """Summarize a news article with title context."""
    try:
        from src.services.ml import get_summarization_service
        
        summarization = get_summarization_service()
        result = summarization.summarize_news_article(title, content, max_length)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News summarization failed: {str(e)}")


# ==================== Translation ====================

@router.post("/translate")
async def translate_text(
    text: str,
    source_lang: str = "en",
    target_lang: str = "ps",
) -> Dict[str, Any]:
    """Translate text between languages.
    
    Supports: English, Pashto (ps), Dari/Farsi (fa), Urdu (ur), Arabic (ar), and many more.
    """
    try:
        from src.services.ml import get_translation_service
        
        translation = get_translation_service()
        result = translation.translate(text, source_lang, target_lang)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post("/translate/to-english")
async def translate_to_english(
    text: str,
    source_lang: str = "ps",
) -> Dict[str, Any]:
    """Translate text to English."""
    try:
        from src.services.ml import get_translation_service
        
        translation = get_translation_service()
        translated = translation.translate_to_english(text, source_lang)
        
        return {
            "source_text": text,
            "translated_text": translated,
            "source_lang": source_lang,
            "target_lang": "en",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post("/translate/from-english")
async def translate_from_english(
    text: str,
    target_lang: str = "ps",
) -> Dict[str, Any]:
    """Translate English text to another language."""
    try:
        from src.services.ml import get_translation_service
        
        translation = get_translation_service()
        translated = translation.translate_from_english(text, target_lang)
        
        return {
            "source_text": text,
            "translated_text": translated,
            "source_lang": "en",
            "target_lang": target_lang,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.get("/translate/languages")
async def get_supported_languages() -> Dict[str, Any]:
    """Get information about supported languages."""
    try:
        from src.services.ml import get_translation_service
        
        translation = get_translation_service()
        info = translation.multilingual_support_info()
        
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get language info: {str(e)}")


# ==================== Monitoring & Metrics ====================

@router.get("/monitoring/system")
async def get_system_metrics() -> Dict[str, Any]:
    """Get overall ML system metrics."""
    try:
        from src.services.ml import get_monitoring_service
        
        monitoring = get_monitoring_service()
        metrics = monitoring.get_system_metrics()
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/monitoring/models")
async def get_model_metrics(model_name: str = None) -> Dict[str, Any]:
    """Get metrics for ML models."""
    try:
        from src.services.ml import get_monitoring_service
        
        monitoring = get_monitoring_service()
        metrics = monitoring.get_model_metrics(model_name)
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model metrics: {str(e)}")


@router.get("/monitoring/services")
async def get_service_metrics(service_name: str = None) -> Dict[str, Any]:
    """Get metrics for ML services."""
    try:
        from src.services.ml import get_monitoring_service
        
        monitoring = get_monitoring_service()
        metrics = monitoring.get_service_metrics(service_name)
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service metrics: {str(e)}")


@router.get("/monitoring/request-rate")
async def get_request_rate(window_minutes: int = 60) -> Dict[str, Any]:
    """Get request rate for the last N minutes."""
    try:
        from src.services.ml import get_monitoring_service
        
        monitoring = get_monitoring_service()
        rate = monitoring.get_request_rate(window_minutes)
        
        return rate
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get request rate: {str(e)}")


@router.get("/monitoring/top-models")
async def get_top_models(top_n: int = 5) -> Dict[str, Any]:
    """Get top N most used models."""
    try:
        from src.services.ml import get_monitoring_service
        
        monitoring = get_monitoring_service()
        top_models = monitoring.get_top_models(top_n)
        
        return {
            "top_models": top_models,
            "count": len(top_models),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get top models: {str(e)}")


@router.get("/monitoring/slow-requests")
async def get_slow_requests(
    threshold_ms: float = 1000,
    limit: int = 10,
) -> Dict[str, Any]:
    """Get slowest recent requests."""
    try:
        from src.services.ml import get_monitoring_service
        
        monitoring = get_monitoring_service()
        slow = monitoring.get_slow_requests(threshold_ms, limit)
        
        return {
            "slow_requests": slow,
            "count": len(slow),
            "threshold_ms": threshold_ms,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get slow requests: {str(e)}")


@router.get("/monitoring/export")
async def export_metrics() -> Dict[str, Any]:
    """Export all metrics for analysis or persistence."""
    try:
        from src.services.ml import get_monitoring_service
        
        monitoring = get_monitoring_service()
        export = monitoring.export_metrics()
        
        return export
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export metrics: {str(e)}")


@router.post("/monitoring/reset")
async def reset_metrics() -> Dict[str, Any]:
    """Reset all monitoring metrics."""
    try:
        from src.services.ml import get_monitoring_service
        
        monitoring = get_monitoring_service()
        monitoring.reset_metrics()
        
        return {
            "status": "success",
            "message": "Monitoring metrics reset",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset metrics: {str(e)}")
