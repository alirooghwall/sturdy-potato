/**
 * URL Analysis Module
 * Analyzes URLs for phishing, domain age, and reputation
 */

// Known phishing patterns and suspicious TLDs
const SUSPICIOUS_TLDS = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work', '.click', '.link', '.info'];
const KNOWN_BRANDS = ['paypal', 'amazon', 'google', 'facebook', 'apple', 'microsoft', 'netflix', 'bank', 'chase', 'wellsfargo', 'citibank', 'usps', 'fedex', 'ups', 'dhl'];
const SUSPICIOUS_KEYWORDS = ['login', 'signin', 'verify', 'secure', 'account', 'update', 'confirm', 'banking', 'password', 'credential'];

/**
 * Expand shortened URLs
 * @param {string} url - URL to expand
 * @returns {Promise<string>} - Expanded URL
 */
export async function expandUrl(url) {
  const shorteners = ['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly', 'adf.ly', 'tiny.cc'];
  
  try {
    const urlObj = new URL(url);
    if (shorteners.some(s => urlObj.hostname.includes(s))) {
      // In a real implementation, we would follow redirects
      // For now, flag it as suspicious
      return { original: url, expanded: url, isShortened: true };
    }
    return { original: url, expanded: url, isShortened: false };
  } catch {
    return { original: url, expanded: url, isShortened: false };
  }
}

/**
 * Analyze domain characteristics
 * @param {string} url - URL to analyze
 * @returns {Object} - Domain analysis results
 */
export function analyzeDomain(url) {
  const result = {
    domain: '',
    tld: '',
    isSuspiciousTld: false,
    hasIpAddress: false,
    hasManySubdomains: false,
    hasLongSubdomain: false,
    containsBrandName: false,
    detectedBrand: null,
    domainLength: 0,
    hasNumbers: false,
    hasHyphens: false,
    isHttps: false,
    suspiciousPatterns: []
  };

  try {
    const urlObj = new URL(url);
    result.domain = urlObj.hostname;
    result.isHttps = urlObj.protocol === 'https:';
    
    // Check for IP address
    const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    result.hasIpAddress = ipPattern.test(urlObj.hostname);
    
    // Analyze TLD
    const tldMatch = urlObj.hostname.match(/\.[a-z]+$/i);
    if (tldMatch) {
      result.tld = tldMatch[0].toLowerCase();
      result.isSuspiciousTld = SUSPICIOUS_TLDS.includes(result.tld);
    }
    
    // Check subdomains
    const parts = urlObj.hostname.split('.');
    result.hasManySubdomains = parts.length > 3;
    result.hasLongSubdomain = parts.some(p => p.length > 20);
    
    // Check for brand impersonation
    const lowerDomain = urlObj.hostname.toLowerCase();
    for (const brand of KNOWN_BRANDS) {
      if (lowerDomain.includes(brand)) {
        // Check if it's the legitimate domain
        const legitimatePatterns = [
          new RegExp(`^${brand}\\.com$`),
          new RegExp(`^www\\.${brand}\\.com$`),
          new RegExp(`^${brand}\\.net$`),
          new RegExp(`^${brand}\\.org$`),
          new RegExp(`^[a-z]+\\.${brand}\\.com$`),  // subdomains of brand.com
          new RegExp(`\\.${brand}\\.com$`)  // any subdomain ending in .brand.com
        ];
        const isLegitimate = legitimatePatterns.some(pattern => pattern.test(lowerDomain));
        if (!isLegitimate) {
          result.containsBrandName = true;
          result.detectedBrand = brand;
          result.suspiciousPatterns.push(`Contains "${brand}" but isn't the official website`);
        }
        break;
      }
    }
    
    // Domain characteristics
    result.domainLength = urlObj.hostname.length;
    result.hasNumbers = /\d/.test(urlObj.hostname);
    result.hasHyphens = urlObj.hostname.includes('-');
    
    // Check for suspicious patterns in path
    const pathLower = urlObj.pathname.toLowerCase();
    for (const keyword of SUSPICIOUS_KEYWORDS) {
      if (pathLower.includes(keyword)) {
        result.suspiciousPatterns.push(`URL path contains "${keyword}"`);
      }
    }
    
    // Check for lookalike patterns (only if not already flagged as brand impersonation)
    // These detect character substitution tricks like g00gle, paypa1, etc.
    if (!result.containsBrandName) {
      const lookalikes = [
        { pattern: /paypa[1i]|paypai/i, brand: 'PayPal' },
        { pattern: /arnaz[o0]n|amaz[o0]n(?!\.)/i, brand: 'Amazon' },
        { pattern: /g[o0]{2}gle|go[o0]g1e/i, brand: 'Google' },
        { pattern: /faceb[o0]{2}k|facebo[o0]k/i, brand: 'Facebook' },
        { pattern: /micr[o0]s[o0]ft|micros0ft/i, brand: 'Microsoft' },
        { pattern: /netf1ix|netfl1x/i, brand: 'Netflix' },
        { pattern: /app1e|appie/i, brand: 'Apple' }
      ];
      
      for (const { pattern, brand } of lookalikes) {
        // Only flag if pattern matches AND it's not a legitimate domain
        const brandLower = brand.toLowerCase();
        const isLegit = lowerDomain === `${brandLower}.com` || 
                        lowerDomain === `www.${brandLower}.com` ||
                        lowerDomain.endsWith(`.${brandLower}.com`);
        
        if (pattern.test(lowerDomain) && !isLegit) {
          result.containsBrandName = true;
          result.detectedBrand = brand;
          result.suspiciousPatterns.push(`Domain uses lookalike characters for "${brand}"`);
          break;
        }
      }
    }
    
  } catch {
    result.suspiciousPatterns.push('Invalid URL format');
  }
  
  return result;
}

