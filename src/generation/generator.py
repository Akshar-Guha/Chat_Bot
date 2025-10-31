from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from time import monotonic
from typing import Dict, List, Optional

import requests
from langchain_community.llms import Ollama


logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Standardised response from an LLM call."""

    answer: str
    prompt: str
    model: str
    provenance: List[Dict]
    metadata: Dict


class LLMGenerator:
    """LLM interface supporting local Ollama and hosted endpoints."""

    def __init__(
        self,
        model_type: str = "ollama",
        model_name: str = "llama2",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 512,
        timeout: int = 60,
    ) -> None:
        self.model_type = model_type.lower()
        self.model_name = model_name
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.timeout = timeout

        self._session = requests.Session()

        self._ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self._ollama_generate_url = f"{self._ollama_host.rstrip('/')}/api/generate"

        logger.info(
            "LLMGenerator initialised",
            extra={
                "model_type": self.model_type,
                "model_name": self.model_name,
                "api_base": self.api_base,
            },
        )

    def generate(self, query: str, retrieved_chunks: List[Dict]) -> GenerationResult:
        """Generate an answer using the configured backend."""

        context = self._build_context(retrieved_chunks)
        prompt = self._build_prompt(query, context)

        start_time = monotonic()

        if self.model_type == "ollama":
            answer = self._generate_with_ollama(prompt)
        elif self.model_type in {"huggingface", "huggingface_endpoint", "hf"}:
            answer = self._generate_with_huggingface(prompt)
        elif self.model_type == "mock":
            answer = self._generate_mock_response(query, retrieved_chunks)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

        latency_ms = int((monotonic() - start_time) * 1000)

        provenance = self._extract_provenance(answer, retrieved_chunks)
        metadata = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "latency_ms": latency_ms,
            "num_chunks": len(retrieved_chunks),
        }

        return GenerationResult(
            answer=answer,
            prompt=prompt,
            model=f"{self.model_type}:{self.model_name}",
            provenance=provenance,
            metadata=metadata,
        )

    def _generate_with_ollama(self, prompt: str) -> str:
        try:
            ollama = Ollama(
                base_url=self._ollama_host,
                model=self.model_name,
                temperature=self.temperature,
                top_p=self.top_p,
            )
            response = ollama.invoke(prompt)
            return response.strip()
        except Exception as exc:
            logger.exception("Ollama request failed")
            raise RuntimeError(
                "Failed to reach Ollama. Ensure the daemon is running."
            ) from exc

    def _generate_with_huggingface(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("Missing Hugging Face API key for online mode")
        if not self.api_base:
            raise RuntimeError("Missing Hugging Face endpoint URL for online mode")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "max_new_tokens": self.max_tokens,
                "return_full_text": False,
            },
        }

        try:
            response = self._session.post(
                self.api_base,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list) and data:
                item = data[0]
                if isinstance(item, dict) and "generated_text" in item:
                    return item["generated_text"].strip()
            if isinstance(data, dict):
                if "generated_text" in data:
                    return str(data["generated_text"]).strip()
                if "choices" in data and data["choices"]:
                    choice = data["choices"][0]
                    return str(choice.get("text", "")).strip()

            raise RuntimeError(f"Unexpected Hugging Face response: {data}")
        except requests.RequestException as exc:
            logger.exception("Hugging Face request failed")
            raise RuntimeError("Failed to call Hugging Face endpoint") from exc

    def _generate_mock_response(
        self, query: str, retrieved_chunks: List[Dict]
    ) -> str:
        context_hint = (
            retrieved_chunks[0].get("text", "")[:120]
            if retrieved_chunks
            else ""
        )
        return (
            "[Mock Response] Unable to reach an LLM backend right now. "
            f"Query: {query}\nContext snippet: {context_hint}"
        )

    def _build_context(self, retrieved_chunks: List[Dict]) -> str:
        parts = []
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            text = chunk.get("text", "")
            chunk_id = str(chunk.get("chunk_id", ""))[:8]
            score = chunk.get("score", 0.0)
            parts.append(
                f"[Source {idx} | ID: {chunk_id} | Relevance: {score:.3f}]\n{text}\n"
            )
        return "\n".join(parts)

    def _build_prompt(self, query: str, context: str) -> str:
        system_prompt = (
            "You are a helpful assistant. Use the provided context to answer "
            "the question. Cite sources using [Source N]. If the answer "
            "cannot be derived, say so clearly."
        )

        return (
            f"{system_prompt}\n\nContext:\n{context}\n\n"
            f"Question: {query}\n\nAnswer:"
        )

    def _extract_provenance(
        self, answer: str, retrieved_chunks: List[Dict]
    ) -> List[Dict]:
        provenance: List[Dict] = []

        citations = re.findall(r"\[Source (\d+)\]", answer)
        for citation in citations:
            index = int(citation) - 1
            if 0 <= index < len(retrieved_chunks):
                chunk = retrieved_chunks[index]
                provenance.append(
                    {
                        "chunk_id": chunk.get("chunk_id"),
                        "doc_id": chunk.get("metadata", {}).get("doc_id"),
                        "score": chunk.get("score"),
                        "text_snippet": chunk.get("text", "")[:100],
                    }
                )

        if not provenance and retrieved_chunks:
            chunk = retrieved_chunks[0]
            provenance.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "doc_id": chunk.get("metadata", {}).get("doc_id"),
                    "score": chunk.get("score"),
                    "text_snippet": chunk.get("text", "")[:100],
                }
            )

        return provenance
