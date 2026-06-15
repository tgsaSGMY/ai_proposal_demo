"""Integration tests for the /api/demo router + cookie minting.

Drives FastAPI via TestClient with a mocked SupabaseService (see conftest).
Verifies the contract the frontend at pages/index.vue relies on:
  - first GET mints `demo_session_id` (HttpOnly cookie, Lax, /, 30d)
  - subsequent GETs reuse the cookie
  - PUT round-trips grant_id / template_id / payload fields
  - DELETE wipes the row but leaves the cookie in place
  - rate-limited mint returns 429 with a Retry-After header
"""

from __future__ import annotations

import uuid

from app.api.dependencies import DEMO_SESSION_COOKIE_NAME, DEMO_SESSION_COOKIE_MAX_AGE_SECONDS
from app.config import DEMO_SESSION_EXPIRY_DAYS


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def test_first_get_mints_cookie_and_creates_row(client, demo_store):
    response = client.get("/api/demo")
    assert response.status_code == 200
    body = response.json()
    assert _is_uuid(body["session_id"])

    # Cookie is set on the response — TestClient persists it on the client.
    # Cookie attribute names are case-insensitive per RFC 6265 — lower
    # the haystack once and assert against lowercase literals.
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert DEMO_SESSION_COOKIE_NAME in set_cookie
    assert "httponly" in set_cookie
    assert "path=/" in set_cookie
    assert f"max-age={DEMO_SESSION_COOKIE_MAX_AGE_SECONDS}" in set_cookie
    assert "samesite=lax" in set_cookie

    # The store actually got the row.
    assert body["session_id"] in demo_store.rows


def test_subsequent_get_reuses_cookie(client):
    first = client.get("/api/demo")
    second = client.get("/api/demo")
    assert first.json()["session_id"] == second.json()["session_id"]
    # No new Set-Cookie on the second hit (cookie was already valid).
    assert "set-cookie" not in {h.lower() for h in second.headers}


def test_garbage_cookie_is_replaced_with_fresh_uuid(client):
    """A spoofed / corrupted cookie value falls back to the mint branch."""
    client.cookies.set(DEMO_SESSION_COOKIE_NAME, "not-a-uuid")
    response = client.get("/api/demo")
    assert response.status_code == 200
    assert _is_uuid(response.json()["session_id"])


def test_put_round_trips_payload(client):
    client.get("/api/demo")  # mint

    put = client.put(
        "/api/demo",
        json={
            "grant_id": "sbir",
            "template_id": "sbir-p1",
            "stored_answer": {"chat_answers": {"q1": "answer one"}},
            "conversation_history": [{"role": "user", "content": "hi"}],
        },
    )
    assert put.status_code == 200
    payload = put.json()
    assert payload["grant_id"] == "sbir"
    assert payload["template_id"] == "sbir-p1"

    get = client.get("/api/demo")
    assert get.json()["grant_id"] == "sbir"
    assert get.json()["template_id"] == "sbir-p1"


def test_put_with_empty_body_is_a_noop(client):
    client.get("/api/demo")
    response = client.put("/api/demo", json={})
    assert response.status_code == 200
    # Row exists but has no grant set.
    assert response.json().get("grant_id") is None


def test_delete_clears_row_and_next_get_mints_fresh(client, demo_store):
    mint = client.get("/api/demo")
    session_id = mint.json()["session_id"]
    assert session_id in demo_store.rows

    response = client.delete("/api/demo")
    assert response.status_code == 200
    assert response.json() == {"status": "reset", "session_id": session_id}
    assert session_id not in demo_store.rows

    # After DELETE the row is gone; get_demo_session_id treats the stale cookie
    # as a miss and mints a fresh session (same behaviour as a claimed row).
    next_get = client.get("/api/demo")
    new_session_id = next_get.json()["session_id"]
    assert _is_uuid(new_session_id)
    assert new_session_id != session_id
    assert new_session_id in demo_store.rows


