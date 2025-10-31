# Generation module initialization

import importlib

from . import generator as _generator

GenerationResult = _generator.GenerationResult
LLMGenerator = _generator.LLMGenerator

try:
    _spg = importlib.import_module(
        ".spiking_brain_generator",
        __package__,
    )

    SpikingBrainGenerator = getattr(_spg, "SpikingBrainGenerator")
    SpikingBrainResult = getattr(_spg, "SpikingBrainResult")
except ModuleNotFoundError:
    class SpikingBrainResult:  # type: ignore[no-redef]
        """Placeholder when spiking brain extras are unavailable."""

        ...

    class SpikingBrainGenerator:  # type: ignore[no-redef]
        """Stub raising when SpikingBrain optional deps are missing."""

        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            raise RuntimeError(
                "SpikingBrain generator requires optional dependencies "
                "such as modelscope and vllm."
            )
from .rag_pipeline import RAGPipeline

__all__ = [
    'LLMGenerator',
    'GenerationResult',
    'SpikingBrainGenerator',
    'SpikingBrainResult',
    'RAGPipeline'
]
