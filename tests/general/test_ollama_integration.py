#!/usr/bin/env python3
"""
Test script for Ollama integration
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from generation.generator import LLMGenerator

def test_ollama_integration():
    """Test Ollama integration"""
    print("🧪 Testing Ollama integration...")

    # Test generator initialization
    try:
        generator = LLMGenerator(
            model_type="ollama",
            model_name="llama2",
            temperature=0.7,
            max_tokens=200
        )
        print("✅ Generator initialized successfully")
        print(f"   Model type: {generator.model_type}")
        print(f"   Model name: {generator.model_name}")
        return True

    except Exception as e:
        print(f"❌ Generator initialization failed: {e}")
        return False

def test_ollama_generation():
    """Test actual generation with Ollama"""
    print("\n🤖 Testing generation...")

    try:
        generator = LLMGenerator(
            model_type="ollama",
            model_name="llama2",
            temperature=0.1,
            max_tokens=100
        )

        # Simple test query
        result = generator.generate(
            query="What is artificial intelligence?",
            retrieved_chunks=[{
                'text': 'AI is the simulation of human intelligence in machines.',
                'chunk_id': 'test-001',
                'score': 0.9
            }]
        )

        print("✅ Generation successful!")
        print(f"   Answer: {result.answer[:100]}...")
        print(f"   Model: {result.model}")
        return True

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Ollama Integration Test")
    print("=" * 40)

    success1 = test_ollama_integration()
    success2 = test_ollama_generation()

    print("\n" + "=" * 40)
    if success1 and success2:
        print("🎉 All tests passed! Ollama integration is working.")
        print("\nNext steps:")
        print("1. Start Ollama: ollama serve")
        print("2. Pull models: ollama pull llama2")
        print("3. Start API: python -m uvicorn src.api.main:app --reload")
        print("4. Test: curl -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{\"query\": \"Hello\"}'")
    else:
        print("⚠️  Some tests failed. Check Ollama installation and models.")
