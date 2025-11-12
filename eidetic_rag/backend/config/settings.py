"""
Application settings and configuration
"""

from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Project info
    PROJECT_NAME: str = "EideticRAG API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Advanced Retrieval-Augmented Generation system"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False  # Disable reload for stability

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"

    # RAG settings
    DEFAULT_RETRIEVAL_K: int = 5
    DEFAULT_TEMPERATURE: float = 0.7
    INDEX_DIR: str = "./index"
    EMBEDDINGS_CACHE_DIR: str = "./index/embeddings_cache"

    # Model settings
    DEFAULT_MODEL_TYPE: str = "mock"
    DEFAULT_MODEL_NAME: str = "gpt-3.5-turbo"
    OPENAI_API_KEY: Optional[str] = None
    
    # Optional RAG-specific settings (from .env)
    RAG_GENERATOR_TYPE: Optional[str] = None
    RAG_MODEL_NAME: Optional[str] = None
    RAG_DEVICE: Optional[str] = None
    RAG_TEMPERATURE: Optional[float] = None
    RAG_TOP_P: Optional[float] = None
    RAG_MAX_TOKENS: Optional[int] = None

    # Database settings
    DATABASE_URL: str = "sqlite:///./memory.db"

    # Redis settings (for caching)
    REDIS_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
