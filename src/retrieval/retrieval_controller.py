"""
Retrieval Controller - Manages adaptive retrieval based on intent
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
import numpy as np

from .intent_classifier import IntentClassifier, QueryIntent
from ..core.embeddings import EmbeddingGenerator
from ..core.vector_index import VectorIndex


@dataclass
class RetrievalPolicy:
    """Retrieval policy configuration"""
    k: int                        # Number of chunks to retrieve
    depth: int                    # Search depth (for multi-hop)
    multi_hop: bool              # Enable multi-hop retrieval
    rerank: bool                 # Enable reranking
    diversity_factor: float      # Diversity vs relevance trade-off
    min_score_threshold: float   # Minimum similarity score
    expand_query: bool           # Query expansion
    metadata: Dict


class RetrievalController:
    """Controls retrieval behavior based on query intent"""
    
    def __init__(
        self,
        index_dir: Path,
        default_k: int = 5
    ):
        """
        Initialize retrieval controller
        
        Args:
            index_dir: Directory containing vector index
            default_k: Default number of chunks to retrieve
        """
        self.index_dir = Path(index_dir)
        self.default_k = default_k
        
        # Initialize components
        self.intent_classifier = IntentClassifier()
        self.embedder = EmbeddingGenerator(
            cache_dir=self.index_dir / 'embeddings_cache'
        )
        self.index = VectorIndex(persist_dir=self.index_dir)
        
        # Define retrieval policies per intent
        self.policies = {
            QueryIntent.FACTUAL: RetrievalPolicy(
                k=3,
                depth=1,
                multi_hop=False,
                rerank=True,
                diversity_factor=0.1,
                min_score_threshold=0.7,
                expand_query=False,
                metadata={'strategy': 'precise'}
            ),
            QueryIntent.COMPARATIVE: RetrievalPolicy(
                k=8,
                depth=2,
                multi_hop=True,
                rerank=True,
                diversity_factor=0.5,
                min_score_threshold=0.5,
                expand_query=True,
                metadata={'strategy': 'broad'}
            ),
            QueryIntent.CAUSAL: RetrievalPolicy(
                k=6,
                depth=2,
                multi_hop=True,
                rerank=True,
                diversity_factor=0.3,
                min_score_threshold=0.6,
                expand_query=True,
                metadata={'strategy': 'chain'}
            ),
            QueryIntent.DEFINITIONAL: RetrievalPolicy(
                k=4,
                depth=1,
                multi_hop=False,
                rerank=True,
                diversity_factor=0.2,
                min_score_threshold=0.65,
                expand_query=False,
                metadata={'strategy': 'focused'}
            ),
            QueryIntent.PROCEDURAL: RetrievalPolicy(
                k=7,
                depth=1,
                multi_hop=False,
                rerank=True,
                diversity_factor=0.2,
                min_score_threshold=0.6,
                expand_query=False,
                metadata={'strategy': 'sequential'}
            ),
            QueryIntent.CODE: RetrievalPolicy(
                k=5,
                depth=1,
                multi_hop=False,
                rerank=True,
                diversity_factor=0.1,
                min_score_threshold=0.7,
                expand_query=False,
                metadata={'strategy': 'technical'}
            ),
            QueryIntent.EXPLORATORY: RetrievalPolicy(
                k=10,
                depth=2,
                multi_hop=True,
                rerank=False,
                diversity_factor=0.6,
                min_score_threshold=0.4,
                expand_query=True,
                metadata={'strategy': 'exploratory'}
            ),
            QueryIntent.UNKNOWN: RetrievalPolicy(
                k=5,
                depth=1,
                multi_hop=False,
                rerank=False,
                diversity_factor=0.3,
                min_score_threshold=0.5,
                expand_query=False,
                metadata={'strategy': 'default'}
            )
        }
    
    def retrieve(
        self,
        query: str,
        override_k: Optional[int] = None,
        override_policy: Optional[RetrievalPolicy] = None
    ) -> Dict:
        """
        Retrieve chunks based on query intent
        
        Args:
            query: User query
            override_k: Override number of chunks
            override_policy: Override retrieval policy
        
        Returns:
            Dictionary with retrieval results and metadata
        """
        # Classify intent
        intent_result = self.intent_classifier.classify(query)
        
        # Get retrieval policy
        if override_policy:
            policy = override_policy
        else:
            policy = self.policies.get(
                intent_result.primary_intent,
                self.policies[QueryIntent.UNKNOWN]
            )
        
        # Apply override k if provided
        if override_k:
            policy.k = override_k
        
        # Expand query if needed
        if policy.expand_query:
            expanded_queries = self._expand_query(query, intent_result)
        else:
            expanded_queries = [query]
        
        # Retrieve chunks
        all_chunks = []
        for q in expanded_queries:
            chunks = self._retrieve_single(q, policy)
            all_chunks.extend(chunks)
        
        # Remove duplicates
        unique_chunks = self._deduplicate_chunks(all_chunks)
        
        # Apply diversity if needed
        if policy.diversity_factor > 0:
            diverse_chunks = self._diversify_results(
                unique_chunks,
                policy.k,
                policy.diversity_factor
            )
        else:
            diverse_chunks = unique_chunks[:policy.k]
        
        # Multi-hop retrieval if enabled
        if policy.multi_hop and policy.depth > 1:
            diverse_chunks = self._multi_hop_retrieval(
                query,
                diverse_chunks,
                policy
            )
        
        # Rerank if enabled
        if policy.rerank:
            diverse_chunks = self._rerank_chunks(
                query,
                diverse_chunks,
                intent_result
            )
        
        # Filter by score threshold
        filtered_chunks = [
            c for c in diverse_chunks
            if c.get('score', 0) >= policy.min_score_threshold
        ]
        
        # Return results
        return {
            'chunks': filtered_chunks[:policy.k],
            'intent': intent_result.primary_intent.value,
            'intent_confidence': intent_result.confidence,
            'policy': {
                'k': policy.k,
                'multi_hop': policy.multi_hop,
                'strategy': policy.metadata.get('strategy', 'default')
            },
            'metadata': {
                'num_chunks_retrieved': len(filtered_chunks),
                'query_expanded': policy.expand_query,
                'reranked': policy.rerank,
                'min_score': policy.min_score_threshold
            }
        }
    
    def _retrieve_single(
        self,
        query: str,
        policy: RetrievalPolicy
    ) -> List[Dict]:
        """Retrieve chunks for a single query"""
        # Generate embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Search index
        chunks = self.index.search(
            query_embedding=query_embedding,
            k=policy.k * 2  # Retrieve more for filtering
        )
        
        return chunks
    
    def _expand_query(
        self,
        query: str,
        intent_result
    ) -> List[str]:
        """Expand query based on intent"""
        expanded = [query]
        
        # Add variations based on intent
        if intent_result.primary_intent == QueryIntent.COMPARATIVE:
            # Add individual entity queries
            entities = self._extract_entities(query)
            for entity in entities:
                expanded.append(f"What is {entity}?")
        
        elif intent_result.primary_intent == QueryIntent.CAUSAL:
            # Add cause and effect queries
            expanded.append(query.replace("why", "what causes"))
            expanded.append(query.replace("why", "what is the result of"))
        
        elif intent_result.primary_intent == QueryIntent.EXPLORATORY:
            # Add specific aspect queries
            keywords = intent_result.keywords
            for keyword in keywords[:2]:
                expanded.append(f"{keyword} {query}")
        
        return expanded[:3]  # Limit expansion
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query (simple version)"""
        # Simple noun phrase extraction
        import re
        
        # Look for capitalized words (potential entities)
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        
        # Also look for quoted phrases
        quoted = re.findall(r'"([^"]+)"', query)
        entities.extend(quoted)
        
        return entities[:3]
    
    def _deduplicate_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Remove duplicate chunks"""
        seen_ids = set()
        unique = []
        
        for chunk in chunks:
            chunk_id = chunk.get('chunk_id')
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique.append(chunk)
        
        # Sort by score
        unique.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return unique
    
    def _diversify_results(
        self,
        chunks: List[Dict],
        k: int,
        diversity_factor: float
    ) -> List[Dict]:
        """Apply MMR (Maximal Marginal Relevance) for diversity"""
        if not chunks:
            return []
        
        # Start with highest scoring chunk
        selected = [chunks[0]]
        candidates = chunks[1:]
        
        while len(selected) < k and candidates:
            # Calculate MMR scores
            mmr_scores = []
            
            for candidate in candidates:
                # Relevance score
                relevance = candidate.get('score', 0)
                
                # Similarity to selected chunks (simple version using text overlap)
                max_sim = 0
                for sel in selected:
                    sim = self._text_similarity(
                        candidate.get('text', ''),
                        sel.get('text', '')
                    )
                    max_sim = max(max_sim, sim)
                
                # MMR score
                mmr = diversity_factor * relevance - (1 - diversity_factor) * max_sim
                mmr_scores.append(mmr)
            
            # Select chunk with highest MMR
            best_idx = np.argmax(mmr_scores)
            selected.append(candidates[best_idx])
            candidates.pop(best_idx)
        
        return selected
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity using word overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _multi_hop_retrieval(
        self,
        query: str,
        initial_chunks: List[Dict],
        policy: RetrievalPolicy
    ) -> List[Dict]:
        """Perform multi-hop retrieval"""
        all_chunks = initial_chunks.copy()
        
        # Extract key terms from initial chunks
        key_terms = []
        for chunk in initial_chunks[:3]:
            # Simple key term extraction
            text = chunk.get('text', '')
            # Extract capitalized words as potential entities
            entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            key_terms.extend(entities)
        
        # Retrieve additional chunks based on key terms
        for term in set(key_terms[:5]):
            term_chunks = self._retrieve_single(term, policy)
            all_chunks.extend(term_chunks[:2])
        
        # Deduplicate and return
        return self._deduplicate_chunks(all_chunks)
    
    def _rerank_chunks(
        self,
        query: str,
        chunks: List[Dict],
        intent_result
    ) -> List[Dict]:
        """Rerank chunks based on intent-specific criteria"""
        
        # Simple reranking based on keyword presence
        query_words = set(query.lower().split())
        
        for chunk in chunks:
            text = chunk.get('text', '').lower()
            text_words = set(text.split())
            
            # Calculate keyword overlap
            overlap = len(query_words & text_words) / len(query_words) if query_words else 0
            
            # Adjust score based on intent
            if intent_result.primary_intent == QueryIntent.FACTUAL:
                # Boost chunks with numbers/dates
                if re.search(r'\d+', text):
                    overlap *= 1.2
            elif intent_result.primary_intent == QueryIntent.COMPARATIVE:
                # Boost chunks mentioning multiple entities
                if text.count(' and ') > 1 or text.count(' vs ') > 0:
                    overlap *= 1.15
            
            # Update score
            original_score = chunk.get('score', 0)
            chunk['score'] = original_score * 0.7 + overlap * 0.3
        
        # Re-sort by new scores
        chunks.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return chunks
    
    def get_policy(self, intent: QueryIntent) -> RetrievalPolicy:
        """Get retrieval policy for an intent"""
        return self.policies.get(intent, self.policies[QueryIntent.UNKNOWN])
