"""Comprehensive error handling for ISR Platform."""

import logging
import traceback
from typing import Any
from datetime import datetime, UTC

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class ISRException(Exception):
    """Base exception for ISR Platform."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(ISRException):
    """Database operation error."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class AuthenticationError(ISRException):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationError(ISRException):
    """Authorization error."""
    
    def __init__(self, message: str = "Insufficient permissions", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ResourceNotFoundError(ISRException):
    """Resource not found error."""
    
    def __init__(self, resource: str, resource_id: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ExternalAPIError(ISRException):
    """External API call error."""
    
    def __init__(self, service: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=f"{service} API error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


class ValidationError(ISRException):
    """Data validation error."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class RateLimitError(ISRException):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


async def isr_exception_handler(request: Request, exc: ISRException) -> JSONResponse:
    """Handle ISR custom exceptions."""
    logger.error(
        f"ISR Exception: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "details": exc.details,
        },
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now(UTC).isoformat(),
            "path": str(request.url.path),
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={"path": request.url.path, "method": request.method},
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "timestamp": datetime.now(UTC).isoformat(),
            "path": str(request.url.path),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(
        f"Validation Error: {exc.errors()}",
        extra={"path": request.url.path, "method": request.method},
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors(),
            "timestamp": datetime.now(UTC).isoformat(),
            "path": str(request.url.path),
        },
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database errors."""
    logger.error(
        f"Database Error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "DatabaseError",
            "message": "Database operation failed",
            "timestamp": datetime.now(UTC).isoformat(),
            "path": str(request.url.path),
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    logger.critical(
        f"Unhandled Exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now(UTC).isoformat(),
            "path": str(request.url.path),
        },
    )


def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(ISRException, isr_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered")


class ErrorLogger:
    """Centralized error logging."""
    
    @staticmethod
    def log_error(
        error: Exception,
        context: dict[str, Any] | None = None,
        severity: str = "ERROR",
    ):
        """Log error with context.
        
        Args:
            error: Exception that occurred
            context: Additional context information
            severity: Log severity level
        """
        context = context or {}
        
        log_data = {
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "timestamp": datetime.now(UTC).isoformat(),
            "traceback": traceback.format_exc(),
            **context,
        }
        
        if severity == "CRITICAL":
            logger.critical(f"Critical Error: {error}", extra=log_data)
        elif severity == "ERROR":
            logger.error(f"Error: {error}", extra=log_data)
        elif severity == "WARNING":
            logger.warning(f"Warning: {error}", extra=log_data)
        else:
            logger.info(f"Info: {error}", extra=log_data)


def safe_execute(func, fallback=None, log_errors=True):
    """Decorator for safe execution with error handling.
    
    Args:
        func: Function to wrap
        fallback: Fallback value if error occurs
        log_errors: Whether to log errors
    
    Returns:
        Wrapped function
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if log_errors:
                ErrorLogger.log_error(
                    e,
                    context={
                        "function": func.__name__,
                        "args": str(args)[:100],
                    },
                )
            return fallback
    
    return wrapper
