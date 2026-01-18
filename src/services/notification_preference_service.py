"""Service for managing notification preferences and history."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain import NotificationLog, NotificationPreference
from src.models.orm import NotificationLogORM, NotificationPreferenceORM, UserORM
from src.services.database import get_db_service


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


logger = logging.getLogger(__name__)


class NotificationPreferenceService:
    """Service for managing notification preferences."""

    def __init__(self):
        """Initialize the service."""
        self._db_service = None

    @property
    def db_service(self):
        """Get database service lazily."""
        if self._db_service is None:
            self._db_service = get_db_service()
        return self._db_service

    async def get_preferences(self, user_id: str) -> NotificationPreference | None:
        """Get notification preferences for a user.
        
        Args:
            user_id: User ID to query
            
        Returns:
            NotificationPreference or None if not found
        """
        try:
            async with self.db_service.session() as session:
                query = select(NotificationPreferenceORM).where(
                    NotificationPreferenceORM.user_id == user_id
                )
                result = await session.execute(query)
                pref = result.scalar_one_or_none()
                
                if pref:
                    return NotificationPreference(
                        user_id=UUID(str(pref.user_id)),
                        email_enabled=pref.email_enabled,
                        email_address=pref.email_address,
                        slack_enabled=pref.slack_enabled,
                        sms_enabled=pref.sms_enabled,
                        phone_number=pref.phone_number,
                        notify_on_critical=pref.notify_on_critical,
                        notify_on_high=pref.notify_on_high,
                        notify_on_medium=pref.notify_on_medium,
                        notify_on_low=pref.notify_on_low,
                        quiet_hours_enabled=pref.quiet_hours_enabled,
                        quiet_hours_start=pref.quiet_hours_start,
                        quiet_hours_end=pref.quiet_hours_end,
                        daily_briefing_enabled=pref.daily_briefing_enabled,
                        daily_briefing_time=pref.daily_briefing_time,
                        created_at=pref.created_at,
                        updated_at=pref.updated_at,
                    )
        except Exception as e:
            logger.warning(f"Failed to get notification preferences: {e}")
        
        return None

    async def save_preferences(
        self,
        user_id: str,
        preferences: dict[str, Any],
    ) -> NotificationPreference:
        """Save notification preferences for a user.
        
        Args:
            user_id: User ID
            preferences: Preferences dictionary
            
        Returns:
            Updated NotificationPreference
        """
        pref = NotificationPreference(
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            email_enabled=preferences.get("email_enabled", True),
            email_address=preferences.get("email_address"),
            slack_enabled=preferences.get("slack_enabled", False),
            sms_enabled=preferences.get("sms_enabled", False),
            phone_number=preferences.get("phone_number"),
            notify_on_critical=preferences.get("notify_on_critical", True),
            notify_on_high=preferences.get("notify_on_high", True),
            notify_on_medium=preferences.get("notify_on_medium", False),
            notify_on_low=preferences.get("notify_on_low", False),
            quiet_hours_enabled=preferences.get("quiet_hours_enabled", False),
            quiet_hours_start=preferences.get("quiet_hours_start", "22:00"),
            quiet_hours_end=preferences.get("quiet_hours_end", "07:00"),
            daily_briefing_enabled=preferences.get("daily_briefing_enabled", True),
            daily_briefing_time=preferences.get("daily_briefing_time", "08:00"),
        )
        
        try:
            async with self.db_service.session() as session:
                # Check if preferences exist
                query = select(NotificationPreferenceORM).where(
                    NotificationPreferenceORM.user_id == user_id
                )
                result = await session.execute(query)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing
                    existing.email_enabled = pref.email_enabled
                    existing.email_address = pref.email_address
                    existing.slack_enabled = pref.slack_enabled
                    existing.sms_enabled = pref.sms_enabled
                    existing.phone_number = pref.phone_number
                    existing.notify_on_critical = pref.notify_on_critical
                    existing.notify_on_high = pref.notify_on_high
                    existing.notify_on_medium = pref.notify_on_medium
                    existing.notify_on_low = pref.notify_on_low
                    existing.quiet_hours_enabled = pref.quiet_hours_enabled
                    existing.quiet_hours_start = pref.quiet_hours_start
                    existing.quiet_hours_end = pref.quiet_hours_end
                    existing.daily_briefing_enabled = pref.daily_briefing_enabled
                    existing.daily_briefing_time = pref.daily_briefing_time
                    existing.updated_at = utcnow()
                else:
                    # Create new
                    orm_pref = NotificationPreferenceORM(
                        user_id=user_id,
                        email_enabled=pref.email_enabled,
                        email_address=pref.email_address,
                        slack_enabled=pref.slack_enabled,
                        sms_enabled=pref.sms_enabled,
                        phone_number=pref.phone_number,
                        notify_on_critical=pref.notify_on_critical,
                        notify_on_high=pref.notify_on_high,
                        notify_on_medium=pref.notify_on_medium,
                        notify_on_low=pref.notify_on_low,
                        quiet_hours_enabled=pref.quiet_hours_enabled,
                        quiet_hours_start=pref.quiet_hours_start,
                        quiet_hours_end=pref.quiet_hours_end,
                        daily_briefing_enabled=pref.daily_briefing_enabled,
                        daily_briefing_time=pref.daily_briefing_time,
                    )
                    session.add(orm_pref)
                
                await session.commit()
                logger.info(f"Notification preferences saved for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to save notification preferences: {e}")
        
        return pref

    async def log_notification(
        self,
        user_id: str | None,
        channel: str,
        notification_type: str,
        title: str,
        message: str,
        status: str = "sent",
        error_message: str | None = None,
    ) -> NotificationLog:
        """Log a sent notification.
        
        Args:
            user_id: Target user ID (optional)
            channel: Notification channel (email, slack, sms, websocket)
            notification_type: Type of notification (alert, briefing, etc.)
            title: Notification title
            message: Notification message
            status: Delivery status (sent, failed, pending)
            error_message: Error message if failed
            
        Returns:
            NotificationLog
        """
        log = NotificationLog(
            log_id=uuid4(),
            user_id=UUID(user_id) if user_id else None,
            channel=channel,
            notification_type=notification_type,
            title=title,
            message=message,
            status=status,
            sent_at=utcnow(),
            error_message=error_message,
        )
        
        try:
            async with self.db_service.session() as session:
                orm_log = NotificationLogORM(
                    log_id=log.log_id,
                    user_id=user_id,
                    channel=channel,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    status=status,
                    sent_at=log.sent_at,
                    error_message=error_message,
                )
                session.add(orm_log)
                await session.commit()
                logger.debug(f"Notification logged: {channel} - {title}")
        except Exception as e:
            logger.warning(f"Failed to log notification: {e}")
        
        return log

    async def get_notification_history(
        self,
        user_id: str | None = None,
        channel: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get notification history.
        
        Args:
            user_id: Filter by user ID (optional)
            channel: Filter by channel (optional)
            limit: Maximum results
            offset: Results offset
            
        Returns:
            Dictionary with notifications and pagination
        """
        notifications = []
        total = 0
        
        try:
            async with self.db_service.session() as session:
                query = select(NotificationLogORM)
                
                if user_id:
                    query = query.where(NotificationLogORM.user_id == user_id)
                if channel:
                    query = query.where(NotificationLogORM.channel == channel)
                
                query = query.order_by(NotificationLogORM.sent_at.desc())
                query = query.limit(limit).offset(offset)
                
                result = await session.execute(query)
                logs = result.scalars().all()
                
                for log in logs:
                    notifications.append({
                        "log_id": str(log.log_id),
                        "user_id": str(log.user_id) if log.user_id else None,
                        "channel": log.channel,
                        "notification_type": log.notification_type,
                        "title": log.title,
                        "message": log.message[:100] + "..." if len(log.message) > 100 else log.message,
                        "status": log.status,
                        "sent_at": log.sent_at.isoformat() if log.sent_at else None,
                        "error_message": log.error_message,
                    })
                
                # Count total
                count_query = select(NotificationLogORM)
                if user_id:
                    count_query = count_query.where(NotificationLogORM.user_id == user_id)
                if channel:
                    count_query = count_query.where(NotificationLogORM.channel == channel)
                count_result = await session.execute(count_query)
                total = len(count_result.scalars().all())
                
        except Exception as e:
            logger.warning(f"Failed to get notification history: {e}")
        
        return {
            "notifications": notifications,
            "total": total,
            "limit": limit,
            "offset": offset,
        }


# Global service instance
_notification_pref_service: NotificationPreferenceService | None = None


def get_notification_pref_service() -> NotificationPreferenceService:
    """Get the notification preference service instance."""
    global _notification_pref_service
    if _notification_pref_service is None:
        _notification_pref_service = NotificationPreferenceService()
    return _notification_pref_service
