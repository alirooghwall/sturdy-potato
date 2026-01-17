/**
 * Risk Scoring Engine
 * Combines all analysis modules to produce final risk assessment
 */

import { analyzeUrl } from './urlAnalyzer.js';
import { analyzeMessage } from './messageAnalyzer.js';
import { analyzeWebsiteContent } from './websiteAnalyzer.js';

/**
 * Risk level thresholds
 */
const RISK_THRESHOLDS = {
  safe: { max: 29, color: '#22c55e', label: 'Safe' },
  suspicious: { max: 59, color: '#f59e0b', label: 'Suspicious' },
  dangerous: { max: 100, color: '#ef4444', label: 'Dangerous' }
};

/**
 * Get risk level from score
 * @param {number} score - Risk score (0-100)
 * @returns {Object} - Risk level details
 */
export function getRiskLevel(score) {
  if (score <= RISK_THRESHOLDS.safe.max) {
    return { ...RISK_THRESHOLDS.safe, level: 'safe' };
  } else if (score <= RISK_THRESHOLDS.suspicious.max) {
    return { ...RISK_THRESHOLDS.suspicious, level: 'suspicious' };
  } else {
    return { ...RISK_THRESHOLDS.dangerous, level: 'dangerous' };
  }
}

/**
 * Combine URL and website content analysis
 * @param {string} url - URL to analyze
 * @param {Object} pageData - Page content data
 * @returns {Promise<Object>} - Combined analysis result
 */
export async function analyzeWebsite(url, pageData = null) {
  // Analyze URL
  const urlAnalysis = await analyzeUrl(url);
  
  // If no page data, return URL analysis only
  if (!pageData) {
    return {
      url,
      riskScore: urlAnalysis.riskScore,
      riskLevel: urlAnalysis.riskLevel,
      isScam: urlAnalysis.isScam,
      confidence: urlAnalysis.confidence,
      scamType: urlAnalysis.detectedBrand 
        ? `Brand Impersonation (${urlAnalysis.detectedBrand})`
        : 'Phishing',
      explanation: urlAnalysis.explanation,
      factors: urlAnalysis.factors,
      urlAnalysis
    };
  }

  // Analyze website content
  const contentAnalysis = analyzeWebsiteContent({
    ...pageData,
    url
  });

  // Combine scores (weighted average with URL having more weight for domain issues)
  let combinedScore;
  if (urlAnalysis.riskScore > 50 || contentAnalysis.riskScore > 50) {
    // Take higher score if either is high
    combinedScore = Math.max(urlAnalysis.riskScore, contentAnalysis.riskScore);
  } else {
    // Average for lower risk items
    combinedScore = Math.round((urlAnalysis.riskScore * 0.4) + (contentAnalysis.riskScore * 0.6));
  }

  // Combine factors
  const allFactors = [
    ...urlAnalysis.factors.map(f => ({ ...f, source: 'url' })),
    ...contentAnalysis.factors.map(f => ({ ...f, source: 'content' }))
  ];

  // Determine scam type
  let scamType = 'Unknown';
  if (contentAnalysis.brandAnalysis?.isImpersonation) {
    scamType = `Brand Impersonation (${contentAnalysis.brandAnalysis.impersonatedBrand})`;
  } else if (urlAnalysis.detectedBrand) {
    scamType = `Suspected ${urlAnalysis.detectedBrand} Phishing`;
  } else if (contentAnalysis.loginAnalysis?.hasSensitiveFields) {
    scamType = 'Credential Harvesting';
  } else if (combinedScore > 50) {
    scamType = 'Phishing';
  }

  // Generate combined explanation
  const explanation = generateCombinedExplanation(urlAnalysis, contentAnalysis, combinedScore);

  const riskLevel = getRiskLevel(combinedScore);

  return {
    url,
    riskScore: combinedScore,
    riskLevel: riskLevel.level,
    isScam: combinedScore >= 60,
    confidence: Math.round((urlAnalysis.confidence + (contentAnalysis.riskScore > 0 ? 70 : 50)) / 2),
    scamType,
    explanation,
    factors: allFactors,
    urlAnalysis,
    contentAnalysis
  };
}

