"""
Query endpoints for RAG operations
"""

from fastapi import APIRouter, Depends, HTTPException

from eidetic_rag.backend.app.services.rag_service import RAGService
from eidetic_rag.backend.app.core.dependencies import get_rag_service
from eidetic_rag.backend.app.models.schemas import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Process a query through the RAG pipeline

    Returns answer with retrieved chunks and provenance information.
    Supports web search integration with configurable strategies.
    """
    try:
        result = await rag_service.query(
            query_text=request.query,
            k=request.k,
            filters=request.filters,
            web_search_enabled=request.use_web_search,
            include_wikipedia=request.use_wikipedia,
            search_strategy=request.search_strategy
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def query_stream(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Stream query results (future enhancement)
    """
    # TODO: Implement streaming response
    raise HTTPException(
        status_code=501,
        detail="Streaming not yet implemented"
    )


@router.get("/model/info")
async def get_model_info(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Get information about the current model
    """
    try:
        # Get model info from RAG service
        model_info = await rag_service.get_model_info()

        return {
            "model_name": model_info.get('model_name', 'unknown'),
            "model_type": model_info.get('model_type', 'unknown'),
            "generator_type": model_info.get('generator_type', 'unknown'),
            "device": model_info.get('device', 'unknown'),
            "config": model_info.get('config', {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
