"""
Chat service for RAG-based conversational responses.

This module implements the chat pipeline:
1. Intent classification - determines user intent
2. Retrieval strategy - selects appropriate context source
3. LLM generation - generates response with context
4. Source attribution - tracks sources used
"""

import logging
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.models.unit import Unit
from app.models.subject import Subject
from app.models.file import File
from app.services import retrieval_service, summary_service
from app.utils.embeddings import embed_text
from app.utils.summary_vector_store import (
    get_summary_vector_store,
    SummarySearchResult,
)
from app.utils.llm import get_llm_generator
from app.utils.prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    TEACH_FROM_START_PROMPT,
    EXPLAIN_TOPIC_PROMPT,
    EXPLAIN_DETAIL_PROMPT,
    REVISE_PROMPT,
    GENERATE_QUESTIONS_PROMPT,
)

logger = logging.getLogger(__name__)


# Type alias for intent
IntentType = Literal[
    "teach_from_start",
    "explain_topic",
    "explain_detail",
    "revise",
    "generate_questions",
]


@dataclass
class Source:
    """
    A source reference for chat response attribution.
    
    Attributes:
        source_type: Type of source ("chunk", "topic_summary", "unit_summary").
        source_id: Database ID of the source.
        title: Human-readable title.
        score: Similarity score if from retrieval.
    """
    
    source_type: str
    source_id: int
    title: str
    score: float | None = None


@dataclass
class ChatResult:
    """
    Result of a chat query.
    
    Attributes:
        answer: The LLM-generated response.
        intent: The classified intent.
        sources: List of sources used for the response.
        context_tokens: Approximate token count of context used.
    """
    
    answer: str
    intent: IntentType
    sources: list[Source]
    context_tokens: int


def _check_scope_ready(
    db: Session,
    subject_id: int | None = None,
    unit_id: int | None = None,
    topic_id: int | None = None,
) -> tuple[bool, str | None]:
    """
    Check if the materials in the given scope are ready for chat.
    
    Returns:
        Tuple of (is_ready, message_if_not_ready)
    """
    from sqlalchemy import or_
    
    # Base query for files
    stmt = select(File)
    
    if topic_id:
        stmt = stmt.where(File.topic_id == topic_id)
    elif unit_id:
        # Get all topics for unit
        topic_ids = db.scalars(select(Topic.id).where(Topic.unit_id == unit_id)).all()
        if not topic_ids:
            return True, None # No topics, so technically nothing to wait for
        stmt = stmt.where(File.topic_id.in_(topic_ids))
    elif subject_id:
        # Get all units for subject
        unit_ids = db.scalars(select(Unit.id).where(Unit.subject_id == subject_id)).all()
        if not unit_ids:
            return True, None
        # Get all topics for units
        topic_ids = db.scalars(select(Topic.id).where(Topic.unit_id.in_(unit_ids))).all()
        if not topic_ids:
            return True, None
        stmt = stmt.where(File.topic_id.in_(topic_ids))
    else:
        return True, None

    files = db.scalars(stmt).all()
    if not files:
        return True, None # No files uploaded yet
    
    # Check if any file is pending or processing
    processing_files = [f for f in files if f.status in ("pending", "processing")]
    if processing_files:
        return False, "Your material is still being processed. Try again shortly."
    
    # If all failed
    if all(f.status == "failed" for f in files):
        return False, "The uploaded material failed to process. Please try re-uploading."
        
    return True, None


# =============================================================================
# INTENT CLASSIFICATION
# =============================================================================

