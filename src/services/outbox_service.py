"""Outbox service - mock email sending with approval enforcement."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Draft, Email
from ..database import OutboxTable
from .draft_service import DraftService, ApprovalRequiredError
from .email_service import EmailService


class OutboxMessage:
    """Represents a message in the outbox."""
    def __init__(
        self,
        id: str,
        draft_id: str,
        to_address: str,
        subject: str,
        body: str,
        queued_at: datetime,
    ):
        self.id = id
        self.draft_id = draft_id
        self.to_address = to_address
        self.subject = subject
        self.body = body
        self.queued_at = queued_at


class OutboxService:
    """
    Mock outbox for 'sending' emails.
    
    IMPORTANT: Nothing actually leaves the system.
    This stores sent messages in a database table for review.
    
    In production, this would integrate with an email sending service
    (SendGrid, SES, SMTP, etc.) but the approval gate remains enforced.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        draft_service: DraftService,
        email_service: EmailService,
    ):
        self.session = session
        self.draft_service = draft_service
        self.email_service = email_service
    
    async def send_draft(self, draft_id: str) -> OutboxMessage:
        """
        'Send' an approved draft by adding it to the outbox.
        
        HARD GATE: Will raise ApprovalRequiredError if draft is not approved.
        """
        if not await self.draft_service.can_send(draft_id):
            # Route through mark_sent so SEND_BLOCKED is always audited
            await self.draft_service.mark_sent(draft_id)
            # mark_sent raises; this is unreachable but keeps type checkers happy
            raise ApprovalRequiredError(
                f"Draft {draft_id} is not approved for sending. "
                "Human approval is REQUIRED."
            )
        
        draft = await self.draft_service.get_draft(draft_id)
        if not draft:
            raise ValueError(f"Draft not found: {draft_id}")
        
        email = await self.email_service.get_email(draft.email_id)
        if not email:
            raise ValueError(f"Original email not found: {draft.email_id}")
        
        outbox_msg = OutboxMessage(
            id=str(uuid.uuid4()),
            draft_id=draft.id,
            to_address=email.from_address,
            subject=draft.subject,
            body=draft.body,
            queued_at=datetime.utcnow(),
        )
        
        db_outbox = OutboxTable(
            id=outbox_msg.id,
            draft_id=outbox_msg.draft_id,
            to_address=outbox_msg.to_address,
            subject=outbox_msg.subject,
            body=outbox_msg.body,
            queued_at=outbox_msg.queued_at,
        )
        self.session.add(db_outbox)
        
        await self.draft_service.mark_sent(draft_id)
        
        await self.session.commit()
        
        return outbox_msg
    
    async def get_outbox(self, limit: int = 50) -> list[OutboxMessage]:
        """Get messages from the outbox."""
        result = await self.session.execute(
            select(OutboxTable)
            .order_by(OutboxTable.queued_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        
        return [
            OutboxMessage(
                id=row.id,
                draft_id=row.draft_id,
                to_address=row.to_address,
                subject=row.subject,
                body=row.body,
                queued_at=row.queued_at,
            )
            for row in rows
        ]
