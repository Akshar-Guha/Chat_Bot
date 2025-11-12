"""
Pydantic models and schemas
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for queries"""
    query: str = Field(..., description="The query text")
    k: Optional[int] = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of chunks to retrieve"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata filters for retrieval"
    )
    use_web_search: bool = Field(
        default=False,
        description="Enable web search integration"
    )
    use_wikipedia: bool = Field(
        default=False,
        description="Include Wikipedia results when web search is enabled"
    )
    search_strategy: str = Field(
        default="hybrid",
        description="Search strategy: local_only, web_only, or hybrid"
    )


class QueryResponse(BaseModel):
    """Response model for queries"""
    query: str
    answer: str
    chunks: List[Dict[str, Any]]
    provenance: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class DocumentIngestRequest(BaseModel):
    """Request model for document ingestion"""
    filename: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class DocumentIngestResponse(BaseModel):
    """Response model for document ingestion"""
    doc_id: str
    filename: str
    num_chunks: int
    message: str


class IndexStatsResponse(BaseModel):
    """Response model for index statistics"""
    total_documents: int
    total_chunks: int
    index_size: str
    last_updated: Optional[str]


class MemoryEntryRequest(BaseModel):
    """Request model for memory operations"""
    content: str
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class MemoryEntryResponse(BaseModel):
    """Response model for memory operations"""
    id: str
    content: str
    metadata: Dict[str, Any]
    tags: List[str]
    created_at: str
