"""
SQLAlchemy ORM models package.

This package contains all database models organized by domain:
- User: Multi-user support
- Subject, Unit, Topic: Curriculum hierarchy
- File: Uploaded documents
- Chunk: RAG text chunks
- TopicSummary, UnitSummary: Hierarchical summaries
"""

from app.models.user import User
from app.models.subject import Subject
from app.models.unit import Unit
from app.models.topic import Topic
from app.models.file import File
from app.models.chunk import Chunk
from app.models.summary import TopicSummary, UnitSummary
from app.models.unit_processing_state import UnitProcessingState

__all__ = [
    "User",
    "Subject",
    "Unit",
    "Topic",
    "File",
    "Chunk",
    "TopicSummary",
    "UnitSummary",
    "UnitProcessingState",
]
