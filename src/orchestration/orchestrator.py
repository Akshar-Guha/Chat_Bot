"""
Orchestrator - Coordinates all EideticRAG components
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..core.ingestor import DocumentIngestor
from ..core.chunker import TextChunker
from ..core.embeddings import EmbeddingGenerator
from ..core.vector_index import VectorIndex
from ..retrieval.retrieval_controller import RetrievalController
from ..generation.generator import LLMGenerator
from ..reflection.reflection_agent import ReflectionAgent
from ..memory.memory_manager import MemoryManager
from .cache_manager import CacheManager
from .logger import StructuredLogger


class EideticRAGOrchestrator:
    """Main orchestrator for EideticRAG pipeline"""
    
    def __init__(
        self,
        config: Optional[Dict] = None,
        index_dir: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
        log_dir: Optional[Path] = None
    ):
        """
        Initialize orchestrator
        
        Args:
            config: Configuration dictionary
            index_dir: Directory for vector index
            cache_dir: Directory for cache
            log_dir: Directory for logs
        """
        self.config = config or {}
        
        # Setup directories
        self.index_dir = Path(index_dir) if index_dir else Path("./index")
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./cache")
        self.log_dir = Path(log_dir) if log_dir else Path("./logs")
        
        # Initialize logger
        self.logger = StructuredLogger(log_dir=self.log_dir)
        
        # Initialize cache
        self.cache = CacheManager(cache_dir=self.cache_dir)
        
        # Initialize components
        self._init_components()
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def _init_components(self):
        """Initialize all components"""
        # Core components
        self.ingestor = DocumentIngestor()
        self.chunker = TextChunker(
            chunk_size=self.config.get('chunk_size', 500),
            chunk_overlap=self.config.get('chunk_overlap', 50)
        )
        self.embedder = EmbeddingGenerator(
            model_name=self.config.get('embedding_model', 'all-MiniLM-L6-v2'),
            cache_dir=self.index_dir / 'embeddings_cache'
        )
        self.index = VectorIndex(persist_dir=self.index_dir)
        
        # Retrieval
        self.retriever = RetrievalController(
            index_dir=self.index_dir,
            default_k=self.config.get('default_k', 5)
        )
        
        # Generation
        self.generator = LLMGenerator(
            model_type=self.config.get('model_type', 'mock'),
            model_name=self.config.get('model_name', 'gpt-3.5-turbo'),
            api_key=self.config.get('api_key'),
            temperature=self.config.get('temperature', 0.7)
        )
        
        # Reflection
        self.reflection_agent = ReflectionAgent(
            max_iterations=self.config.get('max_reflection_iterations', 3),
            hallucination_threshold=self.config.get('hallucination_threshold', 0.3)
        )
        
        # Memory
        self.memory_manager = MemoryManager(
            db_path=Path(self.config.get('memory_db_path', './memory.db'))
        )
    
    async def process_query_async(
        self,
        query: str,
        use_cache: bool = True,
        use_memory: bool = True,
        use_reflection: bool = True
    ) -> Dict:
        """
        Process query asynchronously
        
        Args:
            query: User query
            use_cache: Whether to use cache
            use_memory: Whether to use memory
            use_reflection: Whether to use reflection
        
        Returns:
            Query result dictionary
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self.process_query,
            query,
            use_cache,
            use_memory,
            use_reflection
        )
        return result
    
    def process_query(
        self,
        query: str,
        use_cache: bool = True,
        use_memory: bool = True,
        use_reflection: bool = True
    ) -> Dict:
        """
        Process query through full pipeline
        
        Args:
            query: User query
            use_cache: Whether to use cache
            use_memory: Whether to use memory
            use_reflection: Whether to use reflection
        
        Returns:
            Query result dictionary
        """
        start_time = time.time()
        
        # Log query
        query_id = self.logger.log_query(query, "unknown")
        
        try:
            # Check cache
            if use_cache:
                cached_result = self.cache.get_query_result(query)
                if cached_result:
                    self.logger.log_cache_hit("query", query, True)
                    cached_result['cached'] = True
                    cached_result['query_id'] = query_id
                    return cached_result
                else:
                    self.logger.log_cache_hit("query", query, False)
            
            # Step 1: Retrieval
            retrieval_start = time.time()
            retrieval_result = self._retrieve_with_memory(query, use_memory)
            retrieval_duration = (time.time() - retrieval_start) * 1000
            
            self.logger.log_retrieval(
                query_id,
                len(retrieval_result['chunks']),
                retrieval_result.get('policy', {}).get('strategy', 'default'),
                retrieval_duration
            )
            
            # Step 2: Generation
            generation_start = time.time()
            generation_result = self.generator.generate(
                query,
                retrieval_result['chunks']
            )
            generation_duration = (time.time() - generation_start) * 1000
            
            self.logger.log_generation(
                query_id,
                generation_result.model,
                generation_result.metadata.get('max_tokens', 0),
                generation_duration
            )
            
            # Step 3: Reflection (if enabled)
            if use_reflection:
                reflection_start = time.time()
                reflection_result = self.reflection_agent.reflect_on_answer(
                    generation_result.answer,
                    query,
                    retrieval_result['chunks'],
                    self.generator,
                    self.retriever
                )
                reflection_duration = (time.time() - reflection_start) * 1000
                
                self.logger.log_reflection(
                    query_id,
                    reflection_result.decision.action.value if reflection_result.decision else "none",
                    reflection_result.verification.hallucination_score,
                    reflection_result.iterations,
                    {'duration_ms': reflection_duration}
                )
                
                final_answer = reflection_result.final_answer
                verification = reflection_result.verification
            else:
                final_answer = generation_result.answer
                verification = None
            
            # Step 4: Memory storage
            if use_memory:
                memory_id = self.memory_manager.create_memory(
                    query=query,
                    answer=final_answer,
                    chunk_ids=[c['chunk_id'] for c in retrieval_result['chunks']],
                    chunk_scores=[c['score'] for c in retrieval_result['chunks']],
                    intent=retrieval_result.get('intent'),
                    intent_confidence=retrieval_result.get('intent_confidence'),
                    model_used=generation_result.model
                )
                
                self.logger.log_memory_operation("create", memory_id, True)
            
            # Build final result
            total_duration = (time.time() - start_time) * 1000
            
            result = {
                'query_id': query_id,
                'query': query,
                'answer': final_answer,
                'chunks': retrieval_result['chunks'],
                'provenance': generation_result.provenance,
                'intent': retrieval_result.get('intent'),
                'verification': {
                    'hallucination_score': verification.hallucination_score if verification else None,
                    'support_ratio': verification.overall_support_ratio if verification else None,
                    'unsupported_claims': len(verification.unsupported_claims) if verification else 0
                } if verification else None,
                'metadata': {
                    'model': generation_result.model,
                    'total_duration_ms': total_duration,
                    'retrieval_duration_ms': retrieval_duration,
                    'generation_duration_ms': generation_duration,
                    'reflection_enabled': use_reflection,
                    'memory_enabled': use_memory,
                    'cached': False
                }
            }
            
            # Cache result
            if use_cache:
                self.cache.cache_query_result(query, result)
            
            self.logger.log_performance("query_processing", total_duration, True)
            
            return result
            
        except Exception as e:
            self.logger.log_error(e, "query_processing", {'query': query})
            raise
    
    def _retrieve_with_memory(
        self,
        query: str,
        use_memory: bool
    ) -> Dict:
        """Retrieve with memory augmentation"""
        # Check cache first
        cached_retrieval = self.cache.get_retrieval(query)
        if cached_retrieval:
            chunks, metadata = cached_retrieval
            return {'chunks': chunks, **metadata}
        
        # Retrieve from index
        retrieval_result = self.retriever.retrieve(query)
        
        # Augment with memory if enabled
        if use_memory:
            memory_results = self.memory_manager.search_memories(query, k=3)
            
            if memory_results:
                # Add relevant memories as pseudo-chunks
                for memory, score in memory_results[:2]:
                    memory_chunk = {
                        'chunk_id': f"memory_{memory['id']}",
                        'text': f"Previous Q: {memory['query_text']}\nA: {memory['answer_text']}",
                        'score': score * 0.8,  # Slightly reduce memory scores
                        'metadata': {
                            'source': 'memory',
                            'memory_id': memory['id'],
                            'timestamp': memory.get('timestamp')
                        }
                    }
                    retrieval_result['chunks'].append(memory_chunk)
                
                # Re-sort by score
                retrieval_result['chunks'].sort(key=lambda x: x['score'], reverse=True)
        
        # Cache retrieval
        self.cache.cache_retrieval(query, retrieval_result['chunks'], retrieval_result)
        
        return retrieval_result
    
    async def ingest_document_async(
        self,
        file_path: Path
    ) -> Dict:
        """Ingest document asynchronously"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self.ingest_document,
            file_path
        )
        return result
    
    def ingest_document(
        self,
        file_path: Path
    ) -> Dict:
        """
        Ingest a document into the system
        
        Args:
            file_path: Path to document
        
        Returns:
            Ingestion result dictionary
        """
        start_time = time.time()
        
        try:
            # Ingest
            doc = self.ingestor.ingest(file_path)
            
            # Chunk
            chunks = self.chunker.chunk_document(doc.doc_id, doc.content, doc.metadata)
            
            # Embed
            embedded_chunks = self.embedder.embed_chunks(chunks)
            
            # Index
            num_indexed = self.index.add_embeddings(embedded_chunks)
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.log_performance(
                f"document_ingestion",
                duration,
                True,
                {'doc_id': doc.doc_id, 'num_chunks': num_indexed}
            )
            
            return {
                'doc_id': doc.doc_id,
                'filename': doc.filename,
                'num_chunks': num_indexed,
                'duration_ms': duration,
                'success': True
            }
            
        except Exception as e:
            self.logger.log_error(e, "document_ingestion", {'file': str(file_path)})
            raise
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        return {
            'index': self.index.get_stats(),
            'cache': self.cache.get_cache_stats(),
            'memory': {
                'total_memories': len(self.memory_manager.list_memories(limit=1000))
            }
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.cache.close()
        self.executor.shutdown(wait=True)
