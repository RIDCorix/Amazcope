import React, { createContext, useCallback, useContext, useState } from 'react';

import {
  chatService,
  type ChatContext,
  type ChatMessage,
} from '@/services/chatService';

interface ChatContextType {
  messages: ChatMessage[];
  isLoading: boolean;
  context: ChatContext | null;
  sendMessage: (
    content: string,
    context?: Record<string, any>
  ) => Promise<void>;
  clearMessages: () => void;
  loadContext: () => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [context, setContext] = useState<ChatContext | null>(null);

  const loadContext = useCallback(async () => {
    try {
      const ctx = await chatService.getContext();
      setContext(ctx);
    } catch (error) {
      console.error('Failed to load chat context:', error);
    }
  }, []);

  const sendMessage = useCallback(
    async (content: string, additionalContext?: Record<string, any>) => {
      const userMessage: ChatMessage = {
        role: 'user',
        content,
      };

      setMessages(prev => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const response = await chatService.sendMessage({
          messages: [...messages, userMessage],
          context: additionalContext,
        });

        setMessages(prev => [...prev, response.message]);
      } catch (error) {
        console.error('Failed to send message:', error);
        const errorMessage: ChatMessage = {
          role: 'assistant',
          content:
            '🤖 Oops! Amazcope Lens encountered a technical hiccup. Please try asking again in a moment.',
        };
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    },
    [messages]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        isLoading,
        context,
        sendMessage,
        clearMessages,
        loadContext,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
