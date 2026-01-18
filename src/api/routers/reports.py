"""Report generation API endpoints."""

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from src.services.report_generator import (
    ReportFormat,
    ReportStatus,
    ReportType,
    get_report_service,
)

from .auth import require_permission


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


router = APIRouter()


# Request/Response schemas
class GenerateReportRequest(BaseModel):
    """Request to generate a report."""
    report_type: ReportType
    format: ReportFormat = ReportFormat.HTML
    period_start: datetime | None = None
    period_end: datetime | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    """Response for report information."""
    report_id: UUID
    report_type: str
    title: str
    classification: str
    status: str
    format: str
    created_at: str
    completed_at: str | None
    summary: str
    section_count: int


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    request: GenerateReportRequest,
    user: Annotated[dict, Depends(require_permission("report:generate"))],
) -> ReportResponse:
    """Generate a new report."""
    service = get_report_service()

    report = service.generate_report(
        report_type=request.report_type,
        format=request.format,
        period_start=request.period_start,
        period_end=request.period_end,
        parameters=request.parameters,
        created_by=user.get("username"),
    )

    return ReportResponse(
        report_id=report.report_id,
        report_type=report.report_type.value,
        title=report.title,
        classification=report.classification,
        status=report.status.value,
        format=report.format.value,
        created_at=report.created_at.isoformat(),
        completed_at=report.completed_at.isoformat() if report.completed_at else None,
        summary=report.summary,
        section_count=len(report.sections),
    )


@router.get("", response_model=list[ReportResponse])
async def list_reports(
    user: Annotated[dict, Depends(require_permission("report:read"))],
    report_type: ReportType | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ReportResponse]:
    """List generated reports."""
    service = get_report_service()
    reports = service.list_reports(report_type=report_type, limit=limit)

    return [
        ReportResponse(
            report_id=r.report_id,
            report_type=r.report_type.value,
            title=r.title,
            classification=r.classification,
            status=r.status.value,
            format=r.format.value,
            created_at=r.created_at.isoformat(),
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
            summary=r.summary,
            section_count=len(r.sections),
        )
        for r in reports
    ]


@router.get("/types")
async def list_report_types(
    user: Annotated[dict, Depends(require_permission("report:read"))],
) -> dict[str, Any]:
    """List available report types."""
    return {
        "report_types": [
            {
                "type": rt.value,
                "name": rt.value.replace("_", " ").title(),
                "description": {
                    ReportType.DAILY_SITREP: "Daily situation report with incident summary and threat overview",
                    ReportType.THREAT_ASSESSMENT: "Comprehensive threat assessment with actor analysis",
                    ReportType.INCIDENT_REPORT: "Detailed report for a specific incident",
                    ReportType.ANOMALY_SUMMARY: "Summary of detected anomalies across domains",
                    ReportType.NARRATIVE_ANALYSIS: "Analysis of information environment and narratives",
                    ReportType.SIMULATION_RESULTS: "Results and outcomes from simulation runs",
                    ReportType.EXECUTIVE_BRIEF: "High-level executive briefing",
                    ReportType.CUSTOM: "Custom report with specified parameters",
                }.get(rt, ""),
            }
            for rt in ReportType
        ],
        "formats": [f.value for f in ReportFormat],
    }


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    user: Annotated[dict, Depends(require_permission("report:read"))],
) -> ReportResponse:
    """Get report metadata by ID."""
    service = get_report_service()
    report = service.get_report(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    return ReportResponse(
        report_id=report.report_id,
        report_type=report.report_type.value,
        title=report.title,
        classification=report.classification,
        status=report.status.value,
        format=report.format.value,
        created_at=report.created_at.isoformat(),
        completed_at=report.completed_at.isoformat() if report.completed_at else None,
        summary=report.summary,
        section_count=len(report.sections),
    )


@router.get("/{report_id}/content")
async def get_report_content(
    report_id: UUID,
    user: Annotated[dict, Depends(require_permission("report:read"))],
    format_override: ReportFormat | None = Query(default=None, alias="format"),
):
    """Get rendered report content."""
    service = get_report_service()
    report = service.get_report(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not completed (status: {report.status.value})",
        )

    # Use override format if provided
    if format_override:
        report.format = format_override

    content = service.render_report(report)

    if report.format == ReportFormat.HTML:
        return HTMLResponse(content=content)
    elif report.format == ReportFormat.JSON:
        return PlainTextResponse(content=content, media_type="application/json")
    else:
        return PlainTextResponse(content=content, media_type="text/markdown")


@router.get("/{report_id}/sections")
async def get_report_sections(
    report_id: UUID,
    user: Annotated[dict, Depends(require_permission("report:read"))],
) -> dict[str, Any]:
    """Get report sections."""
    service = get_report_service()
    report = service.get_report(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    return {
        "report_id": str(report.report_id),
        "title": report.title,
        "sections": [
            {
                "order": s.order,
                "title": s.title,
                "section_type": s.section_type,
                "content": s.content,
                "data": s.data,
                "tables": s.tables,
                "charts": s.charts,
            }
            for s in sorted(report.sections, key=lambda x: x.order)
        ],
    }


@router.post("/quick/sitrep")
async def generate_quick_sitrep(
    user: Annotated[dict, Depends(require_permission("report:generate"))],
    format: ReportFormat = Query(default=ReportFormat.MARKDOWN),
) -> dict[str, Any]:
    """Generate a quick daily SITREP."""
    service = get_report_service()

    report = service.generate_report(
        report_type=ReportType.DAILY_SITREP,
        format=format,
        created_by=user.get("username"),
    )

    content = service.render_report(report)

    return {
        "report_id": str(report.report_id),
        "title": report.title,
        "classification": report.classification,
        "summary": report.summary,
        "content": content,
        "timestamp": utcnow().isoformat(),
    }


@router.post("/quick/threat-assessment")
async def generate_quick_threat_assessment(
    user: Annotated[dict, Depends(require_permission("report:generate"))],
    region: str = Query(default="Afghanistan"),
    format: ReportFormat = Query(default=ReportFormat.MARKDOWN),
) -> dict[str, Any]:
    """Generate a quick threat assessment."""
    service = get_report_service()

    report = service.generate_report(
        report_type=ReportType.THREAT_ASSESSMENT,
        format=format,
        parameters={"region": region},
        created_by=user.get("username"),
    )

    content = service.render_report(report)

    return {
        "report_id": str(report.report_id),
        "title": report.title,
        "classification": report.classification,
        "summary": report.summary,
        "content": content,
        "timestamp": utcnow().isoformat(),
    }
