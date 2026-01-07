"""
Subject service for subject-related database operations.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.schemas.subject import SubjectCreate


def get_subject_by_id(db: Session, subject_id: int) -> Subject | None:
    """
    Get a subject by ID.
    
    Args:
        db: Database session.
        subject_id: Subject ID to look up.
        
    Returns:
        Subject if found, None otherwise.
    """
    return db.get(Subject, subject_id)


def get_subject_for_user(
    db: Session,
    subject_id: int,
    user_id: int,
) -> Subject | None:
    """
    Get a subject by ID, ensuring it belongs to the specified user.
    
    Args:
        db: Database session.
        subject_id: Subject ID to look up.
        user_id: User ID that must own the subject.
        
    Returns:
        Subject if found and owned by user, None otherwise.
    """
    stmt = select(Subject).where(
        Subject.id == subject_id,
        Subject.user_id == user_id,
    )
    return db.scalar(stmt)


def list_subjects_for_user(db: Session, user_id: int) -> list[Subject]:
    """
    List all subjects for a user.
    
    Args:
        db: Database session.
        user_id: User ID to list subjects for.
        
    Returns:
        List of subjects owned by the user.
    """
    stmt = select(Subject).where(Subject.user_id == user_id).order_by(Subject.created_at)
    return list(db.scalars(stmt).all())


def create_subject(
    db: Session,
    subject_in: SubjectCreate,
    user_id: int,
) -> Subject:
    """
    Create a new subject for a user.
    
    Args:
        db: Database session.
        subject_in: Subject creation data.
        user_id: ID of the owning user.
        
    Returns:
        Created subject instance.
    """
    subject = Subject(
        name=subject_in.name,
        user_id=user_id,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject
