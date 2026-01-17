/**
 * Message Scam Analyzer Module
 * Detects scams in SMS, WhatsApp, Telegram, and Email messages
 */

// Scam pattern categories
const URGENCY_PATTERNS = [
  /urgent(ly)?/i,
  /immediate(ly)?/i,
  /act (now|fast|quickly)/i,
  /limited time/i,
  /expires? (today|soon|in \d+)/i,
  /last chance/i,
  /don't (miss|wait|delay)/i,
  /hurry/i,
  /asap/i,
  /right (now|away)/i,
  /within \d+ (hours?|minutes?|days?)/i,
  /deadline/i
];

const PAYMENT_PATTERNS = [
  /send (money|\$|payment)/i,
  /wire transfer/i,
  /western union/i,
  /moneygram/i,
  /gift card/i,
  /itunes card/i,
  /google play card/i,
  /bitcoin|btc|crypto/i,
  /pay (now|immediately|first)/i,
  /processing fee/i,
  /upfront (fee|payment)/i,
  /advance (fee|payment)/i,
  /registration fee/i,
  /bank (details|account|transfer)/i,
  /wallet address/i,
  /usdt|ethereum|eth/i
];

const CREDENTIAL_PATTERNS = [
  /verify your (account|identity|email|phone)/i,
  /confirm your (details|information|password)/i,
  /update your (account|payment|billing)/i,
  /your account (has been|will be|is) (locked|suspended|compromised)/i,
  /unusual (activity|login|sign-in)/i,
  /click (here|this link|below) to/i,
  /enter your (password|pin|ssn|social security)/i,
  /reset your password/i,
  /security (alert|warning|notice)/i,
  /login credentials/i
];

const FAKE_JOB_PATTERNS = [
  /work from home/i,
  /earn \$?\d+[,\d]*\s*(per|a|\/)\s*(day|week|month|hour)/i,
  /no experience (needed|required|necessary)/i,
  /easy money/i,
  /guaranteed (income|salary|earnings)/i,
  /make money (fast|quickly|online)/i,
  /hiring (immediately|urgently|now)/i,
  /data entry (job|work|position)/i,
  /simple (tasks?|work|job)/i,
  /flexible (hours|schedule|timing)/i,
  /part[ -]?time.*\$\d+/i,
  /be your own boss/i,
  /financial freedom/i,
  /passive income/i,
  /recruitment fee/i
];

const MLM_PATTERNS = [
  /network marketing/i,
  /multi[ -]?level/i,
  /downline/i,
  /upline/i,
  /referral (bonus|commission|income)/i,
  /build (your|a) team/i,
  /join (my|our|the) team/i,
  /limited (slots?|positions?|spots?)/i,
  /ground floor opportunity/i,
  /get in early/i,
  /recruit (people|members|friends)/i,
  /residual income/i,
  /life[ -]?changing opportunity/i,
  /financial (independence|freedom)/i,
  /direct (sales?|selling)/i
];

const CRYPTO_SCAM_PATTERNS = [
  /crypto (investment|opportunity|trading)/i,
  /bitcoin (investment|doubling|multiplying)/i,
  /guaranteed (returns?|profit|roi)/i,
  /\d+x (returns?|profit|gains?)/i,
  /double your (money|investment|crypto)/i,
  /trading (bot|signal|platform)/i,
  /nft (giveaway|airdrop|drop)/i,
  /free (crypto|bitcoin|ethereum|tokens?)/i,
  /mining (opportunity|investment)/i,
  /defi (opportunity|investment)/i,
  /send \d+.*get \d+/i,
  /airdrop/i,
  /token (sale|launch|presale)/i
];

