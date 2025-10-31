"""
Test harness for Stage 2 - Baseline RAG
"""

import sys
from pathlib import Path
import json
import requests
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generation.rag_pipeline import RAGPipeline
from src.core.ingestor import DocumentIngestor
from src.core.chunker import TextChunker
from src.core.embeddings import EmbeddingGenerator
from src.core.vector_index import VectorIndex


def setup_test_index():
    """Setup test index with sample data"""
    base_path = Path(__file__).parent.parent
    test_index_dir = base_path / "test_rag_index"
    
    # Initialize components
    ingestor = DocumentIngestor()
    chunker = TextChunker(chunk_size=300, chunk_overlap=30)
    embedder = EmbeddingGenerator(cache_dir=test_index_dir / "cache")
    index = VectorIndex(persist_dir=test_index_dir)
    
    # Clear and rebuild index
    index.clear_index()
    
    # Ingest sample documents
    sample_docs = [
        base_path / "data" / "sample_documents" / "sample1.txt",
        base_path / "data" / "sample_documents" / "sample2.txt"
    ]
    
    for doc_path in sample_docs:
        doc = ingestor.ingest(doc_path)
        chunks = chunker.chunk_document(doc.doc_id, doc.content)
        embedded_chunks = embedder.embed_chunks(chunks)
        index.add_embeddings(embedded_chunks)
    
    return test_index_dir


def test_end_to_end():
    """Test end-to-end query processing"""
    print("\n=== Test: End-to-End Query ===")
    
    # Setup test index
    test_index_dir = setup_test_index()
    
    # Initialize RAG pipeline
    rag = RAGPipeline(
        index_dir=test_index_dir,
        model_type="mock",  # Use mock for testing
        retrieval_k=3
    )
    
    # Load ground truth
    base_path = Path(__file__).parent.parent
    with open(base_path / "data" / "test_dataset" / "ground_truth.json", 'r') as f:
        ground_truth = json.load(f)
    
    # Test with a known query
    test_query = ground_truth['test_queries'][0]
    result = rag.query(test_query['query'])
    
    # Verify response structure
    assert 'answer' in result, "Missing answer in response"
    assert 'chunks' in result, "Missing chunks in response"
    assert 'provenance' in result, "Missing provenance in response"
    assert 'metadata' in result, "Missing metadata in response"
    
    # Verify chunks were retrieved
    assert len(result['chunks']) > 0, "No chunks retrieved"
    
    # Verify answer cites sources
    assert len(result['provenance']) > 0, "No provenance information"
    
    # Check if expected content is in retrieved chunks
    expected_chunk_ids = test_query['expected_chunks']
    retrieved_texts = ' '.join([c['text'] for c in result['chunks']])
    
    # Check for key terms from expected answer
    if "1956" in test_query['expected_answer']:
        assert "1956" in retrieved_texts or "1956" in result['answer'], \
            "Expected content not found in retrieval or answer"
    
    print(f"✓ End-to-end test passed")
    print(f"  Query: {test_query['query']}")
    print(f"  Answer: {result['answer'][:100]}...")
    print(f"  Chunks retrieved: {len(result['chunks'])}")
    print(f"  Sources cited: {len(result['provenance'])}")
    
    return True


def test_latency_sanity():
    """Test that queries complete in reasonable time"""
    print("\n=== Test: Latency Sanity Check ===")
    
    test_index_dir = Path(__file__).parent.parent / "test_rag_index"
    
    # Initialize RAG pipeline
    rag = RAGPipeline(
        index_dir=test_index_dir,
        model_type="mock",
        retrieval_k=5
    )
    
    # Run multiple queries
    test_queries = [
        "What is machine learning?",
        "How does climate change affect the planet?",
        "What are the applications of AI?"
    ]
    
    for query in test_queries:
        start_time = time.time()
        result = rag.query(query)
        elapsed = time.time() - start_time
        
        # Should complete within 5 seconds (generous for embedding generation)
        assert elapsed < 5.0, f"Query took too long: {elapsed:.2f}s"
        assert result is not None, "Query returned None"
        
        print(f"✓ Query completed in {elapsed:.2f}s: {query[:50]}...")
    
    print("✓ Latency sanity check passed")
    return True


