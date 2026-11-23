"""Audit logging models."""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    EMAIL_RECEIVED = "email_received"
    EMAIL_CLASSIFIED = "email_classified"
    DRAFT_CREATED = "draft_created"
    DRAFT_EDITED = "draft_edited"
    DRAFT_APPROVED = "draft_approved"
    DRAFT_REJECTED = "draft_rejected"
    DRAFT_SENT = "draft_sent"
    SEND_BLOCKED = "send_blocked"
    CLASSIFICATION_ERROR = "classification_error"


class AuditLog(BaseModel):
    """Immutable audit log entry."""
    id: str = Field(..., description="Unique log entry ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: AuditAction
    entity_type: str = Field(..., description="Type of entity (email, draft, etc.)")
    entity_id: str = Field(..., description="ID of the affected entity")
    actor: str = Field(default="system", description="User or system that performed action")
    details: Optional[dict[str, Any]] = Field(None, description="Additional context")
    
    model_config = {"frozen": True}  # Audit logs are immutable