const LOTTERY_PATTERNS = [
  /you('ve| have)? won/i,
  /winner (selected|chosen|notification)/i,
  /lottery (winner|prize|claim)/i,
  /prize (money|claim|winning)/i,
  /unclaimed (funds|prize|inheritance)/i,
  /inheritance (fund|money|claim)/i,
  /million (dollars|\$|pounds|euros)/i,
  /claim your (prize|winnings|money)/i,
  /congratulations.*winner/i,
  /selected (at )?random/i
];

const ROMANCE_SCAM_PATTERNS = [
  /i('m| am) (stuck|stranded)/i,
  /need money for (ticket|flight|emergency)/i,
  /military (deployment|service)/i,
  /oil rig/i,
  /can('t| not) access (my|the) (bank|account|funds)/i,
  /send me money.*come see you/i,
  /prove your love/i,
  /webcam (show|chat)/i
];

const THREAT_PATTERNS = [
  /legal action/i,
  /arrest warrant/i,
  /police will/i,
  /fbi|cia|irs|dea/i,
  /sue you/i,
  /court (order|summons|date)/i,
  /criminal (charges|investigation)/i,
  /tax (fraud|evasion)/i,
  /jail|prison/i,
  /deportation/i
];

/**
 * Detect scam patterns in text
 * @param {string} text - Message text to analyze
 * @returns {Object} - Detection results
 */
export function detectPatterns(text) {
  const results = {
    urgency: [],
    payment: [],
    credential: [],
    fakeJob: [],
    mlm: [],
    crypto: [],
    lottery: [],
    romance: [],
    threat: []
  };

  // Helper to find matches
  const findMatches = (patterns, category) => {
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        results[category].push(match[0]);
      }
    }
  };

  findMatches(URGENCY_PATTERNS, 'urgency');
  findMatches(PAYMENT_PATTERNS, 'payment');
  findMatches(CREDENTIAL_PATTERNS, 'credential');
  findMatches(FAKE_JOB_PATTERNS, 'fakeJob');
  findMatches(MLM_PATTERNS, 'mlm');
  findMatches(CRYPTO_SCAM_PATTERNS, 'crypto');
  findMatches(LOTTERY_PATTERNS, 'lottery');
  findMatches(ROMANCE_SCAM_PATTERNS, 'romance');
  findMatches(THREAT_PATTERNS, 'threat');

  return results;
}

/**
 * Calculate message risk score
 * @param {Object} patterns - Detected patterns
 * @returns {Object} - Risk score and breakdown
 */
export function calculateMessageRiskScore(patterns) {
  const weights = {
    urgency: 10,
    payment: 25,
    credential: 30,
    fakeJob: 20,
    mlm: 20,
    crypto: 25,
    lottery: 30,
    romance: 25,
    threat: 25
  };

  let score = 0;
  const breakdown = [];

  for (const [category, matches] of Object.entries(patterns)) {
    if (matches.length > 0) {
      const categoryScore = Math.min(weights[category] * matches.length, weights[category] * 2);
      score += categoryScore;
      breakdown.push({
        category,
        matches: matches.slice(0, 3), // Limit to 3 examples
        contribution: categoryScore
      });
    }
  }

  // Bonus for multiple categories (indicates sophisticated scam)
  const categoriesDetected = breakdown.length;
  if (categoriesDetected >= 3) {
    score += 15;
    breakdown.push({
      category: 'multipleIndicators',
      matches: [`${categoriesDetected} different scam indicators detected`],
      contribution: 15
    });
  }

  return {
    score: Math.min(score, 100),
    breakdown
  };
}

/**
 * Determine scam type based on patterns
 * @param {Object} patterns - Detected patterns
 * @returns {string} - Scam type classification
 */
export function classifyScamType(patterns) {
  const scores = {
    'Phishing': patterns.credential.length * 3,
    'Fake Job Scam': patterns.fakeJob.length * 3,
    'MLM/Pyramid Scheme': patterns.mlm.length * 3,
    'Crypto Scam': patterns.crypto.length * 3,
    'Lottery/Prize Scam': patterns.lottery.length * 3,
    'Romance Scam': patterns.romance.length * 3,
    'Advance Fee Fraud': patterns.payment.length * 2,
    'Intimidation Scam': patterns.threat.length * 3
  };

  // Find highest scoring type
  let maxScore = 0;
  let scamType = 'Suspicious Message';

  for (const [type, score] of Object.entries(scores)) {
    if (score > maxScore) {
      maxScore = score;
      scamType = type;
    }
  }

  return maxScore > 0 ? scamType : 'Unknown';
}

/**
 * Generate human-readable explanation
 * @param {Object} analysis - Analysis results
 * @returns {string} - Explanation text
 */
export function generateExplanation(analysis) {
  const { scamType, patterns, riskScore, riskLevel } = analysis;
  const explanations = [];

  if (riskLevel === 'safe') {
    return '✅ This message appears to be safe. No obvious scam indicators detected.';
  }

  explanations.push(`🚨 **Warning: Possible ${scamType}**\n`);

  // Add specific warnings based on detected patterns
  if (patterns.urgency.length > 0) {
    explanations.push('⏰ **Creates urgency** - Scammers pressure you to act fast so you don\'t have time to think.');
  }

  if (patterns.payment.length > 0) {
    explanations.push('💸 **Asks for money** - Legitimate companies rarely ask for payment via gift cards, crypto, or wire transfers.');
  }

  if (patterns.credential.length > 0) {
    explanations.push('🔐 **Requests personal info** - Never share passwords, PINs, or personal details through messages.');
  }

  if (patterns.fakeJob.length > 0) {
    explanations.push('💼 **Fake job signs** - Real jobs don\'t promise easy money or require upfront payments.');
  }

  if (patterns.mlm.length > 0) {
    explanations.push('📊 **MLM/Pyramid signs** - Focus on recruiting others instead of selling real products.');
  }

  if (patterns.crypto.length > 0) {
    explanations.push('🪙 **Crypto scam signs** - No legitimate investment can guarantee returns or double your money.');
  }

  if (patterns.lottery.length > 0) {
    explanations.push('🎰 **Lottery scam signs** - You can\'t win a lottery you never entered.');
  }

  if (patterns.romance.length > 0) {
    explanations.push('💔 **Romance scam signs** - Be wary of online connections asking for money.');
  }

  if (patterns.threat.length > 0) {
    explanations.push('⚖️ **Uses threats** - Government agencies don\'t demand immediate payment or threaten arrest via text.');
  }

  // Add recommendation
  explanations.push('\n**What to do:**');
  if (riskLevel === 'dangerous') {
    explanations.push('🛑 Do NOT respond, click any links, or send money.');
    explanations.push('🗑️ Delete this message and block the sender.');
    explanations.push('📢 Report to authorities if you\'ve lost money.');
  } else {
    explanations.push('⚠️ Be cautious and verify through official channels.');
    explanations.push('🔍 Google the company or sender independently.');
    explanations.push('❌ Never share personal information or send money.');
  }

  return explanations.join('\n');
}

/**
 * Main message analysis function
 * @param {string} text - Message to analyze
 * @returns {Object} - Complete analysis result
 */
export function analyzeMessage(text) {
  if (!text || text.trim().length === 0) {
    return {
      riskScore: 0,
      scamType: 'None',
      isScam: false,
      riskLevel: 'safe',
      explanation: 'No text provided for analysis.',
      confidence: 0
    };
  }

  // Detect patterns
  const patterns = detectPatterns(text);
  
  // Calculate risk score
  const { score, breakdown } = calculateMessageRiskScore(patterns);
  
  // Classify scam type
  const scamType = classifyScamType(patterns);
  
  // Determine risk level
  let riskLevel;
  if (score < 25) {
    riskLevel = 'safe';
  } else if (score < 50) {
    riskLevel = 'suspicious';
  } else {
    riskLevel = 'dangerous';
  }

  // Calculate confidence based on number of indicators
  const indicatorCount = Object.values(patterns).flat().length;
  const confidence = Math.min(95, 40 + indicatorCount * 10);

  const analysis = {
    riskScore: score,
    scamType,
    isScam: score >= 50,
    riskLevel,
    patterns,
    breakdown,
    confidence
  };

  // Generate explanation
  analysis.explanation = generateExplanation(analysis);

  return analysis;
}

export default {
  analyzeMessage,
  detectPatterns,
  classifyScamType,
  calculateMessageRiskScore
};
