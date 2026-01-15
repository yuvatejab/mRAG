"""Custom exceptions and error handlers"""

from typing import Optional
from fastapi import HTTPException, status


class RAGException(Exception):
    """Base exception for RAG application"""
    
    def __init__(self, message: str, detail: Optional[str] = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class DocumentProcessingError(RAGException):
    """Exception raised during document processing"""
    pass


class VectorizationError(RAGException):
    """Exception raised during vectorization"""
    pass


class ChatError(RAGException):
    """Exception raised during chat operations"""
    pass


class SessionNotFoundError(RAGException):
    """Exception raised when session is not found"""
    pass


class DocumentNotFoundError(RAGException):
    """Exception raised when document is not found"""
    pass


class FileValidationError(RAGException):
    """Exception raised during file validation"""
    pass


def raise_http_exception(
    status_code: int,
    message: str,
    detail: Optional[str] = None
) -> None:
    """
    Raise HTTP exception with consistent format.
    
    Args:
        status_code: HTTP status code
        message: Error message
        detail: Optional detailed error information
    """
    raise HTTPException(
        status_code=status_code,
        detail={"error": message, "detail": detail}
    )


def handle_file_validation_error(filename: str, reason: str) -> None:
    """Handle file validation errors"""
    raise_http_exception(
        status.HTTP_400_BAD_REQUEST,
        f"Invalid file: {filename}",
        reason
    )


def handle_session_not_found(session_id: str) -> None:
    """Handle session not found errors"""
    raise_http_exception(
        status.HTTP_404_NOT_FOUND,
        "Session not found",
        f"Session ID: {session_id}"
    )


def handle_document_not_found(document_id: str) -> None:
    """Handle document not found errors"""
    raise_http_exception(
        status.HTTP_404_NOT_FOUND,
        "Document not found",
        f"Document ID: {document_id}"
    )


def handle_processing_error(document_id: str, stage: str, error: Exception) -> None:
    """Handle document processing errors"""
    raise_http_exception(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        f"Processing failed at {stage} stage",
        f"Document ID: {document_id}, Error: {str(error)}"
    )
