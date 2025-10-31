"""
Health check endpoints
"""

from datetime import datetime
from fastapi import APIRouter, Depends

from eidetic_rag.backend.app.services.rag_service import RAGService
from eidetic_rag.backend.app.core.dependencies import get_rag_service

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "EideticRAG API"
    }


@router.get("/detailed")
async def detailed_health_check(
    rag_service: RAGService = Depends(get_rag_service)
):
    """Detailed health check with service status"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "EideticRAG API",
        "services": {
            "rag_service": "ready" if rag_service else "not_initialized"
        }
    }
