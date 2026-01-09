"""
Unit Processing State model.

This model is the SINGLE SOURCE OF TRUTH for a unit's readiness for chat.
It tracks the progress of the background pipeline:
Upload -> Text Extraction -> Chunking -> Embeddings -> Ready
"""

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Boolean, Integer, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.unit import Unit


class UnitProcessingState(Base):
    """
    Tracks the processing state of a unit.
    
    Attributes:
        unit_id: Foreign key to the unit.
        has_files: Whether files have been uploaded.
        text_extracted: Whether text extraction is complete/successful.
        chunk_count: Number of chunks generated.
        embeddings_ready: Whether embeddings have been generated.
        status: Overall status enum (empty, uploaded, processing, ready, failed).
        last_error: Last error message if status is 'failed'.
    """
    
    __tablename__ = "unit_processing_states"
    
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), primary_key=True)
    
    # Progress flags
    has_files: Mapped[bool] = mapped_column(Boolean, default=False)
    text_extracted: Mapped[bool] = mapped_column(Boolean, default=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    embeddings_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Overall status
    # simple string for now to avoid enum complexity with alembic in this env if not needed, 
    # but strictly controlled by logic.
    status: Mapped[str] = mapped_column(String(50), default="empty") 
    
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    unit: Mapped["Unit"] = relationship("Unit", back_populates="processing_state")
    
    def __repr__(self) -> str:
        return f"<UnitProcessingState(unit_id={self.unit_id}, status='{self.status}')>"
