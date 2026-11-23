"""Factory for creating LLM classifiers based on configuration."""
from ..config import get_settings
from .base import LLMClassifier
from .openai_classifier import OpenAIClassifier
from .anthropic_classifier import AnthropicClassifier
from .mock_classifier import MockClassifier


def get_classifier(force_mock: bool = False) -> LLMClassifier:
    """
    Create appropriate classifier based on configuration.
    
    Args:
        force_mock: If True, always return MockClassifier regardless of settings
        
    Returns:
        Configured LLMClassifier instance
    """
    settings = get_settings()
    
    if force_mock or settings.mock_mode:
        return MockClassifier()
    
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY required when LLM_PROVIDER=openai and MOCK_MODE=false")
        return OpenAIClassifier()
    
    elif settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY required when LLM_PROVIDER=anthropic and MOCK_MODE=false")
        return AnthropicClassifier()
    
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