/**
 * Generate combined explanation from URL and content analysis
 */
function generateCombinedExplanation(urlAnalysis, contentAnalysis, score) {
  const explanations = [];
  const riskLevel = getRiskLevel(score);

  if (riskLevel.level === 'safe') {
    explanations.push('✅ This website appears to be safe.');
    explanations.push('');
    explanations.push('No major red flags detected, but always be careful:');
    explanations.push('• Never share passwords via email or messages');
    explanations.push('• Verify URLs before entering sensitive info');
    return explanations.join('\n');
  }

  if (riskLevel.level === 'dangerous') {
    explanations.push('🚨 **HIGH RISK - Likely Scam or Phishing**');
  } else {
    explanations.push('⚠️ **Proceed with Caution**');
  }
  explanations.push('');

  // Add URL-based warnings
  if (urlAnalysis.detectedBrand) {
    explanations.push(`🎭 **Possible ${urlAnalysis.detectedBrand} Impersonation**`);
    explanations.push(`   This site might be pretending to be ${urlAnalysis.detectedBrand}.`);
    explanations.push('');
  }

  if (!urlAnalysis.domainAnalysis?.isHttps) {
    explanations.push('🔓 **No Secure Connection**');
    explanations.push('   This site doesn\'t use HTTPS encryption.');
    explanations.push('');
  }

  // Add content-based warnings
  if (contentAnalysis.brandAnalysis?.isImpersonation) {
    explanations.push(`🎭 **Brand Impersonation Detected**`);
    explanations.push(`   Page contains ${contentAnalysis.brandAnalysis.impersonatedBrand} branding but isn't their official site.`);
    explanations.push('');
  }

  if (contentAnalysis.loginAnalysis?.hasSensitiveFields) {
    explanations.push('🔐 **Requests Sensitive Information**');
    explanations.push('   This page asks for sensitive data like passwords or financial info.');
    explanations.push('');
  }

  if (contentAnalysis.loginAnalysis?.suspiciousFormActions?.length > 0) {
    explanations.push('📤 **Suspicious Form Destination**');
    explanations.push('   Data entered here may be sent to an unknown location.');
    explanations.push('');
  }

  // Recommendations
  explanations.push('**What you should do:**');
  if (riskLevel.level === 'dangerous') {
    explanations.push('🛑 Do NOT enter any personal information');
    explanations.push('🚫 Do NOT log in or create an account');
    explanations.push('↩️ Leave this website immediately');
    explanations.push('✅ Go directly to the official website instead');
  } else {
    explanations.push('🔍 Double-check the URL is correct');
    explanations.push('🏠 Go to the official website directly instead of clicking links');
    explanations.push('❓ Contact the company through official channels if unsure');
  }

  return explanations.join('\n');
}

/**
 * Format analysis result for display
 * @param {Object} analysis - Analysis result
 * @returns {Object} - Formatted result
 */
export function formatAnalysisResult(analysis) {
  const riskLevel = getRiskLevel(analysis.riskScore);
  
  return {
    risk_score: analysis.riskScore,
    scam_type: analysis.scamType || 'Unknown',
    is_scam: analysis.isScam,
    explanation: analysis.explanation,
    confidence: `${analysis.confidence}%`,
    risk_level: riskLevel.level,
    risk_color: riskLevel.color,
    risk_label: riskLevel.label
  };
}

/**
 * Perform quick URL-only analysis (for speed)
 * @param {string} url - URL to analyze
 * @returns {Promise<Object>} - Quick analysis result
 */
export async function quickUrlAnalysis(url) {
  const result = await analyzeUrl(url);
  return formatAnalysisResult(result);
}

/**
 * Perform message analysis
 * @param {string} text - Message text
 * @returns {Object} - Analysis result
 */
export function analyzeMessageContent(text) {
  const result = analyzeMessage(text);
  return formatAnalysisResult(result);
}

export default {
  analyzeWebsite,
  analyzeMessageContent,
  quickUrlAnalysis,
  formatAnalysisResult,
  getRiskLevel
};
