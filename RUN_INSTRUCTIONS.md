# EideticRAG - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- 8GB RAM minimum
- 10GB disk space

---

## 📦 Installation

### 1. Backend Setup
```bash
# Navigate to project root
cd s:\projects\Project-1

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd src/frontend

# Install Node dependencies
npm install
```

---

## 🏃 Running the Application

### Start Backend Server
```bash
# From project root
python -m src.api.main

# Server will start on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Start Frontend (in a new terminal)
```bash
# From src/frontend directory
cd src/frontend
npm start

# UI will open at http://localhost:3000
```

---

## 🧪 Running Tests

### Run All Tests
```bash
# From project root
python -m pytest tests/ -v
```

### Run Individual Stage Tests
```bash
# Test specific stages
python tests/test_stage0.py  # Planning & Setup
python tests/test_stage1.py  # Core Foundation
python tests/test_stage2.py  # Baseline RAG
python tests/test_stage3.py  # Retriever Controller
python tests/test_stage4.py  # Memory Layer
python tests/test_stage5.py  # Reflection Agent
python tests/test_stage6.py  # Orchestration
python tests/test_stage7.py  # Frontend
```

---

## 📝 First Steps

### 1. Ingest Sample Documents
```bash
# Using CLI
python -m src.core.cli ingest data/sample_documents/sample1.txt
python -m src.core.cli ingest data/sample_documents/sample2.txt
```

### 2. Try a Query
1. Open http://localhost:3000 in your browser
2. Enter a question like "What is machine learning?"
3. Click "Search"
4. View the answer with sources and provenance

### 3. Explore Features
- **Memory Inspector**: View and edit stored memories
- **Document Manager**: Upload new documents
- **Dashboard**: Monitor system performance

---

## ⚙️ Configuration

### Using OpenAI Instead of Mock
```bash
# Set environment variable
set OPENAI_API_KEY=your-api-key  # Windows
# export OPENAI_API_KEY=your-api-key  # Linux/Mac

# Update config in code
# In src/api/main.py, change:
model_type="openai"  # Instead of "mock"
```

### Adjust Chunking Parameters
Edit `src/api/main.py`:
```python
chunker = TextChunker(
    chunk_size=500,    # Adjust chunk size
    chunk_overlap=50   # Adjust overlap
)
```

---

## 📊 Monitoring

### View Logs
```bash
# Logs are in the logs/ directory
tail -f logs/eidetic_rag_*.log
```

### Access Dashboard
Navigate to http://localhost:3000/dashboard

---

## 🛠️ Troubleshooting

### Issue: ModuleNotFoundError
**Solution**: Ensure you're in the virtual environment and dependencies are installed
```bash
pip install -r requirements.txt
```

### Issue: Port Already in Use
**Solution**: Change ports in configuration
- Backend: Edit `src/api/main.py` - change port 8000
- Frontend: Use `npm start -- --port 3001`

### Issue: ChromaDB Error
**Solution**: Clear the index
```bash
rm -rf index/  # Remove index directory
python -m src.core.cli reindex
```

### Issue: Memory Database Error
**Solution**: Reset the database
```bash
rm memory.db  # Remove database file
# It will be recreated on next run
```

---

## 📚 Key Commands Reference

### CLI Commands
```bash
# Ingest document
python -m src.core.cli ingest <file_path>

# Rebuild index
python -m src.core.cli reindex

# Inspect index
python -m src.core.cli inspect

# Search index
python -m src.core.cli search "your query"
```

### API Endpoints
- `POST /query` - Submit a query
- `POST /ingest` - Upload a document
- `GET /stats` - Get system statistics
- `DELETE /index/clear` - Clear the index

---

## 🔒 Security Notes

1. **Never commit API keys** - Use environment variables
2. **CORS is enabled** - Restrict origins in production
3. **File uploads** - Limited to specific formats
4. **Memory data** - Can be exported/deleted for privacy

---

## 📖 Additional Resources

- [README.md](./README.md) - Project overview
- [DEVELOPMENT_STATUS.md](./DEVELOPMENT_STATUS.md) - Development progress
- [API Docs](http://localhost:8000/docs) - Interactive API documentation
- Test files in `tests/` - Examples of usage

---

## 💡 Tips

1. Start with small documents for testing
2. Monitor the Dashboard for performance metrics
3. Use the Memory Inspector to improve responses
4. Enable reflection for better answer quality
5. Check logs if something goes wrong

---

**Version**: 0.1.0  
**Support**: Create an issue in the repository
