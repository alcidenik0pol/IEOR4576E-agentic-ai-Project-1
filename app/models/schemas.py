"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    question: str = Field(..., min_length=1, max_length=2000, description="User question about HuggingFace models")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    answer: str = Field(..., description="The chatbot's answer")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0 to 1")
    sources: list[str] = Field(default_factory=list, description="Model IDs referenced in the answer")
    out_of_scope: bool = Field(..., description="Whether the question was detected as out of scope")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = "ok"
    model_count: int = Field(..., description="Number of models in the snapshot")
    snapshot_date: str = Field(..., description="Date of the data snapshot")
    llm_available: bool = Field(default=False, description="Whether the LLM is initialized and ready")
