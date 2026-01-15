import { useState, useEffect, useRef } from 'react';
import { ProcessingProgress } from '../types';

// @ts-ignore - Vite env variables
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function useWebSocket(sessionId: string) {
  const [progress, setProgress] = useState<ProcessingProgress | null>(() => {
    // Load progress from localStorage on mount
    if (sessionId) {
      const stored = localStorage.getItem(`progress_${sessionId}`);
      if (stored) {
        try {
          return JSON.parse(stored);
        } catch (e) {
          console.error('Failed to parse stored progress:', e);
        }
      }
    }
    return null;
  });
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const isCompletedRef = useRef(false);

  useEffect(() => {
    if (!sessionId) return;

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const connect = () => {
      // Don't reconnect if processing is already completed
      if (isCompletedRef.current) {
        console.log('Processing completed, not reconnecting WebSocket');
        return;
      }

      try {
        // In development, use the dev server's host with ws protocol
        // The Vite proxy will forward WebSocket connections to the backend
        let wsUrl: string;
        // @ts-ignore - Vite env variables
        if (import.meta.env.DEV) {
          // Development: connect to Vite dev server, which will proxy to backend
          const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
          wsUrl = `${protocol}//${window.location.host}/api/ws/${sessionId}`;
        } else {
          // Production: use configured WS_BASE_URL or derive from current location
          const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
          const host = window.location.host;
          wsUrl = WS_BASE_URL ? `${WS_BASE_URL}/api/ws/${sessionId}` : `${protocol}//${host}/api/ws/${sessionId}`;
        }
        
        console.log(`Connecting WebSocket for session: ${sessionId}`);
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log(`WebSocket connected for session: ${sessionId}`);
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            
            // Update progress state
            setProgress(data);
            
            // Persist progress to localStorage
            localStorage.setItem(`progress_${sessionId}`, JSON.stringify(data));
            
            // Check if processing is completed
            if (data.status === 'completed' || data.stage === 'completed') {
              console.log('Processing completed, marking as done');
              isCompletedRef.current = true;
              
              // Close WebSocket connection after completion
              if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
              }
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log(`WebSocket disconnected for session: ${sessionId}`);
          setIsConnected(false);
          
          // Only attempt to reconnect if processing is not completed
          if (!isCompletedRef.current) {
            reconnectTimeoutRef.current = setTimeout(() => {
              console.log('Attempting to reconnect...');
              connect();
            }, 3000);
          } else {
            console.log('Processing completed, not reconnecting');
          }
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        setIsConnected(false);
      }
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [sessionId]);

  return { progress, isConnected };
}
