"""
SQLAlchemy declarative base configuration.

This module provides the base class for all ORM models.
All models should inherit from Base to be properly registered
with SQLAlchemy's metadata system.

Future models will include:
- Subject (Phase 1)
- Unit (Phase 1)
- Topic (Phase 1)
- User (Phase 1)
- Document/Chunk (Phase 2)
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    
    All database models should inherit from this class.
    This ensures proper metadata registration and enables
    features like automatic table creation.
    
    Example:
        class Subject(Base):
            __tablename__ = "subjects"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(255))
    """
    
    pass
