# EideticRAG - Advanced RAG System

A modern, production-ready Retrieval-Augmented Generation (RAG) system with persistent memory, reflection capabilities, and a beautiful React frontend.

## 🏗️ Architecture Overview

This project follows modern software engineering best practices with a clean, domain-driven architecture:

### Backend Structure (Domain-Driven Design)
```
eidetic_rag/backend/
├── app/
│   ├── api/v1/          # REST API endpoints organized by domain
│   │   ├── health.py    # Health checks
│   │   ├── queries.py   # Query operations
│   │   ├── documents.py # Document management
│   │   └── memory.py    # Memory operations
│   ├── core/            # Core functionality
│   │   ├── dependencies.py # Dependency injection
│   │   └── services/    # Business logic services
│   ├── models/          # Pydantic models
│   └── main.py         # Application entry point
├── config/              # Configuration management
└── tests/              # Comprehensive test suite
```

### Frontend Structure (Feature-Based)
```
src/frontend/src/
├── components/          # Reusable UI components
│   ├── ui/             # Basic UI components
│   ├── features/       # Feature-specific components
│   └── common/         # Shared components
├── hooks/              # Custom React hooks
├── services/           # API services
├── types/              # TypeScript definitions
├── utils/              # Utility functions
└── pages/              # Route components
```

## 🚀 Key Features

### ✅ Modern Tech Stack
- **Backend**: FastAPI, SQLAlchemy, ChromaDB, OpenAI/LangChain
- **Frontend**: React 18, TypeScript, Material-UI, React Query
- **DevOps**: Poetry, Black, isort, mypy, pre-commit
- **Architecture**: Domain-driven design, dependency injection, async/await

### ✅ Advanced RAG Capabilities
- **Multi-modal ingestion**: PDF, DOCX, TXT, HTML, Markdown
- **Intelligent chunking**: Semantic-aware text splitting
- **Vector search**: ChromaDB with FAISS indexing
- **Persistent memory**: SQL-based memory with tagging
- **Reflection system**: Hallucination detection and answer verification
- **Adaptive retrieval**: Context-aware result ranking
- **Local LLM Support**: Ollama integration for privacy and cost control

### ✅ Production Ready
- **Health monitoring**: Comprehensive health checks
- **Structured logging**: Loguru with configurable levels
- **Error handling**: Graceful error recovery
- **Configuration**: Environment-based settings
- **Caching**: Multi-level caching (Redis + disk)
- **Testing**: Comprehensive test coverage

## 🛠️ Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Redis (optional, for caching)
- **Ollama** (for local LLM) - Download from https://ollama.ai/

### Ollama Setup (Local LLM)
```bash
# Install Ollama
# Visit https://ollama.ai/ and follow installation instructions

# Pull a model (recommended: llama2 for general use)
ollama pull llama2

# Alternative models
ollama pull mistral     # Faster, good quality
ollama pull codellama   # For code-related queries
ollama pull llama2:13b  # More capable but slower

# Start Ollama service
ollama serve
```

The system is configured to use Ollama by default for local, private LLM generation.

### Backend Setup
```bash
# Install dependencies with Poetry (modern package management)
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run migrations (if using database features)
poetry run alembic upgrade head

# Start the server
poetry run eidetic-rag
# or
poetry run uvicorn eidetic_rag.backend.app.main:app --reload
```

### Frontend Setup
```bash
cd src/frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

### API Documentation
Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

## 📁 Modern Project Structure Details

### Backend Architecture

#### Domain-Driven API Structure
```
app/api/v1/
├── health/     # System health and monitoring
├── queries/    # RAG query operations
├── documents/  # Document ingestion and management
└── memory/     # Persistent memory operations
```

#### Service Layer
```
app/services/
├── rag_service.py      # Main RAG orchestration
├── embedding_service.py # Text embeddings
├── vector_service.py   # Vector operations
└── generation_service.py # LLM integration
```

#### Configuration Management
```python
# config/settings.py - Centralized configuration
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "EideticRAG API"
    OPENAI_API_KEY: str
    DATABASE_URL: str = "sqlite:///./memory.db"

    class Config:
        env_file = ".env"
```

### Frontend Architecture

#### Custom Hooks
```typescript
// src/frontend/src/hooks/useQuery.ts - RAG query hook
export const useQuery = () => {
  const [data, setData] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (request: QueryRequest) => {
    // Query logic with loading states
  }, []);

  return { data, loading, error, execute };
};
```

#### Type-Safe API Service
```typescript
// src/frontend/src/services/api.ts - Modern API service
class ApiService {
  async query(request: QueryRequest): Promise<QueryResponse> {
    const response = await this.client.post('/queries/', request);
    return response.data;
  }
}
```

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=eidetic_rag

# Run specific tests
poetry run pytest tests/test_queries.py
```

### Frontend Tests
```bash
cd src/frontend

# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev
COPY . .
CMD ["poetry", "run", "eidetic-rag"]
```

### Environment Variables
```bash
# .env
OPENAI_API_KEY=your_key_here
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
DEBUG=false
```

## 📚 Best Practices Implemented

### ✅ Code Quality
- **Linting**: Black, isort, flake8, mypy
- **Pre-commit**: Automated code formatting and checks
- **Type hints**: Full type coverage
- **Documentation**: Comprehensive docstrings

### ✅ Architecture Patterns
- **Dependency injection**: FastAPI dependency system
- **Repository pattern**: Data access abstraction
- **Service layer**: Business logic separation
- **Configuration management**: Environment-based settings

### ✅ Modern Development
- **Async/await**: Full async support
- **Connection pooling**: Efficient resource usage
- **Health checks**: System monitoring
- **Graceful shutdown**: Clean resource cleanup

## 🔧 Development

### Adding New Features

#### Backend Feature
1. Create domain module in `app/api/v1/`
2. Add service in `app/services/`
3. Update dependency injection
4. Add tests in `tests/`

#### Frontend Feature
1. Create feature components in `components/features/`
2. Add custom hooks in `hooks/`
3. Update types in `types/`
4. Add tests

### Code Style
```bash
# Format Python code
poetry run black .
poetry run isort .

# Format frontend code
cd src/frontend && npm run lint:fix
```

## 📈 Performance

### Optimizations Implemented
- **Vector indexing**: FAISS for fast similarity search
- **Connection pooling**: Efficient database connections
- **Caching layers**: Multi-level caching strategy
- **Async processing**: Non-blocking operations
- **Batch processing**: Efficient bulk operations

### Monitoring
- **Health endpoints**: System status monitoring
- **Performance metrics**: Query timing and throughput
- **Error tracking**: Comprehensive error logging
- **Resource usage**: Memory and CPU monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Note**: This is a complete modernization using current best practices while maintaining backward compatibility with the existing frontend interface.
