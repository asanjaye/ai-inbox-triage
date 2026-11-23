"""Draft management service with HARD approval gate enforcement."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Email, Classification, Draft, DraftStatus, AuditAction,
)
from ..database import DraftTable
from ..llm.draft_generator import DraftGenerator
from .audit_service import AuditService


class ApprovalRequiredError(Exception):
    """Raised when attempting to send an unapproved draft."""
    pass


class DraftService:
    """
    Service for managing reply drafts with HARD approval gate.
    
    CRITICAL: No draft can be sent without explicit approval.
    The send method enforces this at the code level.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        audit: AuditService,
        draft_generator: Optional[DraftGenerator] = None,
    ):
        self.session = session
        self.audit = audit
        self.draft_generator = draft_generator or DraftGenerator(use_mock=True)
    
    async def create_draft(
        self, email: Email, classification: Classification
    ) -> Draft:
        """Generate and store a draft reply."""
        draft = await self.draft_generator.generate_draft(email, classification)
        await self._save_draft(draft)
        
        await self.audit.log(
            action=AuditAction.DRAFT_CREATED,
            entity_type="draft",
            entity_id=draft.id,
            details={
                "email_id": email.id,
                "category": classification.category.value,
            },
        )
        
        return draft
    
    async def _save_draft(self, draft: Draft) -> None:
        """Save draft to database."""
        db_draft = DraftTable(
            id=draft.id,
            email_id=draft.email_id,
            subject=draft.subject,
            body=draft.body,
            status=draft.status.value,
            created_at=draft.created_at,
            updated_at=draft.updated_at,
            edit_history=draft.edit_history,
        )
        self.session.add(db_draft)
        await self.session.commit()
    
    async def get_draft(self, draft_id: str) -> Optional[Draft]:
        """Get draft by ID."""
        result = await self.session.execute(
            select(DraftTable).where(DraftTable.id == draft_id)
        )
        row = result.scalar_one_or_none()
        
        if not row:
            return None
        
        return self._row_to_draft(row)
    
    async def get_draft_for_email(self, email_id: str) -> Optional[Draft]:
        """Get draft for a specific email."""
        result = await self.session.execute(
            select(DraftTable).where(DraftTable.email_id == email_id)
        )
        row = result.scalar_one_or_none()
        
        if not row:
            return None
        
        return self._row_to_draft(row)
    
    def _row_to_draft(self, row: DraftTable) -> Draft:
        """Convert database row to Draft model."""
        return Draft(
            id=row.id,
            email_id=row.email_id,
            subject=row.subject,
            body=row.body,
            status=DraftStatus(row.status),
            created_at=row.created_at,
            updated_at=row.updated_at,
            approved_at=row.approved_at,
            approved_by=row.approved_by,
            sent_at=row.sent_at,
            rejection_reason=row.rejection_reason,
            edit_history=row.edit_history or [],
        )
    
    async def update_draft(
        self, draft_id: str, body: str, subject: Optional[str] = None, editor: str = "user"
    ) -> Draft:
        """Update draft content."""
        result = await self.session.execute(
            select(DraftTable).where(DraftTable.id == draft_id)
        )
        row = result.scalar_one_or_none()
        
        if not row:
            raise ValueError(f"Draft not found: {draft_id}")
        
        old_body = row.body
        old_subject = row.subject
        
        history = row.edit_history or []
        history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "editor": editor,
            "old_body": old_body[:200],  # Truncate for storage
            "old_subject": old_subject,
        })
        
        row.body = body
        if subject:
            row.subject = subject
        row.updated_at = datetime.utcnow()
        row.edit_history = history
        
        if row.status == DraftStatus.APPROVED.value:
            row.status = DraftStatus.PENDING.value
            row.approved_at = None
            row.approved_by = None
        
        await self.session.commit()
        
        await self.audit.log(
            action=AuditAction.DRAFT_EDITED,
            entity_type="draft",
            entity_id=draft_id,
            actor=editor,
            details={"changes": "content_updated"},
        )
        
        return self._row_to_draft(row)
    
    async def approve_draft(self, draft_id: str, approved_by: str) -> Draft:
        """
        Approve a draft for sending.
        
        This is the ONLY way to mark a draft as approved.
        """
        result = await self.session.execute(
            select(DraftTable).where(DraftTable.id == draft_id)
        )
        row = result.scalar_one_or_none()
        
        if not row:
            raise ValueError(f"Draft not found: {draft_id}")
        
        if row.status == DraftStatus.SENT.value:
            raise ValueError("Cannot approve already sent draft")
        
        row.status = DraftStatus.APPROVED.value
        row.approved_at = datetime.utcnow()
        row.approved_by = approved_by
        row.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        await self.audit.log(
            action=AuditAction.DRAFT_APPROVED,
            entity_type="draft",
            entity_id=draft_id,
            actor=approved_by,
        )
        
        return self._row_to_draft(row)
    
    async def reject_draft(
        self, draft_id: str, rejected_by: str, reason: Optional[str] = None
    ) -> Draft:
        """Reject a draft."""
        result = await self.session.execute(
            select(DraftTable).where(DraftTable.id == draft_id)
        )
        row = result.scalar_one_or_none()
        
        if not row:
            raise ValueError(f"Draft not found: {draft_id}")
        
        row.status = DraftStatus.REJECTED.value
        row.rejection_reason = reason
        row.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        await self.audit.log(
            action=AuditAction.DRAFT_REJECTED,
            entity_type="draft",
            entity_id=draft_id,
            actor=rejected_by,
            details={"reason": reason},
        )
        
        return self._row_to_draft(row)
    
    async def can_send(self, draft_id: str) -> bool:
        """
        Check if a draft can be sent.
        
        HARD GATE: Only approved drafts can be sent.
        """
        draft = await self.get_draft(draft_id)
        if not draft:
            return False
        return draft.status == DraftStatus.APPROVED
    
    async def mark_sent(self, draft_id: str) -> Draft:
        """
        Mark a draft as sent (called by OutboxService after sending).
        
        HARD GATE: Raises ApprovalRequiredError if draft is not approved.
        """
        result = await self.session.execute(
            select(DraftTable).where(DraftTable.id == draft_id)
        )
        row = result.scalar_one_or_none()
        
        if not row:
            raise ValueError(f"Draft not found: {draft_id}")
        
        if row.status != DraftStatus.APPROVED.value:
            await self.audit.log(
                action=AuditAction.SEND_BLOCKED,
                entity_type="draft",
                entity_id=draft_id,
                details={
                    "current_status": row.status,
                    "reason": "HARD_GATE_UNAPPROVED",
                },
            )
            raise ApprovalRequiredError(
                f"Cannot send draft {draft_id}: status is {row.status}, "
                f"must be {DraftStatus.APPROVED.value}. "
                "Human approval is REQUIRED before sending."
            )
        
        row.status = DraftStatus.SENT.value
        row.sent_at = datetime.utcnow()
        row.updated_at = datetime.utcnow()
        
        await self.session.commit()
        
        await self.audit.log(
            action=AuditAction.DRAFT_SENT,
            entity_type="draft",
            entity_id=draft_id,
        )
        
        return self._row_to_draft(row)
    
    async def list_drafts(
        self,
        status: Optional[DraftStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Draft]:
        """List drafts with optional status filter."""
        query = select(DraftTable)
        
        if status:
            query = query.where(DraftTable.status == status.value)
        
        query = query.order_by(DraftTable.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        rows = result.scalars().all()
        
        return [self._row_to_draft(row) for row in rows]
    
    async def get_pending_queue(self) -> list[Draft]:
        """Get all pending drafts awaiting approval."""
        return await self.list_drafts(status=DraftStatus.PENDING)
