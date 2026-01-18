"""ML Models API endpoints."""

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from src.services.ml_models import (
    ModelStatus,
    ModelType,
    get_ml_service,
)

from .auth import require_permission


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


router = APIRouter()


# Request/Response schemas
class TextClassificationRequest(BaseModel):
    """Request for text classification."""
    text: str = Field(min_length=1, max_length=50000)
    model_id: str = "xlm-roberta-dari"
    language: str | None = None


class EntityExtractionRequest(BaseModel):
    """Request for entity extraction."""
    text: str = Field(min_length=1, max_length=50000)
    model_id: str = "xlm-roberta-ner"
    language: str | None = None


class TimeSeriesForecastRequest(BaseModel):
    """Request for time series forecasting."""
    metric_name: str
    historical_data: list[dict[str, Any]]
    horizon_hours: int = Field(default=168, ge=1, le=720)
    model_id: str = "lstm-displacement"


class ExplainPredictionRequest(BaseModel):
    """Request to explain a prediction."""
    prediction_id: UUID
    model_id: str
    method: str = "SHAP"
    input_data: dict[str, Any] | None = None


class ModelInfoResponse(BaseModel):
    """Response for model information."""
    model_id: str
    model_type: str
    version: str
    status: str
    description: str
    performance_metrics: dict[str, float]


@router.get("/models", response_model=list[ModelInfoResponse])
async def list_models(
    user: Annotated[dict, Depends(require_permission("ml:read"))],
    model_type: ModelType | None = None,
    status_filter: ModelStatus | None = Query(default=None, alias="status"),
) -> list[ModelInfoResponse]:
    """List available ML models."""
    service = get_ml_service()
    models = service.list_models(model_type=model_type, status=status_filter)

    return [
        ModelInfoResponse(
            model_id=m.model_id,
            model_type=m.model_type.value,
            version=m.version,
            status=m.status.value,
            description=m.description,
            performance_metrics=m.performance_metrics,
        )
        for m in models
    ]


@router.get("/models/{model_id}", response_model=ModelInfoResponse)
async def get_model(
    model_id: str,
    user: Annotated[dict, Depends(require_permission("ml:read"))],
) -> ModelInfoResponse:
    """Get model information by ID."""
    service = get_ml_service()
    model = service.get_model_info(model_id)

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found",
        )

    return ModelInfoResponse(
        model_id=model.model_id,
        model_type=model.model_type.value,
        version=model.version,
        status=model.status.value,
        description=model.description,
        performance_metrics=model.performance_metrics,
    )


@router.get("/health")
async def get_models_health(
    user: Annotated[dict, Depends(require_permission("ml:read"))],
) -> dict[str, Any]:
    """Get health status of all ML models."""
    service = get_ml_service()
    return service.get_model_health()


@router.post("/detect/objects")
async def detect_objects(
    user: Annotated[dict, Depends(require_permission("ml:read"))],
    file: UploadFile = File(...),
    model_id: str = Query(default="yolov8-military"),
    confidence_threshold: float = Query(default=0.5, ge=0.0, le=1.0),
) -> dict[str, Any]:
    """Run object detection on an image."""
    service = get_ml_service()

    # Read image data
    image_data = await file.read()

    result = service.detect_objects(
        image_data=image_data,
        model_id=model_id,
        confidence_threshold=confidence_threshold,
        metadata={"filename": file.filename, "content_type": file.content_type},
    )

    return {
        "detection_id": str(result.detection_id),
        "image_id": result.image_id,
        "model_id": result.model_id,
        "detection_count": len(result.detections),
        "detections": [
            {
                "label": d.label,
                "confidence": d.confidence,
                "bbox": {
                    "x_min": d.x_min,
                    "y_min": d.y_min,
                    "x_max": d.x_max,
                    "y_max": d.y_max,
                },
            }
            for d in result.detections
        ],
        "inference_time_ms": result.inference_time_ms,
        "timestamp": result.timestamp.isoformat(),
    }


@router.post("/classify/text")
async def classify_text(
    request: TextClassificationRequest,
    user: Annotated[dict, Depends(require_permission("ml:read"))],
) -> dict[str, Any]:
    """Classify text using NLP model."""
    service = get_ml_service()

    result = service.classify_text(
        text=request.text,
        model_id=request.model_id,
        language=request.language,
    )

    return result


@router.post("/extract/entities")
async def extract_entities(
    request: EntityExtractionRequest,
    user: Annotated[dict, Depends(require_permission("ml:read"))],
) -> dict[str, Any]:
    """Extract named entities from text."""
    service = get_ml_service()

    result = service.extract_entities(
        text=request.text,
        model_id=request.model_id,
        language=request.language,
    )

    return result


@router.post("/forecast")
async def forecast_time_series(
    request: TimeSeriesForecastRequest,
    user: Annotated[dict, Depends(require_permission("ml:read"))],
) -> dict[str, Any]:
    """Generate time series forecast."""
    service = get_ml_service()

    result = service.forecast_time_series(
        metric_name=request.metric_name,
        historical_data=request.historical_data,
        horizon_hours=request.horizon_hours,
        model_id=request.model_id,
    )

    return {
        "forecast_id": str(result.forecast_id),
        "metric_name": result.metric_name,
        "model_id": result.model_id,
        "horizon_hours": result.horizon_hours,
        "predictions": result.predictions[:24],  # Return first 24 hours
        "prediction_count": len(result.predictions),
        "confidence_intervals": result.confidence_intervals,
        "feature_importance": result.feature_importance,
        "timestamp": result.timestamp.isoformat(),
    }


@router.post("/explain")
async def explain_prediction(
    request: ExplainPredictionRequest,
    user: Annotated[dict, Depends(require_permission("ml:read"))],
) -> dict[str, Any]:
    """Get explanation for a model prediction."""
    service = get_ml_service()

    result = service.explain_prediction(
        prediction_id=request.prediction_id,
        model_id=request.model_id,
        method=request.method,
        input_data=request.input_data,
    )

    return {
        "explanation_id": str(result.explanation_id),
        "prediction_id": str(result.prediction_id),
        "model_id": result.model_id,
        "method": result.method,
        "feature_attributions": result.feature_attributions,
        "top_features": result.top_features,
        "natural_language_explanation": result.natural_language_explanation,
        "timestamp": result.timestamp.isoformat(),
    }
