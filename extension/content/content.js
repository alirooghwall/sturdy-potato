/**
 * Scam Shield - Content Script
 * Injects warning banners and scans page content
 */

// Prevent double injection
if (window.scamShieldInjected) {
  console.log('Scam Shield already active');
} else {
  window.scamShieldInjected = true;
  
  /**
   * Initialize content script
   */
  function init() {
    // Request analysis from background script
    requestAnalysis();
    
    // Listen for messages from background/popup
    chrome.runtime.onMessage.addListener(handleMessage);
  }

  /**
   * Request page analysis from background script
   */
  async function requestAnalysis() {
    try {
      // Collect page data for analysis
      const pageData = collectPageData();
      
      // Send to background script
      const response = await chrome.runtime.sendMessage({
        action: 'analyzeWebsite',
        data: {
          url: window.location.href,
          pageData
        }
      });

      if (response.success && response.result) {
        handleAnalysisResult(response.result);
      }
    } catch (error) {
      console.error('Scam Shield analysis error:', error);
    }
  }

  /**
   * Collect page data for analysis
   */
  function collectPageData() {
    // Get all forms
    const forms = Array.from(document.forms).map(form => ({
      action: form.action,
      method: form.method,
      id: form.id,
      name: form.name
    }));

    // Get all inputs
    const inputs = Array.from(document.querySelectorAll('input')).map(input => ({
      type: input.type,
      name: input.name,
      id: input.id,
      placeholder: input.placeholder
    }));

    // Get images (for logo detection)
    const images = Array.from(document.images).slice(0, 20).map(img => ({
      src: img.src,
      alt: img.alt,
      className: img.className
    }));

    // Get page text (limited)
    const textContent = document.body?.innerText?.substring(0, 5000) || '';

    return {
      url: window.location.href,
      title: document.title,
      forms,
      inputs,
      images,
      text: textContent
    };
  }

  /**
   * Handle analysis result
   */
  function handleAnalysisResult(result) {
    // Only show banner for suspicious or dangerous sites
    if (result.riskLevel === 'suspicious' || result.riskLevel === 'dangerous') {
      showWarningBanner(result);
    }
  }

  /**
   * Show warning banner at top of page
   */
  function showWarningBanner(result) {
    // Remove existing banner if any
    const existingBanner = document.getElementById('scam-shield-banner');
    if (existingBanner) {
      existingBanner.remove();
    }

    // Create banner element
    const banner = document.createElement('div');
    banner.id = 'scam-shield-banner';
    banner.className = `scam-shield-banner scam-shield-${result.riskLevel}`;
    
    const isDangerous = result.riskLevel === 'dangerous';
    const icon = isDangerous ? '🚨' : '⚠️';
    const title = isDangerous ? 'Warning: Potential Scam Detected!' : 'Caution: Suspicious Website';
    
    banner.innerHTML = `
      <div class="scam-shield-content">
        <div class="scam-shield-icon">${icon}</div>
        <div class="scam-shield-text">
          <strong>${title}</strong>
          <p>${getShortExplanation(result)}</p>
        </div>
        <div class="scam-shield-actions">
          <button class="scam-shield-btn scam-shield-btn-details" id="scam-shield-details">
            Learn More
          </button>
          <button class="scam-shield-btn scam-shield-btn-close" id="scam-shield-close">
            ✕
          </button>
        </div>
      </div>
      <div class="scam-shield-details" id="scam-shield-details-panel" style="display: none;">
        <div class="scam-shield-details-content">
          <h4>Risk Score: ${result.riskScore}/100</h4>
          <p class="scam-shield-explanation">${result.explanation?.replace(/\n/g, '<br>') || 'No details available'}</p>
        </div>
      </div>
    `;

    // Insert at top of body
    document.body.insertBefore(banner, document.body.firstChild);

    // Add margin to body to prevent content overlap
    document.body.style.marginTop = '60px';

    // Add event listeners
    document.getElementById('scam-shield-close').addEventListener('click', () => {
      banner.remove();
      document.body.style.marginTop = '';
    });

    document.getElementById('scam-shield-details').addEventListener('click', () => {
      const panel = document.getElementById('scam-shield-details-panel');
      panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    });
  }

  /**
   * Get short explanation for banner
   */
  function getShortExplanation(result) {
    if (result.scamType && result.scamType !== 'Unknown') {
      return `This site shows signs of ${result.scamType.toLowerCase()}. Be careful with your personal information.`;
    }
    if (result.riskLevel === 'dangerous') {
      return 'This website has multiple scam indicators. Do not enter personal information.';
    }
    return 'This website has some suspicious characteristics. Proceed with caution.';
  }

  /**
   * Handle messages from background/popup
   */
  function handleMessage(request, sender, sendResponse) {
    if (request.action === 'getPageData') {
      sendResponse({ pageData: collectPageData() });
    } else if (request.action === 'showBanner') {
      showWarningBanner(request.data);
      sendResponse({ success: true });
    } else if (request.action === 'hideBanner') {
      const banner = document.getElementById('scam-shield-banner');
      if (banner) {
        banner.remove();
        document.body.style.marginTop = '';
      }
      sendResponse({ success: true });
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}
