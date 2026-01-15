"""Pydantic schemas for request/response validation"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.models import DocumentStatus, MessageRole


# Session Schemas
class SessionCreate(BaseModel):
    """Session creation schema"""
    session_id: str = Field(..., description="Unique session identifier")


class SessionResponse(BaseModel):
    """Session response schema"""
    session_id: str
    created_at: datetime
    last_active: datetime
    
    class Config:
        from_attributes = True


# Document Schemas
class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    document_id: str
    filename: str
    status: DocumentStatus
    message: str


class DocumentResponse(BaseModel):
    """Document response schema"""
    id: str
    session_id: str
    filename: str
    file_size: int
    status: DocumentStatus
    element_count: int
    chunk_count: int
    element_counts: Dict[str, int]
    uploaded_at: datetime
    processed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


# Progress Schemas
class ProgressDetails(BaseModel):
    """Progress details"""
    element_counts: Optional[Dict[str, int]] = None
    chunk_count: Optional[int] = None
    chunk_details: Optional[List[Dict[str, Any]]] = None
    vector_store_status: Optional[str] = None
    message: Optional[str] = None


class ProgressUpdate(BaseModel):
    """Progress update schema"""
    document_id: str
    stage: str
    progress: int = Field(..., ge=0, le=100)
    details: Optional[ProgressDetails] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Chat Schemas
class ChatRequest(BaseModel):
    """Chat request schema"""
    session_id: str
    query: str = Field(..., min_length=1, max_length=2000)
    document_ids: Optional[List[str]] = None  # Filter by specific documents
    num_chunks: int = Field(default=3, ge=1, le=10)


class VisualContent(BaseModel):
    """Visual content in chat response"""
    tables: List[Dict[str, Any]] = []
    images: List[Dict[str, Any]] = []
    chunks: List[Dict[str, Any]] = []


class ChatResponse(BaseModel):
    """Chat response schema"""
    message_id: str
    answer: str
    visuals: VisualContent
    timestamp: datetime
    processing_time: float


class ChatMessage(BaseModel):
    """Chat message schema"""
    id: str
    role: MessageRole
    content: str
    visuals: Optional[Dict[str, Any]]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Chat history response"""
    session_id: str
    messages: List[ChatMessage]
    total_count: int


# Cleanup Schemas
class CleanupResponse(BaseModel):
    """Cleanup response schema"""
    status: str
    message: str
    deleted_items: Dict[str, int]


# Error Schemas
class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
