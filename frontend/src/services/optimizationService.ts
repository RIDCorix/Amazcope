import apiClient from '@/lib/api';

export interface OptimizationSuggestion {
  id: string;
  product_id: string;
  suggestion_type: string;
  priority: string;
  status: string;
  title: string;
  description: string;
  reasoning: string;
  current_value: string | null;
  suggested_value: string | null;
  expected_impact: string | null;
  impact_score: number;
  effort_score: number;
  confidence_score: number;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SuggestionResponse {
  suggestion_type: string;
  priority: string;
  title: string;
  description: string;
  reasoning: string;
  current_value: string | null;
  suggested_value: string | null;
  expected_impact: string | null;
  impact_score: number;
  effort_score: number;
  confidence_score: number;
  metadata: Record<string, any>;
}

export interface OptimizationReport {
  product_id: string;
  product_title: string;
  generated_at: string;
  suggestions: SuggestionResponse[];
  overall_score: number;
  top_priority: string;
  cache_hit: boolean;
}

export interface GenerateSuggestionsRequest {
  product_id: string;
  include_competitors?: boolean;
  suggestion_types?: string[];
}

export interface ABTest {
  id: string;
  product_id: string;
  name: string;
  description: string | null;
  test_type: string;
  status: string;
  control_variant: Record<string, any>;
  test_variant: Record<string, any>;
  baseline_metrics: Record<string, any>;
  control_metrics: Record<string, any>;
  test_metrics: Record<string, any>;
  sample_size: number;
  confidence_level: number | null;
  p_value: number | null;
  winner: string | null;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateABTestRequest {
  product_id: string;
  suggestion_id?: number;
  name: string;
  description?: string;
  test_type: string;
  control_variant: Record<string, any>;
  test_variant: Record<string, any>;
  baseline_metrics?: Record<string, any>;
}

export interface ABTestResult {
  test_id: number;
  test_name: string;
  status: string;
  sample_size: number;
  control_metrics: Record<string, any>;
  test_metrics: Record<string, any>;
  winner: string | null;
  confidence_level: number | null;
  p_value: number | null;
  improvement_percentage: number | null;
  recommendation: string;
}

export const optimizationService = {
  /**
   * Generate Amazcope Lens-powered optimization insights for a product
   */
  async generateSuggestions(
    request: GenerateSuggestionsRequest
  ): Promise<OptimizationReport> {
    const response = await apiClient.post(
      '/api/v1/optimization/suggestions',
      request
    );
    return response.data;
  },

  /**
   * Get all optimization suggestions for a product
   */
  async getProductSuggestions(
    productId: string,
    params?: { status?: string; suggestion_type?: string }
  ): Promise<OptimizationSuggestion[]> {
    const response = await apiClient.get(
      `/api/v1/optimization/suggestions/product/${productId}`,
      {
        params,
      }
    );
    return response.data;
  },

  /**
   * Get a specific optimization suggestion by ID
   */
  async getSuggestion(suggestionId: string): Promise<OptimizationSuggestion> {
    const response = await apiClient.get(
      `/api/v1/optimization/suggestions/${suggestionId}`
    );
    return response.data;
  },

  /**
   * Update suggestion status (accept, reject, implement)
   */
  async updateSuggestion(
    suggestionId: string,
    update: { status?: string; implemented_at?: string }
  ): Promise<OptimizationSuggestion> {
    const response = await apiClient.patch(
      `/api/v1/optimization/suggestions/${suggestionId}`,
      update
    );
    return response.data;
  },

  /**
   * Accept a suggestion
   */
  async acceptSuggestion(
    suggestionId: string
  ): Promise<OptimizationSuggestion> {
    return this.updateSuggestion(suggestionId, { status: 'accepted' });
  },

  /**
   * Reject a suggestion
   */
  async rejectSuggestion(
    suggestionId: string
  ): Promise<OptimizationSuggestion> {
    return this.updateSuggestion(suggestionId, { status: 'rejected' });
  },

  /**
   * Mark suggestion as implemented
   */
  async implementSuggestion(
    suggestionId: string
  ): Promise<OptimizationSuggestion> {
    return this.updateSuggestion(suggestionId, {
      status: 'implemented',
      implemented_at: new Date().toISOString(),
    });
  },

  /**
   * Delete a suggestion
   */
  async deleteSuggestion(suggestionId: string): Promise<void> {
    await apiClient.delete(`/api/v1/optimization/suggestions/${suggestionId}`);
  },

  // A/B Testing methods

  /**
   * Create a new A/B test
   */
  async createABTest(request: CreateABTestRequest): Promise<ABTest> {
    const response = await apiClient.post(
      '/api/v1/optimization/tests',
      request
    );
    return response.data;
  },

  /**
   * Get all A/B tests
   */
  async getABTests(params?: {
    product_id?: string;
    status?: string;
  }): Promise<ABTest[]> {
    const response = await apiClient.get('/api/v1/optimization/tests', {
      params,
    });
    return response.data;
  },

  /**
   * Get a specific A/B test
   */
  async getABTest(testId: number): Promise<ABTest> {
    const response = await apiClient.get(
      `/api/v1/optimization/tests/${testId}`
    );
    return response.data;
  },

  /**
   * Update A/B test metrics
   */
  async updateABTest(
    testId: number,
    update: {
      control_metrics?: Record<string, any>;
      test_metrics?: Record<string, any>;
      sample_size?: number;
      status?: string;
    }
  ): Promise<ABTest> {
    const response = await apiClient.patch(
      `/api/v1/optimization/tests/${testId}`,
      update
    );
    return response.data;
  },

  /**
   * Get A/B test results with analysis
   */
  async getABTestResults(testId: number): Promise<ABTestResult> {
    const response = await apiClient.get(
      `/api/v1/optimization/tests/${testId}/results`
    );
    return response.data;
  },

  /**
   * Delete an A/B test
   */
  async deleteABTest(testId: number): Promise<void> {
    await apiClient.delete(`/api/v1/optimization/tests/${testId}`);
  },
};
