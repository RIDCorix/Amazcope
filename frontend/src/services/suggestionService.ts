/**
 * API service for Amazcope Lens insights and suggestions
 */

import apiClient from '@/lib/api';

export interface Suggestion {
  id: string;
  product_id: string;
  title: string;
  description: string;
  reasoning?: string | null;
  priority: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  status:
    | 'pending'
    | 'approved'
    | 'declined'
    | 'partially_approved'
    | 'expired';
  confidence_score?: number | null;
  estimated_impact?: string | Record<string, any> | null;
  action_count: number;
  pending_action_count: number;
  ai_model?: string | null;
  ai_prompt_tokens?: number | null;
  ai_completion_tokens?: number | null;
  created_at: string;
  updated_at: string;
  reviewed_at?: string | null;
  reviewed_by_user_id?: number | null;
}

export interface SuggestionAction {
  id: string;
  suggestion_id: string;
  action_type:
    | 'price_change'
    | 'content_update'
    | 'tracking_adjustment'
    | 'metadata_update';
  target_field: string;
  current_value: string | null;
  proposed_value: string;
  reasoning: string | null;
  estimated_impact?: string | null;
  status: 'pending' | 'approved' | 'declined' | 'applied' | 'failed';
  applied_at: string | null;
  applied_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface SuggestionDetail extends Suggestion {
  actions: SuggestionAction[];
  approved_action_count: number;
  product?: {
    id: string;
    asin: string;
    title: string;
  };
}

export interface SuggestionStats {
  total_suggestions: number;
  pending: number;
  approved: number;
  declined: number;
  partially_approved: number;
  expired: number;
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
}

export interface SuggestionFilters {
  status_filter?: string;
  priority?: string;
  category?: string;
  product_id?: string;
  limit?: number;
}

export const suggestionService = {
  /**
   * List suggestions with optional filters
   */
  async listSuggestions(filters?: SuggestionFilters): Promise<Suggestion[]> {
    const { data } = await apiClient.get('/api/v1/suggestions', {
      params: filters,
    });
    return data;
  },

  /**
   * Get detailed suggestion with all actions
   */
  async getSuggestion(id: string): Promise<SuggestionDetail> {
    const { data } = await apiClient.get(`/api/v1/suggestions/${id}`);
    return data;
  },

  /**
   * Review entire suggestion (approve/decline)
   */
  async reviewSuggestion(
    id: string,
    decision: 'approved' | 'declined' | 'partially_approved',
    options?: {
      approved_action_ids?: number[];
      declined_action_ids?: number[];
      apply_immediately?: boolean;
    }
  ) {
    const { data } = await apiClient.post(`/api/v1/suggestions/${id}/review`, {
      suggestion_id: id,
      decision,
      ...options,
    });
    return data;
  },

  /**
   * Review specific actions within a suggestion
   */
  async reviewActions(
    suggestionId: string,
    actionIds: string[],
    status: 'approved' | 'declined'
  ): Promise<{ message: string }> {
    const { data } = await apiClient.post(
      `/api/v1/suggestions/${suggestionId}/actions/review`,
      {
        action_ids: actionIds,
        status,
      }
    );
    return data;
  },

  /**
   * Apply approved actions immediately
   */
  async applyActions(
    suggestionId: string,
    actionIds?: string[]
  ): Promise<{
    successful: string[];
    failed: Array<{ action_id: string; error: string }>;
  }> {
    const { data } = await apiClient.post(
      `/api/v1/suggestions/${suggestionId}/apply`,
      actionIds ? { action_ids: actionIds } : {}
    );
    return data;
  },

  /**
   * Get suggestion statistics
   */
  async getStats(): Promise<SuggestionStats> {
    const { data } = await apiClient.get('/api/v1/suggestions/stats/overview');
    return data;
  },

  /**
   * Delete a suggestion
   */
  async deleteSuggestion(id: string) {
    const { data } = await apiClient.delete(`/api/v1/suggestions/${id}`);
    return data;
  },
};
