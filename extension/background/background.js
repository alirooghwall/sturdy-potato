/**
 * Scam Shield - Background Service Worker
 * Handles URL analysis and messaging between components
 */

// Import analysis modules
import { analyzeUrl } from '../lib/urlAnalyzer.js';
import { analyzeMessage } from '../lib/messageAnalyzer.js';
import { analyzeWebsite } from '../lib/riskScoring.js';
import { cacheAnalysisResult, getCachedResult, saveReport, createReport, REPORT_TYPES } from '../lib/reporting.js';

// Listen for messages from popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  handleMessage(request, sender).then(sendResponse);
  return true; // Keep channel open for async response
});

/**
 * Handle incoming messages
 */
async function handleMessage(request, sender) {
  const { action, data } = request;

  try {
    switch (action) {
      case 'analyzeUrl':
        return await handleAnalyzeUrl(data.url);

      case 'analyzeMessage':
        return handleAnalyzeMessage(data.text);

      case 'analyzeWebsite':
        return await handleAnalyzeWebsite(data.url, data.pageData);

      case 'reportSite':
        return await handleReportSite(data);

      case 'getAnalysisCache':
        return await getCachedResult(data.url);

      case 'getCurrentTab':
        return await getCurrentTab();

      default:
        return { success: false, error: 'Unknown action' };
    }
  } catch (error) {
    console.error('Background script error:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Handle URL analysis request
 */
async function handleAnalyzeUrl(url) {
  // Check cache first
  const cached = await getCachedResult(url);
  if (cached) {
    return { success: true, result: cached, cached: true };
  }

  // Analyze URL
  const result = await analyzeUrl(url);

  // Cache result
  await cacheAnalysisResult(url, result);

  return { success: true, result, cached: false };
}

/**
 * Handle message analysis request
 */
function handleAnalyzeMessage(text) {
  const result = analyzeMessage(text);
  return { success: true, result };
}

/**
 * Handle full website analysis
 */
async function handleAnalyzeWebsite(url, pageData) {
  // Check cache for quick URL analysis
  const cached = await getCachedResult(url);
  if (cached && !pageData) {
    return { success: true, result: cached, cached: true };
  }

  // Perform analysis
  const result = await analyzeWebsite(url, pageData);

  // Cache result
  await cacheAnalysisResult(url, result);

  return { success: true, result, cached: false };
}

/**
 * Handle site report
 */
async function handleReportSite(data) {
  const { url, type = REPORT_TYPES.URL, description = '' } = data;
  
  const report = createReport(type, url, description);
  const saved = await saveReport(report);

  return { 
    success: saved, 
    report: saved ? report : null,
    error: saved ? null : 'Failed to save report'
  };
}

/**
 * Get current active tab
 */
async function getCurrentTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tabs.length > 0) {
    return { success: true, tab: tabs[0] };
  }
  return { success: false, error: 'No active tab found' };
}

// Listen for tab updates to auto-analyze
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    // Skip chrome:// and internal URLs
    if (tab.url.startsWith('chrome://') || 
        tab.url.startsWith('chrome-extension://') ||
        tab.url.startsWith('about:')) {
      return;
    }

    try {
      // Quick URL analysis for badge update
      const result = await analyzeUrl(tab.url);
      
      // Update extension badge based on risk level
      updateBadge(tabId, result.riskLevel, result.riskScore);
      
      // Cache the result
      await cacheAnalysisResult(tab.url, result);
    } catch (error) {
      console.error('Auto-analysis error:', error);
    }
  }
});

/**
 * Update extension badge based on risk level
 */
function updateBadge(tabId, riskLevel, score) {
  const badges = {
    safe: { color: '#22c55e', text: '' },
    suspicious: { color: '#f59e0b', text: '!' },
    dangerous: { color: '#ef4444', text: '!!' }
  };

  const badge = badges[riskLevel] || badges.safe;

  chrome.action.setBadgeBackgroundColor({ 
    color: badge.color, 
    tabId 
  });
  
  chrome.action.setBadgeText({ 
    text: badge.text, 
    tabId 
  });
}

// Initialize on install
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('Scam Shield installed successfully!');
    
    // Set default settings
    chrome.storage.local.set({
      settings: {
        autoScan: true,
        showNotifications: true,
        language: 'en'
      }
    });
  }
});

console.log('Scam Shield background service worker started');
