"""
Pydantic schemas for Summary models.

Provides validation and serialization for summary operations.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


class TopicSummaryBase(BaseModel):
    """Base schema for topic summary."""
    
    summary_text: str = Field(..., description="The summary text")


class TopicSummaryRead(BaseModel):
    """Schema for reading a topic summary."""
    
    id: int
    user_id: int
    subject_id: int
    unit_id: int
    topic_id: int
    summary_text: str
    token_count: int
    source_chunk_count: int
    has_embedding: bool = Field(default=False)
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class TopicSummaryResponse(BaseModel):
    """Response schema for topic summary generation."""
    
    topic_id: int
    topic_title: str
    summary_text: str
    token_count: int
    source_chunk_count: int
    regenerated: bool = Field(
        default=False, 
        description="True if summary was regenerated"
    )


class UnitSummaryBase(BaseModel):
    """Base schema for unit summary."""
    
    summary_text: str = Field(..., description="The summary text")


class UnitSummaryRead(BaseModel):
    """Schema for reading a unit summary."""
    
    id: int
    user_id: int
    subject_id: int
    unit_id: int
    summary_text: str
    token_count: int
    source_topic_count: int
    has_embedding: bool = Field(default=False)
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class UnitSummaryResponse(BaseModel):
    """Response schema for unit summary generation."""
    
    unit_id: int
    unit_title: str
    summary_text: str
    token_count: int
    source_topic_count: int
    regenerated: bool = Field(
        default=False, 
        description="True if summary was regenerated"
    )


class EmbedSummariesResponse(BaseModel):
    """Response for embedding summaries."""
    
    summaries_embedded: int
    already_embedded: int
