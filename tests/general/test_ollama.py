"""Test Ollama directly"""
import requests
import json

def test_ollama():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.2:1b",
        "prompt": "What is 2+2?",
        "stream": False
    }
    
    print("Testing Ollama...")
    print(f"URL: {url}")
    print(f"Model: {payload['model']}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result.get('response', 'No response field')}")
            print("\n✓ Ollama is working!")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ollama()
