"""
Generation service for LLM operations
"""

from typing import Optional
from pathlib import Path
import sys
import asyncio

# Add parent to path to import core modules
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from generation.generator import LLMGenerator
except ImportError:
    LLMGenerator = None


class GenerationService:
    """Service for text generation using LLMs"""

    def __init__(self, model_type: str = "mock", model_name: str = "gpt-3.5-turbo",
                 api_key: Optional[str] = None, temperature: float = 0.7):
        self.model_type = model_type
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.generator = None

    async def initialize(self) -> None:
        """Initialize the generation service"""
        if LLMGenerator:
            self.generator = LLMGenerator(
                model_type=self.model_type,
                model_name=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature
            )
        else:
            print("Warning: LLMGenerator not available")

    async def generate(self, prompt: str, max_tokens: int = 500, 
                      temperature: float = None, **kwargs) -> str:
        """Generate text using the LLM"""
        if not self.generator:
            # Fallback response if generator not available
            return f"Mock response: The system is processing your query. Please ensure Ollama is running or configure a different LLM backend."

        # Parse prompt to extract query and context
        import re
        parts = prompt.split('\n\nContext:\n')
        if len(parts) >= 2:
            query = parts[0].replace('Query: ', '').strip()
            context_text = parts[1]
        else:
            query = prompt
            context_text = ""

        # Build chunks from context
        mock_chunks = []
        if context_text:
            # Extract chunks - handle both local and web results
            chunk_matches = re.findall(
                r'\[(Chunk|Web Result) (\d+)\](.*?)(?=\[(?:Chunk|Web Result) \d+\]|\Z)', 
                context_text, 
                re.DOTALL
            )
            for chunk_type, idx, chunk_text in chunk_matches:
                mock_chunks.append({
                    'chunk_id': f'{chunk_type.lower().replace(" ", "_")}_{idx}',
                    'text': chunk_text.strip(),
                    'score': 0.9 - (int(idx) * 0.05),
                    'metadata': {'source': 'web' if 'Web' in chunk_type else 'local'}
                })

        # Generate using LLMGenerator
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.generator.generate, query, mock_chunks
            )
            # Return the answer from the result
            return result.answer if hasattr(result, 'answer') else str(result)
        except Exception as e:
            print(f"Generation error: {e}")
            return f"I apologize, but I encountered an error generating a response. Please check that your LLM backend (Ollama) is running. Error: {str(e)}"

    async def cleanup(self) -> None:
        """Cleanup resources"""
        self.generator = None
