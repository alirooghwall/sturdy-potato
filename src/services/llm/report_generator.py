"""Intelligent report generation using LLM."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from .llm_service import get_llm_service, LLMService

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate intelligent reports using LLM."""
    
    def __init__(self, llm_service: LLMService | None = None):
        """Initialize report generator.
        
        Args:
            llm_service: LLM service instance (uses global if None)
        """
        self.llm = llm_service or get_llm_service()
    
    async def generate_satellite_analysis_report(
        self,
        analysis_data: dict[str, Any],
        analysis_type: str,
        include_recommendations: bool = True,
        format: str = "markdown",
    ) -> dict[str, Any]:
        """Generate comprehensive report from satellite analysis.
        
        Args:
            analysis_data: Analysis results
            analysis_type: Type of analysis (deforestation, flood, etc.)
            include_recommendations: Include actionable recommendations
            format: Output format (markdown, html, pdf)
        
        Returns:
            Generated report with metadata
        """
        system_prompt = """You are an expert ISR analyst specializing in satellite imagery analysis and geospatial intelligence. 
Your task is to generate professional, actionable intelligence reports from satellite analysis data.

Format your reports with:
- Executive Summary
- Key Findings
- Detailed Analysis
- Risk Assessment
- Actionable Recommendations
- Next Steps

Be precise, use military/intelligence terminology when appropriate, and focus on actionable insights."""
        
        user_prompt = f"""Generate a comprehensive {analysis_type} analysis report based on the following data:

Analysis Type: {analysis_type}
Detection Date: {analysis_data.get('detection_date', 'N/A')}
Location: {analysis_data.get('location', 'N/A')}
Area Affected: {analysis_data.get('area_affected_hectares', 0)} hectares
Change Magnitude: {analysis_data.get('change_percentage', 0)}%
Confidence: {analysis_data.get('confidence', 0):.2f}
Severity: {analysis_data.get('severity', 'N/A')}

Additional Details:
{self._format_dict(analysis_data.get('details', {}))}

Please provide:
1. Executive summary (2-3 sentences)
2. Key findings (bullet points)
3. Detailed analysis
4. Risk assessment
5. {'Actionable recommendations' if include_recommendations else 'Observations'}

Format in {format}."""
        
        try:
            report_content = await self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for factual reports
                max_tokens=2000,
            )
            
            return {
                "report_id": str(uuid4()),
                "analysis_type": analysis_type,
                "generated_at": datetime.utcnow().isoformat(),
                "format": format,
                "content": report_content,
                "source_data": analysis_data,
                "metadata": {
                    "llm_provider": self.llm.config.provider.value,
                    "llm_model": self.llm.default_model,
                    "confidence": analysis_data.get('confidence', 0),
                },
            }
        
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            raise
    
    async def generate_narrative_intelligence_report(
        self,
        narrative_data: dict[str, Any],
        related_sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate intelligence report on narrative evolution.
        
        Args:
            narrative_data: Narrative tracking data
            related_sources: Related source information
        
        Returns:
            Intelligence report
        """
        system_prompt = """You are an information warfare analyst specializing in narrative tracking, propaganda detection, and influence operations.
Generate tactical intelligence reports that identify:
- Narrative evolution patterns
- Coordination indicators
- Target audiences
- Threat assessments
- Counter-narrative recommendations"""
        
        user_prompt = f"""Generate a narrative intelligence report:

Narrative: {narrative_data.get('name', 'Unknown')}
Status: {narrative_data.get('status', 'Unknown')}
Propagation Pattern: {narrative_data.get('propagation_pattern', 'Unknown')}
Total Volume: {narrative_data.get('total_volume', 0)} mentions
Growth Rate: {narrative_data.get('growth_rate', 0):.2f}%/hour
Platforms: {narrative_data.get('platforms', [])}

Key Keywords: {narrative_data.get('top_keywords', [])}
Key Entities: {narrative_data.get('top_entities', [])}

Mutations Detected: {len(narrative_data.get('mutation_events', []))}
Related Narratives: {len(narrative_data.get('related_narratives', []))}

Analyze:
1. Narrative intent and objectives
2. Target audiences
3. Coordination indicators
4. Threat level assessment
5. Counter-narrative strategies"""
        
        try:
            report_content = await self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=2000,
            )
            
            return {
                "report_id": str(uuid4()),
                "report_type": "narrative_intelligence",
                "generated_at": datetime.utcnow().isoformat(),
                "content": report_content,
                "narrative_data": narrative_data,
            }
        
        except Exception as e:
            logger.error(f"Narrative report error: {e}")
            raise
    
    async def generate_executive_briefing(
        self,
        alerts: list[dict[str, Any]],
        key_events: list[dict[str, Any]],
        time_period: str = "24h",
    ) -> dict[str, Any]:
        """Generate executive briefing summarizing all activities.
        
        Args:
            alerts: Recent alerts
            key_events: Key events detected
            time_period: Time period for briefing
        
        Returns:
            Executive briefing
        """
        system_prompt = """You are a senior intelligence officer preparing executive-level briefings for decision-makers.
Provide concise, high-level summaries focusing on:
- Most critical threats
- Emerging trends
- Required actions
- Strategic implications

Use clear, decisive language appropriate for executive consumption."""
        
        # Organize alerts by severity
        critical = [a for a in alerts if a.get('severity') == 'CRITICAL']
        high = [a for a in alerts if a.get('severity') == 'HIGH']
        
        user_prompt = f"""Generate executive briefing for the past {time_period}:

CRITICAL ALERTS: {len(critical)}
{self._format_alerts_summary(critical[:5])}

HIGH PRIORITY ALERTS: {len(high)}
{self._format_alerts_summary(high[:5])}

KEY EVENTS: {len(key_events)}
{self._format_events_summary(key_events[:10])}

Provide:
1. Situation Overview (3-4 sentences)
2. Top 3 Critical Issues (ranked by priority)
3. Emerging Trends
4. Immediate Actions Required
5. Strategic Recommendations

Keep it concise - executive summary style."""
        
        try:
            briefing_content = await self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2,  # Very factual
                max_tokens=1500,
            )
            
            return {
                "briefing_id": str(uuid4()),
                "generated_at": datetime.utcnow().isoformat(),
                "time_period": time_period,
                "content": briefing_content,
                "statistics": {
                    "critical_alerts": len(critical),
                    "high_alerts": len(high),
                    "total_alerts": len(alerts),
                    "key_events": len(key_events),
                },
            }
        
        except Exception as e:
            logger.error(f"Executive briefing error: {e}")
            raise
    
    async def generate_threat_assessment(
        self,
        threat_data: dict[str, Any],
        historical_context: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate detailed threat assessment report.
        
        Args:
            threat_data: Current threat information
            historical_context: Historical threat data
        
        Returns:
            Threat assessment report
        """
        system_prompt = """You are a threat intelligence analyst. Generate detailed threat assessments that include:
- Threat characterization
- Capability analysis
- Intent assessment
- Opportunity evaluation
- Risk scoring
- Mitigation recommendations"""
        
        user_prompt = f"""Generate threat assessment:

Current Threat:
Type: {threat_data.get('type', 'Unknown')}
Severity: {threat_data.get('severity', 'Unknown')}
Confidence: {threat_data.get('confidence', 0)}
Location: {threat_data.get('location', 'Unknown')}

Indicators:
{self._format_dict(threat_data.get('indicators', {}))}

Historical Context:
{len(historical_context)} similar incidents in past 90 days

Provide:
1. Threat Summary
2. Actor Analysis (if applicable)
3. Capability Assessment
4. Intent Indicators
5. Risk Score (1-10)
6. Recommended Response Actions
7. Monitoring Requirements"""
        
        try:
            assessment_content = await self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=2000,
            )
            
            return {
                "assessment_id": str(uuid4()),
                "generated_at": datetime.utcnow().isoformat(),
                "content": assessment_content,
                "threat_data": threat_data,
            }
        
        except Exception as e:
            logger.error(f"Threat assessment error: {e}")
            raise
    
    def _format_dict(self, data: dict[str, Any]) -> str:
        """Format dictionary for prompt."""
        return "\n".join([f"- {k}: {v}" for k, v in data.items()])
    
    def _format_alerts_summary(self, alerts: list[dict[str, Any]]) -> str:
        """Format alerts for prompt."""
        if not alerts:
            return "None"
        
        summary = []
        for alert in alerts:
            summary.append(
                f"- [{alert.get('severity')}] {alert.get('event_type')}: "
                f"{alert.get('description', '')[:100]}"
            )
        return "\n".join(summary)
    
    def _format_events_summary(self, events: list[dict[str, Any]]) -> str:
        """Format events for prompt."""
        if not events:
            return "None"
        
        summary = []
        for event in events:
            summary.append(
                f"- {event.get('timestamp')}: {event.get('description', '')[:80]}"
            )
        return "\n".join(summary)


# Global instance
_report_generator: ReportGenerator | None = None


def get_report_generator() -> ReportGenerator:
    """Get report generator instance."""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
