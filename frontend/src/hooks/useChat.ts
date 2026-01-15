import { useState, useEffect } from 'react';
import { ChatMessage } from '../types';
import { sendChatMessage, getChatHistory } from '../services/api';

export function useChat(sessionId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!sessionId) return;

    // Load chat history
    const loadHistory = async () => {
      try {
        const history = await getChatHistory(sessionId);
        setMessages(history.messages || []);
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    };

    loadHistory();
  }, [sessionId]);

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(sessionId, content);

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: response.message_id,
        role: 'assistant',
        content: response.answer,
        timestamp: response.timestamp,
        metadata: {
          chunks_used: response.visuals.chunks.length,
          has_tables: response.visuals.tables.length > 0,
          has_images: response.visuals.images.length > 0,
          // Extract HTML from table objects and base64 from image objects
          tables: response.visuals.tables.map((t: any) => t.html || t),
          images: response.visuals.images.map((i: any) => i.base64 || i),
        },
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, sendMessage, isLoading };
}
