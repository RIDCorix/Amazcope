/**
 * Product Metrics Service
 *
 * TypeScript service for fetching and managing product metrics data.
 * Provides methods for trend analysis and multi-product comparison.
 */

import apiClient from '@/lib/api';

// ============================================================================
// Interfaces
// ============================================================================

export interface ProductMetric {
  id: string;
  product_id: string;
  recorded_at: string;
  price: number | null;
  original_price: number | null;
  buybox_price: number | null;
  discount_percentage: number | null;
  bsr_main_category: number | null;
  bsr_small_category: number | null;
  rating: number | null;
  review_count: number;
  in_stock: boolean;
  stock_status: string | null;
  seller_name: string | null;
  is_amazon_seller: boolean;
  is_fba: boolean;
  is_deal: boolean;
  is_prime: boolean;
  coupon_available: boolean;
  coupon_text: string | null;
  category_avg_price: number | null;
  category_avg_rating: number | null;
  category_avg_reviews: number | null;
  scrape_successful: boolean;
  scrape_error: string | null;
}

export interface MetricsSummary {
  product_id: string;
  current_price: number | null;
  price_change_7d: number | null;
  price_change_30d: number | null;
  current_bsr: number | null;
  bsr_change_7d: number | null;
  bsr_change_30d: number | null;
  current_rating: number | null;
  rating_change_7d: number | null;
  rating_change_30d: number | null;
  review_count: number;
  review_growth_7d: number | null;
  review_growth_30d: number | null;
  last_updated: string;
}

export interface PriceTrendDataPoint {
  date: string;
  price: number | null;
  buybox_price: number | null;
  original_price: number | null;
  category_avg_price?: number | null;
}

export interface BSRTrendDataPoint {
  date: string;
  bsr_main: number | null;
  bsr_small: number | null;
}

export interface ReviewTrendDataPoint {
  date: string;
  rating: number | null;
  review_count: number;
  category_avg_rating?: number | null;
  category_avg_reviews?: number | null;
}

export interface MetricDataPoint {
  date: string;
  value: number | null;
}

export interface ProductMetricTrend {
  product_id: string;
  product_title: string;
  product_asin: string;
  data_points:
    | PriceTrendDataPoint[]
    | BSRTrendDataPoint[]
    | ReviewTrendDataPoint[];
}

export interface MetricComparisonResponse {
  metric_type: 'price' | 'bsr' | 'rating' | 'reviews';
  start_date: string;
  end_date: string;
  products: ProductMetricTrend[];
  category_average: MetricDataPoint[] | null;
}

export interface MetricComparisonRequest {
  product_ids: string[];
  metric_type: 'price' | 'bsr' | 'rating' | 'reviews';
  days?: number;
}

export interface CategoryTrendRequest {
  category_name: string;
  days?: number;
}

// ============================================================================
// NEW: Dynamic Metrics System Interfaces
// ============================================================================

export interface MetricFieldMetadata {
  display_name: string;
  description: string;
  type: string;
  category: string;
}

export interface DynamicTrendResponse {
  metadata: Record<string, MetricFieldMetadata>;
  data: Array<Record<string, any>>;
  total_points: number;
}

export interface FieldCategory {
  name: string;
  display_name: string;
  description: string;
  type: string;
}

export interface AvailableFieldsResponse {
  categories: Record<string, FieldCategory[]>;
  total_fields: number;
}

// ============================================================================
// Service Methods
// ============================================================================

