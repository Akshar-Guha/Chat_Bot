"""
Document Ingestor - Handles PDF, TXT, and other document formats
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import PyPDF2
from bs4 import BeautifulSoup
import chardet


@dataclass
class Document:
    """Represents an ingested document"""
    doc_id: str
    filename: str
    content: str
    metadata: Dict
    page_offsets: Optional[List[Tuple[int, int]]] = None  # (page_num, char_offset)


class DocumentIngestor:
    """Handles document ingestion from various formats"""
    
    def __init__(self):
        self.supported_formats = {'.txt', '.pdf', '.html', '.md'}
    
    def ingest(self, file_path: Path) -> Document:
        """Ingest a document from file path"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = file_path.suffix.lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported format: {file_ext}")
        
        # Generate document ID
        doc_id = self._generate_doc_id(file_path)
        
        # Extract content based on file type
        if file_ext == '.txt' or file_ext == '.md':
            content, metadata = self._ingest_text(file_path)
            page_offsets = None
        elif file_ext == '.pdf':
            content, metadata, page_offsets = self._ingest_pdf(file_path)
        elif file_ext == '.html':
            content, metadata = self._ingest_html(file_path)
            page_offsets = None
        else:
            raise ValueError(f"Handler not implemented for {file_ext}")
        
        return Document(
            doc_id=doc_id,
            filename=file_path.name,
            content=content,
            metadata=metadata,
            page_offsets=page_offsets
        )
    
    def _generate_doc_id(self, file_path: Path) -> str:
        """Generate unique document ID"""
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()[:16]
    
    def _ingest_text(self, file_path: Path) -> Tuple[str, Dict]:
        """Ingest plain text file"""
        # Detect encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
        
        # Read content
        content = file_path.read_text(encoding=encoding)
        
        metadata = {
            'format': 'text',
            'encoding': encoding,
            'size': len(content),
            'path': str(file_path)
        }
        
        return content, metadata
    
    def _ingest_pdf(self, file_path: Path) -> Tuple[str, Dict, List[Tuple[int, int]]]:
        """Ingest PDF file"""
        content_parts = []
        page_offsets = []
        char_offset = 0
        
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            num_pages = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                content_parts.append(page_text)
                page_offsets.append((page_num + 1, char_offset))
                char_offset += len(page_text)
        
        content = '\n'.join(content_parts)
        
        metadata = {
            'format': 'pdf',
            'pages': num_pages,
            'size': len(content),
            'path': str(file_path)
        }
        
        return content, metadata, page_offsets
    
    def _ingest_html(self, file_path: Path) -> Tuple[str, Dict]:
        """Ingest HTML file"""
        html_content = file_path.read_text(encoding='utf-8')
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract text content
        content = soup.get_text(separator='\n', strip=True)
        
        # Extract title if present
        title = ''
        if soup.title:
            title = soup.title.string
        
        metadata = {
            'format': 'html',
            'title': title,
            'size': len(content),
            'path': str(file_path)
        }
        
        return content, metadata
