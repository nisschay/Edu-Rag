"""
Subject model representing an academic subject/course.

A subject belongs to a user and contains ordered units.
Example: "Computer Science 101", "Calculus I"
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.unit import Unit
    from app.models.user import User


class Subject(Base):
    """
    Subject model representing an academic course or subject.
    
    Attributes:
        id: Primary key.
        user_id: Foreign key to the owning user.
        name: Subject name (e.g., "Introduction to Physics").
        created_at: Timestamp of creation.
        user: Reference to the owning user.
        units: List of units within this subject.
    """
    
    __tablename__ = "subjects"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subjects")
    units: Mapped[list["Unit"]] = relationship(
        "Unit",
        back_populates="subject",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Unit.unit_number",
    )
    
    def __repr__(self) -> str:
        return f"<Subject(id={self.id}, name='{self.name}')>"
