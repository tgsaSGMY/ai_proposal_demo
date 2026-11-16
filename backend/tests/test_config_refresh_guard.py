"""POST /api/config/refresh is an operational endpoint guarded by SERVICE_KEY.

The demo has no user accounts, so refresh used to be callable by anyone on the
internet. It now needs the X-Service-Key header, and is refused outright when
the server has no key configured. The public catalogue stays open.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app import config as app_config

REFRESH = "/api/config/refresh"


@pytest.fixture
def reload_spy():
    spy = AsyncMock(return_value={"success": True, "datasets_preloaded": False})
    with patch("app.api.config.reload_configurations", spy):
        yield spy


def test_refused_when_server_has_no_key(client, reload_spy, monkeypatch):
    monkeypatch.setattr(app_config, "SERVICE_KEY", "")

    response = client.post(REFRESH, headers={"X-Service-Key": "anything"})

    assert response.status_code == 503
    reload_spy.assert_not_awaited()


@pytest.mark.parametrize("headers", [{}, {"X-Service-Key": ""}, {"X-Service-Key": "wrong"}])
def test_missing_or_wrong_key_is_refused(client, reload_spy, monkeypatch, headers):
    monkeypatch.setattr(app_config, "SERVICE_KEY", "right-secret")

    response = client.post(REFRESH, headers=headers)

    assert response.status_code == 401
    reload_spy.assert_not_awaited()


def test_right_key_refreshes_small_catalogues_only(client, reload_spy, monkeypatch):
    monkeypatch.setattr(app_config, "SERVICE_KEY", "right-secret")

    response = client.post(REFRESH, headers={"X-Service-Key": "right-secret"})

    assert response.status_code == 200
    assert response.json()["data"]["datasets_preloaded"] is False
    reload_spy.assert_awaited_once()


def test_public_catalogue_needs_no_key(client, mock_supabase, monkeypatch):
    from app.main import app

    monkeypatch.setattr(app_config, "SERVICE_KEY", "right-secret")
    monkeypatch.setattr(app.state, "all_grants_config", None, raising=False)
    mock_supabase.get_all_grants_config = AsyncMock(return_value=[])

    response = client.get("/api/config")

    assert response.status_code == 200
    assert response.json() == []
