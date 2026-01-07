"""
Topic API routes.

Provides CRUD endpoints for topics within units.
Topics are the leaf nodes of the academic hierarchy.
"""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.topic import TopicCreate, TopicList, TopicRead
from app.services import subject_service, unit_service, topic_service

router = APIRouter(
    prefix="/subjects/{subject_id}/units/{unit_id}/topics",
    tags=["Topics"],
)


def validate_unit_ownership(
    db: DbSession,
    subject_id: int,
    unit_id: int,
    user_id: int,
) -> None:
    """
    Validate that subject and unit exist and belong to the user.
    
    Raises:
        HTTPException: If subject or unit not found or not owned by user.
    """
    # Validate subject ownership
    subject = subject_service.get_subject_for_user(db, subject_id, user_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )
    
    # Validate unit belongs to subject
    unit = unit_service.get_unit_for_subject(db, unit_id, subject_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )


@router.post(
    "",
    response_model=TopicRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Topic",
    description="Create a new topic within a unit.",
)
def create_topic(
    db: DbSession,
    current_user: CurrentUser,
    subject_id: int,
    unit_id: int,
    topic_in: TopicCreate,
) -> TopicRead:
    """
    Create a new topic within a unit.
    
    Example Request:
        POST /api/v1/subjects/1/units/1/topics
        {"title": "Binary Search Algorithm"}
        
    Example Response:
        {
            "id": 1,
            "unit_id": 1,
            "title": "Binary Search Algorithm",
            "created_at": "2026-01-06T12:00:00"
        }
    """
    validate_unit_ownership(db, subject_id, unit_id, current_user.id)
    topic = topic_service.create_topic(db, topic_in, unit_id)
    return TopicRead.model_validate(topic)


@router.get(
    "",
    response_model=TopicList,
    summary="List Topics",
    description="List all topics for a unit.",
)
def list_topics(
    db: DbSession,
    current_user: CurrentUser,
    subject_id: int,
    unit_id: int,
) -> TopicList:
    """
    List all topics for a unit.
    
    Example Response:
        {
            "topics": [
                {"id": 1, "unit_id": 1, "title": "Binary Search", ...},
                {"id": 2, "unit_id": 1, "title": "Linear Search", ...}
            ],
            "count": 2
        }
    """
    validate_unit_ownership(db, subject_id, unit_id, current_user.id)
    topics = topic_service.list_topics_for_unit(db, unit_id)
    return TopicList(
        topics=[TopicRead.model_validate(t) for t in topics],
        count=len(topics),
    )


@router.get(
    "/{topic_id}",
    response_model=TopicRead,
    summary="Get Topic",
    description="Get a specific topic by ID.",
)
def get_topic(
    db: DbSession,
    current_user: CurrentUser,
    subject_id: int,
    unit_id: int,
    topic_id: int,
) -> TopicRead:
    """
    Get a specific topic by ID.
    
    Validates the full ownership chain:
    user -> subject -> unit -> topic
    """
    validate_unit_ownership(db, subject_id, unit_id, current_user.id)
    topic = topic_service.get_topic_for_unit(db, topic_id, unit_id)
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )
    return TopicRead.model_validate(topic)
