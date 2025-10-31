"""
Embedding service for the RAG system
"""

from typing import List, Any
from pathlib import Path
import sys
import asyncio

# Add parent to path to import core modules
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from core.embeddings import EmbeddingGenerator
except ImportError:
    EmbeddingGenerator = None


class EmbeddingService:
    """Service for generating and managing embeddings"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.generator: EmbeddingGenerator = None

    async def initialize(self) -> None:
        """Initialize the embedding service"""
        if EmbeddingGenerator:
            self.generator = EmbeddingGenerator(cache_dir=self.cache_dir)
        else:
            print("Warning: EmbeddingGenerator not available")

    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for text"""
        if not self.generator:
            raise RuntimeError("Embedding service not initialized")
        return await asyncio.get_event_loop().run_in_executor(
            None, self.generator.embed_text, text
        )

    async def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for multiple chunks"""
        if not self.generator:
            raise RuntimeError("Embedding service not initialized")
        return await asyncio.get_event_loop().run_in_executor(
            None, self.generator.embed_chunks, chunks
        )

    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.generator = None
