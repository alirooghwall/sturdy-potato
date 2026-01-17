/**
 * Scam Shield - Popup Script
 * Handles popup UI interactions
 */

// DOM Elements
const statusIcon = document.getElementById('status-icon');
const statusText = document.getElementById('status-text');
const siteUrl = document.getElementById('site-url');
const statusCard = document.getElementById('site-status');
const riskScoreContainer = document.getElementById('risk-score-container');
const riskScore = document.getElementById('risk-score');
const scoreFill = document.getElementById('score-fill');
const scanBtn = document.getElementById('scan-btn');
const messageInput = document.getElementById('message-input');
const analyzeBtn = document.getElementById('analyze-btn');
const analysisResults = document.getElementById('analysis-results');
const resultTitle = document.getElementById('result-title');
const resultContent = document.getElementById('result-content');
const reportBtn = document.getElementById('report-btn');

// Current tab URL
let currentUrl = '';
let currentAnalysis = null;

/**
 * Initialize popup
 */
async function init() {
  // Get current tab
  try {
    const response = await chrome.runtime.sendMessage({ action: 'getCurrentTab' });
    if (response.success && response.tab?.url) {
      currentUrl = response.tab.url;
      displayCurrentSite(response.tab);
      
      // Auto-analyze if it's a web page
      if (isValidUrl(currentUrl)) {
        await analyzeCurrentSite();
      }
    }
  } catch (error) {
    console.error('Failed to get current tab:', error);
    displayError('Unable to access current tab');
  }

  // Set up event listeners
  setupEventListeners();
}

/**
 * Check if URL is valid for analysis
 */
function isValidUrl(url) {
  return url && 
         !url.startsWith('chrome://') && 
         !url.startsWith('chrome-extension://') &&
         !url.startsWith('about:') &&
         !url.startsWith('edge://');
}

/**
 * Display current site info
 */
function displayCurrentSite(tab) {
  try {
    const url = new URL(tab.url);
    siteUrl.textContent = url.hostname;
  } catch {
    siteUrl.textContent = tab.url.substring(0, 40) + '...';
  }
}

/**
 * Analyze current site
 */
async function analyzeCurrentSite() {
  if (!isValidUrl(currentUrl)) {
    updateStatus('skip', 'Not a website', 'Extension pages cannot be analyzed');
    return;
  }

  updateStatus('analyzing', 'Analyzing...', 'Checking for scam indicators');
  scanBtn.disabled = true;

  try {
    // Request analysis from background script
    const response = await chrome.runtime.sendMessage({
      action: 'analyzeUrl',
      data: { url: currentUrl }
    });

    if (response.success && response.result) {
      currentAnalysis = response.result;
      displayUrlAnalysis(response.result);
    } else {
      throw new Error(response.error || 'Analysis failed');
    }
  } catch (error) {
    console.error('Analysis error:', error);
    updateStatus('error', 'Analysis Failed', error.message);
  } finally {
    scanBtn.disabled = false;
  }
}

/**
 * Display URL analysis result
 */
function displayUrlAnalysis(result) {
  const { riskLevel, riskScore: score, explanation, scamType } = result;

  // Update status
  const statusConfig = {
    safe: { icon: '✅', text: 'Safe', class: 'status-safe' },
    suspicious: { icon: '⚠️', text: 'Suspicious', class: 'status-suspicious' },
    dangerous: { icon: '🚨', text: 'Dangerous', class: 'status-dangerous' }
  };

  const status = statusConfig[riskLevel] || statusConfig.safe;
  
  statusCard.className = `status-card ${status.class}`;
  statusIcon.textContent = status.icon;
  statusText.textContent = status.text;

  // Show risk score
  riskScoreContainer.style.display = 'block';
  riskScore.textContent = score;
  scoreFill.style.width = `${score}%`;

  // Show results if not safe
  if (riskLevel !== 'safe') {
    showResults(`⚠️ ${scamType || 'Warning'}`, explanation);
  } else {
    hideResults();
  }
}

