"""Draft management endpoints with approval workflow."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_session
from ...models import Draft, DraftStatus
from ...services import (
    DraftService, AuditService, EmailService, 
    ClassificationService, OutboxService,
)
from ...services.draft_service import ApprovalRequiredError
from ...llm import get_classifier
from ...llm.draft_generator import DraftGenerator
from ...config import get_settings

router = APIRouter()


class DraftUpdateRequest(BaseModel):
    body: str
    subject: Optional[str] = None
    editor: str = "user"


class ApprovalRequest(BaseModel):
    approved_by: str


class RejectionRequest(BaseModel):
    rejected_by: str
    reason: Optional[str] = None


async def get_services(session: AsyncSession = Depends(get_session)):
    """Get all required services."""
    audit = AuditService(session)
    email_service = EmailService(session, audit)
    settings = get_settings()
    draft_generator = DraftGenerator(use_mock=settings.mock_mode)
    draft_service = DraftService(session, audit, draft_generator)
    classifier = get_classifier()
    classification_service = ClassificationService(session, classifier, audit)
    outbox_service = OutboxService(session, draft_service, email_service)
    
    return {
        "audit": audit,
        "email": email_service,
        "draft": draft_service,
        "classification": classification_service,
        "outbox": outbox_service,
    }


@router.get("/", response_model=list[Draft])
async def list_drafts(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    services: dict = Depends(get_services),
):
    """List drafts with optional status filter."""
    draft_status = DraftStatus(status) if status else None
    return await services["draft"].list_drafts(
        status=draft_status, limit=limit, offset=offset
    )


@router.get("/pending", response_model=list[Draft])
async def get_pending_queue(services: dict = Depends(get_services)):
    """Get all drafts pending approval."""
    return await services["draft"].get_pending_queue()


@router.get("/{draft_id}", response_model=Draft)
async def get_draft(draft_id: str, services: dict = Depends(get_services)):
    """Get a specific draft."""
    draft = await services["draft"].get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.post("/generate/{email_id}", response_model=Draft)
async def generate_draft(email_id: str, services: dict = Depends(get_services)):
    """Generate a draft reply for an email."""
    email = await services["email"].get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    classification = await services["classification"].get_classification(email_id)
    if not classification:
        classification = await services["classification"].classify_email(email)
    
    existing_draft = await services["draft"].get_draft_for_email(email_id)
    if existing_draft:
        return existing_draft
    
    return await services["draft"].create_draft(email, classification)


@router.put("/{draft_id}", response_model=Draft)
async def update_draft(
    draft_id: str,
    request: DraftUpdateRequest,
    services: dict = Depends(get_services),
):
    """Update draft content."""
    try:
        return await services["draft"].update_draft(
            draft_id, request.body, request.subject, request.editor
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{draft_id}/approve", response_model=Draft)
async def approve_draft(
    draft_id: str,
    request: ApprovalRequest,
    services: dict = Depends(get_services),
):
    """
    Approve a draft for sending.
    
    This is the REQUIRED step before any draft can be sent.
    """
    try:
        return await services["draft"].approve_draft(draft_id, request.approved_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{draft_id}/reject", response_model=Draft)
async def reject_draft(
    draft_id: str,
    request: RejectionRequest,
    services: dict = Depends(get_services),
):
    """Reject a draft."""
    try:
        return await services["draft"].reject_draft(
            draft_id, request.rejected_by, request.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{draft_id}/send")
async def send_draft(draft_id: str, services: dict = Depends(get_services)):
    """
    Send an approved draft.
    
    HARD GATE: Will fail if draft is not approved.
    Note: This uses a mock outbox - no actual emails are sent.
    """
    try:
        outbox_msg = await services["outbox"].send_draft(draft_id)
        return {
            "status": "queued",
            "outbox_id": outbox_msg.id,
            "to": outbox_msg.to_address,
            "subject": outbox_msg.subject,
            "note": "Mock outbox - no actual email sent",
        }
    except ApprovalRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{draft_id}/can-send")
async def check_can_send(draft_id: str, services: dict = Depends(get_services)):
    """Check if a draft can be sent (is approved)."""
    can_send = await services["draft"].can_send(draft_id)
    draft = await services["draft"].get_draft(draft_id)
    
    return {
        "draft_id": draft_id,
        "can_send": can_send,
        "status": draft.status.value if draft else None,
        "reason": "Approved" if can_send else "Human approval required",
    }
