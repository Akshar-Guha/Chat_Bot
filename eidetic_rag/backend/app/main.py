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
import logging

# Add src directory to path
SRC_DIR = Path(__file__).resolve().parent.parent.parent.parent / "src"
sys.path.append(str(SRC_DIR))

# Load environment variables from .env file
load_dotenv()

from src.core.ingestor import DocumentIngestor
from src.core.chunker import TextChunker
from src.core.embeddings import EmbeddingGenerator
from src.core.vector_index import VectorIndex
from src.orchestration.orchestrator import EideticRAGOrchestrator

# Import web search service
try:
    from eidetic_rag.backend.app.services.web_search_service import WebSearchService
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    WebSearchService = None

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
CACHE_DIR = Path("./cache")
LOG_DIR = Path("./logs")
MEMORY_DB = Path("./memory.db")
DEFAULT_OLLAMA_MODEL = "llama3.2:1b"
orchestrator = None
web_search_service = None


logger = logging.getLogger(__name__)


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
    use_cache: Optional[bool] = True
    use_memory: Optional[bool] = True
    use_reflection: Optional[bool] = True
    use_web_search: Optional[bool] = False
    search_strategy: Optional[str] = "hybrid"  # "local_only", "web_only", or "hybrid"
    use_wikipedia: Optional[bool] = False


class QueryResponse(BaseModel):
    query: str
    answer: str
    chunks: List[Dict]
    provenance: List[Dict]
    metadata: Dict
    spike_info: Optional[Dict] = None  # SpikingBrain-specific information
    verification: Optional[Dict] = None  # Reflection verification results
    intent: Optional[str] = None  # Query intent classification


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


def format_web_results(web_results: List[Dict]) -> str:
    """Format web search results as readable, clean text for LLM consumption"""
    if not web_results:
        return "No web results available."
    
    context_parts = []
    for i, result in enumerate(web_results, start=1):
        title = result.get('title', 'Untitled')
        content = result.get('content', '')
        url = result.get('url', '')
        source = result.get('source', 'web').upper()
        
        # Clean and format content
        if content:
            # Ensure content is readable
            content = content.strip()
            if len(content) > 800:
                content = content[:800] + "..."
        else:
            content = "No content available."
        
        context_parts.append(
            f"[{source} Result {i}]\n"
            f"Title: {title}\n"
            f"Content: {content}\n"
            f"URL: {url}"
        )
    
    return "\n\n".join(context_parts)


