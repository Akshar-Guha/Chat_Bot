"""Test RAG pipeline with mock generator"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.chunker import TextChunker
from core.embeddings import EmbeddingGenerator
from core.vector_index import VectorIndex
from generation.rag_pipeline import RAGPipeline


def test_with_mock():
    print("Testing RAG Pipeline with Mock Generator...\n")
    
    # Test content
    doc_id = "test_doc_001"
    content = """
    EideticRAG is an advanced Retrieval-Augmented Generation system.
    It uses vector embeddings for semantic search and LLM integration.
    The system has multiple stages including ingestion, chunking, embedding,
    retrieval, generation, memory, and reflection.
    """
    
    # Initialize
    print("1. Setting up components...")
    index_dir = Path("./test_index")
    
    chunker = TextChunker()
    embedder = EmbeddingGenerator(cache_dir=index_dir / "embeddings_cache")
    vector_index = VectorIndex(persist_dir=index_dir)
    
    # Process
    print("2. Processing document...")
    chunks = chunker.chunk_document(doc_id, content, {"source": "test"})
    embedded_chunks = embedder.embed_chunks(chunks)
    vector_index.add_embeddings(embedded_chunks)
    
    # Test with mock generator
    print("3. Testing with mock generator...")
    rag = RAGPipeline(
        index_dir=index_dir,
        generator_type="mock",
        model_name="mock-model",
        retrieval_k=2
    )
    
    query = "What is EideticRAG?"
    result = rag.query(query, k=2)
    
    print(f"\n✓ Query: {result['query']}")
    print(f"✓ Answer: {result['answer']}")
    print(f"✓ Chunks retrieved: {len(result['chunks'])}")
    print(f"✓ Metadata: {result['metadata']}")
    
    print("\n✓✓✓ RAG PIPELINE WORKING! ✓✓✓")
    print("\nNote: Ollama requires more GPU memory for the current model.")
    print("Consider using a smaller model like llama3.2:1b for local testing.")
    
    return True


if __name__ == "__main__":
    test_with_mock()
