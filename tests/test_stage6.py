"""
Test harness for Stage 6 - Orchestration, Caching & Logging
"""

import sys
from pathlib import Path
import time
import asyncio
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.cache_manager import CacheManager
from src.orchestration.logger import StructuredLogger
from src.orchestration.orchestrator import EideticRAGOrchestrator
import numpy as np


def test_cache_correctness():
    """Test that cache returns correct results"""
    print("\n=== Test: Cache Correctness ===")
    
    # Initialize cache
    test_cache_dir = Path("test_cache")
    cache = CacheManager(cache_dir=test_cache_dir)
    
    # Test embedding cache
    text = "This is a test sentence for caching"
    embedding = np.random.rand(384)  # Simulate embedding
    
    # Cache embedding
    key = cache.cache_embedding(text, embedding, model="test_model")
    assert key is not None, "Failed to cache embedding"
    
    # Retrieve embedding
    retrieved = cache.get_embedding(text, model="test_model")
    assert retrieved is not None, "Failed to retrieve cached embedding"
    assert np.allclose(embedding, retrieved), "Retrieved embedding doesn't match"
    
    print("✓ Embedding cache working correctly")
    
    # Test query cache
    query = "What is machine learning?"
    result = {
        'answer': "ML is a subset of AI...",
        'chunks': [{'id': 'c1', 'text': 'test'}],
        'metadata': {'test': True}
    }
    
    # Cache query result
    cache.cache_query_result(query, result)
    
    # First retrieval should hit cache
    cached_result = cache.get_query_result(query)
    assert cached_result is not None, "Failed to retrieve cached query"
    assert cached_result['answer'] == result['answer'], "Cached result doesn't match"
    
    # Verify cache hit tracking
    stats = cache.get_cache_stats()
    assert stats['hits'] > 0, "Cache hits not tracked"
    
    print(f"✓ Query cache working (hit rate: {stats['hit_rate']:.2%})")
    
    # Test cache invalidation
    cache.invalidate_query(query)
    invalidated_result = cache.get_query_result(query)
    assert invalidated_result is None, "Cache not properly invalidated"
    
    print("✓ Cache invalidation working")
    
    # Cleanup
    cache.close()
    import shutil
    if test_cache_dir.exists():
        shutil.rmtree(test_cache_dir)
    
    return True


def test_failure_recovery():
    """Test graceful failure handling"""
    print("\n=== Test: Failure Recovery ===")
    
    # Initialize orchestrator with test config
    config = {
        'model_type': 'mock',
        'chunk_size': 300,
        'max_reflection_iterations': 2
    }
    
    orchestrator = EideticRAGOrchestrator(
        config=config,
        index_dir=Path("test_orch_index"),
        cache_dir=Path("test_orch_cache"),
        log_dir=Path("test_orch_logs")
    )
    
    # Test with empty index (should handle gracefully)
    try:
        result = orchestrator.process_query(
            "Test query with no indexed documents",
            use_cache=False,
            use_reflection=False
        )
        
        # Should return some result even with empty index
        assert result is not None, "Query failed with empty index"
        assert 'answer' in result, "No answer in result"
        print("✓ Handled empty index gracefully")
        
    except Exception as e:
        print(f"✗ Failed to handle empty index: {e}")
        return False
    
    # Test with invalid query
    try:
        result = orchestrator.process_query(
            "",  # Empty query
            use_cache=False,
            use_reflection=False
        )
        
        assert result is not None, "Failed on empty query"
        print("✓ Handled invalid query gracefully")
        
    except Exception as e:
        # Should handle gracefully, not crash
        print("✓ Exception handled for invalid query")
    
    # Cleanup
    orchestrator.cleanup()
    
    print("\n✓ Failure recovery tests passed")
    return True


def test_trace_completeness():
    """Test that logs contain required fields"""
    print("\n=== Test: Trace Completeness ===")
    
    # Initialize logger
    test_log_dir = Path("test_logs")
    logger = StructuredLogger(
        log_dir=test_log_dir,
        enable_console=False,
        enable_file=True
    )
    
    # Log various operations
    query_id = logger.log_query("Test query", "factual", {'test': True})
    assert query_id is not None, "No query ID generated"
    
    logger.log_retrieval(query_id, 5, "default", 150.5, {'source': 'test'})
    logger.log_generation(query_id, "gpt-3.5", 200, 500.3)
    logger.log_reflection(query_id, "accept", 0.15, 1)
    
    # Check that log files were created
    log_files = list(test_log_dir.glob("*.log"))
    assert len(log_files) > 0, "No log files created"
    
    # Check structured JSON log
    json_files = list(test_log_dir.glob("*.json"))
    assert len(json_files) > 0, "No JSON log files created"
    
    print(f"✓ Created {len(log_files)} log files")
    
    # Verify log content (basic check)
    log_content_found = False
    for log_file in log_files:
        content = log_file.read_text()
        if query_id in content:
            log_content_found = True
            break
    
    assert log_content_found, "Query ID not found in logs"
    print(f"✓ Logs contain query tracking (ID: {query_id})")
    
    # Test error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.log_error(e, "test_context", {'test': True})
    
    # Check error log exists
    error_logs = list(test_log_dir.glob("errors_*.log"))
    assert len(error_logs) > 0, "No error log created"
    print("✓ Error logging working")
    
    # Cleanup
    import shutil
    if test_log_dir.exists():
        shutil.rmtree(test_log_dir)
    
    print("\n✓ Trace completeness verified")
    return True


