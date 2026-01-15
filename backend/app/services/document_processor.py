"""Document processing service"""

import os
from typing import Dict, List, Any, Optional, Callable, Awaitable
from pathlib import Path

from unstructured.partition.pdf import partition_pdf

from app.config import settings
from app.utils.logger import logger
from app.utils.error_handlers import DocumentProcessingError
from app.utils.progress_tracker import ProgressTracker


class DocumentProcessor:
    """Service for processing PDF documents"""
    
    def __init__(self):
        """Initialize document processor"""
        # Set system paths
        os.environ["PATH"] = f"{settings.TESSERACT_PATH}{os.pathsep}{os.environ.get('PATH', '')}"
        os.environ["TESSDATA_PREFIX"] = f"{settings.TESSERACT_PATH}\\tessdata"
        os.environ["PATH"] = f"{settings.POPPLER_PATH}{os.pathsep}{os.environ.get('PATH', '')}"
    
    async def partition_pdf(
        self,
        file_path: str,
        progress_tracker: Optional[ProgressTracker] = None
    ) -> Dict[str, Any]:
        """
        Extract elements from PDF using unstructured.
        
        Args:
            file_path: Path to PDF file
            progress_tracker: Optional progress tracker
            
        Returns:
            Dictionary with elements and counts
            
        Raises:
            DocumentProcessingError: If processing fails
        """
        try:
            logger.info(f"Starting PDF partitioning: {file_path}")
            
            if progress_tracker:
                await progress_tracker.start_stage(
                    "partitioning",
                    f"Extracting elements from {Path(file_path).name}"
                )
            
            # Extract elements - using fast strategy for better performance
            # Note: Can switch to "hi_res" for better accuracy at the cost of speed
            
            # Send intermediate progress updates during partitioning
            import asyncio
            
            # Start partitioning in background and send progress updates
            async def partition_with_progress():
                # Send 25% progress
                if progress_tracker:
                    await progress_tracker.update("partitioning", 25, {"message": "Analyzing document structure..."})
                
                # Run the blocking partition_pdf in a thread pool
                loop = asyncio.get_event_loop()
                elements = await loop.run_in_executor(
                    None,
                    lambda: partition_pdf(
                        filename=file_path,
                        strategy="hi_res",
                        infer_table_structure=True,
                        extract_image_block_types=["Image"],
                        extract_image_block_to_payload=True,
                        languages=["eng"],
                        poppler_path=settings.POPPLER_PATH,
                        include_page_breaks=False,
                        chunking_strategy=None
                    )
                )
                
                # Send 75% progress after partitioning
                if progress_tracker:
                    await progress_tracker.update("partitioning", 75, {"message": "Processing extracted elements..."})
                
                return elements
            
            elements = await partition_with_progress()
            
            # Count element types
            element_counts = {
                "text": 0,
                "table": 0,
                "image": 0,
                "other": 0
            }
            
            for element in elements:
                element_type = type(element).__name__
                if element_type == "Table":
                    element_counts["table"] += 1
                elif element_type == "Image":
                    element_counts["image"] += 1
                elif element_type in ["Title", "NarrativeText", "ListItem", "Text"]:
                    element_counts["text"] += 1
                else:
                    element_counts["other"] += 1
            
            total_elements = len(elements)
            
            logger.info(
                f"PDF partitioning complete: {total_elements} elements "
                f"(text: {element_counts['text']}, "
                f"tables: {element_counts['table']}, "
                f"images: {element_counts['image']})"
            )
            
            if progress_tracker:
                await progress_tracker.complete_stage(
                    "partitioning",
                    {
                        "element_counts": element_counts,
                        "total_elements": total_elements,
                        "message": f"Extracted {total_elements} elements"
                    }
                )
            
            return {
                "elements": elements,
                "counts": element_counts,
                "total": total_elements
            }
            
        except Exception as e:
            logger.error(f"PDF partitioning failed: {e}", exc_info=True)
            if progress_tracker:
                await progress_tracker.error("partitioning", str(e))
            raise DocumentProcessingError(
                "Failed to partition PDF",
                detail=str(e)
            )
