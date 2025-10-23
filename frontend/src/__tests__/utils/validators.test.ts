/**
 * Validation utilities tests
 */

describe('Validator Utilities', () => {
  describe('isValidEmail', () => {
    const isValidEmail = (email: string): boolean => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    };

    it('should validate correct email formats', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
      expect(isValidEmail('user.name@domain.co.uk')).toBe(true);
      expect(isValidEmail('user+tag@example.com')).toBe(true);
    });

    it('should reject invalid email formats', () => {
      expect(isValidEmail('invalid')).toBe(false);
      expect(isValidEmail('invalid@')).toBe(false);
      expect(isValidEmail('@example.com')).toBe(false);
      expect(isValidEmail('invalid@.com')).toBe(false);
      expect(isValidEmail('')).toBe(false);
    });
  });

  describe('isValidASIN', () => {
    const isValidASIN = (asin: string): boolean => {
      const asinRegex = /^B0[A-Z0-9]{8}$/;
      return asinRegex.test(asin);
    };

    it('should validate correct ASIN formats', () => {
      expect(isValidASIN('B07XJ8C8F5')).toBe(true);
      expect(isValidASIN('B08NMBZQ3K')).toBe(true);
    });

    it('should reject invalid ASIN formats', () => {
      expect(isValidASIN('B07XJ8C8F')).toBe(false); // Too short
      expect(isValidASIN('B07XJ8C8F5X')).toBe(false); // Too long
      expect(isValidASIN('A07XJ8C8F5')).toBe(false); // Doesn't start with B0
      expect(isValidASIN('b07xj8c8f5')).toBe(false); // Lowercase
      expect(isValidASIN('')).toBe(false); // Empty
    });
  });

  describe('isValidAmazonURL', () => {
    const isValidAmazonURL = (url: string): boolean => {
      try {
        const urlObj = new URL(url);
        const isAmazonDomain =
          /amazon\.(com|co\.uk|ca|de|fr|it|es|jp|in|com\.au|com\.br|com\.mx|nl|sg)/.test(
            urlObj.hostname
          );
        const hasASIN = /\/(dp|gp\/product)\/([A-Z0-9]{10})/.test(url);
        return isAmazonDomain && hasASIN;
      } catch {
        return false;
      }
    };

    it('should validate correct Amazon URLs', () => {
      expect(isValidAmazonURL('https://www.amazon.com/dp/B07XJ8C8F5')).toBe(
        true
      );
      expect(
        isValidAmazonURL(
          'https://www.amazon.com/Product-Title/dp/B07XJ8C8F5/ref=xxx'
        )
      ).toBe(true);
      expect(
        isValidAmazonURL('https://www.amazon.co.uk/gp/product/B07XJ8C8F5')
      ).toBe(true);
    });

    it('should reject invalid Amazon URLs', () => {
      expect(isValidAmazonURL('https://www.google.com')).toBe(false);
      expect(isValidAmazonURL('https://www.amazon.com')).toBe(false); // No ASIN
      expect(isValidAmazonURL('invalid-url')).toBe(false);
      expect(isValidAmazonURL('')).toBe(false);
    });
  });

  describe('isValidPrice', () => {
    const isValidPrice = (price: number): boolean => {
      return !isNaN(price) && price >= 0 && price <= 1000000;
    };

    it('should validate correct prices', () => {
      expect(isValidPrice(29.99)).toBe(true);
      expect(isValidPrice(0)).toBe(true);
      expect(isValidPrice(1000)).toBe(true);
    });

    it('should reject invalid prices', () => {
      expect(isValidPrice(-1)).toBe(false);
      expect(isValidPrice(NaN)).toBe(false);
      expect(isValidPrice(1000001)).toBe(false);
    });
  });

  describe('isValidThreshold', () => {
    const isValidThreshold = (threshold: number): boolean => {
      return !isNaN(threshold) && threshold >= 0 && threshold <= 100;
    };

    it('should validate correct thresholds', () => {
      expect(isValidThreshold(10.0)).toBe(true);
      expect(isValidThreshold(0)).toBe(true);
      expect(isValidThreshold(100)).toBe(true);
      expect(isValidThreshold(50.5)).toBe(true);
    });

    it('should reject invalid thresholds', () => {
      expect(isValidThreshold(-1)).toBe(false);
      expect(isValidThreshold(101)).toBe(false);
      expect(isValidThreshold(NaN)).toBe(false);
    });
  });

  describe('isStrongPassword', () => {
    const isStrongPassword = (password: string): boolean => {
      if (password.length < 8) return false;
      const hasUpperCase = /[A-Z]/.test(password);
      const hasLowerCase = /[a-z]/.test(password);
      const hasNumber = /[0-9]/.test(password);
      const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
      return hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar;
    };

    it('should validate strong passwords', () => {
      expect(isStrongPassword('StrongP@ss123')).toBe(true);
      expect(isStrongPassword('MyP@ssw0rd!')).toBe(true);
    });

    it('should reject weak passwords', () => {
      expect(isStrongPassword('weak')).toBe(false); // Too short
      expect(isStrongPassword('alllowercase123!')).toBe(false); // No uppercase
      expect(isStrongPassword('ALLUPPERCASE123!')).toBe(false); // No lowercase
      expect(isStrongPassword('NoNumbers!')).toBe(false); // No numbers
      expect(isStrongPassword('NoSpecialChar123')).toBe(false); // No special chars
      expect(isStrongPassword('')).toBe(false); // Empty
    });
  });

  describe('sanitizeInput', () => {
    const sanitizeInput = (input: string): string => {
      return input
        .replace(/[<>]/g, '') // Remove potential HTML tags
        .trim();
    };

    it('should sanitize dangerous input', () => {
      expect(sanitizeInput('<script>alert("xss")</script>')).toBe(
        'scriptalert("xss")/script'
      );
      expect(sanitizeInput('  normal text  ')).toBe('normal text');
      expect(sanitizeInput('<div>test</div>')).toBe('divtest/div');
    });

    it('should preserve safe input', () => {
      expect(sanitizeInput('safe text')).toBe('safe text');
      expect(sanitizeInput('user@example.com')).toBe('user@example.com');
    });
  });
});
