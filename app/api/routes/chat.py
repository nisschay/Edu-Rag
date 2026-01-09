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
            
    # --- STRICT GATEKEEPING ---
    # Convert request.unit_id to int if present for consistency
    target_unit_id = request.unit_id
    if target_unit_id:
        # We need to fetch the unit object to check state, if we haven't already
        # We might have fetched it for validation but didn't keep reference.
        # Let's re-fetch or rely on relationship if we had `unit` object (we verified existence but didn't load state?)
        # `unit` variable might be local in `if request.unit_id` block.
        
        # Let's get Unit including State
        unit_model = unit_service.get_unit_for_subject(db, target_unit_id, subject_id)
        if not unit_model:
             raise HTTPException(status_code=404, detail="Unit not found")
        
        state = unit_model.processing_state
        if not state:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No material uploaded yet (State missing)"
            )
            
        # 1. State Readiness Check
        if state.status != "ready":
            msg = "Material is still processing"
            if state.status == "failed":
                msg = f"Material failed to process: {state.last_error or 'Unknown error'}"
            elif state.status == "empty":
                msg = "No material uploaded yet"
            elif state.status == "uploaded":
                 msg = "Material uploaded but not processed yet"
            
            # Deterministic, blocking response (using 400 as standard for "Bad Request" logic)
            logger.warning(f"Chat Blocked: Unit {target_unit_id} status is {state.status}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

        # 2. Content Check
        # Must have chunks or be marked as having extracted text at least (though chunks are needed for RAG)
        if state.chunk_count == 0:
             # Could be a summary-only unit? But usually we need chunks.
             # If no chunks, RAG will be empty.
             logger.warning(f"Chat Blocked: Unit {target_unit_id} has 0 chunks")
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No content available in this unit yet")

    # 3. Prompt Check
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

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


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Flexible Chat with RAG",
    description="Ask a question with optional subject/unit/topic scope. Provides graceful fallbacks.",
)
def chat_flexible_endpoint(
    db: DbSession,
    current_user: CurrentUser,
    request: ChatRequest,
) -> ChatResponse:
    """
    Process a chat message with flexible scoping.
    
    This endpoint:
    1. Accepts optional subject, unit, and topic IDs
    2. Infers appropriate context scope
    3. Handles missing content gracefully
    4. Never returns 500 for valid requests
    """
    logger.info(
        f"Flexible chat request: user={current_user.id}, "
        f"subject={request.subject_id}, unit={request.unit_id}, topic={request.topic_id}"
    )
    
    # --- STRICT GATEKEEPING ---
    # Even for flexible chat, if a unit implies context, we must validate it.
    target_unit_id = request.unit_id
    
    # If topic provided but no unit, find unit
    if request.topic_id and not target_unit_id:
        topic = topic_service.get_topic(db, request.topic_id)
        if topic:
            target_unit_id = topic.unit_id
            
    if target_unit_id:
        # Get Unit including State
        unit_model = unit_service.get_unit_for_subject(db, target_unit_id, request.subject_id or 0) 
        # Note: subject_id might be None in request, so we might need to be careful. 
        # But if unit_id is valid, we can fetch it directly.
        # unit_service.get_unit_for_subject usually requires subject_id. 
        # Let's just use db.get(Unit, id) if we are sure, but ownership validation is good.
        # However, ChatRequest flexible might not have subject_id. 
        # If we have unit_id, we can just check THAT unit's state.
        
        unit_model = db.get(Unit, target_unit_id)
        
        if unit_model:
            state = unit_model.processing_state
            if not state:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No material uploaded yet (State missing)"
                )
            
            # 1. State Readiness
            if state.status != "ready":
                msg = "Material is still processing"
                if state.status == "failed":
                    msg = f"Material failed to process: {state.last_error or 'Unknown error'}"
                elif state.status == "empty":
                    msg = "No material uploaded yet"
                elif state.status == "uploaded":
                    msg = "Material uploaded but not processed yet"
                
                logger.warning(f"Flexible Chat Blocked: Unit {target_unit_id} status is {state.status}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

            # 2. Content Check
            if state.chunk_count == 0:
                logger.warning(f"Flexible Chat Blocked: Unit {target_unit_id} has 0 chunks")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No content available in this unit yet")

    # 3. Prompt Check
    if not request.message or not request.message.strip():
        # For flexible, maybe we're nicer? No, user said "Eliminate ALL 400 errors" likely from LLM.
        # Sending empty string to LLM causes 400. So block it here.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    try:
        result = chat_service.chat_flexible(
            db=db,
            user_id=current_user.id,
            message=request.message,
            subject_id=request.subject_id,
            unit_id=request.unit_id,
            topic_id=request.topic_id,
        )
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        # Even in case of error, try to return a friendly message
        result = chat_service.ChatResult(
            answer="I encountered a temporary issue processing your request. Please try again in a moment.",
            intent="explain_topic",
            sources=[],
            context_tokens=0,
        )
    
    # Build response
    sources = [
        SourceReference(
            source_type=s.source_type,
            source_id=s.source_id,
            score=s.score or 0.0,
            preview="",
        )
        for s in result.sources
    ]
    
    return ChatResponse(
        answer=result.answer,
        intent=result.intent,
        sources=sources,
        subject_id=request.subject_id or 0,
        unit_id=request.unit_id,
        topic_id=request.topic_id,
    )
