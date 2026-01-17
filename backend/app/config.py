"""Application configuration"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    APP_NAME: str = "Multi-Modal RAG API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173", 
        "http://localhost:3000",
        "https://multimodal-rag-frontend.onrender.com",
        "https://multimodal-rag-backend.onrender.com"
    ]
    
    # API Keys
    GROQ_API_KEY: str
    
    # Database
    DATABASE_URL: str = "sqlite:///./rag_app.db"
    
    # File Storage
    UPLOAD_DIR: Path = Path("./uploads")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".pdf"]
    
    # ChromaDB
    CHROMA_PERSIST_DIR: Path = Path("./chroma_data")
    
    # System Dependencies (cross-platform)
    TESSERACT_PATH: str = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR" if os.name == 'nt' else "/usr/bin")
    POPPLER_PATH: str = os.getenv("POPPLER_PATH", r"C:\Program Files\poppler\poppler-25.12.0\Library\bin" if os.name == 'nt' else "/usr/bin")
    
    # Processing
    CHUNK_MAX_CHARS: int = 3000
    CHUNK_NEW_AFTER_CHARS: int = 2400
    CHUNK_COMBINE_UNDER_CHARS: int = 500
    
    # Session Management
    SESSION_RETENTION_DAYS: int = 30
    
    # Embeddings
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    
    # LLM
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.0
    
    class Config:
        # Use root .env file (one level up from backend/)
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env that aren't in the model


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