def test_rate_limit_returns_429_with_retry_after(client, rate_limit_rows):
    """Simulate hourly cap exceeded on the mint branch."""
    from app.config import DEMO_IP_HOURLY_LIMIT

    rate_limit_rows[:] = [("hour", DEMO_IP_HOURLY_LIMIT + 1), ("day", 1)]

    response = client.get("/api/demo")
    assert response.status_code == 429
    detail = response.json()["detail"]
    assert detail["code"] == "DEMO_HOURLY_LIMIT_EXCEEDED"
    assert detail["retry_after"] >= 1
    assert "retry-after" in {h.lower() for h in response.headers}


def test_rate_limit_skipped_when_cookie_already_present(client, rate_limit_rows):
    """An existing-session GET must not consume rate-limit budget."""
    rate_limit_rows[:] = [("hour", 1), ("day", 1)]
    mint = client.get("/api/demo")
    assert mint.status_code == 200

    # Now flip the limiter to "would reject" and confirm the second call
    # passes anyway because the cookie short-circuits the mint branch.
    from app.config import DEMO_IP_HOURLY_LIMIT
    rate_limit_rows[:] = [("hour", DEMO_IP_HOURLY_LIMIT + 1), ("day", 1)]

    response = client.get("/api/demo")
    assert response.status_code == 200


def test_get_skips_claimed_row_and_mints_fresh(client, demo_store):
    """A returning visitor whose row was claimed should mint a fresh session
    instead of reusing the dead row. The claimed row stays in the store as
    analytics; the new row uses a new UUID."""
    first = client.get("/api/demo")
    first_session_id = first.json()["session_id"]
    assert demo_store.rows[first_session_id]["status"] == "active"

    # Simulate the parent platform claiming the row.
    demo_store.rows[first_session_id]["status"] = "claimed"

    # Second GET: TestClient's cookie jar still has the cookie from the first
    # GET, so the backend sees a stale demo_session_id pointing at a now-
    # claimed row. get_demo_session_id should mint a fresh session.
    response = client.get("/api/demo")

    new_session_id = response.json()["session_id"]
    assert _is_uuid(new_session_id)
    assert new_session_id != first_session_id
    # Set-Cookie header on the response should rotate the cookie value.
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert f"demo_session_id={new_session_id.lower()}" in set_cookie

    # The claimed row is preserved.
    assert demo_store.rows[first_session_id]["status"] == "claimed"
    # The new row exists and is active.
    assert demo_store.rows[new_session_id]["status"] == "active"


def test_cookie_max_age_matches_env(client):
    """The Set-Cookie max-age must match DEMO_SESSION_EXPIRY_DAYS from .env."""
    response = client.get("/api/demo")
    assert response.status_code == 200
    expected_max_age = DEMO_SESSION_EXPIRY_DAYS * 24 * 60 * 60
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert f"max-age={expected_max_age}" in set_cookie


def test_expired_session_is_rejected_and_mints_fresh(client, demo_store):
    """A row with expires_at in the past must be treated as invalid, triggering
    a fresh session mint on the next request."""
    from datetime import datetime, timedelta, timezone
    mint = client.get("/api/demo")
    first_session_id = mint.json()["session_id"]
    assert first_session_id in demo_store.rows

    # Manually expire the row
    demo_store.rows[first_session_id]["expires_at"] = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()

    # Next GET: the backend sees an expired row, returns None, and mints fresh.
    response = client.get("/api/demo")
    new_session_id = response.json()["session_id"]
    assert _is_uuid(new_session_id)
    assert new_session_id != first_session_id
    assert new_session_id in demo_store.rows
    # The old row is still in the store (not deleted by the test)
    assert first_session_id in demo_store.rows


def test_new_row_has_expires_at(client, demo_store):
    """A newly created demo row must have a future expires_at."""
    from datetime import datetime, timezone
    response = client.get("/api/demo")
    session_id = response.json()["session_id"]
    row = demo_store.rows[session_id]
    assert "expires_at" in row
    expires_at = row["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    assert expires_at > datetime.now(timezone.utc)
