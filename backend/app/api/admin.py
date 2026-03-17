# 内部人員/系統獨有操作的api

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from app.models import RoutingRule, UpdateSectionSettingsRequest
from app.services.supabase_service import SupabaseService
from .dependencies import get_supabase_service, verify_internal_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Administration"]
)

@router.get("/models", response_model=List[Dict[str, Any]])
async def get_all_models(request: Request):
    """獲取所有可用的模型列表"""
    if not hasattr(request.app.state, 'model_registry'):
        raise HTTPException(status_code=500, detail="Model registry not initialized.")
    
    models = list(request.app.state.model_registry.values())
    return models

@router.get("/routing-rules", response_model=List[Dict[str, Any]])
async def get_all_routing_rules(request: Request):
    """獲取所有路由規則"""
    if not hasattr(request.app.state, 'routing_rules'):
        raise HTTPException(status_code=500, detail="Routing rules not initialized.")
    return request.app.state.routing_rules

@router.post("/routing-rules", response_model=Dict[str, Any])
async def set_routing_rule(
    rule: RoutingRule,
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _=Depends(verify_internal_user),
):
    """新增或更新一個路由規則"""
    try:
        new_rule_data = await supabase_service.upsert_routing_rule(rule)
        
        # 動態更新應用程式的實時狀態
        request.app.state.routing_rules = await supabase_service.get_all_routing_rules()
        logger.info(f"Routing rule updated for model '{rule.model_id}'. Reloaded rules.")
        
        return {"status": "success", "rule": new_rule_data}
    except Exception as e:
        logger.error(f"Failed to set routing rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/routing-rules/{rule_id}", status_code=200)
async def delete_routing_rule(
    rule_id: str,
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _=Depends(verify_internal_user),
):
    """刪除指定 ID 的路由規則"""
    try:
        await supabase_service.delete_routing_rule(rule_id)
        
        # 動態更新應用程式的實時狀態
        request.app.state.routing_rules = await supabase_service.get_all_routing_rules()
        logger.info(f"Routing rule '{rule_id}' deleted successfully. Reloaded rules.")
        
        return {"status": "success", "message": f"Routing rule '{rule_id}' deleted successfully."}
    except Exception as e:
        logger.error(f"Failed to delete routing rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sections/{section_id}/prompts", status_code=200, summary="更新章節的自定義指令列表")
async def update_section_prompts_endpoint(
    request: Request,
    section_id: str, 
    request_data: UpdateSectionSettingsRequest,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _=Depends(verify_internal_user),
):
    """更新指定章節的自定義提示詞列表。"""
    if not request_data.grant_id or not request_data.template_id:
        raise HTTPException(status_code=400, detail="Grant ID and template ID are required.")

    success = await supabase_service.update_section_settings(
        request,
        section_id, 
        request_data.template_id,
        request_data.grant_id,
        request_data.custom_prompt_list, 
        request_data.system_prompt,
        request_data.search_external,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Section not found or update failed.")
    return {"message": "Section settings updated successfully."}

@router.get("/user-usage")
async def user_usage(user_id: str, supabase_service: SupabaseService = Depends(get_supabase_service)):
    """取得指定 user_id 的總用量 (cost)"""
    usage = await supabase_service.get_user_usage(user_id)
    return {"usage": usage} 

@router.post("/refresh-datasets", summary="手動刷新所有 datasets")
async def refresh_datasets_endpoint(
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """
    手動刷新所有 datasets 數據，從數據庫重新加載最新的 datasets。
    更新 app.state.all_datasets。
    """
    try:
        logger.info("Starting manual refresh of datasets...")
        datasets_data = await supabase_service.get_all_datasets()
        
        # 更新應用程式的實時狀態
        request.app.state.all_datasets = datasets_data
        logger.info(f"Successfully reloaded {len(request.app.state.all_datasets)} datasets.")
        
        return {
            "status": "success",
            "message": "Datasets refreshed successfully",
            "datasets": request.app.state.all_datasets,
        }
    except Exception as e:
        logger.error(f"Failed to refresh datasets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
