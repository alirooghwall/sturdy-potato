"""LLM-powered intelligence features API."""

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.services.llm.llm_service import LLMProvider, get_llm_service, set_llm_service, LLMConfig
from src.services.llm.report_generator import get_report_generator
from src.services.llm.conversational_query import get_conversational_query
from src.services.llm.insight_discovery import get_insight_discovery
from src.services.llm.anomaly_explainer import get_anomaly_explainer
from src.services.llm.prediction_service import get_prediction_service

from .auth import require_permission

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class LLMConfigRequest(BaseModel):
    """LLM configuration request."""
    provider: LLMProvider
    api_key: str | None = None
    model: str = "gpt-4"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class QueryRequest(BaseModel):
    """Conversational query request."""
    query: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None
    context_data: dict[str, Any] = Field(default_factory=dict)


class ReportRequest(BaseModel):
    """Report generation request."""
    analysis_data: dict[str, Any]
    analysis_type: str
    include_recommendations: bool = True
    format: str = "markdown"


class InsightRequest(BaseModel):
    """Insight discovery request."""
    satellite_alerts: list[dict[str, Any]] = Field(default_factory=list)
    narratives: list[dict[str, Any]] = Field(default_factory=list)
    social_media_activity: list[dict[str, Any]] = Field(default_factory=list)


class AnomalyExplanationRequest(BaseModel):
    """Anomaly explanation request."""
    anomaly_data: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)


class PredictionRequest(BaseModel):
    """Prediction request."""
    prediction_type: str  # narrative_evolution, event_likelihood, environmental
    data: dict[str, Any]
    time_horizon: int = 48  # hours or months depending on type


class ExecutiveBriefingRequest(BaseModel):
    """Executive briefing request."""
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    key_events: list[dict[str, Any]] = Field(default_factory=list)
    time_period: str = "24h"


# Endpoints

@router.post("/configure")
async def configure_llm(
    config: LLMConfigRequest,
    user: Annotated[dict, Depends(require_permission("admin"))],
) -> dict[str, Any]:
    """Configure LLM provider and settings."""
    llm_config = LLMConfig(
        provider=config.provider,
        api_key=config.api_key,
        model=config.model,
        temperature=config.temperature,
    )
    
    from src.services.llm import LLMService
    llm_service = LLMService(llm_config)
    set_llm_service(llm_service)
    
    return {
        "status": "configured",
        "provider": config.provider.value,
        "model": config.model,
        "temperature": config.temperature,
    }


@router.post("/query")
async def conversational_query(
    request: QueryRequest,
    user: Annotated[dict, Depends(require_permission("llm:read"))],
) -> dict[str, Any]:
    """Query intelligence data using natural language."""
    query_service = get_conversational_query()
    
    try:
        response = await query_service.query(
            user_query=request.query,
            conversation_id=request.conversation_id,
            context_data=request.context_data,
        )
        return response
    
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}",
        )


@router.post("/query/stream")
async def conversational_query_stream(
    request: QueryRequest,
    user: Annotated[dict, Depends(require_permission("llm:read"))],
):
    """Query with streaming response."""
    query_service = get_conversational_query()
    
    async def generate():
        try:
            async for chunk in query_service.query_stream(
                user_query=request.query,
                conversation_id=request.conversation_id,
                context_data=request.context_data,
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Streaming query error: {e}")
            yield f"\n\nError: {str(e)}"
    
    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/report/generate")
async def generate_report(
    request: ReportRequest,
    user: Annotated[dict, Depends(require_permission("llm:write"))],
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Generate intelligence report from analysis data."""
    report_gen = get_report_generator()
    
    try:
        report = await report_gen.generate_satellite_analysis_report(
            analysis_data=request.analysis_data,
            analysis_type=request.analysis_type,
            include_recommendations=request.include_recommendations,
            format=request.format,
        )
        return report
    
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


@router.post("/report/executive-briefing")
async def generate_executive_briefing(
    request: ExecutiveBriefingRequest,
    user: Annotated[dict, Depends(require_permission("llm:write"))],
) -> dict[str, Any]:
    """Generate executive briefing."""
    report_gen = get_report_generator()
    
    try:
        briefing = await report_gen.generate_executive_briefing(
            alerts=request.alerts,
            key_events=request.key_events,
            time_period=request.time_period,
        )
        return briefing
    
    except Exception as e:
        logger.error(f"Briefing generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Briefing generation failed: {str(e)}",
        )


@router.post("/insights/discover")
async def discover_insights(
    request: InsightRequest,
    user: Annotated[dict, Depends(require_permission("llm:read"))],
) -> dict[str, Any]:
    """Discover insights and correlations across data sources."""
    insight_service = get_insight_discovery()
    
    try:
        insights = await insight_service.discover_correlations(
            satellite_alerts=request.satellite_alerts,
            narratives=request.narratives,
            social_media_activity=request.social_media_activity,
        )
        
        return {
            "insights_found": len(insights),
            "insights": [
                {
                    "insight_id": str(i.insight_id),
                    "category": i.category,
                    "title": i.title,
                    "description": i.description,
                    "confidence": i.confidence,
                    "importance": i.importance,
                    "evidence": i.evidence,
                    "recommendations": i.recommendations,
                }
                for i in insights
            ],
        }
    
    except Exception as e:
        logger.error(f"Insight discovery error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insight discovery failed: {str(e)}",
        )


@router.post("/explain/anomaly")
async def explain_anomaly(
    request: AnomalyExplanationRequest,
    user: Annotated[dict, Depends(require_permission("llm:read"))],
) -> dict[str, Any]:
    """Explain detected anomaly."""
    explainer = get_anomaly_explainer()
    
    try:
        explanation = await explainer.explain_anomaly(
            anomaly_data=request.anomaly_data,
            context=request.context,
        )
        return explanation
    
    except Exception as e:
        logger.error(f"Anomaly explanation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation failed: {str(e)}",
        )


@router.post("/predict")
async def make_prediction(
    request: PredictionRequest,
    user: Annotated[dict, Depends(require_permission("llm:read"))],
) -> dict[str, Any]:
    """Generate prediction or forecast."""
    prediction_service = get_prediction_service()
    
    try:
        if request.prediction_type == "narrative_evolution":
            result = await prediction_service.predict_narrative_evolution(
                narrative_data=request.data,
                time_horizon_hours=request.time_horizon,
            )
        
        elif request.prediction_type == "event_likelihood":
            result = await prediction_service.predict_event_likelihood(
                event_type=request.data.get("event_type", ""),
                current_indicators=request.data.get("indicators", {}),
                historical_precedents=request.data.get("precedents", []),
            )
        
        elif request.prediction_type == "environmental":
            result = await prediction_service.forecast_environmental_impact(
                satellite_trend=request.data,
                forecast_months=request.time_horizon,
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid prediction type: {request.prediction_type}",
            )
        
        return result
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


@router.get("/status")
async def get_llm_status(
    user: Annotated[dict, Depends(require_permission("llm:read"))],
) -> dict[str, Any]:
    """Get LLM service status."""
    try:
        llm = get_llm_service()
        
        return {
            "configured": True,
            "provider": llm.config.provider.value,
            "model": llm.default_model,
            "temperature": llm.config.temperature,
            "max_tokens": llm.config.max_tokens,
        }
    
    except Exception as e:
        return {
            "configured": False,
            "error": str(e),
        }
