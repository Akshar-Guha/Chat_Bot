"""
Generation service for LLM operations
"""

from typing import Optional
from pathlib import Path
import sys

# Add parent to path to import core modules
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from generation.generator import Generator
except ImportError:
    Generator = None


class GenerationService:
    """Service for text generation using LLMs"""

    def __init__(self, model_type: str = "mock", model_name: str = "gpt-3.5-turbo",
                 api_key: Optional[str] = None, temperature: float = 0.7):
        self.model_type = model_type
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.generator: Generator = None

    async def initialize(self) -> None:
        """Initialize the generation service"""
        if Generator:
            self.generator = Generator(
                model_type=self.model_type,
                model_name=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature
            )
        else:
            print("Warning: Generator not available")

    async def generate(self, prompt: str, context: str = "", **kwargs) -> str:
        """Generate text using the LLM"""
        if not self.generator:
            # Fallback response if generator not available
            return f"Mock response for prompt: {prompt[:100]}..."

        # For now, use the prompt directly since the Generator expects query + chunks
        # In a full implementation, we'd extract query and context and convert to chunks format
        mock_query = prompt.split('\n\n')[0].replace('Query: ', '') if 'Query: ' in prompt else prompt
        mock_chunks = []

        # Extract chunks from context if available
        if context:
            import re
            # Simple parsing - in real implementation this would be more sophisticated
            chunk_matches = re.findall(r'\[Chunk \d+\]\s*(.*?)(?=\[Chunk \d+\]|\Z)', context, re.DOTALL)
            for i, chunk_text in enumerate(chunk_matches):
                mock_chunks.append({
                    'chunk_id': f'chunk_{i}',
                    'text': chunk_text.strip(),
                    'score': 0.9 - (i * 0.1),  # Decreasing scores
                    'metadata': {'doc_id': 'mock_doc', 'chunk_index': i}
                })

        result = await asyncio.get_event_loop().run_in_executor(
            None, self.generator.generate, mock_query, mock_chunks
        )

        # Return the answer from the result
        return result.answer if hasattr(result, 'answer') else str(result)

    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.generator = None
