"""Service for managing system configuration and audit logs."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import ConfigAuditLog
from src.models.orm import ConfigAuditLogORM, ConfigurationORM
from src.services.database import get_db_service


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


logger = logging.getLogger(__name__)


class ConfigurationService:
    """Service for managing system configuration."""

    def __init__(self):
        """Initialize the service."""
        self._db_service = None

    @property
    def db_service(self):
        """Get database service lazily."""
        if self._db_service is None:
            self._db_service = get_db_service()
        return self._db_service

    async def get_configuration(self, key: str) -> dict[str, Any] | None:
        """Get a configuration value by key.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration dictionary or None
        """
        try:
            async with self.db_service.session() as session:
                query = select(ConfigurationORM).where(ConfigurationORM.key == key)
                result = await session.execute(query)
                config = result.scalar_one_or_none()
                
                if config:
                    return {
                        "key": config.key,
                        "value": config.value,
                        "description": config.description,
                        "category": config.category,
                        "is_secret": config.is_secret,
                        "is_required": config.is_required,
                        "created_at": config.created_at.isoformat() if config.created_at else None,
                        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
                    }
        except Exception as e:
            logger.warning(f"Failed to get configuration: {e}")
        
        return None

    async def set_configuration(
        self,
        key: str,
        value: str,
        description: str | None = None,
        category: str = "general",
        is_secret: bool = False,
        is_required: bool = False,
        user_id: str | None = None,
        username: str | None = None,
    ) -> dict[str, Any]:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            description: Optional description
            category: Configuration category
            is_secret: Whether value is a secret
            is_required: Whether configuration is required
            user_id: User making the change
            username: Username making the change
            
        Returns:
            Configuration dictionary
        """
        old_value = None
        
        try:
            async with self.db_service.session() as session:
                # Check if configuration exists
                query = select(ConfigurationORM).where(ConfigurationORM.key == key)
                result = await session.execute(query)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Store old value for audit
                    old_value = existing.value
                    
                    # Update existing
                    existing.value = value
                    if description is not None:
                        existing.description = description
                    existing.category = category
                    existing.is_secret = is_secret
                    existing.is_required = is_required
                    existing.updated_at = utcnow()
                else:
                    # Create new
                    config = ConfigurationORM(
                        key=key,
                        value=value,
                        description=description,
                        category=category,
                        is_secret=is_secret,
                        is_required=is_required,
                    )
                    session.add(config)
                
                await session.commit()
                logger.info(f"Configuration saved: {key}")
        except Exception as e:
            logger.warning(f"Failed to save configuration: {e}")
        
        # Log audit
        await self.log_config_change(
            user_id=user_id or "system",
            username=username or "system",
            action="updated" if old_value else "created",
            key=key,
            old_value="***" if is_secret else old_value,
            new_value="***" if is_secret else value,
        )
        
        return {
            "key": key,
            "value": "***" if is_secret else value,
            "category": category,
        }

    async def delete_configuration(
        self,
        key: str,
        user_id: str | None = None,
        username: str | None = None,
    ) -> bool:
        """Delete a configuration value.
        
        Args:
            key: Configuration key
            user_id: User making the change
            username: Username making the change
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            async with self.db_service.session() as session:
                query = select(ConfigurationORM).where(ConfigurationORM.key == key)
                result = await session.execute(query)
                config = result.scalar_one_or_none()
                
                if config:
                    old_value = config.value
                    is_secret = config.is_secret
                    await session.delete(config)
                    await session.commit()
                    
                    # Log audit
                    await self.log_config_change(
                        user_id=user_id or "system",
                        username=username or "system",
                        action="deleted",
                        key=key,
                        old_value="***" if is_secret else old_value,
                        new_value=None,
                    )
                    
                    logger.info(f"Configuration deleted: {key}")
                    return True
        except Exception as e:
            logger.warning(f"Failed to delete configuration: {e}")
        
        return False

    async def log_config_change(
        self,
        user_id: str,
        username: str,
        action: str,
        key: str,
        old_value: str | None,
        new_value: str | None,
    ) -> ConfigAuditLog:
        """Log a configuration change for audit.
        
        Args:
            user_id: User who made the change
            username: Username who made the change
            action: Action performed (created, updated, deleted)
            key: Configuration key
            old_value: Previous value
            new_value: New value
            
        Returns:
            ConfigAuditLog
        """
        log = ConfigAuditLog(
            log_id=uuid4(),
            user_id=user_id,
            username=username,
            action=action,
            key=key,
            old_value=old_value,
            new_value=new_value,
            timestamp=utcnow(),
        )
        
        try:
            async with self.db_service.session() as session:
                orm_log = ConfigAuditLogORM(
                    log_id=log.log_id,
                    user_id=user_id,
                    username=username,
                    action=action,
                    key=key,
                    old_value=old_value,
                    new_value=new_value,
                    timestamp=log.timestamp,
                )
                session.add(orm_log)
                await session.commit()
                logger.debug(f"Config audit logged: {action} - {key}")
        except Exception as e:
            logger.warning(f"Failed to log config change: {e}")
        
        return log

    async def get_audit_log(
        self,
        limit: int = 50,
        offset: int = 0,
        key: str | None = None,
    ) -> dict[str, Any]:
        """Get configuration audit log.
        
        Args:
            limit: Maximum results
            offset: Results offset
            key: Filter by configuration key
            
        Returns:
            Dictionary with changes and pagination
        """
        changes = []
        total = 0
        
        try:
            async with self.db_service.session() as session:
                query = select(ConfigAuditLogORM)
                
                if key:
                    query = query.where(ConfigAuditLogORM.key == key)
                
                query = query.order_by(ConfigAuditLogORM.timestamp.desc())
                query = query.limit(limit).offset(offset)
                
                result = await session.execute(query)
                logs = result.scalars().all()
                
                for log in logs:
                    changes.append({
                        "log_id": str(log.log_id),
                        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                        "user": log.username,
                        "user_id": log.user_id,
                        "action": log.action,
                        "key": log.key,
                        "old_value": log.old_value,
                        "new_value": log.new_value,
                    })
                
                # Count total
                count_query = select(ConfigAuditLogORM)
                if key:
                    count_query = count_query.where(ConfigAuditLogORM.key == key)
                count_result = await session.execute(count_query)
                total = len(count_result.scalars().all())
                
        except Exception as e:
            logger.warning(f"Failed to get audit log: {e}")
        
        return {
            "changes": changes,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def export_configuration(
        self,
        include_secrets: bool = False,
        format: str = "env",
    ) -> str:
        """Export configuration as .env format.
        
        Args:
            include_secrets: Whether to include secret values
            format: Export format (env, json)
            
        Returns:
            Configuration as string
        """
        lines = ["# ISR Platform Configuration Export"]
        lines.append(f"# Generated: {utcnow().isoformat()}")
        lines.append("")
        
        try:
            async with self.db_service.session() as session:
                query = select(ConfigurationORM).order_by(ConfigurationORM.category, ConfigurationORM.key)
                result = await session.execute(query)
                configs = result.scalars().all()
                
                current_category = None
                for config in configs:
                    # Add category header
                    if config.category != current_category:
                        current_category = config.category
                        lines.append(f"\n# {current_category.upper()}")
                    
                    # Add description as comment
                    if config.description:
                        lines.append(f"# {config.description}")
                    
                    # Add value (masked if secret and not including secrets)
                    value = config.value if (include_secrets or not config.is_secret) else "***"
                    lines.append(f"{config.key}={value}")
                
        except Exception as e:
            logger.warning(f"Failed to export configuration: {e}")
            lines.append("\n# Error: Could not load configurations from database")
        
        return "\n".join(lines)


# Global service instance
_configuration_service: ConfigurationService | None = None


def get_configuration_service() -> ConfigurationService:
    """Get the configuration service instance."""
    global _configuration_service
    if _configuration_service is None:
        _configuration_service = ConfigurationService()
    return _configuration_service
