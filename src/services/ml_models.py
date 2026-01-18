"""ML Model Integration Layer for ISR Platform.

Provides unified interface for ML model inference including
visual detection, NLP, time-series forecasting, and explainability.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class ModelType(str, Enum):
    """Types of ML models."""
    VISUAL_DETECTION = "VISUAL_DETECTION"
    NLP_CLASSIFICATION = "NLP_CLASSIFICATION"
    NLP_NER = "NLP_NER"
    TIME_SERIES = "TIME_SERIES"
    ANOMALY_DETECTION = "ANOMALY_DETECTION"
    GRAPH_ANALYSIS = "GRAPH_ANALYSIS"


class ModelStatus(str, Enum):
    """Model deployment status."""
    LOADING = "LOADING"
    READY = "READY"
    ERROR = "ERROR"
    UPDATING = "UPDATING"


@dataclass
class BoundingBox:
    """Bounding box for visual detection."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class VisualDetectionResult:
    """Result of visual detection model."""
    detection_id: UUID
    image_id: str
    detections: list[BoundingBox] = field(default_factory=list)
    model_id: str = ""
    inference_time_ms: float = 0.0
    image_metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=utcnow)


@dataclass
class TimeSeriesForecast:
    """Time series forecast result."""
    forecast_id: UUID
    metric_name: str
    horizon_hours: int
    predictions: list[dict[str, Any]] = field(default_factory=list)
    confidence_intervals: dict[str, list[float]] = field(default_factory=dict)
    model_id: str = ""
    feature_importance: dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=utcnow)


@dataclass
class ExplainabilityResult:
    """Explainability output for model predictions."""
    explanation_id: UUID
    prediction_id: UUID
    model_id: str
    method: str  # SHAP, LIME, attention, etc.
    feature_attributions: dict[str, float] = field(default_factory=dict)
    top_features: list[dict[str, Any]] = field(default_factory=list)
    visualization_data: dict[str, Any] = field(default_factory=dict)
    natural_language_explanation: str = ""
    timestamp: datetime = field(default_factory=utcnow)


@dataclass
class ModelInfo:
    """Information about a deployed model."""
    model_id: str
    model_type: ModelType
    version: str
    status: ModelStatus
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    performance_metrics: dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=utcnow)


