# Backend Dockerfile - Optimized and Working
FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    TESSERACT_PATH=/usr/bin/tesseract \
    POPPLER_PATH=/usr/bin

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libmagic1 \
    curl \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip setuptools wheel

# Group 1: Core web framework (fast - ~15s)
RUN pip install \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    python-multipart==0.0.6 \
    pydantic==2.5.3 \
    pydantic-settings==2.1.0 \
    sqlalchemy==2.0.25 \
    python-dotenv==1.0.0 \
    websockets==12.0

# Group 2: Document processing (fast - ~5s)
RUN pip install \
    pytesseract==0.3.10 \
    pdf2image==1.17.0 \
    pillow==10.2.0

# Group 3: LLM API (fast - ~3s)
RUN pip install groq

# Group 4: Vector database (medium - ~80s)
RUN pip install chromadb==0.4.22

# Group 5: Embeddings (slow but necessary - ~4-5 min)
# This downloads ML models which takes time but is unavoidable
RUN pip install sentence-transformers

# Group 6: LangChain ecosystem (medium - ~30s)
RUN pip install \
    langchain \
    langchain-community \
    langchain-chroma \
    langchain-huggingface \
    langchain-groq

# Group 7: Unstructured (medium - ~90s)
RUN pip install "unstructured[pdf]==0.11.8"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads chroma_data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "app.main"]
