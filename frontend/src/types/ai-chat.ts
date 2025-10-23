/**
 * AI Chat Types
 * TypeScript definitions for Learning Coach AI chat functionality
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  userId: string;
  message: string;
  currentNodeSlug?: string | null;
  conversationHistory: ConversationMessage[];
}

export interface ChatResponse {
  response: string;
  suggestions: string[];
  nextSteps: string[];
  metadata?: {
    nodeSlug?: string;
    confidence?: number;
    processingTime?: number;
  };
}

export interface AnalyzeRequest {
  userId: string;
  nodeSlug: string;
  learningData: {
    timeSpent?: number;
    attempts?: number;
    completionRate?: number;
  };
}

export interface AnalyzeResponse {
  analysis: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  nextSteps: string[];
}

export interface StreamChunk {
  type: 'token' | 'complete' | 'error' | 'response';
  content?: string;
  data?: ChatResponse;
  error?: string;
  response?: string;
}
