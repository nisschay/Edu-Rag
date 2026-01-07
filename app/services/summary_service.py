"""
Summarization service for topic and unit summaries.

This service handles:
- Generating topic summaries from chunks
- Generating unit summaries from topic summaries
- Storing and embedding summaries
- Idempotent summary generation
"""

import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.summary import TopicSummary, UnitSummary
from app.models.topic import Topic
from app.models.unit import Unit
from app.models.chunk import Chunk
from app.services import chunk_service
from app.utils.prompts import get_topic_summary_prompt, get_unit_summary_prompt
from app.utils.llm import get_llm_generator
from app.utils.chunking import TextChunker
from app.utils.embeddings import embed_text
from app.utils.summary_vector_store import (
    get_summary_vector_store,
    SummaryMetadata,
)

logger = logging.getLogger(__name__)


# Token counter for summaries
_chunker = TextChunker()


def count_tokens(text: str) -> int:
    """Count tokens in text."""
    return _chunker.count_tokens(text)


# =============================================================================
# TOPIC SUMMARY OPERATIONS
# =============================================================================

def get_topic_summary(db: Session, topic_id: int) -> TopicSummary | None:
    """
    Get a topic summary by topic ID.
    
    Args:
        db: Database session.
        topic_id: The topic ID.
        
    Returns:
        TopicSummary if found, None otherwise.
    """
    stmt = select(TopicSummary).where(TopicSummary.topic_id == topic_id)
    return db.execute(stmt).scalar_one_or_none()


def get_topic_summary_by_id(db: Session, summary_id: int) -> TopicSummary | None:
    """Get a topic summary by its ID."""
    return db.get(TopicSummary, summary_id)


def list_topic_summaries_for_unit(db: Session, unit_id: int) -> list[TopicSummary]:
    """
    List all topic summaries for a unit.
    
    Args:
        db: Database session.
        unit_id: The unit ID.
        
    Returns:
        List of topic summaries.
    """
    stmt = (
        select(TopicSummary)
        .where(TopicSummary.unit_id == unit_id)
        .order_by(TopicSummary.topic_id)
    )
    return list(db.execute(stmt).scalars().all())


