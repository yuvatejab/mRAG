import { useState } from 'react';
import { uploadDocument } from '../services/api';

export function useUpload(sessionId: string) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const upload = async (file: File) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      const result = await uploadDocument(sessionId, file);
      return { success: true, ...result };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setUploadError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsUploading(false);
    }
  };

  return {
    uploadDocument: upload,
    isUploading,
    uploadError,
  };
}
