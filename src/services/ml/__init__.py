"""Machine Learning services for ISR Platform.

Provides advanced ML capabilities including:
- Named Entity Recognition (NER) with transformers
- Sentiment analysis
- Text classification and categorization
- Threat detection
- Document embedding and similarity
- Zero-shot classification
- Text summarization
- Translation (multilingual)
- Performance monitoring
"""

from .model_manager import ModelManager, get_model_manager
from .ner_service import NERService, get_ner_service
from .sentiment_service import SentimentService, get_sentiment_service
from .classification_service import ClassificationService, get_classification_service
from .threat_detection import ThreatDetectionService, get_threat_detection_service
from .embedding_service import EmbeddingService, get_embedding_service
from .summarization_service import SummarizationService, get_summarization_service
from .translation_service import TranslationService, get_translation_service
from .monitoring_service import MLMonitoringService, get_monitoring_service, track_ml_operation
from .propaganda_detector import PropagandaDetector, get_propaganda_detector
from .news_verifier import NewsVerifier, get_news_verifier

__all__ = [
    "ModelManager",
    "get_model_manager",
    "NERService",
    "get_ner_service",
    "SentimentService",
    "get_sentiment_service",
    "ClassificationService",
    "get_classification_service",
    "ThreatDetectionService",
    "get_threat_detection_service",
    "EmbeddingService",
    "get_embedding_service",
    "SummarizationService",
    "get_summarization_service",
    "TranslationService",
    "get_translation_service",
    "MLMonitoringService",
    "get_monitoring_service",
    "track_ml_operation",
    "PropagandaDetector",
    "get_propaganda_detector",
    "NewsVerifier",
    "get_news_verifier",
]
