"""
File storage utilities for handling file uploads.

Manages file storage on disk with organized directory structure.
"""

import os
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Base upload directory
UPLOAD_DIR = Path("data/uploads")


def ensure_upload_dir() -> Path:
    """
    Ensure upload directory exists.
    
    Returns:
        Path to upload directory.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def get_topic_upload_dir(subject_id: int, unit_id: int, topic_id: int) -> Path:
    """
    Get upload directory for a specific topic.
    
    Creates directory structure: data/uploads/subject_{id}/unit_{id}/topic_{id}/
    
    Args:
        subject_id: Subject ID.
        unit_id: Unit ID.
        topic_id: Topic ID.
        
    Returns:
        Path to topic's upload directory.
    """
    topic_dir = UPLOAD_DIR / f"subject_{subject_id}" / f"unit_{unit_id}" / f"topic_{topic_id}"
    topic_dir.mkdir(parents=True, exist_ok=True)
    return topic_dir


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate unique filename to prevent collisions.
    
    Preserves original extension but adds UUID prefix.
    
    Args:
        original_filename: Original uploaded filename.
        
    Returns:
        Unique filename with UUID prefix.
    """
    ext = Path(original_filename).suffix
    unique_id = uuid.uuid4().hex[:12]
    safe_name = Path(original_filename).stem[:50]  # Limit length
    # Remove unsafe characters
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in safe_name)
    return f"{unique_id}_{safe_name}{ext}"


def save_file(
    content: bytes,
    original_filename: str,
    subject_id: int,
    unit_id: int,
    topic_id: int,
) -> tuple[str, Path]:
    """
    Save uploaded file to disk.
    
    Args:
        content: File content as bytes.
        original_filename: Original filename.
        subject_id: Subject ID for directory structure.
        unit_id: Unit ID for directory structure.
        topic_id: Topic ID for directory structure.
        
    Returns:
        Tuple of (unique_filename, full_path).
    """
    ensure_upload_dir()
    topic_dir = get_topic_upload_dir(subject_id, unit_id, topic_id)
    
    unique_filename = generate_unique_filename(original_filename)
    filepath = topic_dir / unique_filename
    
    # Write file
    filepath.write_bytes(content)
    logger.info(f"Saved file: {filepath}")
    
    return unique_filename, filepath


def delete_file(filepath: str) -> bool:
    """
    Delete a file from disk.
    
    Args:
        filepath: Path to file.
        
    Returns:
        True if deleted, False if not found.
    """
    try:
        path = Path(filepath)
        if path.exists():
            path.unlink()
            logger.info(f"Deleted file: {filepath}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete file {filepath}: {e}")
        return False


def get_file_size(content: bytes) -> int:
    """
    Get file size in bytes.
    
    Args:
        content: File content.
        
    Returns:
        Size in bytes.
    """
    return len(content)


# Maximum file size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_file_size(content: bytes) -> bool:
    """
    Check if file size is within limits.
    
    Args:
        content: File content.
        
    Returns:
        True if size is acceptable.
    """
    return len(content) <= MAX_FILE_SIZE
