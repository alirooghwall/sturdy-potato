"""Tests for report generation service."""

import pytest
from datetime import UTC, datetime, timedelta

from src.services.report_generator import (
    ReportFormat,
    ReportGeneratorService,
    ReportStatus,
    ReportType,
)


@pytest.fixture
def service():
    """Create report generator service instance."""
    return ReportGeneratorService()


class TestReportGeneratorService:
    """Tests for ReportGeneratorService."""

    def test_generate_daily_sitrep(self, service):
        """Test generating a daily SITREP."""
        report = service.generate_report(
            report_type=ReportType.DAILY_SITREP,
            format=ReportFormat.HTML,
        )

        assert report is not None
        assert report.report_type == ReportType.DAILY_SITREP
        assert report.status == ReportStatus.COMPLETED
        assert len(report.sections) > 0
        assert report.summary != ""

    def test_generate_threat_assessment(self, service):
        """Test generating a threat assessment."""
        report = service.generate_report(
            report_type=ReportType.THREAT_ASSESSMENT,
            parameters={"region": "Kandahar"},
        )

        assert report is not None
        assert report.report_type == ReportType.THREAT_ASSESSMENT
        assert "Kandahar" in report.title

    def test_generate_anomaly_summary(self, service):
        """Test generating an anomaly summary."""
        report = service.generate_report(
            report_type=ReportType.ANOMALY_SUMMARY,
        )

        assert report is not None
        assert report.report_type == ReportType.ANOMALY_SUMMARY
        assert any("Anomaly" in s.title for s in report.sections)

    def test_generate_narrative_analysis(self, service):
        """Test generating a narrative analysis report."""
        report = service.generate_report(
            report_type=ReportType.NARRATIVE_ANALYSIS,
        )

        assert report is not None
        assert report.report_type == ReportType.NARRATIVE_ANALYSIS

    def test_report_with_custom_period(self, service):
        """Test generating report with custom time period."""
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=7)

        report = service.generate_report(
            report_type=ReportType.DAILY_SITREP,
            period_start=start_time,
            period_end=end_time,
        )

        assert report.period_start == start_time
        assert report.period_end == end_time

    def test_render_markdown(self, service):
        """Test rendering report as Markdown."""
        report = service.generate_report(
            report_type=ReportType.DAILY_SITREP,
            format=ReportFormat.MARKDOWN,
        )

        content = service.render_report(report)

        assert content.startswith("# ")
        assert "## Summary" in content
        assert report.title in content

    def test_render_html(self, service):
        """Test rendering report as HTML."""
        report = service.generate_report(
            report_type=ReportType.DAILY_SITREP,
            format=ReportFormat.HTML,
        )

        content = service.render_report(report)

        assert "<!DOCTYPE html>" in content
        assert "<html>" in content
        assert report.title in content

    def test_render_json(self, service):
        """Test rendering report as JSON."""
        import json

        report = service.generate_report(
            report_type=ReportType.DAILY_SITREP,
            format=ReportFormat.JSON,
        )

        content = service.render_report(report)
        data = json.loads(content)

        assert data["report_id"] == str(report.report_id)
        assert data["report_type"] == "DAILY_SITREP"
        assert "sections" in data

    def test_list_reports(self, service):
        """Test listing generated reports."""
        # Generate a few reports
        service.generate_report(ReportType.DAILY_SITREP)
        service.generate_report(ReportType.THREAT_ASSESSMENT)

        reports = service.list_reports()

        assert len(reports) >= 2

    def test_list_reports_by_type(self, service):
        """Test listing reports filtered by type."""
        service.generate_report(ReportType.DAILY_SITREP)
        service.generate_report(ReportType.THREAT_ASSESSMENT)

        reports = service.list_reports(report_type=ReportType.DAILY_SITREP)

        assert all(r.report_type == ReportType.DAILY_SITREP for r in reports)

    def test_get_report_by_id(self, service):
        """Test getting report by ID."""
        report = service.generate_report(ReportType.DAILY_SITREP)

        retrieved = service.get_report(report.report_id)

        assert retrieved is not None
        assert retrieved.report_id == report.report_id

    def test_report_classification(self, service):
        """Test that reports have appropriate classification."""
        sitrep = service.generate_report(ReportType.DAILY_SITREP)
        threat = service.generate_report(ReportType.THREAT_ASSESSMENT)
        executive = service.generate_report(ReportType.EXECUTIVE_BRIEF)

        assert sitrep.classification == "CONFIDENTIAL"
        assert threat.classification == "SECRET"
        assert executive.classification == "TOP SECRET"

    def test_report_sections_ordered(self, service):
        """Test that report sections are properly ordered."""
        report = service.generate_report(ReportType.DAILY_SITREP)

        orders = [s.order for s in report.sections]
        assert orders == sorted(orders)


class TestReportFormats:
    """Tests for different report formats."""

    def test_all_formats_generate(self, service):
        """Test that all formats can be generated."""
        for fmt in ReportFormat:
            report = service.generate_report(
                report_type=ReportType.DAILY_SITREP,
                format=fmt,
            )
            content = service.render_report(report)
            assert content is not None
            assert len(content) > 0
