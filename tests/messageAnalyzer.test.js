/**
 * Message Analyzer Tests
 */

import { analyzeMessage, detectPatterns, classifyScamType, calculateMessageRiskScore } from '../src/analysis/messageAnalyzer.js';

describe('Message Analyzer', () => {
  describe('detectPatterns', () => {
    test('detects urgency patterns', () => {
      const result = detectPatterns('Act now! This is urgent! Limited time offer expires today!');
      expect(result.urgency.length).toBeGreaterThan(0);
    });

    test('detects payment patterns', () => {
      const result = detectPatterns('Please send payment via gift card or bitcoin to receive your prize');
      expect(result.payment.length).toBeGreaterThan(0);
    });

    test('detects credential harvesting patterns', () => {
      const result = detectPatterns('Your account has been suspended. Click here to verify your password immediately.');
      expect(result.credential.length).toBeGreaterThan(0);
    });

    test('detects fake job patterns', () => {
      const result = detectPatterns('Work from home! Earn $5000 per week! No experience needed! Easy money!');
      expect(result.fakeJob.length).toBeGreaterThan(0);
    });

    test('detects MLM patterns', () => {
      const result = detectPatterns('Join our team! Build your downline! Limited slots available! Ground floor opportunity!');
      expect(result.mlm.length).toBeGreaterThan(0);
    });

    test('detects crypto scam patterns', () => {
      const result = detectPatterns('Guaranteed 10x returns on your bitcoin investment! Double your crypto today!');
      expect(result.crypto.length).toBeGreaterThan(0);
    });

    test('detects lottery scam patterns', () => {
      const result = detectPatterns('Congratulations! You have won $1 million in our lottery! Claim your prize now!');
      expect(result.lottery.length).toBeGreaterThan(0);
    });

    test('detects threat patterns', () => {
      const result = detectPatterns('You will face legal action and arrest warrant if you don\'t pay immediately. The IRS is coming for you.');
      expect(result.threat.length).toBeGreaterThan(0);
    });
  });

  describe('classifyScamType', () => {
    test('classifies phishing', () => {
      const patterns = {
        urgency: [],
        payment: [],
        credential: ['verify your account', 'enter your password'],
        fakeJob: [],
        mlm: [],
        crypto: [],
        lottery: [],
        romance: [],
        threat: []
      };
      expect(classifyScamType(patterns)).toBe('Phishing');
    });

    test('classifies fake job scam', () => {
      const patterns = {
        urgency: [],
        payment: [],
        credential: [],
        fakeJob: ['work from home', 'easy money', 'no experience'],
        mlm: [],
        crypto: [],
        lottery: [],
        romance: [],
        threat: []
      };
      expect(classifyScamType(patterns)).toBe('Fake Job Scam');
    });

    test('classifies MLM scam', () => {
      const patterns = {
        urgency: [],
        payment: [],
        credential: [],
        fakeJob: [],
        mlm: ['build your team', 'downline', 'ground floor'],
        crypto: [],
        lottery: [],
        romance: [],
        threat: []
      };
      expect(classifyScamType(patterns)).toBe('MLM/Pyramid Scheme');
    });

    test('classifies crypto scam', () => {
      const patterns = {
        urgency: [],
        payment: [],
        credential: [],
        fakeJob: [],
        mlm: [],
        crypto: ['guaranteed returns', 'double your bitcoin'],
        lottery: [],
        romance: [],
        threat: []
      };
      expect(classifyScamType(patterns)).toBe('Crypto Scam');
    });
  });

  describe('calculateMessageRiskScore', () => {
    test('returns high score for multiple indicators', () => {
      const patterns = {
        urgency: ['act now', 'limited time'],
        payment: ['gift card'],
        credential: ['verify your account'],
        fakeJob: [],
        mlm: [],
        crypto: [],
        lottery: [],
        romance: [],
        threat: []
      };
      const { score } = calculateMessageRiskScore(patterns);
      expect(score).toBeGreaterThan(50);
    });

    test('returns low score for no indicators', () => {
      const patterns = {
        urgency: [],
        payment: [],
        credential: [],
        fakeJob: [],
        mlm: [],
        crypto: [],
        lottery: [],
        romance: [],
        threat: []
      };
      const { score } = calculateMessageRiskScore(patterns);
      expect(score).toBe(0);
    });
  });

  describe('analyzeMessage', () => {
    test('identifies safe messages', () => {
      const result = analyzeMessage('Hello! How are you doing today? Hope you have a great day!');
      expect(result.riskLevel).toBe('safe');
      expect(result.isScam).toBe(false);
    });

    test('identifies dangerous scam messages', () => {
      const result = analyzeMessage(
        'URGENT! Your account has been suspended. Click here immediately to verify your password and avoid legal action. Send $500 via gift card to unlock your account. Act now - only 24 hours left!'
      );
      expect(result.riskLevel).toBe('dangerous');
      expect(result.isScam).toBe(true);
    });

    test('identifies fake job scams', () => {
      const result = analyzeMessage(
        'Work from home opportunity! Earn $10,000 per month with no experience needed. Easy money guaranteed! Limited slots available. Pay registration fee of $99 to start.'
      );
      expect(result.isScam).toBe(true);
      expect(['Fake Job Scam', 'MLM/Pyramid Scheme']).toContain(result.scamType);
    });

    test('identifies crypto scams', () => {
      const result = analyzeMessage(
        'Invest in our bitcoin trading platform! Guaranteed 5x returns in 24 hours. Send 1 BTC, get 5 BTC back! This crypto opportunity is limited time only!'
      );
      expect(result.isScam).toBe(true);
      expect(result.scamType).toBe('Crypto Scam');
    });

    test('returns required fields', () => {
      const result = analyzeMessage('Test message');
      expect(result).toHaveProperty('riskScore');
      expect(result).toHaveProperty('scamType');
      expect(result).toHaveProperty('isScam');
      expect(result).toHaveProperty('riskLevel');
      expect(result).toHaveProperty('explanation');
      expect(result).toHaveProperty('confidence');
    });

    test('handles empty input', () => {
      const result = analyzeMessage('');
      expect(result.riskScore).toBe(0);
      expect(result.isScam).toBe(false);
    });
  });
});
