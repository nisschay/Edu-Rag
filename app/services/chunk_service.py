"""
Chunk service providing business logic for chunk operations.

This service handles:
- Creating chunks from file text
- Listing chunks for a topic
- Managing chunk lifecycle
"""

import logging
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.file import File
from app.models.topic import Topic
from app.models.unit import Unit
from app.models.subject import Subject
from app.schemas.chunk import ChunkCreate
from app.utils.chunking import chunk_text, TextChunk

logger = logging.getLogger(__name__)


def get_chunk_by_id(db: Session, chunk_id: int) -> Chunk | None:
    """
    Get a chunk by ID.
    
    Args:
        db: Database session.
        chunk_id: The chunk ID to look up.
        
    Returns:
        Chunk if found, None otherwise.
    """
    return db.get(Chunk, chunk_id)


def list_chunks_for_topic(db: Session, topic_id: int) -> list[Chunk]:
    """
    List all chunks for a topic.
    
    Args:
        db: Database session.
        topic_id: The topic ID.
        
    Returns:
        List of chunks ordered by source file and index.
    """
    stmt = (
        select(Chunk)
        .where(Chunk.topic_id == topic_id)
        .order_by(Chunk.source_file_id, Chunk.chunk_index)
    )
    return list(db.execute(stmt).scalars().all())


def list_chunks_for_file(db: Session, file_id: int) -> list[Chunk]:
    """
    List all chunks for a specific file.
    
    Args:
        db: Database session.
        file_id: The file ID.
        
    Returns:
        List of chunks ordered by index.
    """
    stmt = (
        select(Chunk)
        .where(Chunk.source_file_id == file_id)
        .order_by(Chunk.chunk_index)
    )
    return list(db.execute(stmt).scalars().all())


def get_chunks_without_embeddings(db: Session, topic_id: int) -> list[Chunk]:
    """
    Get chunks that haven't been embedded yet.
    
    Args:
        db: Database session.
        topic_id: The topic ID.
        
    Returns:
        List of chunks without embeddings.
    """
    stmt = (
        select(Chunk)
        .where(Chunk.topic_id == topic_id)
        .where(Chunk.embedding_id.is_(None))
        .order_by(Chunk.id)
    )
    return list(db.execute(stmt).scalars().all())


