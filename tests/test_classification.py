"""Tests for email classification."""
import pytest
from datetime import datetime

from src.models import Email, EmailCategory, EmailPriority
from src.llm import MockClassifier


@pytest.fixture
def classifier():
    return MockClassifier()


class TestMockClassifier:
    """Test the mock classifier rules."""
    
    async def test_classify_spam(self, classifier):
        """Test spam detection."""
        email = Email(
            id="spam-1",
            from_address="prince@nigeria.ng",
            to_address="victim@company.com",
            subject="URGENT: Million dollars waiting",
            body="Congratulations! You have won a million dollars. Click here to claim your prize.",
            received_at=datetime.utcnow(),
        )
        
        result = await classifier.classify(email)
        
        assert result.category == EmailCategory.SPAM
        assert result.priority == EmailPriority.LOW
        assert result.needs_reply is False
        assert result.is_mock is True
    
    async def test_classify_urgent_support(self, classifier):
        """Test urgent escalation detection."""
        email = Email(
            id="urgent-1",
            from_address="customer@company.com",
            to_address="support@company.com",
            subject="URGENT: System is down!",
            body="Emergency! Our entire system has been down for 2 hours. We need immediate help!",
            received_at=datetime.utcnow(),
        )
        
        result = await classifier.classify(email)
        
        assert result.category == EmailCategory.URGENT_ESCALATION
        assert result.priority in [EmailPriority.CRITICAL, EmailPriority.HIGH]
        assert result.needs_reply is True
    
    async def test_classify_sales_lead(self, classifier):
        """Test sales lead detection."""
        email = Email(
            id="sales-1",
            from_address="prospect@business.com",
            to_address="sales@company.com",
            subject="Interested in your services",
            body="Hi, I'm interested in your pricing for the enterprise plan. Can you send a quote?",
            received_at=datetime.utcnow(),
        )
        
        result = await classifier.classify(email)
        
        assert result.category == EmailCategory.SALES_LEAD
        assert result.needs_reply is True
    
    async def test_classify_support_request(self, classifier):
        """Test support request detection."""
        email = Email(
            id="support-1",
            from_address="user@example.com",
            to_address="support@company.com",
            subject="Help needed with login",
            body="I'm having an issue logging in. I keep getting an error message. Can you help?",
            received_at=datetime.utcnow(),
        )
        
        result = await classifier.classify(email)
        
        assert result.category == EmailCategory.SUPPORT_REQUEST
        assert result.needs_reply is True
    
    async def test_classify_invoice(self, classifier):
        """Test invoice detection."""
        email = Email(
            id="invoice-1",
            from_address="billing@vendor.com",
            to_address="ap@company.com",
            subject="Invoice #12345 - Payment Due",
            body="Please find attached invoice #12345. Amount due: $500. Payment terms: Net 30.",
            received_at=datetime.utcnow(),
        )
        
        result = await classifier.classify(email)
        
        assert result.category == EmailCategory.INVOICE
    
    async def test_classify_scheduling(self, classifier):
        """Test scheduling request detection."""
        email = Email(
            id="scheduling-1",
            from_address="colleague@company.com",
            to_address="inbox@company.com",
            subject="Meeting request",
            body="Can we schedule a call for tomorrow to discuss the project? Let me know your availability.",
            received_at=datetime.utcnow(),
        )
        
        result = await classifier.classify(email)
        
        assert result.category == EmailCategory.SCHEDULING
        assert result.needs_reply is True
    
    async def test_classify_newsletter(self, classifier):
        """Test newsletter detection."""
        email = Email(
            id="newsletter-1",
            from_address="noreply@newsletter.com",
            to_address="inbox@company.com",
            subject="Weekly Digest",
            body="Here's your weekly update. Click here to unsubscribe from this newsletter.",
            received_at=datetime.utcnow(),
        )
        
        result = await classifier.classify(email)
        
        assert result.category == EmailCategory.NEWSLETTER
        assert result.priority == EmailPriority.LOW
        assert result.needs_reply is False
    
    async def test_classification_includes_summary(self, classifier):
        """Test that classification includes a summary."""
        email = Email(
            id="any-1",
            from_address="sender@example.com",
            to_address="recipient@company.com",
            subject="Test Subject",
            body="Test body content.",
            received_at=datetime.utcnow(),
        )
        
        result = await classifier.classify(email)
        
        assert result.summary is not None
        assert len(result.summary) > 0
        assert result.email_id == email.id
    
    async def test_mock_mode_flag(self, classifier):
        """Test that mock classifier sets is_mock flag."""
        email = Email(
            id="mock-test-1",
            from_address="sender@example.com",
            to_address="recipient@company.com",
            subject="Test",
            body="Test",
            received_at=datetime.utcnow(),
        )
        
        result = await classifier.classify(email)
        
        assert result.is_mock is True
        assert classifier.is_mock is True
        assert "mock" in classifier.model_name.lower()
