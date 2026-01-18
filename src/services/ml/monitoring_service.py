"""ML performance monitoring and metrics tracking.

Tracks model usage, performance, and accuracy metrics.
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


@dataclass
class ModelMetrics:
    """Metrics for a single model."""
    model_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    last_used: Optional[datetime] = None
    
    @property
    def avg_time_ms(self) -> float:
        """Average execution time."""
        if self.total_calls == 0:
            return 0.0
        return self.total_time_ms / self.total_calls
    
    @property
    def success_rate(self) -> float:
        """Success rate percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_name": self.model_name,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": round(self.success_rate, 2),
            "avg_time_ms": round(self.avg_time_ms, 2),
            "min_time_ms": round(self.min_time_ms, 2) if self.min_time_ms != float('inf') else 0.0,
            "max_time_ms": round(self.max_time_ms, 2),
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }


@dataclass
class ServiceMetrics:
    """Metrics for an ML service."""
    service_name: str
    requests_total: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    avg_processing_time_ms: float = 0.0
    requests_by_hour: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "service_name": self.service_name,
            "requests_total": self.requests_total,
            "requests_successful": self.requests_successful,
            "requests_failed": self.requests_failed,
            "success_rate": (
                (self.requests_successful / self.requests_total * 100)
                if self.requests_total > 0 else 0.0
            ),
            "avg_processing_time_ms": round(self.avg_processing_time_ms, 2),
            "recent_errors": self.errors[-10:],  # Last 10 errors
        }


