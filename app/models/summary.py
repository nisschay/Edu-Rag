"""
Summary models for topic and unit summaries.

Summaries provide hierarchical abstraction of content:
- TopicSummary: 200-300 tokens, concept-focused
- UnitSummary: 300-500 tokens, structured in teaching order
"""

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import ForeignKey, String, Text, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.topic import Topic
    from app.models.unit import Unit


class TopicSummary(Base):
    """
    Topic summary model for concept-focused summaries.
    
    Attributes:
        id: Primary key.
        user_id: Owner user ID (for filtering).
        subject_id: Subject ID (for filtering).
        unit_id: Unit ID (for filtering).
        topic_id: Topic ID (unique, one summary per topic).
        summary_text: The generated summary (200-300 tokens).
        token_count: Number of tokens in summary.
        source_chunk_count: Number of chunks used to generate.
        embedding_id: FAISS summary index position.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
        topic: Reference to the topic.
    """
    
    __tablename__ = "topic_summaries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Metadata for scoped retrieval
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    subject_id: Mapped[int] = mapped_column(Integer, index=True)
    unit_id: Mapped[int] = mapped_column(Integer, index=True)
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id"), 
        unique=True, 
        index=True
    )
    
    # Summary content
    summary_text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    source_chunk_count: Mapped[int] = mapped_column(Integer)
    
    # Embedding tracking
    embedding_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    topic: Mapped["Topic"] = relationship("Topic", backref="summary")
    
    def __repr__(self) -> str:
        return f"<TopicSummary(id={self.id}, topic_id={self.topic_id})>"


class UnitSummary(Base):
    """
    Unit summary model for teaching-order structured summaries.
    
    Attributes:
        id: Primary key.
        user_id: Owner user ID (for filtering).
        subject_id: Subject ID (for filtering).
        unit_id: Unit ID (unique, one summary per unit).
        summary_text: The generated summary (300-500 tokens).
        token_count: Number of tokens in summary.
        source_topic_count: Number of topic summaries used.
        embedding_id: FAISS summary index position.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last update.
        unit: Reference to the unit.
    """
    
    __tablename__ = "unit_summaries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Metadata for scoped retrieval
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    subject_id: Mapped[int] = mapped_column(Integer, index=True)
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id"), 
        unique=True, 
        index=True
    )
    
    # Summary content
    summary_text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    source_topic_count: Mapped[int] = mapped_column(Integer)
    
    # Embedding tracking
    embedding_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    unit: Mapped["Unit"] = relationship("Unit", backref="summary")
    
    def __repr__(self) -> str:
        return f"<UnitSummary(id={self.id}, unit_id={self.unit_id})>"
