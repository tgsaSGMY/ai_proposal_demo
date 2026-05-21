"""Guard against accidental re-registration of removed routers.

Phase 0.5 of next-implementation.md dropped auth, external_auth, datasets,
generate, and the per-user projects routes. If any of them sneaks back in,
the demo becomes a security/footprint liability — these tests fail loudly.
"""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/api/auth/login"),
        ("POST", "/api/auth/register"),
        ("GET", "/api/auth/me"),
        ("GET", "/api/external_auth/callback"),
        ("GET", "/api/datasets"),
        ("POST", "/api/datasets"),
        ("POST", "/api/generate"),
        ("GET", "/api/projects/00000000-0000-0000-0000-000000000000"),
        ("POST", "/api/projects"),
    ],
)
def test_removed_routes_return_404(client, method, path):
    response = client.request(method, path)
    assert response.status_code == 404, (
        f"{method} {path} returned {response.status_code} — "
        f"a removed router has been re-registered."
    )


def test_demo_routes_are_still_registered(client):
    """Sanity check: not every route is 404."""
    response = client.get("/api/demo")
    assert response.status_code == 200


def test_root_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "demo" in response.json()["message"].lower()


def test_cors_only_allows_known_origins(client):
    """Preflight from a random origin must not echo back Access-Control-Allow-Origin."""
    preflight = client.options(
        "/api/demo",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI's CORSMiddleware rejects by omitting the Allow-Origin header
    # (or returning 400 in stricter setups). Either way, the evil origin
    # must not appear in the response.
    assert preflight.headers.get("access-control-allow-origin") != "https://evil.example.com"