def classify_intent(
    message: str,
    subject_name: str = "Unknown",
    unit_title: str = "Unknown",
    topic_title: str = "Unknown",
) -> IntentType:
    """
    Classify user intent from their message.
    
    Args:
        message: The user's message text.
        subject_name: Name of the subject.
        unit_title: Title of the unit.
        topic_title: Title of the topic.
        
    Returns:
        The classified intent type.
    """
    logger.info(f"Classifying intent for message: {message[:100]}...")
    
    llm = get_llm_generator()
    
    # Use LLM for intent classification
    prompt = INTENT_CLASSIFICATION_PROMPT.format(
        message=message,
        subject_name=subject_name,
        unit_title=unit_title,
        topic_title=topic_title,
    )
    
    valid_intents = [
        "teach_from_start",
        "explain_topic",
        "explain_detail",
        "revise",
        "generate_questions",
    ]
    
    raw_intent = llm.classify_intent(prompt, valid_intents)
    
    # Normalize and validate
    intent = raw_intent.strip().lower().replace(" ", "_")
    
    if intent not in valid_intents:
        logger.warning(f"Invalid intent '{intent}', defaulting to explain_topic")
        intent = "explain_topic"
    
    logger.info(f"Classified intent: {intent}")
    
    return intent  # type: ignore


# =============================================================================
# RETRIEVAL STRATEGIES
# =============================================================================

def _retrieve_unit_summaries(
    user_id: int,
    subject_id: int,
    unit_id: int | None,
    query: str,
    top_k: int = 3,
) -> tuple[list[SummarySearchResult], list[Source]]:
    """
    Retrieve unit summaries for broad context.
    
    Used for: teach_from_start, revise intents.
    
    Args:
        user_id: User ID for filtering.
        subject_id: Subject ID for filtering.
        unit_id: Optional unit ID to scope.
        query: Search query.
        top_k: Number of results.
        
    Returns:
        Tuple of (search results, source references).
    """
    logger.info(f"Retrieving unit summaries for query: {query[:50]}...")
    
    query_embedding = embed_text(query)
    store = get_summary_vector_store()
    
    results = store.search(
        query_embedding=query_embedding,
        top_k=top_k,
        summary_type="unit",
        user_id=user_id,
        subject_id=subject_id,
        unit_id=unit_id,
    )
    
    sources = [
        Source(
            source_type="unit_summary",
            source_id=r.metadata.summary_id,
            title=f"Unit Summary #{r.metadata.summary_id}",
            score=r.score,
        )
        for r in results
    ]
    
    logger.info(f"Retrieved {len(results)} unit summaries")
    
    return results, sources


def _retrieve_topic_summaries(
    user_id: int,
    subject_id: int,
    unit_id: int | None,
    topic_id: int | None,
    query: str,
    top_k: int = 5,
) -> tuple[list[SummarySearchResult], list[Source]]:
    """
    Retrieve topic summaries for medium-grained context.
    
    Used for: explain_topic, generate_questions intents.
    
    Args:
        user_id: User ID for filtering.
        subject_id: Subject ID for filtering.
        unit_id: Optional unit ID to scope.
        topic_id: Optional topic ID to scope.
        query: Search query.
        top_k: Number of results.
        
    Returns:
        Tuple of (search results, source references).
    """
    logger.info(f"Retrieving topic summaries for query: {query[:50]}...")
    
    query_embedding = embed_text(query)
    store = get_summary_vector_store()
    
    results = store.search(
        query_embedding=query_embedding,
        top_k=top_k,
        summary_type="topic",
        user_id=user_id,
        subject_id=subject_id,
        unit_id=unit_id,
        topic_id=topic_id,
    )
    
    sources = [
        Source(
            source_type="topic_summary",
            source_id=r.metadata.summary_id,
            title=f"Topic Summary #{r.metadata.summary_id}",
            score=r.score,
        )
        for r in results
    ]
    
    logger.info(f"Retrieved {len(results)} topic summaries")
    
    return results, sources


