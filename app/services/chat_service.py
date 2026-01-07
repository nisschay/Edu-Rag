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

from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.models.unit import Unit
from app.models.subject import Subject
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


# =============================================================================
# INTENT CLASSIFICATION
# =============================================================================

def classify_intent(message: str) -> IntentType:
    """
    Classify user intent from their message.
    
    Intent types:
    - teach_from_start: User wants to learn a topic from scratch
    - explain_topic: User wants a summary/overview of a topic
    - explain_detail: User wants specific details or clarification
    - revise: User wants to review or refresh knowledge
    - generate_questions: User wants practice questions
    
    Args:
        message: The user's message text.
        
    Returns:
        The classified intent type.
    """
    logger.info(f"Classifying intent for message: {message[:100]}...")
    
    llm = get_llm_generator()
    
    # Use LLM for intent classification
    prompt = INTENT_CLASSIFICATION_PROMPT.format(message=message)
    
    raw_intent = llm.classify_intent(prompt)
    
    # Normalize and validate
    intent = raw_intent.strip().lower().replace(" ", "_")
    
    valid_intents = [
        "teach_from_start",
        "explain_topic",
        "explain_detail",
        "revise",
        "generate_questions",
    ]
    
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
        subject_id=subject_id,
        unit_id=unit_id,
        topic_id=topic_id,
        query=query,
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
    topic_name: str | None = None,
    unit_name: str | None = None,
) -> str:
    """
    Generate LLM response based on intent and context.
    
    Args:
        intent: The classified intent.
        context: Retrieved context text.
        message: User's original message.
        topic_name: Optional topic name for context.
        unit_name: Optional unit name for context.
        
    Returns:
        The generated response text.
    """
    logger.info(f"Generating response for intent: {intent}")
    
    llm = get_llm_generator()
    template = _get_prompt_template(intent)
    
    # Build the prompt
    prompt = template.format(
        context=context,
        question=message,
        topic_name=topic_name or "the topic",
        unit_name=unit_name or "the unit",
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
    
    # Step 1: Classify intent
    intent = classify_intent(message)
    
    # Step 2: Retrieve context based on intent
    context = ""
    sources: list[Source] = []
    context_tokens = 0
    
    # Get topic/unit names for prompts
    topic_name = None
    unit_name = None
    
    if topic_id:
        topic = db.get(Topic, topic_id)
        if topic:
            topic_name = topic.title
            unit_id = topic.unit_id  # Ensure unit_id is set from topic
    
    if unit_id:
        unit = db.get(Unit, unit_id)
        if unit:
            unit_name = unit.title
    
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
        topic_name=topic_name,
        unit_name=unit_name,
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
