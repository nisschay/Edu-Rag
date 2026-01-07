"""
User service for user-related database operations.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """
    Get a user by ID.
    
    Args:
        db: Database session.
        user_id: User ID to look up.
        
    Returns:
        User if found, None otherwise.
    """
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Get a user by email address.
    
    Args:
        db: Database session.
        email: Email address to look up.
        
    Returns:
        User if found, None otherwise.
    """
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session.
        user_in: User creation data.
        
    Returns:
        Created user instance.
    """
    user = User(email=user_in.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_user(db: Session, email: str) -> User:
    """
    Get existing user or create new one.
    
    Used for OAuth flow where users are auto-created on first login.
    
    Args:
        db: Database session.
        email: User email address.
        
    Returns:
        Existing or newly created user.
    """
    user = get_user_by_email(db, email)
    if user is None:
        user = create_user(db, UserCreate(email=email))
    return user
