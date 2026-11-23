"""IMAP email source stub - demonstrates interface for future implementation."""
from typing import AsyncIterator, Optional

from ..models import Email
from .base import EmailSource


class ImapEmailSource(EmailSource):
    """
    IMAP email source (STUB).
    
    This is a stub implementation demonstrating the interface.
    To implement fully, you would need:
    1. IMAP server credentials
    2. aioimaplib package for async IMAP
    
    Example implementation pattern:
    ```python
    from aioimaplib import IMAP4_SSL
    
    imap = IMAP4_SSL(host, port)
    await imap.wait_hello_from_server()
    await imap.login(username, password)
    await imap.select('INBOX')
    ```
    """
    
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._client = None
    
    async def connect(self) -> None:
        """
        Connect to IMAP server.
        
        Would implement:
        1. Create IMAP4_SSL connection
        2. Login with credentials
        3. Select inbox
        """
        raise NotImplementedError(
            "IMAP adapter is a stub. To implement:\n"
            "1. pip install aioimaplib\n"
            "2. Configure IMAP server credentials\n"
            "3. Implement connection logic in this method"
        )
    
    async def disconnect(self) -> None:
        """Disconnect from IMAP server."""
        if self._client:
            # await self._client.logout()
            self._client = None
    
    async def fetch_emails(
        self,
        limit: Optional[int] = None,
        since_id: Optional[str] = None,
    ) -> AsyncIterator[Email]:
        """
        Fetch emails via IMAP.
        
        Would use SEARCH and FETCH commands:
        ```python
        _, data = await imap.search('UNSEEN')
        for msg_id in data[0].split():
            _, msg_data = await imap.fetch(msg_id, '(RFC822)')
            # Parse email from msg_data
        ```
        """
        raise NotImplementedError("IMAP adapter is a stub")
        yield  # Make this a generator
    
    async def get_email(self, email_id: str) -> Optional[Email]:
        """Fetch single email by message ID."""
        raise NotImplementedError("IMAP adapter is a stub")
    
    async def mark_processed(self, email_id: str) -> None:
        """
        Mark email as read via IMAP.
        
        Would use:
        ```python
        await imap.store(email_id, '+FLAGS', '\\Seen')
        ```
        """
        raise NotImplementedError("IMAP adapter is a stub")
    
    @property
    def source_type(self) -> str:
        return "imap"
