# 初始化和關閉服務

import logging
from fastapi import FastAPI
from app.services.supabase_service import SupabaseService
from app.services.qdrant_service import QdrantService
from app.services.llm_service import LLMService
import asyncio

logger = logging.getLogger(__name__)

async def startup_event_handler(app: FastAPI):
    """
    主要任務:
    1. 初始化所有核心服務 (Supabase, Qdrant, LLM)。
    2. 將服務實例附加到 app.state，以便在整個應用程式中共享。
    3. 從數據庫預加載必要的配置數據到內存中，以提高後續請求的性能。
    """
    logger.info("Application startup process initiated...")
    
    try:
        # --- 1. 初始化核心服務 ---
        logger.info("Initializing core services...")
        supabase_service = SupabaseService()
        qdrant_service = QdrantService()
        llm_service = LLMService(qdrant_service) # LLMService 依賴 QdrantService

        # --- 2. 將服務實例附加到 app.state ---
        app.state.supabase_service = supabase_service
        app.state.qdrant_service = qdrant_service
        app.state.llm_service = llm_service
        logger.info("Core services initialized and attached to app state.")

        # --- 3. 預加載配置數據到內存 ---
        logger.info("Pre-loading configurations from Supabase...")
        
        # 使用 asyncio.gather 可以併發執行這些異步加載操作，提高啟動速度
        models_data, rules_data, grants_data = await asyncio.gather(
            supabase_service.get_all_models(),
            supabase_service.get_all_routing_rules(),
            supabase_service.get_all_grants_config()
        )
        
        # 將加載的數據存儲到 app.state
        app.state.model_registry = {m['id']: m for m in models_data}
        app.state.routing_rules = rules_data
        app.state.all_grants_config = grants_data
        
        logger.info(f"Successfully loaded {len(app.state.model_registry)} models.")
        logger.info(f"Successfully loaded {len(app.state.routing_rules)} routing rules.")
        logger.info(f"Successfully loaded configurations for {len(app.state.all_grants_config)} grants.")
        
    except Exception as e:
        logger.critical(f"A critical error occurred during application startup: {e}", exc_info=True)
        raise RuntimeError("Failed to initialize application state during startup.") from e

    logger.info("Application startup process completed successfully.")

async def shutdown_event_handler(app: FastAPI):
    """關閉任何需要清理的資源，例如數據庫連接池、後台任務等。 """
    logger.info("Application shutdown process completed.")