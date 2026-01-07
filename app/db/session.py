"""
Database session management.

This module provides:
- SQLAlchemy engine configuration
- Session factory
- Dependency injection for FastAPI routes
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Create engine with appropriate settings
# SQLite requires check_same_thread=False for FastAPI's async nature
# This connect_args is only needed for SQLite and will be ignored by PostgreSQL
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,  # Log SQL statements in debug mode
    pool_pre_ping=True,  # Verify connections before use
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    
    Yields a session and ensures proper cleanup after the request.
    Use with FastAPI's Depends() for automatic injection.
    
    Yields:
        Session: SQLAlchemy session instance.
        
    Example:
        @router.get("/items")
        def get_items(db: DbSession):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Type alias for dependency injection
DbSession = Annotated[Session, Depends(get_db)]
