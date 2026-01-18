"""Advanced News Verification and Fact-Checking Service.

Multi-layer verification system:
1. Source credibility scoring
2. Cross-reference verification
3. Temporal consistency checking
4. Entity verification
5. Claim extraction and verification
6. Historical context analysis
7. Bias detection
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from .propaganda_detector import get_propaganda_detector
from .classification_service import get_classification_service
from .ner_service import get_ner_service
from .embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class NewsVerifier:
    """Advanced news verification and fact-checking system.
    
    Verification Methods:
    1. Source Credibility (domain, author, publication history)
    2. Cross-Reference (multiple sources corroborate)
    3. Temporal Consistency (timeline makes sense)
    4. Entity Verification (entities exist and are correctly described)
    5. Claim Verification (factual claims can be verified)
    6. Linguistic Analysis (professional vs. amateur)
    7. Context Analysis (historical and political context)
    """

    def __init__(self):
        """Initialize news verifier."""
        self.propaganda_detector = get_propaganda_detector()
        self.classification_service = get_classification_service()
        self.ner_service = get_ner_service()
        self.embedding_service = get_embedding_service()
        
        # Source credibility database (simplified - in production use real database)
        self.trusted_sources = {
            "reuters.com": {"credibility": 0.95, "bias": "center"},
            "apnews.com": {"credibility": 0.95, "bias": "center"},
            "bbc.com": {"credibility": 0.90, "bias": "center-left"},
            "theguardian.com": {"credibility": 0.85, "bias": "center-left"},
            "nytimes.com": {"credibility": 0.85, "bias": "center-left"},
            "aljazeera.com": {"credibility": 0.75, "bias": "center"},
            "cnn.com": {"credibility": 0.70, "bias": "left"},
            "foxnews.com": {"credibility": 0.65, "bias": "right"},
        }
        
        # Claim indicators (statements that should be verified)
        self.claim_patterns = [
            r"\d+%",  # Percentages
            r"\d+\s+(people|soldiers|civilians|deaths)",  # Numbers with impact
            r"(said|claimed|stated|announced|declared) that",  # Statements
            r"(according to|reported by|sources say)",  # Attribution
        ]
        
        # Red flag patterns for fake news
        self.fake_news_indicators = {
            "clickbait": [
                r"you won't believe",
                r"shocking",
                r"secret",
                r"they don't want you to know",
                r"number \d+ will",
            ],
            "conspiracy": [
                r"cover-?up",
                r"conspiracy",
                r"they are hiding",
                r"mainstream media",
                r"deep state",
            ],
            "unreliable_sources": [
                r"anonymous sources",
                r"insider says",
                r"leaked documents",
                r"secret report",
            ],
            "emotional_manipulation": [
                r"outraged",
                r"disgusting",
                r"horrifying",
                r"devastating",
            ],
        }
        
        logger.info("News verifier initialized")
    
    def verify_news(
        self,
        title: str,
        content: str,
        source: Optional[str] = None,
        published_date: Optional[datetime] = None,
        cross_references: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Comprehensive news verification.
        
        Args:
            title: Article title
            content: Article content
            source: Source URL or domain
            published_date: Publication date
            cross_references: List of related articles from other sources
        
        Returns:
            Verification analysis with credibility score
        """
        full_text = f"{title}. {content}"
        
        try:
            # 1. Source credibility
            source_credibility = self._assess_source_credibility(source)
            
            # 2. Content quality analysis
            content_quality = self._analyze_content_quality(title, content)
            
            # 3. Propaganda/disinformation detection
            propaganda_analysis = self.propaganda_detector.detect_propaganda(full_text)
            
            # 4. Claim extraction and verifiability
            claims = self._extract_claims(full_text)
            
            # 5. Entity verification
            entity_verification = self._verify_entities(full_text)
            
            # 6. Temporal consistency
            temporal_check = self._check_temporal_consistency(content, published_date)
            
            # 7. Cross-reference verification
            cross_ref_score = 0.5  # Default if no cross-references
            if cross_references:
                cross_ref_score = self._verify_cross_references(
                    full_text, cross_references
                )
            
            # 8. Linguistic professionalism
            linguistic_score = self._assess_linguistic_quality(content)
            
            # 9. Bias detection
            bias_analysis = self._detect_bias(full_text)
            
            # 10. Fake news indicators
            fake_news_flags = self._check_fake_news_indicators(full_text)
            
            # Calculate overall credibility score
            credibility_score = self._calculate_credibility_score(
                source_credibility=source_credibility["score"],
                content_quality=content_quality["score"],
                propaganda_score=propaganda_analysis["propaganda_score"],
                cross_ref_score=cross_ref_score,
                linguistic_score=linguistic_score,
                fake_news_flags=len(fake_news_flags),
                temporal_score=temporal_check["score"],
            )
            
            # Determine verification status
            verification_status = self._score_to_status(credibility_score)
            
            return {
                "credibility_score": round(credibility_score, 3),
                "verification_status": verification_status,
                "confidence": round(self._calculate_confidence(credibility_score), 3),
                "source_credibility": source_credibility,
                "content_quality": content_quality,
                "propaganda_analysis": {
                    "is_propaganda": propaganda_analysis["is_propaganda"],
                    "score": propaganda_analysis["propaganda_score"],
                    "risk_level": propaganda_analysis.get("risk_level", "UNKNOWN"),
                },
                "claims": claims,
                "entity_verification": entity_verification,
                "temporal_consistency": temporal_check,
                "cross_reference_score": round(cross_ref_score, 3),
                "linguistic_quality": round(linguistic_score, 3),
                "bias_analysis": bias_analysis,
                "fake_news_indicators": fake_news_flags,
                "recommendation": self._get_recommendation(verification_status, credibility_score),
            }
        
        except Exception as e:
            logger.error(f"Error verifying news: {e}")
            return {
                "credibility_score": 0.0,
                "verification_status": "ERROR",
                "error": str(e),
            }
    
    def _assess_source_credibility(self, source: Optional[str]) -> Dict[str, Any]:
        """Assess source credibility."""
        if not source:
            return {
                "score": 0.5,
                "known_source": False,
                "reputation": "UNKNOWN",
            }
        
        # Extract domain
        import re
        domain_match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', source)
        domain = domain_match.group(1) if domain_match else source
        
        # Check if known trusted source
        if domain in self.trusted_sources:
            info = self.trusted_sources[domain]
            return {
                "score": info["credibility"],
                "known_source": True,
                "domain": domain,
                "reputation": "TRUSTED" if info["credibility"] >= 0.8 else "KNOWN",
                "bias": info["bias"],
            }
        
        # Unknown source - moderate score with warning
        return {
            "score": 0.4,
            "known_source": False,
            "domain": domain,
            "reputation": "UNKNOWN",
            "warning": "Source not in trusted database",
        }
    
    def _analyze_content_quality(self, title: str, content: str) -> Dict[str, Any]:
        """Analyze content quality indicators."""
        # Check title quality
        title_quality = 0.5
        if title:
            # Good indicators
            if len(title) >= 30 and len(title) <= 100:
                title_quality += 0.2
            if not title.endswith("!"):
                title_quality += 0.1
            if not any(word in title.lower() for word in ["shocking", "unbelievable"]):
                title_quality += 0.2
        
        # Check content quality
        content_quality = 0.5
        if content:
            words = content.split()
            # Length (substantial articles are better)
            if len(words) >= 200:
                content_quality += 0.2
            
            # Has paragraphs (not just wall of text)
            if "\n\n" in content or content.count("\n") >= 3:
                content_quality += 0.1
            
            # Contains quotes (good journalism)
            if '"' in content:
                content_quality += 0.1
            
            # Contains attributions
            if any(word in content.lower() for word in ["according to", "said", "reported"]):
                content_quality += 0.1
        
        overall = (title_quality + content_quality) / 2
        
        return {
            "score": min(overall, 1.0),
            "title_quality": min(title_quality, 1.0),
            "content_quality": min(content_quality, 1.0),
        }
    
    def _extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract factual claims that should be verified."""
        import re
        claims = []
        
        # Extract sentences with claim patterns
        sentences = text.split('. ')
        
        for sentence in sentences:
            for pattern in self.claim_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    claims.append({
                        "claim": sentence.strip(),
                        "type": "factual",
                        "verifiable": True,
                        "confidence": 0.7,
                    })
                    break
        
        return claims[:10]  # Return top 10 claims
    
    def _verify_entities(self, text: str) -> Dict[str, Any]:
        """Verify entities mentioned in text."""
        # Extract entities
        entities = self.ner_service.get_unique_entities(text, min_confidence=0.6)
        
        # In production, verify against knowledge base
        # For now, just count and categorize
        
        entity_count = sum(len(ents) for ents in entities.values())
        
        # More entities generally means more verifiable (but not always)
        verification_score = min(entity_count * 0.1, 0.8)
        
        return {
            "entities_found": entity_count,
            "by_type": {k: len(v) for k, v in entities.items()},
            "verification_score": verification_score,
            "entities": entities,
        }
    
    def _check_temporal_consistency(
        self,
        content: str,
        published_date: Optional[datetime],
    ) -> Dict[str, Any]:
        """Check if temporal references make sense."""
        import re
        
        # Extract date references
        date_patterns = [
            r'\d{4}',  # Years
            r'(yesterday|today|last week|last month)',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)',
        ]
        
        date_mentions = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            date_mentions.extend(matches)
        
        # Check consistency (simplified)
        consistent = True
        issues = []
        
        if published_date:
            # Check if "yesterday" matches date
            if "yesterday" in content.lower():
                # In production, verify against actual date
                pass
        
        # Score based on date references
        score = 0.7 if date_mentions else 0.5
        if not consistent:
            score = 0.3
        
        return {
            "score": score,
            "consistent": consistent,
            "date_references": len(date_mentions),
            "issues": issues,
        }
    
    def _verify_cross_references(
        self,
        text: str,
        cross_references: List[Dict[str, str]],
    ) -> float:
        """Verify against other sources."""
        if not cross_references:
            return 0.5
        
        # Compare semantic similarity with other sources
        reference_texts = [ref.get("content", ref.get("title", "")) for ref in cross_references]
        
        if not reference_texts or not any(reference_texts):
            return 0.5
        
        # Calculate similarity
        all_texts = [text] + reference_texts
        try:
            similarities = self.embedding_service.batch_similarity([text], reference_texts)
            
            if len(similarities) > 0 and len(similarities[0]) > 0:
                avg_similarity = float(similarities[0].mean())
                
                # Higher similarity = better corroboration
                # But not too high (might be copy-paste)
                if avg_similarity > 0.9:
                    score = 0.6  # Suspiciously similar
                elif avg_similarity > 0.6:
                    score = 0.9  # Good corroboration
                elif avg_similarity > 0.4:
                    score = 0.7  # Some corroboration
                else:
                    score = 0.4  # Weak corroboration
                
                return score
        except Exception as e:
            logger.error(f"Error in cross-reference verification: {e}")
        
        return 0.5
    
    def _assess_linguistic_quality(self, content: str) -> float:
        """Assess professional writing quality."""
        if not content:
            return 0.5
        
        words = content.split()
        sentences = content.split('. ')
        
        quality_score = 0.5
        
        # Average sentence length (12-20 words is good)
        if sentences:
            avg_sent_length = len(words) / len(sentences)
            if 12 <= avg_sent_length <= 20:
                quality_score += 0.2
        
        # Proper capitalization
        if sum(1 for s in sentences if s and s[0].isupper()) / max(len(sentences), 1) > 0.8:
            quality_score += 0.1
        
        # Not excessive punctuation
        if content.count("!") < len(sentences) * 0.3:
            quality_score += 0.1
        
        # Spelling (simplified check)
        if not any(word.isupper() and len(word) > 3 for word in words):
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _detect_bias(self, text: str) -> Dict[str, Any]:
        """Detect political or ideological bias."""
        text_lower = text.lower()
        
        # Bias indicators (simplified)
        left_indicators = ["progressive", "reform", "equality", "rights", "climate"]
        right_indicators = ["conservative", "traditional", "freedom", "security", "defense"]
        
        left_count = sum(1 for word in left_indicators if word in text_lower)
        right_count = sum(1 for word in right_indicators if word in text_lower)
        
        if left_count > right_count * 2:
            bias = "LEFT"
            bias_score = min(left_count * 0.2, 1.0)
        elif right_count > left_count * 2:
            bias = "RIGHT"
            bias_score = min(right_count * 0.2, 1.0)
        else:
            bias = "CENTER"
            bias_score = 0.3
        
        return {
            "detected_bias": bias,
            "bias_score": round(bias_score, 3),
            "left_indicators": left_count,
            "right_indicators": right_count,
        }
    
    def _check_fake_news_indicators(self, text: str) -> List[Dict[str, str]]:
        """Check for fake news red flags."""
        import re
        text_lower = text.lower()
        
        flags = []
        
        for category, patterns in self.fake_news_indicators.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    flags.append({
                        "category": category,
                        "indicator": pattern,
                    })
        
        return flags
    
    def _calculate_credibility_score(
        self,
        source_credibility: float,
        content_quality: float,
        propaganda_score: float,
        cross_ref_score: float,
        linguistic_score: float,
        fake_news_flags: int,
        temporal_score: float,
    ) -> float:
        """Calculate overall credibility score."""
        # Weighted components
        score = (
            source_credibility * 0.30 +
            content_quality * 0.15 +
            (1 - propaganda_score) * 0.20 +  # Inverted
            cross_ref_score * 0.15 +
            linguistic_score * 0.10 +
            temporal_score * 0.10
        )
        
        # Penalty for fake news indicators
        penalty = min(fake_news_flags * 0.1, 0.3)
        score = max(0, score - penalty)
        
        return min(score, 1.0)
    
    def _score_to_status(self, score: float) -> str:
        """Convert credibility score to status."""
        if score >= 0.8:
            return "VERIFIED"
        elif score >= 0.6:
            return "LIKELY_TRUE"
        elif score >= 0.4:
            return "UNCERTAIN"
        elif score >= 0.2:
            return "QUESTIONABLE"
        else:
            return "LIKELY_FALSE"
    
    def _calculate_confidence(self, score: float) -> float:
        """Calculate confidence in the verification."""
        # Confidence is higher at extremes
        distance_from_center = abs(score - 0.5)
        confidence = 0.5 + distance_from_center
        return min(confidence, 1.0)
    
    def _get_recommendation(self, status: str, score: float) -> str:
        """Get recommendation for users."""
        recommendations = {
            "VERIFIED": "This article appears credible and well-sourced. Safe to trust.",
            "LIKELY_TRUE": "This article appears mostly credible. Cross-check important claims.",
            "UNCERTAIN": "This article has mixed credibility. Verify claims independently before sharing.",
            "QUESTIONABLE": "This article has credibility concerns. Treat with skepticism.",
            "LIKELY_FALSE": "This article shows strong signs of misinformation. Do not trust or share.",
        }
        return recommendations.get(status, "Unable to determine credibility.")


# Global instance
_news_verifier: Optional[NewsVerifier] = None


def get_news_verifier() -> NewsVerifier:
    """Get the global news verifier instance."""
    global _news_verifier
    if _news_verifier is None:
        _news_verifier = NewsVerifier()
    return _news_verifier
