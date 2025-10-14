# app/api/admin.py

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from app.models import RoutingRule, UpdateSectionSettingsRequest
from app.services.supabase_service import SupabaseService
from .dependencies import get_supabase_service

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
    return list(request.app.state.model_registry.values())

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

@router.put("/sections/{section_id}/prompts", status_code=200, summary="更新章節的自定義指令列表")
async def update_section_prompts_endpoint(
    section_id: str, 
    request_data: UpdateSectionSettingsRequest,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """更新指定章節的自定義提示詞列表。"""
    success = await supabase_service.update_section_settings(
        section_id, 
        request_data.prompts, 
        request_data.system_prompt,
        request_data.source_type
    )
    if not success:
        raise HTTPException(status_code=404, detail="Section not found or update failed.")
    return {"message": "Section settings updated successfully."}