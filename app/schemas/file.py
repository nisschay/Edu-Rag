"""
File Pydantic schemas for request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class FileBase(BaseModel):
    """Base schema with common file fields."""
    
    filename: str


class FileRead(FileBase):
    """
    Schema for reading file metadata.
    
    Example:
        {
            "id": 1,
            "topic_id": 1,
            "filename": "lecture_notes.pdf",
            "file_type": "pdf",
            "file_size": 102400,
            "created_at": "2026-01-06T12:00:00"
        }
    """
    
    id: int
    topic_id: int
    file_type: str
    file_size: int
    status: str
    processing_error: str | None = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class FileList(BaseModel):
    """
    Schema for listing files.
    
    Example:
        {
            "files": [
                {"id": 1, "topic_id": 1, "filename": "notes.pdf", ...},
                {"id": 2, "topic_id": 1, "filename": "slides.pptx", ...}
            ],
            "count": 2
        }
    """
    
    files: list[FileRead]
    count: int


class FileWithText(FileRead):
    """
    Schema for file with extracted text (debug endpoint).
    
    Example:
        {
            "id": 1,
            "topic_id": 1,
            "filename": "lecture_notes.pdf",
            "file_type": "pdf",
            "file_size": 102400,
            "created_at": "2026-01-06T12:00:00",
            "extracted_text": "Chapter 1: Introduction..."
        }
    """
    
    extracted_text: str | None = None
    text_length: int = Field(default=0, description="Length of extracted text")
    
    @classmethod
    def from_file(cls, file: "FileRead", extracted_text: str | None) -> "FileWithText":
        """Create FileWithText from file and text."""
        return cls(
            id=file.id,
            topic_id=file.topic_id,
            filename=file.filename,
            file_type=file.file_type,
            file_size=file.file_size,
            created_at=file.created_at,
            extracted_text=extracted_text,
            text_length=len(extracted_text) if extracted_text else 0,
        )


class UploadResponse(BaseModel):
    """
    Response after successful file upload.
    
    Example:
        {
            "message": "File uploaded successfully",
            "file": {...},
            "text_preview": "Chapter 1: Introduction to..."
        }
    """
    
    message: str
    file: FileRead
    text_preview: str = Field(
        default="",
        description="First 500 characters of extracted text",
    )
