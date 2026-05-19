# Application startup / shutdown wiring.
#
# The demo backend has no auth and no mother-platform integration, so this
# module only initialises Supabase + LLM services and pre-loads the read-only
# catalog (grants, templates, sections, datasets, model registry, routing rules).

import asyncio
import logging

from fastapi import FastAPI

from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


async def reload_configurations(app: FastAPI):
    """Re-pull the read-only catalog into app.state."""
    logger.info("Reloading configurations from Supabase...")
    supabase_service = app.state.supabase_service

    models_data, rules_data, grants_data, datasets_data = await asyncio.gather(
        supabase_service.get_all_models(),
        supabase_service.get_all_routing_rules(),
        supabase_service.get_all_grants_config(),
        supabase_service.get_all_datasets(),
    )

    app.state.model_registry = {m["id"]: m for m in models_data}
    app.state.routing_rules = rules_data
    app.state.all_grants_config = grants_data
    app.state.all_datasets = datasets_data

    logger.info(
        "Reload complete: %d models, %d rules, %d grants, %d datasets.",
        len(app.state.model_registry),
        len(app.state.routing_rules),
        len(app.state.all_grants_config),
        len(app.state.all_datasets),
    )
    return {
        "success": True,
        "models_count": len(app.state.model_registry),
        "rules_count": len(app.state.routing_rules),
        "grants_count": len(app.state.all_grants_config),
        "datasets_count": len(app.state.all_datasets),
    }


async def startup_event_handler(app: FastAPI):
    logger.info("Application startup initiated.")
    try:
        app.state.supabase_service = SupabaseService()
        app.state.llm_service = LLMService()
        logger.info("Core services initialised.")
        await reload_configurations(app)
    except Exception as exc:
        logger.critical("Critical startup failure: %s", exc, exc_info=True)
        raise RuntimeError("Failed to initialize application state during startup.") from exc
    logger.info("Application startup completed.")


async def shutdown_event_handler(app: FastAPI):
    logger.info("Application shutdown completed.")
