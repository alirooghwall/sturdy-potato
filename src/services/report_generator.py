"""Report Generation Service for ISR Platform.

Provides automated report generation for situational awareness,
threat assessments, and operational summaries.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class ReportType(str, Enum):
    """Types of reports."""
    DAILY_SITREP = "DAILY_SITREP"
    THREAT_ASSESSMENT = "THREAT_ASSESSMENT"
    INCIDENT_REPORT = "INCIDENT_REPORT"
    ANOMALY_SUMMARY = "ANOMALY_SUMMARY"
    NARRATIVE_ANALYSIS = "NARRATIVE_ANALYSIS"
    SIMULATION_RESULTS = "SIMULATION_RESULTS"
    EXECUTIVE_BRIEF = "EXECUTIVE_BRIEF"
    CUSTOM = "CUSTOM"


class ReportFormat(str, Enum):
    """Report output formats."""
    PDF = "PDF"
    HTML = "HTML"
    JSON = "JSON"
    MARKDOWN = "MARKDOWN"


class ReportStatus(str, Enum):
    """Report generation status."""
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class ReportSection:
    """A section within a report."""
    title: str
    content: str
    section_type: str = "text"
    data: dict[str, Any] = field(default_factory=dict)
    charts: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    order: int = 0


@dataclass
class Report:
    """Generated report."""
    report_id: UUID
    report_type: ReportType
    title: str
    classification: str
    status: ReportStatus
    format: ReportFormat
    created_by: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    completed_at: datetime | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    sections: list[ReportSection] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    file_path: str | None = None
    file_size_bytes: int = 0


class ReportGeneratorService:
    """Service for generating reports."""

    def __init__(self) -> None:
        """Initialize report generator."""
        self._reports: dict[UUID, Report] = {}
        self._templates: dict[ReportType, dict[str, Any]] = self._load_templates()

    def _load_templates(self) -> dict[ReportType, dict[str, Any]]:
        """Load report templates."""
        return {
            ReportType.DAILY_SITREP: {
                "title_template": "Daily Situation Report - {date}",
                "sections": ["executive_summary", "threat_overview", "incidents", 
                            "entity_activity", "recommendations"],
                "classification": "CONFIDENTIAL",
            },
            ReportType.THREAT_ASSESSMENT: {
                "title_template": "Threat Assessment Report - {region}",
                "sections": ["threat_summary", "threat_actors", "threat_scores",
                            "vulnerabilities", "mitigation"],
                "classification": "SECRET",
            },
            ReportType.INCIDENT_REPORT: {
                "title_template": "Incident Report - {incident_id}",
                "sections": ["incident_details", "timeline", "entities_involved",
                            "impact_assessment", "response_actions"],
                "classification": "CONFIDENTIAL",
            },
            ReportType.ANOMALY_SUMMARY: {
                "title_template": "Anomaly Detection Summary - {period}",
                "sections": ["anomaly_overview", "by_domain", "high_priority",
                            "trends", "recommendations"],
                "classification": "UNCLASSIFIED",
            },
            ReportType.NARRATIVE_ANALYSIS: {
                "title_template": "Narrative Analysis Report - {period}",
                "sections": ["narrative_overview", "disinformation", "campaigns",
                            "sentiment_trends", "recommendations"],
                "classification": "CONFIDENTIAL",
            },
            ReportType.SIMULATION_RESULTS: {
                "title_template": "Simulation Results - {simulation_name}",
                "sections": ["simulation_overview", "agent_summary", "events",
                            "disasters", "outcomes", "lessons_learned"],
                "classification": "UNCLASSIFIED",
            },
            ReportType.EXECUTIVE_BRIEF: {
                "title_template": "Executive Brief - {date}",
                "sections": ["key_findings", "critical_threats", "recommendations"],
                "classification": "TOP SECRET",
            },
        }

    def generate_report(
        self,
        report_type: ReportType,
        format: ReportFormat = ReportFormat.HTML,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        parameters: dict[str, Any] | None = None,
        created_by: str | None = None,
    ) -> Report:
        """Generate a report."""
        params = parameters or {}
        template = self._templates.get(report_type, {})
        
        # Set default period
        if not period_end:
            period_end = utcnow()
        if not period_start:
            period_start = period_end - timedelta(days=1)
        
        # Generate title
        title = template.get("title_template", f"{report_type.value} Report").format(
            date=period_end.strftime("%Y-%m-%d"),
            period=f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}",
            region=params.get("region", "Afghanistan"),
            incident_id=params.get("incident_id", "N/A"),
            simulation_name=params.get("simulation_name", "Unnamed"),
        )
        
        report = Report(
            report_id=uuid4(),
            report_type=report_type,
            title=title,
            classification=template.get("classification", "UNCLASSIFIED"),
            status=ReportStatus.GENERATING,
            format=format,
            created_by=created_by,
            period_start=period_start,
            period_end=period_end,
            metadata=params,
        )
        
        # Generate sections based on report type
        sections = self._generate_sections(report_type, period_start, period_end, params)
        report.sections = sections
        
        # Generate summary
        report.summary = self._generate_summary(report_type, sections)
        
        # Mark as completed
        report.status = ReportStatus.COMPLETED
        report.completed_at = utcnow()
        
        self._reports[report.report_id] = report
        return report

    def _generate_sections(
        self,
        report_type: ReportType,
        period_start: datetime,
        period_end: datetime,
        params: dict[str, Any],
    ) -> list[ReportSection]:
        """Generate report sections based on type."""
        generators = {
            ReportType.DAILY_SITREP: self._generate_sitrep_sections,
            ReportType.THREAT_ASSESSMENT: self._generate_threat_sections,
            ReportType.ANOMALY_SUMMARY: self._generate_anomaly_sections,
            ReportType.NARRATIVE_ANALYSIS: self._generate_narrative_sections,
        }
        
        generator = generators.get(report_type, self._generate_default_sections)
        return generator(period_start, period_end, params)

    def _generate_sitrep_sections(
        self,
        period_start: datetime,
        period_end: datetime,
        params: dict[str, Any],
    ) -> list[ReportSection]:
        """Generate daily SITREP sections."""
        return [
            ReportSection(
                title="Executive Summary",
                content=(
                    "During the reporting period, the overall security situation in Afghanistan "
                    "remained volatile with continued incidents in multiple provinces. "
                    "Key developments include increased activity in border regions and "
                    "ongoing humanitarian operations in central provinces."
                ),
                section_type="summary",
                order=1,
            ),
            ReportSection(
                title="Threat Overview",
                content="Current threat levels by region:",
                section_type="data",
                data={
                    "kabul": {"level": "HIGH", "trend": "stable"},
                    "kandahar": {"level": "CRITICAL", "trend": "increasing"},
                    "herat": {"level": "MEDIUM", "trend": "decreasing"},
                    "nangarhar": {"level": "HIGH", "trend": "increasing"},
                },
                tables=[{
                    "headers": ["Region", "Threat Level", "Trend", "Key Concerns"],
                    "rows": [
                        ["Kabul", "HIGH", "Stable", "Urban security, IEDs"],
                        ["Kandahar", "CRITICAL", "Increasing", "Insurgent activity"],
                        ["Herat", "MEDIUM", "Decreasing", "Border tensions"],
                        ["Nangarhar", "HIGH", "Increasing", "Cross-border movement"],
                    ],
                }],
                order=2,
            ),
            ReportSection(
                title="Incidents",
                content=f"Total incidents reported: 23\nVerified: 18\nUnder investigation: 5",
                section_type="statistics",
                data={
                    "total_incidents": 23,
                    "by_type": {
                        "security": 12,
                        "humanitarian": 6,
                        "infrastructure": 3,
                        "other": 2,
                    },
                },
                order=3,
            ),
            ReportSection(
                title="Entity Activity",
                content="Notable entity movements and activities detected during the period.",
                section_type="analysis",
                data={
                    "new_entities": 15,
                    "updated_entities": 47,
                    "high_threat_entities": 3,
                },
                order=4,
            ),
            ReportSection(
                title="Recommendations",
                content=(
                    "1. Increase surveillance in Kandahar province\n"
                    "2. Monitor border crossing points in Nangarhar\n"
                    "3. Continue coordination with humanitarian partners\n"
                    "4. Review security protocols for Kabul operations"
                ),
                section_type="recommendations",
                order=5,
            ),
        ]

    def _generate_threat_sections(
        self,
        period_start: datetime,
        period_end: datetime,
        params: dict[str, Any],
    ) -> list[ReportSection]:
        """Generate threat assessment sections."""
        return [
            ReportSection(
                title="Threat Summary",
                content=(
                    "This assessment covers identified threats in the operational area. "
                    "Overall threat level: HIGH. Primary concerns include insurgent activity, "
                    "IED threats, and information warfare campaigns."
                ),
                order=1,
            ),
            ReportSection(
                title="Threat Actors",
                content="Identified threat actors and their assessed capabilities:",
                data={
                    "actors": [
                        {"name": "Group A", "capability": "HIGH", "intent": "HIGH"},
                        {"name": "Group B", "capability": "MEDIUM", "intent": "HIGH"},
                    ],
                },
                order=2,
            ),
            ReportSection(
                title="Threat Scores",
                content="Aggregated threat scores for the assessment period:",
                data={
                    "average_score": 67.5,
                    "max_score": 89.2,
                    "critical_count": 5,
                    "high_count": 12,
                },
                order=3,
            ),
        ]

    def _generate_anomaly_sections(
        self,
        period_start: datetime,
        period_end: datetime,
        params: dict[str, Any],
    ) -> list[ReportSection]:
        """Generate anomaly summary sections."""
        return [
            ReportSection(
                title="Anomaly Overview",
                content=(
                    f"Anomaly detection summary for period "
                    f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}."
                ),
                data={
                    "total_anomalies": 45,
                    "critical": 3,
                    "high": 12,
                    "medium": 20,
                    "low": 10,
                },
                order=1,
            ),
            ReportSection(
                title="Anomalies by Domain",
                content="Distribution of anomalies across detection domains:",
                data={
                    "geo_movement": 15,
                    "network_traffic": 12,
                    "social_media": 10,
                    "economic": 8,
                },
                order=2,
            ),
        ]

    def _generate_narrative_sections(
        self,
        period_start: datetime,
        period_end: datetime,
        params: dict[str, Any],
    ) -> list[ReportSection]:
        """Generate narrative analysis sections."""
        return [
            ReportSection(
                title="Narrative Overview",
                content=(
                    "Analysis of information environment during the reporting period. "
                    "Key narratives identified include economic concerns, security messaging, "
                    "and humanitarian appeals."
                ),
                data={
                    "documents_analyzed": 1250,
                    "propaganda_detected": 89,
                    "campaigns_identified": 2,
                },
                order=1,
            ),
            ReportSection(
                title="Disinformation Summary",
                content="Identified disinformation and propaganda activities:",
                data={
                    "disinformation_count": 45,
                    "top_topics": ["economy", "security", "governance"],
                    "source_types": {"social_media": 30, "news": 10, "other": 5},
                },
                order=2,
            ),
        ]

    def _generate_default_sections(
        self,
        period_start: datetime,
        period_end: datetime,
        params: dict[str, Any],
    ) -> list[ReportSection]:
        """Generate default sections for custom reports."""
        return [
            ReportSection(
                title="Report Content",
                content="Custom report content based on provided parameters.",
                data=params,
                order=1,
            ),
        ]

    def _generate_summary(
        self,
        report_type: ReportType,
        sections: list[ReportSection],
    ) -> str:
        """Generate report summary."""
        summaries = {
            ReportType.DAILY_SITREP: (
                "Daily situation report summarizing security incidents, threat levels, "
                "and operational recommendations for the reporting period."
            ),
            ReportType.THREAT_ASSESSMENT: (
                "Comprehensive threat assessment identifying key threat actors, "
                "capabilities, and recommended mitigation measures."
            ),
            ReportType.ANOMALY_SUMMARY: (
                "Summary of detected anomalies across all monitoring domains "
                "with prioritization and trend analysis."
            ),
            ReportType.NARRATIVE_ANALYSIS: (
                "Analysis of information environment including propaganda detection, "
                "campaign identification, and sentiment trends."
            ),
        }
        return summaries.get(report_type, "Report generated successfully.")

    def render_report(self, report: Report) -> str:
        """Render report to specified format."""
        if report.format == ReportFormat.MARKDOWN:
            return self._render_markdown(report)
        elif report.format == ReportFormat.HTML:
            return self._render_html(report)
        elif report.format == ReportFormat.JSON:
            return self._render_json(report)
        else:
            return self._render_markdown(report)

    def _render_markdown(self, report: Report) -> str:
        """Render report as Markdown."""
        lines = [
            f"# {report.title}",
            "",
            f"**Classification:** {report.classification}",
            f"**Generated:** {report.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Report ID:** {report.report_id}",
            "",
            "---",
            "",
            "## Summary",
            "",
            report.summary,
            "",
        ]
        
        for section in sorted(report.sections, key=lambda s: s.order):
            lines.extend([
                f"## {section.title}",
                "",
                section.content,
                "",
            ])
            
            if section.tables:
                for table in section.tables:
                    headers = table.get("headers", [])
                    rows = table.get("rows", [])
                    if headers:
                        lines.append("| " + " | ".join(headers) + " |")
                        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                        for row in rows:
                            lines.append("| " + " | ".join(str(c) for c in row) + " |")
                        lines.append("")
        
        lines.extend([
            "---",
            "",
            f"*Report generated by ISR Platform*",
        ])
        
        return "\n".join(lines)

    def _render_html(self, report: Report) -> str:
        """Render report as HTML."""
        sections_html = ""
        for section in sorted(report.sections, key=lambda s: s.order):
            sections_html += f"<section><h2>{section.title}</h2><p>{section.content}</p></section>"
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{report.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; }}
        .classification {{ color: red; font-weight: bold; }}
        section {{ margin: 20px 0; }}
        h2 {{ color: #333; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report.title}</h1>
        <p class="classification">Classification: {report.classification}</p>
        <p>Generated: {report.created_at.strftime('%Y-%m-%d %H:%M UTC')}</p>
    </div>
    <section class="summary">
        <h2>Summary</h2>
        <p>{report.summary}</p>
    </section>
    {sections_html}
    <footer>
        <p><em>Report generated by ISR Platform</em></p>
    </footer>
</body>
</html>"""

    def _render_json(self, report: Report) -> str:
        """Render report as JSON."""
        import json
        return json.dumps({
            "report_id": str(report.report_id),
            "report_type": report.report_type.value,
            "title": report.title,
            "classification": report.classification,
            "status": report.status.value,
            "created_at": report.created_at.isoformat(),
            "summary": report.summary,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "data": s.data,
                }
                for s in report.sections
            ],
        }, indent=2)

    def get_report(self, report_id: UUID) -> Report | None:
        """Get report by ID."""
        return self._reports.get(report_id)

    def list_reports(
        self,
        report_type: ReportType | None = None,
        limit: int = 50,
    ) -> list[Report]:
        """List reports."""
        reports = list(self._reports.values())
        if report_type:
            reports = [r for r in reports if r.report_type == report_type]
        return sorted(reports, key=lambda r: r.created_at, reverse=True)[:limit]


# Global instance
_report_service: ReportGeneratorService | None = None


def get_report_service() -> ReportGeneratorService:
    """Get the report generator service instance."""
    global _report_service
    if _report_service is None:
        _report_service = ReportGeneratorService()
    return _report_service
