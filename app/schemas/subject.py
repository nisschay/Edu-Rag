"""
Subject Pydantic schemas for request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SubjectBase(BaseModel):
    """Base schema with common subject fields."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Subject name")


class SubjectCreate(SubjectBase):
    """
    Schema for creating a new subject.
    
    Example:
        {"name": "Introduction to Computer Science"}
    """
    
    pass


class SubjectRead(SubjectBase):
    """
    Schema for reading subject data.
    
    Example:
        {
            "id": 1,
            "user_id": 1,
            "name": "Introduction to Computer Science",
            "created_at": "2026-01-06T12:00:00"
        }
    """
    
    id: int
    user_id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class SubjectList(BaseModel):
    """
    Schema for listing subjects.
    
    Example:
        {
            "subjects": [
                {"id": 1, "user_id": 1, "name": "CS 101", "created_at": "..."},
                {"id": 2, "user_id": 1, "name": "Math 201", "created_at": "..."}
            ],
            "count": 2
        }
    """
    
    subjects: list[SubjectRead]
    count: int
