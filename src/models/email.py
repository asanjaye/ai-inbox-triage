"""Email data models."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EmailCategory(str, Enum):
    SALES_LEAD = "sales_lead"
    SUPPORT_REQUEST = "support_request"
    INVOICE = "invoice"
    SCHEDULING = "scheduling"
    NEWSLETTER = "newsletter"
    SPAM = "spam"
    URGENT_ESCALATION = "urgent_escalation"
    PERSONAL = "personal"
    OTHER = "other"


class EmailPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Email(BaseModel):
    """Represents an incoming email."""
    id: str = Field(..., description="Unique email identifier")
    from_address: str = Field(..., description="Sender email address")
    from_name: Optional[str] = Field(None, description="Sender display name")
    to_address: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    received_at: datetime = Field(default_factory=datetime.utcnow)
    has_attachments: bool = Field(default=False)
    thread_id: Optional[str] = Field(None, description="Thread/conversation ID")
    
    # Ground truth labels for evaluation (optional)
    label_category: Optional[EmailCategory] = Field(None, description="Ground truth category")
    label_priority: Optional[EmailPriority] = Field(None, description="Ground truth priority")
    label_needs_reply: Optional[bool] = Field(None, description="Ground truth needs-reply flag")
