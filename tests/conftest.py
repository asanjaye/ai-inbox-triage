"""Pytest configuration and shared fixtures."""
import os
import pytest

os.environ["MOCK_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

pytest_plugins = ["pytest_asyncio"]
