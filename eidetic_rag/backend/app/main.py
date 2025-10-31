"""
EideticRAG Backend Application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from eidetic_rag.backend.config.settings import get_settings
from eidetic_rag.backend.app.core.dependencies import get_rag_service

from eidetic_rag.backend.app.api.v1.health import router as health_router
from eidetic_rag.backend.app.api.v1.documents import router as documents_router
from eidetic_rag.backend.app.api.v1.queries import router as queries_router
from eidetic_rag.backend.app.api.v1.memory import router as memory_router
logger = logging.getLogger(__name__)
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    settings = get_settings()

    # Log startup information
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")

    yield

    # Shutdown
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(
        health_router,
        prefix="/api/v1/health",
        tags=["health"]
    )
    app.include_router(
        queries_router,
        prefix="/api/v1/queries",
        tags=["queries"]
    )
    app.include_router(
        documents_router,
        prefix="/api/v1/documents",
        tags=["documents"]
    )
    app.include_router(
        memory_router,
        prefix="/api/v1/memory",
        tags=["memory"]
    )

    return app


def main() -> None:
    """Main entry point"""
    settings = get_settings()
    app = create_app()

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
