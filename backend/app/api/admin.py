# 内部人員/系統獨有操作的api

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from app.models import RoutingRule, UpdateSectionSettingsRequest,ScrapeRequest
from app.services.supabase_service import SupabaseService
from .dependencies import get_supabase_service,get_llm_service
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
    )
    if not success:
        raise HTTPException(status_code=404, detail="Section not found or update failed.")
    return {"message": "Section settings updated successfully."}

# @router.post("/scrape_and_analyze", summary="抓取網頁並由 AI 分析重點")
# async def scrape_and_analyze(
#     req: ScrapeRequest,
#     request: Request,
#     llm_service: LLMService = Depends(get_llm_service) 
# ):
    # try:
    #     # 1. 抓取網頁內容
    #     scraped_text = scrape_website_text(req.url)
    #     print(scraped_text)
    #     print(req.context_keywords)

    #     # 2. 準備 Prompt 讓 AI 分析
    #     system_prompt = f"""
    #     你是一位高效的信息分析專家。你的任務是閱讀一份網頁內容，並根據用戶提供的「關注點」，提煉出最相關的核心要點。

    #     用戶正在撰寫一份商業計劃書，他們提供的「關注點」是計劃書中需要填寫的欄位。
    #     關注點: {req.context_keywords}

    #     請你總結網頁內容中與這些關注點最相關的信息，並以一個清晰、簡潔的段落返回。總結的內容將作為額外參考資料，幫助用戶撰寫計劃書。
    #     """
        
    #     user_prompt = f"網頁原文:\n---\n{scraped_text}\n---\n請根據以上原文和系統指令中的關注點，生成重點摘要。"

    #     # 3. 調用 OpenAI
    #     model_info = request.app.state.model_registry.get("gpt-3.5-turbo-1106") 
    #     if not model_info:
    #         raise HTTPException(status_code=500, detail="GPT-3.5 Turbo model not configured.")

    #     async with httpx.AsyncClient(timeout=60.0) as client:
    #         summary, error = await llm_service.call_external_api(client, model_info, [
    #             {"role": "system", "content": system_prompt},
    #             {"role": "user", "content": user_prompt}
    #         ])
    #         if error:
    #             raise HTTPException(status_code=500, detail=error.get("error", "LLM API failed"))
        
    #     return {"summary": summary}
        
    # except HTTPException as e:
    #     raise e
    # except Exception as e:
    #     logger.error(f"Unexpected error in scrape_and_analyze: {e}")
    #     raise HTTPException(status_code=500, detail="伺服器內部錯誤")


@router.post("/scrape_and_analyze", summary="抓取網頁並由 AI 分析重點")
async def scrape_and_analyze(
    req: ScrapeRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service)
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
        system_prompt = f"""
        你是一位高效的信息分析專家。你的任務是閱讀一份網頁內容，
        並根據用戶提供的「關注點」，提煉出最相關的核心要點。

        用戶正在撰寫一份商業計劃書，
        他們提供的「關注點」是計劃書中需要填寫的欄位。
        關注點: {req.context_keywords}

        請你總結網頁內容中與這些關注點最相關的信息，
        並以一個清晰、簡潔的段落返回。
        """

        user_prompt = f"網頁原文:\n---\n{scraped_text}\n---\n請根據以上原文和系統指令生成重點摘要。"

        # 3️⃣ 取得模型設定
        model_registry = request.app.state.model_registry
        model_to_use = model_registry.get("gpt-3.5-turbo-1106") or model_registry.get("gpt-4.5-turbo")
        if not model_to_use:
            raise HTTPException(status_code=500, detail="需要配置 GPT-3.5 或 GPT-4 模型。")

        # 4️⃣ 組成 messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 5️⃣ 調用 LLM API
        async with httpx.AsyncClient(timeout=180.0) as client:
            summary, llm_error = await llm_service.call_external_api(
                client,
                model_to_use,
                messages,
                is_json_output=False  
            )

        if llm_error:
            raise HTTPException(status_code=500, detail=f"LLM API Error: {llm_error}")

        # 6️⃣ 返回最終摘要結果
        return {"summary": summary.strip()}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error during scrape_and_analyze: {e}")
        raise HTTPException(status_code=500, detail="伺服器內部錯誤")

