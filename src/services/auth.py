"""Authentication service for ISR Platform."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config.settings import get_settings
from src.models.domain import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationError(Exception):
    """Authentication error."""

    pass


class AuthorizationError(Exception):
    """Authorization error."""

    pass


class AuthService:
    """Service for authentication and authorization."""

    def __init__(self) -> None:
        """Initialize auth service."""
        self.settings = get_settings()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def create_access_token(
        self,
        user_id: UUID,
        username: str,
        roles: list[str],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create an access token."""
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.settings.access_token_expire_minutes)

        expire = utcnow() + expires_delta
        payload = {
            "sub": str(user_id),
            "username": username,
            "roles": roles,
            "exp": expire,
            "type": "access",
        }
        return jwt.encode(
            payload,
            self.settings.secret_key,
            algorithm=self.settings.algorithm,
        )

    def create_refresh_token(
        self,
        user_id: UUID,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a refresh token."""
        if expires_delta is None:
            expires_delta = timedelta(days=self.settings.refresh_token_expire_days)

        expire = utcnow() + expires_delta
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
        }
        return jwt.encode(
            payload,
            self.settings.secret_key,
            algorithm=self.settings.algorithm,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a token."""
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm],
            )
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {e}") from e

    def validate_access_token(self, token: str) -> dict[str, Any]:
        """Validate an access token and return the payload."""
        payload = self.decode_token(token)
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        return payload

    def check_permission(
        self,
        user_roles: list[str],
        required_permission: str,
    ) -> bool:
        """Check if user has required permission."""
        # Define role permissions
        role_permissions = {
            "VIEWER": ["dashboard:read", "alert:read", "report:read"],
            "ANALYST": [
                "dashboard:read",
                "alert:read",
                "alert:acknowledge",
                "alert:resolve",
                "entity:read",
                "event:read",
                "narrative:read",
                "simulation:read",
                "simulation:create",
                "simulation:run",
                "report:read",
                "report:generate",
                "ml:read",
            ],
            "SENIOR_ANALYST": [
                "alert:create",
                "simulation:create",
                "simulation:run",
                "entity:annotate",
            ],
            "OPERATOR": [
                "alert:escalate",
                "system:status",
            ],
            "ADMIN": [
                "user:manage",
                "role:manage",
                "system:configure",
                "audit:read",
            ],
            "SUPER_ADMIN": ["*"],
        }

        for role in user_roles:
            permissions = role_permissions.get(role, [])
            # Inherit permissions from lower roles
            if role == "ANALYST":
                permissions.extend(role_permissions.get("VIEWER", []))
            elif role == "SENIOR_ANALYST":
                permissions.extend(role_permissions.get("ANALYST", []))
                permissions.extend(role_permissions.get("VIEWER", []))
            elif role == "OPERATOR":
                permissions.extend(role_permissions.get("SENIOR_ANALYST", []))
                permissions.extend(role_permissions.get("ANALYST", []))
                permissions.extend(role_permissions.get("VIEWER", []))

            if "*" in permissions or required_permission in permissions:
                return True

        return False

    def require_permission(
        self,
        user_roles: list[str],
        required_permission: str,
    ) -> None:
        """Require a specific permission, raise error if not authorized."""
        if not self.check_permission(user_roles, required_permission):
            raise AuthorizationError(
                f"Permission denied: {required_permission} required"
            )


# Global instance
_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    """Get the auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
