"""
File model representing an uploaded academic file.

Files are attached to topics and contain extracted text content.
Supported formats: PDF, PPT/PPTX, DOCX, TXT
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.topic import Topic


class File(Base):
    """
    File model representing an uploaded document.
    
    Attributes:
        id: Primary key.
        topic_id: Foreign key to the parent topic.
        filename: Original filename from upload.
        filepath: Path to stored file on disk.
        file_type: File extension (pdf, docx, pptx, txt).
        file_size: Size in bytes.
        extracted_text: Raw text extracted from the file.
        created_at: Timestamp of upload.
        topic: Reference to the parent topic.
    """
    
    __tablename__ = "files"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    filepath: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(10))
    file_size: Mapped[int] = mapped_column()
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processing, ready, failed
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    topic: Mapped["Topic"] = relationship("Topic", back_populates="files")
    
    def __repr__(self) -> str:
        return f"<File(id={self.id}, filename='{self.filename}')>"
