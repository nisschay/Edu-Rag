"""
Unit Pydantic schemas for request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class UnitBase(BaseModel):
    """Base schema with common unit fields."""
    
    title: str = Field(..., min_length=1, max_length=255, description="Unit title")


class UnitCreate(UnitBase):
    """
    Schema for creating a new unit.
    
    unit_number is optional - if not provided, it will be auto-assigned
    as the next number in sequence.
    
    Example:
        {"title": "Introduction to Algorithms"}
        {"title": "Data Structures", "unit_number": 2}
    """
    
    unit_number: int | None = Field(
        default=None,
        ge=1,
        description="Unit order number (auto-assigned if not provided)",
    )


class UnitRead(UnitBase):
    """
    Schema for reading unit data.
    
    Example:
        {
            "id": 1,
            "subject_id": 1,
            "unit_number": 1,
            "title": "Introduction to Algorithms",
            "created_at": "2026-01-06T12:00:00"
        }
    """
    
    id: int
    subject_id: int
    unit_number: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class UnitList(BaseModel):
    """
    Schema for listing units.
    
    Example:
        {
            "units": [
                {"id": 1, "subject_id": 1, "unit_number": 1, "title": "Intro", ...},
                {"id": 2, "subject_id": 1, "unit_number": 2, "title": "Basics", ...}
            ],
            "count": 2
        }
    """
    
    units: list[UnitRead]
    count: int
