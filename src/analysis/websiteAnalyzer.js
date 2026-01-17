/**
 * Website Content Analyzer Module
 * Analyzes webpage content for phishing and scam indicators
 */

// Patterns for fake login pages
const LOGIN_FORM_INDICATORS = [
  'password',
  'login',
  'signin',
  'sign-in',
  'log-in',
  'username',
  'email',
  'credential'
];

const SENSITIVE_FIELDS = [
  'ssn',
  'social security',
  'credit card',
  'card number',
  'cvv',
  'expiry',
  'expiration',
  'bank account',
  'routing number',
  'pin'
];

const BRAND_PATTERNS = {
  'PayPal': {
    logos: ['paypal-logo', 'pp-logo'],
    keywords: ['paypal', 'pay with paypal'],
    legitDomains: ['paypal.com']
  },
  'Amazon': {
    logos: ['amazon-logo', 'a-logo'],
    keywords: ['amazon', 'prime', 'add to cart'],
    legitDomains: ['amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.ca']
  },
  'Google': {
    logos: ['google-logo', 'g-logo'],
    keywords: ['google', 'gmail', 'sign in with google'],
    legitDomains: ['google.com', 'accounts.google.com', 'gmail.com']
  },
  'Facebook': {
    logos: ['facebook-logo', 'fb-logo'],
    keywords: ['facebook', 'fb', 'meta'],
    legitDomains: ['facebook.com', 'fb.com', 'meta.com']
  },
  'Microsoft': {
    logos: ['microsoft-logo', 'ms-logo', 'windows-logo'],
    keywords: ['microsoft', 'windows', 'outlook', 'office 365'],
    legitDomains: ['microsoft.com', 'live.com', 'outlook.com', 'office.com']
  },
  'Apple': {
    logos: ['apple-logo'],
    keywords: ['apple', 'icloud', 'apple id'],
    legitDomains: ['apple.com', 'icloud.com']
  },
  'Netflix': {
    logos: ['netflix-logo'],
    keywords: ['netflix', 'watch now', 'streaming'],
    legitDomains: ['netflix.com']
  },
  'Bank of America': {
    logos: ['bofa-logo', 'bankofamerica'],
    keywords: ['bank of america', 'bofa'],
    legitDomains: ['bankofamerica.com']
  },
  'Chase': {
    logos: ['chase-logo'],
    keywords: ['chase', 'jpmorgan'],
    legitDomains: ['chase.com']
  },
  'Wells Fargo': {
    logos: ['wellsfargo-logo', 'wf-logo'],
    keywords: ['wells fargo'],
    legitDomains: ['wellsfargo.com']
  }
};

/**
 * Analyze page content for login forms
 * @param {Object} pageData - Page content data
 * @returns {Object} - Login form analysis
 */
export function analyzeLoginForms(pageData) {
  const result = {
    hasLoginForm: false,
    hasSensitiveFields: false,
    formCount: 0,
    passwordFields: 0,
    suspiciousFormActions: []
  };

  const { forms = [], inputs = [], text = '' } = pageData;
  const lowerText = text.toLowerCase();

  // Check for login form indicators in text
  result.hasLoginForm = LOGIN_FORM_INDICATORS.some(indicator => 
    lowerText.includes(indicator)
  );

  // Check for sensitive field requests
  result.hasSensitiveFields = SENSITIVE_FIELDS.some(field =>
    lowerText.includes(field)
  );

  // Analyze forms
  result.formCount = forms.length;
  
  for (const form of forms) {
    // Check form action URLs
    if (form.action) {
      try {
        const actionUrl = new URL(form.action, pageData.url);
        // Flag if form submits to different domain
        if (actionUrl.hostname !== new URL(pageData.url).hostname) {
          result.suspiciousFormActions.push({
            action: form.action,
            reason: 'Form submits to a different domain'
          });
        }
      } catch {
        // Relative URL or invalid - check for suspicious patterns
        if (form.action.includes('http') && !form.action.includes(pageData.url)) {
          result.suspiciousFormActions.push({
            action: form.action,
            reason: 'Form submits to external URL'
          });
        }
      }
    }
  }

  // Count password fields
  result.passwordFields = inputs.filter(input => 
    input.type === 'password' || input.name?.toLowerCase().includes('password')
  ).length;

  return result;
}

/**
 * Detect brand impersonation on the page
 * @param {Object} pageData - Page content data
 * @returns {Object} - Brand impersonation analysis
 */
export function detectBrandImpersonation(pageData) {
  const result = {
    detectedBrands: [],
    isImpersonation: false,
    impersonatedBrand: null,
    confidence: 0
  };

  const { text = '', images = [], url = '' } = pageData;
  const lowerText = text.toLowerCase();
  
  let currentDomain;
  try {
    currentDomain = new URL(url).hostname.toLowerCase();
  } catch {
    return result;
  }

  for (const [brand, patterns] of Object.entries(BRAND_PATTERNS)) {
    let brandScore = 0;
    const indicators = [];

    // Check keywords
    for (const keyword of patterns.keywords) {
      if (lowerText.includes(keyword.toLowerCase())) {
        brandScore += 20;
        indicators.push(`Contains "${keyword}"`);
      }
    }

    // Check logo references in images
    for (const image of images) {
      const imgSrc = (image.src || '').toLowerCase();
      const imgAlt = (image.alt || '').toLowerCase();
      
      for (const logo of patterns.logos) {
        if (imgSrc.includes(logo) || imgAlt.includes(logo)) {
          brandScore += 30;
          indicators.push(`Contains ${brand} logo`);
          break;
        }
      }
    }

    // If brand detected, check if legitimate domain
    if (brandScore > 0) {
      const isLegit = patterns.legitDomains.some(domain => 
        currentDomain === domain || 
        currentDomain === `www.${domain}` ||
        currentDomain.endsWith(`.${domain}`)
      );

      if (!isLegit) {
        result.detectedBrands.push({
          brand,
          confidence: Math.min(brandScore, 100),
          indicators
        });

        if (brandScore > result.confidence) {
          result.confidence = Math.min(brandScore, 100);
          result.impersonatedBrand = brand;
          result.isImpersonation = true;
        }
      }
    }
  }

  return result;
}

