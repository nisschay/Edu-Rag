"""
Unit model representing a unit/chapter within a subject.

Units are ordered within a subject and contain topics.
Example: "Unit 1: Introduction", "Unit 2: Advanced Topics"
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.subject import Subject
    from app.models.topic import Topic


class Unit(Base):
    """
    Unit model representing a chapter or module within a subject.
    
    Attributes:
        id: Primary key.
        subject_id: Foreign key to the parent subject.
        unit_number: Ordering number (1, 2, 3...).
        title: Unit title (e.g., "Introduction to Algorithms").
        created_at: Timestamp of creation.
        subject: Reference to the parent subject.
        topics: List of topics within this unit.
    """
    
    __tablename__ = "units"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    unit_number: Mapped[int] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="units")
    topics: Mapped[list["Topic"]] = relationship(
        "Topic",
        back_populates="unit",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    processing_state: Mapped["UnitProcessingState"] = relationship(
        "UnitProcessingState",
        back_populates="unit",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False, # One-to-one
    )
    
    def __repr__(self) -> str:
        return f"<Unit(id={self.id}, unit_number={self.unit_number}, title='{self.title}')>"
