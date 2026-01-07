"""
Chunk model representing a text chunk from processed files.

Chunks are the fundamental unit of RAG retrieval.
Each chunk belongs to exactly one topic and contains metadata
for filtering during retrieval.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.topic import Topic


class Chunk(Base):
    """
    Chunk model representing a text segment for RAG retrieval.
    
    Chunks are created by splitting extracted file text into
    overlapping segments of 300-600 tokens. Each chunk maintains
    full metadata for scoped retrieval.
    
    Attributes:
        id: Primary key (chunk_id).
        user_id: Owner of the content (for filtering).
        subject_id: Subject scope (for filtering).
        unit_id: Unit scope (for filtering).
        topic_id: Topic scope (for filtering).
        source_file_id: Source file this chunk was extracted from.
        chunk_index: Position of this chunk within the file.
        text: The actual chunk text content.
        token_count: Number of tokens in this chunk.
        embedding_id: FAISS index position (null if not yet embedded).
        created_at: Timestamp of creation.
        source_file: Reference to the source file.
        topic: Reference to the parent topic.
    """
    
    __tablename__ = "chunks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Metadata for scoped retrieval
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    subject_id: Mapped[int] = mapped_column(Integer, index=True)
    unit_id: Mapped[int] = mapped_column(Integer, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    source_file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), index=True)
    
    # Chunk data
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    
    # Embedding tracking
    embedding_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    source_file: Mapped["File"] = relationship("File", backref="chunks")
    topic: Mapped["Topic"] = relationship("Topic", backref="chunks")
    
    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, topic_id={self.topic_id}, index={self.chunk_index})>"
