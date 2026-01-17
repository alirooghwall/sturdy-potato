# 🛡️ Scam Shield

**AI-Powered Phishing, Fraud, and Scam Detection Platform**

A browser extension that protects users from online scams, phishing attacks, and fraud in real-time.

## ✨ Features

### Website Scam Detection
- Real-time analysis of visited websites
- Detection of phishing attempts and fake login pages
- Brand impersonation detection
- Risk banner display (Green = Safe, Yellow = Suspicious, Red = Dangerous)

### URL Analysis
- Expanded shortened URLs
- Domain age and reputation analysis
- Risk score (0-100) with explanation

### Message Scam Analyzer
- Analyze suspicious messages from SMS, WhatsApp, Telegram, and Email
- Detect urgency tactics, payment requests, credential harvesting
- Identify fake jobs, MLM scams, and crypto fraud

### Fake Job & MLM Detection
- Pattern-based detection of job scams
- MLM/Pyramid scheme identification
- Crypto scam detection

### Brand Impersonation Detection
- Logo and brand name misuse detection
- Domain lookalike detection
- Warning when sites pretend to be known companies

## 🚀 Installation

### Chrome/Edge Extension (Developer Mode)

1. Clone this repository:
   ```bash
   git clone https://github.com/alirooghwall/sturdy-potato.git
   cd sturdy-potato
   ```

2. Install dependencies (for development):
   ```bash
   npm install
   ```

3. Load the extension in Chrome:
   - Open `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `extension` folder from this project

4. The Scam Shield icon will appear in your browser toolbar

## 📁 Project Structure

```
scam-shield/
├── extension/           # Browser extension files
│   ├── manifest.json    # Extension manifest (v3)
│   ├── popup/           # Extension popup UI
│   │   ├── popup.html
│   │   ├── popup.css
│   │   └── popup.js
│   ├── content/         # Content scripts
│   │   ├── content.js
│   │   └── content.css
│   ├── background/      # Service worker
│   │   └── background.js
│   └── icons/           # Extension icons
├── src/                 # Core analysis modules
│   ├── analysis/
│   │   ├── urlAnalyzer.js       # URL/domain analysis
│   │   ├── messageAnalyzer.js   # Message scam detection
│   │   ├── websiteAnalyzer.js   # Page content analysis
│   │   ├── riskScoring.js       # Risk scoring engine
│   │   └── reporting.js         # Community reporting
│   └── index.js         # Module exports
├── tests/               # Test files
│   ├── urlAnalyzer.test.js
│   ├── messageAnalyzer.test.js
│   └── websiteAnalyzer.test.js
└── package.json
```

## 🛠️ Development

### Running Tests
```bash
npm test
```

### Running Linter
```bash
npm run lint
```

## 🔒 Privacy

- **No permanent storage** of personal messages
- **Ephemeral processing** - messages analyzed and discarded
- **No tracking** of browsing behavior
- **No credential collection**
- **Encrypted communication**

## 📊 Risk Scoring

The system calculates a risk score between 0-100 based on:
- Language manipulation patterns
- Domain age and characteristics
- Payment method requests
- Brand impersonation indicators
- Community reports

### Risk Levels
- 🟢 **Safe** (0-29): No significant threats detected
- 🟡 **Suspicious** (30-59): Some warning signs present
- 🔴 **Dangerous** (60-100): High probability of scam

## 🎯 Scam Types Detected

| Type | Description |
|------|-------------|
| Phishing | Fake login pages, credential harvesting |
| Fake Job | "Easy money", upfront payment required |
| MLM/Pyramid | Multi-level marketing, recruitment focus |
| Crypto Scam | Guaranteed returns, doubling schemes |
| Lottery Scam | Prize claims, advance fees |
| Romance Scam | Financial requests from online connections |
| Advance Fee Fraud | Payment before service/product |
| Intimidation | Fake legal threats, IRS impersonation |

## 🌐 Supported Platforms

- Google Chrome
- Microsoft Edge (Chromium)
- Other Chromium-based browsers

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## ⚠️ Disclaimer

This tool provides risk assessments based on pattern analysis and heuristics. While it helps identify potential scams, it may not catch all threats. Always exercise caution when sharing personal information online.