def create_chunk(db: Session, chunk_data: ChunkCreate) -> Chunk:
    """
    Create a new chunk.
    
    Args:
        db: Database session.
        chunk_data: Chunk creation data.
        
    Returns:
        Created chunk.
    """
    chunk = Chunk(
        user_id=chunk_data.user_id,
        subject_id=chunk_data.subject_id,
        unit_id=chunk_data.unit_id,
        topic_id=chunk_data.topic_id,
        source_file_id=chunk_data.source_file_id,
        chunk_index=chunk_data.chunk_index,
        text=chunk_data.text,
        token_count=chunk_data.token_count,
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


def create_chunks_batch(db: Session, chunks_data: list[ChunkCreate]) -> list[Chunk]:
    """
    Create multiple chunks in a batch.
    
    Args:
        db: Database session.
        chunks_data: List of chunk creation data.
        
    Returns:
        List of created chunks.
    """
    chunks = [
        Chunk(
            user_id=c.user_id,
            subject_id=c.subject_id,
            unit_id=c.unit_id,
            topic_id=c.topic_id,
            source_file_id=c.source_file_id,
            chunk_index=c.chunk_index,
            text=c.text,
            token_count=c.token_count,
        )
        for c in chunks_data
    ]
    db.add_all(chunks)
    db.commit()
    for chunk in chunks:
        db.refresh(chunk)
    return chunks


def delete_chunks_for_file(db: Session, file_id: int) -> int:
    """
    Delete all chunks for a file.
    
    Args:
        db: Database session.
        file_id: The file ID.
        
    Returns:
        Number of chunks deleted.
    """
    stmt = delete(Chunk).where(Chunk.source_file_id == file_id)
    result = db.execute(stmt)
    db.commit()
    return result.rowcount


def delete_chunks_for_topic(db: Session, topic_id: int) -> int:
    """
    Delete all chunks for a topic.
    
    Args:
        db: Database session.
        topic_id: The topic ID.
        
    Returns:
        Number of chunks deleted.
    """
    stmt = delete(Chunk).where(Chunk.topic_id == topic_id)
    result = db.execute(stmt)
    db.commit()
    return result.rowcount


def process_file_into_chunks(
    db: Session,
    file: File,
    user_id: int,
    subject_id: int,
    unit_id: int,
) -> list[Chunk]:
    """
    Process a file's extracted text into chunks.
    
    This function:
    1. Deletes existing chunks for the file
    2. Chunks the extracted text
    3. Creates new chunk records
    
    Args:
        db: Database session.
        file: The file to process.
        user_id: Owner user ID.
        subject_id: Subject ID for metadata.
        unit_id: Unit ID for metadata.
        
    Returns:
        List of created chunks.
    """
    logger.info(f"Processing file {file.id} ({file.filename}) into chunks")
    
    # Skip if no extracted text
    if not file.extracted_text:
        logger.warning(f"File {file.id} has no extracted text")
        return []
    
    # Delete existing chunks for this file
    deleted_count = delete_chunks_for_file(db, file.id)
    if deleted_count > 0:
        logger.info(f"Deleted {deleted_count} existing chunks for file {file.id}")
    
    # Chunk the text
    text_chunks: list[TextChunk] = chunk_text(file.extracted_text)
    logger.info(f"Created {len(text_chunks)} chunks from file {file.id}")
    
    # Create chunk records
    chunks_data = [
        ChunkCreate(
            user_id=user_id,
            subject_id=subject_id,
            unit_id=unit_id,
            topic_id=file.topic_id,
            source_file_id=file.id,
            chunk_index=tc.chunk_index,
            text=tc.text,
            token_count=tc.token_count,
        )
        for tc in text_chunks
    ]
    
    chunks = create_chunks_batch(db, chunks_data)
    
    total_tokens = sum(c.token_count for c in chunks)
    logger.info(
        f"File {file.id}: created {len(chunks)} chunks with {total_tokens} total tokens"
    )
    
    return chunks


def process_topic_into_chunks(
    db: Session,
    topic: Topic,
    user_id: int,
    subject_id: int,
    unit_id: int,
) -> tuple[int, int, int]:
    """
    Process all files in a topic into chunks.
    
    Args:
        db: Database session.
        topic: The topic to process.
        user_id: Owner user ID.
        subject_id: Subject ID for metadata.
        unit_id: Unit ID for metadata.
        
    Returns:
        Tuple of (files_processed, chunks_created, total_tokens).
    """
    logger.info(f"Processing topic {topic.id} ({topic.title}) into chunks")
    
    files_processed = 0
    total_chunks = 0
    total_tokens = 0
    
    for file in topic.files:
        if file.extracted_text:
            chunks = process_file_into_chunks(
                db=db,
                file=file,
                user_id=user_id,
                subject_id=subject_id,
                unit_id=unit_id,
            )
            files_processed += 1
            total_chunks += len(chunks)
            total_tokens += sum(c.token_count for c in chunks)
    
    logger.info(
        f"Topic {topic.id}: processed {files_processed} files, "
        f"created {total_chunks} chunks, {total_tokens} total tokens"
    )
    
    return files_processed, total_chunks, total_tokens


def update_chunk_embedding_id(db: Session, chunk_id: int, embedding_id: int) -> Chunk:
    """
    Update a chunk's embedding ID after embedding.
    
    Args:
        db: Database session.
        chunk_id: The chunk ID.
        embedding_id: The FAISS index position.
        
    Returns:
        Updated chunk.
    """
    chunk = db.get(Chunk, chunk_id)
    if chunk:
        chunk.embedding_id = embedding_id
        db.commit()
        db.refresh(chunk)
    return chunk


def update_chunks_embedding_ids(
    db: Session,
    chunk_embedding_pairs: list[tuple[int, int]],
) -> int:
    """
    Update multiple chunks' embedding IDs.
    
    Args:
        db: Database session.
        chunk_embedding_pairs: List of (chunk_id, embedding_id) tuples.
        
    Returns:
        Number of chunks updated.
    """
    count = 0
    for chunk_id, embedding_id in chunk_embedding_pairs:
        chunk = db.get(Chunk, chunk_id)
        if chunk:
            chunk.embedding_id = embedding_id
            count += 1
    db.commit()
    return count


def get_chunks_by_ids(db: Session, chunk_ids: list[int]) -> list[Chunk]:
    """
    Get multiple chunks by their IDs.
    
    Args:
        db: Database session.
        chunk_ids: List of chunk IDs.
        
    Returns:
        List of chunks.
    """
    if not chunk_ids:
        return []
    
    stmt = select(Chunk).where(Chunk.id.in_(chunk_ids))
    return list(db.execute(stmt).scalars().all())