class MLModelService:
    """Service for ML model inference and management."""

    def __init__(self) -> None:
        """Initialize ML model service."""
        self._models: dict[str, ModelInfo] = {}
        self._initialize_models()

    def _initialize_models(self) -> None:
        """Initialize available models."""
        # Visual Detection Models
        self._models["yolov8-military"] = ModelInfo(
            model_id="yolov8-military",
            model_type=ModelType.VISUAL_DETECTION,
            version="1.0.0",
            status=ModelStatus.READY,
            description="YOLOv8 fine-tuned for military vehicle and equipment detection",
            input_schema={"type": "image", "formats": ["jpg", "png", "tiff"]},
            output_schema={"type": "detections", "classes": ["vehicle", "equipment", "personnel", "structure"]},
            performance_metrics={"mAP": 0.82, "inference_ms": 45},
        )

        self._models["resnet-satellite"] = ModelInfo(
            model_id="resnet-satellite",
            model_type=ModelType.VISUAL_DETECTION,
            version="1.0.0",
            status=ModelStatus.READY,
            description="ResNet-50 for satellite imagery classification",
            input_schema={"type": "image", "formats": ["tiff", "jp2"]},
            output_schema={"type": "classification", "classes": ["urban", "rural", "infrastructure", "military", "agricultural"]},
            performance_metrics={"accuracy": 0.89, "inference_ms": 30},
        )

        # NLP Models
        self._models["xlm-roberta-dari"] = ModelInfo(
            model_id="xlm-roberta-dari",
            model_type=ModelType.NLP_CLASSIFICATION,
            version="1.0.0",
            status=ModelStatus.READY,
            description="XLM-RoBERTa fine-tuned for Dari/Pashto text classification",
            input_schema={"type": "text", "languages": ["dari", "pashto", "persian"]},
            output_schema={"type": "classification", "classes": ["news", "propaganda", "opinion", "rumor"]},
            performance_metrics={"f1": 0.78, "inference_ms": 120},
        )

        self._models["xlm-roberta-ner"] = ModelInfo(
            model_id="xlm-roberta-ner",
            model_type=ModelType.NLP_NER,
            version="1.0.0",
            status=ModelStatus.READY,
            description="XLM-RoBERTa for multilingual named entity recognition",
            input_schema={"type": "text", "languages": ["dari", "pashto", "english", "arabic"]},
            output_schema={"type": "entities", "types": ["PERSON", "ORGANIZATION", "LOCATION", "EVENT", "DATE"]},
            performance_metrics={"f1": 0.81, "inference_ms": 85},
        )

        # Time Series Models
        self._models["lstm-displacement"] = ModelInfo(
            model_id="lstm-displacement",
            model_type=ModelType.TIME_SERIES,
            version="1.0.0",
            status=ModelStatus.READY,
            description="LSTM for population displacement forecasting",
            input_schema={"type": "time_series", "features": ["conflict_events", "weather", "economic"]},
            output_schema={"type": "forecast", "horizon": "7_days"},
            performance_metrics={"mae": 0.12, "rmse": 0.18},
        )

        self._models["prophet-threat"] = ModelInfo(
            model_id="prophet-threat",
            model_type=ModelType.TIME_SERIES,
            version="1.0.0",
            status=ModelStatus.READY,
            description="Prophet model for threat level forecasting",
            input_schema={"type": "time_series", "features": ["incidents", "intelligence", "seasonal"]},
            output_schema={"type": "forecast", "horizon": "14_days"},
            performance_metrics={"mape": 0.15},
        )

        # Anomaly Detection Models
        self._models["autoencoder-network"] = ModelInfo(
            model_id="autoencoder-network",
            model_type=ModelType.ANOMALY_DETECTION,
            version="1.0.0",
            status=ModelStatus.READY,
            description="Autoencoder for network traffic anomaly detection",
            input_schema={"type": "tabular", "features": ["bytes_in", "bytes_out", "connections", "ports"]},
            output_schema={"type": "anomaly_score", "threshold": 0.85},
            performance_metrics={"precision": 0.88, "recall": 0.82},
        )

        # Graph Analysis Models
        self._models["gnn-network"] = ModelInfo(
            model_id="gnn-network",
            model_type=ModelType.GRAPH_ANALYSIS,
            version="1.0.0",
            status=ModelStatus.READY,
            description="Graph Neural Network for relationship and pattern analysis",
            input_schema={"type": "graph", "node_features": True, "edge_features": True},
            output_schema={"type": "node_classification", "link_prediction": True},
            performance_metrics={"auc": 0.86},
        )

    def detect_objects(
        self,
        image_data: bytes,
        model_id: str = "yolov8-military",
        confidence_threshold: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> VisualDetectionResult:
        """Run visual object detection on image."""
        import numpy as np

        model = self._models.get(model_id)
        if not model or model.model_type != ModelType.VISUAL_DETECTION:
            raise ValueError(f"Visual detection model {model_id} not found")

        # Simulated detection for demo
        # In production, load actual model and run inference
        detections = []

        # Simulate some detections
        num_detections = np.random.randint(0, 5)
        labels = ["military_vehicle", "civilian_vehicle", "structure", "personnel_group"]

        for _ in range(num_detections):
            x_min = np.random.uniform(0, 0.7)
            y_min = np.random.uniform(0, 0.7)
            detections.append(BoundingBox(
                x_min=x_min,
                y_min=y_min,
                x_max=x_min + np.random.uniform(0.1, 0.3),
                y_max=y_min + np.random.uniform(0.1, 0.3),
                confidence=np.random.uniform(confidence_threshold, 1.0),
                label=np.random.choice(labels),
            ))

        return VisualDetectionResult(
            detection_id=uuid4(),
            image_id=metadata.get("image_id", str(uuid4())) if metadata else str(uuid4()),
            detections=detections,
            model_id=model_id,
            inference_time_ms=np.random.uniform(30, 60),
            image_metadata=metadata or {},
        )

    def classify_text(
        self,
        text: str,
        model_id: str = "xlm-roberta-dari",
        language: str | None = None,
    ) -> dict[str, Any]:
        """Classify text using NLP model."""
        import numpy as np

        model = self._models.get(model_id)
        if not model or model.model_type != ModelType.NLP_CLASSIFICATION:
            raise ValueError(f"NLP classification model {model_id} not found")

        # Simulated classification for demo
        classes = ["news", "propaganda", "opinion", "rumor"]
        probs = np.random.dirichlet(np.ones(len(classes)))

        return {
            "prediction_id": str(uuid4()),
            "model_id": model_id,
            "text_length": len(text),
            "detected_language": language or "dari",
            "classification": classes[np.argmax(probs)],
            "confidence": float(max(probs)),
            "class_probabilities": {c: float(p) for c, p in zip(classes, probs)},
            "inference_time_ms": np.random.uniform(80, 150),
            "timestamp": utcnow().isoformat(),
        }

    def extract_entities(
        self,
        text: str,
        model_id: str = "xlm-roberta-ner",
        language: str | None = None,
    ) -> dict[str, Any]:
        """Extract named entities from text."""
        model = self._models.get(model_id)
        if not model or model.model_type != ModelType.NLP_NER:
            raise ValueError(f"NER model {model_id} not found")

        # Simulated NER for demo
        # In production, run actual model inference
        entities = []

        # Simple pattern matching demo
        location_patterns = ["Kabul", "Kandahar", "Herat", "Nangarhar"]
        org_patterns = ["Taliban", "NATO", "UN", "UNHCR"]

        for loc in location_patterns:
            if loc.lower() in text.lower():
                start = text.lower().find(loc.lower())
                entities.append({
                    "text": loc,
                    "type": "LOCATION",
                    "start": start,
                    "end": start + len(loc),
                    "confidence": 0.9,
                })

        for org in org_patterns:
            if org.lower() in text.lower():
                start = text.lower().find(org.lower())
                entities.append({
                    "text": org,
                    "type": "ORGANIZATION",
                    "start": start,
                    "end": start + len(org),
                    "confidence": 0.88,
                })

        return {
            "prediction_id": str(uuid4()),
            "model_id": model_id,
            "text_length": len(text),
            "detected_language": language or "dari",
            "entities": entities,
            "entity_count": len(entities),
            "timestamp": utcnow().isoformat(),
        }

    def forecast_time_series(
        self,
        metric_name: str,
        historical_data: list[dict[str, Any]],
        horizon_hours: int = 168,
        model_id: str = "lstm-displacement",
    ) -> TimeSeriesForecast:
        """Generate time series forecast."""
        import numpy as np

        model = self._models.get(model_id)
        if not model or model.model_type != ModelType.TIME_SERIES:
            raise ValueError(f"Time series model {model_id} not found")

        # Simulated forecast for demo
        predictions = []
        base_value = historical_data[-1]["value"] if historical_data else 100

        for h in range(horizon_hours):
            # Simple random walk with trend
            trend = 0.01 * h
            noise = np.random.normal(0, base_value * 0.05)
            predicted_value = base_value * (1 + trend) + noise

            predictions.append({
                "hour": h,
                "timestamp": (utcnow().replace(minute=0, second=0, microsecond=0)).isoformat(),
                "value": max(0, predicted_value),
                "lower_bound": max(0, predicted_value * 0.85),
                "upper_bound": predicted_value * 1.15,
            })

        return TimeSeriesForecast(
            forecast_id=uuid4(),
            metric_name=metric_name,
            horizon_hours=horizon_hours,
            predictions=predictions,
            confidence_intervals={"80": [0.9, 1.1], "95": [0.85, 1.15]},
            model_id=model_id,
            feature_importance={
                "historical_trend": 0.35,
                "seasonal": 0.25,
                "conflict_events": 0.2,
                "weather": 0.1,
                "economic": 0.1,
            },
        )

    def explain_prediction(
        self,
        prediction_id: UUID,
        model_id: str,
        method: str = "SHAP",
        input_data: dict[str, Any] | None = None,
    ) -> ExplainabilityResult:
        """Generate explanation for a model prediction."""
        import numpy as np

        # Simulated explainability for demo
        # In production, use actual SHAP/LIME libraries

        feature_names = ["feature_1", "feature_2", "feature_3", "feature_4", "feature_5"]
        attributions = {f: float(np.random.uniform(-1, 1)) for f in feature_names}

        # Sort by absolute value
        sorted_features = sorted(
            attributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        top_features = [
            {
                "feature": f,
                "attribution": a,
                "direction": "positive" if a > 0 else "negative",
                "importance_rank": i + 1,
            }
            for i, (f, a) in enumerate(sorted_features[:3])
        ]

        # Generate natural language explanation
        top_feature = sorted_features[0]
        direction = "increased" if top_feature[1] > 0 else "decreased"
        explanation = (
            f"The prediction was primarily driven by {top_feature[0]}, which {direction} "
            f"the output by {abs(top_feature[1]):.2f}. "
            f"Secondary factors include {sorted_features[1][0]} and {sorted_features[2][0]}."
        )

        return ExplainabilityResult(
            explanation_id=uuid4(),
            prediction_id=prediction_id,
            model_id=model_id,
            method=method,
            feature_attributions=attributions,
            top_features=top_features,
            natural_language_explanation=explanation,
        )

    def get_model_info(self, model_id: str) -> ModelInfo | None:
        """Get information about a model."""
        return self._models.get(model_id)

    def list_models(
        self,
        model_type: ModelType | None = None,
        status: ModelStatus | None = None,
    ) -> list[ModelInfo]:
        """List available models."""
        models = list(self._models.values())

        if model_type:
            models = [m for m in models if m.model_type == model_type]

        if status:
            models = [m for m in models if m.status == status]

        return models

    def get_model_health(self) -> dict[str, Any]:
        """Get health status of all models."""
        status_counts = {}
        for model in self._models.values():
            status_counts[model.status.value] = status_counts.get(model.status.value, 0) + 1

        return {
            "total_models": len(self._models),
            "status_breakdown": status_counts,
            "models": [
                {
                    "model_id": m.model_id,
                    "type": m.model_type.value,
                    "status": m.status.value,
                    "version": m.version,
                }
                for m in self._models.values()
            ],
            "timestamp": utcnow().isoformat(),
        }


# Global instance
_ml_service: MLModelService | None = None


def get_ml_service() -> MLModelService:
    """Get the ML model service instance."""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLModelService()
    return _ml_service
