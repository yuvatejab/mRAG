"""Chunking service"""

import json
from typing import List, Dict, Any, Optional

from unstructured.chunking.title import chunk_by_title

from app.config import settings
from app.utils.logger import logger
from app.utils.error_handlers import DocumentProcessingError
from app.utils.progress_tracker import ProgressTracker


class ChunkingService:
    """Service for chunking documents"""
    
    async def create_chunks(
        self,
        elements: List[Any],
        progress_tracker: Optional[ProgressTracker] = None
    ) -> List[Dict[str, Any]]:
        """
        Create chunks from document elements.
        
        Args:
            elements: List of document elements
            progress_tracker: Optional progress tracker
            
        Returns:
            List of chunks with metadata
            
        Raises:
            DocumentProcessingError: If chunking fails
        """
        try:
            logger.info(f"Starting chunking of {len(elements)} elements")
            
            if progress_tracker:
                await progress_tracker.start_stage(
                    "chunking",
                    f"Creating chunks from {len(elements)} elements"
                )
            
            # Create chunks
            chunks = chunk_by_title(
                elements,
                max_characters=settings.CHUNK_MAX_CHARS,
                new_after_n_chars=settings.CHUNK_NEW_AFTER_CHARS,
                combine_text_under_n_chars=settings.CHUNK_COMBINE_UNDER_CHARS
            )
            
            # Process chunks and extract metadata
            processed_chunks = []
            total_chunks = len(chunks)
            
            for i, chunk in enumerate(chunks):
                chunk_data = self._extract_chunk_metadata(chunk, i + 1)
                processed_chunks.append(chunk_data)
                
                # Update progress more frequently for better UX
                if progress_tracker:
                    # Calculate progress (10% to 90% range, leaving 0% for start and 100% for completion)
                    progress = int(10 + ((i + 1) / total_chunks * 80))
                    await progress_tracker.update(
                        "chunking",
                        progress,
                        {
                            "chunks_processed": i + 1, 
                            "total_chunks": total_chunks,
                            "message": f"Processing chunk {i + 1} of {total_chunks}..."
                        }
                    )
            
            logger.info(f"Chunking complete: {len(processed_chunks)} chunks created")
            
            if progress_tracker:
                # Create chunk summary with full transparency
                chunk_details = [
                    {
                        "id": c["chunk_id"],
                        "text": c["text"][:500] + "..." if len(c["text"]) > 500 else c["text"],  # Preview first 500 chars
                        "fullTextLength": len(c["text"]),
                        "hasText": bool(c["text"]),
                        "hasTable": len(c["tables"]) > 0,
                        "hasImage": len(c["images"]) > 0,
                        "tableCount": len(c["tables"]),
                        "imageCount": len(c["images"]),
                        "metadata": {
                            "tables": len(c["tables"]),
                            "images": len(c["images"])
                        }
                    }
                    for c in processed_chunks
                ]
                
                await progress_tracker.complete_stage(
                    "chunking",
                    {
                        "chunk_count": len(processed_chunks),
                        "chunk_details": chunk_details,  # Send all chunks for full transparency
                        "message": f"Created {len(processed_chunks)} chunks"
                    }
                )
            
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Chunking failed: {e}", exc_info=True)
            if progress_tracker:
                await progress_tracker.error("chunking", str(e))
            raise DocumentProcessingError(
                "Failed to create chunks",
                detail=str(e)
            )
    
    def _extract_chunk_metadata(self, chunk: Any, chunk_id: int) -> Dict[str, Any]:
        """
        Extract metadata from a chunk.
        
        Args:
            chunk: Chunk object
            chunk_id: Chunk identifier
            
        Returns:
            Dictionary with chunk data and metadata
        """
        chunk_data = {
            "chunk_id": chunk_id,
            "text": chunk.text,
            "tables": [],
            "images": [],
            "metadata": {}
        }
        
        # Extract tables and images from original elements
        if hasattr(chunk, 'metadata') and hasattr(chunk.metadata, 'orig_elements'):
            for element in chunk.metadata.orig_elements:
                element_type = type(element).__name__
                
                # Handle tables
                if element_type == 'Table':
                    table_html = getattr(element.metadata, 'text_as_html', element.text)
                    chunk_data['tables'].append(table_html)
                
                # Handle images
                elif element_type == 'Image':
                    if hasattr(element, 'metadata') and hasattr(element.metadata, 'image_base64'):
                        chunk_data['images'].append(element.metadata.image_base64)
        
        return chunk_data
