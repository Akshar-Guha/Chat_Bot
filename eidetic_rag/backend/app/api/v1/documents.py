"""
Documents API endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path
import sys

# Add parent to path to import core modules
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from core.ingestor import DocumentIngestor
    from core.chunker import TextChunker
    from core.embeddings import EmbeddingGenerator
    from core.vector_index import VectorIndex
except ImportError:
    # Fallback for when modules don't exist yet
    DocumentIngestor = None
    TextChunker = None
    EmbeddingGenerator = None
    VectorIndex = None

router = APIRouter()

INDEX_DIR = Path("./index")


@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    Ingest a document into the index
    """
    core_modules = [DocumentIngestor, TextChunker, EmbeddingGenerator, VectorIndex]
    if not all(core_modules):
        raise HTTPException(
            status_code=500,
            detail=(
                "Core modules not available. "
                "Please ensure all dependencies are installed."
            )
        )

    try:
        # Save uploaded file temporarily
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Initialize components
        ingestor = DocumentIngestor()
        chunker = TextChunker()
        embedder = EmbeddingGenerator(cache_dir=INDEX_DIR / 'embeddings_cache')
        index = VectorIndex(persist_dir=INDEX_DIR)

        # Process document
        doc = ingestor.ingest(temp_path)
        chunks = chunker.chunk_document(doc.doc_id, doc.content, doc.metadata)
        embedded_chunks = embedder.embed_chunks(chunks)
        count = index.add_embeddings(embedded_chunks)

        # Clean up temp file
        temp_path.unlink()

        return {
            "doc_id": doc.doc_id,
            "filename": doc.filename,
            "num_chunks": count,
            "message": f"Successfully ingested {doc.filename} ({count} chunks)"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_document_stats():
    """Get document index statistics"""
    if not VectorIndex:
        raise HTTPException(
            status_code=500,
            detail="Vector index module not available"
        )

    try:
        index = VectorIndex(persist_dir=INDEX_DIR)
        stats = index.get_stats()

        return {
            "status": "success",
            "stats": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_documents():
    """Clear all documents from the index"""
    if not VectorIndex:
        raise HTTPException(
            status_code=500,
            detail="Vector index module not available"
        )

    try:
        index = VectorIndex(persist_dir=INDEX_DIR)
        index.clear_index()

        return {
            "status": "success",
            "message": "All documents cleared successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))