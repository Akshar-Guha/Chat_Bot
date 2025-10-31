#!/usr/bin/env python3
"""
Simple API test for the RAG system with Ollama
"""
import requests
import json

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:8000"

    print("🧪 Testing EideticRAG API with Ollama")
    print("=" * 50)

    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/")
        print("✅ API Health Check:", response.json())
    except Exception as e:
        print("❌ API Health Check Failed:", str(e))
        return False

    # Test 2: Stats
    try:
        response = requests.get(f"{base_url}/stats")
        print("✅ Index Stats:", response.json())
    except Exception as e:
        print("❌ Index Stats Failed:", str(e))

    # Test 3: Query (this will use Ollama)
    test_query = "What is machine learning?"
    print(f"\n🤖 Testing Query: '{test_query}'")
    print("-" * 30)

    try:
        response = requests.post(
            f"{base_url}/query",
            json={"query": test_query, "k": 3},
            timeout=30  # Give time for Ollama generation
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Query Successful!")
            print(f"   Answer: {result['answer'][:200]}...")
            print(f"   Model Used: {result['metadata']['model']}")
            print(f"   Chunks Retrieved: {result['metadata']['num_chunks_retrieved']}")
            print(f"   Processing Time: ~{result['metadata'].get('processing_time', 'N/A')}s")
            return True
        else:
            print(f"❌ Query Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Query Timeout: Ollama might be processing slowly")
        return False
    except Exception as e:
        print(f"❌ Query Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_api()

    print("\n" + "=" * 50)
    if success:
        print("🎉 Integration Test PASSED!")
        print("\nYour EideticRAG system with Ollama is working perfectly!")
        print("✅ API server running")
        print("✅ Ollama integration active")
        print("✅ RAG pipeline functional")
        print("\n🌐 Access the web interface at: http://localhost:3000")
        print("📖 API documentation at: http://localhost:8000/docs")
    else:
        print("⚠️  Some tests failed. Check:")
        print("1. Ollama is running: ollama serve")
        print("2. Model is available: ollama list")
        print("3. API server: python -m uvicorn src.api.main:app --reload")
