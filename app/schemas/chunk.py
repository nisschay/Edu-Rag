"""
Pydantic schemas for Chunk model.

Provides validation and serialization for chunk operations.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ChunkBase(BaseModel):
    """Base schema with common chunk fields."""
    
    text: str = Field(..., description="The chunk text content")


class ChunkCreate(ChunkBase):
    """Schema for creating a new chunk."""
    
    user_id: int
    subject_id: int
    unit_id: int
    topic_id: int
    source_file_id: int
    chunk_index: int
    token_count: int


class ChunkRead(BaseModel):
    """Schema for reading a chunk."""
    
    id: int
    user_id: int
    subject_id: int
    unit_id: int
    topic_id: int
    source_file_id: int
    chunk_index: int
    text: str
    token_count: int
    embedding_id: int | None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ChunkList(BaseModel):
    """Schema for listing chunks."""
    
    id: int
    chunk_index: int
    token_count: int
    text_preview: str = Field(..., description="First 100 characters of chunk text")
    has_embedding: bool
    
    model_config = {"from_attributes": True}


class ChunkWithScore(BaseModel):
    """Schema for chunk with similarity score (from retrieval)."""
    
    chunk_id: int
    text: str
    score: float
    source_file_id: int
    topic_id: int
    unit_id: int
    subject_id: int
    
    model_config = {"from_attributes": True}


class ChunkingRequest(BaseModel):
    """Request schema for triggering chunking."""
    
    pass  # No additional params needed, topic_id comes from URL


class ChunkingResponse(BaseModel):
    """Response schema for chunking operation."""
    
    topic_id: int
    files_processed: int
    chunks_created: int
    total_tokens: int


class EmbeddingRequest(BaseModel):
    """Request schema for triggering embedding."""
    
    pass  # No additional params needed, topic_id comes from URL


class EmbeddingResponse(BaseModel):
    """Response schema for embedding operation."""
    
    topic_id: int
    chunks_embedded: int
    already_embedded: int


class RetrievalRequest(BaseModel):
    """Request schema for testing retrieval."""
    
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")


class RetrievalResponse(BaseModel):
    """Response schema for retrieval operation."""
    
    query: str
    topic_id: int
    chunks_found: int
    chunks: list[ChunkWithScore]
