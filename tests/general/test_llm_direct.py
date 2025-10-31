"""Direct test of RAG pipeline with LLM"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.chunker import TextChunker
from core.embeddings import EmbeddingGenerator
from core.vector_index import VectorIndex
from generation.rag_pipeline import RAGPipeline

def test_llm_integration():
    print("Testing LLM Integration...\n")
    
    # Create test document content
    doc_id = "test_doc_001"
    content = """
    EideticRAG is an advanced Retrieval-Augmented Generation system designed for 
    accurate and context-aware question answering. It uses vector embeddings for 
    semantic search and integrates with large language models like Ollama.
    
    The system consists of multiple stages:
    1. Document ingestion and chunking
    2. Embedding generation using sentence transformers
    3. Vector indexing with ChromaDB
    4. Adaptive retrieval based on query intent
    5. LLM generation with provenance tracking
    6. Memory layer for conversation context
    7. Reflection agent for answer verification
    
    EideticRAG supports multiple LLM backends including Ollama, OpenAI, and 
    SpikingBrain. It provides a FastAPI backend and modern React frontend for
    easy interaction.
    """
    
    # Initialize components
    print("1. Initializing components...")
    index_dir = Path("./test_index")
    
    chunker = TextChunker()
    embedder = EmbeddingGenerator(cache_dir=index_dir / "embeddings_cache")
    vector_index = VectorIndex(persist_dir=index_dir)
    
    # Chunk and embed
    print("2. Chunking document...")
    chunks = chunker.chunk_document(doc_id, content, {"source": "test"})
    print(f"   Created {len(chunks)} chunks")
    
    print("3. Generating embeddings...")
    embedded_chunks = embedder.embed_chunks(chunks)
    print(f"   Generated {len(embedded_chunks)} embeddings")
    
    print("4. Adding to index...")
    count = vector_index.add_embeddings(embedded_chunks)
    print(f"   Added {count} chunks to index")
    
    # Initialize RAG pipeline
    print("\n5. Initializing RAG pipeline with Ollama...")
    rag = RAGPipeline(
        index_dir=index_dir,
        generator_type="ollama",
        model_name="deepseek-coder:6.7b-instruct-q4_K_M",
        retrieval_k=3
    )
    
    # Test query
    print("\n6. Testing query with LLM...")
    query = "What is EideticRAG and what are its main components?"
    print(f"   Query: {query}")
    
    try:
        result = rag.query(query, k=3)
        print(f"\n   ✓ LLM Response:")
        print(f"   {result['answer']}")
        print(f"\n   Retrieved {len(result['chunks'])} chunks")
        print(f"   Metadata: {result['metadata']}")
        
        if result.get('spike_info'):
            print(f"   SpikingBrain info: {result['spike_info']}")
            
        print("\n✓✓✓ LLM INTEGRATION WORKING! ✓✓✓")
        return True
    except Exception as e:
        print(f"\n   ✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_llm_integration()
    sys.exit(0 if success else 1)