/**
 * Update status display
 */
function updateStatus(type, text, detail) {
  const icons = {
    analyzing: '⏳',
    safe: '✅',
    suspicious: '⚠️',
    dangerous: '🚨',
    error: '❌',
    skip: 'ℹ️'
  };

  statusIcon.textContent = icons[type] || '⏳';
  statusText.textContent = text;
  
  if (type === 'analyzing') {
    statusCard.className = 'status-card analyzing';
    riskScoreContainer.style.display = 'none';
  }
}

/**
 * Analyze message text
 */
async function analyzeMessage() {
  const text = messageInput.value.trim();
  
  if (!text) {
    alert('Please enter a message to analyze');
    return;
  }

  analyzeBtn.disabled = true;
  analyzeBtn.textContent = '⏳ Analyzing...';

  try {
    const response = await chrome.runtime.sendMessage({
      action: 'analyzeMessage',
      data: { text }
    });

    if (response.success && response.result) {
      displayMessageAnalysis(response.result);
    } else {
      throw new Error(response.error || 'Analysis failed');
    }
  } catch (error) {
    console.error('Message analysis error:', error);
    showResults('❌ Error', 'Failed to analyze message: ' + error.message);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = '🔎 Analyze Message';
  }
}

/**
 * Display message analysis result
 */
function displayMessageAnalysis(result) {
  const { riskLevel, riskScore: score, scamType, explanation, confidence } = result;

  const icons = {
    safe: '✅',
    suspicious: '⚠️',
    dangerous: '🚨'
  };

  const title = `${icons[riskLevel] || '⚠️'} ${scamType || 'Analysis Complete'}`;
  
  let content = `<div class="result-item">
    <div class="result-label">Risk Score</div>
    <div class="result-value"><strong>${score}/100</strong> (${riskLevel})</div>
  </div>`;

  content += `<div class="result-item">
    <div class="result-label">Confidence</div>
    <div class="result-value">${confidence}%</div>
  </div>`;

  content += `<div class="result-item">
    <div class="result-label">Analysis</div>
    <div class="result-value" style="white-space: pre-wrap;">${escapeHtml(explanation)}</div>
  </div>`;

  showResults(title, content, true);
}

/**
 * Show results section
 */
function showResults(title, content, isHtml = false) {
  resultTitle.textContent = title;
  
  if (isHtml) {
    resultContent.innerHTML = content;
  } else {
    resultContent.innerHTML = `<div style="white-space: pre-wrap;">${escapeHtml(content)}</div>`;
  }
  
  analysisResults.style.display = 'block';
}

/**
 * Hide results section
 */
function hideResults() {
  analysisResults.style.display = 'none';
}

/**
 * Report current site
 */
async function reportSite() {
  if (!currentUrl || !isValidUrl(currentUrl)) {
    alert('Cannot report this page');
    return;
  }

  const description = prompt('Why are you reporting this site? (optional)');
  
  if (description === null) {
    return; // User cancelled
  }

  reportBtn.disabled = true;
  reportBtn.textContent = '⏳ Reporting...';

  try {
    const response = await chrome.runtime.sendMessage({
      action: 'reportSite',
      data: {
        url: currentUrl,
        description: description || 'User reported as suspicious'
      }
    });

    if (response.success) {
      alert('✅ Thank you for your report! This helps protect others.');
      reportBtn.textContent = '✅ Reported';
    } else {
      throw new Error(response.error || 'Failed to submit report');
    }
  } catch (error) {
    console.error('Report error:', error);
    alert('Failed to submit report. Please try again.');
    reportBtn.textContent = '🚨 Report This Site';
    reportBtn.disabled = false;
  }
}

/**
 * Escape HTML for safe display
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  scanBtn.addEventListener('click', analyzeCurrentSite);
  analyzeBtn.addEventListener('click', analyzeMessage);
  reportBtn.addEventListener('click', reportSite);

  // Allow Enter key in textarea with Ctrl/Cmd
  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      analyzeMessage();
    }
  });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
