/**
 * Scam Shield - Main Module Export
 * AI-Powered Phishing, Fraud, and Scam Detection Platform
 */

export { analyzeUrl, analyzeDomain, expandUrl } from './analysis/urlAnalyzer.js';
export { analyzeMessage, detectPatterns, classifyScamType } from './analysis/messageAnalyzer.js';
export { analyzeWebsiteContent, analyzeLoginForms, detectBrandImpersonation } from './analysis/websiteAnalyzer.js';
export { analyzeWebsite, analyzeMessageContent, quickUrlAnalysis, getRiskLevel, formatAnalysisResult } from './analysis/riskScoring.js';
export { createReport, saveReport, getReports, checkReported, REPORT_TYPES } from './analysis/reporting.js';
