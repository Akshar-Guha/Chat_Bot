import os
from pathlib import Path
import json
import requests

BASE_URL = os.environ.get("EIDETIC_RAG_BASE_URL", "http://127.0.0.1:8000")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
os.environ.setdefault("OLLAMA_HOST", OLLAMA_HOST)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_documents"
DOC_PATH = DATA_DIR / "sample1.txt"


def show_response(label: str, response: requests.Response) -> None:
    print(f"\n=== {label} ===")
    print(f"Status: {response.status_code}")
    try:
        parsed = response.json()
        print(json.dumps(parsed, indent=2))
    except ValueError:
        print(response.text)


def main() -> None:
    if not DOC_PATH.exists():
        raise FileNotFoundError(f"Sample document not found at {DOC_PATH}")

    print(f"Using BASE URL: {BASE_URL}")
    print(f"Using OLLAMA_HOST: {os.environ['OLLAMA_HOST']}")

    with DOC_PATH.open("rb") as handle:
        files = {"file": (DOC_PATH.name, handle, "text/plain")}
        ingest_resp = requests.post(f"{BASE_URL}/ingest", files=files, timeout=120)
    show_response("POST /ingest", ingest_resp)

    query_payload = {"query": "What is EideticRAG?"}
    query_resp = requests.post(
        f"{BASE_URL}/query",
        json=query_payload,
        timeout=120,
    )
    show_response("POST /query", query_resp)

    stats_resp = requests.get(f"{BASE_URL}/stats", timeout=30)
    show_response("GET /stats", stats_resp)

    clear_resp = requests.delete(f"{BASE_URL}/index/clear", timeout=30)
    show_response("DELETE /index/clear", clear_resp)

    stats_after_resp = requests.get(f"{BASE_URL}/stats", timeout=30)
    show_response("GET /stats (after clear)", stats_after_resp)


if __name__ == "__main__":
    main()