/**
 * Calculate URL risk score
 * @param {Object} domainAnalysis - Domain analysis results
 * @returns {Object} - Risk score and factors
 */
export function calculateUrlRiskScore(domainAnalysis) {
  let score = 0;
  const factors = [];
  
  // IP address instead of domain (high risk)
  if (domainAnalysis.hasIpAddress) {
    score += 35;
    factors.push({ factor: 'Uses IP address instead of domain name', weight: 35 });
  }
  
  // Suspicious TLD
  if (domainAnalysis.isSuspiciousTld) {
    score += 15;
    factors.push({ factor: `Suspicious domain extension (${domainAnalysis.tld})`, weight: 15 });
  }
  
  // Brand impersonation (high risk)
  if (domainAnalysis.containsBrandName) {
    score += 40;
    factors.push({ factor: `Possible impersonation of ${domainAnalysis.detectedBrand}`, weight: 40 });
  }
  
  // Many subdomains
  if (domainAnalysis.hasManySubdomains) {
    score += 10;
    factors.push({ factor: 'Unusually many subdomains', weight: 10 });
  }
  
  // Long subdomain
  if (domainAnalysis.hasLongSubdomain) {
    score += 10;
    factors.push({ factor: 'Unusually long subdomain', weight: 10 });
  }
  
  // No HTTPS
  if (!domainAnalysis.isHttps) {
    score += 15;
    factors.push({ factor: 'No secure connection (HTTPS)', weight: 15 });
  }
  
  // Very long domain
  if (domainAnalysis.domainLength > 30) {
    score += 5;
    factors.push({ factor: 'Unusually long domain name', weight: 5 });
  }
  
  // Suspicious patterns
  for (const pattern of domainAnalysis.suspiciousPatterns) {
    if (!factors.some(f => f.factor.includes(pattern))) {
      score += 10;
      factors.push({ factor: pattern, weight: 10 });
    }
  }
  
  // Cap score at 100
  score = Math.min(score, 100);
  
  return { score, factors };
}

/**
 * Main URL analysis function
 * @param {string} url - URL to analyze
 * @returns {Promise<Object>} - Complete analysis result
 */
export async function analyzeUrl(url) {
  const expandedInfo = await expandUrl(url);
  const domainAnalysis = analyzeDomain(expandedInfo.expanded);
  const { score, factors } = calculateUrlRiskScore(domainAnalysis);
  
  // Determine risk level
  let riskLevel;
  if (score < 30) {
    riskLevel = 'safe';
  } else if (score < 60) {
    riskLevel = 'suspicious';
  } else {
    riskLevel = 'dangerous';
  }
  
  // Generate explanation
  const explanation = generateUrlExplanation(riskLevel, factors, domainAnalysis);
  
  return {
    url: expandedInfo.original,
    expandedUrl: expandedInfo.expanded,
    isShortened: expandedInfo.isShortened,
    domain: domainAnalysis.domain,
    riskScore: score,
    riskLevel,
    isScam: score >= 60,
    confidence: Math.min(95, 50 + factors.length * 10),
    factors,
    explanation,
    detectedBrand: domainAnalysis.detectedBrand
  };
}

/**
 * Generate human-readable explanation
 */
function generateUrlExplanation(riskLevel, factors, domainAnalysis) {
  const explanations = [];
  
  if (riskLevel === 'safe') {
    explanations.push('✅ This website appears to be safe.');
    if (domainAnalysis.isHttps) {
      explanations.push('🔒 Uses secure HTTPS connection.');
    }
  } else {
    if (domainAnalysis.containsBrandName) {
      explanations.push(`⚠️ This site may be pretending to be ${domainAnalysis.detectedBrand}.`);
      explanations.push('🚨 Be careful - scammers often copy famous websites to steal your information.');
    }
    
    for (const { factor } of factors.slice(0, 3)) {
      explanations.push(`⚠️ ${factor}`);
    }
    
    if (riskLevel === 'dangerous') {
      explanations.push('🛑 We recommend NOT entering any personal information on this site.');
    } else {
      explanations.push('⚡ Proceed with caution and verify this is the real website.');
    }
  }
  
  return explanations.join('\n');
}

export default {
  analyzeUrl,
  analyzeDomain,
  expandUrl,
  calculateUrlRiskScore
};
