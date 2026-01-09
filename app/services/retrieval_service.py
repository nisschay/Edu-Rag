"""
Retrieval service for RAG-based chunk retrieval.

This module provides the main retrieval function that:
1. Embeds the query
2. Searches FAISS for similar chunks
3. Filters by metadata (user/subject/unit/topic)
4. Returns matching chunks with scores
"""

import logging
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.services import chunk_service
from app.utils.embeddings import embed_text, get_embedding_generator
from app.utils.vector_store import (
    get_vector_store,
    FAISSVectorStore,
    ChunkMetadata,
    SearchResult,
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """
    A retrieved chunk with similarity score.
    
    Attributes:
        chunk_id: Database chunk ID.
        text: Chunk text content.
        score: Similarity score (0-1, higher is better).
        source_file_id: Source file ID.
        topic_id: Topic ID.
        unit_id: Unit ID.
        subject_id: Subject ID.
    """
    
    chunk_id: int
    text: str
    score: float
    source_file_id: int
    topic_id: int
    unit_id: int
    subject_id: int


def embed_topic_chunks(
    db: Session,
    topic_id: int,
    user_id: int,
    subject_id: int,
    unit_id: int,
) -> tuple[int, int]:
    """
    Embed all unembedded chunks for a topic.
    
    Args:
        db: Database session.
        topic_id: Topic ID.
        user_id: User ID for metadata.
        subject_id: Subject ID for metadata.
        unit_id: Unit ID for metadata.
        
    Returns:
        Tuple of (chunks_embedded, already_embedded).
    """
    logger.info(f"Embedding chunks for topic {topic_id}")
    
    # Get chunks without embeddings
    chunks = chunk_service.get_chunks_without_embeddings(db, topic_id)
    
    if not chunks:
        # Count already embedded
        all_chunks = chunk_service.list_chunks_for_topic(db, topic_id)
        already_embedded = len(all_chunks)
        logger.info(f"No new chunks to embed, {already_embedded} already embedded")
        return 0, already_embedded
    
    logger.info(f"Found {len(chunks)} chunks to embed")
    
    # Get embedding generator
    generator = get_embedding_generator()
    
    # Extract texts
    texts = [c.text for c in chunks]
    
    # Generate embeddings
    embeddings = generator.embed_texts(texts)
    
    if len(embeddings) != len(chunks):
        logger.error(
            f"Embedding count mismatch: {len(embeddings)} embeddings, {len(chunks)} chunks"
        )
        raise ValueError("Embedding generation failed")
    
    # Prepare metadata
    metadata_list = [
        ChunkMetadata(
            chunk_id=chunk.id,
            user_id=user_id,
            subject_id=subject_id,
            unit_id=unit_id,
            topic_id=topic_id,
            source_file_id=chunk.source_file_id,
        )
        for chunk in chunks
    ]
    
    # Add to vector store
    store = get_vector_store()
    positions = store.add_embeddings(embeddings, metadata_list)
    
    # Update chunk records with embedding IDs
    chunk_embedding_pairs = [
        (chunk.id, pos)
        for chunk, pos in zip(chunks, positions)
    ]
    chunk_service.update_chunks_embedding_ids(db, chunk_embedding_pairs)
    
    # Save the index
    store.save()
    
    # Count already embedded
    all_chunks = chunk_service.list_chunks_for_topic(db, topic_id)
    already_embedded = len(all_chunks) - len(chunks)
    
    logger.info(
        f"Embedded {len(chunks)} chunks for topic {topic_id}, "
        f"{already_embedded} were already embedded"
    )
    
    return len(chunks), already_embedded


def retrieve_chunks(
    db: Session,
    user_id: int,
    query: str,
    subject_id: int | None = None,
    unit_id: int | None = None,
    topic_id: int | None = None,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """
    Retrieve relevant chunks for a query within a topic scope.
    
    This function:
    1. Embeds the query using OpenAI
    2. Searches FAISS for similar vectors
    3. Filters by user_id, subject_id, unit_id, topic_id
    4. Returns top-k matching chunks with their text
    
    Args:
        db: Database session.
        user_id: User ID (required for filtering).
        query: Search query text.
        subject_id: Optional Subject ID.
        unit_id: Optional Unit ID.
        topic_id: Optional Topic ID.
        top_k: Number of results to return (default 5).
        
    Returns:
        List of RetrievedChunk objects sorted by score (descending).
        
    Raises:
        ValueError: If query is empty or OpenAI API not configured.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    logger.info(
        f"Retrieving chunks for query (scope: sub={subject_id}, unit={unit_id}, topic={topic_id}), "
        f"user {user_id}"
    )
    
    # Embed the query
    query_embedding = embed_text(query)
    
    # Search with metadata filtering
    store = get_vector_store()
    results: list[SearchResult] = store.search(
        query_embedding=query_embedding,
        top_k=top_k,
        user_id=user_id,
        subject_id=subject_id,
        unit_id=unit_id,
        topic_id=topic_id,
    )
    
    if not results:
        logger.info("No matching chunks found")
        return []
    
    # Get chunk texts from database
    chunk_ids = [r.chunk_id for r in results]
    chunks = chunk_service.get_chunks_by_ids(db, chunk_ids)
    chunk_map = {c.id: c for c in chunks}
    
    # Build response
    retrieved: list[RetrievedChunk] = []
    for result in results:
        chunk = chunk_map.get(result.chunk_id)
        if chunk:
            retrieved.append(RetrievedChunk(
                chunk_id=result.chunk_id,
                text=chunk.text,
                score=result.score,
                source_file_id=result.metadata.source_file_id,
                topic_id=result.metadata.topic_id,
                unit_id=result.metadata.unit_id,
                subject_id=result.metadata.subject_id,
            ))
    
    logger.info(f"Retrieved {len(retrieved)} chunks for query")
    
    return retrieved
