"""Generate draft replies based on classification."""
import json
import uuid
from datetime import datetime

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Email, Classification, Draft, EmailCategory
from ..config import get_settings
from .prompts import REPLY_GUIDELINES, DRAFT_GENERATION_PROMPT


class DraftGenerator:
    """Generates reply drafts based on email classification."""
    
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        settings = get_settings()
        self.settings = settings
        
        if not use_mock:
            if settings.llm_provider == "openai" and settings.openai_api_key:
                self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
                self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    async def generate_draft(
        self, email: Email, classification: Classification
    ) -> Draft:
        """Generate a reply draft for an email."""
        if self.use_mock or self.settings.mock_mode:
            body = self._generate_mock_reply(email, classification)
        else:
            body = await self._generate_llm_reply(email, classification)
        
        return Draft(
            id=str(uuid.uuid4()),
            email_id=email.id,
            subject=f"Re: {email.subject}",
            body=body,
        )
    
    def _generate_mock_reply(
        self, email: Email, classification: Classification
    ) -> str:
        """Generate a template-based mock reply."""
        guidelines = REPLY_GUIDELINES.get(
            classification.category.value,
            {"tone": "professional", "template": "Thank you for your email. {custom_response}"}
        )
        
        category_responses = {
            EmailCategory.SALES_LEAD: """Thank you for your interest in our services!

I'd be happy to discuss how we can help with your needs. Based on your inquiry, I think we could be a great fit.

Would you be available for a brief 15-minute call this week? I'm flexible with timing and can work around your schedule.

Looking forward to connecting!

Best regards""",
            
            EmailCategory.SUPPORT_REQUEST: """Thank you for reaching out about this issue.

I understand this is frustrating, and I want to help resolve it as quickly as possible. I've reviewed your message and here's what I recommend:

1. First, let's verify the current state of the issue
2. I'll investigate on our end
3. I'll follow up within 24 hours with next steps

If this is urgent, please let me know and I'll prioritize accordingly.

Best regards""",
            
            EmailCategory.INVOICE: """Thank you for sending this invoice.

I've received it and will process it according to our standard payment terms. If there are any questions about the charges, I'll reach out.

Best regards""",
            
            EmailCategory.SCHEDULING: """Thank you for reaching out about scheduling!

I'd be happy to find a time that works. Here are some slots I have available:
- [Time slot 1]
- [Time slot 2]
- [Time slot 3]

Please let me know which works best for you, or suggest an alternative if none of these fit your schedule.

Best regards""",
            
            EmailCategory.URGENT_ESCALATION: """Thank you for bringing this to my attention immediately.

I'm treating this as a top priority. Here's what I'm doing right now:

1. Investigating the issue
2. Assembling the right team members
3. Will provide an update within the hour

Please stand by - I'll keep you informed of any developments.

Best regards""",
        }
        
        return category_responses.get(
            classification.category,
            f"""Thank you for your email regarding "{email.subject}".

I've received your message and will review it shortly. If you need immediate assistance, please let me know.

Best regards"""
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _generate_llm_reply(
        self, email: Email, classification: Classification
    ) -> str:
        """Generate reply using LLM."""
        guidelines = REPLY_GUIDELINES.get(
            classification.category.value,
            {"tone": "professional", "template": "Standard professional response"}
        )
        
        prompt = DRAFT_GENERATION_PROMPT.format(
            from_name=email.from_name or "Unknown",
            from_address=email.from_address,
            subject=email.subject,
            body=email.body[:2000],
            category=classification.category.value,
            priority=classification.priority.value,
            summary=classification.summary,
            tone=guidelines["tone"],
            template=guidelines["template"],
        )
        
        if self.settings.llm_provider == "openai":
            response = await self.openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.choices[0].message.content
        else:
            response = await self.anthropic_client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