# Initialize components on startup
@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global orchestrator, web_search_service

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Get generator configuration
    config = get_generator_config()
    generator_type = config["generator_type"]
    model_name = config["model_name"]
    device = config["device"]

    print(f"Initializing EideticRAG Orchestrator with generator: {generator_type}")
    print(f"Model: {model_name}")
    print(f"Device: {device}")

    # Build orchestrator config
    orch_config = {
        'model_type': generator_type,
        'model_name': model_name,
        'api_key': config.get('api_key'),
        'temperature': config['temperature'],
        'chunk_size': 500,
        'chunk_overlap': 50,
        'default_k': 5,
        'max_reflection_iterations': 3,
        'hallucination_threshold': 0.3,
        'memory_db_path': str(MEMORY_DB)
    }

    # Initialize orchestrator with full features
    orchestrator = EideticRAGOrchestrator(
        config=orch_config,
        index_dir=INDEX_DIR,
        cache_dir=CACHE_DIR,
        log_dir=LOG_DIR
    )

    # Initialize web search service if available
    if WEB_SEARCH_AVAILABLE and WebSearchService:
        web_search_service = WebSearchService()
        print("✓ Web Search service initialized")
    else:
        print("⚠ Web Search service not available")

    print("✓ EideticRAG API initialized with Memory, Reflection, and Caching")


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
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")

        # Update generator if provided
        if request.generator is not None:
            # Temporarily update config (Note: In production, consider creating a new orchestrator)
            if request.generator.type:
                orchestrator.config['model_type'] = request.generator.type
            if request.generator.model:
                orchestrator.config['model_name'] = request.generator.model
            if request.generator.api_key:
                orchestrator.config['api_key'] = request.generator.api_key
            if request.generator.temperature is not None:
                orchestrator.config['temperature'] = request.generator.temperature
            
            # Reinitialize generator with new config
            orchestrator._init_components()

        # Perform web search BEFORE generating answer if enabled
        web_results = []
        search_strategy = "local_only"
        
        if request.use_web_search and web_search_service:
            search_strategy = request.search_strategy or "hybrid"
            
            # Perform web search if not local_only
            if search_strategy != "local_only":
                web_results = await web_search_service.search(
                    query=request.query,
                    max_results=5,
                    include_wikipedia=request.use_wikipedia
                )
                logging.getLogger(__name__).info(
                    "Web search found %s results", len(web_results)
                )
        
        # Process query with orchestrator (supports memory, reflection, caching)
        # For web_only or hybrid, inject web context into the query
        enhanced_query = request.query
        
        if web_results:
            web_context = format_web_results(web_results)
            if search_strategy == "web_only":
                # Only use web context
                enhanced_query = (
                    f"Based on the following web search results, answer the question: {request.query}\n\n"
                    f"Web Search Results:\n{web_context}"
                )
            elif search_strategy == "hybrid":
                # Add web context as additional information
                enhanced_query = (
                    f"{request.query}\n\n"
                    f"Additional context from web search:\n{web_context}"
                )
        
        result = await orchestrator.process_query_async(
            query=enhanced_query,
            use_cache=request.use_cache if request.use_cache is not None else True,
            use_memory=request.use_memory if request.use_memory is not None else True,
            use_reflection=request.use_reflection if request.use_reflection is not None else True
        )
        
        # Add metadata about web search
        result['metadata']['web_search_enabled'] = bool(request.use_web_search and web_search_service)
        result['metadata']['num_web_results'] = len(web_results)
        result['metadata']['wikipedia_enabled'] = bool(request.use_wikipedia)
        result['metadata']['search_strategy'] = search_strategy
        
        # Include web results in chunks for reference
        if web_results:
            result['chunks'] = result.get('chunks', []) + web_results

        return QueryResponse(**result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/web/status")
async def web_status(q: Optional[str] = None):
    """Check web search connectivity and return a sample result"""
    try:
        if not (WEB_SEARCH_AVAILABLE and web_search_service):
            return {
                "connected": False,
                "available": False,
                "result_count": 0,
                "sample": None
            }

        query_text = q or "latest news"
        results = await web_search_service.search(query=query_text, max_results=3)
        return {
            "connected": True,
            "available": True,
            "result_count": len(results),
            "sample": results[0] if results else None
        }
    except Exception as e:
        return {
            "connected": False,
            "available": True,
            "error": str(e)
        }

@app.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """Get information about the current model"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")

        return ModelInfoResponse(
            model_name=orchestrator.generator.model_name,
            model_type=orchestrator.generator.model_type,
            generator_type=orchestrator.config.get('model_type', 'unknown'),
            device='cpu',
            config={}
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

        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")

        # Process document using the orchestrator
        result = await orchestrator.ingest_document_async(temp_path)

        return IngestResponse(
            doc_id=result['doc_id'],
            filename=result['filename'],
            num_chunks=result['num_chunks'],
            message=f"Successfully ingested {result['filename']} with {result['num_chunks']} chunks"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


@app.get("/stats")
async def get_stats():
    """Get comprehensive system statistics"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        full_stats = orchestrator.get_stats()
        
        # Extract stats from orchestrator
        index_stats = full_stats.get('index', {})
        cache_stats = full_stats.get('cache', {})
        memory_stats = full_stats.get('memory', {})
        
        # Basic stats for backward compatibility
        stats = {
            'total_chunks': index_stats.get('total_chunks', 0),
            'total_documents': index_stats.get('total_documents', 0),
            'collection_name': index_stats.get('collection_name', 'eidetic_rag'),
            'embedding_space': index_stats.get('embedding_space', 'cosine'),
            'cache_hits': cache_stats.get('hits', 0),
            'cache_misses': cache_stats.get('misses', 0),
            'cache_hit_rate': cache_stats.get('hit_rate', 0.0),
            'total_memories': memory_stats.get('total_memories', 0)
        }
        
        # Enhanced stats for dashboard (preserving the full structure)
        enhanced_stats = {
            'index': {
                'total_chunks': index_stats.get('total_chunks', 0),
                'total_documents': index_stats.get('total_documents', 0),
                'collection_name': index_stats.get('collection_name', 'eidetic_rag')
            },
            'cache': {
                'hits': cache_stats.get('hits', 0),
                'misses': cache_stats.get('misses', 0),
                'hit_rate': cache_stats.get('hit_rate', 0.0),
                'queries_cached': cache_stats.get('queries_cached', 0)
            },
            'memory': {
                'total_memories': memory_stats.get('total_memories', 0)
            },
            'performance': {
                'avg_query_time_ms': 250,  # Default value
                'queries_today': 0,
                'queries_this_week': 0
            }
        }

        return {
            "status": "success",
            "stats": stats,  # Legacy flat format
            "detailed_stats": enhanced_stats  # New structured format
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/index/clear")
async def clear_index():
    """Clear the entire index"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        orchestrator.index.clear_index()

        return {
            "status": "success",
            "message": "Index cleared successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def get_documents():
    """Get all documents from the index"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        
        # Get documents from the index
        documents = orchestrator.index.get_all_documents()
        
        return {
            "status": "success",
            "documents": documents
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the index"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        
        # Delete document from index
        orchestrator.index.delete_document(doc_id)
        
        return {
            "status": "success",
            "message": f"Document {doc_id} deleted successfully"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory")
async def get_memories(limit: int = 50):
    """Get all memories from the memory database"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        
        if not orchestrator.memory_manager:
            return {
                "status": "success",
                "memories": []
            }
        
        # Get memories from memory manager
        raw_memories = orchestrator.memory_manager.get_all_memories(limit=limit)
        
        # Transform memories to match frontend interface
        memories = []
        for mem in raw_memories:
            transformed_memory = {
                "id": mem.get("id", ""),
                "content": f"Q: {mem.get('query_text', '')}\nA: {mem.get('answer_text', '')}",
                "metadata": {
                    "query_text": mem.get("query_text", ""),
                    "answer_text": mem.get("answer_text", ""),
                    "importance_score": mem.get("importance_score", 0.5),
                    "intent": mem.get("intent"),
                    "intent_confidence": mem.get("intent_confidence"),
                    "model_used": mem.get("model_used"),
                    "user_feedback": mem.get("user_feedback"),
                    "access_count": mem.get("access_count", 0),
                    "is_edited": mem.get("is_edited", False),
                    "is_private": mem.get("is_private", False),
                },
                "tags": [],  # No tags in current model, can be added later
                "created_at": mem.get("timestamp", "")
            }
            memories.append(transformed_memory)
        
        return {
            "status": "success",
            "memories": memories
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/memory/{memory_id}")
async def update_memory_entry(memory_id: str, content: Optional[str] = None, 
                               importance_score: Optional[float] = None,
                               metadata: Optional[Dict] = None):
    """Update a memory entry"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        
        if not orchestrator.memory_manager:
            raise HTTPException(status_code=500, detail="Memory manager not available")
        
        # Update memory - map content to answer parameter
        orchestrator.memory_manager.update_memory(
            memory_id=memory_id,
            answer=content,  # Frontend sends 'content', backend expects 'answer'
            importance_score=importance_score
        )
        
        return {
            "status": "success",
            "message": f"Memory {memory_id} updated successfully"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/{memory_id}")
async def delete_memory_entry(memory_id: str):
    """Delete a memory entry"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        
        if not orchestrator.memory_manager:
            raise HTTPException(status_code=500, detail="Memory manager not available")
        
        # Delete memory
        orchestrator.memory_manager.delete_memory(memory_id)
        
        return {
            "status": "success",
            "message": f"Memory {memory_id} deleted successfully"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/export")
async def export_memories():
    """Export all memories as JSON"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        
        if not orchestrator.memory_manager:
            return {
                "status": "success",
                "memories": []
            }
        
        # Export memories
        memories = orchestrator.memory_manager.export_memories()
        
        from fastapi.responses import JSONResponse
        import json
        
        return JSONResponse(
            content={"memories": memories},
            headers={
                "Content-Disposition": f"attachment; filename=memories_export_{os.getpid()}.json"
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
