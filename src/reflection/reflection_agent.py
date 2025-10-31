"""
Reflection Agent - Orchestrates verification and regeneration
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .verification_engine import VerificationEngine, AnswerVerification
from ..generation.generator import LLMGenerator
from ..retrieval.retrieval_controller import RetrievalController


class ReflectionAction(Enum):
    """Actions the reflection agent can take"""
    ACCEPT = "accept"           # Answer is good
    REGENERATE = "regenerate"   # Try generating again
    BROADEN = "broaden"        # Broaden retrieval and regenerate
    ESCALATE = "escalate"       # Use stronger model
    REFUSE = "refuse"           # Cannot provide good answer


@dataclass
class ReflectionDecision:
    """Decision made by reflection agent"""
    action: ReflectionAction
    confidence: float
    reasoning: str
    metadata: Dict


@dataclass
class ReflectionResult:
    """Result of reflection process"""
    original_answer: str
    final_answer: str
    verification: AnswerVerification
    decision: ReflectionDecision
    iterations: int
    success: bool
    metadata: Dict


class ReflectionAgent:
    """Agent that reflects on generated answers and improves them"""
    
    def __init__(
        self,
        verification_engine: Optional[VerificationEngine] = None,
        max_iterations: int = 3,
        hallucination_threshold: float = 0.3
    ):
        """
        Initialize reflection agent
        
        Args:
            verification_engine: Verification engine to use
            max_iterations: Maximum reflection iterations
            hallucination_threshold: Maximum acceptable hallucination score
        """
        self.verification_engine = verification_engine or VerificationEngine()
        self.max_iterations = max_iterations
        self.hallucination_threshold = hallucination_threshold
    
    def reflect_on_answer(
        self,
        answer: str,
        query: str,
        retrieved_chunks: List[Dict],
        generator: Optional[LLMGenerator] = None,
        retrieval_controller: Optional[RetrievalController] = None
    ) -> ReflectionResult:
        """
        Reflect on an answer and potentially improve it
        
        Args:
            answer: Generated answer
            query: Original query
            retrieved_chunks: Retrieved chunks used
            generator: Generator for regeneration
            retrieval_controller: Controller for retrieval adjustment
        
        Returns:
            ReflectionResult with final answer and metadata
        """
        original_answer = answer
        current_answer = answer
        current_chunks = retrieved_chunks
        iterations = 0
        
        # Track all decisions
        decisions = []
        
        while iterations < self.max_iterations:
            iterations += 1
            
            # Verify current answer
            verification = self.verification_engine.verify_answer(
                current_answer,
                current_chunks,
                query
            )
            
            # Make decision based on verification
            decision = self._make_decision(verification, iterations)
            decisions.append(decision)
            
            # Execute decision
            if decision.action == ReflectionAction.ACCEPT:
                # Answer is good enough
                return ReflectionResult(
                    original_answer=original_answer,
                    final_answer=current_answer,
                    verification=verification,
                    decision=decision,
                    iterations=iterations,
                    success=True,
                    metadata={
                        'decisions': decisions,
                        'chunks_used': len(current_chunks)
                    }
                )
            
            elif decision.action == ReflectionAction.REGENERATE:
                # Regenerate with same chunks
                if generator:
                    new_result = generator.generate(query, current_chunks)
                    current_answer = new_result.answer
                else:
                    # Can't regenerate without generator
                    break
            
            elif decision.action == ReflectionAction.BROADEN:
                # Broaden retrieval and regenerate
                if retrieval_controller and generator:
                    # Retrieve more chunks
                    new_retrieval = retrieval_controller.retrieve(
                        query,
                        override_k=len(current_chunks) * 2  # Double the chunks
                    )
                    current_chunks = new_retrieval['chunks']
                    
                    # Regenerate with new chunks
                    new_result = generator.generate(query, current_chunks)
                    current_answer = new_result.answer
                else:
                    break
            
            elif decision.action == ReflectionAction.ESCALATE:
                # Would use stronger model here
                # For now, just try one more time with current setup
                if generator:
                    # Increase temperature for diversity
                    original_temp = generator.temperature
                    generator.temperature = min(1.0, generator.temperature + 0.2)
                    
                    new_result = generator.generate(query, current_chunks)
                    current_answer = new_result.answer
                    
                    # Restore temperature
                    generator.temperature = original_temp
                else:
                    break
            
            elif decision.action == ReflectionAction.REFUSE:
                # Cannot provide good answer
                current_answer = self._generate_refusal(query, verification)
                
                return ReflectionResult(
                    original_answer=original_answer,
                    final_answer=current_answer,
                    verification=verification,
                    decision=decision,
                    iterations=iterations,
                    success=False,
                    metadata={
                        'decisions': decisions,
                        'reason': 'insufficient_sources'
                    }
                )
        
        # Max iterations reached
        final_verification = self.verification_engine.verify_answer(
            current_answer,
            current_chunks,
            query
        )
        
        return ReflectionResult(
            original_answer=original_answer,
            final_answer=current_answer,
            verification=final_verification,
            decision=decisions[-1] if decisions else None,
            iterations=iterations,
            success=final_verification.hallucination_score <= self.hallucination_threshold,
            metadata={
                'decisions': decisions,
                'max_iterations_reached': True
            }
        )
    
    def _make_decision(
        self,
        verification: AnswerVerification,
        iteration: int
    ) -> ReflectionDecision:
        """Make decision based on verification results"""
        
        hallucination_score = verification.hallucination_score
        support_ratio = verification.overall_support_ratio
        
        # If answer is well-supported, accept it
        if hallucination_score <= self.hallucination_threshold:
            return ReflectionDecision(
                action=ReflectionAction.ACCEPT,
                confidence=support_ratio,
                reasoning=f"Answer is well-supported ({support_ratio:.1%} of claims verified)",
                metadata={'hallucination_score': hallucination_score}
            )
        
        # On first iteration, try regenerating
        if iteration == 1:
            return ReflectionDecision(
                action=ReflectionAction.REGENERATE,
                confidence=0.5,
                reasoning=f"High hallucination score ({hallucination_score:.1%}), trying regeneration",
                metadata={'hallucination_score': hallucination_score}
            )
        
        # On second iteration, try broadening retrieval
        if iteration == 2:
            return ReflectionDecision(
                action=ReflectionAction.BROADEN,
                confidence=0.3,
                reasoning="Regeneration didn't help, broadening retrieval",
                metadata={'hallucination_score': hallucination_score}
            )
        
        # On third iteration, check if it's hopeless
        if support_ratio < 0.2:
            return ReflectionDecision(
                action=ReflectionAction.REFUSE,
                confidence=0.1,
                reasoning="Insufficient source support for query",
                metadata={'support_ratio': support_ratio}
            )
        
        # Last resort: escalate
        return ReflectionDecision(
            action=ReflectionAction.ESCALATE,
            confidence=0.2,
            reasoning="Attempting with adjusted parameters",
            metadata={'iteration': iteration}
        )
    
    def _generate_refusal(
        self,
        query: str,
        verification: AnswerVerification
    ) -> str:
        """Generate a refusal message"""
        unsupported_count = len(verification.unsupported_claims)
        total_claims = len(verification.claims)
        
        return (
            f"I cannot provide a reliable answer to your query: '{query}'. "
            f"Based on the available sources, I found that {unsupported_count} out of "
            f"{total_claims} potential claims could not be verified. "
            "Please provide more specific information or rephrase your query."
        )
    
    def annotate_answer(
        self,
        verification: AnswerVerification
    ) -> str:
        """
        Annotate answer with verification results
        
        Args:
            verification: Verification results
        
        Returns:
            Annotated answer with unsupported claims highlighted
        """
        annotated = verification.answer_text
        
        # Sort unsupported claims by position (reverse order for replacement)
        unsupported = sorted(
            verification.unsupported_claims,
            key=lambda c: c.start_pos,
            reverse=True
        )
        
        for claim in unsupported:
            if claim.start_pos >= 0 and claim.end_pos >= 0:
                # Add annotation
                original = annotated[claim.start_pos:claim.end_pos]
                annotated_text = f"[UNSUPPORTED: {original}]"
                
                annotated = (
                    annotated[:claim.start_pos] +
                    annotated_text +
                    annotated[claim.end_pos:]
                )
        
        # Add summary at the end
        support_percentage = verification.overall_support_ratio * 100
        summary = f"\n\n[Verification: {support_percentage:.0f}% of claims supported by sources]"
        annotated += summary
        
        return annotated
    
    def explain_decision(
        self,
        reflection_result: ReflectionResult
    ) -> str:
        """
        Generate human-readable explanation of reflection process
        
        Args:
            reflection_result: Result of reflection
        
        Returns:
            Explanation text
        """
        lines = []
        
        # Summary
        if reflection_result.success:
            lines.append(f"✓ Answer verified after {reflection_result.iterations} iteration(s)")
        else:
            lines.append(f"⚠ Answer could not be fully verified after {reflection_result.iterations} iteration(s)")
        
        # Verification stats
        ver = reflection_result.verification
        lines.append(
            f"• Support ratio: {ver.overall_support_ratio:.1%} "
            f"({ver.metadata['supported_claims']}/{ver.metadata['total_claims']} claims)"
        )
        lines.append(f"• Hallucination score: {ver.hallucination_score:.1%}")
        
        # Decision trail
        if 'decisions' in reflection_result.metadata:
            lines.append("\nDecision trail:")
            for i, decision in enumerate(reflection_result.metadata['decisions'], 1):
                lines.append(f"  {i}. {decision.action.value}: {decision.reasoning}")
        
        # Unsupported claims if any
        if ver.unsupported_claims:
            lines.append("\nUnsupported claims:")
            for claim in ver.unsupported_claims[:3]:  # Show max 3
                lines.append(f"  • {claim.text[:100]}...")
        
        return "\n".join(lines)
