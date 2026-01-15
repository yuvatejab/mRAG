"""Chat API endpoints"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MessageRole
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    CleanupResponse,
    VisualContent
)
from app.services.rag_service import RAGService
from app.services.chat_service import ChatService
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
rag_service = RAGService()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get AI response.
    
    Args:
        request: Chat request with query and session info
        db: Database session
        
    Returns:
        Chat response with answer and visuals
    """
    try:
        logger.info(f"Chat request from session {request.session_id}: {request.query[:100]}")
        
        # Get chat history for context
        chat_history = ChatService.get_history_for_context(
            db,
            request.session_id,
            limit=10
        )
        
        # Query RAG system
        result = await rag_service.query_with_history(
            query=request.query,
            session_id=request.session_id,
            chat_history=chat_history,
            num_chunks=request.num_chunks,
            document_ids=request.document_ids
        )
        
        # Save user message
        ChatService.create_message(
            db,
            session_id=request.session_id,
            role=MessageRole.USER,
            content=request.query
        )
        
        # Save assistant message
        message = ChatService.create_message(
            db,
            session_id=request.session_id,
            role=MessageRole.ASSISTANT,
            content=result["answer"],
            visuals={
                "chunks": result["chunks"],
                "tables": result["tables"],
                "images": result["images"]
            }
        )
        
        return ChatResponse(
            message_id=message.id,
            answer=result["answer"],
            visuals=VisualContent(
                tables=result["tables"],
                images=result["images"],
                chunks=result["chunks"]
            ),
            timestamp=message.timestamp,
            processing_time=result["processing_time"]
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_history(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a session.
    
    Args:
        session_id: Session identifier
        limit: Maximum number of messages
        db: Database session
        
    Returns:
        Chat history
    """
    messages = ChatService.get_history(db, session_id, limit)
    
    return ChatHistoryResponse(
        session_id=session_id,
        messages=messages,
        total_count=len(messages)
    )


@router.delete("/history/{session_id}", response_model=CleanupResponse)
async def clear_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Clear chat history for a session.
    
    Args:
        session_id: Session identifier
        db: Database session
        
    Returns:
        Cleanup response
    """
    count = ChatService.clear_history(db, session_id)
    
    logger.info(f"Cleared chat history for session {session_id}: {count} messages")
    
    return CleanupResponse(
        status="success",
        message=f"Chat history cleared successfully",
        deleted_items={"messages": count}
    )
