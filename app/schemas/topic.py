"""
Topic Pydantic schemas for request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TopicBase(BaseModel):
    """Base schema with common topic fields."""
    
    title: str = Field(..., min_length=1, max_length=255, description="Topic title")


class TopicCreate(TopicBase):
    """
    Schema for creating a new topic.
    
    Example:
        {"title": "Binary Search Algorithm"}
    """
    
    pass


class TopicRead(TopicBase):
    """
    Schema for reading topic data.
    
    Example:
        {
            "id": 1,
            "unit_id": 1,
            "title": "Binary Search Algorithm",
            "created_at": "2026-01-06T12:00:00"
        }
    """
    
    id: int
    unit_id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class TopicList(BaseModel):
    """
    Schema for listing topics.
    
    Example:
        {
            "topics": [
                {"id": 1, "unit_id": 1, "title": "Binary Search", ...},
                {"id": 2, "unit_id": 1, "title": "Linear Search", ...}
            ],
            "count": 2
        }
    """
    
    topics: list[TopicRead]
    count: int
