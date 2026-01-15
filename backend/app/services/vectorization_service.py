"""Vectorization service"""

import json
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings
from app.utils.logger import logger
from app.utils.error_handlers import VectorizationError
from app.utils.progress_tracker import ProgressTracker


class VectorizationService:
    """Service for creating and managing vector stores"""
    
    def __init__(self):
        """Initialize vectorization service"""
        self.embeddings = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self) -> None:
        """Initialize embedding model"""
        try:
            logger.info(f"Initializing embeddings model: {settings.EMBEDDING_MODEL}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={
                    'normalize_embeddings': True,
                    'batch_size': 32  # Process in batches for better performance
                }
            )
            logger.info("Embeddings model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise VectorizationError("Failed to initialize embeddings", detail=str(e))
    
    async def create_vector_store(
        self,
        chunks: List[Dict[str, Any]],
        session_id: str,
        document_id: str,
        document_name: str,
        progress_tracker: Optional[ProgressTracker] = None
    ) -> str:
        """
        Create vector store from chunks.
        
        Args:
            chunks: List of processed chunks
            session_id: Session identifier
            document_id: Document identifier
            document_name: Document filename
            progress_tracker: Optional progress tracker
            
        Returns:
            Collection name
            
        Raises:
            VectorizationError: If vectorization fails
        """
        try:
            logger.info(f"Creating vector store for session {session_id}, document {document_id}")
            
            if progress_tracker:
                await progress_tracker.start_stage(
                    "vectorization",
                    f"Creating vector store with {len(chunks)} chunks"
                )
            
            # Create LangChain documents
            documents = []
            total_chunks = len(chunks)
            
            for i, chunk in enumerate(chunks):
                # Create enhanced content for embedding
                enhanced_content = chunk["text"]
                
                # Add table information
                if chunk["tables"]:
                    enhanced_content += f"\n[Contains {len(chunk['tables'])} table(s)]"
                
                # Add image information
                if chunk["images"]:
                    enhanced_content += f"\n[Contains {len(chunk['images'])} image(s)]"
                
                # Create document with rich metadata
                doc = Document(
                    page_content=enhanced_content,
                    metadata={
                        "session_id": session_id,
                        "document_id": document_id,
                        "document_name": document_name,
                        "chunk_id": chunk["chunk_id"],
                        "original_content": json.dumps({
                            "raw_text": chunk["text"],
                            "tables_html": chunk["tables"],
                            "images_base64": chunk["images"]
                        })
                    }
                )
                documents.append(doc)
                
                # Update progress more frequently (10% to 50% range for document creation)
                if progress_tracker:
                    progress = int(10 + ((i + 1) / total_chunks * 40))
                    await progress_tracker.update(
                        "vectorization",
                        progress,
                        {
                            "vectors_created": i + 1, 
                            "total_chunks": total_chunks,
                            "message": f"Preparing document {i + 1} of {total_chunks}..."
                        }
                    )
            
            # Create collection name (one per session)
            collection_name = f"session_{session_id}"
            
            # Create or get vector store
            persist_directory = str(settings.CHROMA_PERSIST_DIR / collection_name)
            
            # Send progress update before embedding generation
            if progress_tracker:
                await progress_tracker.update(
                    "vectorization",
                    55,
                    {"message": "Generating embeddings..."}
                )
            
            # Process in batches for better performance
            batch_size = 50  # Process 50 documents at a time
            if len(documents) <= batch_size:
                # Small batch - process all at once
                if progress_tracker:
                    await progress_tracker.update(
                        "vectorization",
                        70,
                        {"message": "Creating vector store..."}
                    )
                
                vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=persist_directory,
                    collection_name=collection_name,
                    collection_metadata={"hnsw:space": "cosine"}
                )
                
                if progress_tracker:
                    await progress_tracker.update(
                        "vectorization",
                        90,
                        {"message": "Storing vectors..."}
                    )
            else:
                # Large batch - process incrementally
                vectorstore = None
                total_batches = (len(documents) + batch_size - 1) // batch_size
                
                for batch_idx, i in enumerate(range(0, len(documents), batch_size)):
                    batch = documents[i:i + batch_size]
                    
                    # Update progress (50% to 90% range for batch processing)
                    if progress_tracker:
                        batch_progress = int(50 + ((batch_idx + 1) / total_batches * 40))
                        await progress_tracker.update(
                            "vectorization",
                            batch_progress,
                            {"message": f"Processing batch {batch_idx + 1} of {total_batches}..."}
                        )
                    
                    if vectorstore is None:
                        vectorstore = Chroma.from_documents(
                            documents=batch,
                            embedding=self.embeddings,
                            persist_directory=persist_directory,
                            collection_name=collection_name,
                            collection_metadata={"hnsw:space": "cosine"}
                        )
                    else:
                        vectorstore.add_documents(batch)
                    
                    # Update progress
                    if progress_tracker:
                        progress = int(min(i + batch_size, len(documents)) / len(documents) * 100)
                        await progress_tracker.update(
                            "vectorization",
                            progress,
                            {"vectors_stored": min(i + batch_size, len(documents)), "total_chunks": len(documents)}
                        )
            
            logger.info(
                f"Vector store created successfully: {collection_name}, "
                f"{len(documents)} vectors"
            )
            
            if progress_tracker:
                await progress_tracker.complete_stage(
                    "vectorization",
                    {
                        "vector_store_status": "success",
                        "collection_name": collection_name,
                        "vectors_count": len(documents),
                        "message": f"Stored {len(documents)} vectors successfully"
                    }
                )
            
            return collection_name
            
        except Exception as e:
            logger.error(f"Vectorization failed: {e}", exc_info=True)
            if progress_tracker:
                await progress_tracker.error("vectorization", str(e))
            raise VectorizationError(
                "Failed to create vector store",
                detail=str(e)
            )
    
    def get_vector_store(self, session_id: str) -> Optional[Chroma]:
        """
        Get existing vector store for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Vector store or None if not found
        """
        try:
            collection_name = f"session_{session_id}"
            persist_directory = str(settings.CHROMA_PERSIST_DIR / collection_name)
            
            vectorstore = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings,
                collection_name=collection_name
            )
            
            return vectorstore
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return None
    
    def delete_vector_store(self, session_id: str) -> bool:
        """
        Delete vector store for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection_name = f"session_{session_id}"
            persist_directory = settings.CHROMA_PERSIST_DIR / collection_name
            
            if persist_directory.exists():
                import shutil
                shutil.rmtree(persist_directory)
                logger.info(f"Deleted vector store: {collection_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete vector store: {e}")
            return False