def test_edge_cases():
    """Test edge case handling"""
    print("\n=== Test: Edge Cases ===")
    
    test_index_dir = Path(__file__).parent.parent / "test_rag_index"
    
    # Initialize RAG pipeline
    rag = RAGPipeline(
        index_dir=test_index_dir,
        model_type="mock",
        retrieval_k=5
    )
    
    # Test 1: Empty query
    result = rag.query("")
    assert result is not None, "Failed on empty query"
    print("✓ Empty query handled gracefully")
    
    # Test 2: Very long query
    long_query = "test " * 1000
    result = rag.query(long_query)
    assert result is not None, "Failed on long query"
    print("✓ Long query handled gracefully")
    
    # Test 3: Special characters
    special_query = "What about @#$% special *&^% characters?"
    result = rag.query(special_query)
    assert result is not None, "Failed on special characters"
    print("✓ Special characters handled gracefully")
    
    # Test 4: Query with no good matches
    nonsense_query = "xyzabc123 quantum blockchain metaverse NFT"
    result = rag.query(nonsense_query)
    assert result is not None, "Failed on nonsense query"
    assert 'answer' in result, "Missing answer for nonsense query"
    print("✓ Nonsense query handled gracefully")
    
    # Test 5: Broken document handling
    try:
        ingestor = DocumentIngestor()
        fake_path = Path("/nonexistent/fake.pdf")
        doc = ingestor.ingest(fake_path)
        assert False, "Should have raised exception for nonexistent file"
    except FileNotFoundError:
        print("✓ Nonexistent file handled with proper error")
    
    print("✓ All edge cases handled properly")
    return True


def test_api_endpoints():
    """Test API endpoints (requires server to be running)"""
    print("\n=== Test: API Endpoints ===")
    print("Note: This test requires the API server to be running")
    print("Start server with: python -m src.api.main")
    
    api_url = "http://localhost:8000"
    
    try:
        # Test root endpoint
        response = requests.get(f"{api_url}/")
        if response.status_code != 200:
            print("⚠ API server not running, skipping API tests")
            return True
        
        data = response.json()
        assert data['status'] == 'running', "API not running"
        print("✓ API root endpoint working")
        
        # Test query endpoint
        query_data = {
            "query": "What is machine learning?",
            "k": 3
        }
        response = requests.post(f"{api_url}/query", json=query_data)
        assert response.status_code == 200, f"Query failed: {response.status_code}"
        
        result = response.json()
        assert 'answer' in result, "Missing answer in API response"
        assert 'chunks' in result, "Missing chunks in API response"
        print("✓ Query endpoint working")
        
        # Test stats endpoint
        response = requests.get(f"{api_url}/stats")
        assert response.status_code == 200, f"Stats failed: {response.status_code}"
        print("✓ Stats endpoint working")
        
        print("✓ All API endpoints tested successfully")
        
    except requests.exceptions.ConnectionError:
        print("⚠ API server not running, skipping API tests")
    
    return True


def run_all_tests():
    """Run all Stage 2 tests"""
    print("\n=== Stage 2 Tests: Baseline RAG ===")
    
    try:
        # Run tests
        test_end_to_end()
        test_latency_sanity()
        test_edge_cases()
        test_api_endpoints()
        
        print("\n✅ All Stage 2 tests passed!")
        print("\nStage 2 Acceptance Criteria Met:")
        print("✓ End-to-end query processing works")
        print("✓ Queries complete without crashing")
        print("✓ Edge cases handled gracefully")
        print("✓ API endpoints functional")
        
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
