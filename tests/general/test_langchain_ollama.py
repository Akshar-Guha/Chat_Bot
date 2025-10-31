from langchain_community.llms import Ollama

try:
    ollama = Ollama(
        base_url="http://localhost:11434",
        model="llama3.2:1b",
        temperature=0.7
    )
    response = ollama.invoke("Say hello in one word")
    print(f"Success! Response: {response}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
