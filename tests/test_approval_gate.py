"""
Tests for the HARD approval gate enforcement.

These tests verify that:
1. Unapproved drafts CANNOT be sent
2. Only explicitly approved drafts can be sent
3. The audit log captures blocked send attempts
"""
import pytest
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from src.database import Base, DraftTable, AuditLogTable
from src.models import (
    Email, Classification, Draft, DraftStatus,
    EmailCategory, EmailPriority, AuditAction,
)
from src.services import DraftService, AuditService, EmailService, OutboxService
from src.services.draft_service import ApprovalRequiredError
from src.llm.draft_generator import DraftGenerator


@pytest.fixture
async def db_session():
    """Create in-memory database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_maker() as session:
        yield session


@pytest.fixture
def sample_email():
    """Create a sample email for testing."""
    return Email(
        id="test-email-001",
        from_address="sender@example.com",
        from_name="Test Sender",
        to_address="recipient@company.com",
        subject="Test Email",
        body="This is a test email body.",
        received_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_classification(sample_email):
    """Create a sample classification."""
    return Classification(
        email_id=sample_email.id,
        category=EmailCategory.SUPPORT_REQUEST,
        priority=EmailPriority.MEDIUM,
        needs_reply=True,
        summary="Test support request",
        model_used="test",
        is_mock=True,
    )


@pytest.fixture
async def services(db_session, sample_email):
    """Set up all required services."""
    audit = AuditService(db_session)
    email_service = EmailService(db_session, audit)
    draft_generator = DraftGenerator(use_mock=True)
    draft_service = DraftService(db_session, audit, draft_generator)
    outbox_service = OutboxService(db_session, draft_service, email_service)
    
    from src.database import EmailTable
    db_email = EmailTable(
        id=sample_email.id,
        from_address=sample_email.from_address,
        from_name=sample_email.from_name,
        to_address=sample_email.to_address,
        subject=sample_email.subject,
        body=sample_email.body,
        received_at=sample_email.received_at,
    )
    db_session.add(db_email)
    await db_session.commit()
    
    return {
        "audit": audit,
        "email": email_service,
        "draft": draft_service,
        "outbox": outbox_service,
    }


class TestApprovalGateEnforcement:
    """Test suite for approval gate enforcement."""
    
    async def test_new_draft_is_pending(
        self, services, sample_email, sample_classification
    ):
        """New drafts should start in pending status."""
        draft = await services["draft"].create_draft(
            sample_email, sample_classification
        )
        
        assert draft.status == DraftStatus.PENDING
        assert draft.approved_at is None
        assert draft.approved_by is None
    
    async def test_pending_draft_cannot_be_sent(
        self, services, sample_email, sample_classification
    ):
        """CRITICAL: Pending drafts must not be sendable."""
        draft = await services["draft"].create_draft(
            sample_email, sample_classification
        )
        
        can_send = await services["draft"].can_send(draft.id)
        assert can_send is False, "Pending draft should NOT be sendable"
        
        with pytest.raises(ApprovalRequiredError) as exc_info:
            await services["outbox"].send_draft(draft.id)
        
        msg = str(exc_info.value).lower()
        assert "approval" in msg or "approved" in msg
    
    async def test_rejected_draft_cannot_be_sent(
        self, services, sample_email, sample_classification
    ):
        """Rejected drafts must not be sendable."""
        draft = await services["draft"].create_draft(
            sample_email, sample_classification
        )
        
        await services["draft"].reject_draft(draft.id, "reviewer", "Not appropriate")
        
        can_send = await services["draft"].can_send(draft.id)
        assert can_send is False
        
        with pytest.raises(ApprovalRequiredError):
            await services["outbox"].send_draft(draft.id)
    
    async def test_only_approved_draft_can_be_sent(
        self, services, sample_email, sample_classification
    ):
        """Only explicitly approved drafts can be sent."""
        draft = await services["draft"].create_draft(
            sample_email, sample_classification
        )
        
        can_send_before = await services["draft"].can_send(draft.id)
        assert can_send_before is False
        
        approved_draft = await services["draft"].approve_draft(draft.id, "approver@company.com")
        
        assert approved_draft.status == DraftStatus.APPROVED
        assert approved_draft.approved_by == "approver@company.com"
        assert approved_draft.approved_at is not None
        
        can_send_after = await services["draft"].can_send(draft.id)
        assert can_send_after is True
        
        outbox_msg = await services["outbox"].send_draft(draft.id)
        assert outbox_msg is not None
        assert outbox_msg.draft_id == draft.id
    
    async def test_edit_revokes_approval(
        self, services, sample_email, sample_classification
    ):
        """Editing an approved draft should revoke approval."""
        draft = await services["draft"].create_draft(
            sample_email, sample_classification
        )
        
        await services["draft"].approve_draft(draft.id, "approver")
        
        can_send_approved = await services["draft"].can_send(draft.id)
        assert can_send_approved is True
        
        edited_draft = await services["draft"].update_draft(
            draft.id, "New edited content", editor="someone"
        )
        
        assert edited_draft.status == DraftStatus.PENDING
        assert edited_draft.approved_at is None
        
        can_send_edited = await services["draft"].can_send(draft.id)
        assert can_send_edited is False
        
        with pytest.raises(ApprovalRequiredError):
            await services["outbox"].send_draft(draft.id)
    
    async def test_blocked_send_creates_audit_log(
        self, db_session, services, sample_email, sample_classification
    ):
        """Blocked send attempts must be logged in audit trail."""
        draft = await services["draft"].create_draft(
            sample_email, sample_classification
        )
        
        try:
            await services["outbox"].send_draft(draft.id)
        except ApprovalRequiredError:
            pass
        
        result = await db_session.execute(
            select(AuditLogTable).where(
                AuditLogTable.action == AuditAction.SEND_BLOCKED.value
            )
        )
        blocked_logs = result.scalars().all()
        
        assert len(blocked_logs) >= 1, "Blocked send should be logged"
        assert blocked_logs[0].entity_id == draft.id
        assert "HARD_GATE" in str(blocked_logs[0].details)
    
    async def test_mark_sent_enforces_approval(
        self, services, sample_email, sample_classification
    ):
        """Direct mark_sent call must also enforce approval gate."""
        draft = await services["draft"].create_draft(
            sample_email, sample_classification
        )
        
        with pytest.raises(ApprovalRequiredError) as exc_info:
            await services["draft"].mark_sent(draft.id)
        
        assert "Human approval is REQUIRED" in str(exc_info.value)
    
    async def test_cannot_send_already_sent_draft(
        self, services, sample_email, sample_classification
    ):
        """Cannot send a draft that's already been sent."""
        draft = await services["draft"].create_draft(
            sample_email, sample_classification
        )
        
        await services["draft"].approve_draft(draft.id, "approver")
        await services["outbox"].send_draft(draft.id)
        
        with pytest.raises(ApprovalRequiredError):
            await services["outbox"].send_draft(draft.id)
