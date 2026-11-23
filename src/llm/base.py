"""Base class for LLM classifiers."""
from abc import ABC, abstractmethod

from ..models import Email, Classification


class LLMClassifier(ABC):
    """Abstract interface for email classifiers."""
    
    @abstractmethod
    async def classify(self, email: Email) -> Classification:
        """
        Classify an email and return structured results.
        
        Args:
            email: The email to classify
            
        Returns:
            Classification with category, priority, needs_reply, and summary
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""
        pass
    
    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """Return True if this is a mock/deterministic classifier."""
        pass
