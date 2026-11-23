"""Tests for the FastAPI endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from pathlib import Path
import shutil
import tempfile
import os

# Isolate env before importing app/settings
_TEST_DIR = tempfile.mkdtemp(prefix="inbox_triage_test_")
os.environ["MOCK_MODE"] = "true"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DIR}/test.db"
os.environ["EMAIL_SOURCE_PATH"] = str(
    Path(__file__).resolve().parent.parent / "data" / "synthetic_emails.json"
)

from src.config import get_settings
get_settings.cache_clear()

from src import database as db_module
from src.api.app import create_app


@pytest.fixture
async def client(tmp_path):
    """Create test client with a fresh writable database."""
    db_path = tmp_path / "api_test.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    os.environ["MOCK_MODE"] = "true"
    get_settings.cache_clear()

    # Reset module-level engine so init_db uses the new URL
    db_module._engine = None
    db_module._session_maker = None

    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    if db_module._engine is not None:
        await db_module._engine.dispose()
    db_module._engine = None
    db_module._session_maker = None
    get_settings.cache_clear()


class TestHealthEndpoint:
    async def test_health_check(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestEmailEndpoints:
    async def test_list_emails_empty(self, client):
        response = await client.get("/api/emails/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_import_emails(self, client):
        response = await client.post("/api/emails/import?limit=5")
        assert response.status_code == 200
        emails = response.json()
        assert isinstance(emails, list)
        assert len(emails) <= 5
        assert len(emails) > 0

    async def test_get_email_not_found(self, client):
        response = await client.get("/api/emails/nonexistent-id")
        assert response.status_code == 404


class TestDraftEndpoints:
    async def test_list_drafts_empty(self, client):
        response = await client.get("/api/drafts/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_pending_queue_empty(self, client):
        response = await client.get("/api/drafts/pending")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_send_unapproved_draft_blocked(self, client):
        """Unapproved drafts must be blocked via API (403)."""
        await client.post("/api/emails/import?limit=10")
        emails = (await client.get("/api/emails/")).json()
        assert emails, "Expected imported emails"

        # Prefer an email that needs a reply (sales/support/etc.)
        email_id = emails[0]["id"]
        for email in emails:
            # Generate drafts until one succeeds that needs reply
            draft_response = await client.post(f"/api/drafts/generate/{email['id']}")
            if draft_response.status_code == 200:
                draft = draft_response.json()
                # Only proceed if draft was created for a needs-reply email
                # (generator always creates when called)
                email_id = email["id"]
                break
        else:
            pytest.skip("Could not generate any draft")

        draft_response = await client.post(f"/api/drafts/generate/{email_id}")
        assert draft_response.status_code == 200
        draft = draft_response.json()
        assert draft["status"] == "pending"

        send_response = await client.post(f"/api/drafts/{draft['id']}/send")
        assert send_response.status_code == 403
        assert "approval" in send_response.json()["detail"].lower()

    async def test_approve_then_send(self, client):
        """Approved drafts can be sent to the mock outbox."""
        await client.post("/api/emails/import?limit=10")
        emails = (await client.get("/api/emails/")).json()
        assert emails

        email_id = emails[0]["id"]
        draft_response = await client.post(f"/api/drafts/generate/{email_id}")
        assert draft_response.status_code == 200
        draft = draft_response.json()

        approve_response = await client.post(
            f"/api/drafts/{draft['id']}/approve",
            json={"approved_by": "test-approver@company.com"},
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "approved"

        send_response = await client.post(f"/api/drafts/{draft['id']}/send")
        assert send_response.status_code == 200
        result = send_response.json()
        assert result["status"] == "queued"


class TestTriageEndpoints:
    async def test_process_all(self, client):
        response = await client.post(
            "/api/triage/process-all",
            params={"import_new": True, "generate_drafts": True, "limit": 10},
        )
        assert response.status_code == 200
        summary = response.json()
        assert summary["total_emails"] >= 1
        assert "by_category" in summary
        assert "by_priority" in summary
        assert "needs_reply" in summary


class TestAuditEndpoints:
    async def test_list_audit_logs(self, client):
        response = await client.get("/api/audit/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
