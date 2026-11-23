"""Classification result models."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .email import EmailCategory, EmailPriority


class Classification(BaseModel):
    """LLM classification result for an email."""
    email_id: str = Field(..., description="Reference to the classified email")
    category: EmailCategory = Field(..., description="Determined email category")
    priority: EmailPriority = Field(..., description="Determined priority level")
    needs_reply: bool = Field(..., description="Whether email requires a response")
    summary: str = Field(..., description="Brief summary of email content")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Classification confidence")
    reasoning: Optional[str] = Field(None, description="LLM reasoning for classification")
    classified_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = Field(default="", description="Model that performed classification")
    is_mock: bool = Field(default=False, description="Whether mock mode was used")


class ClassificationRequest(BaseModel):
    """Request schema for classifying an email."""
    email_id: str


class ClassificationResponse(BaseModel):
    """Response schema for classification endpoint."""
    classification: Classification
    draft_created: bool = Field(default=False)
