# ISR Platform - API Keys Setup Guide

This guide helps you obtain and configure all external API keys needed for the ISR Platform.

---

## 🔑 Required API Keys

### 1. SECRET_KEY (Required)

**Purpose:** JWT token signing and encryption

**How to Generate:**
```bash
# Linux/Mac
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Add to .env:**
```bash
SECRET_KEY=your_generated_64_character_hex_string_here
```

⚠️ **CRITICAL:** Never commit this to version control!

---

## 📰 News Sources (Recommended)

### 2. NewsAPI.org

**Purpose:** Global news aggregation (80,000+ sources)

**Free Tier:** 100 requests/day

**How to Get:**
1. Visit https://newsapi.org/register
2. Sign up with email
3. Verify email
4. Copy API key from dashboard

**Add to .env:**
```bash
NEWSAPI_API_KEY=your_newsapi_key_here
NEWSAPI_ENABLED=true
```

**Test it:**
```bash
curl "https://newsapi.org/v2/top-headlines?country=us&apiKey=YOUR_KEY"
```

---

### 3. The Guardian Open Platform

**Purpose:** Quality news from The Guardian

**Free Tier:** 5,000 requests/day, 12 requests/second

**How to Get:**
1. Visit https://open-platform.theguardian.com/access/
2. Register for a developer key
3. Fill out form (state "Intelligence research and analysis")
4. Receive key via email (usually instant)

**Add to .env:**
```bash
GUARDIAN_API_KEY=your_guardian_key_here
GUARDIAN_ENABLED=true
```

**Test it:**
```bash
curl "https://content.guardianapis.com/search?q=afghanistan&api-key=YOUR_KEY"
```

---

### 4. New York Times API

**Purpose:** Premium news content

**Free Tier:** 500 requests/day, 5 requests/minute

**How to Get:**
1. Visit https://developer.nytimes.com/get-started
2. Create NYT account
3. Create an app
4. Enable "Article Search API"
5. Copy API key

**Add to .env:**
```bash
NYTIMES_API_KEY=your_nytimes_key_here
NYTIMES_ENABLED=true
```

**Test it:**
```bash
curl "https://api.nytimes.com/svc/search/v2/articlesearch.json?q=afghanistan&api-key=YOUR_KEY"
```

---

## 🤖 AI/LLM Services (Optional but Recommended)

### 5. OpenAI API

**Purpose:** Advanced LLM features (GPT-4, embeddings, etc.)

**Pricing:** Pay-as-you-go (starts at $0.0015/1K tokens)

**How to Get:**
1. Visit https://platform.openai.com/signup
2. Create account
3. Add payment method
4. Go to https://platform.openai.com/api-keys
5. Create new secret key
6. Copy and save immediately (shown only once!)

**Add to .env:**
```bash
OPENAI_API_KEY=sk-your_openai_key_here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
```

**Features Enabled:**
- Intelligent report generation
- Conversational query interface
- Automated insight discovery
- Anomaly explanation
- Predictive intelligence

**Test it:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

---

### 6. Anthropic Claude API

**Purpose:** Alternative LLM provider (Claude models)

**Pricing:** Pay-as-you-go

**How to Get:**
1. Visit https://console.anthropic.com/
2. Sign up for Anthropic account
3. Add payment method
4. Generate API key

**Add to .env:**
```bash
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229
```

**Test it:**
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-opus-20240229","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}'
```

---

## 🌤️ Weather Data (Optional)

### 7. OpenWeatherMap API

**Purpose:** Weather intelligence for operations

**Free Tier:** 60 requests/minute, 1,000,000 requests/month

**How to Get:**
1. Visit https://home.openweathermap.org/users/sign_up
2. Create account
3. Verify email
4. Go to https://home.openweathermap.org/api_keys
5. Copy default API key or create new one

**Add to .env:**
```bash
WEATHER_API_KEY=your_openweathermap_key_here
WEATHER_ENABLED=true
```

**Test it:**
```bash
curl "https://api.openweathermap.org/data/2.5/weather?q=Kabul&appid=YOUR_KEY"
```

---

## 📱 Social Media (Optional - Mock Data Available)

### 8. Twitter/X API v2

**Purpose:** Real-time social media intelligence

**Pricing:** Free tier available (write-only), Essential $100/month for read access

**How to Get:**
1. Visit https://developer.twitter.com/
2. Sign up for developer account
3. Create a project and app
4. Generate API keys and bearer token

**Add to .env:**
```bash
SOCIAL_TWITTER_API_KEY=your_api_key
SOCIAL_TWITTER_API_SECRET=your_api_secret
SOCIAL_TWITTER_BEARER_TOKEN=your_bearer_token
SOCIAL_ENABLED=true
SOCIAL_USE_MOCK_DATA=false
```

**Note:** Platform defaults to mock social media data if no keys provided.

---

### 9. Telegram Bot API

**Purpose:** Monitor Telegram channels

**Free:** Yes, completely free

**How to Get:**
1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Follow instructions to create bot
4. Copy bot token
5. Add bot to channels you want to monitor

**Add to .env:**
```bash
SOCIAL_TELEGRAM_BOT_TOKEN=your_telegram_bot_token
SOCIAL_TELEGRAM_CHANNELS=["@channel1", "@channel2"]
SOCIAL_ENABLED=true
```

---

## 🛰️ Satellite Imagery (Enterprise - Optional)

### 10. Planet Labs API

**Purpose:** Daily satellite imagery

**Pricing:** Enterprise pricing (contact sales)

