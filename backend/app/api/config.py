# 調取完整主題、模板和分項

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from app.models import GrantConfig
from app.core.lifecycle import reload_configurations

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Configuration"]
)

@router.get("/config", response_model=List[GrantConfig])
async def get_all_configs(request: Request):
    """
    從應用程式狀態中獲取已加載的所有 Grant、Template 和 Section 配置，直接返回內存中的數據。
    """
    try:
        if not hasattr(request.app.state, 'all_grants_config'):
             raise HTTPException(status_code=503, detail="Configurations are not yet loaded or failed to load.")
        return request.app.state.all_grants_config 
    except Exception as e:
        logger.error(f"Failed to retrieve configurations from app state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching configurations.")

@router.get("/datasets-lifecycle", response_model=List[Dict[str, Any]])
async def get_datasets_from_lifecycle(request: Request):
    """
    從應用程式狀態中獲取 lifecycle 預加載的 datasets，直接返回內存中的數據。
    """
    try:
        if not hasattr(request.app.state, 'all_datasets'):
            raise HTTPException(status_code=503, detail="Datasets are not yet loaded or failed to load.")
        return request.app.state.all_datasets
    except Exception as e:
        logger.error(f"Failed to retrieve datasets from app state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching datasets.")

@router.post("/config/refresh")
async def refresh_configurations(request: Request):
    """
    手動刷新模型、路由規則和 Grant 配置數據。
    重新從 Supabase 加載所有配置到內存中。
    """
    try:
        result = await reload_configurations(request.app)
        return {
            "success": True,
            "message": "Configurations refreshed successfully",
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to refresh configurations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to refresh configurations: {str(e)}")