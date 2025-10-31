..#0
  Ollama Integration Guide

## Prerequisites
1. **Install Ollama**: Download from https://ollama.ai/
2. **Pull a model**: Run `ollama pull llama2` (or any other model)
3. **Start Ollama service**: Run `ollama serve`

## Available Models
- `llama2`: Fast and capable (default)
- `llama2:13b`: More powerful but slower
- `mistral`: Good alternative
- `codellama`: For code-related queries

## Configuration
The system is now configured to use Ollama by default. You can change the model in `src/api/main.py`:

```python
model_type="ollama"
model_name="llama2"  # Change this to use different models
```

## Usage
1. **Start the API**:
   ```bash
   cd src/api
   python -m uvicorn main:app --reload
   ```

2. **Test with curl**:
   ```bash
   curl -X POST "http://localhost:8000/query" \
        -H "Content-Type: application/json" \
        -d '{"query": "What is machine learning?"}'
   ```

3. **Switch models**: Edit `src/api/main.py` and restart the server

## Performance Tips
- **GPU**: Use CUDA-enabled models for better performance
- **RAM**: Ensure sufficient RAM (4GB+ for llama2)
- **Temperature**: Adjust in the generator for creativity vs accuracy
- **Context length**: Longer contexts need more RAM

## Troubleshooting
- **Connection errors**: Ensure Ollama is running (`ollama serve`)
- **Model not found**: Pull the model first (`ollama pull llama2`)
- **Slow responses**: Try smaller models or adjust parameters
