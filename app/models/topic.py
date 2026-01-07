"""
Topic model representing a specific topic within a unit.

Topics are the leaf nodes of the academic hierarchy.
Example: "Binary Search", "Recursion Basics"
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.unit import Unit
    from app.models.file import File


class Topic(Base):
    """
    Topic model representing a specific learning topic within a unit.
    
    Attributes:
        id: Primary key.
        unit_id: Foreign key to the parent unit.
        title: Topic title (e.g., "Bubble Sort Algorithm").
        created_at: Timestamp of creation.
        unit: Reference to the parent unit.
        files: List of uploaded files for this topic.
    """
    
    __tablename__ = "topics"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    unit: Mapped["Unit"] = relationship("Unit", back_populates="topics")
    files: Mapped[list["File"]] = relationship(
        "File",
        back_populates="topic",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Topic(id={self.id}, title='{self.title}')>"
