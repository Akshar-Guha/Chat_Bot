"""
Dependency injection and service management
"""

from typing import AsyncGenerator

from eidetic_rag.backend.config.settings import get_settings
from eidetic_rag.backend.app.services.rag_service import RAGService


async def get_rag_service() -> AsyncGenerator[RAGService, None]:
    """Dependency to get RAG service instance"""
    settings = get_settings()
    service = RAGService(settings)
    try:
        await service.initialize()
        yield service
    finally:
        await service.cleanup()