export const metricsService = {
  /**
   * Get metrics summary for a product with 7-day and 30-day changes
   */
  async getMetricsSummary(productId: string): Promise<MetricsSummary> {
    const response = await apiClient.get(
      `/api/v1/metrics/products/${productId}/summary`
    );
    return response.data;
  },

  /**
   * Get all metrics for a product within a date range
   */
  async getProductMetrics(
    productId: string,
    days: number = 30
  ): Promise<ProductMetric[]> {
    const response = await apiClient.get(
      `/api/v1/metrics/products/${productId}/metrics`,
      {
        params: { days },
      }
    );
    return response.data;
  },

  /**
   * Get the most recent metric snapshot for a product
   */
  async getLatestMetric(productId: string): Promise<ProductMetric> {
    const response = await apiClient.get(
      `/api/v1/metrics/products/${productId}/latest`
    );
    return response.data;
  },

  // ============================================================================
  // NEW: Dynamic Metrics API
  // ============================================================================

  /**
   * Get all available metric fields that can be queried
   *
   * **Returns:** Field registry with categories, types, and descriptions
   *
   * @example
   * const fields = await metricsService.getAvailableFields();
   * // Build UI dropdown from fields.categories
   */
  async getAvailableFields(): Promise<AvailableFieldsResponse> {
    const response = await apiClient.get('/api/v1/metrics/fields/available');
    return response.data;
  },

  /**
   * 🚀 Dynamic metric trends endpoint - Query any combination of fields!
   *
   * **This replaces getPriceTrend(), getBSRTrend(), and getReviewTrend()**
   *
   * @param productId - Product ID to query
   * @param fields - Array of field names to retrieve
   * @param days - Number of days to go back (1-365)
   *
   * @example
   * // Get price data (replaces getPriceTrend)
   * const priceData = await metricsService.getTrends(123, ['price', 'buybox_price', 'original_price'], 30);
   *
   * @example
   * // Get BSR data (replaces getBSRTrend)
   * const bsrData = await metricsService.getTrends(123, ['bsr_main', 'bsr_small'], 30);
   *
   * @example
   * // Get review data (replaces getReviewTrend)
   * const reviewData = await metricsService.getTrends(123, ['rating', 'review_count'], 30);
   *
   * @example
   * // Get multiple metrics in one call
   * const dashboardData = await metricsService.getTrends(
   *   123,
   *   ['price', 'bsr_main', 'rating', 'review_count', 'in_stock'],
   *   90
   * );
   */
  async getTrends(
    productId: string,
    fields: string[],
    days: number = 30
  ): Promise<DynamicTrendResponse> {
    const response = await apiClient.get(
      `/api/v1/metrics/products/${productId}/trends`,
      {
        params: {
          fields: fields.join(','),
          days,
        },
      }
    );
    return response.data;
  },

  /**
   * Get price trend data for a product (backward compatible wrapper)
   *
   * @deprecated Use getTrends() instead for better flexibility
   * @example
   * // Old way:
   * const data = await metricsService.getPriceTrend(123, 30);
   *
   * // New way (recommended):
   * const data = await metricsService.getTrends(123, ['price', 'buybox_price', 'original_price'], 30);
   */
  async getPriceTrend(
    productId: string,
    days: number = 30
  ): Promise<PriceTrendDataPoint[]> {
    const response = await this.getTrends(
      productId,
      ['price', 'buybox_price', 'original_price'],
      days
    );
    return response.data.map((point: any) => ({
      date: point.date,
      price: point.price,
      buybox_price: point.buybox_price,
      original_price: point.original_price,
    }));
  },

  /**
   * Get BSR trend data for a product (backward compatible wrapper)
   *
   * @deprecated Use getTrends() instead for better flexibility
   * @example
   * // Old way:
   * const data = await metricsService.getBSRTrend(123, 30);
   *
   * // New way (recommended):
   * const data = await metricsService.getTrends(123, ['bsr_main', 'bsr_small'], 30);
   */
  async getBSRTrend(
    productId: string,
    days: number = 30
  ): Promise<BSRTrendDataPoint[]> {
    const response = await this.getTrends(
      productId,
      ['bsr_main', 'bsr_small'],
      days
    );
    return response.data.map((point: any) => ({
      date: point.date,
      bsr_main: point.bsr_main,
      bsr_small: point.bsr_small,
    }));
  },

  /**
   * Get review count and rating trend for a product (backward compatible wrapper)
   *
   * @deprecated Use getTrends() instead for better flexibility
   * @example
   * // Old way:
   * const data = await metricsService.getReviewTrend(123, 30);
   *
   * // New way (recommended):
   * const data = await metricsService.getTrends(123, ['rating', 'review_count'], 30);
   */
  async getReviewTrend(
    productId: string,
    days: number = 30
  ): Promise<ReviewTrendDataPoint[]> {
    const response = await this.getTrends(
      productId,
      ['rating', 'review_count'],
      days
    );
    return response.data.map((point: any) => ({
      date: point.date,
      rating: point.rating,
      review_count: point.review_count,
    }));
  },

  /**
   * Compare metrics for multiple products with optional category average overlay
   */
  async compareProducts(
    request: MetricComparisonRequest
  ): Promise<MetricComparisonResponse> {
    const response = await apiClient.post('/api/v1/metrics/compare', request);
    return response.data;
  },

  /**
   * Get category average trend data
   */
  async getCategoryTrend(
    categoryName: string,
    days: number = 30
  ): Promise<MetricDataPoint[]> {
    const response = await apiClient.post('/api/v1/metrics/category/trend', {
      category_name: categoryName,
      days,
    });
    return response.data;
  },
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Format percentage change with + or - sign
 */
export function formatPercentageChange(value: number | null): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * Get color for percentage change (green for positive, red for negative)
 * Note: For BSR, lower is better, so colors are inverted
 */
export function getChangeColor(
  value: number | null,
  invertColors: boolean = false
): string {
  if (value === null || value === undefined) {
    return 'text-gray-500';
  }

  const isPositive = value > 0;
  const isGood = invertColors ? !isPositive : isPositive;

  return isGood ? 'text-green-600' : 'text-red-600';
}

/**
 * Format currency value
 */
export function formatCurrency(
  value: number | null,
  currency: string = 'USD'
): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(value);
}

/**
 * Format BSR (Best Seller Rank) with commas
 */
export function formatBSR(value: number | null): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }

  return `#${new Intl.NumberFormat('en-US').format(value)}`;
}

/**
 * Format rating (1-5 stars)
 */
export function formatRating(value: number | null): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }

  return `${value.toFixed(1)} ★`;
}

/**
 * Get metric type display name
 */
export function getMetricTypeName(metricType: string): string {
  const names: Record<string, string> = {
    price: 'Price',
    bsr: 'Best Seller Rank',
    rating: 'Rating',
    reviews: 'Review Count',
  };

  return names[metricType] || metricType;
}

/**
 * Get chart color by index for multi-product comparison
 */
export function getChartColor(index: number): string {
  const colors = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#14b8a6', // teal
    '#f97316', // orange
    '#6366f1', // indigo
    '#84cc16', // lime
  ];

  return colors[index % colors.length];
}
