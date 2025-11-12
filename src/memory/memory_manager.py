"""
Memory Manager - Handles CRUD operations for memory
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import json
import numpy as np
from sqlalchemy import create_engine, and_, or_, desc
from sqlalchemy.orm import sessionmaker, Session
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.models import Base, MemoryEntry, ConversationSession, MemoryIndex
from core.embeddings import EmbeddingGenerator


class MemoryManager:
    """Manages memory persistence and retrieval"""
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize memory manager
        
        Args:
            db_path: Path to SQLite database
            embedding_model: Model for memory embeddings
        """
        if db_path is None:
            db_path = Path("./memory.db")
        
        self.db_path = db_path
        
        # Setup database
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize embedder
        self.embedder = EmbeddingGenerator(model_name=embedding_model)
        self.embedding_model = embedding_model
        
        # Current session
        self.current_session_id = None
    
    def create_memory(
        self,
        query: str,
        answer: str,
        chunk_ids: List[str],
        chunk_scores: List[float],
        intent: Optional[str] = None,
        intent_confidence: Optional[float] = None,
        model_used: Optional[str] = None,
        importance_score: float = 0.5
    ) -> str:
        """
        Create a new memory entry
        
        Args:
            query: Query text
            answer: Answer text
            chunk_ids: IDs of chunks used
            chunk_scores: Scores of chunks
            intent: Query intent
            intent_confidence: Intent confidence score
            model_used: Model used for generation
            importance_score: Importance of this memory
        
        Returns:
            Memory entry ID
        """
        memory_id = str(uuid.uuid4())[:16]
        
        with self.SessionLocal() as session:
            # Create memory entry
            memory = MemoryEntry(
                id=memory_id,
                query_text=query,
                answer_text=answer,
                chunk_ids=chunk_ids,
                chunk_scores=chunk_scores,
                intent=intent,
                intent_confidence=intent_confidence,
                model_used=model_used,
                importance_score=importance_score,
                timestamp=datetime.utcnow()
            )
            
            session.add(memory)
            
            # Create index entry
            self._create_memory_index(session, memory)
            
            # Add to current session if exists
            if self.current_session_id:
                self._add_to_session(session, memory_id)
            
            session.commit()
        
        return memory_id
    
    def get_memory(self, memory_id: str) -> Optional[Dict]:
        """
        Retrieve a memory entry
        
        Args:
            memory_id: Memory entry ID
        
        Returns:
            Memory entry as dictionary or None
        """
        with self.SessionLocal() as session:
            memory = session.query(MemoryEntry).filter(
                and_(
                    MemoryEntry.id == memory_id,
                    MemoryEntry.is_deleted == False
                )
            ).first()
            
            if memory:
                # Update access tracking
                memory.access_count += 1
                memory.last_accessed = datetime.utcnow()
                session.commit()
                
                return memory.to_dict()
        
        return None
    
    def update_memory(
        self,
        memory_id: str,
        answer: Optional[str] = None,
        importance_score: Optional[float] = None,
        user_feedback: Optional[str] = None,
        feedback_text: Optional[str] = None
    ) -> bool:
        """
        Update a memory entry
        
        Args:
            memory_id: Memory entry ID
            answer: New answer text
            importance_score: New importance score
            user_feedback: User feedback (positive/negative/neutral)
            feedback_text: Feedback text
        
        Returns:
            True if updated successfully
        """
        with self.SessionLocal() as session:
            memory = session.query(MemoryEntry).filter(
                and_(
                    MemoryEntry.id == memory_id,
                    MemoryEntry.is_deleted == False
                )
            ).first()
            
            if not memory:
                return False
            
            # Update fields
            if answer is not None:
                if not memory.is_edited:
                    memory.original_answer = memory.answer_text
                    memory.is_edited = True
                    memory.edit_timestamp = datetime.utcnow()
                memory.answer_text = answer
            
            if importance_score is not None:
                memory.importance_score = importance_score
            
            if user_feedback is not None:
                memory.user_feedback = user_feedback
            
            if feedback_text is not None:
                memory.feedback_text = feedback_text
            
            session.commit()
            
            # Update index if answer changed
            if answer is not None:
                self._update_memory_index(session, memory)
            
            return True
    
    def delete_memory(self, memory_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a memory entry
        
        Args:
            memory_id: Memory entry ID
            hard_delete: If True, permanently delete; else soft delete
        
        Returns:
            True if deleted successfully
        """
        with self.SessionLocal() as session:
            memory = session.query(MemoryEntry).filter(
                MemoryEntry.id == memory_id
            ).first()
            
            if not memory:
                return False
            
            if hard_delete:
                # Delete index entries
                session.query(MemoryIndex).filter(
                    MemoryIndex.memory_id == memory_id
                ).delete()
                
                # Delete memory
                session.delete(memory)
            else:
                # Soft delete
                memory.is_deleted = True
            
            session.commit()
            return True
    
    def list_memories(
        self,
        limit: int = 50,
        offset: int = 0,
        session_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_importance: Optional[float] = None
    ) -> List[Dict]:
        """
        List memory entries with filters
        
        Args:
            limit: Maximum number of entries
            offset: Offset for pagination
            session_id: Filter by session
            start_date: Filter by start date
            end_date: Filter by end date
            min_importance: Minimum importance score
        
        Returns:
            List of memory entries
        """
        with self.SessionLocal() as session:
            query = session.query(MemoryEntry).filter(
                MemoryEntry.is_deleted == False
            )
            
            # Apply filters
            if start_date:
                query = query.filter(MemoryEntry.timestamp >= start_date)
            
            if end_date:
                query = query.filter(MemoryEntry.timestamp <= end_date)
            
            if min_importance is not None:
                query = query.filter(MemoryEntry.importance_score >= min_importance)
            
            # Order by timestamp desc
            query = query.order_by(desc(MemoryEntry.timestamp))
            
            # Apply pagination
            memories = query.offset(offset).limit(limit).all()
            
            return [m.to_dict() for m in memories]
    
    def search_memories(
        self,
        query: str,
        k: int = 10,
        min_score: float = 0.5
    ) -> List[Tuple[Dict, float]]:
        """
        Search memories using semantic similarity
        
        Args:
            query: Search query
            k: Number of results
            min_score: Minimum similarity score
        
        Returns:
            List of (memory, score) tuples
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        with self.SessionLocal() as session:
            # Get all memory indices
            indices = session.query(MemoryIndex).all()
            
            if not indices:
                return []
            
            # Calculate similarities
            similarities = []
            for idx in indices:
                if idx.embedding:
                    memory_embedding = np.array(idx.embedding)
                    similarity = self.embedder.compute_similarity(
                        query_embedding,
                        memory_embedding
                    )
                    
                    if similarity >= min_score:
                        similarities.append((idx.memory_id, similarity))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Get top k memories
            results = []
            for memory_id, score in similarities[:k]:
                memory = session.query(MemoryEntry).filter(
                    and_(
                        MemoryEntry.id == memory_id,
                        MemoryEntry.is_deleted == False
                    )
                ).first()
                
                if memory:
                    results.append((memory.to_dict(), score))
            
            return results
    
    def export_memories(
        self,
        output_path: Path,
        session_id: Optional[str] = None
    ) -> int:
        """
        Export memories to JSON file
        
        Args:
            output_path: Path to output file
            session_id: Export only memories from this session
        
        Returns:
            Number of memories exported
        """
        memories = self.list_memories(limit=10000, session_id=session_id)
        
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'total_memories': len(memories),
            'memories': memories
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return len(memories)
    
    def import_memories(self, input_path: Path) -> int:
        """
        Import memories from JSON file
        
        Args:
            input_path: Path to input file
        
        Returns:
            Number of memories imported
        """
        with open(input_path, 'r') as f:
            import_data = json.load(f)
        
        memories = import_data.get('memories', [])
        imported_count = 0
        
        with self.SessionLocal() as session:
            for memory_data in memories:
                # Check if memory already exists
                existing = session.query(MemoryEntry).filter(
                    MemoryEntry.id == memory_data['id']
                ).first()
                
                if not existing:
                    memory = MemoryEntry(
                        id=memory_data['id'],
                        query_text=memory_data['query_text'],
                        answer_text=memory_data['answer_text'],
                        chunk_ids=memory_data.get('chunk_ids', []),
                        chunk_scores=memory_data.get('chunk_scores', []),
                        intent=memory_data.get('intent'),
                        intent_confidence=memory_data.get('intent_confidence'),
                        model_used=memory_data.get('model_used'),
                        importance_score=memory_data.get('importance_score', 0.5),
                        user_feedback=memory_data.get('user_feedback'),
                        feedback_text=memory_data.get('feedback_text')
                    )
                    
                    session.add(memory)
                    self._create_memory_index(session, memory)
                    imported_count += 1
            
            session.commit()
        
        return imported_count
    
    def promote_memory(self, memory_id: str) -> bool:
        """
        Promote a memory (increase importance)
        
        Args:
            memory_id: Memory entry ID
        
        Returns:
            True if promoted successfully
        """
        with self.SessionLocal() as session:
            memory = session.query(MemoryEntry).filter(
                and_(
                    MemoryEntry.id == memory_id,
                    MemoryEntry.is_deleted == False
                )
            ).first()
            
            if memory:
                memory.importance_score = min(1.0, memory.importance_score + 0.2)
                session.commit()
                return True
        
        return False
    
    def demote_memory(self, memory_id: str) -> bool:
        """
        Demote a memory (decrease importance)
        
        Args:
            memory_id: Memory entry ID
        
        Returns:
            True if demoted successfully
        """
        with self.SessionLocal() as session:
            memory = session.query(MemoryEntry).filter(
                and_(
                    MemoryEntry.id == memory_id,
                    MemoryEntry.is_deleted == False
                )
            ).first()
            
            if memory:
                memory.importance_score = max(0.0, memory.importance_score - 0.2)
                session.commit()
                return True
        
        return False
    
    def _create_memory_index(self, session: Session, memory: MemoryEntry):
        """Create index entry for memory"""
        # Generate embedding for query
        query_embedding = self.embedder.embed_text(memory.query_text)
        
        # Extract keywords (simple version)
        keywords = self._extract_keywords(memory.query_text)
        
        index = MemoryIndex(
            id=str(uuid.uuid4())[:16],
            memory_id=memory.id,
            embedding=query_embedding.tolist(),
            embedding_model=self.embedding_model,
            keywords=keywords,
            timestamp=memory.timestamp,
            session_id=self.current_session_id
        )
        
        session.add(index)
    
    def _update_memory_index(self, session: Session, memory: MemoryEntry):
        """Update index entry for memory"""
        # Delete old index
        session.query(MemoryIndex).filter(
            MemoryIndex.memory_id == memory.id
        ).delete()
        
        # Create new index
        self._create_memory_index(session, memory)
    
    def _add_to_session(self, session: Session, memory_id: str):
        """Add memory to current session"""
        if not self.current_session_id:
            return
        
        conv_session = session.query(ConversationSession).filter(
            ConversationSession.id == self.current_session_id
        ).first()
        
        if conv_session:
            memory_ids = conv_session.memory_ids or []
            memory_ids.append(memory_id)
            conv_session.memory_ids = memory_ids
            conv_session.query_count += 1
    
    def get_all_memories(self, limit: int = 50) -> List[Dict]:
        """
        Get all memories (wrapper for list_memories for API compatibility)
        
        Args:
            limit: Maximum number of memories to return
        
        Returns:
            List of memory dictionaries
        """
        return self.list_memories(limit=limit)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (simple version)"""
        # Simple keyword extraction
        import re
        
        # Remove common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were'}
        
        # Tokenize and filter
        words = re.findall(r'\b[a-z]+\b', text.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        
        # Get unique keywords
        return list(set(keywords))[:10]
