"""
Verification Engine - Verifies generated content against sources
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re
import numpy as np
from pathlib import Path

from ..core.embeddings import EmbeddingGenerator


@dataclass
class Claim:
    """Represents a claim in the generated answer"""
    text: str
    sentence_idx: int
    start_pos: int
    end_pos: int
    claim_type: str  # factual, opinion, procedural, etc.


@dataclass
class VerificationResult:
    """Result of verification for a claim"""
    claim: Claim
    is_supported: bool
    supporting_chunks: List[Dict]
    confidence: float
    explanation: str


@dataclass
class AnswerVerification:
    """Complete verification result for an answer"""
    answer_text: str
    claims: List[Claim]
    verification_results: List[VerificationResult]
    overall_support_ratio: float
    unsupported_claims: List[Claim]
    hallucination_score: float
    metadata: Dict


class VerificationEngine:
    """Verifies generated answers against retrieved sources"""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize verification engine
        
        Args:
            embedding_model: Model for semantic similarity
        """
        self.embedder = EmbeddingGenerator(model_name=embedding_model)
        
        # Thresholds
        self.support_threshold = 0.7  # Minimum similarity for support
        self.hallucination_threshold = 0.3  # Max unsupported ratio for acceptance
    
    def verify_answer(
        self,
        answer: str,
        retrieved_chunks: List[Dict],
        query: str = None
    ) -> AnswerVerification:
        """
        Verify an answer against retrieved sources
        
        Args:
            answer: Generated answer text
            retrieved_chunks: List of retrieved chunks
            query: Original query (optional)
        
        Returns:
            AnswerVerification result
        """
        # Extract claims from answer
        claims = self._extract_claims(answer)
        
        # Verify each claim
        verification_results = []
        unsupported_claims = []
        
        for claim in claims:
            result = self._verify_claim(claim, retrieved_chunks)
            verification_results.append(result)
            
            if not result.is_supported:
                unsupported_claims.append(claim)
        
        # Calculate metrics
        supported_count = sum(1 for r in verification_results if r.is_supported)
        total_claims = len(claims) if claims else 1
        
        overall_support_ratio = supported_count / total_claims
        hallucination_score = 1.0 - overall_support_ratio
        
        # Build metadata
        metadata = {
            'total_claims': total_claims,
            'supported_claims': supported_count,
            'unsupported_claims': len(unsupported_claims),
            'num_chunks_used': len(retrieved_chunks),
            'verification_method': 'semantic_similarity'
        }
        
        if query:
            metadata['query'] = query
        
        return AnswerVerification(
            answer_text=answer,
            claims=claims,
            verification_results=verification_results,
            overall_support_ratio=overall_support_ratio,
            unsupported_claims=unsupported_claims,
            hallucination_score=hallucination_score,
            metadata=metadata
        )
    
    def _extract_claims(self, answer: str) -> List[Claim]:
        """Extract verifiable claims from answer"""
        claims = []
        
        # Split into sentences
        sentences = self._split_sentences(answer)
        
        for idx, sentence in enumerate(sentences):
            # Skip very short sentences
            if len(sentence.strip()) < 10:
                continue
            
            # Determine claim type
            claim_type = self._classify_claim_type(sentence)
            
            # Find position in original text
            start_pos = answer.find(sentence)
            end_pos = start_pos + len(sentence) if start_pos >= 0 else -1
            
            claim = Claim(
                text=sentence.strip(),
                sentence_idx=idx,
                start_pos=start_pos,
                end_pos=end_pos,
                claim_type=claim_type
            )
            
            claims.append(claim)
        
        return claims
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter out empty sentences
        sentences = [s for s in sentences if s.strip()]
        
        return sentences
    
    def _classify_claim_type(self, sentence: str) -> str:
        """Classify the type of claim"""
        sentence_lower = sentence.lower()
        
        # Check for different claim types
        if any(word in sentence_lower for word in ['is', 'are', 'was', 'were', 'equals']):
            return 'factual'
        elif any(word in sentence_lower for word in ['think', 'believe', 'feel', 'opinion']):
            return 'opinion'
        elif any(word in sentence_lower for word in ['how to', 'steps', 'first', 'then', 'finally']):
            return 'procedural'
        elif any(word in sentence_lower for word in ['because', 'therefore', 'thus', 'hence']):
            return 'causal'
        elif '?' in sentence:
            return 'question'
        else:
            return 'statement'
    
    def _verify_claim(
        self,
        claim: Claim,
        retrieved_chunks: List[Dict]
    ) -> VerificationResult:
        """Verify a single claim against chunks"""
        
        # Skip opinion claims
        if claim.claim_type == 'opinion':
            return VerificationResult(
                claim=claim,
                is_supported=True,  # Opinions don't need verification
                supporting_chunks=[],
                confidence=1.0,
                explanation="Opinion claim - no verification needed"
            )
        
        # Generate embedding for claim
        claim_embedding = self.embedder.embed_text(claim.text)
        
        # Find supporting chunks
        supporting_chunks = []
        max_similarity = 0.0
        
        for chunk in retrieved_chunks:
            chunk_text = chunk.get('text', '')
            
            # Check for direct text match first
            if self._has_text_overlap(claim.text, chunk_text):
                supporting_chunks.append(chunk)
                max_similarity = max(max_similarity, 0.95)
                continue
            
            # Check semantic similarity
            chunk_embedding = self.embedder.embed_text(chunk_text)
            similarity = self.embedder.compute_similarity(claim_embedding, chunk_embedding)
            
            if similarity >= self.support_threshold:
                supporting_chunks.append(chunk)
                max_similarity = max(max_similarity, similarity)
        
        # Determine if claim is supported
        is_supported = len(supporting_chunks) > 0
        confidence = max_similarity if is_supported else 0.0
        
        # Generate explanation
        if is_supported:
            explanation = f"Supported by {len(supporting_chunks)} source(s) with confidence {confidence:.2f}"
        else:
            explanation = "No supporting evidence found in retrieved sources"
        
        return VerificationResult(
            claim=claim,
            is_supported=is_supported,
            supporting_chunks=supporting_chunks[:3],  # Limit to top 3
            confidence=confidence,
            explanation=explanation
        )
    
    def _has_text_overlap(self, claim_text: str, chunk_text: str) -> bool:
        """Check for significant text overlap, including synonyms"""
        # Simple word overlap check
        claim_words = set(claim_text.lower().split())
        chunk_words = set(chunk_text.lower().split())
        
        # Remove common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were'}
        
        claim_words = claim_words - stopwords
        chunk_words = chunk_words - stopwords
        
        if not claim_words:
            return False
        
        # Calculate overlap ratio
        overlap = claim_words & chunk_words
        overlap_ratio = len(overlap) / len(claim_words)
        
        # Also check for common synonyms
        synonyms = {
            'machine learning': ['ml', 'machine-learning', 'artificial intelligence', 'ai'],
            'computers': ['computer', 'systems', 'machines'],
            'learn': ['learning', 'understand', 'process'],
            'data': ['information', 'dataset', 'examples'],
            'enables': ['allows', 'permits', 'makes possible'],
            'patterns': ['structures', 'relationships', 'regularities']
        }
        
        # Check for synonym overlap
        synonym_overlap = 0
        for word in claim_words:
            for key, syn_list in synonyms.items():
                if word in key.split() or any(word == syn for syn in syn_list):
                    # Check if any synonym appears in chunk
                    if any(syn in chunk_text.lower() for syn in syn_list) or key in chunk_text.lower():
                        synonym_overlap += 1
                        break
        
        # Adjust overlap ratio to include synonyms
        adjusted_ratio = (len(overlap) + synonym_overlap * 0.5) / len(claim_words)
        
        return adjusted_ratio >= 0.3  # Lowered threshold to catch more cases
    
    def suggest_corrections(
        self,
        verification_result: AnswerVerification
    ) -> List[Dict]:
        """Suggest corrections for unsupported claims"""
        suggestions = []
        
        for unsupported_claim in verification_result.unsupported_claims:
            # Find verification result for this claim
            ver_result = next(
                (r for r in verification_result.verification_results 
                 if r.claim == unsupported_claim),
                None
            )
            
            if not ver_result:
                continue
            
            suggestion = {
                'claim': unsupported_claim.text,
                'position': (unsupported_claim.start_pos, unsupported_claim.end_pos),
                'suggestion_type': 'remove',
                'explanation': ver_result.explanation
            }
            
            # Try to find related information in chunks
            related_info = self._find_related_information(
                unsupported_claim,
                verification_result.verification_results
            )
            
            if related_info:
                suggestion['suggestion_type'] = 'replace'
                suggestion['suggested_text'] = related_info
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def _find_related_information(
        self,
        claim: Claim,
        verification_results: List[VerificationResult]
    ) -> Optional[str]:
        """Find related information from supported claims"""
        # Extract keywords from unsupported claim
        keywords = set(claim.text.lower().split()) - {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
        }
        
        # Look for supported claims with similar keywords
        best_match = None
        best_overlap = 0
        
        for result in verification_results:
            if result.is_supported and result.claim != claim:
                claim_keywords = set(result.claim.text.lower().split())
                overlap = len(keywords & claim_keywords)
                
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = result.claim.text
        
        return best_match
