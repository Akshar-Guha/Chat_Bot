"""
Text Chunker - Splits documents into manageable chunks with metadata
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import re
import hashlib


@dataclass
class Chunk:
    """Represents a document chunk"""
    chunk_id: str
    doc_id: str
    text: str
    start_char: int
    end_char: int
    chunk_index: int
    metadata: Dict


class TextChunker:
    """Handles text chunking with configurable strategies"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        """
        Initialize chunker
        
        Args:
            chunk_size: Target size for chunks in characters
            chunk_overlap: Number of overlapping characters between chunks
            min_chunk_size: Minimum size for a chunk
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict] = None
    ) -> List[Chunk]:
        """
        Split document into chunks
        
        Args:
            doc_id: Document identifier
            text: Document text to chunk
            metadata: Optional metadata to attach to chunks
        
        Returns:
            List of Chunk objects
        """
        if not text:
            return []
        
        chunks = []
        
        # Split by paragraphs first
        paragraphs = self._split_paragraphs(text)
        
        current_pos = 0
        chunk_index = 0
        
        for para in paragraphs:
            para_start = text.find(para, current_pos)
            if para_start == -1:
                continue
            
            # If paragraph is small enough, use as chunk
            if len(para) <= self.chunk_size:
                if para.strip():  # Skip empty paragraphs
                    chunk = self._create_chunk(
                        doc_id=doc_id,
                        text=para,
                        start_char=para_start,
                        end_char=para_start + len(para),
                        chunk_index=chunk_index,
                        metadata=metadata
                    )
                    chunks.append(chunk)
                    chunk_index += 1
            else:
                # Split large paragraph into smaller chunks
                para_chunks = self._split_large_text(para, para_start)
                for pc_text, pc_start, pc_end in para_chunks:
                    chunk = self._create_chunk(
                        doc_id=doc_id,
                        text=pc_text,
                        start_char=pc_start,
                        end_char=pc_end,
                        chunk_index=chunk_index,
                        metadata=metadata
                    )
                    chunks.append(chunk)
                    chunk_index += 1
            
            current_pos = para_start + len(para)
        
        # Apply overlap between chunks
        chunks = self._apply_overlap(chunks, text)
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        # Split on double newlines or multiple spaces
        paragraphs = re.split(r'\n\n+|\r\n\r\n+', text)
        
        # Further split very long paragraphs on single newlines
        result = []
        for para in paragraphs:
            if len(para) > self.chunk_size * 2:
                # Split on single newlines for very long paragraphs
                sub_paras = para.split('\n')
                result.extend(sub_paras)
            else:
                result.append(para)
        
        return [p.strip() for p in result if p.strip()]
    
    def _split_large_text(
        self,
        text: str,
        base_offset: int
    ) -> List[tuple]:
        """Split large text into smaller chunks"""
        chunks = []
        
        # Try to split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = []
        current_length = 0
        chunk_start = 0
        
        for sent in sentences:
            sent_length = len(sent)
            
            if current_length + sent_length <= self.chunk_size:
                current_chunk.append(sent)
                current_length += sent_length + 1  # +1 for space
            else:
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunks.append((
                        chunk_text,
                        base_offset + chunk_start,
                        base_offset + chunk_start + len(chunk_text)
                    ))
                    chunk_start += len(chunk_text) + 1
                
                # Start new chunk with current sentence
                current_chunk = [sent]
                current_length = sent_length
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append((
                chunk_text,
                base_offset + chunk_start,
                base_offset + chunk_start + len(chunk_text)
            ))
        
        return chunks
    
    def _apply_overlap(self, chunks: List[Chunk], original_text: str) -> List[Chunk]:
        """Apply overlap between consecutive chunks"""
        if len(chunks) <= 1 or self.chunk_overlap == 0:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                # First chunk - add overlap from next chunk
                if i + 1 < len(chunks):
                    next_chunk = chunks[i + 1]
                    overlap_text = next_chunk.text[:self.chunk_overlap]
                    new_text = chunk.text + ' ' + overlap_text
                else:
                    new_text = chunk.text
            elif i == len(chunks) - 1:
                # Last chunk - add overlap from previous chunk
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk.text[-self.chunk_overlap:]
                new_text = overlap_text + ' ' + chunk.text
            else:
                # Middle chunks - add overlap from both sides
                prev_chunk = chunks[i - 1]
                next_chunk = chunks[i + 1]
                prev_overlap = prev_chunk.text[-self.chunk_overlap:]
                next_overlap = next_chunk.text[:self.chunk_overlap]
                new_text = prev_overlap + ' ' + chunk.text + ' ' + next_overlap
            
            # Update chunk with new text
            chunk.text = new_text
            chunk.chunk_id = self._generate_chunk_id(chunk.doc_id, chunk.text)
            overlapped_chunks.append(chunk)
        
        return overlapped_chunks
    
    def _create_chunk(
        self,
        doc_id: str,
        text: str,
        start_char: int,
        end_char: int,
        chunk_index: int,
        metadata: Optional[Dict] = None
    ) -> Chunk:
        """Create a chunk object"""
        chunk_id = self._generate_chunk_id(doc_id, text)
        
        chunk_metadata = {
            'char_count': len(text),
            'word_count': len(text.split()),
            'has_overlap': self.chunk_overlap > 0
        }
        
        if metadata:
            chunk_metadata.update(metadata)
        
        return Chunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            text=text,
            start_char=start_char,
            end_char=end_char,
            chunk_index=chunk_index,
            metadata=chunk_metadata
        )
    
    def _generate_chunk_id(self, doc_id: str, text: str) -> str:
        """Generate unique chunk ID"""
        content = f"{doc_id}:{text[:100]}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
