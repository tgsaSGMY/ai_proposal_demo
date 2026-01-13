# 内部人員/系統獨有操作的api

import json
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from app.models import RoutingRule, UpdateSectionSettingsRequest,ScrapeRequest
from app.services.supabase_service import SupabaseService
from .dependencies import get_supabase_service,get_llm_service,verify_internal_user
from app.services.llm_service import LLMService
from app.utils.scrape_website_text import scrape_website_text
import httpx

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

@router.post("/scrape_and_analyze", summary="抓取網頁並由 AI 分析重點")
async def scrape_and_analyze(
    req: ScrapeRequest,
    request: Request,
    user_id: str = "dba4dabc-a24d-4e1a-aa2b-b239d06a8cf5",
    llm_service: LLMService = Depends(get_llm_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    try:
        # 1️⃣ 抓取網頁內容
        scraped_text = scrape_website_text(req.url)
        if not scraped_text.strip():
            raise HTTPException(status_code=400, detail="無法抓取網站內容或內容為空。")

        # 避免超長文字導致 token 超限
        if len(scraped_text) > 10000:
            scraped_text = scraped_text[:10000]

        # 2️⃣ 準備 Prompt
        max_items = req.max_items or 4
        target_lines = []
        for target in req.context_targets:
            section_hint = (
                    f" (section: {target.section_id}, field: {target.property_key}, sub: {target.sub_field_key})"
                    if target.section_id and target.property_key and target.sub_field_key
                    else ""
            )
            target_lines.append(f"- composite_key: {section_hint}")

        targets_block = "\n".join(target_lines) if target_lines else "(未提供具體欄位，請僅在高度相關時回傳)"

        system_prompt = f"""
        你是一位精準的信息萃取專家。請閱讀提供的網頁原文，
        只在內容與使用者的關注欄位高度相關時，建立自動填寫建議。

        使用者正在撰寫商業計劃書。以下為潛在的目標欄位：
        {targets_block}
        請務必遵守以下要求：
        1. 只輸出 JSON 物件，格式為：
                {{
                    "summary": "對原文的高度概括，1-2 句",
                    "auto_fill": [
                        {{
                            "composite_key": "<section::field::sub>",
                            "label": "對應欄位標籤",
                            "relevance": "high" 或 "medium",
                            "content": "從原文中提煉的重點，1-3 句內"
                        }}
                    ]
                }}
        2. composite_key 必須與使用者提供的目標欄位完全對應。
        3. 最多提供 {max_items} 個 auto_fill 項目，若沒有高度相關內容則輸出空陣列。
        4. 不得虛構或推測資訊。
        5. content除了公司名等專有名詞外，其他一律使用繁體中文回答。
        """

        user_prompt = (
                "網頁原文:\n---\n"
                + scraped_text
        )

        # 3️⃣ 取得模型設定
        model_registry = request.app.state.model_registry
        model_to_use = model_registry.get("gpt-4.1-nano") or model_registry.get("gpt-4.5-turbo")
        if not model_to_use:
            raise HTTPException(status_code=500, detail="需要配置 GPT-3.5 或 GPT-4 模型。")

        # 4️⃣ 組成 messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 5️⃣ 調用 LLM API
        async with httpx.AsyncClient(timeout=180.0) as client:
            summary_raw, llm_error = await llm_service.call_external_api(
                client,
                model_to_use,
                messages,
                is_json_output=True
            )

        if llm_error:
            raise HTTPException(status_code=500, detail=f"LLM API Error: {llm_error}")

        if summary_raw is None:
            raise HTTPException(status_code=500, detail="LLM 回傳內容為空。")

        await supabase_service.log_cost_usage(user_id, model_to_use, messages, summary_raw)

        try:
            parsed_summary = json.loads(summary_raw)
        except json.JSONDecodeError:
            logger.warning("LLM 未回傳有效 JSON，回傳原始摘要。")
            return {"summary": summary_raw.strip(), "auto_fill": []}

        auto_fill_items = parsed_summary.get("auto_fill") or []
        filtered_items = []
        seen_keys = set()

        for item in auto_fill_items:
            composite_key = (item.get("composite_key") or "").strip()
            content = (item.get("content") or "").strip()
            relevance = (item.get("relevance") or "").lower()

            if not composite_key or not content:
                continue
            if composite_key in seen_keys:
                continue

            filtered_items.append(
                {
                    "composite_key": composite_key,
                    "label": item.get("label") or "",
                    "relevance": relevance,
                    "content": content,
                }
            )
            seen_keys.add(composite_key)

            if len(filtered_items) >= max_items:
                break

        parsed_summary["auto_fill"] = filtered_items
        parsed_summary.setdefault("summary", "")

        return parsed_summary

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error during scrape_and_analyze: {e}")
        raise HTTPException(status_code=500, detail="伺服器內部錯誤")

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