def generate_topic_summary(
    db: Session,
    topic: Topic,
    user_id: int,
    subject_id: int,
    unit_id: int,
    subject_name: str,
    unit_title: str,
    force_regenerate: bool = False,
) -> tuple[TopicSummary, bool]:
    """
    Generate a summary for a topic.
    
    Args:
        db: Database session.
        topic: The topic to summarize.
        user_id: Owner user ID.
        subject_id: Subject ID.
        unit_id: Unit ID.
        subject_name: Subject name for prompt.
        unit_title: Unit title for prompt.
        force_regenerate: If True, regenerate even if exists.
        
    Returns:
        Tuple of (TopicSummary, regenerated_flag).
    """
    logger.info(f"Generating summary for topic {topic.id} ({topic.title})")
    
    # Check if summary already exists
    existing = get_topic_summary(db, topic.id)
    if existing and not force_regenerate:
        logger.info(f"Topic {topic.id} already has a summary")
        return existing, False
    
    # Get chunks for this topic
    chunks = chunk_service.list_chunks_for_topic(db, topic.id)
    
    if not chunks:
        logger.warning(f"No chunks found for topic {topic.id}")
        raise ValueError(f"No chunks found for topic {topic.id}. Run chunking first.")
    
    # Build chunks text
    chunks_text = "\n\n---\n\n".join([c.text for c in chunks])
    
    # Generate summary using LLM
    prompt_template = get_topic_summary_prompt()
    prompt = prompt_template.format(
        topic_title=topic.title,
        subject_name=subject_name,
        unit_title=unit_title,
        chunks_text=chunks_text,
    )
    
    llm = get_llm_generator()
    summary_text = llm.generate_summary(prompt, max_tokens=400)
    
    token_count = count_tokens(summary_text)
    
    logger.info(f"Generated topic summary: {token_count} tokens from {len(chunks)} chunks")
    
    # Create or update summary
    if existing:
        existing.summary_text = summary_text
        existing.token_count = token_count
        existing.source_chunk_count = len(chunks)
        existing.embedding_id = None  # Reset embedding since content changed
        db.commit()
        db.refresh(existing)
        return existing, True
    else:
        summary = TopicSummary(
            user_id=user_id,
            subject_id=subject_id,
            unit_id=unit_id,
            topic_id=topic.id,
            summary_text=summary_text,
            token_count=token_count,
            source_chunk_count=len(chunks),
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        return summary, False


# =============================================================================
# UNIT SUMMARY OPERATIONS
# =============================================================================

def get_unit_summary(db: Session, unit_id: int) -> UnitSummary | None:
    """
    Get a unit summary by unit ID.
    
    Args:
        db: Database session.
        unit_id: The unit ID.
        
    Returns:
        UnitSummary if found, None otherwise.
    """
    stmt = select(UnitSummary).where(UnitSummary.unit_id == unit_id)
    return db.execute(stmt).scalar_one_or_none()


def get_unit_summary_by_id(db: Session, summary_id: int) -> UnitSummary | None:
    """Get a unit summary by its ID."""
    return db.get(UnitSummary, summary_id)


def generate_unit_summary(
    db: Session,
    unit: Unit,
    user_id: int,
    subject_id: int,
    subject_name: str,
    force_regenerate: bool = False,
) -> tuple[UnitSummary, bool]:
    """
    Generate a summary for a unit from its topic summaries.
    
    Args:
        db: Database session.
        unit: The unit to summarize.
        user_id: Owner user ID.
        subject_id: Subject ID.
        subject_name: Subject name for prompt.
        force_regenerate: If True, regenerate even if exists.
        
    Returns:
        Tuple of (UnitSummary, regenerated_flag).
    """
    logger.info(f"Generating summary for unit {unit.id} ({unit.title})")
    
    # Check if summary already exists
    existing = get_unit_summary(db, unit.id)
    if existing and not force_regenerate:
        logger.info(f"Unit {unit.id} already has a summary")
        return existing, False
    
    # Get topic summaries for this unit
    topic_summaries = list_topic_summaries_for_unit(db, unit.id)
    
    if not topic_summaries:
        logger.warning(f"No topic summaries found for unit {unit.id}")
        raise ValueError(
            f"No topic summaries found for unit {unit.id}. "
            "Generate topic summaries first."
        )
    
    # Build topic summaries text with topic titles
    topic_texts = []
    for ts in topic_summaries:
        topic_texts.append(f"## {ts.topic.title}\n{ts.summary_text}")
    topic_summaries_text = "\n\n".join(topic_texts)
    
    # Generate summary using LLM
    prompt_template = get_unit_summary_prompt()
    prompt = prompt_template.format(
        unit_title=unit.title,
        subject_name=subject_name,
        topic_summaries_text=topic_summaries_text,
    )
    
    llm = get_llm_generator()
    summary_text = llm.generate_summary(prompt, max_tokens=600)
    
    token_count = count_tokens(summary_text)
    
    logger.info(
        f"Generated unit summary: {token_count} tokens from "
        f"{len(topic_summaries)} topic summaries"
    )
    
    # Create or update summary
    if existing:
        existing.summary_text = summary_text
        existing.token_count = token_count
        existing.source_topic_count = len(topic_summaries)
        existing.embedding_id = None  # Reset embedding since content changed
        db.commit()
        db.refresh(existing)
        return existing, True
    else:
        summary = UnitSummary(
            user_id=user_id,
            subject_id=subject_id,
            unit_id=unit.id,
            summary_text=summary_text,
            token_count=token_count,
            source_topic_count=len(topic_summaries),
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        return summary, False


# =============================================================================
# EMBEDDING OPERATIONS
# =============================================================================

def embed_topic_summary(db: Session, summary: TopicSummary) -> bool:
    """
    Embed a topic summary and store in the summary vector store.
    
    Args:
        db: Database session.
        summary: The topic summary to embed.
        
    Returns:
        True if embedded, False if already had embedding.
    """
    if summary.embedding_id is not None:
        logger.debug(f"Topic summary {summary.id} already has embedding")
        return False
    
    # Generate embedding
    embedding = embed_text(summary.summary_text)
    
    # Create metadata
    metadata = SummaryMetadata(
        summary_id=summary.id,
        summary_type="topic",
        user_id=summary.user_id,
        subject_id=summary.subject_id,
        unit_id=summary.unit_id,
        topic_id=summary.topic_id,
    )
    
    # Add to vector store
    store = get_summary_vector_store()
    position = store.add_embedding(embedding, metadata)
    
    # Update summary record
    summary.embedding_id = position
    db.commit()
    
    # Save the index
    store.save()
    
    logger.info(f"Embedded topic summary {summary.id} at position {position}")
    
    return True


def embed_unit_summary(db: Session, summary: UnitSummary) -> bool:
    """
    Embed a unit summary and store in the summary vector store.
    
    Args:
        db: Database session.
        summary: The unit summary to embed.
        
    Returns:
        True if embedded, False if already had embedding.
    """
    if summary.embedding_id is not None:
        logger.debug(f"Unit summary {summary.id} already has embedding")
        return False
    
    # Generate embedding
    embedding = embed_text(summary.summary_text)
    
    # Create metadata
    metadata = SummaryMetadata(
        summary_id=summary.id,
        summary_type="unit",
        user_id=summary.user_id,
        subject_id=summary.subject_id,
        unit_id=summary.unit_id,
        topic_id=None,
    )
    
    # Add to vector store
    store = get_summary_vector_store()
    position = store.add_embedding(embedding, metadata)
    
    # Update summary record
    summary.embedding_id = position
    db.commit()
    
    # Save the index
    store.save()
    
    logger.info(f"Embedded unit summary {summary.id} at position {position}")
    
    return True


def embed_all_summaries_for_unit(db: Session, unit_id: int) -> tuple[int, int]:
    """
    Embed all summaries (topic + unit) for a unit.
    
    Args:
        db: Database session.
        unit_id: The unit ID.
        
    Returns:
        Tuple of (newly_embedded, already_embedded).
    """
    newly_embedded = 0
    already_embedded = 0
    
    # Embed topic summaries
    topic_summaries = list_topic_summaries_for_unit(db, unit_id)
    for ts in topic_summaries:
        if embed_topic_summary(db, ts):
            newly_embedded += 1
        else:
            already_embedded += 1
    
    # Embed unit summary
    unit_summary = get_unit_summary(db, unit_id)
    if unit_summary:
        if embed_unit_summary(db, unit_summary):
            newly_embedded += 1
        else:
            already_embedded += 1
    
    logger.info(
        f"Embedded summaries for unit {unit_id}: "
        f"{newly_embedded} new, {already_embedded} existing"
    )
    
    return newly_embedded, already_embedded
