"""RAG Pipeline - Combines retrieval and generation."""

from pathlib import Path
from typing import Dict, List, Optional

from core.embeddings import EmbeddingGenerator
from core.vector_index import VectorIndex
from core.ingestor import DocumentIngestor
from core.chunker import TextChunker

try:
    from generation.spiking_brain_generator import SpikingBrainGenerator
except ModuleNotFoundError:
    SpikingBrainGenerator = None

from generation.generator import LLMGenerator


class RAGPipeline:
    """End-to-end RAG pipeline with multiple generator support"""

    def __init__(
        self,
        index_dir: Path,
        # Supported generator types:
        # "ollama", "huggingface", "spikingbrain", "mock"
        generator_type: str = "ollama",
        model_name: str = "deepseek-coder:6.7b-instruct-q4_K_M",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        retrieval_k: int = 5,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 512,
        device: str = "auto",
        cache_dir: Optional[str] = None
    ):
        """
        Initialize RAG pipeline

        Args:
            index_dir: Directory containing the vector index
            generator_type: Type of LLM to use ("ollama", "openai",
                           "spikingbrain", "mock")
            model_name: Specific model name
            api_key: API key for cloud models
            retrieval_k: Number of chunks to retrieve
            temperature: Generation temperature
            device: Device for SpikingBrain models
            cache_dir: Cache directory for models
        """
        self.index_dir = Path(index_dir)
        self.generator_type = self._normalize_generator_type(generator_type)
        self.retrieval_k = retrieval_k
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.cache_dir = cache_dir
        self.device = device

        # Initialize components
        self.embedder = EmbeddingGenerator(
            cache_dir=self.index_dir / 'embeddings_cache'
        )
        self.index = VectorIndex(persist_dir=self.index_dir)
        self.ingestor = DocumentIngestor()
        self.chunker = TextChunker()

        # Initialize generator based on type
        self.generator = self._create_generator(
            generator_type=self.generator_type,
            model_name=model_name,
            api_key=api_key,
            api_base=api_base,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            device=device,
            cache_dir=cache_dir
        )

    @staticmethod
    def _normalize_generator_type(generator_type: str) -> str:
        mapping = {
            "hf": "huggingface",
            "huggingface_endpoint": "huggingface",
        }
        return mapping.get(generator_type.lower(), generator_type.lower())

    def _create_generator(
        self,
        generator_type: str,
        model_name: str,
        api_key: Optional[str],
        api_base: Optional[str],
        temperature: float,
        top_p: float,
        max_tokens: int,
        device: str,
        cache_dir: Optional[str]
    ):
        """Create the appropriate generator based on type"""
        if generator_type == "spikingbrain":
            if SpikingBrainGenerator is None:
                raise RuntimeError(
                    "SpikingBrain generator requires optional dependencies"
                )

            return SpikingBrainGenerator(
                model_type="huggingface",  # Use HuggingFace interface
                model_name=model_name,
                device=device,
                temperature=temperature,
                cache_dir=cache_dir
            )
        else:
            # Use existing LLM generator for other types
            return LLMGenerator(
                model_type=generator_type,
                model_name=model_name,
                api_key=api_key,
                api_base=api_base,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens
            )

    def update_generator(
        self,
        generator_type: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        cache_dir: Optional[str] = None,
        device: Optional[str] = None,
    ) -> None:
        """Update generator configuration at runtime."""

        if generator_type:
            self.generator_type = self._normalize_generator_type(
                generator_type
            )
        if model_name:
            self.model_name = model_name
        if api_key is not None:
            self.api_key = api_key
        if api_base is not None:
            self.api_base = api_base
        if temperature is not None:
            self.temperature = temperature
        if top_p is not None:
            self.top_p = top_p
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if cache_dir is not None:
            self.cache_dir = cache_dir
        if device is not None:
            self.device = device

        self.generator = self._create_generator(
            generator_type=self.generator_type,
            model_name=self.model_name,
            api_key=self.api_key,
            api_base=self.api_base,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            device=self.device,
            cache_dir=self.cache_dir
        )

    def query(
        self,
        query: str,
        k: Optional[int] = None,
        filters: Optional[Dict] = None
    ) -> Dict:
        """
        Process a query through the RAG pipeline

        Args:
            query: User query
            k: Number of chunks to retrieve (overrides default)
            filters: Optional metadata filters for retrieval

        Returns:
            Dictionary with answer, chunks, and metadata
        """
        k = k or self.retrieval_k

        # Step 1: Generate query embedding
        query_embedding = self.embedder.embed_text(query)

        # Step 2: Retrieve relevant chunks
        retrieved_chunks = self.index.search(
            query_embedding=query_embedding,
            k=k,
            filter_dict=filters
        )

        # Step 3: Generate answer
        if self.generator_type == "spikingbrain":
            generation_result = self.generator.generate(
                query=query,
                retrieved_chunks=retrieved_chunks
            )
        else:
            # Use existing interface for other generators
            generation_result = self.generator.generate(
                query=query,
                retrieved_chunks=retrieved_chunks
            )

        # Step 4: Format response
        response = {
            'query': query,
            'answer': generation_result.answer,
            'chunks': self._format_chunks(retrieved_chunks),
            'provenance': generation_result.provenance,
            'metadata': {
                'model': generation_result.model,
                'generator_type': self.generator_type,
                'num_chunks_retrieved': len(retrieved_chunks),
                'num_chunks_cited': len(generation_result.provenance),
                **generation_result.metadata
            }
        }

        # Add SpikingBrain-specific information if available
        if hasattr(generation_result, 'spike_info'):
            response['spike_info'] = generation_result.spike_info

        return response

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

    def get_model_info(self) -> Dict:
        """Get information about the current generator"""
        if self.generator_type == "spikingbrain":
            return self.generator.get_model_info()
        else:
            return {
                'model_name': self.generator.model_name,
                'model_type': self.generator.model_type,
                'generator_type': self.generator_type
            }

    def ingest_document(self, file_path: Path):
        """Ingest a document into the RAG pipeline."""
        doc = self.ingestor.ingest(file_path)
        chunks = self.chunker.chunk_document(doc.doc_id, doc.content, doc.metadata)
        embedded_chunks = self.embedder.embed_chunks(chunks)
        count = self.index.add_embeddings(embedded_chunks)
        return doc, count