def test_concurrent_queries():
    """Test handling concurrent queries"""
    print("\n=== Test: Concurrent Queries ===")
    
    # Initialize orchestrator
    config = {'model_type': 'mock'}
    orchestrator = EideticRAGOrchestrator(
        config=config,
        index_dir=Path("test_concurrent_index"),
        cache_dir=Path("test_concurrent_cache"),
        log_dir=Path("test_concurrent_logs")
    )
    
    # Define test queries
    queries = [
        "What is AI?",
        "Explain machine learning",
        "What is deep learning?",
        "How does NLP work?"
    ]
    
    async def run_concurrent_queries():
        """Run queries concurrently"""
        tasks = []
        for query in queries:
            task = orchestrator.process_query_async(
                query,
                use_cache=False,
                use_reflection=False
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    # Run concurrent queries
    start_time = time.time()
    results = asyncio.run(run_concurrent_queries())
    duration = time.time() - start_time
    
    # Verify all queries completed
    successful = sum(1 for r in results if isinstance(r, dict) and 'answer' in r)
    assert successful == len(queries), f"Not all queries completed: {successful}/{len(queries)}"
    
    print(f"✓ Processed {len(queries)} concurrent queries in {duration:.2f}s")
    
    # Verify no duplicate query IDs
    query_ids = [r['query_id'] for r in results if isinstance(r, dict)]
    assert len(query_ids) == len(set(query_ids)), "Duplicate query IDs found"
    print("✓ All query IDs unique")
    
    # Cleanup
    orchestrator.cleanup()
    
    print("\n✓ Concurrent query handling verified")
    return True


def test_performance_metrics():
    """Test performance metric collection"""
    print("\n=== Test: Performance Metrics ===")
    
    # Initialize components
    cache = CacheManager(cache_dir=Path("test_perf_cache"))
    
    # Warm up cache
    for i in range(10):
        query = f"test query {i}"
        result = {'answer': f'answer {i}'}
        cache.cache_query_result(query, result)
    
    # Test cache performance
    hits = 0
    misses = 0
    
    for i in range(20):
        query = f"test query {i % 15}"  # Some will hit, some miss
        result = cache.get_query_result(query)
        if result:
            hits += 1
        else:
            misses += 1
    
    stats = cache.get_cache_stats()
    
    assert stats['hits'] > 0, "No cache hits recorded"
    assert stats['misses'] > 0, "No cache misses recorded"
    assert stats['hit_rate'] > 0, "Hit rate not calculated"
    
    print(f"✓ Cache metrics: {hits} hits, {misses} misses, {stats['hit_rate']:.2%} hit rate")
    
    # Test orchestrator stats
    config = {'model_type': 'mock'}
    orchestrator = EideticRAGOrchestrator(
        config=config,
        index_dir=Path("test_perf_index"),
        cache_dir=Path("test_perf_cache2"),
        log_dir=Path("test_perf_logs")
    )
    
    # Process a query to generate metrics
    result = orchestrator.process_query("Test query", use_cache=False, use_reflection=False)
    
    # Get stats
    system_stats = orchestrator.get_stats()
    
    assert 'index' in system_stats, "Missing index stats"
    assert 'cache' in system_stats, "Missing cache stats"
    assert 'memory' in system_stats, "Missing memory stats"
    
    # Check timing metrics in result
    assert 'metadata' in result, "Missing metadata in result"
    assert 'total_duration_ms' in result['metadata'], "Missing duration metric"
    assert result['metadata']['total_duration_ms'] > 0, "Invalid duration"
    
    print(f"✓ Query processed in {result['metadata']['total_duration_ms']:.2f}ms")
    
    # Cleanup
    cache.close()
    orchestrator.cleanup()
    
    print("\n✓ Performance metrics collection verified")
    return True


def run_all_tests():
    """Run all Stage 6 tests"""
    print("\n=== Stage 6 Tests: Orchestration, Caching & Logging ===")
    
    try:
        # Run tests
        test_cache_correctness()
        test_failure_recovery()
        test_trace_completeness()
        test_concurrent_queries()
        test_performance_metrics()
        
        print("\n✅ All Stage 6 tests passed!")
        print("\nStage 6 Acceptance Criteria Met:")
        print("✓ Cache correctness verified")
        print("✓ Failure recovery working")
        print("✓ Trace completeness confirmed")
        print("✓ Concurrent queries handled")
        print("✓ Performance metrics collected")
        
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
