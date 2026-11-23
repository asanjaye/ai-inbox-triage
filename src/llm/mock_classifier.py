"""Deterministic rule-based classifier for testing and offline mode."""
import re
from typing import Tuple

from ..models import Email, Classification, EmailCategory, EmailPriority
from .base import LLMClassifier


class MockClassifier(LLMClassifier):
    """
    Rule-based classifier for deterministic testing.

    Uses keyword matching and heuristics to classify emails.
    Provides predictable results without API calls.
    """

    SPAM_PATTERNS = [
        r"congratulations.*won",
        r"claim your prize",
        r"nigerian prince",
        r"prince\s+abubakar",
        r"million dollars",
        r"\$15\s*million",
        r"act now",
        r"limited time offer",
        r"click here immediately",
        r"viagra|cialis",
        r"make money fast",
        r"gift card.*claim",
        r"no prescription",
        r"90%\s*off",
    ]

    URGENT_KEYWORDS = [
        "urgent", "emergency", "critical", "asap", "immediately",
        "outage", "down", "broken", "security breach", "escalation",
        "cease and desist", "security incident", "cpu at", "stockout",
    ]

    SALES_KEYWORDS = [
        "interested in", "pricing", "quote", "proposal", "demo",
        "services", "partnership", "business opportunity", "rfp",
        "enterprise", "commission", "pipeline", "serious inquiry",
    ]

    SUPPORT_KEYWORDS = [
        "help", "issue", "problem", "bug", "error", "not working",
        "support", "assistance", "broken", "fix", "password",
        "ticket", "export failed", "documentation", "api",
        "duplicate charge", "refund", "suggestion",
    ]

    INVOICE_KEYWORDS = [
        "invoice", "payment due", "bill", "receipt", "amount due",
        "overdue", "remittance", "past due", "accounts receivable",
    ]

    SCHEDULING_KEYWORDS = [
        "meeting", "schedule", "calendar", "availability",
        "appointment", "book a", "time slot", "speaker confirmation",
        "coffee chat", "call this week", "call next",
    ]

    NEWSLETTER_INDICATORS = [
        "unsubscribe", "newsletter", "weekly update", "digest",
        "subscription", "mailing list", "you are receiving this",
        "manage notification", "wellness challenge",
    ]

    PERSONAL_PATTERNS = [
        r"\bsunday dinner\b",
        r"\blove you\b",
        r"\bmom\b",
        r"\bdad says\b",
        r"\byour sister\b",
    ]

    async def classify(self, email: Email) -> Classification:
        """Classify email using rule-based heuristics."""
        text = f"{email.subject} {email.body}".lower()
        from_addr = email.from_address.lower()

        category, priority = self._determine_category_and_priority(text, from_addr, email.subject.lower())
        needs_reply = self._determine_needs_reply(category, text)
        summary = self._generate_summary(email, category)

        return Classification(
            email_id=email.id,
            category=category,
            priority=priority,
            needs_reply=needs_reply,
            summary=summary,
            reasoning="Rule-based classification (mock mode)",
            model_used="mock-classifier-v1",
            is_mock=True,
        )

    def _determine_category_and_priority(
        self, text: str, from_addr: str, subject: str
    ) -> Tuple[EmailCategory, EmailPriority]:
        """Determine category and priority from text analysis."""
        # Spam first — even if subject says URGENT
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return EmailCategory.SPAM, EmailPriority.LOW

        # Personal (word-boundary patterns to avoid matching "mom" inside "common")
        if any(re.search(p, text) for p in self.PERSONAL_PATTERNS):
            return EmailCategory.PERSONAL, EmailPriority.LOW

        # Newsletter / notifications (before support — "help" in marketing)
        if any(ind in text for ind in self.NEWSLETTER_INDICATORS):
            return EmailCategory.NEWSLETTER, EmailPriority.LOW
        if "noreply" in from_addr or "no-reply" in from_addr or "donotreply" in from_addr:
            # Automated shipping / github style
            if "shipped" in text or "tracking" in text or "pull request" in text:
                return EmailCategory.OTHER, EmailPriority.LOW
            return EmailCategory.NEWSLETTER, EmailPriority.LOW

        # Invoice before urgent (overdue invoices)
        invoice_hits = sum(1 for kw in self.INVOICE_KEYWORDS if kw in text)
        if invoice_hits >= 1 and ("invoice" in text or "past due" in text or "amount due" in text):
            if "overdue" in text or "past due" in text:
                return EmailCategory.INVOICE, EmailPriority.HIGH
            return EmailCategory.INVOICE, EmailPriority.MEDIUM

        # Urgent escalations
        urgent_hits = sum(1 for kw in self.URGENT_KEYWORDS if kw in text)
        if urgent_hits >= 1 and (
            "urgent" in subject
            or "critical" in subject
            or "security" in text
            or "outage" in text
            or "escalat" in text
            or "cease and desist" in text
            or "alert" in subject
            or "low inventory" in text
            or "audit notification" in text
            or "third time" in text
        ):
            if any(kw in text for kw in ("down", "outage", "security", "breach", "cpu", "cease")):
                return EmailCategory.URGENT_ESCALATION, EmailPriority.CRITICAL
            return EmailCategory.URGENT_ESCALATION, EmailPriority.HIGH

        # Sales
        sales_hits = sum(1 for kw in self.SALES_KEYWORDS if kw in text)
        if sales_hits >= 1 and (
            "pricing" in text
            or "interested" in text
            or "demo" in text
            or "rfp" in text
            or "enterprise" in text
            or "commission" in text
            or "inquiry" in subject
            or "opportunity" in text
        ):
            if "enterprise" in text or "500+" in text or "rfp" in text:
                return EmailCategory.SALES_LEAD, EmailPriority.HIGH
            return EmailCategory.SALES_LEAD, EmailPriority.MEDIUM

        # Scheduling
        if any(kw in text for kw in self.SCHEDULING_KEYWORDS):
            if "tomorrow" in text or "today" in text or "eod" in text:
                return EmailCategory.SCHEDULING, EmailPriority.HIGH
            return EmailCategory.SCHEDULING, EmailPriority.MEDIUM

        # Support
        if any(kw in text for kw in self.SUPPORT_KEYWORDS):
            if "refund" in text or "duplicate charge" in text:
                return EmailCategory.SUPPORT_REQUEST, EmailPriority.HIGH
            if "suggestion" in subject or "small suggestion" in text:
                return EmailCategory.SUPPORT_REQUEST, EmailPriority.LOW
            return EmailCategory.SUPPORT_REQUEST, EmailPriority.MEDIUM

        # Internal / other automation
        if "reminder" in subject or "performance review" in text or "security training" in text:
            return EmailCategory.OTHER, EmailPriority.MEDIUM
        if "campaign performance" in text or "recruiter" in from_addr or "opportunity at" in text:
            return EmailCategory.OTHER, EmailPriority.LOW

        return EmailCategory.OTHER, EmailPriority.MEDIUM

    def _determine_needs_reply(self, category: EmailCategory, text: str) -> bool:
        """Determine if email needs a reply based on category and content."""
        no_reply_categories = {
            EmailCategory.SPAM,
            EmailCategory.NEWSLETTER,
        }

        if category in no_reply_categories:
            return False

        # Automated alerts that don't need reply
        if "automated alert" in text or "do not reply" in text or "please do not reply" in text:
            return False
        if "reminder:" in text and "meeting" in text and "attendees" in text:
            return False

        question_indicators = ["?", "please respond", "let me know", "get back to", "please confirm", "please reply"]
        if any(ind in text for ind in question_indicators):
            return True

        reply_categories = {
            EmailCategory.SALES_LEAD,
            EmailCategory.SUPPORT_REQUEST,
            EmailCategory.SCHEDULING,
            EmailCategory.URGENT_ESCALATION,
            EmailCategory.PERSONAL,
        }

        if category == EmailCategory.INVOICE and ("past due" in text or "overdue" in text):
            return True

        if category == EmailCategory.OTHER:
            return False

        return category in reply_categories

    def _generate_summary(self, email: Email, category: EmailCategory) -> str:
        """Generate a brief summary of the email."""
        subject = email.subject[:50]

        summaries = {
            EmailCategory.SPAM: f"Spam/promotional email: {subject}",
            EmailCategory.NEWSLETTER: f"Newsletter/subscription: {subject}",
            EmailCategory.SALES_LEAD: f"Sales inquiry: {subject}",
            EmailCategory.SUPPORT_REQUEST: f"Support request: {subject}",
            EmailCategory.INVOICE: f"Invoice/payment: {subject}",
            EmailCategory.SCHEDULING: f"Scheduling request: {subject}",
            EmailCategory.URGENT_ESCALATION: f"Urgent matter: {subject}",
            EmailCategory.PERSONAL: f"Personal message: {subject}",
            EmailCategory.OTHER: f"General email: {subject}",
        }

        return summaries.get(category, f"Email: {subject}")

    @property
    def model_name(self) -> str:
        return "mock-classifier-v1"

    @property
    def is_mock(self) -> bool:
        return True
