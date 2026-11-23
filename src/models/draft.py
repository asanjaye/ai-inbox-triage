"""Draft response models with approval workflow."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DraftStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT = "sent"


class Draft(BaseModel):
    """Auto-generated reply draft requiring human approval."""
    id: str = Field(..., description="Unique draft identifier")
    email_id: str = Field(..., description="Reference to original email")
    subject: str = Field(..., description="Reply subject line")
    body: str = Field(..., description="Draft reply content")
    status: DraftStatus = Field(default=DraftStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = Field(None)
    approved_by: Optional[str] = Field(None, description="User who approved")
    sent_at: Optional[datetime] = Field(None)
    rejection_reason: Optional[str] = Field(None)
    edit_history: list[dict] = Field(default_factory=list)


class DraftUpdateRequest(BaseModel):
    """Request to update draft content."""
    body: str = Field(..., min_length=1)
    subject: Optional[str] = None


class DraftApprovalRequest(BaseModel):
    """Request to approve a draft for sending."""
    approved_by: str = Field(..., min_length=1, description="User performing approval")


class DraftRejectionRequest(BaseModel):
    """Request to reject a draft."""
    rejected_by: str = Field(..., min_length=1)
    reason: Optional[str] = None
