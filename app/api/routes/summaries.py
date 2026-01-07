"""
Summary API routes.

Provides endpoints for generating and managing hierarchical summaries:
- Topic summaries: 200-300 tokens from raw chunks
- Unit summaries: 300-500 tokens from topic summaries
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.summary import (
    TopicSummaryResponse,
    UnitSummaryResponse,
    EmbedSummariesResponse,
)
from app.services import subject_service, unit_service, topic_service, summary_service

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _validate_topic_ownership(
    db: DbSession,
    user_id: int,
    subject_id: int,
    unit_id: int,
    topic_id: int,
) -> tuple:
    """
    Validate that user owns the topic through the hierarchy.
    
    Returns:
        Tuple of (subject, unit, topic) if valid.
        
    Raises:
        HTTPException: If not found or not owned.
    """
    subject = subject_service.get_subject_for_user(db, subject_id, user_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )
    
    unit = unit_service.get_unit_for_subject(db, unit_id, subject_id)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )
    
    topic = topic_service.get_topic_for_unit(db, topic_id, unit_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )
    
    return subject, unit, topic


def _validate_unit_ownership(
    db: DbSession,
    user_id: int,
    subject_id: int,
    unit_id: int,
) -> tuple:
    """
    Validate that user owns the unit through the hierarchy.
    
    Returns:
        Tuple of (subject, unit) if valid.
        
    Raises:
        HTTPException: If not found or not owned.
    """
    subject = subject_service.get_subject_for_user(db, subject_id, user_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )
    
    unit = unit_service.get_unit_for_subject(db, unit_id, subject_id)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )
    
    return subject, unit


# =============================================================================
# TOPIC SUMMARY ENDPOINTS
# =============================================================================

@router.post(
    "/subjects/{subject_id}/units/{unit_id}/topics/{topic_id}/summarize",
    response_model=TopicSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Topic Summary",
    description="Generate or regenerate a summary for a topic from its chunks.",
)
def generate_topic_summary(
    subject_id: int,
    unit_id: int,
    topic_id: int,
    db: DbSession,
    current_user: CurrentUser,
    force: bool = False,
) -> TopicSummaryResponse:
    """
    Generate a summary for a topic.
    
    This endpoint:
    1. Retrieves all chunks for the topic
    2. Uses LLM to generate a 200-300 token summary
    3. Stores the summary in the database
    
    If a summary already exists and force=False, returns existing.
    If force=True, regenerates the summary.
    
    Args:
        subject_id: Subject ID.
        unit_id: Unit ID.
        topic_id: Topic ID.
        force: Force regeneration (default False).
        
    Returns:
        TopicSummaryResponse with summary details.
    """
    logger.info(
        f"Topic summary request: user={current_user.id}, topic={topic_id}, force={force}"
    )
    
    # Validate ownership
    subject, unit, topic = _validate_topic_ownership(
        db, current_user.id, subject_id, unit_id, topic_id
    )
    
    try:
        summary, regenerated = summary_service.generate_topic_summary(
            db=db,
            topic=topic,
            user_id=current_user.id,
            subject_id=subject_id,
            unit_id=unit_id,
            topic_title=topic.title,
            subject_name=subject.name,
            force_regenerate=force,
        )
    except ValueError as e:
        logger.warning(f"Topic summary generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    logger.info(
        f"Topic summary {'regenerated' if regenerated else 'returned'}: "
        f"id={summary.id}, tokens={summary.token_count}"
    )
    
    return TopicSummaryResponse(
        id=summary.id,
        topic_id=summary.topic_id,
        topic_title=topic.title,
        summary_text=summary.summary_text,
        token_count=summary.token_count,
        source_chunk_count=summary.source_chunk_count,
        has_embedding=summary.embedding_id is not None,
        regenerated=regenerated,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
    )


@router.get(
    "/subjects/{subject_id}/units/{unit_id}/topics/{topic_id}/summary",
    response_model=TopicSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Topic Summary",
    description="Retrieve the summary for a topic if it exists.",
)
def get_topic_summary(
    subject_id: int,
    unit_id: int,
    topic_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> TopicSummaryResponse:
    """
    Get the existing summary for a topic.
    
    Returns 404 if no summary exists.
    """
    logger.info(f"Get topic summary: user={current_user.id}, topic={topic_id}")
    
    # Validate ownership
    subject, unit, topic = _validate_topic_ownership(
        db, current_user.id, subject_id, unit_id, topic_id
    )
    
    summary = summary_service.get_topic_summary(db, topic_id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic summary not found. Generate one first.",
        )
    
    return TopicSummaryResponse(
        id=summary.id,
        topic_id=summary.topic_id,
        topic_title=topic.title,
        summary_text=summary.summary_text,
        token_count=summary.token_count,
        source_chunk_count=summary.source_chunk_count,
        has_embedding=summary.embedding_id is not None,
        regenerated=False,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
    )


# =============================================================================
# UNIT SUMMARY ENDPOINTS
# =============================================================================

@router.post(
    "/subjects/{subject_id}/units/{unit_id}/summarize",
    response_model=UnitSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Unit Summary",
    description="Generate or regenerate a summary for a unit from its topic summaries.",
)
def generate_unit_summary(
    subject_id: int,
    unit_id: int,
    db: DbSession,
    current_user: CurrentUser,
    force: bool = False,
) -> UnitSummaryResponse:
    """
    Generate a summary for a unit.
    
    This endpoint:
    1. Retrieves all topic summaries for the unit
    2. Uses LLM to generate a 300-500 token summary
    3. Stores the summary in the database
    
    Requires topic summaries to exist first.
    If a summary already exists and force=False, returns existing.
    If force=True, regenerates the summary.
    
    Args:
        subject_id: Subject ID.
        unit_id: Unit ID.
        force: Force regeneration (default False).
        
    Returns:
        UnitSummaryResponse with summary details.
    """
    logger.info(
        f"Unit summary request: user={current_user.id}, unit={unit_id}, force={force}"
    )
    
    # Validate ownership
    subject, unit = _validate_unit_ownership(
        db, current_user.id, subject_id, unit_id
    )
    
    try:
        summary, regenerated = summary_service.generate_unit_summary(
            db=db,
            unit=unit,
            user_id=current_user.id,
            subject_id=subject_id,
            subject_name=subject.name,
            force_regenerate=force,
        )
    except ValueError as e:
        logger.warning(f"Unit summary generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    logger.info(
        f"Unit summary {'regenerated' if regenerated else 'returned'}: "
        f"id={summary.id}, tokens={summary.token_count}"
    )
    
    return UnitSummaryResponse(
        id=summary.id,
        unit_id=summary.unit_id,
        unit_title=unit.title,
        summary_text=summary.summary_text,
        token_count=summary.token_count,
        source_topic_count=summary.source_topic_count,
        has_embedding=summary.embedding_id is not None,
        regenerated=regenerated,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
    )


@router.get(
    "/subjects/{subject_id}/units/{unit_id}/summary",
    response_model=UnitSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Unit Summary",
    description="Retrieve the summary for a unit if it exists.",
)
def get_unit_summary(
    subject_id: int,
    unit_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> UnitSummaryResponse:
    """
    Get the existing summary for a unit.
    
    Returns 404 if no summary exists.
    """
    logger.info(f"Get unit summary: user={current_user.id}, unit={unit_id}")
    
    # Validate ownership
    subject, unit = _validate_unit_ownership(
        db, current_user.id, subject_id, unit_id
    )
    
    summary = summary_service.get_unit_summary(db, unit_id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit summary not found. Generate one first.",
        )
    
    return UnitSummaryResponse(
        id=summary.id,
        unit_id=summary.unit_id,
        unit_title=unit.title,
        summary_text=summary.summary_text,
        token_count=summary.token_count,
        source_topic_count=summary.source_topic_count,
        has_embedding=summary.embedding_id is not None,
        regenerated=False,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
    )


# =============================================================================
# EMBEDDING ENDPOINTS
# =============================================================================

@router.post(
    "/subjects/{subject_id}/units/{unit_id}/embed-summaries",
    response_model=EmbedSummariesResponse,
    status_code=status.HTTP_200_OK,
    summary="Embed Unit Summaries",
    description="Embed all summaries (topic + unit) for a unit into the summary vector store.",
)
def embed_unit_summaries(
    subject_id: int,
    unit_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> EmbedSummariesResponse:
    """
    Embed all summaries for a unit.
    
    This endpoint:
    1. Embeds all topic summaries for the unit
    2. Embeds the unit summary
    3. Stores embeddings in the summary FAISS index
    
    Summaries must be generated first.
    Already-embedded summaries are skipped.
    """
    logger.info(f"Embed summaries request: user={current_user.id}, unit={unit_id}")
    
    # Validate ownership
    subject, unit = _validate_unit_ownership(
        db, current_user.id, subject_id, unit_id
    )
    
    newly_embedded, already_embedded = summary_service.embed_all_summaries_for_unit(
        db, unit_id
    )
    
    logger.info(
        f"Embedding complete: {newly_embedded} new, {already_embedded} existing"
    )
    
    return EmbedSummariesResponse(
        unit_id=unit_id,
        newly_embedded=newly_embedded,
        already_embedded=already_embedded,
    )
