"""RAG (Retrieval-Augmented Generation) service"""

import json
import time
from typing import List, Dict, Any, Optional

from langchain_groq import ChatGroq

from app.config import settings
from app.services.vectorization_service import VectorizationService
from app.utils.logger import logger
from app.utils.error_handlers import ChatError


class RAGService:
    """Service for RAG operations with chat history"""
    
    def __init__(self):
        """Initialize RAG service"""
        self.vectorization_service = VectorizationService()
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self) -> None:
        """Initialize LLM"""
        try:
            logger.info(f"Initializing LLM: {settings.LLM_MODEL}")
            self.llm = ChatGroq(
                model=settings.LLM_MODEL,
                api_key=settings.GROQ_API_KEY,
                temperature=settings.LLM_TEMPERATURE
            )
            # Test connection
            self.llm.invoke("test")
            logger.info("LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise ChatError("Failed to initialize LLM", detail=str(e))
    
    async def query_with_history(
        self,
        query: str,
        session_id: str,
        chat_history: List[Dict[str, str]],
        num_chunks: int = 3,
        document_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Query RAG system with chat history context.
        
        Args:
            query: User query
            session_id: Session identifier
            chat_history: Previous chat messages
            num_chunks: Number of chunks to retrieve
            document_ids: Optional filter by document IDs
            
        Returns:
            Dictionary with answer and visual content
            
        Raises:
            ChatError: If query fails
        """
        try:
            start_time = time.time()
            logger.info(f"Processing query for session {session_id}: {query[:100]}")
            
            # Get vector store
            vectorstore = self.vectorization_service.get_vector_store(session_id)
            if not vectorstore:
                raise ChatError(
                    "No documents found",
                    detail="Please upload a document first"
                )
            
            # Retrieve relevant chunks
            retriever = vectorstore.as_retriever(search_kwargs={"k": num_chunks})
            
            # Add document filter if specified
            if document_ids:
                retriever.search_kwargs["filter"] = {
                    "document_id": {"$in": document_ids}
                }
            
            chunks = retriever.invoke(query)
            
            if not chunks:
                return {
                    "answer": "I couldn't find any relevant information in the uploaded documents.",
                    "chunks": [],
                    "tables": [],
                    "images": [],
                    "processing_time": time.time() - start_time
                }
            
            # Build context with chat history
            prompt = self._build_prompt_with_history(query, chunks, chat_history)
            
            # Generate answer
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Extract visual content
            visuals = self._extract_visuals(chunks)
            
            processing_time = time.time() - start_time
            logger.info(f"Query processed in {processing_time:.2f}s")
            
            return {
                "answer": answer,
                "chunks": [
                    {
                        "document_name": chunk.metadata.get("document_name"),
                        "chunk_id": chunk.metadata.get("chunk_id"),
                        "content": chunk.page_content[:200] + "..."
                    }
                    for chunk in chunks
                ],
                "tables": visuals["tables"],
                "images": visuals["images"],
                "processing_time": processing_time
            }
            
        except ChatError:
            raise
        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            raise ChatError("Failed to process query", detail=str(e))
    
    def _build_prompt_with_history(
        self,
        query: str,
        chunks: List[Any],
        chat_history: List[Dict[str, str]]
    ) -> str:
        """
        Build prompt with chat history context.
        
        Args:
            query: User query
            chunks: Retrieved chunks
            chat_history: Previous messages
            
        Returns:
            Formatted prompt
        """
        prompt = "You are a helpful AI assistant answering questions about documents.\n\n"
        
        # Add chat history (last 5 messages for context)
        if chat_history:
            prompt += "PREVIOUS CONVERSATION:\n"
            for msg in chat_history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt += f"{role.upper()}: {content}\n"
            prompt += "\n"
        
        # Add retrieved context
        prompt += "RELEVANT DOCUMENT CONTENT:\n"
        for i, chunk in enumerate(chunks, 1):
            prompt += f"--- Document {i} ---\n"
            
            # Get original content
            if "original_content" in chunk.metadata:
                original_data = json.loads(chunk.metadata["original_content"])
                
                # Add text
                raw_text = original_data.get("raw_text", "")
                if raw_text:
                    prompt += f"TEXT:\n{raw_text}\n\n"
                
                # Add tables
                tables_html = original_data.get("tables_html", [])
                if tables_html:
                    prompt += "TABLES:\n"
                    for j, table in enumerate(tables_html):
                        prompt += f"Table {j+1}:\n{table}\n\n"
                
                # Note images
                images = original_data.get("images_base64", [])
                if images:
                    prompt += f"[Note: This section contains {len(images)} image(s)]\n\n"
            
            prompt += "\n"
        
        # Add current query with improved instructions
        prompt += f"""
CURRENT QUESTION: {query}

INSTRUCTIONS:
- Provide a clear, direct answer based on the document content
- Use natural, conversational language
- DO NOT mention "as described in the document" or similar phrases
- DO NOT add disclaimers about previous conversations
- If referencing tables or images, mention them naturally (e.g., "The data shows..." or "As seen in the image...")
- If the information isn't in the documents, simply say "I don't have enough information in the document to answer that"
- Be concise and structured - use bullet points or paragraphs as appropriate
- Focus on answering the question directly

ANSWER:"""
        
        return prompt
    
    def _extract_visuals(self, chunks: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract visual content from chunks.
        
        Args:
            chunks: Retrieved chunks
            
        Returns:
            Dictionary with tables and images
        """
        tables = []
        images = []
        
        for i, chunk in enumerate(chunks):
            if "original_content" in chunk.metadata:
                original_data = json.loads(chunk.metadata["original_content"])
                
                # Extract tables
                tables_html = original_data.get("tables_html", [])
                for j, table in enumerate(tables_html):
                    tables.append({
                        "document_name": chunk.metadata.get("document_name"),
                        "table_index": j + 1,
                        "html": table
                    })
                
                # Extract images
                images_base64 = original_data.get("images_base64", [])
                for j, image in enumerate(images_base64):
                    images.append({
                        "document_name": chunk.metadata.get("document_name"),
                        "image_index": j + 1,
                        "base64": image
                    })
        
        return {"tables": tables, "images": images}
