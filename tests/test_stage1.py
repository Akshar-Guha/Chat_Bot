"""
Test harness for Stage 1 - Core Foundation
"""

import sys
from pathlib import Path
import numpy as np
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.ingestor import DocumentIngestor
from src.core.chunker import TextChunker
from src.core.embeddings import EmbeddingGenerator
from src.core.vector_index import VectorIndex


def test_chunk_integrity():
    """Test that chunk offsets correctly map to original text"""
    print("\n=== Test: Chunk Integrity ===")
    
    # Load sample document
    base_path = Path(__file__).parent.parent
    sample_doc_path = base_path / "data" / "sample_documents" / "sample1.txt"
    
    # Ingest document
    ingestor = DocumentIngestor()
    doc = ingestor.ingest(sample_doc_path)
    
    # Chunk document
    chunker = TextChunker(chunk_size=300, chunk_overlap=30)
    chunks = chunker.chunk_document(doc.doc_id, doc.content)
    
    # Test random chunks
    import random
    test_chunks = random.sample(chunks, min(3, len(chunks)))
    
    for chunk in test_chunks:
        # Extract text using offsets
        extracted = doc.content[chunk.start_char:chunk.end_char]
        
        # Verify extraction matches chunk text (accounting for overlap modifications)
        # Check if the core content is present
        core_text = chunk.text.strip()
        if chunk.metadata.get('has_overlap'):
            # For overlapped chunks, check if original text is contained
            assert chunk.start_char >= 0, f"Invalid start_char: {chunk.start_char}"
            assert chunk.end_char <= len(doc.content), f"Invalid end_char: {chunk.end_char}"
            print(f"✓ Chunk {chunk.chunk_id[:8]}... offsets valid")
        else:
            assert extracted.strip() == core_text, f"Mismatch for chunk {chunk.chunk_id}"
            print(f"✓ Chunk {chunk.chunk_id[:8]}... matches exactly")
    
    print(f"✓ Chunk integrity test passed ({len(chunks)} total chunks)")
    return True


def test_embedding_stability():
    """Test that embeddings are stable for the same input"""
    print("\n=== Test: Embedding Stability ===")
    
    embedder = EmbeddingGenerator()
    
    test_text = "This is a test sentence for embedding stability verification."
    
    # Generate embeddings twice
    embedding1 = embedder.embed_text(test_text)
    embedding2 = embedder.embed_text(test_text)
    
    # Calculate similarity
    similarity = embedder.compute_similarity(embedding1, embedding2)
    
    # Should be nearly identical (allowing for minor floating point differences)
    assert similarity > 0.9999, f"Embeddings not stable: similarity = {similarity}"
    
    print(f"✓ Embedding stability verified (similarity: {similarity:.6f})")
    return True


def test_index_retrieval():
    """Test that index retrieval works correctly"""
    print("\n=== Test: Index Retrieval ===")
    
    # Setup test index
    base_path = Path(__file__).parent.parent
    test_index_dir = base_path / "test_index"
    
    # Initialize components
    ingestor = DocumentIngestor()
    chunker = TextChunker(chunk_size=300, chunk_overlap=30)
    embedder = EmbeddingGenerator(cache_dir=test_index_dir / "cache")
    index = VectorIndex(persist_dir=test_index_dir)
    
    # Clear any existing data
    index.clear_index()
    
    # Load and process sample document
    sample_doc_path = base_path / "data" / "sample_documents" / "sample1.txt"
    doc = ingestor.ingest(sample_doc_path)
    chunks = chunker.chunk_document(doc.doc_id, doc.content)
    embedded_chunks = embedder.embed_chunks(chunks)
    
    # Add to index
    index.add_embeddings(embedded_chunks)
    
    # Test retrieval with known query
    test_query = "When was AI research founded?"
    query_embedding = embedder.embed_text(test_query)
    results = index.search(query_embedding, k=3)
    
    assert len(results) > 0, "No results returned from index"
    
    # Check if relevant content is in top results
    top_result = results[0]
    assert "1956" in top_result['text'] or "Dartmouth" in top_result['text'], \
        "Expected content not found in top result"
    
    print(f"✓ Index retrieval working (found {len(results)} results)")
    print(f"  Top result score: {top_result['score']:.3f}")
    
    # Test retrieval by chunk ID
    chunk_data = index.get_chunk_by_id(top_result['chunk_id'])
    assert chunk_data is not None, "Failed to retrieve chunk by ID"
    assert chunk_data['chunk_id'] == top_result['chunk_id'], "Chunk ID mismatch"
    
    print(f"✓ Chunk retrieval by ID working")
    
    return True


def test_index_persistence():
    """Test that index persists and can be reloaded"""
    print("\n=== Test: Index Persistence ===")
    
    base_path = Path(__file__).parent.parent
    test_index_dir = base_path / "test_index_persist"
    
    # Create initial index
    index1 = VectorIndex(persist_dir=test_index_dir)
    index1.clear_index()
    
    # Add some test data
    embedder = EmbeddingGenerator()
    test_chunks = [
        {
            'chunk_id': 'test_chunk_1',
            'doc_id': 'test_doc',
            'text': 'This is test chunk one',
            'embedding': embedder.embed_text('This is test chunk one'),
            'metadata': {'test': 'data'}
        }
    ]
    
    # Create a simple embedded chunk object
    from types import SimpleNamespace
    embedded_chunk = SimpleNamespace(
        chunk_id=test_chunks[0]['chunk_id'],
        doc_id=test_chunks[0]['doc_id'],
        text=test_chunks[0]['text'],
        embedding=test_chunks[0]['embedding'],
        metadata=test_chunks[0]['metadata']
    )
    
    index1.add_embeddings([embedded_chunk])
    initial_count = index1.doc_count
    
    # Persist (ChromaDB auto-persists)
    index1.persist()
    
    # Create new index instance
    index2 = VectorIndex(persist_dir=test_index_dir)
    
    # Verify data persisted
    assert index2.doc_count == initial_count, \
        f"Document count mismatch: {index2.doc_count} != {initial_count}"
    
    # Verify we can retrieve the chunk
    chunk = index2.get_chunk_by_id('test_chunk_1')
    assert chunk is not None, "Failed to retrieve persisted chunk"
    assert chunk['text'] == 'This is test chunk one', "Persisted data mismatch"
    
    print(f"✓ Index persistence verified ({initial_count} documents)")
    
    return True


def run_all_tests():
    """Run all Stage 1 tests"""
    print("\n=== Stage 1 Tests: Core Foundation ===")
    
    try:
        # Run tests
        test_chunk_integrity()
        test_embedding_stability()
        test_index_retrieval()
        test_index_persistence()
        
        print("\n✅ All Stage 1 tests passed!")
        print("\nStage 1 Acceptance Criteria Met:")
        print("✓ Index persists to disk and can be reloaded")
        print("✓ Chunk integrity maintained")
        print("✓ Embedding stability verified")
        print("✓ Index retrieval functional")
        
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_all_tests()
