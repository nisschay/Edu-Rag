"""
Debug API routes for RAG operations.

These endpoints are for testing and validation only:
- Trigger chunking for a topic
- Trigger embedding for a topic
- Test retrieval with a query

All operations are scoped to user/subject/unit/topic.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.models.topic import Topic
from app.models.unit import Unit
from app.models.subject import Subject
from app.schemas.chunk import (
    ChunkList,
    ChunkingResponse,
    EmbeddingResponse,
    RetrievalRequest,
    RetrievalResponse,
    ChunkWithScore,
)
from app.services import chunk_service, topic_service, unit_service, subject_service
from app.services.retrieval_service import embed_topic_chunks, retrieve_chunks

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_topic_ownership(
    db: DbSession,
    user_id: int,
    subject_id: int,
    unit_id: int,
    topic_id: int,
) -> tuple[Subject, Unit, Topic]:
    """
    Validate that user owns the topic through the hierarchy.
    
    Returns:
        Tuple of (subject, unit, topic) if valid.
        
    Raises:
        HTTPException: If not found or not owned.
    """
    # Check subject ownership
    subject = subject_service.get_subject_for_user(db, subject_id, user_id)
    if not subject:
        logger.warning(f"Subject {subject_id} not found for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )
    
    # Check unit belongs to subject
    unit = unit_service.get_unit_for_subject(db, unit_id, subject_id)
    if not unit:
        logger.warning(f"Unit {unit_id} not found in subject {subject_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )
    
    # Check topic belongs to unit
    topic = topic_service.get_topic_for_unit(db, topic_id, unit_id)
    if not topic:
        logger.warning(f"Topic {topic_id} not found in unit {unit_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )
    
    return subject, unit, topic


@router.post(
    "/subjects/{subject_id}/units/{unit_id}/topics/{topic_id}/chunk",
    response_model=ChunkingResponse,
    status_code=status.HTTP_200_OK,
)
def trigger_chunking(
    subject_id: int,
    unit_id: int,
    topic_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ChunkingResponse:
    """
    Trigger chunking for all files in a topic.
    
    This endpoint:
    1. Validates ownership through the hierarchy
    2. Deletes existing chunks for the topic's files
    3. Re-chunks all files with extracted text
    4. Returns chunking statistics
    
    Debug endpoint for testing chunking logic.
    """
    logger.info(
        f"Chunking request: user={current_user.id}, subject={subject_id}, "
        f"unit={unit_id}, topic={topic_id}"
    )
    
    # Validate ownership
    subject, unit, topic = _validate_topic_ownership(
        db, current_user.id, subject_id, unit_id, topic_id
    )
    
    # Process topic into chunks
    files_processed, chunks_created, total_tokens = chunk_service.process_topic_into_chunks(
        db=db,
        topic=topic,
        user_id=current_user.id,
        subject_id=subject_id,
        unit_id=unit_id,
    )
    
    logger.info(
        f"Chunking complete: {files_processed} files, {chunks_created} chunks, "
        f"{total_tokens} tokens"
    )
    
    return ChunkingResponse(
        topic_id=topic_id,
        files_processed=files_processed,
        chunks_created=chunks_created,
        total_tokens=total_tokens,
    )


@router.post(
    "/subjects/{subject_id}/units/{unit_id}/topics/{topic_id}/embed",
    response_model=EmbeddingResponse,
    status_code=status.HTTP_200_OK,
)
def trigger_embedding(
    subject_id: int,
    unit_id: int,
    topic_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> EmbeddingResponse:
    """
    Trigger embedding for all chunks in a topic.
    
    This endpoint:
    1. Validates ownership through the hierarchy
    2. Finds chunks without embeddings
    3. Generates embeddings using OpenAI
    4. Stores embeddings in FAISS
    5. Returns embedding statistics
    
    Debug endpoint for testing embedding logic.
    Requires OPENAI_API_KEY to be configured.
    """
    logger.info(
        f"Embedding request: user={current_user.id}, subject={subject_id}, "
        f"unit={unit_id}, topic={topic_id}"
    )
    
    # Validate ownership
    subject, unit, topic = _validate_topic_ownership(
        db, current_user.id, subject_id, unit_id, topic_id
    )
    
    try:
        # Embed chunks
        chunks_embedded, already_embedded = embed_topic_chunks(
            db=db,
            topic_id=topic_id,
            user_id=current_user.id,
            subject_id=subject_id,
            unit_id=unit_id,
        )
        
        logger.info(
            f"Embedding complete: {chunks_embedded} embedded, "
            f"{already_embedded} already embedded"
        )
        
        return EmbeddingResponse(
            topic_id=topic_id,
            chunks_embedded=chunks_embedded,
            already_embedded=already_embedded,
        )
        
    except ValueError as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/subjects/{subject_id}/units/{unit_id}/topics/{topic_id}/retrieve",
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
)
def test_retrieval(
    subject_id: int,
    unit_id: int,
    topic_id: int,
    request: RetrievalRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> RetrievalResponse:
    """
    Test retrieval with a query.
    
    This endpoint:
    1. Validates ownership through the hierarchy
    2. Embeds the query using OpenAI
    3. Searches FAISS for similar chunks
    4. Filters by user/subject/unit/topic
    5. Returns top-k matching chunks
    
    Debug endpoint for testing retrieval logic.
    Requires OPENAI_API_KEY to be configured.
    """
    logger.info(
        f"Retrieval request: user={current_user.id}, subject={subject_id}, "
        f"unit={unit_id}, topic={topic_id}, query='{request.query[:50]}...'"
    )
    
    # Validate ownership
    subject, unit, topic = _validate_topic_ownership(
        db, current_user.id, subject_id, unit_id, topic_id
    )
    
    try:
        # Retrieve chunks
        retrieved = retrieve_chunks(
            db=db,
            user_id=current_user.id,
            subject_id=subject_id,
            unit_id=unit_id,
            topic_id=topic_id,
            query=request.query,
            top_k=request.top_k,
        )
        
        logger.info(f"Retrieved {len(retrieved)} chunks")
        
        # Convert to response format
        chunks = [
            ChunkWithScore(
                chunk_id=r.chunk_id,
                text=r.text,
                score=r.score,
                source_file_id=r.source_file_id,
                topic_id=r.topic_id,
                unit_id=r.unit_id,
                subject_id=r.subject_id,
            )
            for r in retrieved
        ]
        
        return RetrievalResponse(
            query=request.query,
            topic_id=topic_id,
            chunks_found=len(chunks),
            chunks=chunks,
        )
        
    except ValueError as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/subjects/{subject_id}/units/{unit_id}/topics/{topic_id}/chunks",
    response_model=list[ChunkList],
    status_code=status.HTTP_200_OK,
)
def list_chunks(
    subject_id: int,
    unit_id: int,
    topic_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> list[ChunkList]:
    """
    List all chunks for a topic.
    
    Debug endpoint to view chunking results.
    """
    logger.info(
        f"List chunks request: user={current_user.id}, subject={subject_id}, "
        f"unit={unit_id}, topic={topic_id}"
    )
    
    # Validate ownership
    _validate_topic_ownership(db, current_user.id, subject_id, unit_id, topic_id)
    
    # Get chunks
    chunks = chunk_service.list_chunks_for_topic(db, topic_id)
    
    # Convert to response format
    return [
        ChunkList(
            id=c.id,
            chunk_index=c.chunk_index,
            token_count=c.token_count,
            text_preview=c.text[:100] + "..." if len(c.text) > 100 else c.text,
            has_embedding=c.embedding_id is not None,
        )
        for c in chunks
    ]
