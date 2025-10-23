// Mock the entire api module to avoid import.meta issues
jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

// Import after mocking
import apiClient from '@/lib/api';
import {
  formatBSR,
  formatCurrency,
  formatRating,
  metricsService,
} from '@/services/metricsService';

// Create a properly typed mock for apiClient
const mockedApiClient = jest.mocked(apiClient);

describe('metricsService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getProductMetrics', () => {
    it('should fetch product metrics successfully', async () => {
      const mockMetrics = [
        {
          id: 'test-uuid-1',
          product_id: 'test-uuid-1',
          price: 29.99,
          bsr_small_category: 100,
          rating: 4.5,
          review_count: 1200,
          recorded_at: '2025-01-01T00:00:00Z',
          in_stock: true,
          scrape_successful: true,
        },
      ];

      mockedApiClient.get.mockResolvedValueOnce({ data: mockMetrics });

      const result = await metricsService.getProductMetrics('test-uuid-1', 7);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/v1/metrics/products/test-uuid-1/metrics',
        expect.any(Object)
      );
      expect(result).toEqual(mockMetrics);
    });

    it('should handle metrics fetch error', async () => {
      mockedApiClient.get.mockRejectedValueOnce(new Error('Failed to fetch'));

      await expect(
        metricsService.getProductMetrics('test-uuid-1')
      ).rejects.toThrow('Failed to fetch');
    });
  });

  describe('getMetricsSummary', () => {
    it('should fetch metrics summary', async () => {
      const mockSummary = {
        product_id: 'test-uuid-1',
        current_price: 28.99,
        price_change_7d: -2.0,
        price_change_30d: -5.0,
        current_bsr: 105,
        bsr_change_7d: -10,
        bsr_change_30d: -25,
        current_rating: 4.5,
        review_count: 1250,
        review_growth_7d: 50,
        review_growth_30d: 150,
        last_updated: '2025-01-01T00:00:00Z',
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockSummary });

      const result = await metricsService.getMetricsSummary('test-uuid-1');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/v1/metrics/products/test-uuid-1/summary'
      );
      expect(result.current_price).toBe(28.99);
    });
  });

  describe('Formatter Functions', () => {
    describe('formatCurrency', () => {
      it('should format currency correctly', () => {
        expect(formatCurrency(29.99)).toBe('$29.99');
        expect(formatCurrency(1000)).toBe('$1,000.00');
        expect(formatCurrency(null)).toBe('N/A');
      });
    });

    describe('formatBSR', () => {
      it('should format BSR correctly', () => {
        expect(formatBSR(100)).toBe('#100');
        expect(formatBSR(1000)).toBe('#1,000');
        expect(formatBSR(null)).toBe('N/A');
      });
    });

    describe('formatRating', () => {
      it('should format rating correctly', () => {
        expect(formatRating(4.5)).toBe('4.5 ★');
        expect(formatRating(5.0)).toBe('5.0 ★');
        expect(formatRating(null)).toBe('N/A');
      });
    });
  });
});
