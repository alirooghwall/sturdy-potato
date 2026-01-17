/**
 * Community Reporting Module
 * Allows users to report suspicious URLs, phone numbers, and wallet addresses
 */

// Storage key for local reports
const REPORTS_STORAGE_KEY = 'scam_shield_reports';
const CACHE_STORAGE_KEY = 'scam_shield_cache';

/**
 * Report types
 */
export const REPORT_TYPES = {
  URL: 'url',
  PHONE: 'phone',
  WALLET: 'wallet',
  EMAIL: 'email'
};

/**
 * Create a new report
 * @param {string} type - Report type
 * @param {string} value - Reported value (URL, phone, etc.)
 * @param {string} description - Optional description
 * @returns {Object} - Report object
 */
export function createReport(type, value, description = '') {
  return {
    id: generateReportId(),
    type,
    value: normalizeValue(type, value),
    description,
    timestamp: Date.now(),
    status: 'pending'
  };
}

/**
 * Generate unique report ID
 */
function generateReportId() {
  return `report_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
}

/**
 * Normalize reported value
 */
function normalizeValue(type, value) {
  switch (type) {
    case REPORT_TYPES.URL:
      try {
        const url = new URL(value);
        return url.hostname.toLowerCase();
      } catch {
        return value.toLowerCase();
      }
    case REPORT_TYPES.PHONE:
      return value.replace(/[^0-9+]/g, '');
    case REPORT_TYPES.WALLET:
      return value.trim();
    case REPORT_TYPES.EMAIL:
      return value.toLowerCase().trim();
    default:
      return value;
  }
}

/**
 * Save report to local storage
 * @param {Object} report - Report to save
 * @returns {Promise<boolean>} - Success status
 */
export async function saveReport(report) {
  try {
    // Use chrome.storage if available, otherwise localStorage
    if (typeof chrome !== 'undefined' && chrome.storage) {
      const result = await chrome.storage.local.get(REPORTS_STORAGE_KEY);
      const reports = result[REPORTS_STORAGE_KEY] || [];
      reports.push(report);
      
      // Keep only last 100 reports
      const trimmedReports = reports.slice(-100);
      await chrome.storage.local.set({ [REPORTS_STORAGE_KEY]: trimmedReports });
    } else {
      const reports = JSON.parse(localStorage.getItem(REPORTS_STORAGE_KEY) || '[]');
      reports.push(report);
      const trimmedReports = reports.slice(-100);
      localStorage.setItem(REPORTS_STORAGE_KEY, JSON.stringify(trimmedReports));
    }
    return true;
  } catch (error) {
    console.error('Failed to save report:', error);
    return false;
  }
}

/**
 * Get all saved reports
 * @returns {Promise<Array>} - Array of reports
 */
export async function getReports() {
  try {
    if (typeof chrome !== 'undefined' && chrome.storage) {
      const result = await chrome.storage.local.get(REPORTS_STORAGE_KEY);
      return result[REPORTS_STORAGE_KEY] || [];
    } else {
      return JSON.parse(localStorage.getItem(REPORTS_STORAGE_KEY) || '[]');
    }
  } catch {
    return [];
  }
}

/**
 * Check if a value has been reported
 * @param {string} type - Report type
 * @param {string} value - Value to check
 * @returns {Promise<Object|null>} - Report if found, null otherwise
 */
export async function checkReported(type, value) {
  const normalizedValue = normalizeValue(type, value);
  const reports = await getReports();
  
  return reports.find(r => 
    r.type === type && r.value === normalizedValue
  ) || null;
}

/**
 * Get report statistics
 * @returns {Promise<Object>} - Statistics object
 */
export async function getReportStats() {
  const reports = await getReports();
  
  return {
    total: reports.length,
    byType: {
      [REPORT_TYPES.URL]: reports.filter(r => r.type === REPORT_TYPES.URL).length,
      [REPORT_TYPES.PHONE]: reports.filter(r => r.type === REPORT_TYPES.PHONE).length,
      [REPORT_TYPES.WALLET]: reports.filter(r => r.type === REPORT_TYPES.WALLET).length,
      [REPORT_TYPES.EMAIL]: reports.filter(r => r.type === REPORT_TYPES.EMAIL).length
    },
    lastReportTime: reports.length > 0 ? reports[reports.length - 1].timestamp : null
  };
}

/**
 * Cache analysis result
 * @param {string} url - URL analyzed
 * @param {Object} result - Analysis result
 */
export async function cacheAnalysisResult(url, result) {
  try {
    let domain;
    try {
      domain = new URL(url).hostname;
    } catch {
      domain = url;
    }

    const cacheEntry = {
      domain,
      result,
      timestamp: Date.now(),
      ttl: 3600000 // 1 hour TTL
    };

    if (typeof chrome !== 'undefined' && chrome.storage) {
      const cached = await chrome.storage.local.get(CACHE_STORAGE_KEY);
      const cache = cached[CACHE_STORAGE_KEY] || {};
      
      // Clean expired entries
      const now = Date.now();
      for (const key of Object.keys(cache)) {
        if (now - cache[key].timestamp > cache[key].ttl) {
          delete cache[key];
        }
      }
      
      cache[domain] = cacheEntry;
      
      // Limit cache size
      const keys = Object.keys(cache);
      if (keys.length > 500) {
        const oldestKey = keys.reduce((a, b) => 
          cache[a].timestamp < cache[b].timestamp ? a : b
        );
        delete cache[oldestKey];
      }
      
      await chrome.storage.local.set({ [CACHE_STORAGE_KEY]: cache });
    }
  } catch (error) {
    console.error('Failed to cache result:', error);
  }
}

/**
 * Get cached analysis result
 * @param {string} url - URL to look up
 * @returns {Promise<Object|null>} - Cached result or null
 */
export async function getCachedResult(url) {
  try {
    let domain;
    try {
      domain = new URL(url).hostname;
    } catch {
      domain = url;
    }

    if (typeof chrome !== 'undefined' && chrome.storage) {
      const cached = await chrome.storage.local.get(CACHE_STORAGE_KEY);
      const cache = cached[CACHE_STORAGE_KEY] || {};
      
      const entry = cache[domain];
      if (entry && Date.now() - entry.timestamp < entry.ttl) {
        return entry.result;
      }
    }
  } catch {
    // Cache miss
  }
  
  return null;
}

export default {
  createReport,
  saveReport,
  getReports,
  checkReported,
  getReportStats,
  cacheAnalysisResult,
  getCachedResult,
  REPORT_TYPES
};
