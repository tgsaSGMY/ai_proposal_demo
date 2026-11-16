"""Start-up must never read or keep the datasets archive.

On 2026-11-16 the shared production VM froze because start-up loaded the whole
datasets table into app.state. These tests pin the contract for the demo:
configuration loading touches only the small catalogue tables, the
`all_datasets` attribute is gone, and readiness flips only once start-up has
finished.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import lifecycle
from app.core.lifecycle import reload_configurations, startup_event_handler
from app.services.supabase_service import SupabaseService
from app.utils import memory_metrics


def _archive_guard(*_args, **_kwargs):
    raise AssertionError("configuration loading must not read the datasets archive")


def _catalogue_stub() -> MagicMock:
    """Supabase stub whose dataset readers fail the test if anything calls them."""
    service = MagicMock(name="SupabaseService")
    service.get_all_models = AsyncMock(return_value=[{"id": "m1", "provider": "google"}])
    service.get_all_routing_rules = AsyncMock(return_value=[{"id": 1}])
    service.get_all_grants_config = AsyncMock(return_value=[{"id": "g1"}])
    service.get_all_active_prompt_templates = AsyncMock(return_value=[{"name": "chat_guidance"}])
    service.get_all_feature_model_settings = AsyncMock(return_value=[{"feature": "x"}])
    service.get_all_datasets = MagicMock(side_effect=_archive_guard)
    service.client.from_ = MagicMock(side_effect=_archive_guard)
    return service


def _fake_app(service) -> SimpleNamespace:
    return SimpleNamespace(
        state=SimpleNamespace(supabase_service=service, prompt_registry_service=MagicMock())
    )


def _patched_services(service):
    return (
        patch.object(lifecycle, "SupabaseService", return_value=service),
        patch.object(lifecycle, "LLMService", return_value=MagicMock()),
        patch.object(lifecycle, "PromptRegistryService", return_value=MagicMock()),
    )


class TestReloadConfigurations:
    @pytest.mark.asyncio
    async def test_reload_never_reads_datasets_and_creates_no_all_datasets(self):
        app = _fake_app(_catalogue_stub())

        result = await reload_configurations(app)

        assert result["success"] is True
        assert result["datasets_preloaded"] is False
        assert "datasets_count" not in result
        assert not hasattr(app.state, "all_datasets")

    @pytest.mark.asyncio
    async def test_reload_still_populates_every_small_catalogue(self):
        app = _fake_app(_catalogue_stub())

        await reload_configurations(app)

        assert app.state.model_registry == {"m1": {"id": "m1", "provider": "gemini"}}
        assert app.state.routing_rules == [{"id": 1}]
        assert app.state.all_grants_config == [{"id": "g1"}]
        assert app.state.prompt_registry == {"chat_guidance": {"name": "chat_guidance"}}
        assert app.state.feature_model_settings == [{"feature": "x"}]
        app.state.prompt_registry_service.load_cache.assert_called_once_with([{"name": "chat_guidance"}])

    def test_unbounded_dataset_reader_no_longer_exists(self):
        assert not hasattr(SupabaseService, "get_all_datasets")


class TestStartupReadiness:
    @pytest.mark.asyncio
    async def test_ready_only_after_successful_startup(self):
        app = FastAPI()
        p1, p2, p3 = _patched_services(_catalogue_stub())
        with p1 as supabase_cls, p2, p3:
            await startup_event_handler(app)

        assert app.state.ready is True
        assert not hasattr(app.state, "all_datasets")
        supabase_cls.assert_called_once_with()  # embedding model built once per process

    @pytest.mark.asyncio
    async def test_failed_startup_leaves_ready_false(self):
        app = FastAPI()
        service = _catalogue_stub()
        service.get_all_models = AsyncMock(side_effect=RuntimeError("db down"))
        p1, p2, p3 = _patched_services(service)
        with p1, p2, p3, pytest.raises(RuntimeError):
            await startup_event_handler(app)

        assert app.state.ready is False

    def test_real_lifespan_reports_ready_through_the_endpoint(self):
        from app.main import app

        p1, p2, p3 = _patched_services(_catalogue_stub())
        try:
            with p1, p2, p3:
                with TestClient(app) as client:  # `with` runs the real start-up handler
                    response = client.get("/api/health/ready")
            assert response.status_code == 200
            assert response.json() == {"status": "ready"}
            assert not hasattr(app.state, "all_datasets")
        finally:
            app.state.ready = False

    def test_endpoint_returns_503_before_startup_finishes(self):
        from app.main import app

        app.state.ready = False
        response = TestClient(app).get("/api/health/ready")

        assert response.status_code == 503
        assert response.json() == {"status": "starting"}


class TestMemoryMetrics:
    def test_reads_linux_status_numbers_in_mb(self, tmp_path):
        status_file = tmp_path / "status"
        status_file.write_text(
            "Name:\tpython\nVmHWM:\t  2048 kB\nVmRSS:\t  1024 kB\nVmSwap:\t     0 kB\n",
            encoding="ascii",
        )

        assert memory_metrics.read_memory_snapshot(str(status_file)) == {
            "rss_mb": 1.0,
            "peak_mb": 2.0,
            "swap_mb": 0.0,
        }

    def test_missing_status_file_never_raises(self, tmp_path):
        assert memory_metrics.read_memory_snapshot(str(tmp_path / "missing")) == {
            "rss_mb": None,
            "peak_mb": None,
            "swap_mb": None,
        }
