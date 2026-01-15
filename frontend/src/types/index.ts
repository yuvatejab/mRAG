export interface ChunkDetail {
  id: number;
  text: string;
  fullTextLength: number;
  hasText: boolean;
  hasTable: boolean;
  hasImage: boolean;
  tableCount: number;
  imageCount: number;
  metadata?: {
    tables: number;
    images: number;
  };
}

export interface ProcessingProgress {
  stage: 'uploading' | 'partitioning' | 'chunking' | 'vectorization' | 'completed';
  status: 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  details?: {
    filename?: string;
    file_size?: number;
    elements_count?: number;
    chunks_count?: number;
    vectors_stored?: number;
    element_types?: Record<string, number>;
    chunk_details?: ChunkDetail[];
  };
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: {
    chunks_used?: number;
    has_tables?: boolean;
    has_images?: boolean;
    tables?: string[];
    images?: string[];
  };
}

export interface Document {
  id: string;
  filename: string;
  upload_date: string;
  status: string;
}
