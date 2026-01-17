/**
 * Website Analyzer Tests
 */

import { analyzeWebsiteContent, analyzeLoginForms, detectBrandImpersonation, analyzePhishingIndicators } from '../src/analysis/websiteAnalyzer.js';

describe('Website Analyzer', () => {
  describe('analyzeLoginForms', () => {
    test('detects login form presence', () => {
      const pageData = {
        url: 'https://example.com',
        text: 'Please login with your username and password',
        forms: [],
        inputs: []
      };
      const result = analyzeLoginForms(pageData);
      expect(result.hasLoginForm).toBe(true);
    });

    test('detects sensitive fields', () => {
      const pageData = {
        url: 'https://example.com',
        text: 'Enter your credit card number and SSN',
        forms: [],
        inputs: []
      };
      const result = analyzeLoginForms(pageData);
      expect(result.hasSensitiveFields).toBe(true);
    });

    test('detects suspicious form actions', () => {
      const pageData = {
        url: 'https://example.com',
        text: 'Login',
        forms: [
          { action: 'https://evil-site.com/steal', method: 'POST' }
        ],
        inputs: []
      };
      const result = analyzeLoginForms(pageData);
      expect(result.suspiciousFormActions.length).toBeGreaterThan(0);
    });

    test('counts password fields', () => {
      const pageData = {
        url: 'https://example.com',
        text: '',
        forms: [],
        inputs: [
          { type: 'password', name: 'password' },
          { type: 'password', name: 'confirm_password' }
        ]
      };
      const result = analyzeLoginForms(pageData);
      expect(result.passwordFields).toBe(2);
    });
  });

  describe('detectBrandImpersonation', () => {
    test('detects PayPal impersonation', () => {
      const pageData = {
        url: 'https://pay-pal-secure.com',
        text: 'Welcome to PayPal. Pay with PayPal for secure transactions.',
        images: [{ src: 'paypal-logo.png', alt: 'PayPal Logo' }]
      };
      const result = detectBrandImpersonation(pageData);
      expect(result.isImpersonation).toBe(true);
      expect(result.impersonatedBrand).toBe('PayPal');
    });

    test('does not flag legitimate sites', () => {
      const pageData = {
        url: 'https://www.paypal.com',
        text: 'Welcome to PayPal',
        images: []
      };
      const result = detectBrandImpersonation(pageData);
      expect(result.isImpersonation).toBe(false);
    });

    test('detects Google impersonation', () => {
      const pageData = {
        url: 'https://google-login-verify.com',
        text: 'Sign in with Google. Enter your Google account credentials.',
        images: [{ src: 'g-logo.png', alt: 'Google' }]
      };
      const result = detectBrandImpersonation(pageData);
      expect(result.isImpersonation).toBe(true);
      expect(result.impersonatedBrand).toBe('Google');
    });
  });

  describe('analyzePhishingIndicators', () => {
    test('detects urgency language', () => {
      const pageData = {
        url: 'https://example.com',
        text: 'Your account has been suspended! Verify immediately within 24 hours or your account will be closed.',
        title: 'Account Suspended'
      };
      const result = analyzePhishingIndicators(pageData);
      expect(result.indicators.length).toBeGreaterThan(0);
      expect(result.score).toBeGreaterThan(0);
    });

    test('detects suspicious requests', () => {
      const pageData = {
        url: 'https://example.com',
        text: 'Please enter your password and confirm your identity to update payment information.',
        title: 'Update Account'
      };
      const result = analyzePhishingIndicators(pageData);
      expect(result.indicators.some(i => i.type === 'request')).toBe(true);
    });
  });

  describe('analyzeWebsiteContent', () => {
    test('returns safe for benign content', () => {
      const pageData = {
        url: 'https://example.com',
        text: 'Welcome to our website. Browse our products and services.',
        forms: [],
        inputs: [],
        images: []
      };
      const result = analyzeWebsiteContent(pageData);
      expect(result.riskLevel).toBe('safe');
    });

    test('returns dangerous for phishing content', () => {
      const pageData = {
        url: 'https://paypal-secure-verify.xyz',
        text: 'Your PayPal account has been suspended! Enter your password immediately to verify your identity and credit card information.',
        forms: [{ action: 'https://evil.com/steal' }],
        inputs: [{ type: 'password' }],
        images: [{ src: 'paypal-logo.png', alt: 'PayPal' }]
      };
      const result = analyzeWebsiteContent(pageData);
      expect(result.riskLevel).toBe('dangerous');
      expect(result.isScam).toBe(true);
    });

    test('returns required fields', () => {
      const pageData = {
        url: 'https://example.com',
        text: '',
        forms: [],
        inputs: [],
        images: []
      };
      const result = analyzeWebsiteContent(pageData);
      expect(result).toHaveProperty('riskScore');
      expect(result).toHaveProperty('riskLevel');
      expect(result).toHaveProperty('isScam');
      expect(result).toHaveProperty('factors');
      expect(result).toHaveProperty('scamType');
    });
  });
});
