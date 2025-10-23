import apiClient from '@/lib/api';

export interface ProductFromUrlRequest {
  url: string;
  price_change_threshold: number;
  bsr_change_threshold: number;
  scrape_reviews: boolean;
  scrape_bestsellers: boolean;
  category_url?: string | null;
  manual_category?: string | null;
  manual_small_category?: string | null;
}

export interface Product {
  id: string;
  current_bsr?: number | null;
  asin: string;
  title: string | null;
  brand: string | null;
  category: string | null;
  small_category?: string | null;
  url: string;
  image_url: string | null;
  is_active: boolean;
  price_change_threshold?: number;
  bsr_change_threshold?: number;
  bsr_category_link?: string | null;
  created_at: string;
  product_description?: string | null;
  updated_at?: string;
  // Denormalized fields from latest snapshot (direct fields, not nested)
  price?: string;
  original_price?: string | null;
  currency?: string;
  discount_percentage?: number | null;
  bsr_main_category?: number | null;
  rating?: number | null;
  review_count?: number;
  in_stock?: boolean;
  stock_status?: string | null;
  is_prime?: boolean;
  scraped_at?: string | null;
  unread_alerts_count?: number;
  // Keep for backward compatibility (deprecated)
  latest_snapshot?: ProductSnapshot;
}

export interface ProductSnapshot {
  id: string;
  price: string;
  original_price: string;
  buybox_price: string;
  bsr_small_category: number;
  bsr_main_category: number | null;
  rating: number;
  review_count: number;
  in_stock: boolean;
  seller_name: string;
  scraped_at: string;
}

export interface Review {
  id: string;
  review_id: string;
  title: string;
  text: string;
  rating: number;
  verified_purchase: boolean;
  helpful_count: number;
  review_date: string;
  reviewer_name: string;
  reviewer_id: string;
  is_vine_voice: boolean;
  images: string[];
  variant_info: Record<string, any>;
  created_at: string;
}

export interface ReviewStats {
  total_reviews: number;
  average_rating: number;
  verified_purchases: number;
  rating_distribution: {
    '5_star': number;
    '4_star': number;
    '3_star': number;
    '2_star': number;
    '1_star': number;
  };
}

export interface BestsellerSnapshot {
  id: string;
  category_name: string;
  category_url: string;
  category_id: string;
  snapshot_date: string;
  total_products_scraped: number;
  product_rank: number | null;
  top_10: Array<{
    rank: number;
    asin: string;
    title: string;
    price: number;
    rating: number;
    review_count: number;
  }> | null;
}

export interface BestsellerHistory {
  product_asin: string;
  history: Array<{
    date: string;
    rank: number;
    category: string;
    total_products: number;
  }>;
}

export interface ProductUpdateCategoryRequest {
  category_url?: string | null;
  manual_category?: string | null;
  manual_small_category?: string | null;
  trigger_bestsellers_scrape?: boolean;
}

export interface ProductUpdateRequest {
  title?: string | null;
  brand?: string | null;
  category?: string | null;
  small_category?: string | null;
  is_active?: boolean | null;
  track_frequency?: string | null;
  price_change_threshold?: number | null;
  bsr_change_threshold?: number | null;
  url?: string | null;
  image_url?: string | null;
  product_description?: string | null;
  features?: Record<string, any> | null;
}

export interface UserProductSettingsRequest {
  is_active?: boolean | null;
  price_change_threshold?: number | null;
  bsr_change_threshold?: number | null;
  notes?: string | null;
}

export interface ProductContentUpdateRequest {
  product_description?: string | null;
  features?: string[] | null;
  marketing_copy?: string | null;
  seo_keywords?: string[] | null;
  competitor_analysis?: string | null;
}

