"""Anomaly explanation system - explains WHY anomalies occurred using LLM."""

import logging
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime

from .llm_service import get_llm_service, LLMService

logger = logging.getLogger(__name__)


class AnomalyExplainer:
    """Explain detected anomalies in human-readable terms."""
    
    def __init__(self, llm_service: LLMService | None = None):
        """Initialize anomaly explainer.
        
        Args:
            llm_service: LLM service instance
        """
        self.llm = llm_service or get_llm_service()
        self.explanations: dict[UUID, dict[str, Any]] = {}
    
    async def explain_anomaly(
        self,
        anomaly_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate human-readable explanation for anomaly.
        
        Args:
            anomaly_data: Anomaly detection data
            context: Additional context (historical data, related events)
        
        Returns:
            Explanation with possible causes and recommendations
        """
        system_prompt = """You are an intelligence analyst explaining anomalies and unusual patterns.
Provide clear, logical explanations for why something is anomalous.
Consider multiple hypotheses and rank by likelihood.
Be specific about what makes it unusual and what it could indicate."""
        
        context_str = ""
        if context:
            context_str = f"\n\nAdditional Context:\n{self._format_context(context)}"
        
        prompt = f"""Explain this detected anomaly:

Anomaly Type: {anomaly_data.get('type', 'Unknown')}
Detection Date: {anomaly_data.get('detection_date', 'Unknown')}
Location: {anomaly_data.get('location', 'Unknown')}
Anomaly Score: {anomaly_data.get('anomaly_score', 0):.2f}
Baseline Value: {anomaly_data.get('baseline', 'N/A')}
Observed Value: {anomaly_data.get('observed', 'N/A')}
Deviation: {anomaly_data.get('deviation', 'N/A')}

Details:
{self._format_dict(anomaly_data.get('details', {}))}
{context_str}

Provide:
1. What is anomalous (clear explanation)
2. Possible causes (ranked by likelihood)
   - Natural causes
   - Human activities
   - Technical issues
   - Hostile actions
3. Implications
4. Recommended verification steps
5. Priority level"""
        
        try:
            explanation = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.6,
                max_tokens=1500,
            )
            
            result = {
                "explanation_id": str(uuid4()),
                "anomaly_id": anomaly_data.get('id'),
                "generated_at": datetime.utcnow().isoformat(),
                "explanation": explanation,
                "anomaly_data": anomaly_data,
                "llm_provider": self.llm.config.provider.value,
            }
            
            # Store explanation
            self.explanations[UUID(result["explanation_id"])] = result
            
            return result
        
        except Exception as e:
            logger.error(f"Anomaly explanation error: {e}")
            raise
    
    async def explain_satellite_change(
        self,
        change_data: dict[str, Any],
        before_image_date: str,
        after_image_date: str,
    ) -> dict[str, Any]:
        """Explain satellite-detected changes.
        
        Args:
            change_data: Change detection results
            before_image_date: Date of before image
            after_image_date: Date of after image
        
        Returns:
            Explanation of what changed and why
        """
        system_prompt = """You are a remote sensing analyst explaining satellite imagery changes.
Provide clear explanations of what physical changes occurred on the ground and likely causes.
Consider seasonal variations, human activities, natural events, and conflicts."""
        
        prompt = f"""Explain this satellite-detected change:

Analysis Type: {change_data.get('analysis_type', 'Unknown')}
Location: {change_data.get('location', 'Unknown')}
Before Date: {before_image_date}
After Date: {after_image_date}
Change Percentage: {change_data.get('change_percentage', 0)}%
Area Affected: {change_data.get('area_hectares', 0)} hectares
Confidence: {change_data.get('confidence', 0):.2f}

Measurements:
{self._format_dict(change_data.get('measurements', {}))}

Explain:
1. What physical change occurred on the ground
2. Most likely causes (ranked)
3. Whether this is concerning (and why)
4. What to investigate further
5. Similar patterns to watch for"""
        
        try:
            explanation = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=1200,
            )
            
            return {
                "explanation_id": str(uuid4()),
                "change_type": change_data.get('analysis_type'),
                "generated_at": datetime.utcnow().isoformat(),
                "explanation": explanation,
                "change_data": change_data,
            }
        
        except Exception as e:
            logger.error(f"Change explanation error: {e}")
            raise
    
    async def explain_narrative_mutation(
        self,
        mutation_data: dict[str, Any],
        narrative_name: str,
    ) -> dict[str, Any]:
        """Explain why a narrative shifted or mutated.
        
        Args:
            mutation_data: Mutation detection data
            narrative_name: Name of the narrative
        
        Returns:
            Explanation of narrative shift
        """
        system_prompt = """You are an information warfare analyst explaining narrative mutations and framing shifts.
Explain why narratives change, who benefits, and what it indicates about information campaigns."""
        
        prompt = f"""Explain this narrative mutation:

Narrative: {narrative_name}
Mutation Type: {mutation_data.get('mutation_type', 'Unknown')}
Detected: {mutation_data.get('detected_at', 'Unknown')}

Before Keywords: {mutation_data.get('before_keywords', [])}
After Keywords: {mutation_data.get('after_keywords', [])}

Before Sentiment: {mutation_data.get('before_sentiment', 0):.2f}
After Sentiment: {mutation_data.get('after_sentiment', 0):.2f}

Confidence: {mutation_data.get('confidence', 0):.2f}

Explain:
1. What changed in the narrative
2. Why this shift likely occurred
3. Who benefits from this change
4. Whether this is organic or orchestrated
5. What to monitor next
6. Counter-narrative strategies"""
        
        try:
            explanation = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.6,
                max_tokens=1200,
            )
            
            return {
                "explanation_id": str(uuid4()),
                "narrative": narrative_name,
                "mutation_type": mutation_data.get('mutation_type'),
                "generated_at": datetime.utcnow().isoformat(),
                "explanation": explanation,
                "mutation_data": mutation_data,
            }
        
        except Exception as e:
            logger.error(f"Mutation explanation error: {e}")
            raise
    
    def _format_dict(self, data: dict[str, Any]) -> str:
        """Format dictionary for prompt."""
        return "\n".join([f"- {k}: {v}" for k, v in data.items()])
    
    def _format_context(self, context: dict[str, Any]) -> str:
        """Format context for prompt."""
        lines = []
        for key, value in context.items():
            if isinstance(value, (list, dict)):
                lines.append(f"{key}: {len(value)} items")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def _parse_insights_response(self, response: str, category: str) -> list[Insight]:
        """Parse LLM response into Insight objects."""
        # Simplified parsing
        insight = Insight(
            insight_id=uuid4(),
            category=category,
            title=f"AI-Discovered {category}",
            description=response[:500],
            confidence=0.7,
            importance="MEDIUM",
        )
        
        return [insight]


# Global instance
_anomaly_explainer: AnomalyExplainer | None = None


def get_anomaly_explainer() -> AnomalyExplainer:
    """Get anomaly explainer instance."""
    global _anomaly_explainer
    if _anomaly_explainer is None:
        _anomaly_explainer = AnomalyExplainer()
    return _anomaly_explainer