def _retrieve_raw_chunks(
    db: Session,
    user_id: int,
    subject_id: int,
    unit_id: int,
    topic_id: int,
    query: str,
    top_k: int = 8,
) -> tuple[list[retrieval_service.RetrievedChunk], list[Source]]:
    """
    Retrieve raw chunks for fine-grained context.
    
    Used for: explain_detail intent.
    
    Args:
        db: Database session.
        user_id: User ID for filtering.
        subject_id: Subject ID for filtering.
        unit_id: Unit ID for filtering.
        topic_id: Topic ID for filtering.
        query: Search query.
        top_k: Number of results.
        
    Returns:
        Tuple of (retrieved chunks, source references).
    """
    logger.info(f"Retrieving raw chunks for query: {query[:50]}...")
    
    chunks = retrieval_service.retrieve_chunks(
        db=db,
        user_id=user_id,
        query=query,
        subject_id=subject_id,
        unit_id=unit_id,
        topic_id=topic_id,
        top_k=top_k,
    )
    
    sources = [
        Source(
            source_type="chunk",
            source_id=c.chunk_id,
            title=f"Chunk #{c.chunk_id}",
            score=c.score,
        )
        for c in chunks
    ]
    
    logger.info(f"Retrieved {len(chunks)} raw chunks")
    
    return chunks, sources


# =============================================================================
# CONTEXT BUILDING
# =============================================================================

def _build_context_from_unit_summaries(
    results: list[SummarySearchResult],
    db: Session,
) -> tuple[str, int]:
    """
    Build context string from unit summary results.
    
    Returns:
        Tuple of (context_text, approximate_token_count).
    """
    if not results:
        return "", 0
    
    context_parts = []
    total_tokens = 0
    
    for r in results:
        summary = summary_service.get_unit_summary_by_id(db, r.metadata.summary_id)
        if summary and summary.unit:
            context_parts.append(f"## {summary.unit.title}\n{summary.summary_text}")
            total_tokens += summary.token_count or 0
    
    return "\n\n".join(context_parts), total_tokens


def _build_context_from_topic_summaries(
    results: list[SummarySearchResult],
    db: Session,
) -> tuple[str, int]:
    """
    Build context string from topic summary results.
    
    Returns:
        Tuple of (context_text, approximate_token_count).
    """
    if not results:
        return "", 0
    
    context_parts = []
    total_tokens = 0
    
    for r in results:
        summary = summary_service.get_topic_summary_by_id(db, r.metadata.summary_id)
        if summary and summary.topic:
            context_parts.append(f"## {summary.topic.title}\n{summary.summary_text}")
            total_tokens += summary.token_count or 0
    
    return "\n\n".join(context_parts), total_tokens


