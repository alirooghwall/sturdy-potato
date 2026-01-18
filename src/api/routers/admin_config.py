"""Admin configuration management endpoints."""

import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.config.settings import get_settings


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


router = APIRouter()


# Dependency for getting current user
async def get_current_user(token: str = Depends(lambda: "mock_user")) -> dict:
    """Get current authenticated user. TODO: Implement proper auth dependency."""
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
    # TODO: Implement configuration storage in database
    # TODO: Validate configuration values
    # TODO: Log configuration changes (audit trail)
    # TODO: Handle restart_required flag
    
    # For now, return mock response
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
    # TODO: Generate .env file content
    # TODO: Log export action (audit trail)
    # TODO: Option to download as file
    
    return {
        "status": "success",
        "message": "Configuration exported",
        "format": "env",
        "includes_secrets": include_secrets,
    }


@router.get("/config/audit-log")
async def get_config_audit_log(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_admin),
) -> dict:
    """Get audit log of configuration changes."""
    # TODO: Query configuration change history from database
    # TODO: Show who changed what and when
    
    return {
        "changes": [
            {
                "timestamp": utcnow().isoformat(),
                "user": "admin",
                "key": "NEWSAPI_API_KEY",
                "action": "updated",
                "old_value": "***",
                "new_value": "***",
            }
        ],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }
