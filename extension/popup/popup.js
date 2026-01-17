/**
 * Scam Shield - Popup Script
 * Handles popup UI interactions
 */

// DOM Elements
const statusIconWrapper = document.getElementById('status-icon-wrapper');
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
const resultsIconWrapper = document.getElementById('results-icon-wrapper');
const reportBtn = document.getElementById('report-btn');

// SVG Icons
const ICONS = {
  loading: `<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 6V12L16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>`,
  safe: `<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M22 4L12 14.01l-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`,
  warning: `<path d="M12 9V13M12 17H12.01M10.29 3.86L1.82 18A2 2 0 0 0 3.54 21H20.46A2 2 0 0 0 22.18 18L13.71 3.86A2 2 0 0 0 10.29 3.86Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`,
  danger: `<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M15 9L9 15M9 9L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>`,
  error: `<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 8V12M12 16H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>`,
  info: `<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 16V12M12 8H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>`
};

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

  updateStatus('analyzing', 'Analyzing', 'Checking for scam indicators...');
  scanBtn.disabled = true;
  scanBtn.classList.add('loading');

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
    scanBtn.classList.remove('loading');
  }
}

/**
 * Display URL analysis result
 */
function displayUrlAnalysis(result) {
  const { riskLevel, riskScore: score, explanation, scamType } = result;

  // Update status
  const statusConfig = {
    safe: { icon: 'safe', text: 'Safe', class: 'status-safe' },
    suspicious: { icon: 'warning', text: 'Suspicious', class: 'status-suspicious' },
    dangerous: { icon: 'danger', text: 'Dangerous', class: 'status-dangerous' }
  };

  const status = statusConfig[riskLevel] || statusConfig.safe;
  
  statusCard.className = `status-card glass-card ${status.class}`;
  statusIcon.innerHTML = ICONS[status.icon];
  statusText.textContent = status.text;

  // Show risk score with animation
  riskScoreContainer.style.display = 'block';
  animateNumber(riskScore, 0, score, 800);
  
  // Animate score bar
  setTimeout(() => {
    scoreFill.style.width = `${score}%`;
  }, 100);

  // Show results if not safe
  if (riskLevel !== 'safe') {
    showResults(scamType || 'Warning Detected', explanation, riskLevel);
  } else {
    hideResults();
  }
}

/**
 * Animate number counting
 */
function animateNumber(element, start, end, duration) {
  const startTime = performance.now();
  
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const easeProgress = 1 - Math.pow(1 - progress, 3); // easeOutCubic
    
    const current = Math.round(start + (end - start) * easeProgress);
    element.textContent = current;
    
    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }
  
  requestAnimationFrame(update);
}

/**
 * Update status display
 */
function updateStatus(type, text, detail) {
  const iconMap = {
    analyzing: 'loading',
    safe: 'safe',
    suspicious: 'warning',
    dangerous: 'danger',
    error: 'error',
    skip: 'info'
  };

  statusIcon.innerHTML = ICONS[iconMap[type]] || ICONS.loading;
  statusText.textContent = text;
  siteUrl.textContent = detail || siteUrl.textContent;
  
  if (type === 'analyzing') {
    statusCard.className = 'status-card glass-card analyzing';
    riskScoreContainer.style.display = 'none';
  }
}

/**
 * Display error state
 */
function displayError(message) {
  updateStatus('error', 'Error', message);
}

/**
 * Analyze message text
 */
async function analyzeMessage() {
  const text = messageInput.value.trim();
  
  if (!text) {
    showNotification('Please enter a message to analyze');
    return;
  }

  analyzeBtn.disabled = true;
  analyzeBtn.classList.add('loading');

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
    showResults('Analysis Error', 'Failed to analyze message: ' + error.message, 'error');
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.classList.remove('loading');
  }
}

/**
 * Display message analysis result
 */
function displayMessageAnalysis(result) {
  const { riskLevel, riskScore: score, scamType, explanation, confidence } = result;

  const title = scamType || 'Analysis Complete';
  
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

  showResults(title, content, riskLevel, true);
}

/**
 * Show results section
 */
function showResults(title, content, level = 'warning', isHtml = false) {
  resultTitle.textContent = title;
  
  // Update icon based on level
  const iconMap = {
    safe: 'safe',
    suspicious: 'warning',
    dangerous: 'danger',
    warning: 'warning',
    error: 'error'
  };
  
  if (resultsIconWrapper) {
    resultsIconWrapper.querySelector('svg').innerHTML = ICONS[iconMap[level]] || ICONS.warning;
  }
  
  // Update results card class
  analysisResults.className = `results glass-card ${level === 'safe' ? 'success' : level === 'dangerous' ? 'danger' : ''}`;
  
  if (isHtml) {
    resultContent.innerHTML = content;
  } else {
    resultContent.innerHTML = `<div style="white-space: pre-wrap;">${escapeHtml(content)}</div>`;
  }
  
  analysisResults.style.display = 'block';
  
  // Trigger animation
  analysisResults.style.animation = 'none';
  analysisResults.offsetHeight; // Trigger reflow
  analysisResults.style.animation = 'fadeInUp 0.3s ease';
}

/**
 * Hide results section
 */
function hideResults() {
  analysisResults.style.display = 'none';
}

/**
 * Show notification (instead of alert)
 */
function showNotification(message) {
  // For now, use alert. Could be enhanced with a toast notification
  alert(message);
}

/**
 * Report current site
 */
async function reportSite() {
  if (!currentUrl || !isValidUrl(currentUrl)) {
    showNotification('Cannot report this page');
    return;
  }

  const description = prompt('Why are you reporting this site? (optional)');
  
  if (description === null) {
    return; // User cancelled
  }

  reportBtn.disabled = true;
  reportBtn.classList.add('loading');

  try {
    const response = await chrome.runtime.sendMessage({
      action: 'reportSite',
      data: {
        url: currentUrl,
        description: description || 'User reported as suspicious'
      }
    });

    if (response.success) {
      showNotification('Report submitted successfully. Thank you for helping protect others!');
      reportBtn.querySelector('span').textContent = 'Reported';
    } else {
      throw new Error(response.error || 'Failed to submit report');
    }
  } catch (error) {
    console.error('Report error:', error);
    showNotification('Failed to submit report. Please try again.');
    reportBtn.disabled = false;
  } finally {
    reportBtn.classList.remove('loading');
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
  
  // Add focus effects for textarea
  messageInput.addEventListener('focus', () => {
    messageInput.parentElement.classList.add('focused');
  });
  
  messageInput.addEventListener('blur', () => {
    messageInput.parentElement.classList.remove('focused');
  });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
