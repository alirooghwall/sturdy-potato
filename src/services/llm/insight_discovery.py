"""Automated insight discovery using LLM - finds hidden patterns and intelligence."""

import logging
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime
from dataclasses import dataclass, field

from .llm_service import get_llm_service, LLMService

logger = logging.getLogger(__name__)


@dataclass
class Insight:
    """Discovered insight."""
    insight_id: UUID
    category: str  # PATTERN, CORRELATION, ANOMALY, TREND, PREDICTION, RISK
    title: str
    description: str
    confidence: float  # 0-1
    importance: str  # CRITICAL, HIGH, MEDIUM, LOW
    evidence: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    related_data: dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.utcnow)


class InsightDiscovery:
    """Automatically discover insights from multi-source data."""
    
    def __init__(self, llm_service: LLMService | None = None):
        """Initialize insight discovery.
        
        Args:
            llm_service: LLM service instance
        """
        self.llm = llm_service or get_llm_service()
        self.discovered_insights: dict[UUID, Insight] = {}
    
    async def discover_correlations(
        self,
        satellite_alerts: list[dict[str, Any]],
        narratives: list[dict[str, Any]],
        social_media_activity: list[dict[str, Any]],
    ) -> list[Insight]:
        """Discover correlations between different data sources.
        
        This is a CREATIVE feature that finds non-obvious connections.
        
        Args:
            satellite_alerts: Recent satellite detections
            narratives: Active narratives
            social_media_activity: Social media data
        
        Returns:
            List of discovered insights
        """
        system_prompt = """You are an expert intelligence analyst specializing in cross-domain correlation analysis.
Find non-obvious connections, patterns, and relationships between different data sources.
Think like a detective - look for coincidences, timing patterns, geographic overlaps, and causal relationships."""
        
        prompt = f"""Analyze these data sources and discover meaningful correlations:

SATELLITE ALERTS ({len(satellite_alerts)}):
{self._summarize_alerts(satellite_alerts[:10])}

ACTIVE NARRATIVES ({len(narratives)}):
{self._summarize_narratives(narratives[:5])}

SOCIAL MEDIA ACTIVITY ({len(social_media_activity)}):
{self._summarize_social_activity(social_media_activity[:10])}

Discover:
1. Temporal correlations (events happening at same time)
2. Geographic correlations (events in same location)
3. Causal relationships (one event causing another)
4. Narrative-event connections (stories about real events)
5. Coordinated activities (multiple actions related)

For each correlation found, provide:
- Category (TEMPORAL, GEOGRAPHIC, CAUSAL, NARRATIVE, COORDINATED)
- Title (brief description)
- Evidence (specific data points)
- Confidence (HIGH/MEDIUM/LOW)
- Importance (CRITICAL/HIGH/MEDIUM/LOW)
- What it means (implications)

Format as JSON array of insights."""
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.6,
                max_tokens=2000,
            )
            
            # Parse response and create Insight objects
            insights = self._parse_insights_response(response, "CORRELATION")
            
            # Store insights
            for insight in insights:
                self.discovered_insights[insight.insight_id] = insight
            
            logger.info(f"Discovered {len(insights)} correlations")
            return insights
        
        except Exception as e:
            logger.error(f"Correlation discovery error: {e}")
            return []
    
    async def discover_emerging_threats(
        self,
        recent_data: dict[str, Any],
        historical_baseline: dict[str, Any],
    ) -> list[Insight]:
        """Discover emerging threats before they become critical.
        
        Uses pattern recognition to identify early warning signs.
        
        Args:
            recent_data: Recent activity data
            historical_baseline: Historical normal patterns
        
        Returns:
            List of potential emerging threats
        """
        system_prompt = """You are a threat intelligence analyst with expertise in early warning systems.
Identify subtle changes, anomalies, and patterns that could indicate emerging threats.
Look for:
- Unusual spikes or drops
- Changes in behavior patterns
- New actors or activities
- Shifts in sentiment or narratives
- Geographic anomalies"""
        
        prompt = f"""Analyze for emerging threats:

RECENT DATA (Past 48 hours):
{self._format_dict(recent_data)}

HISTORICAL BASELINE (Normal patterns):
{self._format_dict(historical_baseline)}

Identify early warning indicators:
1. Deviations from baseline
2. Unusual patterns
3. Precursor activities
4. Risk factors

For each potential threat, provide:
- Title
- Description of the pattern
- Confidence level
- Importance
- Recommended monitoring/response"""
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=1500,
            )
            
            insights = self._parse_insights_response(response, "THREAT")
            
            for insight in insights:
                self.discovered_insights[insight.insight_id] = insight
            
            logger.info(f"Discovered {len(insights)} emerging threats")
            return insights
        
        except Exception as e:
            logger.error(f"Threat discovery error: {e}")
            return []
    
    async def discover_strategic_opportunities(
        self,
        current_situation: dict[str, Any],
        objectives: list[str],
    ) -> list[Insight]:
        """Discover strategic opportunities in current situation.
        
        Creative feature for strategic planning.
        
        Args:
            current_situation: Current intelligence picture
            objectives: Strategic objectives
        
        Returns:
            Identified opportunities
        """
        system_prompt = """You are a strategic intelligence advisor.
Identify opportunities that align with objectives based on current intelligence.
Think strategically about timing, positioning, and advantage."""
        
        prompt = f"""Identify strategic opportunities:

CURRENT SITUATION:
{self._format_dict(current_situation)}

OBJECTIVES:
{chr(10).join(f'{i+1}. {obj}' for i, obj in enumerate(objectives))}

Identify:
1. Windows of opportunity
2. Advantageous conditions
3. Exploitable weaknesses
4. Favorable trends
5. Strategic timing

For each opportunity:
- Description
- How it supports objectives
- Window of opportunity
- Required actions
- Risk factors"""
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1500,
            )
            
            insights = self._parse_insights_response(response, "OPPORTUNITY")
            
            for insight in insights:
                self.discovered_insights[insight.insight_id] = insight
            
            logger.info(f"Discovered {len(insights)} strategic opportunities")
            return insights
        
        except Exception as e:
            logger.error(f"Opportunity discovery error: {e}")
            return []
    
    def _summarize_alerts(self, alerts: list[dict[str, Any]]) -> str:
        """Summarize alerts for prompt."""
        if not alerts:
            return "No recent alerts"
        
        summary = []
        for alert in alerts:
            summary.append(
                f"- [{alert.get('detection_date')}] {alert.get('event_type')}: "
                f"{alert.get('description', '')[:80]} (Severity: {alert.get('severity')})"
            )
        return "\n".join(summary)
    
    def _summarize_narratives(self, narratives: list[dict[str, Any]]) -> str:
        """Summarize narratives for prompt."""
        if not narratives:
            return "No active narratives"
        
        summary = []
        for narrative in narratives:
            summary.append(
                f"- {narrative.get('name')}: {narrative.get('status')} "
                f"(Volume: {narrative.get('total_volume')}, Growth: {narrative.get('growth_rate')}%/hr)"
            )
        return "\n".join(summary)
    
    def _summarize_social_activity(self, activity: list[dict[str, Any]]) -> str:
        """Summarize social media activity."""
        if not activity:
            return "No recent activity"
        
        summary = []
        for item in activity[:5]:
            summary.append(
                f"- [{item.get('platform')}] {item.get('content', '')[:60]}..."
            )
        return "\n".join(summary)
    
    def _format_dict(self, data: dict[str, Any]) -> str:
        """Format dictionary for prompt."""
        lines = []
        for key, value in data.items():
            if isinstance(value, list):
                lines.append(f"{key}: {len(value)} items")
            elif isinstance(value, dict):
                lines.append(f"{key}: {len(value)} entries")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def _parse_insights_response(self, response: str, default_category: str) -> list[Insight]:
        """Parse LLM response into Insight objects."""
        # Simplified parsing - in production, use more robust JSON parsing
        insights = []
        
        # Try to extract structured insights
        # For now, create one insight from the full response
        insight = Insight(
            insight_id=uuid4(),
            category=default_category,
            title=f"AI-Discovered {default_category}",
            description=response[:500],  # First 500 chars
            confidence=0.75,
            importance="MEDIUM",
            evidence=[],
            recommendations=[],
        )
        
        insights.append(insight)
        
        return insights


# Global instance
_insight_discovery: InsightDiscovery | None = None


def get_insight_discovery() -> InsightDiscovery:
    """Get insight discovery instance."""
    global _insight_discovery
    if _insight_discovery is None:
        _insight_discovery = InsightDiscovery()
    return _insight_discovery
