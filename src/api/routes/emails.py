"""Email management endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_session
from ...models import Email
from ...services import EmailService, AuditService
from ...email_sources import JsonEmailSource
from ...config import get_settings

router = APIRouter()


async def get_email_service(session: AsyncSession = Depends(get_session)) -> EmailService:
    audit = AuditService(session)
    return EmailService(session, audit)


@router.get("/", response_model=list[Email])
async def list_emails(
    limit: int = 50,
    offset: int = 0,
    service: EmailService = Depends(get_email_service),
):
    """List all emails in the system."""
    return await service.list_emails(limit=limit, offset=offset)


@router.get("/{email_id}", response_model=Email)
async def get_email(
    email_id: str,
    service: EmailService = Depends(get_email_service),
):
    """Get a specific email by ID."""
    email = await service.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.post("/import", response_model=list[Email])
async def import_emails(
    limit: Optional[int] = None,
    service: EmailService = Depends(get_email_service),
):
    """Import emails from configured source."""
    settings = get_settings()
    
    if settings.email_source == "json":
        source = JsonEmailSource(settings.email_source_path)
    else:
        raise HTTPException(
            status_code=501,
            detail=f"Email source '{settings.email_source}' not implemented"
        )
    
    return await service.import_from_source(source, limit=limit)
