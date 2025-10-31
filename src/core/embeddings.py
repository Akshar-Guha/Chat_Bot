"""
Embedding Generator - Creates vector embeddings for text chunks
"""

from typing import Dict, List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from dataclasses import dataclass
import pickle
from pathlib import Path


@dataclass
class EmbeddedChunk:
    """Chunk with embedding vector"""
    chunk_id: str
    doc_id: str
    text: str
    embedding: np.ndarray
    metadata: dict


class EmbeddingGenerator:
    """Generates embeddings using sentence transformers"""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: Optional[Path] = None,
        device: Optional[str] = None
    ):
        """
        Initialize embedding generator
        
        Args:
            model_name: Name of the sentence transformer model
            cache_dir: Directory to cache embeddings
            device: Device to run model on ('cuda', 'cpu', or None for auto)
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        
        # Set device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        # Load model
        self.model = SentenceTransformer(model_name)
        self.model.to(self.device)
        
        # Model info
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Setup cache if specified
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file = cache_dir / f"{model_name.replace('/', '_')}_cache.pkl"
            self._load_cache()
        else:
            self.cache_file = None
            self.cache = {}
    
    def embed_text(
        self,
        text: Union[str, List[str]],
        batch_size: int = 32
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate embeddings for text
        
        Args:
            text: Single text or list of texts to embed
            batch_size: Batch size for encoding
        
        Returns:
            Embedding vector(s)
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        embeddings = []
        
        for text_item in texts:
            # Check cache first
            if text_item in self.cache:
                embeddings.append(self.cache[text_item])
            else:
                # Generate embedding
                embedding = self.model.encode(
                    text_item,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    device=self.device
                )
                
                # Cache the embedding
                self.cache[text_item] = embedding
                embeddings.append(embedding)
        
        # Save cache periodically
        if self.cache_file and len(self.cache) % 100 == 0:
            self._save_cache()
        
        return embeddings[0] if is_single else embeddings
   
    def embed_chunks(
        self,
        chunks: List,
        batch_size: int = 32
    ) -> List[EmbeddedChunk]:
        """
        Generate embeddings for chunks
        
        Args:
            chunks: List of Chunk objects
            batch_size: Batch size for encoding
        
        Returns:
            List of EmbeddedChunk objects
        """
        embedded_chunks = []
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.text for chunk in batch]
            
            # Generate embeddings for batch
            embeddings = self.embed_text(texts, batch_size=batch_size)
            
            # Create embedded chunks
            for chunk, embedding in zip(batch, embeddings):
                embedded_chunk = EmbeddedChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    text=chunk.text,
                    embedding=embedding,
                    metadata={
                        **chunk.metadata,
                        'embedding_model': self.model_name,
                        'embedding_dim': self.embedding_dim,
                        'start_char': chunk.start_char,
                        'end_char': chunk.end_char,
                        'chunk_index': chunk.chunk_index
                    }
                )
                embedded_chunks.append(embedded_chunk)
        
        # Save cache after processing all chunks
        if self.cache_file:
            self._save_cache()
        
        return embedded_chunks
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Cosine similarity score
        """
        # Normalize vectors
        norm1 = embedding1 / np.linalg.norm(embedding1)
        norm2 = embedding2 / np.linalg.norm(embedding2)
        
        # Compute cosine similarity
        similarity = np.dot(norm1, norm2)
        
        return float(similarity)
    
    def _load_cache(self):
        """Load embedding cache from disk"""
        if self.cache_file and self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
                print(f"Loaded {len(self.cache)} cached embeddings")
            except Exception as e:
                print(f"Failed to load cache: {e}")
                self.cache = {}
        else:
            self.cache = {}
    
    def _save_cache(self):
        """Save embedding cache to disk"""
        if self.cache_file:
            try:
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(self.cache, f)
            except Exception as e:
                print(f"Failed to save cache: {e}")
    
    def clear_cache(self):
        """Clear the embedding cache"""
        self.cache = {}
        if self.cache_file and self.cache_file.exists():
            self.cache_file.unlink()
