"""Email classification service."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Email, Classification, AuditAction, EmailCategory, EmailPriority
from ..database import ClassificationTable
from ..llm import LLMClassifier
from .audit_service import AuditService


class ClassificationService:
    """Service for classifying emails."""
    
    def __init__(
        self,
        session: AsyncSession,
        classifier: LLMClassifier,
        audit: AuditService,
    ):
        self.session = session
        self.classifier = classifier
        self.audit = audit
    
    async def classify_email(self, email: Email) -> Classification:
        """Classify an email and store the result."""
        existing = await self.get_classification(email.id)
        if existing:
            return existing
        
        try:
            classification = await self.classifier.classify(email)
            await self._save_classification(classification)
            
            await self.audit.log(
                action=AuditAction.EMAIL_CLASSIFIED,
                entity_type="email",
                entity_id=email.id,
                details={
                    "category": classification.category.value,
                    "priority": classification.priority.value,
                    "needs_reply": classification.needs_reply,
                    "model": classification.model_used,
                    "is_mock": classification.is_mock,
                },
            )
            
            return classification
            
        except Exception as e:
            await self.audit.log(
                action=AuditAction.CLASSIFICATION_ERROR,
                entity_type="email",
                entity_id=email.id,
                details={"error": str(e)},
            )
            raise
    
    async def _save_classification(self, classification: Classification) -> None:
        """Save classification to database."""
        db_classification = ClassificationTable(
            email_id=classification.email_id,
            category=classification.category.value,
            priority=classification.priority.value,
            needs_reply=classification.needs_reply,
            summary=classification.summary,
            confidence=classification.confidence,
            reasoning=classification.reasoning,
            classified_at=classification.classified_at,
            model_used=classification.model_used,
            is_mock=classification.is_mock,
        )
        self.session.add(db_classification)
        await self.session.commit()
    
    async def get_classification(self, email_id: str) -> Optional[Classification]:
        """Get classification for an email."""
        result = await self.session.execute(
            select(ClassificationTable).where(ClassificationTable.email_id == email_id)
        )
        row = result.scalar_one_or_none()
        
        if not row:
            return None
        
        return Classification(
            email_id=row.email_id,
            category=EmailCategory(row.category),
            priority=EmailPriority(row.priority),
            needs_reply=row.needs_reply,
            summary=row.summary,
            confidence=row.confidence,
            reasoning=row.reasoning,
            classified_at=row.classified_at,
            model_used=row.model_used,
            is_mock=row.is_mock,
        )
    
    async def list_classifications(self, limit: int = 50) -> list[Classification]:
        """List all classifications."""
        result = await self.session.execute(
            select(ClassificationTable)
            .order_by(ClassificationTable.classified_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        
        return [
            Classification(
                email_id=row.email_id,
                category=EmailCategory(row.category),
                priority=EmailPriority(row.priority),
                needs_reply=row.needs_reply,
                summary=row.summary,
                confidence=row.confidence,
                reasoning=row.reasoning,
                classified_at=row.classified_at,
                model_used=row.model_used,
                is_mock=row.is_mock,
            )
            for row in rows
        ]
