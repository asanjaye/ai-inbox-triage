"""High-level triage workflow endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_session
from ...models import Email, Classification, Draft
from ...services import (
    EmailService, ClassificationService, DraftService, AuditService,
)
from ...email_sources import JsonEmailSource
from ...llm import get_classifier
from ...llm.draft_generator import DraftGenerator
from ...config import get_settings

router = APIRouter()


class TriageResult(BaseModel):
    email: Email
    classification: Classification
    draft: Optional[Draft] = None


class TriageSummary(BaseModel):
    total_emails: int
    classified: int
    drafts_created: int
    by_category: dict[str, int]
    by_priority: dict[str, int]
    needs_reply: int


async def get_services(session: AsyncSession = Depends(get_session)):
    """Get all required services."""
    audit = AuditService(session)
    email_service = EmailService(session, audit)
    classifier = get_classifier()
    classification_service = ClassificationService(session, classifier, audit)
    settings = get_settings()
    draft_generator = DraftGenerator(use_mock=settings.mock_mode)
    draft_service = DraftService(session, audit, draft_generator)
    
    return {
        "email": email_service,
        "classification": classification_service,
        "draft": draft_service,
        "audit": audit,
    }


@router.post("/process-all", response_model=TriageSummary)
async def process_all_emails(
    import_new: bool = True,
    generate_drafts: bool = True,
    limit: Optional[int] = None,
    services: dict = Depends(get_services),
):
    """
    Full triage workflow: import, classify, and generate drafts.
    
    Args:
        import_new: Whether to import new emails from source
        generate_drafts: Whether to generate drafts for emails needing replies
        limit: Maximum emails to process
    """
    settings = get_settings()
    
    if import_new:
        source = JsonEmailSource(settings.email_source_path)
        await services["email"].import_from_source(source, limit=limit)
    
    emails = await services["email"].list_emails(limit=limit or 100)
    
    by_category: dict[str, int] = {}
    by_priority: dict[str, int] = {}
    needs_reply = 0
    drafts_created = 0
    
    for email in emails:
        classification = await services["classification"].get_classification(email.id)
        if not classification:
            classification = await services["classification"].classify_email(email)
        
        cat = classification.category.value
        pri = classification.priority.value
        by_category[cat] = by_category.get(cat, 0) + 1
        by_priority[pri] = by_priority.get(pri, 0) + 1
        
        if classification.needs_reply:
            needs_reply += 1
            
            if generate_drafts:
                existing = await services["draft"].get_draft_for_email(email.id)
                if not existing:
                    await services["draft"].create_draft(email, classification)
                    drafts_created += 1
    
    return TriageSummary(
        total_emails=len(emails),
        classified=len(emails),
        drafts_created=drafts_created,
        by_category=by_category,
        by_priority=by_priority,
        needs_reply=needs_reply,
    )


@router.get("/email/{email_id}", response_model=TriageResult)
async def get_triage_result(
    email_id: str,
    services: dict = Depends(get_services),
):
    """Get complete triage result for an email."""
    email = await services["email"].get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    classification = await services["classification"].get_classification(email_id)
    if not classification:
        raise HTTPException(status_code=404, detail="Email not classified yet")
    
    draft = await services["draft"].get_draft_for_email(email_id)
    
    return TriageResult(
        email=email,
        classification=classification,
        draft=draft,
    )


@router.get("/queue")
async def get_review_queue(services: dict = Depends(get_services)):
    """Get emails and drafts requiring review, organized by priority."""
    emails = await services["email"].list_emails(limit=100)
    
    queue = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
    }
    
    for email in emails:
        classification = await services["classification"].get_classification(email.id)
        if not classification:
            continue
        
        if not classification.needs_reply:
            continue
        
        draft = await services["draft"].get_draft_for_email(email.id)
        if draft and draft.status.value in ["sent", "rejected"]:
            continue
        
        item = {
            "email": email.model_dump(),
            "classification": classification.model_dump(),
            "draft": draft.model_dump() if draft else None,
        }
        
        queue[classification.priority.value].append(item)
    
    return {
        "queue": queue,
        "total_pending": sum(len(v) for v in queue.values()),
    }
