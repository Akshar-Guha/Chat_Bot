"""
Memory Models - Database models for memory persistence
"""

from sqlalchemy import create_engine, Column, String, Text, Float, Integer, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Dict, List, Optional
import json

Base = declarative_base()


class MemoryEntry(Base):
    """Memory entry model"""
    __tablename__ = 'memory_entries'
    
    id = Column(String, primary_key=True)
    query_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Retrieved chunks
    chunk_ids = Column(JSON)  # List of chunk IDs
    chunk_scores = Column(JSON)  # Corresponding scores
    
    # Metadata
    intent = Column(String)
    intent_confidence = Column(Float)
    model_used = Column(String)
    
    # Importance and feedback
    importance_score = Column(Float, default=0.5)
    user_feedback = Column(String)  # positive, negative, neutral
    feedback_text = Column(Text)
    
    # Usage tracking
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    
    # Edit tracking
    is_edited = Column(Boolean, default=False)
    original_answer = Column(Text)
    edit_timestamp = Column(DateTime)
    
    # Privacy
    is_private = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'query_text': self.query_text,
            'answer_text': self.answer_text,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'chunk_ids': self.chunk_ids,
            'chunk_scores': self.chunk_scores,
            'intent': self.intent,
            'intent_confidence': self.intent_confidence,
            'model_used': self.model_used,
            'importance_score': self.importance_score,
            'user_feedback': self.user_feedback,
            'feedback_text': self.feedback_text,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'is_edited': self.is_edited,
            'is_private': self.is_private
        }


class ConversationSession(Base):
    """Conversation session model"""
    __tablename__ = 'conversation_sessions'
    
    id = Column(String, primary_key=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    
    # Session metadata
    title = Column(String)
    description = Column(Text)
    tags = Column(JSON)  # List of tags
    
    # Memory references
    memory_ids = Column(JSON)  # List of memory entry IDs
    
    # Statistics
    query_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'memory_ids': self.memory_ids,
            'query_count': self.query_count,
            'total_tokens': self.total_tokens
        }


class MemoryIndex(Base):
    """Index for fast memory retrieval"""
    __tablename__ = 'memory_index'
    
    id = Column(String, primary_key=True)
    memory_id = Column(String, nullable=False)
    
    # Embedding for similarity search
    embedding = Column(JSON)  # Serialized embedding vector
    embedding_model = Column(String)
    
    # Keywords for keyword search
    keywords = Column(JSON)  # List of keywords
    
    # Temporal index
    timestamp = Column(DateTime)
    session_id = Column(String)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'memory_id': self.memory_id,
            'embedding_model': self.embedding_model,
            'keywords': self.keywords,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'session_id': self.session_id
        }
