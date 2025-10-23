/**
 * Service for managing product ownership (UserProduct)
 * Handles claiming/unclaiming products and managing ownership settings
 */

import apiClient from '@/lib/api';
import type {
  ClaimProductResponse,
  CompetitorProductList,
  UserProduct,
  UserProductCreate,
  UserProductUpdate,
} from '@/types/userProduct';

export const userProductService = {
  /**
   * Claim ownership of a product
   */
  async claimProduct(data: UserProductCreate): Promise<ClaimProductResponse> {
    const response = await apiClient.post('/api/v1/user-products/claim', data);
    return response.data;
  },

  /**
   * Unclaim/release ownership of a product
   */
  async unclaimProduct(productId: string): Promise<void> {
    await apiClient.delete(`/api/v1/user-products/${productId}/unclaim`);
  },

  /**
   * Get all products owned by current user
   */
  async getOwnedProducts(): Promise<UserProduct[]> {
    const response = await apiClient.get('/api/v1/user-products/owned');
    return response.data;
  },

  /**
   * Get all products (owned + competitors) with ownership information
   */
  async getCompetitorProducts(params?: {
    category?: string;
    limit?: number;
    offset?: number;
  }): Promise<CompetitorProductList> {
    const response = await apiClient.get('/api/v1/user-products/competitors', {
      params,
    });
    return response.data;
  },

  /**
   * Get ownership details for a specific product
   */
  async getOwnershipDetails(productId: string): Promise<UserProduct> {
    const response = await apiClient.get(`/api/v1/user-products/${productId}`);
    return response.data;
  },

  /**
   * Update ownership settings for a product
   */
  async updateOwnership(
    productId: string,
    data: UserProductUpdate
  ): Promise<UserProduct> {
    const response = await apiClient.put(
      `/api/v1/user-products/${productId}`,
      data
    );
    return response.data;
  },
};
