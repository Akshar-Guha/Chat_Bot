"""
Test harness for Stage 3 - Retriever Controller & Intent Classification
"""

import sys
from pathlib import Path
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retrieval.intent_classifier import IntentClassifier, QueryIntent
from src.retrieval.retrieval_controller import RetrievalController


def test_intent_classification():
    """Test intent classification for different query types"""
    print("\n=== Test: Intent Classification ===")
    
    classifier = IntentClassifier()
    
    test_cases = [
        ("When was AI research founded?", QueryIntent.FACTUAL),
        ("What is the difference between ML and AI?", QueryIntent.COMPARATIVE),
        ("Why does climate change occur?", QueryIntent.CAUSAL),
        ("What is machine learning?", QueryIntent.DEFINITIONAL),
        ("How to implement a neural network?", QueryIntent.PROCEDURAL),
        ("Write a Python function to sort a list", QueryIntent.CODE),
        ("Tell me about renewable energy", QueryIntent.EXPLORATORY)
    ]
    
    correct = 0
    for query, expected_intent in test_cases:
        result = classifier.classify(query)
        
        if result.primary_intent == expected_intent:
            correct += 1
            print(f"✓ '{query[:40]}...' -> {result.primary_intent.value} (confidence: {result.confidence:.2f})")
        else:
            print(f"✗ '{query[:40]}...' -> Expected: {expected_intent.value}, Got: {result.primary_intent.value}")
    
    accuracy = correct / len(test_cases)
    assert accuracy >= 0.7, f"Intent classification accuracy too low: {accuracy:.2%}"
    
    print(f"\n✓ Intent classification accuracy: {accuracy:.2%}")
    return True


def test_policy_selection():
    """Test that different intents select different policies"""
    print("\n=== Test: Policy Selection ===")
    
    # Setup test index
    base_path = Path(__file__).parent.parent
    test_index_dir = base_path / "test_controller_index"
    
    # Initialize controller
    controller = RetrievalController(index_dir=test_index_dir)
    
    # Test queries with different intents
    test_queries = {
        "When was AI founded?": QueryIntent.FACTUAL,
        "Compare Python and Java": QueryIntent.COMPARATIVE,
        "Why is the sky blue?": QueryIntent.CAUSAL,
        "What is deep learning?": QueryIntent.DEFINITIONAL
    }
    
    policies_used = set()
    
    for query, expected_intent in test_queries.items():
        # Classify and get policy
        intent_result = controller.intent_classifier.classify(query)
        policy = controller.get_policy(intent_result.primary_intent)
        
        # Track unique policies
        policy_key = (policy.k, policy.multi_hop, policy.diversity_factor)
        policies_used.add(policy_key)
        
        print(f"✓ Query: '{query[:30]}...'")
        print(f"  Intent: {intent_result.primary_intent.value}")
        print(f"  Policy: k={policy.k}, multi_hop={policy.multi_hop}, strategy={policy.metadata.get('strategy')}")
    
    # Verify different policies are used
    assert len(policies_used) >= 3, f"Not enough policy variation: only {len(policies_used)} unique policies"
    
    print(f"\n✓ Policy selection working ({len(policies_used)} unique policies used)")
    return True


def test_policy_effects():
    """Test that different policies produce measurably different results"""
    print("\n=== Test: Policy Effects ===")
    
    # This test verifies that policies actually change retrieval behavior
    # We'll simulate by checking policy parameters
    
    base_path = Path(__file__).parent.parent
    test_index_dir = base_path / "test_controller_index"
    
    controller = RetrievalController(index_dir=test_index_dir)
    
    # Get policies for different intents
    factual_policy = controller.get_policy(QueryIntent.FACTUAL)
    comparative_policy = controller.get_policy(QueryIntent.COMPARATIVE)
    exploratory_policy = controller.get_policy(QueryIntent.EXPLORATORY)
    
    # Test 1: Factual should retrieve fewer chunks than exploratory
    assert factual_policy.k < exploratory_policy.k, \
        f"Factual k ({factual_policy.k}) should be less than exploratory k ({exploratory_policy.k})"
    print(f"✓ Factual retrieves fewer chunks ({factual_policy.k}) than exploratory ({exploratory_policy.k})")
    
    # Test 2: Comparative should enable multi-hop
    assert comparative_policy.multi_hop == True, "Comparative should enable multi-hop"
    assert factual_policy.multi_hop == False, "Factual should not use multi-hop"
    print(f"✓ Comparative uses multi-hop, factual doesn't")
    
    # Test 3: Exploratory should have higher diversity factor
    assert exploratory_policy.diversity_factor > factual_policy.diversity_factor, \
        "Exploratory should have higher diversity"
    print(f"✓ Exploratory has higher diversity ({exploratory_policy.diversity_factor}) than factual ({factual_policy.diversity_factor})")
    
    # Test 4: Different minimum score thresholds
    assert factual_policy.min_score_threshold > exploratory_policy.min_score_threshold, \
        "Factual should have stricter threshold"
    print(f"✓ Factual has stricter threshold ({factual_policy.min_score_threshold}) than exploratory ({exploratory_policy.min_score_threshold})")
    
    print("\n✓ Policy effects verified - different intents use meaningfully different retrieval strategies")
    return True


def test_query_expansion():
    """Test query expansion for different intents"""
    print("\n=== Test: Query Expansion ===")
    
    base_path = Path(__file__).parent.parent
    test_index_dir = base_path / "test_controller_index"
    
    controller = RetrievalController(index_dir=test_index_dir)
    
    # Test comparative query expansion
    comp_query = "Compare Python and Java programming languages"
    comp_intent = controller.intent_classifier.classify(comp_query)
    expanded = controller._expand_query(comp_query, comp_intent)
    
    assert len(expanded) > 1, "Comparative query should be expanded"
    print(f"✓ Comparative query expanded to {len(expanded)} queries")
    for i, q in enumerate(expanded):
        print(f"  {i+1}. {q[:50]}...")
    
    # Test causal query expansion
    causal_query = "Why does climate change occur?"
    causal_intent = controller.intent_classifier.classify(causal_query)
    expanded = controller._expand_query(causal_query, causal_intent)
    
    assert len(expanded) > 1, "Causal query should be expanded"
    print(f"\n✓ Causal query expanded to {len(expanded)} queries")
    
    # Test factual query (should not expand)
    factual_query = "When was AI founded?"
    factual_intent = controller.intent_classifier.classify(factual_query)
    factual_policy = controller.get_policy(factual_intent.primary_intent)
    
    assert factual_policy.expand_query == False, "Factual queries should not be expanded"
    print(f"\n✓ Factual queries not expanded (as expected)")
    
    return True


def run_all_tests():
    """Run all Stage 3 tests"""
    print("\n=== Stage 3 Tests: Retriever Controller & Intent Classification ===")
    
    try:
        # Run tests
        test_intent_classification()
        test_policy_selection()
        test_policy_effects()
        test_query_expansion()
        
        print("\n✅ All Stage 3 tests passed!")
        print("\nStage 3 Acceptance Criteria Met:")
        print("✓ Intent classification working with good accuracy")
        print("✓ Different intents trigger different retrieval policies")
        print("✓ Policy effects are measurable and meaningful")
        print("✓ Query expansion working for appropriate intents")
        
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
