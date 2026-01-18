"""Threat detection service combining multiple ML models.

Detects and scores security threats in text using ensemble methods.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from .classification_service import get_classification_service
from .sentiment_service import get_sentiment_service
from .ner_service import get_ner_service

logger = logging.getLogger(__name__)


class ThreatDetectionService:
    """Threat detection service using ensemble ML models.
    
    Combines multiple signals:
    - Keyword detection (rule-based)
    - Sentiment analysis (negative sentiment)
    - Entity recognition (threat actors, weapons)
    - Zero-shot classification (threat categorization)
    - Contextual analysis
    """

    def __init__(self):
        """Initialize threat detection service."""
        self.classification_service = get_classification_service()
        self.sentiment_service = get_sentiment_service()
        self.ner_service = get_ner_service()
        
        # Threat keyword patterns
        self.threat_keywords = {
            "violence": [
                r"\b(attack|assault|bomb|explosion|shooting|kill|murder|massacre)\b",
                r"\b(violence|violent|armed|weapon|explosive|IED)\b",
            ],
            "terrorism": [
                r"\b(terror|terrorist|terrorism|insurgent|militant|extremist)\b",
                r"\b(Taliban|ISIS|ISIL|Al-Qaeda|Al Qaeda)\b",
            ],
            "military": [
                r"\b(combat|battle|airstrike|drone|missile|military operation)\b",
                r"\b(troops|soldiers|forces|battalion|regiment)\b",
            ],
            "threat": [
                r"\b(threat|threaten|danger|risk|hazard|menace)\b",
                r"\b(hostage|kidnap|abduct|capture)\b",
            ],
            "instability": [
                r"\b(conflict|war|fighting|clash|confrontation)\b",
                r"\b(crisis|emergency|disaster|chaos|unrest)\b",
            ],
        }
        
        # Known threat actors
        self.threat_actors = {
            "Taliban",
            "ISIS",
            "ISIL",
            "Islamic State",
            "Al-Qaeda",
            "Al Qaeda",
            "Haqqani Network",
            "TTP",
            "Pakistani Taliban",
        }
        
        # Weapons and threat items
        self.threat_items = {
            "IED",
            "explosive",
            "bomb",
            "suicide vest",
            "rocket",
            "missile",
            "AK-47",
            "RPG",
            "mortar",
        }
        
        logger.info("Threat detection service initialized")
    
    def detect_threats(
        self,
        text: str,
        include_details: bool = True,
    ) -> Dict[str, Any]:
        """Detect threats in text using ensemble approach.
        
        Args:
            text: Input text
            include_details: Whether to include detailed analysis
        
        Returns:
            Dictionary with threat assessment
        """
        if not text or not text.strip():
            return {
                "threat_detected": False,
                "threat_score": 0.0,
                "threat_level": "none",
            }
        
        try:
            # 1. Keyword-based detection
            keyword_score, keyword_matches = self._detect_keywords(text)
            
            # 2. Sentiment analysis (negative sentiment indicates potential threat)
            sentiment = self.sentiment_service.analyze(text)
            sentiment_score = self._sentiment_to_threat_score(sentiment)
            
            # 3. Classification-based threat detection
            threat_classification = self.classification_service.classify_threat_level(text)
            classification_score = self._classification_to_score(threat_classification)
            
            # 4. Entity-based detection (threat actors, weapons)
            entity_score, threat_entities = self._detect_threat_entities(text)
            
            # 5. Combine scores (weighted ensemble)
            combined_score = (
                keyword_score * 0.3 +
                sentiment_score * 0.2 +
                classification_score * 0.35 +
                entity_score * 0.15
            )
            
            # Determine threat level
            threat_level = self._score_to_level(combined_score)
            
            result = {
                "threat_detected": combined_score > 0.3,
                "threat_score": round(combined_score, 3),
                "threat_level": threat_level,
            }
            
            if include_details:
                result["details"] = {
                    "keyword_score": round(keyword_score, 3),
                    "keyword_matches": keyword_matches,
                    "sentiment_score": round(sentiment_score, 3),
                    "sentiment": sentiment["sentiment"],
                    "classification_score": round(classification_score, 3),
                    "classification": threat_classification.get("threat_level", "unknown"),
                    "entity_score": round(entity_score, 3),
                    "threat_entities": threat_entities,
                }
            
            logger.debug(f"Threat detection: score={combined_score:.3f}, level={threat_level}")
            return result
        
        except Exception as e:
            logger.error(f"Error in threat detection: {e}")
            return {
                "threat_detected": False,
                "threat_score": 0.0,
                "threat_level": "unknown",
                "error": str(e),
            }
    
    def _detect_keywords(self, text: str) -> tuple[float, Dict[str, List[str]]]:
        """Detect threat keywords in text.
        
        Returns:
            Tuple of (score, matched_keywords_by_category)
        """
        text_lower = text.lower()
        matches = {}
        total_matches = 0
        
        for category, patterns in self.threat_keywords.items():
            category_matches = []
            for pattern in patterns:
                found = re.findall(pattern, text_lower, re.IGNORECASE)
                if found:
                    category_matches.extend(found)
                    total_matches += len(found)
            
            if category_matches:
                matches[category] = list(set(category_matches))
        
        # Score based on number and diversity of matches
        if total_matches == 0:
            score = 0.0
        elif total_matches <= 2:
            score = 0.3
        elif total_matches <= 5:
            score = 0.6
        else:
            score = 0.9
        
        # Boost score if multiple categories matched
        if len(matches) >= 3:
            score = min(1.0, score * 1.2)
        
        return score, matches
    
    def _sentiment_to_threat_score(self, sentiment: Dict[str, Any]) -> float:
        """Convert sentiment to threat score.
        
        Negative sentiment can indicate threat content.
        """
        if sentiment["sentiment"] == "negative":
            return sentiment["score"] * 0.7  # Scale down, sentiment alone isn't definitive
        elif sentiment["sentiment"] == "neutral":
            return 0.3
        else:
            return 0.1
    
    def _classification_to_score(self, classification: Dict[str, Any]) -> float:
        """Convert threat classification to score."""
        threat_level = classification.get("threat_level", "").lower()
        confidence = classification.get("confidence", 0.0)
        
        level_scores = {
            "critical threat": 1.0,
            "high threat": 0.8,
            "medium threat": 0.5,
            "low threat": 0.2,
            "no threat": 0.0,
        }
        
        base_score = level_scores.get(threat_level, 0.3)
        return base_score * confidence
    
    def _detect_threat_entities(self, text: str) -> tuple[float, Dict[str, List[str]]]:
        """Detect threat-related entities.
        
        Returns:
            Tuple of (score, threat_entities)
        """
        # Extract all entities
        entities = self.ner_service.get_unique_entities(text, min_confidence=0.6)
        
        threat_entities = {
            "threat_actors": [],
            "weapons": [],
            "locations": [],
        }
        
        # Check organizations for threat actors
        orgs = entities.get("ORGANIZATION", []) + entities.get("ORG", [])
        for org in orgs:
            if any(actor.lower() in org.lower() for actor in self.threat_actors):
                threat_entities["threat_actors"].append(org)
        
        # Check for weapons/threat items in misc entities
        misc = entities.get("MISC", [])
        for item in misc:
            if any(weapon.lower() in item.lower() for weapon in self.threat_items):
                threat_entities["weapons"].append(item)
        
        # Include locations (relevant for geo-targeting)
        locations = entities.get("LOCATION", []) + entities.get("GPE", [])
        threat_entities["locations"] = locations[:5]  # Top 5
        
        # Calculate score
        actor_score = min(1.0, len(threat_entities["threat_actors"]) * 0.4)
        weapon_score = min(1.0, len(threat_entities["weapons"]) * 0.3)
        
        total_score = actor_score + weapon_score
        
        return min(1.0, total_score), threat_entities
    
    def _score_to_level(self, score: float) -> str:
        """Convert threat score to level."""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low"
        else:
            return "none"
    
    def batch_detect(
        self,
        texts: List[str],
        include_details: bool = False,
    ) -> List[Dict[str, Any]]:
        """Detect threats in multiple texts.
        
        Args:
            texts: List of input texts
            include_details: Whether to include detailed analysis
        
        Returns:
            List of threat assessments
        """
        return [
            self.detect_threats(text, include_details)
            for text in texts
        ]
    
    def get_threat_summary(
        self,
        texts: List[str],
    ) -> Dict[str, Any]:
        """Get threat summary for a collection of texts.
        
        Args:
            texts: List of texts
        
        Returns:
            Summary statistics
        """
        if not texts:
            return {
                "total": 0,
                "threats_detected": 0,
                "threat_rate": 0.0,
            }
        
        results = self.batch_detect(texts, include_details=False)
        
        threats_detected = sum(1 for r in results if r["threat_detected"])
        
        # Count by level
        levels = {"critical": 0, "high": 0, "medium": 0, "low": 0, "none": 0}
        for result in results:
            level = result.get("threat_level", "none")
            levels[level] = levels.get(level, 0) + 1
        
        # Average threat score
        avg_score = sum(r["threat_score"] for r in results) / len(results)
        
        return {
            "total": len(texts),
            "threats_detected": threats_detected,
            "threat_rate": (threats_detected / len(texts)) * 100,
            "avg_threat_score": round(avg_score, 3),
            "by_level": levels,
        }


# Global instance
_threat_detection_service: Optional[ThreatDetectionService] = None


def get_threat_detection_service() -> ThreatDetectionService:
    """Get the global threat detection service instance."""
    global _threat_detection_service
    if _threat_detection_service is None:
        _threat_detection_service = ThreatDetectionService()
    return _threat_detection_service
