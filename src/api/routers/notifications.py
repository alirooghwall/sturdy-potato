"""Notification management endpoints."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.services.notification_preference_service import get_notification_pref_service
from src.services.notification_service import get_notification_service


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency for getting current user
async def get_current_user(token: str = Depends(lambda: "mock_user")) -> dict:
    """Get current authenticated user."""
    return {"user_id": "mock_user", "username": "analyst", "email": "analyst@example.com", "roles": ["analyst"]}


class NotificationPreferences(BaseModel):
    """User notification preferences."""

    email_enabled: bool = True
    email_address: str | None = None
    slack_enabled: bool = False
    sms_enabled: bool = False
    phone_number: str | None = None
    
    # Alert level preferences
    notify_on_critical: bool = True
    notify_on_high: bool = True
    notify_on_medium: bool = False
    notify_on_low: bool = False
    
    # Notification schedule
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"
    
    # Digest settings
    daily_briefing_enabled: bool = True
    daily_briefing_time: str = "08:00"


class TestNotificationRequest(BaseModel):
    """Request to test notification channels."""

    channels: list[str] = Field(..., description="Channels to test: email, slack, sms")
    message: str = Field(default="This is a test notification from ISR Platform")


class SendNotificationRequest(BaseModel):
    """Request to send notification."""

    title: str
    message: str
    severity: str = "MEDIUM"
    channels: list[str] = Field(default=["email"])
    recipients: list[str] | None = None


@router.get("/preferences")
async def get_notification_preferences(
    current_user: dict = Depends(get_current_user),
) -> NotificationPreferences:
    """Get current user's notification preferences."""
    pref_service = get_notification_pref_service()
    
    # Try to get from database
    try:
        prefs = await pref_service.get_preferences(current_user.get("user_id"))
        if prefs:
            return NotificationPreferences(
                email_enabled=prefs.email_enabled,
                email_address=prefs.email_address or current_user.get("email", ""),
                slack_enabled=prefs.slack_enabled,
                sms_enabled=prefs.sms_enabled,
                phone_number=prefs.phone_number,
                notify_on_critical=prefs.notify_on_critical,
                notify_on_high=prefs.notify_on_high,
                notify_on_medium=prefs.notify_on_medium,
                notify_on_low=prefs.notify_on_low,
                quiet_hours_enabled=prefs.quiet_hours_enabled,
                quiet_hours_start=prefs.quiet_hours_start,
                quiet_hours_end=prefs.quiet_hours_end,
                daily_briefing_enabled=prefs.daily_briefing_enabled,
                daily_briefing_time=prefs.daily_briefing_time,
            )
    except Exception as e:
        logger.warning(f"Error fetching preferences: {e}")
    
    # Return defaults
    return NotificationPreferences(
        email_address=current_user.get("email", ""),
    )


@router.put("/preferences")
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Update notification preferences."""
    pref_service = get_notification_pref_service()
    
    # Save to database
    try:
        await pref_service.save_preferences(
            user_id=current_user.get("user_id"),
            preferences=preferences.model_dump(),
        )
        logger.info(f"Notification preferences updated for user {current_user.get('user_id')}")
    except Exception as e:
        logger.warning(f"Error saving preferences: {e}")
    
    return {
        "status": "updated",
        "message": "Notification preferences updated successfully",
        "preferences": preferences.model_dump(),
    }


@router.post("/test")
async def test_notification(
    request: TestNotificationRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Test notification channels."""
    service = get_notification_service()
    
    # Create test alert
    test_alert = {
        "title": "Test Notification",
        "description": request.message,
        "severity": "LOW",
        "reference_number": "TEST-001",
        "location": {"description": "Test Location"},
    }
    
    # Send to specified channels
    results = await service.send_alert_notification(test_alert, channels=request.channels)
    
    return {
        "status": "sent",
        "message": "Test notifications sent",
        "results": results,
    }


@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Send notification to specified channels and recipients."""
    # Require admin role for manual notifications
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to send notifications",
        )
    
    service = get_notification_service()
    
    # Create notification
    notification = {
        "title": request.title,
        "description": request.message,
        "severity": request.severity,
        "reference_number": f"MANUAL-{utcnow().strftime('%Y%m%d-%H%M%S')}",
        "location": {"description": "Manual Notification"},
    }
    
    # Send to specified channels
    results = await service.send_alert_notification(notification, channels=request.channels)
    
    return {
        "status": "sent",
        "message": f"Notification sent to {len(request.channels)} channels",
        "results": results,
        "timestamp": utcnow().isoformat(),
    }


@router.get("/channels")
async def get_available_channels(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get list of available notification channels and their status."""
    import os
    
    channels = [
        {
            "id": "email",
            "name": "Email",
            "enabled": os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true",
            "configured": bool(os.getenv("SMTP_HOST")),
            "description": "Email notifications via SMTP",
        },
        {
            "id": "slack",
            "name": "Slack",
            "enabled": os.getenv("SLACK_NOTIFICATIONS_ENABLED", "false").lower() == "true",
            "configured": bool(os.getenv("SLACK_WEBHOOK_URL")),
            "description": "Slack workspace notifications",
        },
        {
            "id": "sms",
            "name": "SMS",
            "enabled": os.getenv("SMS_NOTIFICATIONS_ENABLED", "false").lower() == "true",
            "configured": bool(os.getenv("TWILIO_ACCOUNT_SID")),
            "description": "SMS via Twilio",
        },
        {
            "id": "websocket",
            "name": "WebSocket",
            "enabled": True,
            "configured": True,
            "description": "Real-time browser notifications",
        },
    ]
    
    return {
        "channels": channels,
        "total": len(channels),
        "enabled": sum(1 for c in channels if c["enabled"]),
    }


@router.get("/history")
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    channel: str | None = None,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get notification history for current user."""
    pref_service = get_notification_pref_service()
    
    # Query from database
    try:
        result = await pref_service.get_notification_history(
            user_id=current_user.get("user_id"),
            channel=channel,
            limit=limit,
            offset=offset,
        )
        return result
    except Exception as e:
        logger.warning(f"Error fetching notification history: {e}")
    
    return {
        "notifications": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }
