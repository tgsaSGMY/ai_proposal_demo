import logging
import time
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request

from app.services.supabase_service import SupabaseService
from app.services.llm_service import LLMService
from app.models import DynamicFieldSchema
from app.api.dependencies import get_supabase_service, get_llm_service, verify_internal_user
from app.utils.extract_json import extract_json_block

logger = logging.getLogger(__name__)

# 草稿計畫相關 API 路由。
router = APIRouter(
    prefix="/api/draft_plans",
    tags=["Draft_Plans"]
)

# --- Pydantic 模型 ---
# 草稿更新請求：全部欄位採可選，支援局部更新。
class DraftPlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    grant_id: Optional[str] = None
    template_id: Optional[str] = None
    user_input: Optional[Dict[str, Any]] = None
    plan_content: Optional[Dict[str, Any]] = None
    rejected_answer: Optional[Dict[str, Any]] = None

class CreateDraftRequest(BaseModel):
    name: str
    mode: str
    grant_id: Optional[str] = None
    template_id: Optional[str] = None

# 批次合成草稿請求：限制一次最多 20 筆，避免後台任務壓力過大。
class BatchSyntheticRequest(BaseModel):
    '''批量生成請求'''
    count: int = Field(..., gt=0, le=20) # 限制一次最多生成 20 个
    grant_id: str
    template_id: str
    user_id: Optional[str] = Field(None, description="兼容舊客戶端，實際以當前登入者為準。")
    dynamic_fields_schema: Optional[List[DynamicFieldSchema]] = Field(
        default=None,
        description="指定批量任務使用的動態欄位標籤清單。",
    )

class SyntheticInputRequest(BaseModel):
    mode: str
    grant_name: str
    template_name: str
    user_id: str
    section_name: Optional[str] = None
    json_output: Optional[Dict[str, Any]] = None
    dynamic_fields_schema: Optional[List[Dict[str, str]]] = None

# --- 後台任務函式 ---
async def internal_generate_synthetic_input(
    req: SyntheticInputRequest,
    request: Request,
    llm_service: LLMService,
    supabase_service: SupabaseService,
) -> Dict[str, Any]:
    # AI隨機生成想法的内部函數

    # 從模型註冊表取用指定模型，若不存在則直接回 500。
    model_info = request.app.state.model_registry.get("gpt-5-mini")
    if not model_info:
        raise HTTPException(status_code=500, detail="GPT-5-mini model not configured for synthetic generation.")

    # 目前僅支援 random 模式，且需帶入動態欄位標籤清單。
    prompt = ""
    if req.mode == "random" and req.dynamic_fields_schema:
        field_labels = "\n".join([f"- {field['label']}" for field in req.dynamic_fields_schema])
        prompt = f"""
        你是一位嚴謹的商業策略專家，負責生成高品質的 AI 訓練資料。

        ### 任務說明
        1. 你需要**先構思一個與「{req.grant_name}」相關的新穎且具吸引力的商業／專案構想**。
        2. 然後，**僅根據你構思的這個點子**，依序回答下列所有問題。
        3. **所有問題都必須回答，不得遺漏、不得省略任何一題。**
        4. **問題的鍵名（key）必須與以下提供的文字完全相同，不得改寫、增刪、重新編號或重新命名。**

        ### 輸出格式（請嚴格遵守 JSON 結構）
        你必須回傳**單一有效 JSON 物件**，且前後不能有任何額外文字或註解。
        結構如下（請完全照抄鍵名與層級）：
        ```json
        {{
            "main_idea": "<在此輸入你生成的核心專案構想（單段文字）>",
            "dynamic_fields": {{
                "<question_label_1>": "<針對問題 1 的詳細文字回答>",
                "<question_label_2>": "<針對問題 2 的詳細文字回答>",
                ...
            }}
        }}
        ```

        📚 背景資訊
        補助主題：{req.grant_name}

        📝 問題清單（這些是 dynamic_fields 的鍵名，請逐一完整回答）：
        {field_labels}
        """
    else:
        raise HTTPException(status_code=400, detail="This internal function currently only supports 'random' mode.")

    # 呼叫 LLM 生成結構化 JSON，並做統一錯誤處理。
    async with httpx.AsyncClient(timeout=120.0) as client:
        messages = [{"role": "user", "content": prompt}]
        raw_output, error, _ = await llm_service.call_external_api(
            client,
            model_info,
            messages,
            is_json_output=True,
        )

        if error:
            raise HTTPException(status_code=500, detail=error.get("error", "Failed to generate synthetic input."))

        # 只萃取 JSON 區塊，避免模型前後多餘文字干擾解析。
        response_json_parsed, parse_error = extract_json_block(raw_output, "synthetic_input")
        if parse_error:
            raise HTTPException(status_code=500, detail=f"Failed to parse LLM JSON output: {parse_error}")
        return response_json_parsed


async def run_synthetic_idea_generation_task(
    draft_id: str,
    request_for_llm: Request, # 傳入 Request 對象以訪問 app.state
    supabase_service: SupabaseService, 
    llm_service: LLMService,
    user_id: str,
    dynamic_fields_schema: Optional[List[Dict[str, str]]] = None
):
    
    """AI隨機生成想法主程式 -後台任務：僅生成 synthetic user_input，不在此階段生成 plan_content。"""
    logger.info(f"Starting background idea generation for draft_id: {draft_id}")
    # 先切換狀態，讓前端可感知任務進入生成中。
    await supabase_service.update_draft_plan(draft_id, {"status": "generating_idea"})
    
    try:
        draft = await supabase_service.get_draft_plan_by_id(draft_id)
        if not draft:
            raise ValueError("Draft not found.")

        # 從草稿關聯資訊取得主題、模板與章節，缺任一則視為資料不完整。
        grant = await supabase_service.get_grant_by_id(draft['grant_id'])
        template = await supabase_service.get_template_by_id(draft['template_id'],draft['grant_id'])
        sections = await supabase_service.get_sections_by_template_id(draft['template_id'],draft['grant_id'])

        if not grant or not template or not sections:
            raise ValueError("Associated grant/template/sections not found for the draft.")

        # 將 DynamicFieldSchema 轉成生成函式所需的簡化 label 結構。
        dynamic_fields_schema1 = []
        for df in (dynamic_fields_schema or []):
            label = getattr(df, "label", "")
            dynamic_fields_schema1.append({"label": label})

        synthetic_req = SyntheticInputRequest(
            mode='random',
            grant_name=grant['name'],
            template_name=template['name'],
            dynamic_fields_schema=dynamic_fields_schema1,
            user_id=user_id,
            
        )
        
        # 呼叫內部生成函式，產出 synthetic user_input。
        generated_user_input = await internal_generate_synthetic_input(synthetic_req, request_for_llm, llm_service,supabase_service)

        # 任務完成後只回寫 user_input，plan_content 先保持空物件。
        update_payload = {
            "status": "completed", # 狀態改為 completed，表示想法已生成
            "user_input": generated_user_input,
            "plan_content": {} # Plan content 保持为空
        }
        await supabase_service.update_draft_plan(draft_id, update_payload)
        logger.info(f"Successfully completed idea generation for draft_id: {draft_id}")

    except Exception as e:
        logger.error(f"Error in background task for draft {draft_id}: {e}")
        error_message = str(e.detail) if isinstance(e, HTTPException) else str(e)
        await supabase_service.update_draft_plan(draft_id, {"status": "error", "error_message": error_message})


# --- API 端點 ---

@router.get("", response_model=List[Dict[str, Any]], summary="获取所有計畫草稿")
async def get_all_drafts(supabase_service: SupabaseService = Depends(get_supabase_service), _=Depends(verify_internal_user)):
    # 獲取所有計畫草稿記錄，僅限內部人員訪問
    return await supabase_service.get_all_draft_plans()

@router.get("/{draft_id}", response_model=Dict[str, Any], summary="获取单个計畫草稿")
async def get_draft(draft_id: str, supabase_service: SupabaseService = Depends(get_supabase_service), _=Depends(verify_internal_user)):
    # 根據 ID 獲取單個計畫草稿詳情
    draft = await supabase_service.get_draft_plan_by_id(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found.")
    return draft

@router.post("", response_model=Dict[str, Any], status_code=201, summary="创建单个計畫草稿")
async def create_single_draft(req: CreateDraftRequest, supabase_service: SupabaseService = Depends(get_supabase_service), _=Depends(verify_internal_user)):
    # 建立新的計畫草稿，包含名稱、模式、主題和模板信息
    draft = await supabase_service.create_draft_plan(
        name=req.name, mode=req.mode, grant_id=req.grant_id, template_id=req.template_id
    )
    if not draft:
        raise HTTPException(status_code=500, detail="Failed to create draft.")
    return draft

@router.post("/batch_synthetic", status_code=202, summary="异步批量生成 AI 計畫想法")
async def create_batch_synthetic_drafts(
    req: BatchSyntheticRequest,
    request: Request, 
    background_tasks: BackgroundTasks,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
    user_ctx: Dict[str, Any] = Depends(verify_internal_user),
):
    # 非同步批量建立草稿，並逐筆掛入背景生成任務。
    created_draft_ids = []
    for i in range(req.count):
        draft_name = f"AI生成-{int(time.time())}-{i+1}"
        new_draft = await supabase_service.create_draft_plan(
            name=draft_name, mode='synthetic', grant_id=req.grant_id, template_id=req.template_id
        )
        if new_draft:
            draft_id = new_draft['id']
            created_draft_ids.append(draft_id)
            # 將 Request 傳入背景任務，以便取用 app.state（模型註冊表）。
            background_tasks.add_task(
                run_synthetic_idea_generation_task,
                draft_id=draft_id,
                request_for_llm=request,
                supabase_service=supabase_service,
                llm_service=llm_service,
                user_id=user_ctx.get("id", ""),
                dynamic_fields_schema=req.dynamic_fields_schema
            )
    return {"message": f"Started generating ideas for {len(created_draft_ids)} drafts.", "draft_ids": created_draft_ids}

@router.put("/{draft_id}", response_model=Dict[str, Any], summary="更新一个計畫草稿")
async def update_draft(draft_id: str, req: DraftPlanUpdateRequest, supabase_service: SupabaseService = Depends(get_supabase_service), _=Depends(verify_internal_user)):
    # 更新指定計畫草稿的內容，包括名稱、計畫內容、用戶輸入等
    updated_draft = await supabase_service.update_draft_plan(draft_id, req.dict(exclude_unset=True))
    if not updated_draft:
        raise HTTPException(status_code=404, detail="Draft not found.")
    return updated_draft

@router.delete("/{draft_id}", status_code=204, summary="删除一个計畫草稿")
async def delete_draft(draft_id: str, supabase_service: SupabaseService = Depends(get_supabase_service), _=Depends(verify_internal_user)):
    # 刪除指定的計畫草稿記錄
    success = await supabase_service.delete_draft_plan(draft_id)
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found.")
    return