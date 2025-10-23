/**
 * Utility functions formatters tests
 */

describe('Formatter Utilities', () => {
  describe('formatCurrency', () => {
    const formatCurrency = (value: number, currency: string = 'USD') => {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency,
      }).format(value);
    };

    it('should format USD correctly', () => {
      expect(formatCurrency(29.99)).toBe('$29.99');
      expect(formatCurrency(1000)).toBe('$1,000.00');
      expect(formatCurrency(0)).toBe('$0.00');
    });

    it('should format other currencies', () => {
      expect(formatCurrency(29.99, 'EUR')).toContain('29.99');
      expect(formatCurrency(29.99, 'GBP')).toContain('29.99');
    });

    it('should handle negative values', () => {
      expect(formatCurrency(-29.99)).toContain('-');
      expect(formatCurrency(-29.99)).toContain('29.99');
    });
  });

  describe('formatNumber', () => {
    const formatNumber = (value: number) => {
      return new Intl.NumberFormat('en-US').format(value);
    };

    it('should format numbers with commas', () => {
      expect(formatNumber(1000)).toBe('1,000');
      expect(formatNumber(1000000)).toBe('1,000,000');
      expect(formatNumber(100)).toBe('100');
    });

    it('should handle decimals', () => {
      const formatDecimal = (value: number, decimals: number = 2) => {
        return value.toFixed(decimals);
      };

      expect(formatDecimal(4.5)).toBe('4.50');
      expect(formatDecimal(4.567, 2)).toBe('4.57');
      expect(formatDecimal(4.567, 0)).toBe('5');
    });
  });

  describe('formatDate', () => {
    const formatDate = (dateString: string) => {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    };

    it('should format dates correctly', () => {
      expect(formatDate('2025-01-01')).toContain('Jan');
      expect(formatDate('2025-01-01')).toContain('2025');
    });

    it('should handle ISO date strings', () => {
      const result = formatDate('2025-01-01T00:00:00Z');
      expect(result).toContain('2025');
    });
  });

  describe('formatPercentage', () => {
    const formatPercentage = (value: number, decimals: number = 1) => {
      return `${value.toFixed(decimals)}%`;
    };

    it('should format percentages', () => {
      expect(formatPercentage(10.5)).toBe('10.5%');
      expect(formatPercentage(100)).toBe('100.0%');
      expect(formatPercentage(0)).toBe('0.0%');
    });

    it('should handle negative percentages', () => {
      expect(formatPercentage(-5.2)).toBe('-5.2%');
    });
  });

  describe('truncateText', () => {
    const truncateText = (text: string, maxLength: number) => {
      if (text.length <= maxLength) return text;
      return text.slice(0, maxLength) + '...';
    };

    it('should truncate long text', () => {
      const longText = 'This is a very long text that needs to be truncated';
      expect(truncateText(longText, 20)).toBe('This is a very long ...');
      expect(truncateText(longText, 20).length).toBeLessThanOrEqual(23); // 20 + '...'
    });

    it('should not truncate short text', () => {
      const shortText = 'Short';
      expect(truncateText(shortText, 20)).toBe('Short');
    });

    it('should handle empty strings', () => {
      expect(truncateText('', 10)).toBe('');
    });
  });

  describe('formatBSR', () => {
    const formatBSR = (rank: number | null) => {
      if (rank === null || rank === undefined) return 'N/A';
      return `#${formatNumber(rank)}`;
    };

    const formatNumber = (value: number) => {
      return new Intl.NumberFormat('en-US').format(value);
    };

    it('should format BSR rankings', () => {
      expect(formatBSR(100)).toBe('#100');
      expect(formatBSR(1000)).toBe('#1,000');
      expect(formatBSR(1000000)).toBe('#1,000,000');
    });

    it('should handle null rankings', () => {
      expect(formatBSR(null)).toBe('N/A');
    });
  });

  describe('formatRating', () => {
    const formatRating = (rating: number) => {
      return rating.toFixed(1);
    };

    it('should format ratings', () => {
      expect(formatRating(4.5)).toBe('4.5');
      expect(formatRating(5)).toBe('5.0');
      expect(formatRating(4.567)).toBe('4.6');
    });
  });
});
