"""Application configuration loaded from environment variables."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-haiku-20240307"
    mock_mode: bool = True
    database_url: str = "sqlite+aiosqlite:///./data/inbox_triage.db"
    host: str = "0.0.0.0"
    port: int = 8000
    email_source: Literal["json", "gmail", "imap"] = "json"
    email_source_path: str = "./data/synthetic_emails.json"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