export const productService = {
  /**
   * Import product from Amazon URL
   */
  async importFromUrl(data: ProductFromUrlRequest): Promise<Product> {
    const response = await apiClient.post(
      '/api/v1/tracking/products/from-url',
      data
    );
    return response.data;
  },

  /**
   * Get all products
   */
  async getProducts(): Promise<Product[]> {
    const response = await apiClient.get('/api/v1/tracking/products');
    return response.data;
  },

  /**
   * Get product by ID
   */
  async getProduct(id: string): Promise<Product> {
    const response = await apiClient.get(`/api/v1/tracking/products/${id}`);
    return response.data;
  },

  /**
   * Get product reviews
   */
  async getReviews(
    productId: string,
    params?: {
      min_rating?: number;
      verified_only?: boolean;
      skip?: number;
      limit?: number;
    }
  ): Promise<Review[]> {
    const response = await apiClient.get(
      `/api/v1/tracking/products/${productId}/reviews`,
      { params }
    );
    return response.data;
  },

  /**
   * Get review statistics
   */
  async getReviewStats(productId: string): Promise<ReviewStats> {
    const response = await apiClient.get(
      `/api/v1/tracking/products/${productId}/reviews/stats`
    );
    return response.data;
  },

  /**
   * Get latest bestseller snapshot
   */
  async getBestsellers(
    productId: string,
    latest = true
  ): Promise<BestsellerSnapshot> {
    const response = await apiClient.get(
      `/api/v1/tracking/products/${productId}/bestsellers`,
      { params: { latest } }
    );
    return response.data;
  },

  /**
   * Get bestseller rank history
   */
  async getBestsellerHistory(
    productId: string,
    days = 30
  ): Promise<BestsellerHistory> {
    const response = await apiClient.get(
      `/api/v1/tracking/products/${productId}/bestsellers/history`,
      { params: { days } }
    );
    return response.data;
  },

  /**
   * Update product details and settings
   */
  async updateProduct(
    id: string,
    data: ProductUpdateRequest
  ): Promise<Product> {
    const response = await apiClient.put(
      `/api/v1/tracking/products/${id}`,
      data
    );
    return response.data;
  },

  /**
   * Update user-specific product settings
   */
  async updateUserProductSettings(
    id: string,
    data: UserProductSettingsRequest
  ): Promise<{
    product_id: string;
    user_id: string;
    is_active: boolean;
    price_change_threshold: number | null;
    bsr_change_threshold: number | null;
    notes: string | null;
    updated_at: string;
  }> {
    const response = await apiClient.patch(
      `/api/v1/tracking/products/${id}/user-settings`,
      data
    );
    return response.data;
  },

  /**
   * Update product content with AI-enhanced descriptions
   */
  async updateProductContent(
    id: string,
    data: ProductContentUpdateRequest
  ): Promise<Product> {
    const response = await apiClient.patch(
      `/api/v1/tracking/products/${id}/content`,
      data
    );
    return response.data;
  },

  /**
   * Update product category information
   */
  async updateProductCategory(
    id: string,
    data: ProductUpdateCategoryRequest
  ): Promise<Product> {
    const response = await apiClient.patch(
      `/api/v1/tracking/products/${id}/category`,
      data
    );
    return response.data;
  },

  /**
   * Delete product
   */
  async deleteProduct(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/tracking/products/${id}`);
  },

  /**
   * Trigger manual scrape
   */
  async triggerScrape(id: string): Promise<void> {
    await apiClient.post(`/api/v1/tracking/products/${id}/scrape`);
  },

  /**
   * Force real-time product refresh (bypasses cache)
   */
  async refreshProduct(
    id: string,
    updateMetadata: boolean = true
  ): Promise<Product> {
    const response = await apiClient.post(
      `/api/v1/tracking/products/${id}/refresh`,
      null,
      { params: { update_metadata: updateMetadata } }
    );
    return response.data;
  },

  /**
   * Batch refresh multiple products (bypasses cache)
   */
  async batchRefreshProducts(
    productIds?: string[],
    updateMetadata: boolean = true
  ): Promise<{
    success: number;
    failed: number;
    errors: Array<{ product_id: string; error: string }>;
    updated_products: Array<{
      product_id: string;
      snapshot_id: number;
      scraped_at: string;
    }>;
  }> {
    const response = await apiClient.post(
      '/api/v1/tracking/products/batch-refresh',
      productIds ? { product_ids: productIds } : null,
      { params: { update_metadata: updateMetadata } }
    );
    return response.data;
  },
};
