/**
 * Chat Service for Amazcope Lens communication
 */

import { apiClient } from '@/lib/api';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  context?: {
    product_id?: number;
    page?: string;
    [key: string]: any;
  };
}

export interface ChatResponse {
  message: ChatMessage;
  tool_calls?: Array<{
    function: string;
    result: any;
  }>;
}

export interface ChatContext {
  user: {
    id: number;
    username: string;
    email: string;
  };
  stats: {
    total_products: number;
    active_products: number;
  };
}

class ChatService {
  /**
   * Send a chat message to Amazcope Lens
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>(
      '/api/v1/chat/chat',
      request
    );
    return response.data;
  }

  /**
   * Get chat context for initialization
   */
  async getContext(): Promise<ChatContext> {
    const response = await apiClient.get<ChatContext>(
      '/api/v1/chat/chat/context'
    );
    return response.data;
  }
}

export const chatService = new ChatService();
