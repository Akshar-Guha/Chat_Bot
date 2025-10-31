"""
Cache Manager - Handles caching for various components
"""

from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import hashlib
import json
import pickle
import time
from datetime import datetime, timedelta
from diskcache import Cache
import numpy as np


class CacheManager:
    """Manages multi-level caching for EideticRAG"""
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl_seconds: int = 3600,
        max_size: int = 1000000000  # 1GB default
    ):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory for cache storage
            ttl_seconds: Default time-to-live in seconds
            max_size: Maximum cache size in bytes
        """
        if cache_dir is None:
            cache_dir = Path("./cache")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.ttl_seconds = ttl_seconds
        
        # Initialize different cache levels
        self.embedding_cache = Cache(
            str(self.cache_dir / "embeddings"),
            size_limit=max_size // 3
        )
        
        self.retrieval_cache = Cache(
            str(self.cache_dir / "retrieval"),
            size_limit=max_size // 3
        )
        
        self.query_cache = Cache(
            str(self.cache_dir / "queries"),
            size_limit=max_size // 3
        )
        
        # Track cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'embeddings_cached': 0,
            'retrievals_cached': 0,
            'queries_cached': 0
        }
    
    def cache_embedding(
        self,
        text: str,
        embedding: np.ndarray,
        model: str = "default"
    ) -> str:
        """
        Cache an embedding
        
        Args:
            text: Original text
            embedding: Embedding vector
            model: Model used for embedding
        
        Returns:
            Cache key
        """
        key = self._generate_key(f"{model}:{text}")
        
        # Convert numpy array to list for serialization
        embedding_data = {
            'embedding': embedding.tolist() if isinstance(embedding, np.ndarray) else embedding,
            'model': model,
            'timestamp': time.time()
        }
        
        self.embedding_cache.set(key, embedding_data, expire=self.ttl_seconds)
        self.stats['embeddings_cached'] += 1
        
        return key
    
    def get_embedding(
        self,
        text: str,
        model: str = "default"
    ) -> Optional[np.ndarray]:
        """
        Get cached embedding
        
        Args:
            text: Original text
            model: Model used for embedding
        
        Returns:
            Embedding vector or None if not cached
        """
        key = self._generate_key(f"{model}:{text}")
        
        data = self.embedding_cache.get(key)
        
        if data:
            self.stats['hits'] += 1
            # Convert back to numpy array
            embedding = np.array(data['embedding'])
            return embedding
        else:
            self.stats['misses'] += 1
            return None
    
    def cache_retrieval(
        self,
        query: str,
        chunks: List[Dict],
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Cache retrieval results
        
        Args:
            query: Query text
            chunks: Retrieved chunks
            metadata: Additional metadata
        
        Returns:
            Cache key
        """
        key = self._generate_key(f"retrieval:{query}")
        
        retrieval_data = {
            'query': query,
            'chunks': chunks,
            'metadata': metadata or {},
            'timestamp': time.time()
        }
        
        self.retrieval_cache.set(key, retrieval_data, expire=self.ttl_seconds)
        self.stats['retrievals_cached'] += 1
        
        return key
    
    def get_retrieval(
        self,
        query: str
    ) -> Optional[Tuple[List[Dict], Dict]]:
        """
        Get cached retrieval results
        
        Args:
            query: Query text
        
        Returns:
            Tuple of (chunks, metadata) or None
        """
        key = self._generate_key(f"retrieval:{query}")
        
        data = self.retrieval_cache.get(key)
        
        if data:
            self.stats['hits'] += 1
            return data['chunks'], data.get('metadata', {})
        else:
            self.stats['misses'] += 1
            return None
    
    def cache_query_result(
        self,
        query: str,
        result: Dict,
        ttl: Optional[int] = None
    ) -> str:
        """
        Cache complete query result
        
        Args:
            query: Query text
            result: Complete result dictionary
            ttl: Custom TTL in seconds
        
        Returns:
            Cache key
        """
        key = self._generate_key(f"query:{query}")
        
        query_data = {
            'query': query,
            'result': result,
            'timestamp': time.time()
        }
        
        expire = ttl if ttl is not None else self.ttl_seconds
        self.query_cache.set(key, query_data, expire=expire)
        self.stats['queries_cached'] += 1
        
        return key
    
    def get_query_result(
        self,
        query: str
    ) -> Optional[Dict]:
        """
        Get cached query result
        
        Args:
            query: Query text
        
        Returns:
            Result dictionary or None
        """
        key = self._generate_key(f"query:{query}")
        
        data = self.query_cache.get(key)
        
        if data:
            self.stats['hits'] += 1
            return data['result']
        else:
            self.stats['misses'] += 1
            return None
    
    def invalidate_query(self, query: str):
        """
        Invalidate cached query result
        
        Args:
            query: Query text
        """
        key = self._generate_key(f"query:{query}")
        self.query_cache.delete(key)
        
        # Also invalidate related retrieval
        retrieval_key = self._generate_key(f"retrieval:{query}")
        self.retrieval_cache.delete(retrieval_key)
    
    def clear_cache(self, cache_type: Optional[str] = None):
        """
        Clear cache
        
        Args:
            cache_type: Type of cache to clear (embedding, retrieval, query, or None for all)
        """
        if cache_type == "embedding" or cache_type is None:
            self.embedding_cache.clear()
            
        if cache_type == "retrieval" or cache_type is None:
            self.retrieval_cache.clear()
            
        if cache_type == "query" or cache_type is None:
            self.query_cache.clear()
        
        if cache_type is None:
            # Reset stats
            self.stats = {
                'hits': 0,
                'misses': 0,
                'embeddings_cached': 0,
                'retrievals_cached': 0,
                'queries_cached': 0
            }
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': hit_rate,
            'embeddings_cached': self.stats['embeddings_cached'],
            'retrievals_cached': self.stats['retrievals_cached'],
            'queries_cached': self.stats['queries_cached'],
            'embedding_cache_size': len(self.embedding_cache),
            'retrieval_cache_size': len(self.retrieval_cache),
            'query_cache_size': len(self.query_cache)
        }
    
    def cleanup_old_entries(self, max_age_hours: int = 24):
        """
        Clean up old cache entries
        
        Args:
            max_age_hours: Maximum age in hours
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        # Clean each cache
        for cache in [self.embedding_cache, self.retrieval_cache, self.query_cache]:
            keys_to_delete = []
            
            for key in cache:
                try:
                    data = cache.get(key)
                    if data and data.get('timestamp', 0) < cutoff_time:
                        keys_to_delete.append(key)
                except:
                    continue
            
            for key in keys_to_delete:
                cache.delete(key)
        
        return len(keys_to_delete)
    
    def _generate_key(self, content: str) -> str:
        """Generate cache key from content"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def close(self):
        """Close cache connections"""
        self.embedding_cache.close()
        self.retrieval_cache.close()
        self.query_cache.close()
