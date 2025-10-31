"""Quick backend API test"""
import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_backend():
    print("Testing EideticRAG Backend APIs...\n")
    
    # Test 1: Root endpoint
    print("1. Testing root endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.json()}\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Test 2: Model info
    print("2. Testing model info endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/model/info", timeout=10)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            info = resp.json()
            print(f"   Model: {info['model_name']}")
            print(f"   Type: {info['generator_type']}")
            print(f"   Device: {info['device']}\n")
        else:
            print(f"   Response: {resp.json()}\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Test 3: Stats
    print("3. Testing stats endpoint...")
    try:
        resp = requests.get(f"{BASE_URL}/stats", timeout=5)
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.json()}\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # Test 4: Ingest a sample document
    print("4. Testing document ingestion...")
    sample_doc = Path("data/sample_documents/sample1.txt")
    if sample_doc.exists():
        try:
            with open(sample_doc, 'rb') as f:
                files = {'file': (sample_doc.name, f, 'text/plain')}
                resp = requests.post(f"{BASE_URL}/ingest", files=files, timeout=60)
            print(f"   Status: {resp.status_code}")
            print(f"   Response: {resp.json()}\n")
        except Exception as e:
            print(f"   Error: {e}\n")
    else:
        print(f"   Sample document not found at {sample_doc}\n")
    
    # Test 5: Query with LLM (if documents are indexed)
    print("5. Testing query endpoint with LLM integration...")
    try:
        query_data = {
            "query": "What is EideticRAG?",
            "k": 3
        }
        resp = requests.post(f"{BASE_URL}/query", json=query_data, timeout=120)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            result = resp.json()
            print(f"   Query: {result['query']}")
            print(f"   Answer: {result['answer'][:200]}...")
            print(f"   Retrieved chunks: {len(result['chunks'])}")
            print(f"   Metadata: {result['metadata']}\n")
        else:
            print(f"   Response: {resp.json()}\n")
    except Exception as e:
        print(f"   Error: {e}\n")

if __name__ == "__main__":
    test_backend()
