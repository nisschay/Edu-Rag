"""
Shared dependencies for API routes.

This module centralizes common dependencies used across routes:
- Database session injection
- Settings injection
- Current user injection (stub for auth)
- Ownership validation helpers
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings
from app.db.session import DbSession, get_db
from app.models.user import User
from app.services import user_service

# Re-export for convenient imports
__all__ = [
    "DbSession",
    "get_db",
    "SettingsDep",
    "get_settings",
    "get_current_user",
    "CurrentUser",
]

# Type alias for settings dependency
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_current_user(
    db: DbSession,
    x_user_id: int = Header(..., description="User ID (auth stub)"),
) -> User:
    """
    Get the current authenticated user.
    
    This is a stub implementation. In production, this would:
    1. Validate a JWT or session token
    2. Extract user identity from the token
    3. Look up the user in the database
    
    For now, we accept a user_id header to simulate authentication.
    
    Args:
        db: Database session.
        x_user_id: User ID from header (temporary auth stub).
        
    Returns:
        User: The authenticated user.
        
    Raises:
        HTTPException: If user not found.
    """
    user = user_service.get_user_by_id(db, x_user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


# Type alias for current user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]
