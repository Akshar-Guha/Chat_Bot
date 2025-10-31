#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    print("Testing core imports...")
    from core.ingestor import DocumentIngestor
    print("✓ DocumentIngestor imported successfully")

    from core.chunker import TextChunker
    print("✓ TextChunker imported successfully")

    from core.embeddings import EmbeddingGenerator
    print("✓ EmbeddingGenerator imported successfully")

    from core.vector_index import VectorIndex
    print("✓ VectorIndex imported successfully")

    print("\nTesting generation imports...")
    from generation.rag_pipeline import RAGPipeline
    print("✓ RAGPipeline imported successfully")

    from generation.spiking_brain_generator import SpikingBrainGenerator
    print("✓ SpikingBrainGenerator imported successfully")

    print("\nAll imports successful!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
