"""
Database module providing SQLAlchemy integration.

This module provides:
- Database engine and session management (session.py)
- Base declarative class for models (base.py)
"""

from app.db.base import Base
from app.db.session import get_db

__all__ = ["Base", "get_db"]
