# 初始化和關閉服務

import logging
from fastapi import FastAPI
from app.services.supabase_service import SupabaseService
from app.services.llm_service import LLMService
from app.config import ENGINE_USAGE_ENABLED
import asyncio

logger = logging.getLogger(__name__)

async def reload_configurations(app: FastAPI):
    """
    重新加載模型、路由規則、Grant 配置數據和 Datasets 到內存。
    可在啟動時和手動刷新時調用。
    """
    try:
        logger.info("Reloading configurations from Supabase...")
        supabase_service = app.state.supabase_service
        
        models_data, rules_data, grants_data, datasets_data = await asyncio.gather(
            supabase_service.get_all_models(),
            supabase_service.get_all_routing_rules(),
            supabase_service.get_all_grants_config(),
            supabase_service.get_all_datasets()
        )
        
        app.state.model_registry = {m['id']: m for m in models_data}
        app.state.routing_rules = rules_data
        app.state.all_grants_config = grants_data
        app.state.all_datasets = datasets_data
        
        logger.info(f"Successfully reloaded {len(app.state.model_registry)} models.")
        logger.info(f"Successfully reloaded {len(app.state.routing_rules)} routing rules.")
        logger.info(f"Successfully reloaded configurations for {len(app.state.all_grants_config)} grants.")
        logger.info(f"Successfully reloaded {len(app.state.all_datasets)} datasets.")
        
        return {
            "success": True,
            "models_count": len(app.state.model_registry),
            "rules_count": len(app.state.routing_rules),
            "grants_count": len(app.state.all_grants_config),
            "datasets_count": len(app.state.all_datasets),
        }
    except Exception as e:
        logger.error(f"Failed to reload configurations: {e}", exc_info=True)
        raise

async def startup_event_handler(app: FastAPI):
    """
    主要任務:
    1. 初始化所有核心服務 (Supabase, LLM)。
    2. 將服務實例附加到 app.state，以便在整個應用程式中共享。
    3. 從數據庫預加載必要的配置數據到內存中，以提高後續請求的性能。
    """
    logger.info("Application startup process initiated...")
    
    try:
        # --- 1. 初始化核心服務 ---
        logger.info("Initializing core services...")
        supabase_service = SupabaseService()
        llm_service = LLMService()

        # --- 2. 將服務實例附加到 app.state ---
        app.state.supabase_service = supabase_service
        app.state.llm_service = llm_service
        logger.info("Core services initialized and attached to app state.")

        # --- 3. 預加載配置數據到內存 ---
        logger.info("Pre-loading configurations from Supabase...")
        await reload_configurations(app)

        # --- 4. 啟動 engine usage 重送背景 task ---
        if ENGINE_USAGE_ENABLED:
            try:
                from app.services.engine_usage_reporter import retry_loop
                app.state.engine_usage_retry_task = asyncio.create_task(
                    retry_loop(app.state.supabase_service)
                )
                logger.info("Engine usage retry loop scheduled.")
            except Exception:
                logger.exception("Failed to schedule engine usage retry loop")
        else:
            logger.info("ENGINE_USAGE_ENABLED=false; skipping retry loop.")

    except Exception as e:
        logger.critical(f"A critical error occurred during application startup: {e}", exc_info=True)
        raise RuntimeError("Failed to initialize application state during startup.") from e

    logger.info("Application startup process completed successfully.")

async def shutdown_event_handler(app: FastAPI):
    """關閉任何需要清理的資源，例如數據庫連接池、後台任務等。 """
    task = getattr(app.state, "engine_usage_retry_task", None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass
    logger.info("Application shutdown process completed.")