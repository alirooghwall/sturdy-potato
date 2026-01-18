"""Authentication service with real JWT implementation."""

import logging
from datetime import datetime, timedelta, UTC
from typing import Any

from passlib.context import CryptContext
from jose import JWTError, jwt

from src.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None


def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
    """Verify token and check type."""
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    if payload.get("type") != token_type:
        logger.warning(f"Invalid token type. Expected {token_type}, got {payload.get('type')}")
        return None
    
    return payload


class AuthService:
    """Authentication service."""
    
    def __init__(self):
        """Initialize auth service."""
        self.pwd_context = pwd_context
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return get_password_hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password."""
        return verify_password(plain_password, hashed_password)
    
    def create_tokens(self, user_id: str, username: str, roles: list[str]) -> dict[str, str]:
        """Create access and refresh tokens for user."""
        token_data = {
            "sub": str(user_id),
            "username": username,
            "roles": roles,
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user_id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    
    def verify_access_token(self, token: str) -> dict[str, Any] | None:
        """Verify access token."""
        return verify_token(token, "access")
    
    def verify_refresh_token(self, token: str) -> dict[str, Any] | None:
        """Verify refresh token."""
        return verify_token(token, "refresh")
    
    def refresh_access_token(self, refresh_token: str) -> str | None:
        """Create new access token from refresh token."""
        payload = self.verify_refresh_token(refresh_token)
        
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # In production, fetch user data from database
        new_access_token = create_access_token({"sub": user_id})
        return new_access_token


# Global instance
_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    """Get auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
