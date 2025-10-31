"""
Vector Index - Manages vector storage and retrieval using ChromaDB
"""

from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
import numpy as np
from pathlib import Path
import shutil
import sqlite3


class VectorIndex:
    """Manages vector index for similarity search"""

    def __init__(
        self,
        collection_name: str = "eidetic_rag",
        persist_dir: Optional[Path] = None
    ):
        """
        Initialize vector index
        
        Args:
            collection_name: Name for the collection
            persist_dir: Directory to persist index
        """
        self.collection_name = collection_name

        self.persist_dir = Path(persist_dir) if persist_dir else None
        self._settings = Settings(anonymized_telemetry=False)

        # Setup ChromaDB client
        if self.persist_dir:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=self._settings
            )
        else:
            self.client = chromadb.Client(self._settings)

        self._initialize_collection()

    def _initialize_collection(self) -> None:
        """Initialise collection and recover from schema mismatches."""

        for attempt in range(2):
            try:
                self.collection = self.client.get_collection(
                    self.collection_name
                )
                self.doc_count = self.collection.count()
                print(
                    "Loaded existing collection with "
                    f"{self.doc_count} documents"
                )
                return
            except Exception as exc:
                if self._should_reset_schema(exc, attempt):
                    continue

            try:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                self.doc_count = 0
                print(f"Created new collection: {self.collection_name}")
                return
            except Exception as exc:
                if self._should_reset_schema(exc, attempt):
                    continue
                raise

        raise RuntimeError("Failed to initialise Chroma collection")

    def _should_reset_schema(self, exc: Exception, attempt: int) -> bool:
        """Reset persistent store if schema mismatch detected on first attempt."""
        if not self.persist_dir:
            return False
        if attempt > 0:
            return False
        if not self._is_schema_mismatch(exc):
            return False

        print(
            "Detected outdated Chroma index schema. Resetting persistent "
            "store."
        )
        self._reset_persistent_store()
        return True

    def _reset_persistent_store(self) -> None:
        """Reset persistent Chroma storage to recover from schema mismatches."""
        if not self.persist_dir:
            return

        shutil.rmtree(self.persist_dir, ignore_errors=True)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=self._settings
        )

    @staticmethod
    def _is_schema_mismatch(exc: Exception) -> bool:
        """Check if the exception stems from an outdated Chroma schema."""
        message = str(exc).lower()
        if isinstance(exc, sqlite3.OperationalError):
            return "no such column" in message and "collections" in message

        return "no such column" in message and "collections" in message
    
    def add_embeddings(
        self,
        embedded_chunks: List,
        batch_size: int = 100
    ) -> int:
        """
        Add embedded chunks to index
        
        Args:
            embedded_chunks: List of EmbeddedChunk objects
            batch_size: Batch size for insertion
        
        Returns:
            Number of chunks added
        """
        if not embedded_chunks:
            return 0
        
        added_count = 0
        
        # Process in batches
        for i in range(0, len(embedded_chunks), batch_size):
            batch = embedded_chunks[i:i + batch_size]
            
            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in batch]
            embeddings = [chunk.embedding.tolist() for chunk in batch]
            documents = [chunk.text for chunk in batch]
            
            # Prepare metadata
            metadatas = []
            for chunk in batch:
                metadata = {
                    'doc_id': chunk.doc_id,
                    'chunk_id': chunk.chunk_id,
                    'start_char': str(chunk.metadata.get('start_char', 0)),
                    'end_char': str(chunk.metadata.get('end_char', 0)),
                    'chunk_index': str(chunk.metadata.get('chunk_index', 0)),
                    'word_count': str(chunk.metadata.get('word_count', 0))
                }
                metadatas.append(metadata)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            added_count += len(batch)
        
        self.doc_count += added_count
        print(f"Added {added_count} chunks to index")
        
        return added_count
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar chunks
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_dict: Optional metadata filters
        
        Returns:
            List of search results with scores
        """
        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(k, self.doc_count),
            where=filter_dict if filter_dict else None,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                result = {
                    'chunk_id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'score': 1.0 - results['distances'][0][i],  # Convert distance to similarity
                    'metadata': results['metadatas'][0][i]
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        """
        Retrieve a specific chunk by ID
        
        Args:
            chunk_id: Chunk identifier
        
        Returns:
            Chunk data or None if not found
        """
        try:
            result = self.collection.get(
                ids=[chunk_id],
                include=['documents', 'metadatas', 'embeddings']
            )
            
            if result['ids']:
                return {
                    'chunk_id': result['ids'][0],
                    'text': result['documents'][0],
                    'metadata': result['metadatas'][0],
                    'embedding': result['embeddings'][0] if result['embeddings'] else None
                }
        except:
            pass
        
        return None
    
    def get_chunks_by_doc_id(self, doc_id: str) -> List[Dict]:
        """
        Retrieve all chunks for a document
        
        Args:
            doc_id: Document identifier
        
        Returns:
            List of chunks
        """
        results = self.collection.get(
            where={"doc_id": doc_id},
            include=['documents', 'metadatas']
        )
        
        chunks = []
        if results['ids']:
            for i in range(len(results['ids'])):
                chunk = {
                    'chunk_id': results['ids'][i],
                    'text': results['documents'][i],
                    'metadata': results['metadatas'][i]
                }
                chunks.append(chunk)
        
        # Sort by chunk index
        chunks.sort(key=lambda x: int(x['metadata'].get('chunk_index', 0)))
        
        return chunks
    
    def delete_document(self, doc_id: str) -> int:
        """
        Delete all chunks for a document
        
        Args:
            doc_id: Document identifier
        
        Returns:
            Number of chunks deleted
        """
        # Get chunks for document
        chunks = self.get_chunks_by_doc_id(doc_id)
        
        if chunks:
            chunk_ids = [chunk['chunk_id'] for chunk in chunks]
            self.collection.delete(ids=chunk_ids)
            self.doc_count -= len(chunk_ids)
            return len(chunk_ids)
        
        return 0
    
    def clear_index(self):
        """Clear all data from the index"""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.doc_count = 0
        print(f"Cleared index: {self.collection_name}")
    
    def get_stats(self) -> Dict:
        """Get index statistics"""
        return {
            'collection_name': self.collection_name,
            'total_chunks': self.doc_count,
            'embedding_space': 'cosine'
        }
    
    def persist(self):
        """Persist index to disk (for ChromaDB persistent client)"""
        # ChromaDB automatically persists with PersistentClient
        pass
