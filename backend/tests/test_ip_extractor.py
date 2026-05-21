"""Unit tests for app.utils.ip_extractor.get_client_ip.

Pure function — no network, no DB. We hand-roll fake Request objects rather
than spin up a TestClient because the function only touches `.headers` and
`.client.host`.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.utils.ip_extractor import get_client_ip


def _request(headers: dict | None = None, host: str | None = "127.0.0.1"):
    return SimpleNamespace(
        headers={} if headers is None else headers,
        client=SimpleNamespace(host=host) if host is not None else None,
    )


def test_prefers_leftmost_x_forwarded_for():
    req = _request({"X-Forwarded-For": "9.9.9.9, 10.0.0.1, 172.16.0.1"})
    assert get_client_ip(req) == "9.9.9.9"


def test_strips_whitespace_around_xff_entry():
    req = _request({"X-Forwarded-For": "   8.8.8.8   ,1.1.1.1"})
    assert get_client_ip(req) == "8.8.8.8"


def test_falls_back_to_x_real_ip_when_xff_missing():
    req = _request({"X-Real-IP": "5.5.5.5"})
    assert get_client_ip(req) == "5.5.5.5"


def test_xff_wins_over_x_real_ip():
    req = _request({"X-Forwarded-For": "9.9.9.9", "X-Real-IP": "5.5.5.5"})
    assert get_client_ip(req) == "9.9.9.9"


def test_falls_back_to_request_client_host_when_no_headers():
    req = _request(host="203.0.113.7")
    assert get_client_ip(req) == "203.0.113.7"


def test_returns_none_when_no_source_available():
    req = _request(host=None)
    assert get_client_ip(req) is None


def test_empty_xff_falls_through_to_next_source():
    """Spec: an empty XFF entry shouldn't masquerade as a valid IP."""
    req = _request({"X-Forwarded-For": "   ,1.1.1.1"}, host="127.0.0.1")
    # First entry strips to "", so we fall through to client.host.
    assert get_client_ip(req) == "127.0.0.1"
