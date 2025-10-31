#!/usr/bin/env python3
"""
Test SpikingBrain initialization
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment variables
os.environ['RAG_GENERATOR_TYPE'] = 'spikingbrain'
os.environ['RAG_MODEL_NAME'] = 'Panyuqi/V1-7B-sft-s3-reasoning'
os.environ['RAG_DEVICE'] = 'cpu'  # Use CPU for testing
os.environ['RAG_CACHE_DIR'] = os.path.expanduser('~/.cache/spikingbrain')

try:
    print("Testing SpikingBrain initialization...")
    from generation.spiking_brain_generator import SpikingBrainGenerator

    print("Creating SpikingBrain generator...")
    generator = SpikingBrainGenerator(
        model_type="huggingface",
        model_name="Panyuqi/V1-7B-sft-s3-reasoning",
        device="cpu",
        max_length=512,  # Smaller for testing
        cache_dir=os.environ['RAG_CACHE_DIR']
    )

    print("✓ SpikingBrain generator created successfully!")
    print(f"Model info: {generator.get_model_info()}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
