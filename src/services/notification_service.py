"""Multi-channel notification service for alerts and intelligence updates."""

import asyncio
import logging
import os
import smtplib
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


logger = logging.getLogger(__name__)


class NotificationChannel:
    """Base class for notification channels."""

    async def send(self, message: dict[str, Any]) -> bool:
        """Send notification. Returns True if successful."""
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel using SMTP."""

    def __init__(self):
        """Initialize email channel."""
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@isr-platform.local")
        self.enabled = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true"

    async def send(self, message: dict[str, Any]) -> bool:
        """Send email notification."""
        if not self.enabled:
            logger.debug("Email notifications disabled")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.get("subject", "ISR Platform Alert")
            msg["From"] = self.from_email
            msg["To"] = message.get("to", "")

            # Create HTML and plain text versions
            text_body = message.get("text", "")
            html_body = message.get("html", f"<html><body>{text_body}</body></html>")

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {message.get('to')}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


class SlackNotificationChannel(NotificationChannel):
    """Slack webhook notification channel."""

    def __init__(self):
        """Initialize Slack channel."""
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.enabled = os.getenv("SLACK_NOTIFICATIONS_ENABLED", "false").lower() == "true"

    async def send(self, message: dict[str, Any]) -> bool:
        """Send Slack notification."""
        if not self.enabled or not self.webhook_url:
            logger.debug("Slack notifications disabled or webhook not configured")
            return False

        try:
            # Format Slack message
            slack_message = {
                "text": message.get("title", "ISR Platform Alert"),
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": message.get("title", "Alert"),
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message.get("text", ""),
                        },
                    },
                ],
            }

            # Add severity color
            severity = message.get("severity", "MEDIUM")
            color = {
                "CRITICAL": "#FF0000",
                "HIGH": "#FF8C00",
                "MEDIUM": "#FFD700",
                "LOW": "#32CD32",
            }.get(severity, "#808080")

            slack_message["attachments"] = [{"color": color, "fields": message.get("fields", [])}]

            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=slack_message,
                    timeout=10,
                )
                response.raise_for_status()

            logger.info("Slack notification sent")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class SMSNotificationChannel(NotificationChannel):
    """SMS notification channel using Twilio."""

    def __init__(self):
        """Initialize SMS channel."""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        self.enabled = os.getenv("SMS_NOTIFICATIONS_ENABLED", "false").lower() == "true"

    async def send(self, message: dict[str, Any]) -> bool:
        """Send SMS notification via Twilio."""
        if not self.enabled or not self.account_sid:
            logger.debug("SMS notifications disabled or Twilio not configured")
            return False

        try:
            # Prepare SMS
            to_number = message.get("phone", "")
            text = message.get("text", "")[:160]  # SMS limit

            # Send via Twilio API
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    auth=(self.account_sid, self.auth_token),
                    data={
                        "From": self.from_number,
                        "To": to_number,
                        "Body": text,
                    },
                    timeout=10,
                )
                response.raise_for_status()

            logger.info(f"SMS sent to {to_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False


class WebSocketNotificationChannel(NotificationChannel):
    """WebSocket notification for real-time web updates."""

    def __init__(self):
        """Initialize WebSocket channel."""
        self.connections: list[Any] = []  # Store active WebSocket connections
        self.enabled = True

    async def send(self, message: dict[str, Any]) -> bool:
        """Broadcast to all connected WebSocket clients."""
        if not self.enabled:
            return False

        # TODO: Implement WebSocket broadcasting
        # This requires WebSocket manager integration
        logger.debug(f"WebSocket broadcast: {len(self.connections)} clients")
        return True

    def add_connection(self, websocket: Any):
        """Add WebSocket connection."""
        self.connections.append(websocket)

    def remove_connection(self, websocket: Any):
        """Remove WebSocket connection."""
        if websocket in self.connections:
            self.connections.remove(websocket)


class NotificationService:
    """Central notification service managing all channels."""

    def __init__(self):
        """Initialize notification service."""
        self.channels = {
            "email": EmailNotificationChannel(),
            "slack": SlackNotificationChannel(),
            "sms": SMSNotificationChannel(),
            "websocket": WebSocketNotificationChannel(),
        }

    async def send_alert_notification(
        self,
        alert: dict[str, Any],
        channels: list[str] | None = None,
    ) -> dict[str, bool]:
        """Send alert notification to specified channels.
        
        Args:
            alert: Alert data dictionary
            channels: List of channels to use (None = use all enabled)
        
        Returns:
            Dictionary mapping channel name to success status
        """
        if channels is None:
            channels = list(self.channels.keys())

        # Format message for different channels
        severity = alert.get("severity", "MEDIUM")
        title = alert.get("title", "Security Alert")
        description = alert.get("description", "")
        location = alert.get("location", {})
        reference = alert.get("reference_number", "N/A")

        # Email message
        email_message = {
            "subject": f"[{severity}] {title}",
            "text": f"""
