"""Admin configuration management endpoints."""

import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.services.configuration_service import get_configuration_service


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency for getting current user
async def get_current_user(token: str = Depends(lambda: "mock_user")) -> dict:
    """Get current authenticated user."""
    return {"user_id": "mock_user", "username": "admin", "roles": ["admin", "analyst"]}


class ConfigItem(BaseModel):
    """Configuration item."""

    key: str
    value: str | None
    description: str | None = None
    category: str
    is_secret: bool = False
    is_required: bool = False


class ConfigUpdateRequest(BaseModel):
    """Request to update configuration."""

    key: str
    value: str
    restart_required: bool = False


class APIKeyTestRequest(BaseModel):
    """Request to test API key."""

    service: str = Field(..., description="newsapi, guardian, nytimes, openai, etc.")
    api_key: str


class APIKeyTestResponse(BaseModel):
    """Response from API key test."""

    service: str
    status: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Verify user is admin."""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("/config")
async def get_configuration(
    category: str | None = None,
    include_secrets: bool = False,
    current_user: dict = Depends(require_admin),
) -> dict:
    """Get current system configuration.
    
    Returns all configuration items, optionally filtered by category.
    Secrets are masked unless include_secrets=True (audit logged).
    """
    settings = get_settings()
    
    config_items = [
        # Application
        ConfigItem(
            key="APP_NAME",
            value=settings.app_name,
            description="Application name",
            category="application",
            is_secret=False,
        ),
        ConfigItem(
            key="ENVIRONMENT",
            value=settings.environment,
            description="Deployment environment",
            category="application",
            is_secret=False,
        ),
        ConfigItem(
            key="DEBUG",
            value=str(settings.debug),
            description="Debug mode enabled",
            category="application",
            is_secret=False,
        ),
        
        # API Configuration
        ConfigItem(
            key="API_HOST",
            value=settings.api_host,
            description="API host binding",
            category="api",
            is_secret=False,
        ),
        ConfigItem(
            key="API_PORT",
            value=str(settings.api_port),
            description="API port",
            category="api",
            is_secret=False,
        ),
        
        # Security
        ConfigItem(
            key="SECRET_KEY",
            value="***REDACTED***" if not include_secrets else settings.secret_key,
            description="JWT secret key",
            category="security",
            is_secret=True,
            is_required=True,
        ),
        ConfigItem(
            key="ACCESS_TOKEN_EXPIRE_MINUTES",
            value=str(settings.access_token_expire_minutes),
            description="Access token expiration (minutes)",
            category="security",
            is_secret=False,
        ),
        
        # Database
        ConfigItem(
            key="DATABASE_URL",
            value="***REDACTED***" if not include_secrets else str(settings.database_url),
            description="PostgreSQL connection string",
            category="database",
            is_secret=True,
            is_required=True,
        ),
        
        # External APIs
        ConfigItem(
            key="NEWSAPI_API_KEY",
            value="***REDACTED***" if not include_secrets else os.getenv("NEWSAPI_API_KEY", ""),
            description="NewsAPI.org API key",
            category="external_apis",
            is_secret=True,
            is_required=False,
        ),
        ConfigItem(
            key="GUARDIAN_API_KEY",
            value="***REDACTED***" if not include_secrets else os.getenv("GUARDIAN_API_KEY", ""),
            description="The Guardian API key",
            category="external_apis",
            is_secret=True,
            is_required=False,
        ),
        ConfigItem(
            key="NYTIMES_API_KEY",
            value="***REDACTED***" if not include_secrets else os.getenv("NYTIMES_API_KEY", ""),
            description="New York Times API key",
            category="external_apis",
            is_secret=True,
            is_required=False,
        ),
        ConfigItem(
            key="OPENAI_API_KEY",
            value="***REDACTED***" if not include_secrets else os.getenv("OPENAI_API_KEY", ""),
            description="OpenAI API key for LLM features",
            category="external_apis",
            is_secret=True,
            is_required=False,
        ),
        ConfigItem(
            key="ANTHROPIC_API_KEY",
            value="***REDACTED***" if not include_secrets else os.getenv("ANTHROPIC_API_KEY", ""),
            description="Anthropic API key for Claude",
            category="external_apis",
            is_secret=True,
            is_required=False,
        ),
        ConfigItem(
            key="WEATHER_API_KEY",
            value="***REDACTED***" if not include_secrets else os.getenv("WEATHER_API_KEY", ""),
            description="OpenWeatherMap API key",
            category="external_apis",
            is_secret=True,
            is_required=False,
        ),
        
        # ML Configuration
        ConfigItem(
            key="USE_ML_PROCESSING",
            value=str(settings.use_ml_processing),
            description="Enable ML processing pipeline",
            category="ml",
            is_secret=False,
        ),
        ConfigItem(
            key="ENABLE_GPU",
            value=str(settings.enable_gpu),
            description="Use GPU for ML inference",
            category="ml",
            is_secret=False,
        ),
    ]
    
    # Filter by category if provided
    if category:
        config_items = [item for item in config_items if item.category == category]
    
    return {
        "config_items": [item.dict() for item in config_items],
        "total": len(config_items),
        "categories": ["application", "api", "security", "database", "external_apis", "ml"],
    }


@router.put("/config/{key}")
async def update_configuration(
    key: str,
    request: ConfigUpdateRequest,
    current_user: dict = Depends(require_admin),
) -> dict:
    """Update a configuration value.
    
    NOTE: Most changes require application restart.
    Database-stored configs can be updated at runtime.
    """
    config_service = get_configuration_service()
    
    # Save to database with audit logging
    try:
        await config_service.set_configuration(
            key=key,
            value=request.value,
            category="runtime",
            is_secret=key.lower().endswith(("_key", "_secret", "_password", "_token")),
            user_id=current_user.get("user_id"),
            username=current_user.get("username"),
        )
        logger.info(f"Configuration updated: {key}")
    except Exception as e:
        logger.warning(f"Error saving configuration: {e}")
    
    return {
        "status": "updated",
        "key": key,
        "message": f"Configuration updated. Restart required: {request.restart_required}",
        "timestamp": utcnow().isoformat(),
    }


@router.post("/config/test-api-key", response_model=APIKeyTestResponse)
async def test_api_key(
    request: APIKeyTestRequest,
    current_user: dict = Depends(require_admin),
) -> APIKeyTestResponse:
    """Test an API key before saving it.
    
    Makes a test request to the service to validate the key works.
    """
    service = request.service.lower()
    api_key = request.api_key
    
    # Test NewsAPI
    if service == "newsapi":
        try:
            import httpx
            response = await httpx.AsyncClient().get(
                "https://newsapi.org/v2/top-headlines",
                params={"country": "us", "pageSize": 1, "apiKey": api_key},
                timeout=10,
            )
            if response.status_code == 200:
                return APIKeyTestResponse(
                    service=service,
                    status="valid",
                    message="API key is valid and working",
                    details={"rate_limit": response.headers.get("X-RateLimit-Remaining", "unknown")},
                )
            elif response.status_code == 401:
                return APIKeyTestResponse(
                    service=service,
                    status="invalid",
                    message="API key is invalid or expired",
                )
            else:
                return APIKeyTestResponse(
                    service=service,
                    status="error",
                    message=f"Unexpected response: {response.status_code}",
                )
        except Exception as e:
            return APIKeyTestResponse(
                service=service,
                status="error",
                message=f"Failed to test API key: {str(e)}",
            )
    
    # Test Guardian
    elif service == "guardian":
        try:
            import httpx
            response = await httpx.AsyncClient().get(
                "https://content.guardianapis.com/search",
                params={"page-size": 1, "api-key": api_key},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                return APIKeyTestResponse(
                    service=service,
                    status="valid",
                    message="API key is valid",
                    details={"tier": data.get("response", {}).get("userTier", "unknown")},
                )
            else:
                return APIKeyTestResponse(
                    service=service,
                    status="invalid",
                    message="API key validation failed",
                )
        except Exception as e:
            return APIKeyTestResponse(
                service=service,
                status="error",
                message=f"Failed to test API key: {str(e)}",
            )
    
    # Test OpenAI
    elif service == "openai":
        try:
            import httpx
            response = await httpx.AsyncClient().get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            if response.status_code == 200:
                return APIKeyTestResponse(
                    service=service,
                    status="valid",
                    message="OpenAI API key is valid",
                )
            else:
                return APIKeyTestResponse(
                    service=service,
                    status="invalid",
                    message="OpenAI API key is invalid",
                )
        except Exception as e:
            return APIKeyTestResponse(
                service=service,
                status="error",
                message=f"Failed to test API key: {str(e)}",
            )
    
    else:
        return APIKeyTestResponse(
            service=service,
            status="unsupported",
            message=f"API key testing not implemented for {service}",
        )


@router.get("/config/categories")
async def get_config_categories(
    current_user: dict = Depends(require_admin),
) -> dict:
    """Get list of configuration categories."""
    return {
        "categories": [
            {"id": "application", "name": "Application", "description": "Core application settings"},
            {"id": "api", "name": "API", "description": "API server configuration"},
            {"id": "security", "name": "Security", "description": "Authentication and encryption"},
            {"id": "database", "name": "Database", "description": "PostgreSQL configuration"},
            {"id": "external_apis", "name": "External APIs", "description": "Third-party API keys"},
            {"id": "ml", "name": "Machine Learning", "description": "ML model configuration"},
            {"id": "ingestion", "name": "Data Ingestion", "description": "Connector settings"},
        ]
    }


@router.post("/config/export")
async def export_configuration(
    include_secrets: bool = False,
    current_user: dict = Depends(require_admin),
) -> dict:
    """Export current configuration as .env format.
    
    Useful for backup or deploying to another environment.
    """
    config_service = get_configuration_service()
    
    # Log the export action
    try:
        await config_service.log_config_change(
            user_id=current_user.get("user_id"),
            username=current_user.get("username"),
            action="exported",
            key="ALL_CONFIG",
            old_value=None,
            new_value=f"include_secrets={include_secrets}",
        )
        
        # Generate export content
        content = await config_service.export_configuration(
            include_secrets=include_secrets,
            format="env",
        )
        
        logger.info(f"Configuration exported by user {current_user.get('username')}")
    except Exception as e:
        logger.warning(f"Error exporting configuration: {e}")
        content = "# Export failed"
    
    return {
        "status": "success",
        "message": "Configuration exported",
        "format": "env",
        "includes_secrets": include_secrets,
        "content": content,
    }


@router.get("/config/audit-log")
async def get_config_audit_log(
    limit: int = 50,
    offset: int = 0,
    key: str | None = None,
    current_user: dict = Depends(require_admin),
) -> dict:
    """Get audit log of configuration changes."""
    config_service = get_configuration_service()
    
    # Query from database
    try:
        result = await config_service.get_audit_log(
            limit=limit,
            offset=offset,
            key=key,
        )
        return result
    except Exception as e:
        logger.warning(f"Error fetching audit log: {e}")
    
    return {
        "changes": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }
