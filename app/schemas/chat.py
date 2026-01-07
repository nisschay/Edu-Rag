"""
Pydantic schemas for Chat functionality.

Provides validation and serialization for chat operations.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


# Intent types for query classification
IntentType = Literal[
    "teach_from_start",
    "explain_topic", 
    "explain_detail",
    "revise",
    "generate_questions"
]


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    
    message: str = Field(..., min_length=1, description="User's message")
    unit_id: int | None = Field(
        default=None, 
        description="Optional unit scope"
    )
    topic_id: int | None = Field(
        default=None, 
        description="Optional topic scope"
    )


class SourceReference(BaseModel):
    """Reference to a source used in the response."""
    
    source_type: Literal["chunk", "topic_summary", "unit_summary"]
    source_id: int
    score: float = Field(default=0.0, description="Relevance score")
    preview: str = Field(default="", description="Text preview")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    
    answer: str = Field(..., description="Generated answer")
    intent: IntentType = Field(..., description="Classified intent")
    sources: list[SourceReference] = Field(
        default_factory=list,
        description="Sources used to generate the answer"
    )
    subject_id: int
    unit_id: int | None = None
    topic_id: int | None = None


class IntentClassification(BaseModel):
    """Result of intent classification."""
    
    intent: IntentType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: str = Field(default="", description="Why this intent was chosen")