ISR Platform Alert

Severity: {severity}
Title: {title}
Description: {description}
Location: {location.get('description', 'Unknown')}
Reference: {reference}
Time: {utcnow().isoformat()}

Login to review: http://localhost:8000/docs
""",
            "html": f"""
<html>
<body>
    <h2 style="color: {'red' if severity == 'CRITICAL' else 'orange'};">ISR Platform Alert</h2>
    <p><strong>Severity:</strong> {severity}</p>
    <p><strong>Title:</strong> {title}</p>
    <p><strong>Description:</strong> {description}</p>
    <p><strong>Location:</strong> {location.get('description', 'Unknown')}</p>
    <p><strong>Reference:</strong> {reference}</p>
    <p><strong>Time:</strong> {utcnow().isoformat()}</p>
    <p><a href="http://localhost:8000/docs">Login to review</a></p>
</body>
</html>
""",
        }

        # Slack message
        slack_message = {
            "title": f"🚨 {title}",
            "text": f"*Severity:* {severity}\n*Description:* {description}",
            "severity": severity,
            "fields": [
                {"title": "Location", "value": location.get("description", "Unknown"), "short": True},
                {"title": "Reference", "value": reference, "short": True},
            ],
        }

        # SMS message
        sms_message = {
            "text": f"ISR ALERT [{severity}]: {title}. Ref: {reference}",
        }

        # WebSocket message
        websocket_message = {
            "type": "alert",
            "data": alert,
        }

        # Send to all requested channels
        results = {}
        for channel_name in channels:
            channel = self.channels.get(channel_name)
            if not channel:
                continue

            try:
                if channel_name == "email":
                    # TODO: Get recipient from user preferences
                    email_message["to"] = os.getenv("ALERT_EMAIL_RECIPIENTS", "admin@example.com")
                    success = await channel.send(email_message)
                elif channel_name == "slack":
                    success = await channel.send(slack_message)
                elif channel_name == "sms":
                    # TODO: Get phone from user preferences
                    sms_message["phone"] = os.getenv("ALERT_SMS_RECIPIENTS", "")
                    success = await channel.send(sms_message)
                elif channel_name == "websocket":
                    success = await channel.send(websocket_message)
                else:
                    success = False

                results[channel_name] = success

            except Exception as e:
                logger.error(f"Failed to send notification via {channel_name}: {e}")
                results[channel_name] = False

        return results

    async def send_field_report_notification(
        self,
        report: dict[str, Any],
        analyst_email: str,
    ) -> bool:
        """Notify analyst of new field report."""
        message = {
            "to": analyst_email,
            "subject": f"New Field Report: {report.get('title')}",
            "text": f"""
New field report received:

Type: {report.get('report_type')}
Priority: {report.get('priority')}
Title: {report.get('title')}
From: {report.get('submitted_by')}
Reference: {report.get('reference_number')}

Review at: http://localhost:8000/docs
""",
        }

        return await self.channels["email"].send(message)

    async def send_daily_briefing(
        self,
        briefing: dict[str, Any],
        recipients: list[str],
    ) -> dict[str, bool]:
        """Send daily intelligence briefing."""
        results = {}

        for recipient in recipients:
            message = {
                "to": recipient,
                "subject": f"Daily Intelligence Briefing - {datetime.now().strftime('%Y-%m-%d')}",
                "text": briefing.get("text", ""),
                "html": briefing.get("html", ""),
            }

            success = await self.channels["email"].send(message)
            results[recipient] = success

        return results


# Global instance
_notification_service: NotificationService | None = None


def get_notification_service() -> NotificationService:
    """Get the notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
