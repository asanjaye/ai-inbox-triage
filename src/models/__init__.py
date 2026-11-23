"""Data models for the inbox triage system."""
from .email import Email, EmailCategory, EmailPriority
from .classification import Classification
from .draft import Draft, DraftStatus
from .audit import AuditLog, AuditAction

__all__ = [
    "Email",
    "EmailCategory", 
    "EmailPriority",
    "Classification",
    "Draft",
    "DraftStatus",
    "AuditLog",
    "AuditAction",
]
