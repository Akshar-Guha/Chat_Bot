"""
Test harness for Stage 5 - Reflection Agent & Verification
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reflection.verification_engine import VerificationEngine, Claim
from src.reflection.reflection_agent import ReflectionAgent, ReflectionAction
from src.generation.generator import LLMGenerator


def test_hallucination_detection():
    """Test detection of hallucinated content"""
    print("\n=== Test: Hallucination Detection ===")
    
    engine = VerificationEngine()
    
    # Test case 1: Fully supported answer
    supported_answer = "AI research was founded in 1956 at Dartmouth College."
    supported_chunks = [
        {
            'chunk_id': 'chunk1',
            'text': 'The field of AI research was founded in 1956 at Dartmouth College, where researchers gathered.',
            'score': 0.95
        }
    ]
    
    result = engine.verify_answer(supported_answer, supported_chunks)
    
    assert result.hallucination_score < 0.3, f"Supported answer wrongly flagged: {result.hallucination_score}"
    assert result.overall_support_ratio > 0.7, "Support ratio too low for supported answer"
    print(f"✓ Supported answer verified (hallucination: {result.hallucination_score:.2f})")
    
    # Test case 2: Partially hallucinated answer
    mixed_answer = "AI was founded in 1956. It immediately solved all computing problems."
    mixed_chunks = [
        {
            'chunk_id': 'chunk2',
            'text': 'AI research was founded in 1956 at Dartmouth College.',
            'score': 0.9
        }
    ]
    
    result = engine.verify_answer(mixed_answer, mixed_chunks)
    
    assert result.hallucination_score > 0.3, "Mixed answer not detected as partial hallucination"
    assert len(result.unsupported_claims) > 0, "No unsupported claims detected"
    print(f"✓ Partial hallucination detected (score: {result.hallucination_score:.2f})")
    
    # Test case 3: Complete hallucination
    hallucinated_answer = "AI was invented by aliens in 2050 on Mars."
    
    result = engine.verify_answer(hallucinated_answer, supported_chunks)
    
    assert result.hallucination_score > 0.7, "Complete hallucination not detected"
    assert result.overall_support_ratio < 0.3, "Support ratio too high for hallucination"
    print(f"✓ Complete hallucination detected (score: {result.hallucination_score:.2f})")
    
    print("\n✓ Hallucination detection working correctly")
    return True


def test_regeneration_flow():
    """Test the regeneration workflow"""
    print("\n=== Test: Regeneration Flow ===")
    
    agent = ReflectionAgent(hallucination_threshold=0.3)
    generator = LLMGenerator(model_type="mock")
    
    # Initial answer with hallucination
    bad_answer = "Python was created in 1991 by Guido van Rossum. It can read minds."
    query = "Tell me about Python programming language"
    chunks = [
        {
            'chunk_id': 'py1',
            'text': 'Python is a high-level programming language created by Guido van Rossum and first released in 1991.',
            'score': 0.9
        }
    ]
    
    # Test reflection
    result = agent.reflect_on_answer(
        answer=bad_answer,
        query=query,
        retrieved_chunks=chunks,
        generator=generator
    )
    
    assert result.iterations > 0, "No iterations performed"
    assert result.verification is not None, "No verification performed"
    
    print(f"✓ Reflection completed in {result.iterations} iteration(s)")
    print(f"  Original: '{bad_answer[:50]}...'")
    print(f"  Final: '{result.final_answer[:50]}...'")
    print(f"  Success: {result.success}")
    
    # Check that decision was made
    assert result.decision is not None, "No decision made"
    print(f"  Final decision: {result.decision.action.value}")
    
    print("\n✓ Regeneration flow working")
    return True


def test_false_positive_check():
    """Test that valid paraphrases aren't flagged as unsupported"""
    print("\n=== Test: False Positive Check ===")
    
    engine = VerificationEngine()
    
    # Paraphrased but correct answer
    paraphrased_answer = "The study of artificial intelligence began in the mid-1950s at a conference at Dartmouth."
    source_chunks = [
        {
            'chunk_id': 'chunk1',
            'text': 'The field of AI research was founded in 1956 at Dartmouth College.',
            'score': 0.9
        }
    ]
    
    result = engine.verify_answer(paraphrased_answer, source_chunks)
    
    # Should recognize paraphrase as supported
    assert result.overall_support_ratio > 0.5, \
        f"Paraphrase wrongly marked unsupported: {result.overall_support_ratio}"
    
    print(f"✓ Paraphrase correctly verified (support: {result.overall_support_ratio:.2f})")
    
    # Test with synonyms
    synonym_answer = "Machine learning enables computers to learn from data."
    synonym_chunks = [
        {
            'chunk_id': 'ml1',
            'text': 'ML allows computers to learn patterns from data without explicit programming.',
            'score': 0.85
        }
    ]
    
    result = engine.verify_answer(synonym_answer, synonym_chunks)
    
    assert result.hallucination_score < 0.5, \
        f"Synonym usage wrongly flagged: {result.hallucination_score}"
    
    print(f"✓ Synonyms handled correctly (hallucination: {result.hallucination_score:.2f})")
    
    print("\n✓ False positive check passed")
    return True


