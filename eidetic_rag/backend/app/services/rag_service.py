"""
RAG Service - Main service layer for RAG operations
"""

from typing import Dict, List, Optional
from pathlib import Path

from eidetic_rag.backend.config.settings import Settings
from eidetic_rag.backend.app.core.embedding_service import EmbeddingService
from eidetic_rag.backend.app.core.vector_service import VectorService
from eidetic_rag.backend.app.core.generation_service import GenerationService
from eidetic_rag.backend.app.services.web_search_service import (
    WebSearchService
)


class RAGService:
    """Main RAG service orchestrating all components"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedding_service: Optional[EmbeddingService] = None
        self.vector_service: Optional[VectorService] = None
        self.generation_service: Optional[GenerationService] = None
        self.web_search_service: Optional[WebSearchService] = None

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
        self.web_search_service = WebSearchService()

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
        filters: Optional[Dict] = None,
        web_search_enabled: bool = False,
        include_wikipedia: bool = False,
        search_strategy: str = "hybrid"
    ) -> Dict:
        """Process a query through the RAG pipeline with optional web search.

        Args:
            query_text: The query to process
            k: Number of chunks to retrieve
            filters: Optional metadata filters
            web_search_enabled: Enable web search integration
            include_wikipedia: Include Wikipedia results in web search
            search_strategy: Strategy for combining results
                ("local_only", "web_only", "hybrid")
        """
        k = k or self.settings.DEFAULT_RETRIEVAL_K

        local_chunks = []
        web_results = []
        sources = []

        # Retrieve local chunks unless strategy is web_only
        if search_strategy != "web_only":
            query_embedding = await self.embedding_service.embed_text(
                query_text
            )
            local_chunks = await self.vector_service.search(
                query_embedding=query_embedding,
                k=k,
                filters=filters
            )

        # Perform web search if enabled and not local_only
        if web_search_enabled and search_strategy != "local_only":
            web_results = await self.web_search_service.search(
                query=query_text,
                max_results=5,
                include_wikipedia=include_wikipedia
            )

        # Combine contexts based on strategy
        if search_strategy == "hybrid":
            local_context = self._format_context(local_chunks)
            web_context = self._format_web_results(web_results)
            context = (
                f"Local Knowledge:\n{local_context}\n\n"
                f"Web Results:\n{web_context}"
            )
            sources = self._format_chunks(local_chunks) + web_results
        elif search_strategy == "web_only":
            context = self._format_web_results(web_results)
            sources = web_results
        else:  # local_only
            context = self._format_context(local_chunks)
            sources = self._format_chunks(local_chunks)

        # Generate answer
        prompt = f"Query: {query_text}\n\nContext: {context}"
        generation_result = await self.generation_service.generate(
            prompt=prompt,
            max_tokens=500,
            temperature=self.settings.DEFAULT_TEMPERATURE
        )

        # Handle the result properly
        if isinstance(generation_result, str):
            answer = generation_result
        else:
            answer = str(generation_result)

        return {
            'query': query_text,
            'answer': answer,
            'chunks': sources,
            'provenance': self._extract_provenance(local_chunks),
            'metadata': {
                'model': self.settings.DEFAULT_MODEL_TYPE,
                'num_chunks_retrieved': len(local_chunks),
                'num_web_results': len(web_results),
                'num_chunks_cited': len(local_chunks),
                'retrieval_k': k,
                'web_search_enabled': web_search_enabled,
                'wikipedia_enabled': include_wikipedia,
                'search_strategy': search_strategy
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
        return formatted

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

    def _format_web_results(self, web_results: List[Dict]) -> str:
        """Format web search results as context for generation"""
        if not web_results:
            return "No web results available."
        context_parts = []
        for i, result in enumerate(web_results, start=1):
            title = result.get('title', 'No title')
            content = result.get('content', 'No content')
            url = result.get('url', '')
            context_parts.append(
                f"[Web Result {i}] {title}\n{content}\nSource: {url}"
            )
        return "\n\n".join(context_parts)

    async def get_model_info(self) -> Dict:
        """Get information about the current model"""
        return {
            'model_name': self.settings.DEFAULT_MODEL_NAME,
            'model_type': self.settings.DEFAULT_MODEL_TYPE,
            'generator_type': self.settings.DEFAULT_MODEL_TYPE,
            'device': 'cpu',
            'config': {
                'temperature': self.settings.DEFAULT_TEMPERATURE,
                'max_tokens': 512,
                'top_p': 0.9
            }
        }
