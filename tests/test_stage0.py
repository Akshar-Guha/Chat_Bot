"""
Test harness for Stage 0 - Planning & Setup
"""

import json
import os
from pathlib import Path


def test_sample_documents_exist():
    """Test that sample documents are present"""
    base_path = Path(__file__).parent.parent
    sample_docs = [
        base_path / "data" / "sample_documents" / "sample1.txt",
        base_path / "data" / "sample_documents" / "sample2.txt"
    ]
    
    for doc_path in sample_docs:
        assert doc_path.exists(), f"Sample document missing: {doc_path}"
        # Verify we can read the content
        content = doc_path.read_text()
        assert len(content) > 0, f"Sample document is empty: {doc_path}"
    
    print("✓ Sample documents exist and are readable")


def test_ground_truth_loads():
    """Test that ground truth file loads correctly"""
    base_path = Path(__file__).parent.parent
    ground_truth_path = base_path / "data" / "test_dataset" / "ground_truth.json"
    
    assert ground_truth_path.exists(), "Ground truth file missing"
    
    with open(ground_truth_path, 'r') as f:
        data = json.load(f)
    
    assert 'test_queries' in data, "Missing test_queries in ground truth"
    assert 'chunk_mappings' in data, "Missing chunk_mappings in ground truth"
    assert len(data['test_queries']) > 0, "No test queries defined"
    assert len(data['chunk_mappings']) > 0, "No chunk mappings defined"
    
    print(f"✓ Ground truth loaded: {len(data['test_queries'])} queries, {len(data['chunk_mappings'])} chunks")


def test_locate_sentence_by_offset():
    """Test that we can locate sentences by character offset"""
    base_path = Path(__file__).parent.parent
    sample_doc_path = base_path / "data" / "sample_documents" / "sample1.txt"
    ground_truth_path = base_path / "data" / "test_dataset" / "ground_truth.json"
    
    # Load document content
    with open(sample_doc_path, 'r') as f:
        doc_content = f.read()
    
    # Load ground truth
    with open(ground_truth_path, 'r') as f:
        ground_truth = json.load(f)
    
    # Test a specific chunk mapping
    chunk_1_1 = ground_truth['chunk_mappings']['chunk_1_1']
    start = chunk_1_1['start_char']
    end = chunk_1_1['end_char']
    
    extracted_text = doc_content[start:end]
    
    # Verify the extracted text matches expectation
    assert "AI research was founded in 1956" in extracted_text, "Failed to locate expected sentence by offset"
    
    print(f"✓ Can locate sentences by character offset")


def run_all_tests():
    """Run all Stage 0 tests"""
    print("\n=== Stage 0 Tests ===")
    
    try:
        test_sample_documents_exist()
        test_ground_truth_loads()
        test_locate_sentence_by_offset()
        
        print("\n✅ All Stage 0 tests passed!")
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    run_all_tests()
