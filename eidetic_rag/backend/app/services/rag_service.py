"""
RAG Service - Main service layer for RAG operations
"""

from typing import Dict, List, Optional
from pathlib import Path

from eidetic_rag.backend.config.settings import Settings
from eidetic_rag.backend.app.core.embedding_service import EmbeddingService
from eidetic_rag.backend.app.core.vector_service import VectorService
from eidetic_rag.backend.app.core.generation_service import GenerationService


class RAGService:
    """Main RAG service orchestrating all components"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedding_service: Optional[EmbeddingService] = None
        self.vector_service: Optional[VectorService] = None
        self.generation_service: Optional[GenerationService] = None

    async def initialize(self) -> None:
        """Initialize all services"""
        self.embedding_service = EmbeddingService(
            cache_dir=Path(self.settings.EMBEDDINGS_CACHE_DIR)
        )
        self.vector_service = VectorService(
            persist_dir=Path(self.settings.INDEX_DIR)
        )
        self.generation_service = GenerationService(
            model_type=self.settings.DEFAULT_MODEL_TYPE,
            model_name=self.settings.DEFAULT_MODEL_NAME,
            api_key=self.settings.OPENAI_API_KEY,
            temperature=self.settings.DEFAULT_TEMPERATURE,
        )

        # Initialize components
        await self.embedding_service.initialize()
        await self.vector_service.initialize()

    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.vector_service:
            await self.vector_service.cleanup()
        if self.generation_service:
            await self.generation_service.cleanup()

    async def query(
        self,
        query_text: str,
        k: Optional[int] = None,
        filters: Optional[Dict] = None
    ) -> Dict:
        """Process a query through the RAG pipeline"""
        k = k or self.settings.DEFAULT_RETRIEVAL_K

        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query_text)

        # Retrieve relevant chunks
        retrieved_chunks = await self.vector_service.search(
            query_embedding=query_embedding,
            k=k,
            filters=filters
        )

        # Generate answer using the correct method signature
        generation_result = await self.generation_service.generate(
            prompt=f"Query: {query_text}\n\nContext: {self._format_context(retrieved_chunks)}",
            max_tokens=500,
            temperature=self.settings.DEFAULT_TEMPERATURE
        )

        # Handle the result properly
        answer = generation_result if isinstance(generation_result, str) else str(generation_result)

        return {
            'query': query_text,
            'answer': answer,
            'chunks': self._format_chunks(retrieved_chunks),
            'provenance': self._extract_provenance(retrieved_chunks),
            'metadata': {
                'model': self.settings.DEFAULT_MODEL_TYPE,
                'num_chunks_retrieved': len(retrieved_chunks),
                'num_chunks_cited': len(retrieved_chunks),
                'retrieval_k': k
            }
        }

    def _format_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Format chunks for response"""
        formatted = []
        for chunk in chunks:
            formatted.append({
                'chunk_id': chunk.get('chunk_id'),
                'text': chunk.get('text'),
                'score': chunk.get('score'),
                'metadata': {
                    'doc_id': chunk.get('metadata', {}).get('doc_id'),
                    'start_char': chunk.get('metadata', {}).get('start_char'),
                    'end_char': chunk.get('metadata', {}).get('end_char'),
                    'chunk_index': chunk.get('metadata', {}).get('chunk_index')
                }
            })
    def _format_context(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks as context for generation"""
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(f"[Chunk {i+1}] {chunk.get('text', '')}")
        return "\n\n".join(context_parts)

    def _extract_provenance(self, chunks: List[Dict]) -> List[Dict]:
        """Extract provenance information from chunks"""
        provenance = []
        for chunk in chunks:
            provenance.append({
                'chunk_id': chunk.get('chunk_id'),
                'text': chunk.get('text', '')[:200] + "...",
                'metadata': chunk.get('metadata', {}),
                'score': chunk.get('score')
            })
        return provenance
