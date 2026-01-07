"""
User Pydantic schemas for request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base schema with common user fields."""
    
    email: EmailStr


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    
    Example:
        {"email": "student@university.edu"}
    """
    
    pass


class UserRead(UserBase):
    """
    Schema for reading user data.
    
    Example:
        {
            "id": 1,
            "email": "student@university.edu",
            "created_at": "2026-01-06T12:00:00"
        }
    """
    
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}
