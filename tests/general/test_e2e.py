"""End-to-end test for the EideticRAG application."""
import requests
from pathlib import Path
import time

BASE_URL = "http://127.0.0.1:8000"
SAMPLE_DOC = Path("data/sample_documents/sample1.txt")

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_e2e():
    print_section("EIDETIC RAG END-TO-END TEST")

    # 1. Clear the index for a clean test
    print_section("1. Clearing Index")
    try:
        resp = requests.delete(f"{BASE_URL}/index/clear", timeout=30)
        if resp.status_code == 200:
            print("✓ Index cleared successfully.")
        else:
            print(f"✗ Failed to clear index: {resp.text}")
            return
    except Exception as e:
        print(f"✗ Error clearing index: {e}")
        return

    # 2. Ingest a sample document
    print_section("2. Ingesting Sample Document")
    if not SAMPLE_DOC.exists():
        print(f"✗ Sample document not found at {SAMPLE_DOC}")
        return
    
    try:
        with open(SAMPLE_DOC, 'rb') as f:
            files = {'file': (SAMPLE_DOC.name, f, 'text/plain')}
            resp = requests.post(f"{BASE_URL}/ingest", files=files, timeout=60)
        
        if resp.status_code == 200:
            ingest_data = resp.json()
            print(f"✓ Document '{ingest_data['filename']}' ingested successfully.")
            print(f"✓ {ingest_data['num_chunks']} chunks created.")
        else:
            print(f"✗ Ingestion failed: {resp.text}")
            return
    except Exception as e:
        print(f"✗ Error during ingestion: {e}")
        return

    # Give the index a moment to settle
    time.sleep(1)

    # 3. Query the ingested document
    print_section("3. Querying with LLM")
    query = "What is EideticRAG?"
    print(f"  Query: {query}")
    try:
        query_data = {"query": query, "k": 3}
        resp = requests.post(f"{BASE_URL}/query", json=query_data, timeout=120)

        if resp.status_code == 200:
            result = resp.json()
            print("✓ Query successful.")
            print(f"  LLM Answer: {result['answer']}")
        else:
            print(f"✗ Query failed: {resp.text}")
            return
    except Exception as e:
        print(f"✗ Error during query: {e}")
        return

    print_section("✓✓✓ APPLICATION IS FULLY FUNCTIONAL ✓✓✓")

if __name__ == "__main__":
    test_e2e()
