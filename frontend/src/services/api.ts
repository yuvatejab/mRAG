const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export interface UploadResponse {
  document_id: string;
  filename: string;
  status: string;
  message: string;
}

export interface ChatRequest {
  session_id: string;
  query: string;
  document_ids?: string[];
  num_chunks?: number;
}

export interface VisualContent {
  tables: any[];
  images: any[];
  chunks: any[];
}

export interface ChatResponse {
  message_id: string;
  answer: string;
  visuals: VisualContent;
  timestamp: string;
  processing_time: number;
}

export async function uploadDocument(
  sessionId: string,
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);

  const response = await fetch(`/api/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

export async function sendChatMessage(
  sessionId: string,
  message: string
): Promise<ChatResponse> {
  const response = await fetch(`/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: sessionId, query: message }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Chat request failed');
  }

  return response.json();
}

export async function getChatHistory(sessionId: string) {
  const response = await fetch(
    `/api/chat/history/${sessionId}`
  );

  if (!response.ok) {
    throw new Error('Failed to fetch chat history');
  }

  return response.json();
}

export async function clearSession(sessionId: string) {
  const response = await fetch(
    `/api/documents/session/${sessionId}`,
    {
      method: 'DELETE',
    }
  );

  if (!response.ok) {
    throw new Error('Failed to clear session');
  }

  return response.json();
}
