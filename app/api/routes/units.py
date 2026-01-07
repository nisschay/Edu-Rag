"""
Unit API routes.

Provides CRUD endpoints for units within subjects.
Units are ordered and contain topics.
"""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.unit import UnitCreate, UnitList, UnitRead
from app.services import subject_service, unit_service

router = APIRouter(prefix="/subjects/{subject_id}/units", tags=["Units"])


def validate_subject_ownership(
    db: DbSession,
    subject_id: int,
    user_id: int,
) -> None:
    """
    Validate that a subject exists and belongs to the user.
    
    Raises:
        HTTPException: If subject not found or not owned by user.
    """
    subject = subject_service.get_subject_for_user(db, subject_id, user_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )


@router.post(
    "",
    response_model=UnitRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Unit",
    description="Create a new unit within a subject.",
)
def create_unit(
    db: DbSession,
    current_user: CurrentUser,
    subject_id: int,
    unit_in: UnitCreate,
) -> UnitRead:
    """
    Create a new unit within a subject.
    
    If unit_number is not provided, it will be auto-assigned
    as the next number in sequence.
    
    Example Request:
        POST /api/v1/subjects/1/units
        {"title": "Introduction to Algorithms"}
        
    Example Response:
        {
            "id": 1,
            "subject_id": 1,
            "unit_number": 1,
            "title": "Introduction to Algorithms",
            "created_at": "2026-01-06T12:00:00"
        }
    """
    validate_subject_ownership(db, subject_id, current_user.id)
    unit = unit_service.create_unit(db, unit_in, subject_id)
    return UnitRead.model_validate(unit)


@router.get(
    "",
    response_model=UnitList,
    summary="List Units",
    description="List all units for a subject, ordered by unit number.",
)
def list_units(
    db: DbSession,
    current_user: CurrentUser,
    subject_id: int,
) -> UnitList:
    """
    List all units for a subject.
    
    Units are returned in order by unit_number.
    
    Example Response:
        {
            "units": [
                {"id": 1, "subject_id": 1, "unit_number": 1, "title": "Intro", ...},
                {"id": 2, "subject_id": 1, "unit_number": 2, "title": "Basics", ...}
            ],
            "count": 2
        }
    """
    validate_subject_ownership(db, subject_id, current_user.id)
    units = unit_service.list_units_for_subject(db, subject_id)
    return UnitList(
        units=[UnitRead.model_validate(u) for u in units],
        count=len(units),
    )


@router.get(
    "/{unit_id}",
    response_model=UnitRead,
    summary="Get Unit",
    description="Get a specific unit by ID.",
)
def get_unit(
    db: DbSession,
    current_user: CurrentUser,
    subject_id: int,
    unit_id: int,
) -> UnitRead:
    """
    Get a specific unit by ID.
    
    Validates that the subject belongs to the authenticated user
    and that the unit belongs to the subject.
    """
    validate_subject_ownership(db, subject_id, current_user.id)
    unit = unit_service.get_unit_for_subject(db, unit_id, subject_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )
    return UnitRead.model_validate(unit)
