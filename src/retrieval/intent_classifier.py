"""
Intent Classifier - Classifies query intent to optimize retrieval
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import re
from dataclasses import dataclass


class QueryIntent(Enum):
    """Query intent types"""
    FACTUAL = "factual"          # Direct facts, dates, names
    COMPARATIVE = "comparative"   # Comparing multiple entities
    CAUSAL = "causal"           # Why/how questions
    DEFINITIONAL = "definitional"  # What is X?
    PROCEDURAL = "procedural"    # How to do something
    CODE = "code"               # Programming related
    EXPLORATORY = "exploratory"  # Open-ended exploration
    UNKNOWN = "unknown"


@dataclass
class IntentClassification:
    """Intent classification result"""
    primary_intent: QueryIntent
    confidence: float
    secondary_intents: List[Tuple[QueryIntent, float]]
    keywords: List[str]
    metadata: Dict


class IntentClassifier:
    """Classifies user query intent"""
    
    def __init__(self):
        """Initialize intent classifier with patterns"""
        
        # Intent patterns
        self.patterns = {
            QueryIntent.FACTUAL: {
                'keywords': ['when', 'where', 'who', 'which', 'what year', 'how many', 'how much'],
                'patterns': [
                    r'when (was|did|will)',
                    r'where (is|was|are)',
                    r'who (is|was|are)',
                    r'what (year|date|time)',
                    r'how (many|much|long|far)'
                ]
            },
            QueryIntent.COMPARATIVE: {
                'keywords': ['compare', 'difference', 'versus', 'vs', 'better', 'worse', 'similar'],
                'patterns': [
                    r'(compare|comparison)',
                    r'(difference|differ) between',
                    r'versus|vs\.',
                    r'(better|worse) than',
                    r'(similar|different) (to|from)'
                ]
            },
            QueryIntent.CAUSAL: {
                'keywords': ['why', 'because', 'cause', 'reason', 'effect', 'result', 'lead to'],
                'patterns': [
                    r'why (does|did|is|are|was)',
                    r'(cause|caused) by',
                    r'(reason|reasons) (for|why)',
                    r'(result|results) (of|in)',
                    r'(lead|leads|led) to'
                ]
            },
            QueryIntent.DEFINITIONAL: {
                'keywords': ['what is', 'what are', 'define', 'definition', 'meaning'],
                'patterns': [
                    r'what (is|are) (a|an|the)?\s*\w+',
                    r'define\s+\w+',
                    r'definition of',
                    r'meaning of',
                    r'what does \w+ mean'
                ]
            },
            QueryIntent.PROCEDURAL: {
                'keywords': ['how to', 'steps', 'process', 'method', 'procedure', 'tutorial'],
                'patterns': [
                    r'how (to|do)',
                    r'(steps|process) (to|for)',
                    r'(method|procedure) (for|to)',
                    r'tutorial (on|for)',
                    r'(guide|instructions) (to|for)'
                ]
            },
            QueryIntent.CODE: {
                'keywords': ['code', 'function', 'algorithm', 'implement', 'program', 'syntax', 'error', 'debug'],
                'patterns': [
                    r'(code|coding|program)',
                    r'(function|method|class)',
                    r'(algorithm|implementation)',
                    r'(syntax|error|bug|debug)',
                    r'(python|java|javascript|c\+\+)'
                ]
            },
            QueryIntent.EXPLORATORY: {
                'keywords': ['tell me about', 'explain', 'describe', 'overview', 'summary'],
                'patterns': [
                    r'tell me (about|more)',
                    r'explain\s+\w+',
                    r'describe\s+\w+',
                    r'(overview|summary) of',
                    r'what can you tell'
                ]
            }
        }
    
    def classify(self, query: str) -> IntentClassification:
        """
        Classify query intent
        
        Args:
            query: User query string
        
        Returns:
            IntentClassification with primary and secondary intents
        """
        query_lower = query.lower()
        
        # Score each intent
        intent_scores = {}
        matched_keywords = []
        
        for intent, config in self.patterns.items():
            score = 0.0
            
            # Check keywords
            for keyword in config['keywords']:
                if keyword in query_lower:
                    score += 0.3
                    matched_keywords.append(keyword)
            
            # Check patterns
            for pattern in config['patterns']:
                if re.search(pattern, query_lower):
                    score += 0.5
            
            # Normalize score
            intent_scores[intent] = min(score, 1.0)
        
        # Sort by score
        sorted_intents = sorted(
            intent_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Determine primary intent
        if sorted_intents[0][1] > 0.3:
            primary_intent = sorted_intents[0][0]
            confidence = sorted_intents[0][1]
        else:
            primary_intent = QueryIntent.UNKNOWN
            confidence = 0.0
        
        # Get secondary intents
        secondary_intents = [
            (intent, score) 
            for intent, score in sorted_intents[1:4]
            if score > 0.2
        ]
        
        # Extract additional features
        metadata = self._extract_features(query)
        
        return IntentClassification(
            primary_intent=primary_intent,
            confidence=confidence,
            secondary_intents=secondary_intents,
            keywords=matched_keywords,
            metadata=metadata
        )
    
    def _extract_features(self, query: str) -> Dict:
        """Extract additional features from query"""
        features = {
            'query_length': len(query),
            'word_count': len(query.split()),
            'has_question_mark': '?' in query,
            'has_numbers': bool(re.search(r'\d+', query)),
            'has_quotes': '"' in query or "'" in query,
            'is_multiline': '\n' in query
        }
        
        # Check for specific entities
        if re.search(r'\b\d{4}\b', query):
            features['has_year'] = True
        
        if re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', query):
            features['has_proper_noun'] = True
        
        return features
