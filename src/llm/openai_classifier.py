"""OpenAI-based email classifier."""
import json
from typing import Any

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Email, Classification, EmailCategory, EmailPriority
from ..config import get_settings
from .base import LLMClassifier
from .prompts import CLASSIFICATION_SYSTEM_PROMPT, CLASSIFICATION_USER_PROMPT


class OpenAIClassifier(LLMClassifier):
    """Email classifier using OpenAI API."""
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def classify(self, email: Email) -> Classification:
        """Classify email using OpenAI with structured output."""
        user_prompt = CLASSIFICATION_USER_PROMPT.format(
            from_name=email.from_name or "Unknown",
            from_address=email.from_address,
            to_address=email.to_address,
            subject=email.subject,
            received_at=email.received_at.isoformat(),
            body=email.body[:4000],  # Truncate very long emails
        )
        
        response = await self.client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        
        result = json.loads(response.choices[0].message.content)
        
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
