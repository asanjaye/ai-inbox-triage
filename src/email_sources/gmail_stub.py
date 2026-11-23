"""Gmail API adapter stub - demonstrates interface for future implementation."""
from typing import AsyncIterator, Optional

from ..models import Email
from .base import EmailSource


class GmailEmailSource(EmailSource):
    """
    Gmail API email source (STUB).
    
    This is a stub implementation demonstrating the interface.
    To implement fully, you would need:
    1. Google Cloud project with Gmail API enabled
    2. OAuth2 credentials (credentials.json)
    3. google-auth and google-api-python-client packages
    
    Example implementation pattern:
    ```python
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    ```
    """
    
    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._service = None
    
    async def connect(self) -> None:
        """
        Connect to Gmail API.
        
        Would implement OAuth2 flow here:
        1. Load existing token or initiate OAuth flow
        2. Build Gmail API service
        """
        raise NotImplementedError(
            "Gmail adapter is a stub. To implement:\n"
            "1. pip install google-auth google-auth-oauthlib google-api-python-client\n"
            "2. Set up Google Cloud project with Gmail API\n"
            "3. Download credentials.json\n"
            "4. Implement OAuth2 flow in this method"
        )
    
    async def disconnect(self) -> None:
        """Disconnect from Gmail API."""
        self._service = None
    
    async def fetch_emails(
        self,
        limit: Optional[int] = None,
        since_id: Optional[str] = None,
    ) -> AsyncIterator[Email]:
        """
        Fetch emails from Gmail.
        
        Would use:
        ```python
        results = service.users().messages().list(
            userId='me',
            maxResults=limit or 50,
            q='is:unread'  # or other query
        ).execute()
        ```
        """
        raise NotImplementedError("Gmail adapter is a stub")
        yield  # Make this a generator
    
    async def get_email(self, email_id: str) -> Optional[Email]:
        """
        Get single email from Gmail.
        
        Would use:
        ```python
        message = service.users().messages().get(
            userId='me',
            id=email_id,
            format='full'
        ).execute()
        ```
        """
        raise NotImplementedError("Gmail adapter is a stub")
    
    async def mark_processed(self, email_id: str) -> None:
        """
        Mark email as read in Gmail.
        
        Would use:
        ```python
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        ```
        """
        raise NotImplementedError("Gmail adapter is a stub")
    
    @property
    def source_type(self) -> str:
        return "gmail"
