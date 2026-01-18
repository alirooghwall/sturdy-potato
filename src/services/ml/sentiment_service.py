"""Sentiment analysis service using transformers.

Analyzes sentiment and emotion in text.
"""

import logging
from typing import Any, Dict, List, Optional

from .model_manager import get_model_manager

logger = logging.getLogger(__name__)


class SentimentService:
    """Sentiment analysis service using transformer models.
    
    Provides:
    - Binary sentiment (positive/negative)
    - Multi-class sentiment (positive/neutral/negative)
    - Confidence scores
    - Batch processing
    """

    def __init__(self, model_name: str = "sentiment"):
        """Initialize sentiment service.
        
        Args:
            model_name: Model to use (sentiment, sentiment_roberta, multilingual_sentiment)
        """
        self.model_name = model_name
        self.model_manager = get_model_manager()
        self._pipeline = None
        
        logger.info(f"Sentiment service initialized with model: {model_name}")
    
    def _get_pipeline(self):
        """Lazy load the sentiment pipeline."""
        if self._pipeline is None:
            logger.info("Loading sentiment pipeline...")
            self._pipeline = self.model_manager.create_pipeline(
                "sentiment-analysis",
                self.model_name,
            )
            logger.info("✓ Sentiment pipeline loaded")
        return self._pipeline
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text.
        
        Args:
            text: Input text
        
        Returns:
            Dictionary with sentiment label and confidence score
        """
        if not text or not text.strip():
            return {
                "label": "NEUTRAL",
                "score": 0.0,
                "sentiment": "neutral",
            }
        
        try:
            pipeline = self._get_pipeline()
            
            # Run inference
            result = pipeline(text[:512])[0]  # Truncate to model max length
            
            # Normalize label
            label = result["label"].upper()
            sentiment = self._normalize_label(label)
            
            return {
                "label": label,
                "score": float(result["score"]),
                "sentiment": sentiment,
            }
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "label": "NEUTRAL",
                "score": 0.0,
                "sentiment": "neutral",
                "error": str(e),
            }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze sentiment for multiple texts.
        
        Args:
            texts: List of input texts
        
        Returns:
            List of sentiment results
        """
        if not texts:
            return []
        
        try:
            pipeline = self._get_pipeline()
            
            # Truncate texts
            truncated = [text[:512] for text in texts]
            
            # Run batch inference
            results = pipeline(truncated)
            
            # Format results
            formatted = []
            for result in results:
                label = result["label"].upper()
                formatted.append({
                    "label": label,
                    "score": float(result["score"]),
                    "sentiment": self._normalize_label(label),
                })
            
            return formatted
        
        except Exception as e:
            logger.error(f"Error in batch sentiment analysis: {e}")
            return [
                {
                    "label": "NEUTRAL",
                    "score": 0.0,
                    "sentiment": "neutral",
                    "error": str(e),
                }
                for _ in texts
            ]
    
    def _normalize_label(self, label: str) -> str:
        """Normalize sentiment label to positive/negative/neutral.
        
        Args:
            label: Raw label from model
        
        Returns:
            Normalized sentiment
        """
        label_upper = label.upper()
        
        # Positive labels
        if any(x in label_upper for x in ["POSITIVE", "POS", "5 STARS", "4 STARS"]):
            return "positive"
        
        # Negative labels
        if any(x in label_upper for x in ["NEGATIVE", "NEG", "1 STAR", "2 STARS"]):
            return "negative"
        
        # Neutral labels
        if any(x in label_upper for x in ["NEUTRAL", "3 STARS"]):
            return "neutral"
        
        # Default
        return "neutral"
    
    def get_polarity_score(self, text: str) -> float:
        """Get polarity score (-1 to 1).
        
        Args:
            text: Input text
        
        Returns:
            Score from -1 (very negative) to 1 (very positive)
        """
        result = self.analyze(text)
        sentiment = result["sentiment"]
        score = result["score"]
        
        if sentiment == "positive":
            return score
        elif sentiment == "negative":
            return -score
        else:
            return 0.0
    
    def classify_sentiment(
        self,
        text: str,
        positive_threshold: float = 0.6,
        negative_threshold: float = 0.6,
    ) -> str:
        """Classify sentiment with configurable thresholds.
        
        Args:
            text: Input text
            positive_threshold: Minimum confidence for positive
            negative_threshold: Minimum confidence for negative
        
        Returns:
            Sentiment classification (positive/negative/neutral)
        """
        result = self.analyze(text)
        sentiment = result["sentiment"]
        score = result["score"]
        
        # Apply thresholds
        if sentiment == "positive" and score >= positive_threshold:
            return "positive"
        elif sentiment == "negative" and score >= negative_threshold:
            return "negative"
        else:
            return "neutral"
    
    def get_sentiment_statistics(self, texts: List[str]) -> Dict[str, Any]:
        """Get sentiment statistics for a collection of texts.
        
        Args:
            texts: List of texts
        
        Returns:
            Dictionary with sentiment distribution and statistics
        """
        if not texts:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "avg_polarity": 0.0,
            }
        
        results = self.analyze_batch(texts)
        
        positive = sum(1 for r in results if r["sentiment"] == "positive")
        negative = sum(1 for r in results if r["sentiment"] == "negative")
        neutral = sum(1 for r in results if r["sentiment"] == "neutral")
        
        # Calculate average polarity
        polarities = []
        for result in results:
            if result["sentiment"] == "positive":
                polarities.append(result["score"])
            elif result["sentiment"] == "negative":
                polarities.append(-result["score"])
            else:
                polarities.append(0.0)
        
        avg_polarity = sum(polarities) / len(polarities) if polarities else 0.0
        
        return {
            "total": len(texts),
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "positive_pct": (positive / len(texts)) * 100,
            "negative_pct": (negative / len(texts)) * 100,
            "neutral_pct": (neutral / len(texts)) * 100,
            "avg_polarity": avg_polarity,
        }


# Global instance
_sentiment_service: Optional[SentimentService] = None


def get_sentiment_service() -> SentimentService:
    """Get the global sentiment service instance."""
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService()
    return _sentiment_service
