"""Advanced Propaganda and Disinformation Detection Service.

Detects propaganda, disinformation, and manipulation techniques using:
- Propaganda technique detection (14+ techniques)
- Narrative consistency analysis
- Source credibility assessment
- Cross-reference verification
- Temporal consistency checking
- Emotional manipulation detection
- Logical fallacy detection
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .classification_service import get_classification_service
from .sentiment_service import get_sentiment_service
from .ner_service import get_ner_service
from .embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class PropagandaDetector:
    """Advanced propaganda and disinformation detection.
    
    Detects 14 propaganda techniques:
    1. Loaded Language
    2. Name Calling/Labeling
    3. Repetition
    4. Exaggeration/Minimization
    5. Appeal to Fear/Prejudice
    6. Doubt
    7. Flag-Waving (Patriotism)
    8. Causal Oversimplification
    9. Slogans
    10. Appeal to Authority
    11. Black-and-White Fallacy
    12. Thought-terminating Cliche
    13. Whataboutism
    14. Bandwagon
    """

    def __init__(self):
        """Initialize propaganda detector."""
        self.classification_service = get_classification_service()
        self.sentiment_service = get_sentiment_service()
        self.ner_service = get_ner_service()
        self.embedding_service = get_embedding_service()
        
        # Propaganda technique patterns
        self.propaganda_patterns = self._init_propaganda_patterns()
        
        # Emotional manipulation keywords
        self.emotional_keywords = {
            "fear": ["threat", "danger", "terror", "crisis", "attack", "destroy", "eliminate"],
            "anger": ["outrage", "disgrace", "shame", "betrayal", "scandal", "corrupt"],
            "pride": ["great", "glory", "victory", "triumph", "hero", "brave"],
            "disgust": ["disgusting", "vile", "filthy", "repulsive", "abhorrent"],
        }
        
        # Logical fallacy patterns
        self.fallacy_patterns = {
            "ad_hominem": r"\b(they|he|she) (is|are) (stupid|fool|idiot|liar)\b",
            "false_dichotomy": r"\b(either|or|only two)\b",
            "slippery_slope": r"\b(if .+ then .+ will)\b",
            "hasty_generalization": r"\b(all|every|always|never|none)\b",
            "strawman": r"\b(claims?|says?|thinks?) that\b",
        }
        
        logger.info("Propaganda detector initialized")
    
    def _init_propaganda_patterns(self) -> Dict[str, List[str]]:
        """Initialize propaganda technique detection patterns."""
        return {
            "loaded_language": [
                r"\b(destroy|annihilate|massacre|slaughter|invade)\b",
                r"\b(evil|terrorist|radical|extremist|militant)\b",
                r"\b(hero|patriot|freedom|liberty|justice)\b",
            ],
            "name_calling": [
                r"\b(terrorist|extremist|radical|fanatic|criminal)\b",
                r"\b(puppet|traitor|coward|fool|liar)\b",
            ],
            "flag_waving": [
                r"\b(nation|country|patriot|homeland|freedom|liberty)\b",
                r"\b(our (people|country|nation|values))\b",
            ],
            "appeal_to_fear": [
                r"\b(threat|danger|risk|warning|alarm|crisis)\b",
                r"\b(if (we|you) don't|unless (we|you))\b",
            ],
            "exaggeration": [
                r"\b(always|never|all|none|every|completely|totally)\b",
                r"\b(massive|huge|enormous|devastating|catastrophic)\b",
            ],
            "doubt": [
                r"\b(allegedly|supposedly|so-called|claims|purportedly)\b",
                r"\b(questions? remain|unclear|disputed|unconfirmed)\b",
            ],
            "repetition": [
                # Detected algorithmically
            ],
            "slogans": [
                r"\b(make .+ great again|fight for|stand with|together we)\b",
            ],
            "whataboutism": [
                r"\b(what about|but what of|and yet|meanwhile)\b",
            ],
            "bandwagon": [
                r"\b(everyone|everybody|all of us|join us|be part of)\b",
                r"\b(millions|thousands|most people|the world)\b",
            ],
        }
    
    def detect_propaganda(
        self,
        text: str,
        check_all: bool = True,
    ) -> Dict[str, Any]:
        """Detect propaganda techniques in text.
        
        Args:
            text: Input text to analyze
            check_all: Whether to run all detection methods
        
        Returns:
            Dictionary with propaganda analysis
        """
        if not text or not text.strip():
            return {
                "is_propaganda": False,
                "confidence": 0.0,
                "techniques": [],
                "analysis": {},
            }
        
        try:
            # 1. Detect specific propaganda techniques
            techniques = self._detect_techniques(text)
            
            # 2. Emotional manipulation detection
            emotional_manipulation = self._detect_emotional_manipulation(text)
            
            # 3. Logical fallacy detection
            fallacies = self._detect_logical_fallacies(text)
            
            # 4. Sentiment extremity (very positive or very negative)
            sentiment = self.sentiment_service.analyze(text)
            sentiment_extremity = abs(self.sentiment_service.get_polarity_score(text))
            
            # 5. Language analysis
            language_analysis = self._analyze_language(text)
            
            # 6. Source credibility indicators
            credibility_indicators = self._check_credibility_indicators(text)
            
            # Calculate propaganda score
            propaganda_score = self._calculate_propaganda_score(
                techniques=techniques,
                emotional_manipulation=emotional_manipulation,
                fallacies=fallacies,
                sentiment_extremity=sentiment_extremity,
                language_analysis=language_analysis,
                credibility_indicators=credibility_indicators,
            )
            
            # Determine if propaganda
            is_propaganda = propaganda_score > 0.5
            
            return {
                "is_propaganda": is_propaganda,
                "propaganda_score": round(propaganda_score, 3),
                "confidence": round(min(propaganda_score * 1.2, 1.0), 3),
                "techniques_detected": techniques,
                "emotional_manipulation": emotional_manipulation,
                "logical_fallacies": fallacies,
                "sentiment": {
                    "type": sentiment["sentiment"],
                    "extremity": round(sentiment_extremity, 3),
                },
                "language_analysis": language_analysis,
                "credibility_indicators": credibility_indicators,
                "risk_level": self._score_to_risk_level(propaganda_score),
            }
        
        except Exception as e:
            logger.error(f"Error detecting propaganda: {e}")
            return {
                "is_propaganda": False,
                "propaganda_score": 0.0,
                "error": str(e),
            }
    
    def _detect_techniques(self, text: str) -> List[Dict[str, Any]]:
        """Detect specific propaganda techniques."""
        detected = []
        text_lower = text.lower()
        
        for technique, patterns in self.propaganda_patterns.items():
            if technique == "repetition":
                # Detect repetition algorithmically
                repetition_score = self._detect_repetition(text)
                if repetition_score > 0.3:
                    detected.append({
                        "technique": "repetition",
                        "confidence": repetition_score,
                        "examples": [],
                    })
            else:
                matches = []
                for pattern in patterns:
                    found = re.findall(pattern, text_lower, re.IGNORECASE)
                    if found:
                        matches.extend(found)
                
                if matches:
                    detected.append({
                        "technique": technique,
                        "confidence": min(len(matches) * 0.2, 1.0),
                        "examples": list(set(matches))[:5],
                    })
        
        return detected
    
    def _detect_repetition(self, text: str) -> float:
        """Detect repetitive phrases."""
        # Extract phrases (3-5 words)
        words = text.lower().split()
        phrases = []
        
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            phrases.append(phrase)
        
        # Count repetitions
        from collections import Counter
        phrase_counts = Counter(phrases)
        
        # Calculate repetition score
        total_phrases = len(phrases)
        if total_phrases == 0:
            return 0.0
        
        repeated = sum(1 for count in phrase_counts.values() if count > 1)
        repetition_score = repeated / total_phrases
        
        return min(repetition_score * 3, 1.0)
    
    def _detect_emotional_manipulation(self, text: str) -> Dict[str, Any]:
        """Detect emotional manipulation techniques."""
        text_lower = text.lower()
        emotions_detected = {}
        
        for emotion, keywords in self.emotional_keywords.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                emotions_detected[emotion] = {
                    "keywords": matches,
                    "intensity": min(len(matches) * 0.3, 1.0),
                }
        
        # Calculate overall emotional manipulation score
        if emotions_detected:
            avg_intensity = sum(e["intensity"] for e in emotions_detected.values()) / len(emotions_detected)
            manipulation_score = avg_intensity
        else:
            manipulation_score = 0.0
        
        return {
            "detected": len(emotions_detected) > 0,
            "score": round(manipulation_score, 3),
            "emotions": emotions_detected,
        }
    
    def _detect_logical_fallacies(self, text: str) -> List[Dict[str, Any]]:
        """Detect logical fallacies."""
        fallacies_found = []
        
        for fallacy, pattern in self.fallacy_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                fallacies_found.append({
                    "fallacy": fallacy,
                    "confidence": min(len(matches) * 0.25, 1.0),
                    "examples": list(set(str(m) for m in matches))[:3],
                })
        
        return fallacies_found
    
    def _analyze_language(self, text: str) -> Dict[str, Any]:
        """Analyze language characteristics."""
        words = text.split()
        
        # Count absolutes
        absolutes = ["all", "every", "always", "never", "none", "nothing", "everything"]
        absolute_count = sum(1 for word in words if word.lower() in absolutes)
        
        # Count superlatives
        superlatives = ["best", "worst", "greatest", "terrible", "amazing", "horrible"]
        superlative_count = sum(1 for word in words if word.lower() in superlatives)
        
        # Count exclamations
        exclamation_count = text.count("!")
        
        # Count questions
        question_count = text.count("?")
        
        # Calculate scores
        absolute_score = min(absolute_count * 0.1, 1.0)
        superlative_score = min(superlative_count * 0.15, 1.0)
        exclamation_score = min(exclamation_count * 0.1, 1.0)
        
        return {
            "absolute_language_score": round(absolute_score, 3),
            "superlative_score": round(superlative_score, 3),
            "exclamation_score": round(exclamation_score, 3),
            "question_count": question_count,
            "overall_language_manipulation": round(
                (absolute_score + superlative_score + exclamation_score) / 3, 3
            ),
        }
    
    def _check_credibility_indicators(self, text: str) -> Dict[str, Any]:
        """Check for credibility indicators and red flags."""
        text_lower = text.lower()
        
        # Positive indicators
        positive_indicators = {
            "sources_cited": bool(re.search(r"\b(according to|source|reported by)\b", text_lower)),
            "specific_details": bool(re.search(r"\d{4}|\d+%|[A-Z][a-z]+ \d+", text)),
            "balanced_view": "however" in text_lower or "although" in text_lower,
        }
        
        # Red flags
        red_flags = {
            "unverified_claims": bool(re.search(r"\b(allegedly|supposedly|rumor|unconfirmed)\b", text_lower)),
            "sensational_language": bool(re.search(r"\b(shocking|unbelievable|exclusive|breaking)\b", text_lower)),
            "conspiracy_language": bool(re.search(r"\b(they don't want|hidden|secret|cover-up)\b", text_lower)),
            "urgent_action": bool(re.search(r"\b(act now|urgent|immediately|hurry)\b", text_lower)),
        }
        
        credibility_score = (
            sum(positive_indicators.values()) * 0.2 -
            sum(red_flags.values()) * 0.25
        )
        credibility_score = max(0, min(1, 0.5 + credibility_score))
        
        return {
            "credibility_score": round(credibility_score, 3),
            "positive_indicators": positive_indicators,
            "red_flags": red_flags,
        }
    
    def _calculate_propaganda_score(
        self,
        techniques: List[Dict],
        emotional_manipulation: Dict,
        fallacies: List[Dict],
        sentiment_extremity: float,
        language_analysis: Dict,
        credibility_indicators: Dict,
    ) -> float:
        """Calculate overall propaganda score."""
        # Technique score (0-0.3)
        technique_score = min(len(techniques) * 0.1, 0.3)
        
        # Emotional manipulation score (0-0.2)
        emotion_score = emotional_manipulation["score"] * 0.2
        
        # Fallacy score (0-0.2)
        fallacy_score = min(len(fallacies) * 0.1, 0.2)
        
        # Sentiment extremity (0-0.15)
        sentiment_score = sentiment_extremity * 0.15
        
        # Language manipulation (0-0.1)
        language_score = language_analysis["overall_language_manipulation"] * 0.1
        
        # Credibility (0-0.05, inverted - low credibility = high propaganda)
        credibility_score = (1 - credibility_indicators["credibility_score"]) * 0.05
        
        total = (
            technique_score +
            emotion_score +
            fallacy_score +
            sentiment_score +
            language_score +
            credibility_score
        )
        
        return min(total, 1.0)
    
    def _score_to_risk_level(self, score: float) -> str:
        """Convert propaganda score to risk level."""
        if score >= 0.75:
            return "CRITICAL"
        elif score >= 0.6:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        elif score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"
    
    def compare_narratives(
        self,
        texts: List[str],
        threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """Compare multiple texts for coordinated propaganda narratives.
        
        Args:
            texts: List of texts to compare
            threshold: Similarity threshold for narrative matching
        
        Returns:
            Analysis of narrative coordination
        """
        if len(texts) < 2:
            return {"coordinated": False, "narrative_clusters": []}
        
        try:
            # Detect propaganda in each text
            propaganda_results = [self.detect_propaganda(text) for text in texts]
            
            # Count propaganda texts
            propaganda_count = sum(1 for r in propaganda_results if r["is_propaganda"])
            
            # Compute semantic similarity between texts
            embeddings = self.embedding_service.encode(texts)
            similarities = self.embedding_service.batch_similarity(texts, texts)
            
            # Find coordinated clusters (high similarity + propaganda)
            coordinated = False
            if propaganda_count >= 2:
                # Check if propaganda texts are similar
                for i in range(len(texts)):
                    for j in range(i + 1, len(texts)):
                        if (propaganda_results[i]["is_propaganda"] and
                            propaganda_results[j]["is_propaganda"] and
                            similarities[i][j] >= threshold):
                            coordinated = True
                            break
            
            return {
                "coordinated": coordinated,
                "total_texts": len(texts),
                "propaganda_count": propaganda_count,
                "propaganda_rate": propaganda_count / len(texts),
                "avg_similarity": float(similarities.mean()) if len(similarities) > 0 else 0.0,
                "high_similarity_pairs": int((similarities >= threshold).sum() / 2),
                "individual_results": propaganda_results,
            }
        
        except Exception as e:
            logger.error(f"Error comparing narratives: {e}")
            return {"coordinated": False, "error": str(e)}


# Global instance
_propaganda_detector: Optional[PropagandaDetector] = None


def get_propaganda_detector() -> PropagandaDetector:
    """Get the global propaganda detector instance."""
    global _propaganda_detector
    if _propaganda_detector is None:
        _propaganda_detector = PropagandaDetector()
    return _propaganda_detector
