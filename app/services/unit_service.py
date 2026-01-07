"""
Unit service for unit-related database operations.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.unit import Unit
from app.schemas.unit import UnitCreate


def get_unit_by_id(db: Session, unit_id: int) -> Unit | None:
    """
    Get a unit by ID.
    
    Args:
        db: Database session.
        unit_id: Unit ID to look up.
        
    Returns:
        Unit if found, None otherwise.
    """
    return db.get(Unit, unit_id)


def get_unit_for_subject(
    db: Session,
    unit_id: int,
    subject_id: int,
) -> Unit | None:
    """
    Get a unit by ID, ensuring it belongs to the specified subject.
    
    Args:
        db: Database session.
        unit_id: Unit ID to look up.
        subject_id: Subject ID that must own the unit.
        
    Returns:
        Unit if found and belongs to subject, None otherwise.
    """
    stmt = select(Unit).where(
        Unit.id == unit_id,
        Unit.subject_id == subject_id,
    )
    return db.scalar(stmt)


def list_units_for_subject(db: Session, subject_id: int) -> list[Unit]:
    """
    List all units for a subject, ordered by unit_number.
    
    Args:
        db: Database session.
        subject_id: Subject ID to list units for.
        
    Returns:
        List of units ordered by unit_number.
    """
    stmt = (
        select(Unit)
        .where(Unit.subject_id == subject_id)
        .order_by(Unit.unit_number)
    )
    return list(db.scalars(stmt).all())


def get_next_unit_number(db: Session, subject_id: int) -> int:
    """
    Get the next available unit number for a subject.
    
    Args:
        db: Database session.
        subject_id: Subject ID to check.
        
    Returns:
        Next unit number (max + 1, or 1 if no units exist).
    """
    stmt = select(func.max(Unit.unit_number)).where(Unit.subject_id == subject_id)
    max_num = db.scalar(stmt)
    return (max_num or 0) + 1


def create_unit(
    db: Session,
    unit_in: UnitCreate,
    subject_id: int,
) -> Unit:
    """
    Create a new unit for a subject.
    
    Args:
        db: Database session.
        unit_in: Unit creation data.
        subject_id: ID of the parent subject.
        
    Returns:
        Created unit instance.
    """
    # Auto-assign unit_number if not provided
    unit_number = unit_in.unit_number
    if unit_number is None:
        unit_number = get_next_unit_number(db, subject_id)
    
    unit = Unit(
        title=unit_in.title,
        unit_number=unit_number,
        subject_id=subject_id,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit
