"""Authentication endpoints."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.schemas.api import TokenSchema, UserLoginSchema, UserResponseSchema
from src.services.auth import (
    AuthenticationError,
    AuthorizationError,
    get_auth_service,
)

router = APIRouter()
# Use auto_error=False so we can return 401 instead of 403 when the token is missing
security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=TokenSchema)
async def login(credentials: UserLoginSchema) -> TokenSchema:
    """Authenticate user and return access token."""
    auth_service = get_auth_service()

    # In production, validate against database
    # For demo, accept any credentials
    if not credentials.username or not credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Create tokens
    user_id = uuid4()
    roles = ["ANALYST"]  # Default role

    access_token = auth_service.create_access_token(
        user_id=user_id,
        username=credentials.username,
        roles=roles,
    )

    return TokenSchema(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenSchema)
async def refresh_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> TokenSchema:
    """Refresh access token."""
    auth_service = get_auth_service()

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = auth_service.decode_token(credentials.credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # Create new access token
    access_token = auth_service.create_access_token(
        user_id=payload["sub"],
        username=payload.get("username", "unknown"),
        roles=payload.get("roles", []),
    )

    return TokenSchema(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponseSchema)
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> UserResponseSchema:
    """Get current authenticated user."""
    auth_service = get_auth_service()

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = auth_service.validate_access_token(credentials.credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    return UserResponseSchema(
        user_id=payload["sub"],
        username=payload.get("username", "unknown"),
        roles=payload.get("roles", []),
        status="ACTIVE",
        last_login=utcnow(),
    )


async def get_current_user_payload(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """Dependency to get current user payload from token."""
    auth_service = get_auth_service()

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        return auth_service.validate_access_token(credentials.credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


def require_permission(permission: str):
    """Dependency factory to require a specific permission."""

    async def _require_permission(
        user: Annotated[dict, Depends(get_current_user_payload)],
    ) -> dict:
        auth_service = get_auth_service()
        try:
            auth_service.require_permission(user.get("roles", []), permission)
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        return user

    return _require_permission
