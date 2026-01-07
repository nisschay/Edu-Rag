"""
Pydantic schemas package.

Contains request/response schemas for API endpoints.
Organized by domain: user, subject, unit, topic, file, chunk, summary, chat.
"""

from app.schemas.user import UserCreate, UserRead
from app.schemas.subject import SubjectCreate, SubjectRead, SubjectList
from app.schemas.unit import UnitCreate, UnitRead, UnitList
from app.schemas.topic import TopicCreate, TopicRead, TopicList
from app.schemas.file import FileRead, FileList, FileWithText, UploadResponse
from app.schemas.chunk import (
    ChunkRead,
    ChunkList,
    ChunkWithScore,
    ChunkingResponse,
    EmbeddingResponse,
    RetrievalRequest,
    RetrievalResponse,
)
from app.schemas.summary import (
    TopicSummaryRead,
    TopicSummaryResponse,
    UnitSummaryRead,
    UnitSummaryResponse,
    EmbedSummariesResponse,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceReference,
    IntentClassification,
)

__all__ = [
    # User
    "UserCreate",
    "UserRead",
    # Subject
    "SubjectCreate",
    "SubjectRead",
    "SubjectList",
    # Unit
    "UnitCreate",
    "UnitRead",
    "UnitList",
    # Topic
    "TopicCreate",
    "TopicRead",
    "TopicList",
    # File
    "FileRead",
    "FileList",
    "FileWithText",
    "UploadResponse",
    # Chunk
    "ChunkRead",
    "ChunkList",
    "ChunkWithScore",
    "ChunkingResponse",
    "EmbeddingResponse",
    "RetrievalRequest",
    "RetrievalResponse",
    # Summary
    "TopicSummaryRead",
    "TopicSummaryResponse",
    "UnitSummaryRead",
    "UnitSummaryResponse",
    "EmbedSummariesResponse",
    # Chat
    "ChatRequest",
    "ChatResponse",
    "SourceReference",
    "IntentClassification",
]
