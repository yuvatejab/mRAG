"""SQLAlchemy database models"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class DocumentStatus(str, enum.Enum):
    """Document processing status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PARTITIONING = "partitioning"
    CHUNKING = "chunking"
    VECTORIZING = "vectorizing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(str, enum.Enum):
    """Chat message role"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Session(Base):
    """User session model"""
    __tablename__ = "sessions"
    
    session_id = Column(String(36), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    documents = relationship("Document", back_populates="session", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class Document(Base):
    """Document metadata model"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.session_id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADING, nullable=False)
    
    # Processing metadata
    element_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    element_counts = Column(JSON, default={})  # {"text": 100, "table": 5, "image": 3}
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="documents")
    messages = relationship("ChatMessage", back_populates="document")
    progress_records = relationship("ProcessingProgress", back_populates="document", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.session_id"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True, index=True)
    
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Visual content metadata (for assistant messages)
    visuals = Column(JSON, nullable=True)  # {"tables": [...], "images": [...], "chunks": [...]}
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    session = relationship("Session", back_populates="messages")
    document = relationship("Document", back_populates="messages")


class ProcessingProgress(Base):
    """Document processing progress tracking"""
    __tablename__ = "processing_progress"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    
    stage = Column(String(50), nullable=False)  # partitioning, chunking, vectorization
    progress = Column(Integer, default=0)  # 0-100
    details = Column(JSON, nullable=True)  # Stage-specific details
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="progress_records")
