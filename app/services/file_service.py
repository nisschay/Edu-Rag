"""
File service for file-related database operations.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file import File
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_file_by_id(db: Session, file_id: int) -> File | None:
    """
    Get a file by ID.
    
    Args:
        db: Database session.
        file_id: File ID to look up.
        
    Returns:
        File if found, None otherwise.
    """
    return db.get(File, file_id)


def get_file_for_topic(
    db: Session,
    file_id: int,
    topic_id: int,
) -> File | None:
    """
    Get a file by ID, ensuring it belongs to the specified topic.
    
    Args:
        db: Database session.
        file_id: File ID to look up.
        topic_id: Topic ID that must own the file.
        
    Returns:
        File if found and belongs to topic, None otherwise.
    """
    stmt = select(File).where(
        File.id == file_id,
        File.topic_id == topic_id,
    )
    return db.scalar(stmt)


def list_files_for_topic(db: Session, topic_id: int) -> list[File]:
    """
    List all files for a topic.
    
    Args:
        db: Database session.
        topic_id: Topic ID to list files for.
        
    Returns:
        List of files ordered by creation time.
    """
    stmt = (
        select(File)
        .where(File.topic_id == topic_id)
        .order_by(File.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def create_file(
    db: Session,
    topic_id: int,
    filename: str,
    filepath: str,
    file_type: str,
    file_size: int,
    extracted_text: str | None = None,
) -> File:
    """
    Create a new file record.
    
    Args:
        db: Database session.
        topic_id: ID of the parent topic.
        filename: Original filename.
        filepath: Path to stored file.
        file_type: File extension.
        file_size: Size in bytes.
        extracted_text: Extracted text content.
        
    Returns:
        Created file instance.
    """
    file = File(
        topic_id=topic_id,
        filename=filename,
        filepath=filepath,
        file_type=file_type,
        file_size=file_size,
        extracted_text=extracted_text,
    )
    db.add(file)
    db.commit()
    db.refresh(file)
    logger.info(f"Created file record: {file.id} - {filename}")
    return file


def delete_file_record(db: Session, file_id: int) -> bool:
    """
    Delete a file record from database.
    
    Args:
        db: Database session.
        file_id: File ID to delete.
        
    Returns:
        True if deleted, False if not found.
    """
    file = get_file_by_id(db, file_id)
    if file is None:
        return False
    
    db.delete(file)
    db.commit()
    logger.info(f"Deleted file record: {file_id}")
    return True
