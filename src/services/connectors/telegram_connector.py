"""Telegram Bot API Integration for real-time messaging monitoring.

Requires Telegram Bot API credentials:
- Bot Token (from @BotFather)

Features:
- Monitor Telegram channels
- Track group messages
- Extract media and links
- Detect forwarded content
- Track user engagement
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseConnector, ConnectorConfig

logger = logging.getLogger(__name__)


class TelegramConnector(BaseConnector[List[Dict[str, Any]]]):
    """Telegram Bot API connector for ISR platform."""

    def __init__(
        self,
        bot_token: str,
        channels: List[str],
        config: ConnectorConfig | None = None
    ):
        """Initialize Telegram connector.
        
        Args:
            bot_token: Telegram bot token from @BotFather
            channels: List of channel usernames or IDs to monitor (e.g., ['@channelname', '-1001234567890'])
            config: Optional connector configuration
        """
        if config is None:
            config = ConnectorConfig(
                name="Telegram",
                max_requests_per_minute=30,  # Telegram allows 30 requests/second
                max_requests_per_hour=1800,
                poll_interval_seconds=300,  # 5 minutes
            )
        
        super().__init__(config)
        self.bot_token = bot_token
        self.channels = channels
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Track last message IDs for each channel to avoid duplicates
        self.last_message_ids: Dict[str, int] = {}
        
        logger.info(f"Telegram connector initialized for {len(channels)} channels")
    
    async def fetch_data(self) -> List[Dict[str, Any]] | None:
        """Fetch messages from monitored Telegram channels."""
        if not self._client:
            return None
        
        all_messages = []
        
        for channel in self.channels:
            try:
                messages = await self._fetch_channel_messages(channel)
                if messages:
                    all_messages.extend(messages)
                    logger.info(f"Fetched {len(messages)} messages from {channel}")
            
            except Exception as e:
                logger.error(f"Error fetching messages from channel '{channel}': {e}")
                continue
        
        return all_messages if all_messages else None
    
    async def _fetch_channel_messages(
        self,
        channel: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch messages from a specific Telegram channel.
        
        Args:
            channel: Channel username or ID
            limit: Maximum number of messages to fetch
        
        Returns:
            List of message dictionaries
        """
        messages = []
        
        try:
            # Get channel info first
            chat_response = await self._client.get(
                f"{self.base_url}/getChat",
                params={"chat_id": channel}
            )
            chat_response.raise_for_status()
            chat_data = chat_response.json()
            
            if not chat_data.get("ok"):
                logger.error(f"Failed to get chat info for {channel}: {chat_data.get('description')}")
                return messages
            
            chat_info = chat_data["result"]
            
            # Get recent messages using getUpdates or getChatHistory
            # Note: Bot must be admin of channel or use getUpdates for groups
            
            # For channels where bot is member, we use getUpdates
            updates_response = await self._client.get(
                f"{self.base_url}/getUpdates",
                params={
                    "limit": limit,
                    "allowed_updates": ["message", "channel_post"]
                }
            )
            updates_response.raise_for_status()
            updates_data = updates_response.json()
            
            if not updates_data.get("ok"):
                logger.error(f"Failed to get updates: {updates_data.get('description')}")
                return messages
            
            last_message_id = self.last_message_ids.get(channel, 0)
            
            for update in updates_data.get("result", []):
                message = update.get("message") or update.get("channel_post")
                
                if not message:
                    continue
                
                # Check if message is from this channel
                message_chat_id = str(message.get("chat", {}).get("id", ""))
                if message_chat_id != channel and message.get("chat", {}).get("username") != channel.lstrip("@"):
                    continue
                
                message_id = message.get("message_id", 0)
                
                # Skip already processed messages
                if message_id <= last_message_id:
                    continue
                
                # Parse message
                parsed_message = self._parse_message(message, chat_info)
                messages.append(parsed_message)
                
                # Update last message ID
                if message_id > self.last_message_ids.get(channel, 0):
                    self.last_message_ids[channel] = message_id
        
        except Exception as e:
            logger.error(f"Error in _fetch_channel_messages for {channel}: {e}")
        
        return messages
    
    def _parse_message(
        self,
        message: Dict[str, Any],
        chat_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse Telegram message into standardized format.
        
        Args:
            message: Raw Telegram message
            chat_info: Channel/chat information
        
        Returns:
            Parsed message dictionary
        """
        # Extract basic info
        message_id = message.get("message_id")
        date = message.get("date")
        text = message.get("text", message.get("caption", ""))
        
        # Extract sender info
        from_user = message.get("from", {})
        
        # Extract media info
        media_type = None
        media_url = None
        
        if "photo" in message:
            media_type = "photo"
            photos = message["photo"]
            if photos:
                # Get largest photo
                largest = max(photos, key=lambda p: p.get("file_size", 0))
                media_url = largest.get("file_id")
        elif "video" in message:
            media_type = "video"
            media_url = message["video"].get("file_id")
        elif "document" in message:
            media_type = "document"
            media_url = message["document"].get("file_id")
        elif "audio" in message:
            media_type = "audio"
            media_url = message["audio"].get("file_id")
        
        # Extract entities (mentions, hashtags, URLs)
        entities = message.get("entities", []) + message.get("caption_entities", [])
        hashtags = []
        mentions = []
        urls = []
        
        for entity in entities:
            entity_type = entity.get("type")
            offset = entity.get("offset", 0)
            length = entity.get("length", 0)
            
            if entity_type == "hashtag":
                hashtags.append(text[offset:offset+length])
            elif entity_type == "mention":
                mentions.append(text[offset:offset+length])
            elif entity_type == "url":
                urls.append(text[offset:offset+length])
            elif entity_type == "text_link":
                urls.append(entity.get("url", ""))
        
        # Check if forwarded
        forward_info = None
        if "forward_from" in message or "forward_from_chat" in message:
            forward_info = {
                "from_user": message.get("forward_from", {}).get("username"),
                "from_chat": message.get("forward_from_chat", {}).get("username"),
                "date": message.get("forward_date"),
            }
        
        # Build parsed message
        parsed = {
            "id": message_id,
            "platform": "telegram",
            "chat_id": message.get("chat", {}).get("id"),
            "chat_username": chat_info.get("username"),
            "chat_title": chat_info.get("title"),
            "chat_type": chat_info.get("type"),
            "author_id": from_user.get("id"),
            "author_username": from_user.get("username"),
            "author_first_name": from_user.get("first_name"),
            "author_is_bot": from_user.get("is_bot", False),
            "text": text,
            "date": datetime.fromtimestamp(date).isoformat() if date else None,
            "media_type": media_type,
            "media_file_id": media_url,
            "hashtags": hashtags,
            "mentions": mentions,
            "urls": urls,
            "forward_info": forward_info,
            "views": message.get("views", 0),
            "reply_to_message_id": message.get("reply_to_message", {}).get("message_id"),
        }
        
        return parsed
    
    async def ingest_data(self, data: List[Dict[str, Any]]) -> None:
        """Ingest Telegram messages into Kafka."""
        from src.services.kafka_bus_real import get_kafka_bus
        
        kafka = get_kafka_bus()
        
        for message in data:
            try:
                await kafka.publish_osint_data(
                    source_type="social",
                    source_id=f"telegram_{message['chat_id']}_{message['id']}",
                    content=message.get("text", ""),
                    metadata={
                        "platform": "telegram",
                        "message_id": message["id"],
                        "chat_id": message["chat_id"],
                        "chat_username": message.get("chat_username"),
                        "chat_title": message.get("chat_title"),
                        "chat_type": message.get("chat_type"),
                        "author_id": message.get("author_id"),
                        "author_username": message.get("author_username"),
                        "author_first_name": message.get("author_first_name"),
                        "author_is_bot": message.get("author_is_bot"),
                        "date": message.get("date"),
                        "media_type": message.get("media_type"),
                        "media_file_id": message.get("media_file_id"),
                        "hashtags": message.get("hashtags", []),
                        "mentions": message.get("mentions", []),
                        "urls": message.get("urls", []),
                        "forward_info": message.get("forward_info"),
                        "views": message.get("views", 0),
                        "reply_to_message_id": message.get("reply_to_message_id"),
                    },
                )
                
                logger.debug(f"Ingested Telegram message: {message['id']} from {message.get('chat_username')}")
            
            except Exception as e:
                logger.error(f"Error ingesting Telegram message: {e}")
                continue
    
    async def get_file_url(self, file_id: str) -> Optional[str]:
        """Get download URL for a file.
        
        Args:
            file_id: Telegram file ID
        
        Returns:
            Download URL or None
        """
        if not self._client:
            return None
        
        try:
            response = await self._client.get(
                f"{self.base_url}/getFile",
                params={"file_id": file_id}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("ok"):
                file_path = data["result"].get("file_path")
                return f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
        
        except Exception as e:
            logger.error(f"Error getting file URL: {e}")
        
        return None
