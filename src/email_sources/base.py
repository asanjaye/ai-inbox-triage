"""Abstract base class for email sources."""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

from ..models import Email


class EmailSource(ABC):
    """
    Abstract interface for email sources.
    
    Implement this interface to add new email providers (Gmail, IMAP, etc.).
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the email source."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the email source."""
        pass
    
    @abstractmethod
    async def fetch_emails(
        self,
        limit: Optional[int] = None,
        since_id: Optional[str] = None,
    ) -> AsyncIterator[Email]:
        """
        Fetch emails from the source.
        
        Args:
            limit: Maximum number of emails to fetch
            since_id: Only fetch emails after this ID (for incremental sync)
            
        Yields:
            Email objects
        """
        pass
    
    @abstractmethod
    async def get_email(self, email_id: str) -> Optional[Email]:
        """Fetch a single email by ID."""
        pass
    
    @abstractmethod
    async def mark_processed(self, email_id: str) -> None:
        """Mark an email as processed (if supported by source)."""
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return identifier for this source type."""
        pass