def test_annotation_and_explanation():
    """Test answer annotation and explanation generation"""
    print("\n=== Test: Annotation & Explanation ===")
    
    agent = ReflectionAgent()
    engine = VerificationEngine()
    
    # Answer with mixed support
    answer = "AI was founded in 1956. It has achieved human-level intelligence. ML is a subset of AI."
    chunks = [
        {
            'chunk_id': 'ai1',
            'text': 'AI research was founded in 1956. Machine Learning is a subset of AI.',
            'score': 0.9
        }
    ]
    
    # Verify
    verification = engine.verify_answer(answer, chunks)
    
    # Annotate
    annotated = agent.annotate_answer(verification)
    
    assert "[UNSUPPORTED" in annotated or "[Verification:" in annotated, \
        "No annotations added to answer"
    
    print("✓ Answer annotated with verification results")
    print(f"  Annotated preview: {annotated[:100]}...")
    
    # Generate explanation
    result = agent.reflect_on_answer(answer, "What is AI?", chunks)
    explanation = agent.explain_decision(result)
    
    assert len(explanation) > 0, "No explanation generated"
    assert "Support ratio" in explanation or "verified" in explanation, \
        "Explanation missing key information"
    
    print("\n✓ Explanation generated:")
    for line in explanation.split('\n')[:5]:  # Show first 5 lines
        print(f"  {line}")
    
    print("\n✓ Annotation and explanation working")
    return True


def test_refusal_generation():
    """Test appropriate refusal when sources insufficient"""
    print("\n=== Test: Refusal Generation ===")
    
    agent = ReflectionAgent(hallucination_threshold=0.2)
    
    # Query with no good sources
    complex_query = "Explain quantum computing and its impact on cryptography"
    irrelevant_chunks = [
        {
            'chunk_id': 'irr1',
            'text': 'Classical computers use bits that are either 0 or 1.',
            'score': 0.4
        }
    ]
    
    # Answer that would be mostly unsupported
    speculative_answer = "Quantum computers will break all encryption by 2030 using superposition."
    
    result = agent.reflect_on_answer(
        answer=speculative_answer,
        query=complex_query,
        retrieved_chunks=irrelevant_chunks
    )
    
    # Should refuse or heavily qualify
    if not result.success:
        assert "cannot provide" in result.final_answer.lower() or \
               "insufficient" in result.final_answer.lower(), \
               "Refusal message not appropriate"
        print(f"✓ Appropriately refused: '{result.final_answer[:100]}...'")
    else:
        # If it didn't refuse, hallucination score should be high
        assert result.verification.hallucination_score > 0.5, \
            "Should have high hallucination score or refuse"
        print(f"✓ High hallucination flagged: {result.verification.hallucination_score:.2f}")
    
    print("\n✓ Refusal generation working appropriately")
    return True


def run_all_tests():
    """Run all Stage 5 tests"""
    print("\n=== Stage 5 Tests: Reflection Agent & Verification ===")
    
    try:
        # Run tests
        test_hallucination_detection()
        test_regeneration_flow()
        test_false_positive_check()
        test_annotation_and_explanation()
        test_refusal_generation()
        
        print("\n✅ All Stage 5 tests passed!")
        print("\nStage 5 Acceptance Criteria Met:")
        print("✓ Hallucination detection working")
        print("✓ Regeneration flow functional")
        print("✓ False positives minimized")
        print("✓ Annotations and explanations clear")
        print("✓ Appropriate refusals for insufficient sources")
        
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
