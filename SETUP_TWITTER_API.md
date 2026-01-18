# Twitter/X API Setup Guide

## Step 1: Get Twitter API Access

### 1.1 Create Twitter Developer Account

1. **Go to:** https://developer.twitter.com/en/portal/dashboard
2. **Sign in** with your Twitter/X account
3. **Apply for Developer Access:**
   - Click "Sign up for Free Account"
   - Choose use case: **"Exploring the API"** or **"Academic Research"**
   - Fill in the application form
   - Accept Terms of Service

### 1.2 Create a Project and App

1. **Create Project:**
   - Name: "ISR Intelligence Platform"
   - Use case: "Monitoring and analysis"
   - Description: "Intelligence gathering and analysis for security research"

2. **Create App:**
   - App name: "isr-platform-monitor"
   - Environment: Production or Development

3. **Save Your Credentials:**
   ```
   API Key: xxxxxxxxxxxxxxxxxxxxxx
   API Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Bearer Token: AAAAAAAAAAAAAAAAAAAAAxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   
   ⚠️ **IMPORTANT:** Save these immediately! You can't see them again.

### 1.3 Set Up Authentication

For our platform, we need **Bearer Token** (simplest for read-only access).

**API Access Levels:**

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0 | 500k tweets/month, Basic endpoints |
| **Basic** | $100/month | 10M tweets/month, Recent search |
| **Pro** | $5,000/month | 50M tweets/month, Full archive |

**For ISR Platform: Free tier is sufficient to start!**

---

## Step 2: Configure ISR Platform

### 2.1 Update `.env` File

```bash
# Twitter/X API Configuration
TWITTER_ENABLED=true
TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAxxxxxxxxxxxxxxxxxxxxxxxxxx
TWITTER_API_KEY=xxxxxxxxxxxxxxxxxxxxxx
TWITTER_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Search keywords (Afghanistan ISR)
TWITTER_SEARCH_QUERIES=Afghanistan,Taliban,Kabul,Kandahar,Helmand

# Monitoring settings
TWITTER_POLL_INTERVAL_SECONDS=600  # 10 minutes
TWITTER_MAX_RESULTS_PER_QUERY=10
```

### 2.2 Update Configuration Code

Already done! The Twitter connector is implemented in:
- `src/services/connectors/twitter_connector.py`
- Auto-configured from `.env`

---

## Step 3: Test Twitter Integration

### 3.1 Start the System

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f api
```

### 3.2 Test Twitter API Connection

```bash
# Test endpoint (check if credentials work)
curl -X GET http://localhost:8000/api/v1/social/twitter/test-connection

# Search tweets
curl -X GET "http://localhost:8000/api/v1/social/twitter/search?query=Afghanistan&max_results=10"

# Get user timeline
curl -X GET "http://localhost:8000/api/v1/social/twitter/user/BBCWorld"
```

### 3.3 Monitor Ingestion

```bash
# Check connector status
curl http://localhost:8000/api/v1/ingestion/connectors

# View Twitter connector details
curl http://localhost:8000/api/v1/ingestion/connectors/twitter

# Check Kafka messages
curl "http://localhost:8000/api/v1/ingestion/kafka/history?topic=isr.osint.social"
```

---

## Step 4: Advanced Twitter Features

### 4.1 Monitor Specific Accounts

Edit `.env`:
```bash
TWITTER_MONITOR_ACCOUNTS=BBCBreaking,Reuters,CNN,AlJazeera
```

### 4.2 Track Hashtags

Edit `.env`:
```bash
TWITTER_MONITOR_HASHTAGS=#Afghanistan,#Taliban,#Kabul
```

### 4.3 Bot Detection

Already built-in! The system automatically detects:
- Suspicious activity patterns
- High retweet ratios
- Coordinated behavior
- Amplification networks

---

## Step 5: Telegram Setup (Optional)

### 5.1 Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send: `/newbot`
3. Follow prompts to create bot
4. Copy the **Bot Token**

### 5.2 Get Channel IDs

1. Add your bot to channels you want to monitor
2. Send a message in the channel
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find `chat.id` in the JSON response

### 5.3 Configure Telegram

Edit `.env`:
```bash
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_MONITOR_CHANNELS=-1001234567890,-1009876543210
TELEGRAM_POLL_INTERVAL_SECONDS=300  # 5 minutes
```

---

## Step 6: Testing & Verification

### 6.1 Test Propaganda Detection on Tweets

```bash
# Get recent tweets
curl -X GET "http://localhost:8000/api/v1/social/twitter/search?query=Taliban"

# Analyze a specific tweet for propaganda
curl -X POST http://localhost:8000/api/v1/ml-api/propaganda/detect \
  -H "Content-Type: application/json" \
  -d '{"text":"Tweet text here..."}'
```