/**
 * Analyze page for phishing indicators
 * @param {Object} pageData - Page content data
 * @returns {Object} - Phishing analysis results
 */
export function analyzePhishingIndicators(pageData) {
  const result = {
    indicators: [],
    score: 0
  };

  const { text = '', title = '', url = '' } = pageData;
  const lowerText = text.toLowerCase();

  // Check for urgency language
  const urgencyPhrases = [
    'your account has been',
    'suspended',
    'verify immediately',
    'action required',
    'urgent action',
    'account will be closed',
    'limited time',
    '24 hours',
    'click here immediately'
  ];

  for (const phrase of urgencyPhrases) {
    if (lowerText.includes(phrase)) {
      result.indicators.push({
        type: 'urgency',
        detail: `Page contains urgency language: "${phrase}"`
      });
      result.score += 15;
    }
  }

  // Check for typos/grammar issues (common in phishing)
  const typoPatterns = [
    /youre\s/i,
    /dont\s/i,
    /wont\s/i,
    /thier/i,
    /recieve/i,
    /verifiy/i,
    /acccount/i,
    /securit[yi]/i
  ];

  let typoCount = 0;
  for (const pattern of typoPatterns) {
    if (pattern.test(text)) {
      typoCount++;
    }
  }

  if (typoCount > 0) {
    result.indicators.push({
      type: 'quality',
      detail: `Page contains potential spelling/grammar issues (${typoCount} found)`
    });
    result.score += typoCount * 5;
  }

  // Check for suspicious requests
  const suspiciousRequests = [
    { pattern: /enter your (password|pin|ssn)/i, detail: 'Requests password/PIN/SSN' },
    { pattern: /confirm your (identity|card|bank)/i, detail: 'Requests identity confirmation' },
    { pattern: /update (your )?payment/i, detail: 'Requests payment update' },
    { pattern: /verify (your )?account/i, detail: 'Requests account verification' }
  ];

  for (const { pattern, detail } of suspiciousRequests) {
    if (pattern.test(text)) {
      result.indicators.push({
        type: 'request',
        detail
      });
      result.score += 20;
    }
  }

  // Cap score
  result.score = Math.min(result.score, 100);

  return result;
}

/**
 * Main website content analysis function
 * @param {Object} pageData - Page content data
 * @returns {Object} - Complete analysis result
 */
export function analyzeWebsiteContent(pageData) {
  const loginAnalysis = analyzeLoginForms(pageData);
  const brandAnalysis = detectBrandImpersonation(pageData);
  const phishingAnalysis = analyzePhishingIndicators(pageData);

  // Calculate overall score
  let score = 0;
  const factors = [];

  // Login form on non-login domain
  if (loginAnalysis.hasLoginForm) {
    score += 10;
    factors.push({ factor: 'Contains login form', weight: 10 });
  }

  // Sensitive fields
  if (loginAnalysis.hasSensitiveFields) {
    score += 20;
    factors.push({ factor: 'Requests sensitive information', weight: 20 });
  }

  // Suspicious form actions
  if (loginAnalysis.suspiciousFormActions.length > 0) {
    score += 25;
    factors.push({ 
      factor: 'Form submits data to suspicious destination', 
      weight: 25 
    });
  }

  // Brand impersonation
  if (brandAnalysis.isImpersonation) {
    score += 40;
    factors.push({ 
      factor: `Possible ${brandAnalysis.impersonatedBrand} impersonation`, 
      weight: 40 
    });
  }

  // Phishing indicators
  score += phishingAnalysis.score;
  for (const indicator of phishingAnalysis.indicators) {
    factors.push({ factor: indicator.detail, weight: 10 });
  }

  // Cap and determine risk level
  score = Math.min(score, 100);
  
  let riskLevel;
  if (score < 30) {
    riskLevel = 'safe';
  } else if (score < 60) {
    riskLevel = 'suspicious';
  } else {
    riskLevel = 'dangerous';
  }

  return {
    riskScore: score,
    riskLevel,
    isScam: score >= 60,
    loginAnalysis,
    brandAnalysis,
    phishingAnalysis,
    factors,
    scamType: brandAnalysis.isImpersonation 
      ? `Brand Impersonation (${brandAnalysis.impersonatedBrand})` 
      : loginAnalysis.hasSensitiveFields 
        ? 'Credential Harvesting'
        : phishingAnalysis.score > 30 
          ? 'Phishing'
          : 'Unknown'
  };
}

export default {
  analyzeWebsiteContent,
  analyzeLoginForms,
  detectBrandImpersonation,
  analyzePhishingIndicators
};
