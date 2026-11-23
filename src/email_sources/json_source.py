"""JSON file email source for synthetic/test data."""
import json
from pathlib import Path
from typing import AsyncIterator, Optional

from ..models import Email
from .base import EmailSource


class JsonEmailSource(EmailSource):
    """
    Email source that reads from a JSON file.
    
    Perfect for testing, demos, and development without real email access.
    """
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._emails: dict[str, Email] = {}
        self._processed: set[str] = set()
    
    async def connect(self) -> None:
        """Load emails from JSON file."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Email source file not found: {self.file_path}")
        
        with open(self.file_path, "r") as f:
            data = json.load(f)
        
        for email_data in data.get("emails", []):
            email = Email(**email_data)
            self._emails[email.id] = email
    
    async def disconnect(self) -> None:
        """Clear loaded emails."""
        self._emails.clear()
        self._processed.clear()
    
    async def fetch_emails(
        self,
        limit: Optional[int] = None,
        since_id: Optional[str] = None,
    ) -> AsyncIterator[Email]:
        """Yield emails from loaded data."""
        emails = list(self._emails.values())
        emails.sort(key=lambda e: e.received_at, reverse=True)
        
        start_yielding = since_id is None
        count = 0
        
        for email in emails:
            if not start_yielding:
                if email.id == since_id:
                    start_yielding = True
                continue
            
            if email.id not in self._processed:
                yield email
                count += 1
                
                if limit and count >= limit:
                    break
    
    async def get_email(self, email_id: str) -> Optional[Email]:
        """Get email by ID."""
        return self._emails.get(email_id)
    
    async def mark_processed(self, email_id: str) -> None:
        """Mark email as processed."""
        self._processed.add(email_id)
    
    @property
    def source_type(self) -> str:
        return "json"
