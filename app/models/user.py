"""
User model for multi-user support.

Users own subjects and all nested content (units, topics).
Authentication is stubbed for now (Google OAuth in future phase).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.subject import Subject


class User(Base):
    """
    User model representing an authenticated user.
    
    Attributes:
        id: Primary key.
        email: Unique email address (from OAuth provider).
        created_at: Timestamp of account creation.
        subjects: List of subjects owned by this user.
    """
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    subjects: Mapped[list["Subject"]] = relationship(
        "Subject",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
