"""Text classification service for topic categorization and zero-shot classification.

Categorizes text into predefined topics or custom labels.
"""

import logging
from typing import Any, Dict, List, Optional

from .model_manager import get_model_manager

logger = logging.getLogger(__name__)


class ClassificationService:
    """Text classification service.
    
    Provides:
    - Zero-shot classification (no training needed)
    - Multi-label classification
    - Topic categorization
    - Custom label classification
    """

    def __init__(self, model_name: str = "zero_shot"):
        """Initialize classification service.
        
        Args:
            model_name: Model to use (zero_shot)
        """
        self.model_name = model_name
        self.model_manager = get_model_manager()
        self._pipeline = None
        
        # Predefined categories for ISR platform
        self.isr_categories = [
            "security threat",
            "military operations",
            "terrorism",
            "political development",
            "humanitarian crisis",
            "economic situation",
            "infrastructure",
            "social unrest",
            "border incident",
            "intelligence report",
        ]
        
        self.conflict_categories = [
            "armed conflict",
            "peace negotiations",
            "ceasefire violation",
            "civilian casualties",
            "military engagement",
            "insurgent activity",
        ]
        
        logger.info(f"Classification service initialized with model: {model_name}")
    
    def _get_pipeline(self):
        """Lazy load the zero-shot classification pipeline."""
        if self._pipeline is None:
            logger.info("Loading zero-shot classification pipeline...")
            self._pipeline = self.model_manager.create_pipeline(
                "zero-shot-classification",
                self.model_name,
            )
            logger.info("✓ Zero-shot classification pipeline loaded")
        return self._pipeline
    
    def classify(
        self,
        text: str,
        candidate_labels: List[str],
        multi_label: bool = False,
    ) -> Dict[str, Any]:
        """Classify text into candidate labels.
        
        Args:
            text: Input text
            candidate_labels: List of possible labels
            multi_label: Whether to allow multiple labels
        
        Returns:
            Dictionary with labels and scores
        """
        if not text or not text.strip():
            return {
                "labels": [],
                "scores": [],
            }
        
        if not candidate_labels:
            return {
                "labels": [],
                "scores": [],
            }
        
        try:
            pipeline = self._get_pipeline()
            
            # Run classification
            result = pipeline(
                text[:512],  # Truncate to model max length
                candidate_labels,
                multi_label=multi_label,
            )
            
            return {
                "labels": result["labels"],
                "scores": [float(s) for s in result["scores"]],
                "sequence": result["sequence"][:100],  # Preview
            }
        
        except Exception as e:
            logger.error(f"Error classifying text: {e}")
            return {
                "labels": [],
                "scores": [],
                "error": str(e),
            }
    
    def classify_isr_topic(
        self,
        text: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Classify text into ISR-related topics.
        
        Args:
            text: Input text
            top_k: Number of top categories to return
        
        Returns:
            List of top categories with scores
        """
        result = self.classify(text, self.isr_categories, multi_label=True)
        
        # Combine labels and scores
        categories = [
            {
                "category": label,
                "score": score,
            }
            for label, score in zip(result["labels"], result["scores"])
        ]
        
        return categories[:top_k]
    
    def classify_conflict_type(
        self,
        text: str,
        top_k: int = 2,
    ) -> List[Dict[str, Any]]:
        """Classify text into conflict-related categories.
        
        Args:
            text: Input text
            top_k: Number of top categories to return
        
        Returns:
            List of top categories with scores
        """
        result = self.classify(text, self.conflict_categories, multi_label=True)
        
        categories = [
            {
                "category": label,
                "score": score,
            }
            for label, score in zip(result["labels"], result["scores"])
        ]
        
        return categories[:top_k]
    
    def is_relevant_to_afghanistan(
        self,
        text: str,
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Determine if text is relevant to Afghanistan.
        
        Args:
            text: Input text
            threshold: Confidence threshold
        
        Returns:
            Dictionary with relevance decision and score
        """
        labels = ["Afghanistan related", "Not Afghanistan related"]
        result = self.classify(text, labels, multi_label=False)
        
        if result["labels"] and result["scores"]:
            top_label = result["labels"][0]
            top_score = result["scores"][0]
            
            is_relevant = (
                "Afghanistan" in top_label and top_score >= threshold
            )
            
            return {
                "is_relevant": is_relevant,
                "confidence": top_score,
                "label": top_label,
            }
        
        return {
            "is_relevant": False,
            "confidence": 0.0,
            "label": "unknown",
        }
    
    def classify_threat_level(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """Classify threat level of text.
        
        Args:
            text: Input text
        
        Returns:
            Dictionary with threat level and confidence
        """
        labels = ["critical threat", "high threat", "medium threat", "low threat", "no threat"]
        result = self.classify(text, labels, multi_label=False)
        
        if result["labels"] and result["scores"]:
            return {
                "threat_level": result["labels"][0],
                "confidence": result["scores"][0],
                "all_levels": [
                    {"level": label, "score": score}
                    for label, score in zip(result["labels"], result["scores"])
                ],
            }
        
        return {
            "threat_level": "unknown",
            "confidence": 0.0,
            "all_levels": [],
        }
    
    def classify_urgency(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """Classify urgency level of text.
        
        Args:
            text: Input text
        
        Returns:
            Dictionary with urgency level and confidence
        """
        labels = ["immediate action required", "urgent", "important", "routine", "low priority"]
        result = self.classify(text, labels, multi_label=False)
        
        if result["labels"] and result["scores"]:
            return {
                "urgency": result["labels"][0],
                "confidence": result["scores"][0],
            }
        
        return {
            "urgency": "unknown",
            "confidence": 0.0,
        }
    
    def batch_classify(
        self,
        texts: List[str],
        candidate_labels: List[str],
        multi_label: bool = False,
    ) -> List[Dict[str, Any]]:
        """Classify multiple texts.
        
        Args:
            texts: List of input texts
            candidate_labels: List of possible labels
            multi_label: Whether to allow multiple labels
        
        Returns:
            List of classification results
        """
        return [
            self.classify(text, candidate_labels, multi_label)
            for text in texts
        ]


# Global instance
_classification_service: Optional[ClassificationService] = None


def get_classification_service() -> ClassificationService:
    """Get the global classification service instance."""
    global _classification_service
    if _classification_service is None:
        _classification_service = ClassificationService()
    return _classification_service
