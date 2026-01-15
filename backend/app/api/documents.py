"""Document management endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, Session as SessionModel
from app.schemas import CleanupResponse
from app.services.vectorization_service import VectorizationService
from app.utils.logger import logger
import shutil
from pathlib import Path

router = APIRouter(prefix="/documents", tags=["documents"])


@router.delete("/{document_id}", response_model=CleanupResponse)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a specific document.
    
    Args:
        document_id: Document identifier
        db: Database session
        
    Returns:
        Cleanup response
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    try:
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    logger.info(f"Deleted document: {document_id}")
    
    return CleanupResponse(
        status="success",
        message="Document deleted successfully",
        deleted_items={"documents": 1}
    )


@router.delete("/session/{session_id}", response_model=CleanupResponse)
async def clear_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Clear all data for a session (documents, chat history, vectors).
    
    Args:
        session_id: Session identifier
        db: Database session
        
    Returns:
        Cleanup response
    """
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Count items
    document_count = len(session.documents)
    message_count = len(session.messages)
    
    # Delete uploaded files
    for document in session.documents:
        try:
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
    
    # Delete vector store
    vectorization_service = VectorizationService()
    vector_deleted = vectorization_service.delete_vector_store(session_id)
    
    # Delete session (cascades to documents and messages)
    db.delete(session)
    db.commit()
    
    logger.info(
        f"Cleared session {session_id}: "
        f"{document_count} documents, {message_count} messages"
    )
    
    return CleanupResponse(
        status="success",
        message="Session cleared successfully",
        deleted_items={
            "documents": document_count,
            "messages": message_count,
            "vector_store": 1 if vector_deleted else 0
        }
    )
