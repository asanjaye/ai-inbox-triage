"""Email source adapters - pluggable interface for reading emails."""
from .base import EmailSource
from .json_source import JsonEmailSource
from .gmail_stub import GmailEmailSource
from .imap_stub import ImapEmailSource

__all__ = ["EmailSource", "JsonEmailSource", "GmailEmailSource", "ImapEmailSource"]
