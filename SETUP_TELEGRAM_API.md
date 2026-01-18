# Telegram Bot API Setup Guide

This guide explains how to set up Telegram Bot API integration for the ISR Platform to monitor Telegram channels and groups for OSINT data collection.

## Overview

The Telegram connector enables:
- **Channel Monitoring**: Track public Telegram channels
- **Group Monitoring**: Monitor Telegram groups (where bot is member)
- **Media Extraction**: Download photos, videos, documents
- **Forward Tracking**: Detect forwarded messages and their origins
- **Engagement Metrics**: Track views and interactions
- **Entity Extraction**: Parse hashtags, mentions, and URLs

## Prerequisites

- Telegram account (mobile phone number)
- Access to channels/groups you want to monitor
- Basic understanding of Telegram Bot API

## Step 1: Create a Telegram Bot

### 1.1 Talk to BotFather

1. Open Telegram and search for `@BotFather`
2. Start a conversation with `/start`
3. Create a new bot with `/newbot`
4. Follow the prompts:
   - **Bot name**: Choose a display name (e.g., "ISR Monitor Bot")
   - **Username**: Choose a unique username ending in `bot` (e.g., `isr_monitor_bot`)

### 1.2 Get Your Bot Token

After creation, BotFather will provide:
```
Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890

Keep your token secure and store it safely!
```

**⚠️ SECURITY WARNING**: This token gives full access to your bot. Never commit it to version control or share it publicly.

## Step 2: Configure Bot Settings

### 2.1 Enable Privacy Mode (Optional)

For group monitoring, you may need to disable privacy mode:

```
/setprivacy
Select your bot
Disable
```

This allows the bot to see all messages in groups (not just commands).

### 2.2 Set Bot Description (Optional)

```
/setdescription
Select your bot
Enter description: "OSINT data collection and analysis bot"
```

### 2.3 Set Bot Commands (Optional)

```
/setcommands
Select your bot
Enter commands:
status - Get bot status
help - Get help information
```

## Step 3: Add Bot to Channels/Groups

### 3.1 For Public Channels

1. Go to the channel you want to monitor
2. Click on the channel name → Administrators
3. Add Administrator → Search for your bot username
4. Grant necessary permissions (at minimum: "Post Messages" to verify bot access)
5. Note the channel username (e.g., `@channelname`)

### 3.2 For Private Channels/Groups

1. Add your bot as a member or administrator
2. Get the channel/group ID:
   - Send a message in the channel/group
   - Use the bot API to get updates: 
     ```bash
     curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
     ```
   - Look for the `chat` object in the response and note the `id` (e.g., `-1001234567890`)

### 3.3 For Public Groups

1. Add your bot as a member
2. Note the group username or ID

## Step 4: Configure ISR Platform

### 4.1 Update Environment Variables

Edit your `.env` file or set environment variables:

```bash
# Telegram Bot API
SOCIAL_TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
SOCIAL_TELEGRAM_CHANNELS=["@channel1", "@channel2", "-1001234567890"]
```

### 4.2 Example Configuration

```bash
# .env file
SOCIAL_ENABLED=true
SOCIAL_USE_MOCK_DATA=false

# Telegram Bot Token (from @BotFather)
SOCIAL_TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890

# Channels to monitor (array of usernames or IDs)
SOCIAL_TELEGRAM_CHANNELS=["@afghanistan_news", "@kabul_updates", "-1001234567890"]

# Rate limits (Telegram allows 30 req/sec, but be conservative)
SOCIAL_MAX_REQUESTS_PER_MINUTE=30
SOCIAL_MAX_REQUESTS_PER_HOUR=1800
SOCIAL_POLL_INTERVAL_SECONDS=300
```

### 4.3 Channel Format

- **Public channels**: Use `@username` format (e.g., `@channelname`)
- **Private channels/groups**: Use numeric ID format (e.g., `-1001234567890`)
- **Multiple channels**: JSON array format `["@channel1", "@channel2"]`

## Step 5: Verify Setup

### 5.1 Test Bot Connection

```python
import asyncio
import httpx

async def test_bot():
    token = "YOUR_BOT_TOKEN"
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.telegram.org/bot{token}/getMe")
        print(response.json())

asyncio.run(test_bot())
```

