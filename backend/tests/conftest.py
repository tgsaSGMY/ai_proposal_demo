"""Shared fixtures for the demo backend test suite.

The real `SupabaseService.__init__` reaches out to Supabase + downloads the
fastembed model; both are unsuitable for unit tests. We instead build a
minimal mock that satisfies the demo router's surface area, inject it via
FastAPI's `dependency_overrides`, and skip the startup/shutdown event
handlers by constructing `TestClient` without the context-manager form
(Starlette only fires lifespan events inside `with TestClient(...) as c:`).
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

# Make `app.*` importable without installing the backend as a package.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Stub the heavyweight env vars before anything in `app` imports config.
os.environ.setdefault("SUPABASE_URL", "http://stub.local")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "stub-key")
os.environ.setdefault("DATABASE_URL", "postgresql://stub/stub")
os.environ.setdefault("SUPABASE_BUCKET_NAME", "stub-bucket")


class FakeDemoStore:
    """In-memory stand-in for the `ai_proposal_platform.demo` table.

    Keeps the supabase mock honest: a get-after-put returns the put payload,
    delete actually removes the row, and ensure is idempotent. Enough to
    exercise `projects.py` end-to-end without a real database.
    """

    def __init__(self) -> None:
        self.rows: Dict[str, Dict[str, Any]] = {}

    async def ensure(self, session_id: str, **kwargs: Any) -> Dict[str, Any]:
        row = self.rows.setdefault(
            session_id,
            {
                "session_id": session_id,
                "grant_id": None,
                "template_id": None,
                "conversation_history": [],
                "stored_answer": {},
                "saved_plan": None,
                "interaction_count": 0,
                "has_generated_docx": False,
                "status": "active",
            },
        )
        for k, v in kwargs.items():
            if v is not None and row.get(k) is None:
                row[k] = v
        return row

    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.rows.get(session_id)

    async def update(self, session_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if session_id not in self.rows:
            return None
        for k, v in data.items():
            if v is not None:
                self.rows[session_id][k] = v
        return self.rows[session_id]

    async def delete(self, session_id: str) -> bool:
        self.rows.pop(session_id, None)
        return True


@pytest.fixture
def demo_store() -> FakeDemoStore:
    return FakeDemoStore()


@pytest.fixture
def rate_limit_rows():
    """Mutable list returned by the mocked rate-limit upsert. Tests overwrite
    it to simulate "under limit" / "over hourly" / "over daily" states."""
    return [("hour", 1), ("day", 1)]


@pytest.fixture
def mock_supabase(demo_store: FakeDemoStore, rate_limit_rows):
    svc = MagicMock(name="SupabaseService")

    svc.ensure_demo_session = AsyncMock(side_effect=demo_store.ensure)
    svc.get_demo_session = AsyncMock(side_effect=demo_store.get)
    svc.update_demo_session = AsyncMock(side_effect=demo_store.update)
    svc.delete_demo_session = AsyncMock(side_effect=demo_store.delete)

    # The rate limiter calls `with supabase.get_db_session() as session`,
    # then `session.execute(...).fetchall()` to read the upserted counts.
    fake_result = MagicMock()
    fake_result.fetchall = lambda: list(rate_limit_rows)
    fake_session = MagicMock()
    fake_session.execute = MagicMock(return_value=fake_result)
    fake_session.commit = MagicMock()

    @contextmanager
    def _db_session():
        yield fake_session

    svc.get_db_session = _db_session
    return svc


@pytest.fixture
def client(mock_supabase):
    """FastAPI TestClient with the supabase + llm dependencies overridden.

    No `with` block — that's how we skip the startup handler that would
    otherwise try to talk to a real Supabase. Catalog endpoints that
    depend on `app.state.all_grants_config` are exercised separately;
    everything under `/api/demo/*` only needs the supabase override.
    """
    from fastapi.testclient import TestClient
    from app.api.dependencies import get_llm_service, get_supabase_service
    from app.main import app

    app.dependency_overrides[get_supabase_service] = lambda: mock_supabase
    app.dependency_overrides[get_llm_service] = lambda: MagicMock()
    # Some endpoints read `request.app.state.supabase_service` directly.
    app.state.supabase_service = mock_supabase

    yield TestClient(app)

    app.dependency_overrides.clear()
