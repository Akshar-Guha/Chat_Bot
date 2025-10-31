"""
FastAPI backend for EideticRAG
"""

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from pathlib import Path
import sys
import os
import tempfile

# Load environment variables from .env file
load_dotenv()

# Add parent to path before importing project modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.ingestor import DocumentIngestor
from core.chunker import TextChunker
from core.embeddings import EmbeddingGenerator
from core.vector_index import VectorIndex
from generation.rag_pipeline import RAGPipeline

# Initialize FastAPI app
app = FastAPI(title="EideticRAG API", version="0.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for components
INDEX_DIR = Path("./index")
DEFAULT_OLLAMA_MODEL = "llama3.2:1b"
rag_pipeline = None


# Request/Response models
class GeneratorSettings(BaseModel):
    type: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None


class QueryRequest(BaseModel):
    query: str
    k: Optional[int] = 5
    filters: Optional[Dict] = None
    generator: Optional[GeneratorSettings] = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    chunks: List[Dict]
    provenance: List[Dict]
    metadata: Dict
    spike_info: Optional[Dict] = None  # SpikingBrain-specific information


class IngestResponse(BaseModel):
    doc_id: str
    filename: str
    num_chunks: int
    message: str


class ModelInfoResponse(BaseModel):
    model_name: str
    model_type: str
    generator_type: str
    device: str
    config: Dict


def get_generator_config():
    """Get generator configuration from environment variables"""
    generator_type = os.getenv("RAG_GENERATOR_TYPE", "ollama").lower()
    model_name = os.getenv("RAG_MODEL_NAME", DEFAULT_OLLAMA_MODEL)
    device = os.getenv("RAG_DEVICE", "auto")
    cache_dir = os.getenv("RAG_CACHE_DIR", None)
    api_key = os.getenv("RAG_API_KEY")
    api_base = os.getenv("RAG_API_BASE")
    temperature = float(os.getenv("RAG_TEMPERATURE", 0.7))
    top_p = float(os.getenv("RAG_TOP_P", 0.9))
    max_tokens = int(os.getenv("RAG_MAX_TOKENS", 512))

    # Validate generator type
    valid_types = ["ollama", "openai", "spikingbrain", "mock"]
    if generator_type not in valid_types:
        print(f"Warning: Invalid generator type '{generator_type}', using 'ollama'")
        generator_type = "ollama"

    return {
        "generator_type": generator_type,
        "model_name": model_name,
        "device": device,
        "cache_dir": cache_dir,
        "api_key": api_key,
        "api_base": api_base,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
    }


# Initialize components on startup
@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global rag_pipeline

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Get generator configuration
    config = get_generator_config()
    generator_type = config["generator_type"]
    model_name = config["model_name"]
    device = config["device"]

    print(f"Initializing RAG pipeline with generator: {generator_type}")
    print(f"Model: {model_name}")
    print(f"Device: {device}")

    # Initialize RAG pipeline
    rag_pipeline = RAGPipeline(
        index_dir=INDEX_DIR,
        generator_type=generator_type,
        model_name=model_name,
        retrieval_k=5,
        device=device,
        cache_dir=config["cache_dir"],
        api_key=config["api_key"],
        api_base=config["api_base"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        max_tokens=config["max_tokens"],
    )

    print("✓ EideticRAG API initialized")


# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "EideticRAG API",
        "version": "0.1.0",
        "status": "running"
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query endpoint - returns answer with retrieved chunks and provenance
    """
    try:
        if not rag_pipeline:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")

        # Process query
        if request.generator is not None:
            rag_pipeline.update_generator(
                generator_type=request.generator.type or rag_pipeline.generator_type,
                model_name=request.generator.model or rag_pipeline.generator.model_name,
                api_key=request.generator.api_key,
                api_base=request.generator.api_base,
                temperature=request.generator.temperature,
                top_p=request.generator.top_p,
                max_tokens=request.generator.max_tokens,
            )

        result = rag_pipeline.query(
            query=request.query,
            k=request.k,
            filters=request.filters
        )

        return QueryResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """Get information about the current model"""
    try:
        if not rag_pipeline:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")

        info = rag_pipeline.get_model_info()

        return ModelInfoResponse(
            model_name=info.get('model_name', 'unknown'),
            model_type=info.get('model_type', 'unknown'),
            generator_type=rag_pipeline.generator_type,
            device=info.get('device', 'unknown'),
            config=info.get('config', {})
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    """
    Ingest a document into the index
    """
    # Create a dedicated, cross-platform temp directory
    temp_dir = INDEX_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / file.filename

    try:
        # Save the uploaded file to the temp directory
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if not rag_pipeline:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")

        # Process document using the global RAG pipeline
        doc, count = rag_pipeline.ingest_document(temp_path)

        return IngestResponse(
            doc_id=doc.doc_id,
            filename=doc.filename,
            num_chunks=count,
            message=f"Successfully ingested {doc.filename} with {count} chunks"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


@app.get("/stats")
async def get_stats():
    """Get index statistics"""
    try:
        if not rag_pipeline:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
        stats = rag_pipeline.index.get_stats()

        return {
            "status": "success",
            "stats": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/index/clear")
async def clear_index():
    """Clear the entire index"""
    try:
        if not rag_pipeline:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
        rag_pipeline.index.clear_index()

        return {
            "status": "success",
            "message": "Index cleared successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
