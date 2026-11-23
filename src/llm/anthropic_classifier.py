"""Anthropic Claude-based email classifier."""
import json
import re

from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Email, Classification, EmailCategory, EmailPriority
from ..config import get_settings
from .base import LLMClassifier
from .prompts import CLASSIFICATION_SYSTEM_PROMPT, CLASSIFICATION_USER_PROMPT


class AnthropicClassifier(LLMClassifier):
    """Email classifier using Anthropic Claude API."""
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def classify(self, email: Email) -> Classification:
        """Classify email using Claude with structured output."""
        user_prompt = CLASSIFICATION_USER_PROMPT.format(
            from_name=email.from_name or "Unknown",
            from_address=email.from_address,
            to_address=email.to_address,
            subject=email.subject,
            received_at=email.received_at.isoformat(),
            body=email.body[:4000],
        )
        
        response = await self.client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=CLASSIFICATION_SYSTEM_PROMPT + "\n\nAlways respond with valid JSON.",
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )
        
        content = response.content[0].text
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(content)
        
        return Classification(
            email_id=email.id,
            category=EmailCategory(result["category"]),
            priority=EmailPriority(result["priority"]),
            needs_reply=result["needs_reply"],
            summary=result["summary"],
            reasoning=result.get("reasoning"),
            model_used=self._model,
            is_mock=False,
        )
    
    @property
    def model_name(self) -> str:
        return self._model
    
    @property
    def is_mock(self) -> bool:
        return False