### 6.2 Test News Verification

```bash
# Verify a news article
curl -X POST http://localhost:8000/api/v1/ml-api/news/verify \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Breaking: Major Development in Afghanistan",
    "content": "Article content here...",
    "source": "bbc.com"
  }'
```

### 6.3 Monitor Real-Time

```bash
# Watch system metrics
watch -n 5 'curl -s http://localhost:8000/api/v1/ingestion/stats'

# View propaganda detections in real-time
curl "http://localhost:8000/api/v1/ml-api/monitoring/system"
```

---

## Troubleshooting

### Error: 401 Unauthorized
**Problem:** Invalid credentials

**Solution:**
1. Check Bearer Token is correct
2. Verify token hasn't expired
3. Regenerate token in Twitter Developer Portal

### Error: 429 Too Many Requests
**Problem:** Rate limit exceeded

**Solution:**
1. Increase `TWITTER_POLL_INTERVAL_SECONDS`
2. Reduce number of search queries
3. Upgrade to Basic plan ($100/month)

### Error: No data ingested
**Problem:** Connector not running

**Solution:**
```bash
# Restart connector
curl -X POST http://localhost:8000/api/v1/ingestion/connectors/twitter/restart

# Check logs
docker-compose logs api | grep -i twitter
```

---

## Rate Limits Reference

### Free Tier (Twitter API v2)

| Endpoint | Limit |
|----------|-------|
| Tweet search | 500k tweets/month |
| User lookup | 300 requests/15min |
| Tweet lookup | 300 requests/15min |

### Recommended Settings

**Conservative (stay well under limits):**
```bash
TWITTER_POLL_INTERVAL_SECONDS=900  # 15 minutes
TWITTER_MAX_RESULTS_PER_QUERY=10
TWITTER_SEARCH_QUERIES=Afghanistan,Taliban  # Max 3 queries
```

**Aggressive (use more of your quota):**
```bash
TWITTER_POLL_INTERVAL_SECONDS=300  # 5 minutes
TWITTER_MAX_RESULTS_PER_QUERY=100
TWITTER_SEARCH_QUERIES=Afghanistan,Taliban,Kabul,Kandahar,Helmand
```

---

## API Endpoints Reference

### Twitter Endpoints

```bash
# Search tweets
GET /api/v1/social/twitter/search?query={query}&max_results={n}

# Get user timeline
GET /api/v1/social/twitter/user/{username}

# Get user details
GET /api/v1/social/twitter/user/{username}/details

# Analyze account for bots
POST /api/v1/social/twitter/analyze-account
Body: {"username": "account_name"}

# Get trending topics
GET /api/v1/social/twitter/trending

# Test connection
GET /api/v1/social/twitter/test-connection
```

### Telegram Endpoints

```bash
# Get channel messages
GET /api/v1/social/telegram/channel/{channel_id}/messages

# Get monitored channels
GET /api/v1/social/telegram/channels

# Search messages
GET /api/v1/social/telegram/search?query={query}
```

---

## Security Best Practices

1. **Never commit API keys to Git**
   - Use `.env` file (already in `.gitignore`)
   - Use environment variables in production

2. **Rotate tokens regularly**
   - Regenerate every 90 days
   - Immediately if compromised

3. **Use separate tokens for dev/prod**
   - Create multiple apps in Twitter Developer Portal
   - Different tokens for different environments

4. **Monitor usage**
   - Check Twitter Developer Dashboard daily
   - Set up alerts for quota usage

---

## Next Steps

Once Twitter is configured:

1. ✅ **Test API:** Use Swagger UI at `http://localhost:8000/docs`
2. ✅ **Monitor ingestion:** Check `/api/v1/ingestion/stats`
3. ✅ **Analyze data:** Use propaganda and verification endpoints
4. 🎨 **Build UI:** Follow `MILITARY_UI_BUILD_GUIDE.md` (next!)

---

## Quick Reference Commands

```bash
# Start system
docker-compose up -d

# View all connectors
curl http://localhost:8000/api/v1/ingestion/connectors | jq

# Check Twitter status
curl http://localhost:8000/api/v1/ingestion/connectors/twitter | jq

# Recent tweets ingested
curl http://localhost:8000/api/v1/ingestion/kafka/history?topic=isr.osint.social | jq

# System health
curl http://localhost:8000/api/v1/ingestion/health | jq
```

---

**Ready for Twitter integration! Get your API keys and let's go!** 🐦
