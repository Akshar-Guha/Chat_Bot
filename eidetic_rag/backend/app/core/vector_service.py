"""
Vector service for managing vector operations
"""

from typing import List
from pathlib import Path
import sys
import asyncio

# Add parent to path to import core modules
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from core.vector_index import VectorIndex
except ImportError:
    VectorIndex = None


class VectorService:
    """Service for vector index operations"""

    def __init__(self, persist_dir: Path):
        self.persist_dir = persist_dir
        self.index: VectorIndex = None

    async def initialize(self) -> None:
        """Initialize the vector service"""
        if VectorIndex:
            self.index = VectorIndex(persist_dir=self.persist_dir)
        else:
            print("Warning: VectorIndex not available")

    async def search(self, query_embedding: List[float], k: int = 5, filters=None) -> List:
        """Search for similar vectors"""
        if not self.index:
            raise RuntimeError("Vector service not initialized")
        return await asyncio.get_event_loop().run_in_executor(
            None, self._search_sync, query_embedding, k, filters
        )

    def _search_sync(self, query_embedding: List[float], k: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Synchronous search implementation"""
        try:
            # Use the VectorIndex search method
            results = self.index.search(query_embedding, k, filters)

            # Format results to match expected structure
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'chunk_id': result.get('id', result.get('chunk_id')),
                    'text': result.get('text', result.get('content', '')),
                    'score': result.get('score', 0.0),
                    'metadata': result.get('metadata', {})
                })

            return formatted_results

        except Exception as e:
            print(f"Search error: {e}")
            # Return empty results on error
            return []

    async def add_embeddings(self, embeddings: List[Dict[str, Any]]) -> int:
        """Add embeddings to the index"""
        if not self.index:
            raise RuntimeError("Vector service not initialized")
        return await asyncio.get_event_loop().run_in_executor(
            None, self.index.add_embeddings, embeddings
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        if not self.index:
            return {"total_documents": 0, "total_chunks": 0, "index_size": "0MB"}
        return self.index.get_stats()

    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.index = None
