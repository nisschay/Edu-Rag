"""
Chat API route.

Provides the main ChatGPT-style endpoint for educational Q&A:
- Intent classification
- RAG-based retrieval
- LLM response generation
- Source attribution
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.chat import ChatRequest, ChatResponse, SourceReference
from app.services import subject_service, unit_service, topic_service, chat_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/subjects/{subject_id}/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with RAG",
    description="Ask a question and get a response using RAG from uploaded materials.",
)
def chat(
    subject_id: int,
    db: DbSession,
    current_user: CurrentUser,
    request: ChatRequest,
) -> ChatResponse:
    """
    Process a chat message with RAG.
    
    This endpoint:
    1. Classifies user intent (teach, explain, detail, revise, questions)
    2. Retrieves appropriate context based on intent:
       - teach_from_start: Unit summaries (broad)
       - explain_topic: Topic summaries (medium)
       - explain_detail: Raw chunks (detailed)
       - revise: Unit summaries (quick review)
       - generate_questions: Topic summaries (structured)
    3. Generates response using LLM with context
    4. Returns response with source attribution
    """
    logger.info(
        f"Chat request: user={current_user.id}, subject={subject_id}, "
        f"unit={request.unit_id}, topic={request.topic_id}"
    )
    logger.info(f"Message: {request.message[:200]}...")
    
    # Validate subject ownership
    subject = subject_service.get_subject_for_user(db, subject_id, current_user.id)
    if not subject:
        logger.warning(f"Subject {subject_id} not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )
    
    # Validate unit if provided
    if request.unit_id:
        unit = unit_service.get_unit_for_subject(db, request.unit_id, subject_id)
        if not unit:
            logger.warning(f"Unit {request.unit_id} not found in subject {subject_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found",
            )
    
    # Validate topic if provided
    if request.topic_id:
        if not request.unit_id:
            # Get unit from topic
            topic = topic_service.get_topic(db, request.topic_id)
            if topic:
                request.unit_id = topic.unit_id
        
        topic = topic_service.get_topic_for_unit(db, request.topic_id, request.unit_id)
        if not topic:
            logger.warning(f"Topic {request.topic_id} not found in unit {request.unit_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found",
            )
    
    # Process chat
    try:
        result = chat_service.chat(
            db=db,
            user_id=current_user.id,
            subject_id=subject_id,
            message=request.message,
            unit_id=request.unit_id,
            topic_id=request.topic_id,
        )
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request",
        )
    
    # Build response
    sources = [
        SourceReference(
            source_type=s.source_type,
            source_id=s.source_id,
            score=s.score or 0.0,
            preview="",  # Could add text preview here if needed
        )
        for s in result.sources
    ]
    
    logger.info(
        f"Chat response: intent={result.intent}, sources={len(sources)}, "
        f"context_tokens={result.context_tokens}"
    )
    
    return ChatResponse(
        answer=result.answer,
        intent=result.intent,
        sources=sources,
        subject_id=subject_id,
        unit_id=request.unit_id,
        topic_id=request.topic_id,
    )
