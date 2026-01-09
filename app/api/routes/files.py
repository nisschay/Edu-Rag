"""
File upload API routes.

Provides endpoints for uploading and managing files attached to topics.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile, status, BackgroundTasks

from app.api.deps import CurrentUser, DbSession
from app.schemas.file import FileList, FileRead, FileWithText, UploadResponse
from app.services import subject_service, unit_service, topic_service, file_service, processing_service
from app.models.unit_processing_state import UnitProcessingState
from app.models.unit import Unit
from app.utils.text_extraction import (
    extract_text,
    get_file_extension,
    is_supported_file,
    ExtractionError,
    SUPPORTED_EXTENSIONS,
)
from app.utils.file_storage import (
    save_file,
    get_file_size,
    validate_file_size,
    MAX_FILE_SIZE,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/subjects/{subject_id}/units/{unit_id}/topics/{topic_id}/files",
    tags=["Files"],
)


def validate_topic_ownership(
    db: DbSession,
    subject_id: int,
    unit_id: int,
    topic_id: int,
    user_id: int,
) -> None:
    """
    Validate the full ownership chain: user -> subject -> unit -> topic.
    
    Raises:
        HTTPException: If any part of the chain is invalid.
    """
    # Validate subject ownership
    subject = subject_service.get_subject_for_user(db, subject_id, user_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )
    
    # Validate unit belongs to subject
    unit = unit_service.get_unit_for_subject(db, unit_id, subject_id)
    if unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found",
        )
    
    # Validate topic belongs to unit
    topic = topic_service.get_topic_for_unit(db, topic_id, unit_id)
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload File",
    description=f"Upload a file to a topic. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}. Max size: {MAX_FILE_SIZE // (1024*1024)}MB.",
)
async def upload_file(
    db: DbSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    subject_id: int,
    unit_id: int,
    topic_id: int,
    file: UploadFile = File(..., description="File to upload"),
) -> UploadResponse:
    """
    Upload a file to a topic.
    
    The file will be:
    1. Validated for type and size
    2. Saved to disk
    3. Metadata stored in database (status: pending)
    4. Processing task added to background queue
    """
    # Validate ownership chain
    validate_topic_ownership(db, subject_id, unit_id, topic_id, current_user.id)
    
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    
    if not is_supported_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if not validate_file_size(content):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )
    
    # Get file metadata
    file_type = get_file_extension(file.filename)
    file_size = get_file_size(content)
    
    # Save file to disk
    try:
        unique_filename, filepath = save_file(
            content=content,
            original_filename=file.filename,
            subject_id=subject_id,
            unit_id=unit_id,
            topic_id=topic_id,
        )
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file",
        )
    
    # Create database record (status: pending - conceptually, but strictly controlled by Unit State)
    db_file = file_service.create_file(
        db=db,
        topic_id=topic_id,
        filename=file.filename,
        filepath=str(filepath),
        file_type=file_type,
        file_size=file_size,
    )
    
    # --- CRITICAL: Unit State Update ---
    # 1. Get Unit
    unit = unit_service.get_unit_for_subject(db, unit_id, subject_id) # Validated above but need object
    
    # 2. Get/Create State
    if not unit.processing_state:
        unit.processing_state = UnitProcessingState(unit_id=unit.id)
        db.add(unit.processing_state)
        db.commit()
    
    # 3. Set Status = UPLOADED
    unit.processing_state.status = "uploaded"
    unit.processing_state.has_files = True
    # Clear error on new upload
    unit.processing_state.last_error = None
    db.commit()
    
    # 4. Trigger Unit Background Processing
    # We cancel any existing tasks implicitly by overwriting status? 
    # Background task will check status but strict serial pipeline means we just start a new one.
    # Ideally we'd kill old one but for now we just launch new one.
    background_tasks.add_task(processing_service.process_unit_background, unit.id)
    
    logger.info(f"Upload: File {db_file.id} saved. Unit {unit_id} marked 'uploaded'. Pipeline triggered.")

    return UploadResponse(
        message="File uploaded. Unit processing started.",
        file=FileRead.model_validate(db_file),
        text_preview="Processing in background...",
    )


@router.get(
    "/{file_id}/status",
    response_model=FileRead,
    summary="Get File Status",
    description="Check the processing status of a file.",
)
def get_file_status(
    db: DbSession,
    current_user: CurrentUser,
    subject_id: int,
    unit_id: int,
    topic_id: int,
    file_id: int,
) -> FileRead:
    """
    Check the processing status of a file.
    """
    validate_topic_ownership(db, subject_id, unit_id, topic_id, current_user.id)
    
    file = file_service.get_file_for_topic(db, file_id, topic_id)
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    return FileRead.model_validate(file)


@router.get(
    "",
    response_model=FileList,
    summary="List Files",
    description="List all files for a topic.",
)
def list_files(
    db: DbSession,
    current_user: CurrentUser,
    subject_id: int,
    unit_id: int,
    topic_id: int,
) -> FileList:
    """
    List all files uploaded to a topic.
    
    Example Response:
        {
            "files": [
                {"id": 1, "topic_id": 1, "filename": "notes.pdf", ...},
                {"id": 2, "topic_id": 1, "filename": "slides.pptx", ...}
            ],
            "count": 2
        }
    """
    validate_topic_ownership(db, subject_id, unit_id, topic_id, current_user.id)
    
    files = file_service.list_files_for_topic(db, topic_id)
    return FileList(
        files=[FileRead.model_validate(f) for f in files],
        count=len(files),
    )


@router.get(
    "/{file_id}",
    response_model=FileRead,
    summary="Get File",
    description="Get file metadata by ID.",
)
def get_file(
    db: DbSession,
    current_user: CurrentUser,
    subject_id: int,
    unit_id: int,
    topic_id: int,
    file_id: int,
) -> FileRead:
    """
    Get file metadata by ID.
    """
    validate_topic_ownership(db, subject_id, unit_id, topic_id, current_user.id)
    
    file = file_service.get_file_for_topic(db, file_id, topic_id)
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    return FileRead.model_validate(file)


@router.get(
    "/{file_id}/text",
    response_model=FileWithText,
    summary="Get Extracted Text (Debug)",
    description="Get file metadata with extracted text content. Debug endpoint.",
)
def get_file_text(
    db: DbSession,
    current_user: CurrentUser,
    subject_id: int,
    unit_id: int,
    topic_id: int,
    file_id: int,
) -> FileWithText:
    """
    Get file with extracted text content.
    
    This is a debug endpoint to verify text extraction.
    
    Example Response:
        {
            "id": 1,
            "topic_id": 1,
            "filename": "lecture_notes.pdf",
            "file_type": "pdf",
            "file_size": 102400,
            "created_at": "2026-01-06T12:00:00",
            "extracted_text": "Chapter 1: Introduction...",
            "text_length": 15432
        }
    """
    validate_topic_ownership(db, subject_id, unit_id, topic_id, current_user.id)
    
    file = file_service.get_file_for_topic(db, file_id, topic_id)
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    return FileWithText(
        id=file.id,
        topic_id=file.topic_id,
        filename=file.filename,
        file_type=file.file_type,
        file_size=file.file_size,
        created_at=file.created_at,
        extracted_text=file.extracted_text,
        text_length=len(file.extracted_text) if file.extracted_text else 0,
    )
