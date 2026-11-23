"""Classification endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_session
from ...models import Classification
from ...services import ClassificationService, AuditService, EmailService
from ...llm import get_classifier

router = APIRouter()


async def get_classification_service(
    session: AsyncSession = Depends(get_session),
) -> ClassificationService:
    audit = AuditService(session)
    classifier = get_classifier()
    return ClassificationService(session, classifier, audit)


async def get_email_service(session: AsyncSession = Depends(get_session)) -> EmailService:
    audit = AuditService(session)
    return EmailService(session, audit)


@router.get("/", response_model=list[Classification])
async def list_classifications(
    limit: int = 50,
    service: ClassificationService = Depends(get_classification_service),
):
    """List all classifications."""
    return await service.list_classifications(limit=limit)


@router.get("/{email_id}", response_model=Classification)
async def get_classification(
    email_id: str,
    service: ClassificationService = Depends(get_classification_service),
):
    """Get classification for a specific email."""
    classification = await service.get_classification(email_id)
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    return classification


@router.post("/{email_id}", response_model=Classification)
async def classify_email(
    email_id: str,
    classification_service: ClassificationService = Depends(get_classification_service),
    email_service: EmailService = Depends(get_email_service),
):
    """Classify an email."""
    email = await email_service.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return await classification_service.classify_email(email)
