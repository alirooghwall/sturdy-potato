/**
 * URL Analyzer Tests
 */

import { analyzeUrl, analyzeDomain, expandUrl, calculateUrlRiskScore } from '../src/analysis/urlAnalyzer.js';

describe('URL Analyzer', () => {
  describe('analyzeDomain', () => {
    test('detects IP address URLs', () => {
      const result = analyzeDomain('http://192.168.1.1/login');
      expect(result.hasIpAddress).toBe(true);
    });

    test('detects suspicious TLDs', () => {
      const result = analyzeDomain('http://example.xyz/page');
      expect(result.isSuspiciousTld).toBe(true);
      expect(result.tld).toBe('.xyz');
    });

    test('detects HTTPS', () => {
      const httpsResult = analyzeDomain('https://example.com');
      expect(httpsResult.isHttps).toBe(true);

      const httpResult = analyzeDomain('http://example.com');
      expect(httpResult.isHttps).toBe(false);
    });

    test('detects brand impersonation in domain', () => {
      const result = analyzeDomain('http://paypal-secure-login.com/verify');
      expect(result.containsBrandName).toBe(true);
      expect(result.detectedBrand).toBe('paypal');
    });

    test('does not flag legitimate domains', () => {
      const result = analyzeDomain('https://www.paypal.com/login');
      expect(result.containsBrandName).toBe(false);
    });

    test('detects many subdomains', () => {
      const result = analyzeDomain('http://login.secure.account.example.com');
      expect(result.hasManySubdomains).toBe(true);
    });

    test('detects long subdomains', () => {
      const result = analyzeDomain('http://thisIsAVeryLongSubdomainThatShouldBeDetected.example.com');
      expect(result.hasLongSubdomain).toBe(true);
    });
  });

  describe('calculateUrlRiskScore', () => {
    test('returns high score for IP address', () => {
      const domainAnalysis = { hasIpAddress: true, isHttps: true, suspiciousPatterns: [] };
      const { score } = calculateUrlRiskScore(domainAnalysis);
      expect(score).toBeGreaterThanOrEqual(35);
    });

    test('returns high score for brand impersonation', () => {
      const domainAnalysis = { 
        containsBrandName: true, 
        detectedBrand: 'PayPal',
        isHttps: true,
        suspiciousPatterns: []
      };
      const { score } = calculateUrlRiskScore(domainAnalysis);
      expect(score).toBeGreaterThanOrEqual(40);
    });

    test('returns low score for safe domains', () => {
      const domainAnalysis = { 
        isHttps: true,
        isSuspiciousTld: false,
        hasIpAddress: false,
        containsBrandName: false,
        hasManySubdomains: false,
        hasLongSubdomain: false,
        domainLength: 15,
        suspiciousPatterns: []
      };
      const { score } = calculateUrlRiskScore(domainAnalysis);
      expect(score).toBeLessThan(30);
    });
  });

  describe('expandUrl', () => {
    test('identifies shortened URLs', async () => {
      const result = await expandUrl('https://bit.ly/abc123');
      expect(result.isShortened).toBe(true);
    });

    test('identifies regular URLs', async () => {
      const result = await expandUrl('https://example.com/page');
      expect(result.isShortened).toBe(false);
    });
  });

  describe('analyzeUrl', () => {
    test('returns safe for legitimate URLs', async () => {
      const result = await analyzeUrl('https://www.google.com');
      expect(result.riskLevel).toBe('safe');
      expect(result.isScam).toBe(false);
    });

    test('returns dangerous for suspicious URLs', async () => {
      const result = await analyzeUrl('http://192.168.1.1/paypal-login/verify.php');
      expect(result.riskLevel).toBe('dangerous');
      expect(result.isScam).toBe(true);
    });

    test('returns analysis with required fields', async () => {
      const result = await analyzeUrl('https://example.com');
      expect(result).toHaveProperty('url');
      expect(result).toHaveProperty('riskScore');
      expect(result).toHaveProperty('riskLevel');
      expect(result).toHaveProperty('isScam');
      expect(result).toHaveProperty('confidence');
      expect(result).toHaveProperty('explanation');
    });
  });
});
