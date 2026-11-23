"""Database setup and ORM models."""
import json
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, String, Text, Boolean, Float, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings
from .models import EmailCategory, EmailPriority, DraftStatus, AuditAction


class Base(DeclarativeBase):
    pass


class EmailTable(Base):
    __tablename__ = "emails"
    
    id = Column(String, primary_key=True)
    from_address = Column(String, nullable=False)
    from_name = Column(String, nullable=True)
    to_address = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)
    has_attachments = Column(Boolean, default=False)
    thread_id = Column(String, nullable=True)
    label_category = Column(String, nullable=True)
    label_priority = Column(String, nullable=True)
    label_needs_reply = Column(Boolean, nullable=True)


class ClassificationTable(Base):
    __tablename__ = "classifications"
    
    email_id = Column(String, primary_key=True)
    category = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    needs_reply = Column(Boolean, nullable=False)
    summary = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    reasoning = Column(Text, nullable=True)
    classified_at = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String, default="")
    is_mock = Column(Boolean, default=False)


class DraftTable(Base):
    __tablename__ = "drafts"
    
    id = Column(String, primary_key=True)
    email_id = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String, default=DraftStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)
    edit_history = Column(JSON, default=list)


class AuditLogTable(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    actor = Column(String, default="system")
    details = Column(JSON, nullable=True)


class OutboxTable(Base):
    """Mock outbox for 'sent' emails - nothing actually leaves the system."""
    __tablename__ = "outbox"
    
    id = Column(String, primary_key=True)
    draft_id = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    queued_at = Column(DateTime, default=datetime.utcnow)


_engine = None
_session_maker = None


async def init_db() -> None:
    """Initialize the database and create tables."""
    global _engine, _session_maker
    settings = get_settings()
    
    _engine = create_async_engine(
        settings.database_url,
        echo=False,
    )
    _session_maker = async_sessionmaker(_engine, expire_on_commit=False)
    
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    if _session_maker is None:
        await init_db()
    async with _session_maker() as session:
        yield session


def get_engine():
    return _engine