def _build_context_from_chunks(
    chunks: list[retrieval_service.RetrievedChunk],
) -> tuple[str, int]:
    """
    Build context string from raw chunk results.
    
    Returns:
        Tuple of (context_text, approximate_token_count).
    """
    if not chunks:
        return "", 0
    
    context_parts = [c.text for c in chunks]
    # Rough estimate: 4 characters per token
    total_tokens = sum(len(c.text) // 4 for c in chunks)
    
    return "\n\n---\n\n".join(context_parts), total_tokens


# =============================================================================
# RESPONSE GENERATION
# =============================================================================

def _get_prompt_template(intent: IntentType) -> str:
    """
    Get the appropriate prompt template for the intent.
    
    Args:
        intent: The classified intent.
        
    Returns:
        The prompt template string.
    """
    templates = {
        "teach_from_start": TEACH_FROM_START_PROMPT,
        "explain_topic": EXPLAIN_TOPIC_PROMPT,
        "explain_detail": EXPLAIN_DETAIL_PROMPT,
        "revise": REVISE_PROMPT,
        "generate_questions": GENERATE_QUESTIONS_PROMPT,
    }
    
    return templates.get(intent, EXPLAIN_TOPIC_PROMPT)


def _generate_response(
    intent: IntentType,
    context: str,
    message: str,
    subject_name: str | None = None,
    unit_title: str | None = None,
    topic_title: str | None = None,
    summary_context: str = "",
    chunk_context: str = "",
) -> str:
    """
    Generate LLM response based on intent and context.
    
    Args:
        intent: The classified intent.
        context: Retrieved context text (mapped to 'context' or 'summary_context' etc).
        message: User's original message.
        subject_name: Optional subject name.
        unit_title: Optional unit title.
        topic_title: Optional topic title.
        summary_context: For explain_topic intent.
        chunk_context: For explain_topic intent.
        
    Returns:
        The generated response text.
    """
    logger.info(f"Generating response for intent: {intent}")
    
    llm = get_llm_generator()
    template = _get_prompt_template(intent)
    
    # Build the prompt with all possible fields
    # Different templates use different keys, but we provide all common ones
    prompt = template.format(
        context=context,
        summary_context=summary_context or context,
        chunk_context=chunk_context,
        message=message,
        subject_name=subject_name or "the subject",
        unit_title=unit_title or "the unit",
        topic_title=topic_title or "the topic",
    )
    
    response = llm.generate_chat_response(prompt)
    
    logger.info(f"Generated response: {len(response)} characters")
    
    return response


# =============================================================================
# MAIN CHAT FUNCTION
# =============================================================================

def chat(
    db: Session,
    user_id: int,
    subject_id: int,
    message: str,
    unit_id: int | None = None,
    topic_id: int | None = None,
) -> ChatResult:
    """
    Process a chat message and generate a RAG response.
    
    This is the main entry point for chat functionality. It:
    1. Classifies the user's intent
    2. Retrieves appropriate context based on intent
    3. Generates a response using LLM
    4. Returns response with sources
    
    Intent-based retrieval strategy:
    - teach_from_start: Unit summaries (broad overview)
    - explain_topic: Topic summaries (medium detail)
    - explain_detail: Raw chunks (fine detail)
    - revise: Unit summaries (quick review)
    - generate_questions: Topic summaries (structured content)
    
    Args:
        db: Database session.
        user_id: User ID for filtering.
        subject_id: Subject ID for scoping.
        message: User's chat message.
        unit_id: Optional unit ID to scope.
        topic_id: Optional topic ID to scope (required for explain_detail).
        
    Returns:
        ChatResult with answer, intent, sources, and context info.
        
    Raises:
        ValueError: If explain_detail requested without topic_id.
    """
    logger.info(
        f"Processing chat for user {user_id}, subject {subject_id}, "
        f"unit {unit_id}, topic {topic_id}"
    )
    logger.info(f"Message: {message[:200]}...")
    
    # Get topic/unit names for prompts
    topic_title = "Unknown Topic"
    unit_title = "Unknown Unit"
    subject_name = "Unknown Subject"
    
    subject = db.get(Subject, subject_id)
    if subject:
        subject_name = subject.name

    if topic_id:
        topic = db.get(Topic, topic_id)
        if topic:
            topic_title = topic.title
            unit_id = topic.unit_id
    
    if unit_id:
        unit = db.get(Unit, unit_id)
        if unit:
            unit_title = unit.title
    
    # Step 1: Classify intent
    intent = classify_intent(
        message=message,
        subject_name=subject_name,
        unit_title=unit_title,
        topic_title=topic_title
    )
    
    # Step 2: Retrieve context based on intent
    context = ""
    sources: list[Source] = []
    context_tokens = 0
    
    # Select retrieval strategy based on intent
    if intent == "teach_from_start":
        # Broad overview with unit summaries
        results, sources = _retrieve_unit_summaries(
            user_id=user_id,
            subject_id=subject_id,
            unit_id=unit_id,
            query=message,
            top_k=3,
        )
        context, context_tokens = _build_context_from_unit_summaries(results, db)
        
        # If no unit summaries, fall back to topic summaries
        if not context:
            logger.info("No unit summaries found, falling back to topic summaries")
            results, sources = _retrieve_topic_summaries(
                user_id=user_id,
                subject_id=subject_id,
                unit_id=unit_id,
                topic_id=topic_id,
                query=message,
                top_k=5,
            )
            context, context_tokens = _build_context_from_topic_summaries(results, db)
    
    elif intent == "explain_topic":
        # Medium detail with topic summaries
        results, sources = _retrieve_topic_summaries(
            user_id=user_id,
            subject_id=subject_id,
            unit_id=unit_id,
            topic_id=topic_id,
            query=message,
            top_k=5,
        )
        context, context_tokens = _build_context_from_topic_summaries(results, db)
    
    elif intent == "explain_detail":
        # Fine detail with raw chunks
        if not topic_id or not unit_id:
            logger.warning(
                "explain_detail without topic_id, falling back to topic summaries"
            )
            results, sources = _retrieve_topic_summaries(
                user_id=user_id,
                subject_id=subject_id,
                unit_id=unit_id,
                topic_id=topic_id,
                query=message,
                top_k=5,
            )
            context, context_tokens = _build_context_from_topic_summaries(results, db)
        else:
            chunks, sources = _retrieve_raw_chunks(
                db=db,
                user_id=user_id,
                subject_id=subject_id,
                unit_id=unit_id,
                topic_id=topic_id,
                query=message,
                top_k=8,
            )
            context, context_tokens = _build_context_from_chunks(chunks)
    
    elif intent == "revise":
        # Quick review with unit summaries
        results, sources = _retrieve_unit_summaries(
            user_id=user_id,
            subject_id=subject_id,
            unit_id=unit_id,
            query=message,
            top_k=3,
        )
        context, context_tokens = _build_context_from_unit_summaries(results, db)
        
        # Fall back to topic summaries
        if not context:
            results, sources = _retrieve_topic_summaries(
                user_id=user_id,
                subject_id=subject_id,
                unit_id=unit_id,
                topic_id=topic_id,
                query=message,
                top_k=5,
            )
            context, context_tokens = _build_context_from_topic_summaries(results, db)
    
    elif intent == "generate_questions":
        # Structured content from topic summaries
        results, sources = _retrieve_topic_summaries(
            user_id=user_id,
            subject_id=subject_id,
            unit_id=unit_id,
            topic_id=topic_id,
            query=message,
            top_k=5,
        )
        context, context_tokens = _build_context_from_topic_summaries(results, db)
    
    # Step 3: Handle no context found
    if not context:
        logger.warning("No context retrieved for query")
        context = "No relevant content found in the uploaded materials."
    
    # Step 4: Generate response
    answer = _generate_response(
        intent=intent,
        context=context,
        message=message,
        subject_name=subject_name,
        unit_title=unit_title,
        topic_title=topic_title,
    )
    
    result = ChatResult(
        answer=answer,
        intent=intent,
        sources=sources,
        context_tokens=context_tokens,
    )
    
    logger.info(
        f"Chat completed: intent={intent}, sources={len(sources)}, "
        f"context_tokens={context_tokens}"
    )
    
    return result


def _chat_global(
    db: Session,
    user_id: int,
    message: str,
) -> ChatResult:
    """
    Perform a global chat across all user materials.
    """
    logger.info(f"Global chat for user {user_id}: {message[:100]}...")
    
    # 1. Classify intent
    intent = classify_intent(
        message=message,
        subject_name="All Subjects",
        unit_title="All Units",
        topic_title="All Topics"
    )
    
    # 2. Retrieve context (always use topic summaries for global for better relevance/speed balance)
    results, sources = _retrieve_topic_summaries(
        user_id=user_id,
        subject_id=None,
        unit_id=None,
        topic_id=None,
        query=message,
        top_k=5,
    )
    
    context, context_tokens = _build_context_from_topic_summaries(results, db)
    
    if not context:
        # Fallback to Unit Summaries
        results, sources = _retrieve_unit_summaries(
            user_id=user_id,
            subject_id=None,
            unit_id=None,
            query=message,
            top_k=3,
        )
        context, context_tokens = _build_context_from_unit_summaries(results, db)
    
    if not context:
        return ChatResult(
            answer="I couldn't find any relevant information in your uploaded materials. Could you please provide more details or upload more content?",
            intent=intent,
            sources=[],
            context_tokens=0,
        )
    
    # 3. Generate response
    answer = _generate_response(
        intent=intent,
        context=context,
        message=message,
        subject_name="Your Materials",
        unit_title="Multiple Units",
        topic_title="Multiple Topics",
    )
    
    return ChatResult(
        answer=answer,
        intent=intent,
        sources=sources,
        context_tokens=context_tokens,
    )


def chat_flexible(
    db: Session,
    user_id: int,
    message: str,
    subject_id: int | None = None,
    unit_id: int | None = None,
    topic_id: int | None = None,
) -> ChatResult:
    """
    Process a chat message with flexible scoping and graceful fallbacks.
    """
    # 0. Check scope readiness
    is_ready, ready_message = _check_scope_ready(db, subject_id, unit_id, topic_id)
    if not is_ready:
        return ChatResult(
            answer=ready_message or "Processing...",
            intent="explain_topic",
            sources=[],
            context_tokens=0,
        )

    # Check if we have ANY ready material at all if no scope
    if not subject_id and not unit_id and not topic_id:
        logger.info("No scope provided, checking for any ready materials")
        # Check if user has any ready files
        has_ready = db.scalars(select(File).where(File.status == "ready")).first() is not None
        if not has_ready:
            return ChatResult(
                answer="Welcome! I'm ready to help. To get started, you can create a subject and upload some study materials, or just ask me a general question if you've already uploaded something!",
                intent="explain_topic",
                sources=[],
                context_tokens=0,
            )
        
        # If we have materials, proceed to a global search (handing off to chat() with special scope)
        # Note: chat() currently requires subject_id. We'll modify it or handle it here.
        return _chat_global(db, user_id, message)

    # Case 1: Topic provided - Use existing logic
    if topic_id:
        try:
            return chat(db, user_id, subject_id or 0, message, unit_id, topic_id)
        except Exception as e:
            logger.error(f"Topic chat failed: {e}")
            # Fallback to unit/subject if topic fails
            if not unit_id and not subject_id:
                return ChatResult(
                    answer="I encountered an issue accessing that topic. Please try another one or check back later.",
                    intent="explain_topic",
                    sources=[],
                    context_tokens=0,
                )

    # Infer subject_id if missing but lower scope exists
    if not subject_id:
        if unit_id:
            unit = db.get(Unit, unit_id)
            if unit:
                subject_id = unit.subject_id
            else:
                 return ChatResult(
                    answer="I couldn't find that unit. Please select a valid unit.",
                    intent="explain_topic",
                    sources=[],
                    context_tokens=0,
                )
    
    # Case 2: Unit provided (no topic)
    if unit_id:
        # Retrieve unit summaries
        results, sources = _retrieve_unit_summaries(
            user_id=user_id,
            subject_id=subject_id,
            unit_id=unit_id,
            query=message,
            top_k=3,
        )
        context, tokens = _build_context_from_unit_summaries(results, db)
        
        if not context:
             return ChatResult(
                answer="No study material has been uploaded for this unit yet. Try uploading some content!",
                intent="explain_topic",
                sources=[],
                context_tokens=0,
            )
            
        # Generate answer
        answer = _generate_response(
            intent="explain_topic",
            context=context,
            message=message,
            unit_name=db.get(Unit, unit_id).title,
            topic_name=None,
        )
        
        return ChatResult(
            answer=answer,
            intent="explain_topic",
            sources=sources,
            context_tokens=tokens,
        )

    # Case 3: Subject only (no unit/topic)
    # Use broad retrieval across the subject
    
    # Check if subject has any content
    subject = db.get(Subject, subject_id)
    if not subject:
         return ChatResult(
            answer="That subject doesn't seem to exist. Please create one to get started.",
            intent="explain_topic",
            sources=[],
            context_tokens=0,
        )
        
    # Retrieve top unit summaries for the subject
    results, sources = _retrieve_unit_summaries(
        user_id=user_id,
        subject_id=subject_id,
        unit_id=None, # Search all units in subject
        query=message,
        top_k=5,
    )
    context, tokens = _build_context_from_unit_summaries(results, db)
    
    if not context:
         return ChatResult(
            answer=f"No material uploaded for {subject.name} yet. Upload some units and topics to start learning!",
            intent="explain_topic",
            sources=[],
            context_tokens=0,
        )
        
    answer = _generate_response(
        intent="teach_from_start",
        context=context,
        message=message,
        unit_name=None,
        topic_name=None,
    )
    
    return ChatResult(
        answer=answer,
        intent="teach_from_start",
        sources=sources,
        context_tokens=tokens,
    )
