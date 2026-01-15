"""Upload API endpoints"""

import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models import Document, DocumentStatus, Session as SessionModel
from app.schemas import DocumentUploadResponse, DocumentResponse
from app.services.document_processor import DocumentProcessor
from app.services.chunking_service import ChunkingService
from app.services.vectorization_service import VectorizationService
from app.utils.logger import logger
from app.utils.error_handlers import handle_file_validation_error
from app.utils.progress_tracker import ProgressTracker

router = APIRouter(prefix="/upload", tags=["upload"])


async def process_document_background(
    document_id: str,
    file_path: str,
    session_id: str,
    document_name: str
):
    """Background task to process uploaded document"""
    from app.database import SessionLocal
    from app.api.websocket import send_progress_update
    db = SessionLocal()
    
    # Accumulate details across stages to maintain context
    accumulated_details = {}
    
    # Create progress callback that sends WebSocket updates
    async def progress_callback(progress_update):
        """Send progress update via WebSocket"""
        nonlocal accumulated_details
        
        # Extract and accumulate details from this update
        if progress_update.details:
            # Extract all available details
            if hasattr(progress_update.details, 'element_counts') and progress_update.details.element_counts:
                accumulated_details['element_types'] = progress_update.details.element_counts
            if hasattr(progress_update.details, 'chunk_count') and progress_update.details.chunk_count:
                accumulated_details['chunks_count'] = progress_update.details.chunk_count
            if hasattr(progress_update.details, 'total_elements') and progress_update.details.total_elements:
                accumulated_details['elements_count'] = progress_update.details.total_elements
            if hasattr(progress_update.details, 'vectors_count') and progress_update.details.vectors_count:
                accumulated_details['vectors_stored'] = progress_update.details.vectors_count
            # Add chunk details for transparency
            if hasattr(progress_update.details, 'chunk_details') and progress_update.details.chunk_details:
                accumulated_details['chunk_details'] = progress_update.details.chunk_details
            # Add filename if available
            if hasattr(progress_update.details, 'filename') and progress_update.details.filename:
                accumulated_details['filename'] = progress_update.details.filename
            if hasattr(progress_update.details, 'file_size') and progress_update.details.file_size:
                accumulated_details['file_size'] = progress_update.details.file_size
        
        message = (progress_update.details.message if progress_update.details and 
                  hasattr(progress_update.details, 'message') and progress_update.details.message 
                  else f"Processing: {progress_update.stage}")
        
        # Send all accumulated details with each update
        await send_progress_update(session_id, {
            "stage": progress_update.stage,
            "status": "processing",
            "progress": progress_update.progress,
            "message": message,
            "details": accumulated_details.copy()  # Send a copy of accumulated details
        })
    
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document not found: {document_id}")
            return
        
        # Initialize services
        doc_processor = DocumentProcessor()
        chunking_service = ChunkingService()
        vectorization_service = VectorizationService()
        
        # Create progress tracker with WebSocket callback
        progress_tracker = ProgressTracker(document_id, callback=progress_callback)
        
        # Initialize accumulated details with document info
        accumulated_details['filename'] = document.filename
        accumulated_details['file_size'] = document.file_size
        
        # Update status and send immediate progress
        document.status = DocumentStatus.PARTITIONING
        db.commit()
        
        # Send initial partitioning update with document info
        await send_progress_update(session_id, {
            "stage": "partitioning",
            "status": "processing",
            "progress": 0,
            "message": "Starting document analysis...",
            "details": accumulated_details.copy()
        })
        
        # Step 1: Partition PDF
        partition_result = await doc_processor.partition_pdf(file_path, progress_tracker)
        document.element_count = partition_result["total"]
        document.element_counts = partition_result["counts"]
        db.commit()
        
        # Update accumulated details with partition results
        accumulated_details['elements_count'] = partition_result['total']
        accumulated_details['element_types'] = partition_result['counts']
        
        # Step 2: Create chunks
        document.status = DocumentStatus.CHUNKING
        db.commit()
        
        # Send chunking start update with all accumulated details
        await send_progress_update(session_id, {
            "stage": "chunking",
            "status": "processing",
            "progress": 0,
            "message": f"Creating chunks from {partition_result['total']} elements...",
            "details": accumulated_details.copy()
        })
        
        chunks = await chunking_service.create_chunks(
            partition_result["elements"],
            progress_tracker
        )
        document.chunk_count = len(chunks)
        db.commit()
        
        # Update accumulated details with chunk count
        accumulated_details['chunks_count'] = len(chunks)
        
        # Step 3: Vectorize
        document.status = DocumentStatus.VECTORIZING
        db.commit()
        
        # Send vectorization start update with all accumulated details
        await send_progress_update(session_id, {
            "stage": "vectorization",
            "status": "processing",
            "progress": 0,
            "message": f"Creating embeddings for {len(chunks)} chunks...",
            "details": accumulated_details.copy()
        })
        
        await vectorization_service.create_vector_store(
            chunks,
            session_id,
            document_id,
            document_name,
            progress_tracker
        )
        
        # Complete
        document.status = DocumentStatus.COMPLETED
        db.commit()
        
        # Update accumulated details with final counts
        accumulated_details['elements_count'] = document.element_count
        accumulated_details['chunks_count'] = document.chunk_count
        accumulated_details['element_types'] = document.element_counts
        
        # Send completion update via WebSocket with all accumulated details
        await send_progress_update(session_id, {
            "stage": "completed",
            "status": "completed",
            "progress": 100,
            "message": "Document processing completed successfully!",
            "details": accumulated_details.copy()
        })
        
        logger.info(f"Document processing completed: {document_id}")
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)
        document.status = DocumentStatus.FAILED
        document.error_message = str(e)
        db.commit()
        
        # Send error update via WebSocket
        await send_progress_update(session_id, {
            "stage": "error",
            "status": "error",
            "progress": 0,
            "message": f"Processing failed: {str(e)}",
            "details": {}
        })
    
    finally:
        db.close()


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(None),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Upload a PDF document for processing.
    
    Args:
        file: PDF file to upload
        session_id: Session identifier
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Upload response with document ID and status
    """
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Ensure session exists
        session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
        if not session:
            session = SessionModel(session_id=session_id)
            db.add(session)
            db.commit()
        
        # Validate file
        if not file.filename.endswith('.pdf'):
            handle_file_validation_error(file.filename, "Only PDF files are allowed")
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset
        
        if file_size > settings.MAX_FILE_SIZE:
            handle_file_validation_error(
                file.filename,
                f"File size exceeds {settings.MAX_FILE_SIZE / (1024*1024)}MB limit"
            )
        
        # Create document record
        document_id = str(uuid.uuid4())
        file_path = settings.UPLOAD_DIR / f"{document_id}_{file.filename}"
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create database record
        document = Document(
            id=document_id,
            session_id=session_id,
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            status=DocumentStatus.UPLOADING
        )
        
        db.add(document)
        db.commit()
        
        logger.info(f"Document uploaded: {document_id} - {file.filename}")
        
        # Send immediate WebSocket update to show upload success
        from app.api.websocket import send_progress_update
        
        # Send upload confirmation immediately (in background task to not block response)
        async def send_upload_notification():
            await send_progress_update(session_id, {
                "stage": "uploading",
                "status": "processing",
                "progress": 100,
                "message": f"File '{file.filename}' uploaded successfully! Starting processing...",
                "details": {
                    "file_size": file_size,
                    "filename": file.filename
                }
            })
        
        background_tasks.add_task(send_upload_notification)
        
        # Start background processing
        background_tasks.add_task(
            process_document_background,
            document_id,
            str(file_path),
            session_id,
            file.filename
        )
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            status=DocumentStatus.PROCESSING,
            message="Document uploaded successfully and processing started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{document_id}")
async def get_progress(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get processing progress for a document.
    
    Args:
        document_id: Document identifier
        db: Database session
        
    Returns:
        Progress information
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "document_id": document_id,
        "status": document.status.value,
        "element_count": document.element_count,
        "chunk_count": document.chunk_count,
        "element_counts": document.element_counts,
        "error_message": document.error_message
    }


@router.get("/documents/{session_id}", response_model=list[DocumentResponse])
async def get_documents(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all documents for a session.
    
    Args:
        session_id: Session identifier
        db: Database session
        
    Returns:
        List of documents
    """
    documents = db.query(Document)\
        .filter(Document.session_id == session_id)\
        .order_by(Document.uploaded_at.desc())\
        .all()
    
    return documents
