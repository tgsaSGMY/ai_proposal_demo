# Application startup / shutdown wiring.
#
# The demo backend has no auth and no mother-platform integration, so this
# module only initialises Supabase + LLM services and pre-loads the read-only
# catalog (grants, templates, sections, model registry, routing rules, active
# prompt templates and feature-model settings shared with the platform).
# The datasets archive is never loaded.

import asyncio
import logging

from fastapi import FastAPI

from app.services.llm_service import LLMService
from app.services.prompt_registry_service import PromptRegistryService
from app.services.supabase_service import SupabaseService
from app.utils.memory_metrics import log_memory
from app.utils.model_helper import normalize_provider

logger = logging.getLogger(__name__)


async def reload_configurations(app: FastAPI):
    """Re-pull the read-only catalog into app.state.

    The datasets archive is deliberately NOT loaded: it grows with usage, and a
    full copy in every backend process exhausted the shared VM's memory
    (2026-11-16). Few-shot examples come from the match_datasets RPC instead.
    """
    logger.info("Reloading configurations from Supabase...")
    supabase_service = app.state.supabase_service

    models_data, rules_data, grants_data, prompts_data, feature_models_data = await asyncio.gather(
        supabase_service.get_all_models(),
        supabase_service.get_all_routing_rules(),
        supabase_service.get_all_grants_config(),
        supabase_service.get_all_active_prompt_templates(),
        supabase_service.get_all_feature_model_settings(),
    )

    for m in models_data:
        m["provider"] = normalize_provider(m.get("provider"))
    app.state.model_registry = {m["id"]: m for m in models_data}
    app.state.routing_rules = rules_data
    app.state.feature_model_settings = feature_models_data
    app.state.all_grants_config = grants_data
    app.state.prompt_registry = {p["name"]: p for p in prompts_data}
    app.state.prompt_registry_service.load_cache(prompts_data)

    logger.info(
        "Reload complete: %d models, %d rules, %d feature model settings, %d grants, %d prompt templates.",
        len(app.state.model_registry),
        len(app.state.routing_rules),
        len(app.state.feature_model_settings),
        len(app.state.all_grants_config),
        len(app.state.prompt_registry),
    )
    return {
        "success": True,
        "models_count": len(app.state.model_registry),
        "rules_count": len(app.state.routing_rules),
        "grants_count": len(app.state.all_grants_config),
        "datasets_preloaded": False,
        "prompts_count": len(app.state.prompt_registry),
    }


async def startup_event_handler(app: FastAPI):
    logger.info("Application startup initiated.")
    # /api/health/ready answers 503 until everything below has succeeded
    app.state.ready = False
    log_memory("before-services")
    try:
        supabase_service = SupabaseService()  # includes the embedding model, once per process
        log_memory("after-supabase-and-embedding-model")
        app.state.supabase_service = supabase_service
        app.state.llm_service = LLMService()
        app.state.prompt_registry_service = PromptRegistryService(supabase_service)
        logger.info("Core services initialised.")
        await reload_configurations(app)
        log_memory("after-configurations")
    except Exception as exc:
        logger.critical("Critical startup failure: %s", exc, exc_info=True)
        raise RuntimeError("Failed to initialize application state during startup.") from exc
    app.state.ready = True
    log_memory("startup-complete")
    logger.info("Application startup completed.")


async def shutdown_event_handler(app: FastAPI):
    logger.info("Application shutdown completed.")