**How to Get:**
1. Visit https://www.planet.com/
2. Contact sales for demo/trial
3. Receive API key after approval

**Add to .env:**
```bash
SATELLITE_PLANET_API_KEY=your_planet_key
SATELLITE_ENABLED=true
```

---

### 11. Sentinel Hub

**Purpose:** ESA Copernicus satellite data

**Free Tier:** Trial available, then paid plans

**How to Get:**
1. Visit https://www.sentinel-hub.com/
2. Create account
3. Create OAuth client
4. Get client ID and secret

**Add to .env:**
```bash
SATELLITE_SENTINEL_CLIENT_ID=your_client_id
SATELLITE_SENTINEL_CLIENT_SECRET=your_client_secret
SATELLITE_ENABLED=true
```

---

## 📧 Notification Services (For Alerts)

### 12. SMTP Email (For Alert Notifications)

**Purpose:** Email notifications for alerts

**Options:**
- Gmail SMTP (free for low volume)
- SendGrid (free tier: 100 emails/day)
- AWS SES (pay-as-you-go)
- Mailgun (free tier: 5,000 emails/month)

**Gmail Example:**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password
SMTP_FROM_EMAIL=noreply@isr-platform.local
```

**Note:** For Gmail, generate App Password at: https://myaccount.google.com/apppasswords

---

### 13. Twilio SMS (Optional)

**Purpose:** SMS alerts for critical threats

**Free Trial:** $15 credit

**How to Get:**
1. Visit https://www.twilio.com/try-twilio
2. Sign up and verify phone
3. Get Account SID and Auth Token
4. Get a Twilio phone number

**Add to .env:**
```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

---

### 14. Slack Webhook (Optional)

**Purpose:** Alert notifications to Slack

**Free:** Yes

**How to Get:**
1. Go to https://api.slack.com/apps
2. Create new app
3. Enable "Incoming Webhooks"
4. Add webhook to workspace
5. Copy webhook URL

**Add to .env:**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_ALERTS_ENABLED=true
```

---

## 🔐 Security Best Practices

### 1. Never Commit API Keys
```bash
# Add to .gitignore (already done)
.env
.env.local
*.env

# Check before committing
git diff .env  # Should show nothing if .gitignore is working
```

### 2. Use Different Keys Per Environment
```bash
# Development
.env

# Production
.env.production

# Staging
.env.staging
```

### 3. Rotate Keys Regularly
- Set calendar reminder for every 90 days
- Use the admin config UI to update keys
- Test new keys before removing old ones

### 4. Monitor API Usage
- Check dashboards for unusual activity
- Set up billing alerts
- Review logs for unauthorized access

### 5. Restrict Key Permissions
- Only enable necessary API endpoints
- Use read-only keys where possible
- Implement IP whitelisting if available

---

## ⚙️ Configuration via Web UI

Once the platform is running, you can manage API keys through the web interface:

1. Login at http://localhost:8000/docs
2. Navigate to **Administration** section
3. Use `/api/v1/admin/config` endpoints:
   - **GET** `/config` - View all configuration
   - **PUT** `/config/{key}` - Update specific key
   - **POST** `/config/test-api-key` - Test before saving

**Example: Test API Key**
```bash
curl -X POST http://localhost:8000/api/v1/admin/config/test-api-key \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "newsapi",
    "api_key": "your_key_to_test"
  }'
```

---

## 📊 Minimum Viable Configuration

To get started quickly, you only need:

```bash
# Absolutely Required
SECRET_KEY=<generate_with_openssl>

# Highly Recommended (choose 1+)
NEWSAPI_API_KEY=<your_key>
# OR
GUARDIAN_API_KEY=<your_key>

# Optional but Useful
OPENAI_API_KEY=<your_key>  # Enables LLM features
```

Everything else can be added later as needed.

---

## 📝 Quick Reference

| Service | Free Tier | Time to Get | Required? |
|---------|-----------|-------------|-----------|
| SECRET_KEY | N/A | 1 min | ✅ Required |
| NewsAPI | 100 req/day | 2 min | ⭐ Recommended |
| Guardian | 5,000 req/day | 5 min | ⭐ Recommended |
| NY Times | 500 req/day | 5 min | Optional |
| OpenAI | Pay-as-you-go | 5 min | ⭐ Recommended |
| Anthropic | Pay-as-you-go | 5 min | Optional |
| Weather | 1M req/month | 2 min | Optional |
| Twitter | Limited | 10 min | Optional |
| Telegram | Unlimited | 2 min | Optional |
| Slack | Unlimited | 5 min | Optional |

---

## 🆘 Troubleshooting

### "Invalid API Key" Error
- Check for extra spaces in .env file
- Verify key is still active in provider dashboard
- Check if you're on free tier and hit rate limits
- Ensure correct key format (some start with specific prefixes)

### "Rate Limit Exceeded"
- Wait for rate limit window to reset
- Upgrade to paid tier if needed
- Enable multiple sources to distribute load

### "Network Error"
- Check internet connection
- Verify API endpoint URLs are correct
- Check if service is experiencing downtime
- Review firewall/proxy settings

---

## 🎯 Next Steps

1. ✅ Generate SECRET_KEY
2. ✅ Get at least one news API key
3. ✅ (Optional) Get OpenAI key for LLM features
4. ✅ Add keys to `.env` file
5. ✅ Start platform: `./scripts/start_platform.sh`
6. ✅ Test configuration: http://localhost:8000/docs

See **QUICK_START_GUIDE.md** for complete setup instructions.
