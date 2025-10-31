import requests

# Test the backend API with a simple query
try:
    response = requests.post(
        "http://localhost:8000/query",
        json={
            "query": "Hello, can you test this?",
            "generator": {
                "type": "ollama",
                "model": "llama3.2:1b"
            }
        },
        timeout=30
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Answer: {result.get('answer', 'No answer')}")
        print(f"Model: {result.get('model', 'Unknown')}")
        print("✓ Backend is working!")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")
