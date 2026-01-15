"""Chat management service"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import ChatMessage, MessageRole
from app.schemas import ChatMessage as ChatMessageSchema
from app.utils.logger import logger


class ChatService:
    """Service for managing chat messages"""
    
    @staticmethod
    def create_message(
        db: Session,
        session_id: str,
        role: MessageRole,
        content: str,
        document_id: Optional[str] = None,
        visuals: Optional[dict] = None
    ) -> ChatMessage:
        """
        Create a new chat message.
        
        Args:
            db: Database session
            session_id: Session identifier
            role: Message role
            content: Message content
            document_id: Optional document identifier
            visuals: Optional visual content
            
        Returns:
            Created message
        """
        message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            document_id=document_id,
            role=role,
            content=content,
            visuals=visuals,
            timestamp=datetime.utcnow()
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        logger.info(f"Created chat message: {message.id} for session {session_id}")
        return message
    
    @staticmethod
    def get_history(
        db: Session,
        session_id: str,
        limit: int = 50
    ) -> List[ChatMessage]:
        """
        Get chat history for a session.
        
        Args:
            db: Database session
            session_id: Session identifier
            limit: Maximum number of messages
            
        Returns:
            List of messages
        """
        messages = db.query(ChatMessage)\
            .filter(ChatMessage.session_id == session_id)\
            .order_by(ChatMessage.timestamp.desc())\
            .limit(limit)\
            .all()
        
        return list(reversed(messages))
    
    @staticmethod
    def clear_history(
        db: Session,
        session_id: str
    ) -> int:
        """
        Clear chat history for a session.
        
        Args:
            db: Database session
            session_id: Session identifier
            
        Returns:
            Number of deleted messages
        """
        count = db.query(ChatMessage)\
            .filter(ChatMessage.session_id == session_id)\
            .delete()
        
        db.commit()
        logger.info(f"Cleared {count} messages for session {session_id}")
        return count
    
    @staticmethod
    def get_history_for_context(
        db: Session,
        session_id: str,
        limit: int = 10
    ) -> List[dict]:
        """
        Get recent chat history formatted for LLM context.
        
        Args:
            db: Database session
            session_id: Session identifier
            limit: Maximum number of messages
            
        Returns:
            List of message dictionaries
        """
        messages = ChatService.get_history(db, session_id, limit)
        
        return [
            {
                "role": msg.role.value,
                "content": msg.content
            }
            for msg in messages
        ]
