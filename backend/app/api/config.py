# 調取完整主題、模板和分項

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from app.models import GrantConfig
from app.core.lifecycle import reload_configurations
from app.api.dependencies import get_supabase_service
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Configuration"]
)

@router.get("/config", response_model=List[GrantConfig])
async def get_all_configs(
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """
    從 app.state 已快取的 Grant/Template/Section 配置回傳。
    template_manager 會在管理員修改時自動刷新此快取，因此快取與 DB 內容保持同步。
    若快取尚未建立（極少見的啟動競態），則退回直接從 Supabase 取得以保持服務韌性。
    """
    try:
        cached = getattr(request.app.state, "all_grants_config", None)
        if cached:
            return cached
        # 退路：app.state 快取尚未填充時直接從 Supabase 取得（防禦性程式碼）
        return await supabase_service.get_all_grants_config()
    except Exception as e:
        logger.error(f"Failed to retrieve configurations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching configurations.")

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


@router.get("/plan_templates", response_model=List[Dict[str, Any]], summary="取得所有計畫模板")
async def get_plan_templates(
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """
    從 Supabase 取得所有計畫模板列表，包含 logo、描述等資訊。
    """
    try:
        response = (
            supabase_service.client
            .from_("plan_templates")
            .select("*")
            .order("order", desc=False)
            .order("id", desc=False)
            .execute()
        )
        
        if response.data:
            return response.data
        return []
        
    except Exception as e:
        logger.error(f"Failed to fetch plan templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch plan templates")