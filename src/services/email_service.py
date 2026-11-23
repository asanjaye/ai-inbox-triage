"""Email management service."""
from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Email, AuditAction
from ..database import EmailTable
from ..email_sources import EmailSource
from .audit_service import AuditService


class EmailService:
    """Service for managing emails in the system."""
    
    def __init__(self, session: AsyncSession, audit: AuditService):
        self.session = session
        self.audit = audit
    
    async def import_from_source(self, source: EmailSource, limit: Optional[int] = None) -> list[Email]:
        """Import emails from an email source."""
        await source.connect()
        imported = []
        
        try:
            async for email in source.fetch_emails(limit=limit):
                existing = await self.get_email(email.id)
                if existing:
                    continue
                
                await self._save_email(email)
                await self.audit.log(
                    action=AuditAction.EMAIL_RECEIVED,
                    entity_type="email",
                    entity_id=email.id,
                    details={
                        "from": email.from_address,
                        "subject": email.subject,
                        "source": source.source_type,
                    },
                )
                imported.append(email)
                await source.mark_processed(email.id)
        finally:
            await source.disconnect()
        
        return imported
    
    async def _save_email(self, email: Email) -> None:
        """Save email to database."""
        db_email = EmailTable(
            id=email.id,
            from_address=email.from_address,
            from_name=email.from_name,
            to_address=email.to_address,
            subject=email.subject,
            body=email.body,
            received_at=email.received_at,
            has_attachments=email.has_attachments,
            thread_id=email.thread_id,
            label_category=email.label_category.value if email.label_category else None,
            label_priority=email.label_priority.value if email.label_priority else None,
            label_needs_reply=email.label_needs_reply,
        )
        self.session.add(db_email)
        await self.session.commit()
    
    async def get_email(self, email_id: str) -> Optional[Email]:
        """Get email by ID."""
        result = await self.session.execute(
            select(EmailTable).where(EmailTable.id == email_id)
        )
        row = result.scalar_one_or_none()
        
        if not row:
            return None
        
        from ..models import EmailCategory, EmailPriority
        return Email(
            id=row.id,
            from_address=row.from_address,
            from_name=row.from_name,
            to_address=row.to_address,
            subject=row.subject,
            body=row.body,
            received_at=row.received_at,
            has_attachments=row.has_attachments,
            thread_id=row.thread_id,
            label_category=EmailCategory(row.label_category) if row.label_category else None,
            label_priority=EmailPriority(row.label_priority) if row.label_priority else None,
            label_needs_reply=row.label_needs_reply,
        )
    
    async def list_emails(self, limit: int = 50, offset: int = 0) -> list[Email]:
        """List emails ordered by received date."""
        from ..models import EmailCategory, EmailPriority
        
        result = await self.session.execute(
            select(EmailTable)
            .order_by(EmailTable.received_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = result.scalars().all()
        
        return [
            Email(
                id=row.id,
                from_address=row.from_address,
                from_name=row.from_name,
                to_address=row.to_address,
                subject=row.subject,
                body=row.body,
                received_at=row.received_at,
                has_attachments=row.has_attachments,
                thread_id=row.thread_id,
                label_category=EmailCategory(row.label_category) if row.label_category else None,
                label_priority=EmailPriority(row.label_priority) if row.label_priority else None,
                label_needs_reply=row.label_needs_reply,
            )
            for row in rows
        ]