Expected output:
```json
{
  "ok": true,
  "result": {
    "id": 1234567890,
    "is_bot": true,
    "first_name": "ISR Monitor Bot",
    "username": "isr_monitor_bot"
  }
}
```

### 5.2 Start the Ingestion System

```bash
# Start the platform
docker-compose up -d

# Check logs
docker-compose logs -f api
```

Look for:
```
✓ Telegram connector registered (monitoring 3 channels)
```

### 5.3 Verify Data Collection

Access the API to check ingested data:

```bash
curl http://localhost:8000/api/v1/ingestion/status
```

## Step 6: Advanced Configuration

### 6.1 Custom Search Queries

The connector automatically monitors all messages from configured channels. To filter specific topics, modify the connector in `src/services/connectors/telegram_connector.py`.

### 6.2 Media Download

To download media files:

```python
# Get file URL
file_url = await telegram_connector.get_file_url(file_id)

# Download file
async with httpx.AsyncClient() as client:
    response = await client.get(file_url)
    with open("downloaded_file.jpg", "wb") as f:
        f.write(response.content)
```

### 6.3 Rate Limiting

Telegram Bot API limits:
- **30 messages/second** to different users
- **1 message/second** to the same user
- **20 messages/minute** to the same group

The connector implements automatic rate limiting.

## Telegram API Features

### Available Endpoints

- `getUpdates`: Poll for new messages
- `getChat`: Get channel/group information
- `getChatMember`: Check member status
- `getFile`: Get file download URL
- `sendMessage`: Send messages (for verification)

### Message Types Supported

- Text messages
- Photos
- Videos
- Documents
- Audio
- Voice messages
- Polls
- Location

### Extracted Data

For each message, the connector extracts:
- Message ID and date
- Author information (user ID, username, name)
- Message text/caption
- Media type and file ID
- Hashtags, mentions, URLs
- Forward information (if forwarded)
- Views count
- Reply relationships

## Troubleshooting

### Bot Can't See Messages

**Problem**: Bot is not receiving messages from group.

**Solutions**:
1. Disable privacy mode: `/setprivacy` → Disable
2. Make bot an administrator (if channel)
3. Ensure bot is a member of the group

### Invalid Bot Token

**Problem**: "Unauthorized" error.

**Solutions**:
1. Verify token is correct (no spaces/newlines)
2. Check if bot was deleted in BotFather
3. Create a new bot if needed

### Channel Not Found

**Problem**: "Chat not found" error.

**Solutions**:
1. Verify channel username is correct (include `@`)
2. For private channels, use numeric ID
3. Ensure bot is member/admin of the channel

### Rate Limiting

**Problem**: "Too Many Requests" error.

**Solutions**:
1. Reduce polling frequency
2. Monitor fewer channels
3. Implement backoff strategy (already included in connector)

## Best Practices

### Security

1. **Never commit bot tokens** to version control
2. **Use environment variables** for all credentials
3. **Rotate tokens** periodically
4. **Monitor bot usage** through BotFather

### Performance

1. **Start with fewer channels** and scale up
2. **Adjust poll interval** based on message volume
3. **Monitor API usage** to avoid rate limits
4. **Use webhooks** for high-volume channels (advanced)

### Data Quality

1. **Filter spam** and irrelevant messages
2. **Verify forwarded content** for authenticity
3. **Track message edits** and deletions
4. **Cross-reference** with other sources

## Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [BotFather Commands](https://core.telegram.org/bots#6-botfather)
- [Telegram Bot Features](https://core.telegram.org/bots/features)
- [Rate Limits](https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this)

## Support

For issues specific to the ISR Platform Telegram integration:
1. Check connector logs: `docker-compose logs telegram`
2. Verify configuration: `curl http://localhost:8000/api/v1/ingestion/config`
3. Review connector status: `curl http://localhost:8000/api/v1/ingestion/status`

## Next Steps

After setting up Telegram:
1. Configure additional channels for monitoring
2. Set up narrative analysis to track propaganda patterns
3. Enable ML models for content classification
4. Configure alerts for high-priority content
5. Integrate with the real-time dashboard

---

**Last Updated**: January 2026
**Version**: 1.0.0
