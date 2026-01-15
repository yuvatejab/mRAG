"""Progress tracking utilities"""

from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

from app.schemas import ProgressUpdate, ProgressDetails
from app.utils.logger import logger


class ProgressTracker:
    """Track and report processing progress"""
    
    def __init__(
        self,
        document_id: str,
        callback: Optional[Callable[[ProgressUpdate], Awaitable[None]]] = None
    ):
        """
        Initialize progress tracker.
        
        Args:
            document_id: Document being processed
            callback: Async callback function for progress updates
        """
        self.document_id = document_id
        self.callback = callback
        self.current_stage = None
        self.current_progress = 0
    
    async def update(
        self,
        stage: str,
        progress: int,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update progress.
        
        Args:
            stage: Processing stage name
            progress: Progress percentage (0-100)
            details: Optional stage-specific details
        """
        self.current_stage = stage
        self.current_progress = progress
        
        # Create progress update
        progress_update = ProgressUpdate(
            document_id=self.document_id,
            stage=stage,
            progress=progress,
            details=ProgressDetails(**details) if details else None,
            timestamp=datetime.utcnow()
        )
        
        # Log progress
        logger.info(
            f"Progress update - Document: {self.document_id}, "
            f"Stage: {stage}, Progress: {progress}%"
        )
        
        # Call callback if provided
        if self.callback:
            try:
                await self.callback(progress_update)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    async def start_stage(self, stage: str, message: Optional[str] = None) -> None:
        """Start a new processing stage"""
        details = {"message": message} if message else None
        await self.update(stage, 0, details)
    
    async def complete_stage(self, stage: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Complete a processing stage"""
        await self.update(stage, 100, details)
    
    async def error(self, stage: str, error_message: str) -> None:
        """Report an error"""
        await self.update(
            stage,
            self.current_progress,
            {"message": error_message, "error": True}
        )