class MLMonitoringService:
    """ML performance monitoring and metrics tracking.
    
    Features:
    - Model usage tracking
    - Performance metrics
    - Error tracking
    - Request rate monitoring
    - Memory usage tracking
    """

    def __init__(self):
        """Initialize monitoring service."""
        self._model_metrics: Dict[str, ModelMetrics] = {}
        self._service_metrics: Dict[str, ServiceMetrics] = {}
        self._start_time = utcnow()
        self._request_history: List[Dict[str, Any]] = []
        self._max_history = 1000
        
        logger.info("ML monitoring service initialized")
    
    def track_model_call(
        self,
        model_name: str,
        execution_time_ms: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Track a model call.
        
        Args:
            model_name: Name of the model
            execution_time_ms: Execution time in milliseconds
            success: Whether the call was successful
            error: Error message if failed
        """
        if model_name not in self._model_metrics:
            self._model_metrics[model_name] = ModelMetrics(model_name=model_name)
        
        metrics = self._model_metrics[model_name]
        metrics.total_calls += 1
        metrics.last_used = utcnow()
        
        if success:
            metrics.successful_calls += 1
            metrics.total_time_ms += execution_time_ms
            metrics.min_time_ms = min(metrics.min_time_ms, execution_time_ms)
            metrics.max_time_ms = max(metrics.max_time_ms, execution_time_ms)
        else:
            metrics.failed_calls += 1
            if error:
                logger.warning(f"Model {model_name} failed: {error}")
    
    def track_service_request(
        self,
        service_name: str,
        processing_time_ms: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Track a service request.
        
        Args:
            service_name: Name of the service
            processing_time_ms: Processing time in milliseconds
            success: Whether the request was successful
            error: Error message if failed
        """
        if service_name not in self._service_metrics:
            self._service_metrics[service_name] = ServiceMetrics(service_name=service_name)
        
        metrics = self._service_metrics[service_name]
        metrics.requests_total += 1
        
        if success:
            metrics.requests_successful += 1
        else:
            metrics.requests_failed += 1
            if error:
                metrics.errors.append(f"{utcnow().isoformat()}: {error}")
                # Keep only last 50 errors
                if len(metrics.errors) > 50:
                    metrics.errors = metrics.errors[-50:]
        
        # Update average processing time
        if metrics.requests_total == 1:
            metrics.avg_processing_time_ms = processing_time_ms
        else:
            # Running average
            metrics.avg_processing_time_ms = (
                (metrics.avg_processing_time_ms * (metrics.requests_total - 1) + processing_time_ms)
                / metrics.requests_total
            )
        
        # Track by hour
        hour_key = utcnow().strftime("%Y-%m-%d %H:00")
        metrics.requests_by_hour[hour_key] += 1
        
        # Add to request history
        self._request_history.append({
            "service": service_name,
            "timestamp": utcnow().isoformat(),
            "processing_time_ms": processing_time_ms,
            "success": success,
        })
        
        # Limit history size
        if len(self._request_history) > self._max_history:
            self._request_history = self._request_history[-self._max_history:]
    
    def get_model_metrics(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific model or all models.
        
        Args:
            model_name: Optional model name. If None, returns all models.
        
        Returns:
            Dictionary with model metrics
        """
        if model_name:
            metrics = self._model_metrics.get(model_name)
            if metrics:
                return metrics.to_dict()
            return {}
        
        return {
            name: metrics.to_dict()
            for name, metrics in self._model_metrics.items()
        }
    
    def get_service_metrics(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific service or all services.
        
        Args:
            service_name: Optional service name. If None, returns all services.
        
        Returns:
            Dictionary with service metrics
        """
        if service_name:
            metrics = self._service_metrics.get(service_name)
            if metrics:
                return metrics.to_dict()
            return {}
        
        return {
            name: metrics.to_dict()
            for name, metrics in self._service_metrics.items()
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics.
        
        Returns:
            Dictionary with system-wide metrics
        """
        from src.services.ml import get_model_manager
        
        model_manager = get_model_manager()
        memory_usage = model_manager.get_memory_usage()
        
        total_requests = sum(m.requests_total for m in self._service_metrics.values())
        total_successful = sum(m.requests_successful for m in self._service_metrics.values())
        total_failed = sum(m.requests_failed for m in self._service_metrics.values())
        
        return {
            "uptime_seconds": (utcnow() - self._start_time).total_seconds(),
            "start_time": self._start_time.isoformat(),
            "total_requests": total_requests,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "success_rate": (
                (total_successful / total_requests * 100)
                if total_requests > 0 else 0.0
            ),
            "models_tracked": len(self._model_metrics),
            "services_tracked": len(self._service_metrics),
            "memory_usage": memory_usage,
        }
    
    def get_request_rate(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get request rate for the last N minutes.
        
        Args:
            window_minutes: Time window in minutes
        
        Returns:
            Dictionary with request rate statistics
        """
        from datetime import timedelta
        
        cutoff_time = utcnow() - timedelta(minutes=window_minutes)
        
        recent_requests = [
            r for r in self._request_history
            if datetime.fromisoformat(r["timestamp"]) >= cutoff_time
        ]
        
        if not recent_requests:
            return {
                "window_minutes": window_minutes,
                "total_requests": 0,
                "requests_per_minute": 0.0,
                "avg_processing_time_ms": 0.0,
            }
        
        total = len(recent_requests)
        successful = sum(1 for r in recent_requests if r["success"])
        avg_time = sum(r["processing_time_ms"] for r in recent_requests) / total
        
        return {
            "window_minutes": window_minutes,
            "total_requests": total,
            "successful_requests": successful,
            "failed_requests": total - successful,
            "requests_per_minute": total / window_minutes,
            "avg_processing_time_ms": round(avg_time, 2),
        }
    
    def get_top_models(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top N most used models.
        
        Args:
            top_n: Number of top models to return
        
        Returns:
            List of top models with metrics
        """
        models = sorted(
            self._model_metrics.values(),
            key=lambda m: m.total_calls,
            reverse=True
        )
        
        return [m.to_dict() for m in models[:top_n]]
    
    def get_slow_requests(
        self,
        threshold_ms: float = 1000,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get slowest recent requests.
        
        Args:
            threshold_ms: Minimum processing time threshold
            limit: Maximum number of results
        
        Returns:
            List of slow requests
        """
        slow_requests = [
            r for r in self._request_history
            if r["processing_time_ms"] >= threshold_ms
        ]
        
        # Sort by processing time (descending)
        slow_requests.sort(key=lambda r: r["processing_time_ms"], reverse=True)
        
        return slow_requests[:limit]
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._model_metrics.clear()
        self._service_metrics.clear()
        self._request_history.clear()
        self._start_time = utcnow()
        logger.info("ML monitoring metrics reset")
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for persistence or analysis.
        
        Returns:
            Complete metrics dump
        """
        return {
            "system": self.get_system_metrics(),
            "models": self.get_model_metrics(),
            "services": self.get_service_metrics(),
            "request_rate_1h": self.get_request_rate(60),
            "top_models": self.get_top_models(10),
            "export_time": utcnow().isoformat(),
        }


# Global instance
_monitoring_service: Optional[MLMonitoringService] = None


def get_monitoring_service() -> MLMonitoringService:
    """Get the global monitoring service instance."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MLMonitoringService()
    return _monitoring_service


# Decorator for tracking ML operations
def track_ml_operation(service_name: str, model_name: Optional[str] = None):
    """Decorator to track ML operation metrics.
    
    Args:
        service_name: Name of the service
        model_name: Optional model name
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            monitoring = get_monitoring_service()
            start_time = time.time()
            error = None
            success = False
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                
                if model_name:
                    monitoring.track_model_call(model_name, elapsed_ms, success, error)
                
                monitoring.track_service_request(service_name, elapsed_ms, success, error)
        
        def sync_wrapper(*args, **kwargs):
            monitoring = get_monitoring_service()
            start_time = time.time()
            error = None
            success = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                elapsed_ms = (time.time() - start_time) * 1000
                
                if model_name:
                    monitoring.track_model_call(model_name, elapsed_ms, success, error)
                
                monitoring.track_service_request(service_name, elapsed_ms, success, error)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
