"""
SpikingBrain Generator - Brain-inspired LLM generation using SpikingBrain-7B
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import os
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig
from modelscope import snapshot_download
import logging

logger = logging.getLogger(__name__)


@dataclass
class SpikingBrainResult:
    """Result from SpikingBrain generation"""
    answer: str
    prompt: str
    model: str
    chunks_used: List[Dict]
    provenance: List[Dict]
    metadata: Dict
    spike_info: Dict  # Information about spiking behavior


class SpikingBrainGenerator:
    """Generates answers using SpikingBrain-7B brain-inspired model"""

    def __init__(
        self,
        model_type: str = "huggingface",  # "huggingface" or "vllm"
        model_name: str = "Panyuqi/V1-7B-sft-s3-reasoning",  # Chat model
        device: str = "auto",
        max_length: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
        do_sample: bool = True,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize SpikingBrain generator

        Args:
            model_type: "huggingface" or "vllm" inference
            model_name: Model name on ModelScope or HuggingFace
            device: Device to run on ("auto", "cpu", "cuda")
            max_length: Maximum sequence length
            temperature: Generation temperature (0.0 to 2.0)
            top_p: Nucleus sampling parameter
            repetition_penalty: Repetition penalty (1.0 to 2.0)
            do_sample: Whether to use sampling
            cache_dir: Directory to cache models
        """
        self.model_type = model_type
        self.model_name = model_name
        self.device = device
        self.max_length = max_length
        self.temperature = temperature
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty
        self.do_sample = do_sample
        self.cache_dir = cache_dir or os.path.expanduser(
            "~/.cache/spikingbrain"
        )

        # Model components
        self.tokenizer = None
        self.model = None
        self.config = None

        # Initialize the model
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the SpikingBrain model and tokenizer"""
        try:
            logger.info(f"Initializing SpikingBrain model: {self.model_name}")

            # Create cache directory
            os.makedirs(self.cache_dir, exist_ok=True)

            # Download model if not present
            if not self._model_exists():
                logger.info(f"Downloading model {self.model_name}...")
                self._download_model()

            # Load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )

            # Load model
            logger.info("Loading model...")
            if self.model_type == "huggingface":
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    cache_dir=self.cache_dir,
                    torch_dtype=(
                        torch.float16 if torch.cuda.is_available()
                        else torch.float32
                    ),
                    device_map=self.device,
                    trust_remote_code=True
                )
            else:  # vllm - we'll handle this differently
                logger.warning(
                    "vLLM integration not yet implemented, using HuggingFace"
                )
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    cache_dir=self.cache_dir,
                    torch_dtype=(
                        torch.float16 if torch.cuda.is_available()
                        else torch.float32
                    ),
                    device_map=self.device,
                    trust_remote_code=True
                )

            # Load config
            self.config = AutoConfig.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )

            # Clean up auto_map if present (as mentioned in docs)
            if hasattr(self.config, 'auto_map'):
                delattr(self.config, 'auto_map')

            logger.info("✓ SpikingBrain model initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize SpikingBrain model: {e}")
            raise

    def _model_exists(self) -> bool:
        """Check if model already exists locally"""
        try:
            model_path = Path(self.cache_dir) / self.model_name.replace("/", "--")
            return model_path.exists()
        except Exception:
            return False

    def _download_model(self):
        """Download model from ModelScope"""
        try:
            snapshot_download(
                self.model_name,
                cache_dir=self.cache_dir,
                revision='master'
            )
        except Exception as e:
            logger.warning(
                f"ModelScope download failed: {e}, trying HuggingFace..."
            )
            # Fallback to HuggingFace if ModelScope fails
            pass

    def generate(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        system_prompt: Optional[str] = None
    ) -> SpikingBrainResult:
        """
        Generate answer using retrieved context with SpikingBrain

        Args:
            query: User query
            retrieved_chunks: List of retrieved chunks with scores
            system_prompt: Optional system prompt override

        Returns:
            SpikingBrainResult with answer and metadata
        """
        # Build context from retrieved chunks
        context = self._build_context(retrieved_chunks)

        # Build prompt with chat template
        prompt = self._build_prompt(query, context, system_prompt)

        # Generate answer
        answer, spike_info = self._generate_answer(prompt)

        # Extract provenance
        provenance = self._extract_provenance(answer, retrieved_chunks)

        return SpikingBrainResult(
            answer=answer,
            prompt=prompt,
            model=f"SpikingBrain-7B/{self.model_name}",
            chunks_used=retrieved_chunks,
            provenance=provenance,
            metadata={
                'temperature': self.temperature,
                'max_length': self.max_length,
                'top_p': self.top_p,
                'repetition_penalty': self.repetition_penalty,
                'do_sample': self.do_sample,
                'num_chunks': len(retrieved_chunks),
                'model_type': self.model_type,
                'device': str(self.model.device) if self.model else 'unknown'
            },
            spike_info=spike_info
        )

    def _build_context(self, retrieved_chunks: List[Dict]) -> str:
        """Build context string from retrieved chunks"""
        context_parts = []

        for i, chunk in enumerate(retrieved_chunks, 1):
            chunk_text = chunk.get('text', '')
            chunk_id = chunk.get('chunk_id', '')[:8]
            score = chunk.get('score', 0.0)

            context_parts.append(
                f"[Source {i} | ID: {chunk_id} | Relevance: {score:.3f}]\n"
                f"{chunk_text}\n"
            )

        return "\n".join(context_parts)

    def _build_prompt(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Build the complete prompt with chat template"""
        if not system_prompt:
            system_prompt = (
                "You are an intelligent AI assistant with brain-inspired "
                "spiking neural networks.\n"
                "You provide accurate, helpful answers based on the given "
                "context. Always cite your sources using [Source N] notation.\n"
                "If the context doesn't contain enough information, clearly "
                "state so. Be concise and precise in your responses."
            )

        # Use chat template if available
        if self.tokenizer and self.tokenizer.chat_template:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": (
                    f"Context:\n{context}\n\nQuestion: {query}\n\n"
                    "Please provide a clear, accurate answer based on the "
                    "context above."
                )}
            ]

            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            # Fallback to simple format
            prompt = (
                f"{system_prompt}\n\nContext:\n{context}\n\n"
                f"Question: {query}\n\nAnswer:"
            )

        return prompt

    def _generate_answer(self, prompt: str) -> tuple[str, Dict]:
        """Generate answer using SpikingBrain model"""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not initialized")

        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=self.max_length - 512  # Leave room for generation
            )

            # Move to device
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=self.max_length,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    repetition_penalty=self.repetition_penalty,
                    do_sample=self.do_sample,
                    pad_token_id=self.tokenizer.eos_token_id,
                    num_return_sequences=1
                )

            # Decode output
            generated_text = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )

            # Extract spike information (mock for now - would need model introspection)
            spike_info = {
                'sparsity_ratio': 0.69,  # From SpikingBrain paper
                'energy_efficiency': '100x',  # From SpikingBrain paper
                'brain_inspired_features': [
                    'hybrid_attention',
                    'moe_modules',
                    'spike_encoding'
                ]
            }

            return generated_text, spike_info

        except Exception as e:
            logger.error(f"SpikingBrain generation error: {e}")
            # Fallback to simple response
            return self._generate_fallback(query), {'error': str(e)}

    def _generate_fallback(self, query: str) -> str:
        """Fallback generation when model fails"""
        return (
            "I apologize, but I encountered an error while processing "
            f"your query: '{query}'. Please try again or contact support "
            "if the problem persists."
        )

    def _extract_provenance(
        self,
        answer: str,
        retrieved_chunks: List[Dict]
    ) -> List[Dict]:
        """Extract provenance information from answer"""
        provenance = []

        # Simple extraction based on [Source N] citations
        import re
        citations = re.findall(r'\[Source (\d+)\]', answer)

        for citation in citations:
            idx = int(citation) - 1
            if 0 <= idx < len(retrieved_chunks):
                chunk = retrieved_chunks[idx]
                provenance.append({
                    'chunk_id': chunk.get('chunk_id'),
                    'doc_id': chunk.get('metadata', {}).get('doc_id'),
                    'score': chunk.get('score'),
                    'text_snippet': chunk.get('text', '')[:100]
                })

        # If no citations found, assume top chunk was used
        if not provenance and retrieved_chunks:
            top_chunk = retrieved_chunks[0]
            provenance.append({
                'chunk_id': top_chunk.get('chunk_id'),
                'doc_id': top_chunk.get('metadata', {}).get('doc_id'),
                'score': top_chunk.get('score'),
                'text_snippet': top_chunk.get('text', '')[:100]
            })

        return provenance

    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        if not self.model or not self.config:
            return {'status': 'not_initialized'}

        return {
            'model_name': self.model_name,
            'model_type': self.model_type,
            'device': str(self.model.device) if self.model else 'unknown',
            'dtype': str(self.model.dtype) if self.model else 'unknown',
            'config': {
                'max_position_embeddings': getattr(
                    self.config, 'max_position_embeddings', 'unknown'
                ),
                'hidden_size': getattr(self.config, 'hidden_size', 'unknown'),
                'num_attention_heads': getattr(
                    self.config, 'num_attention_heads', 'unknown'
                ),
                'num_hidden_layers': getattr(
                    self.config, 'num_hidden_layers', 'unknown'
                ),
            }
        }
