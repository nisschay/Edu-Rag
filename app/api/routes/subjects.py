"""
Subject API routes.

Provides CRUD endpoints for subjects.
Subjects belong to users and contain units.
"""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.subject import SubjectCreate, SubjectList, SubjectRead
from app.services import subject_service

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post(
    "",
    response_model=SubjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Subject",
    description="Create a new subject for the authenticated user.",
)
def create_subject(
    db: DbSession,
    current_user: CurrentUser,
    subject_in: SubjectCreate,
) -> SubjectRead:
    """
    Create a new subject.
    
    The subject will be owned by the authenticated user.
    
    Example Request:
        POST /api/v1/subjects
        {"name": "Introduction to Computer Science"}
        
    Example Response:
        {
            "id": 1,
            "user_id": 1,
            "name": "Introduction to Computer Science",
            "created_at": "2026-01-06T12:00:00"
        }
    """
    subject = subject_service.create_subject(db, subject_in, current_user.id)
    return SubjectRead.model_validate(subject)


@router.get(
    "",
    response_model=SubjectList,
    summary="List Subjects",
    description="List all subjects for the authenticated user.",
)
def list_subjects(
    db: DbSession,
    current_user: CurrentUser,
) -> SubjectList:
    """
    List all subjects owned by the authenticated user.
    
    Example Response:
        {
            "subjects": [
                {"id": 1, "user_id": 1, "name": "CS 101", ...},
                {"id": 2, "user_id": 1, "name": "Math 201", ...}
            ],
            "count": 2
        }
    """
    subjects = subject_service.list_subjects_for_user(db, current_user.id)
    return SubjectList(
        subjects=[SubjectRead.model_validate(s) for s in subjects],
        count=len(subjects),
    )


@router.get(
    "/{subject_id}",
    response_model=SubjectRead,
    summary="Get Subject",
    description="Get a specific subject by ID.",
)
def get_subject(
    db: DbSession,
    current_user: CurrentUser,
    subject_id: int,
) -> SubjectRead:
    """
    Get a specific subject by ID.
    
    Validates that the subject belongs to the authenticated user.
    """
    subject = subject_service.get_subject_for_user(db, subject_id, current_user.id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )
    return SubjectRead.model_validate(subject)
