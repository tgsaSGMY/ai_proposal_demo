import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request

from app.services.supabase_service import SupabaseService
from app.services.llm_service import LLMService
from app.models import DynamicFieldSchema
from app.api.dependencies import get_supabase_service, get_llm_service


# 導入重構後的核心邏輯
from app.core.generation_logic import internal_generate_synthetic_input, SyntheticInputRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/draft_plans",
    tags=["Draft_Plans"]
)

# --- Pydantic 模型 ---
class DraftPlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    grant_id: Optional[str] = None
    template_id: Optional[str] = None
    user_input: Optional[Dict[str, Any]] = None
    plan_content: Optional[Dict[str, Any]] = None

class CreateDraftRequest(BaseModel):
    name: str
    mode: str
    grant_id: Optional[str] = None
    template_id: Optional[str] = None

class BatchSyntheticRequest(BaseModel):
    '''批量生成請求'''
    count: int = Field(..., gt=0, le=20) # 限制一次最多生成 20 个
    grant_id: str
    template_id: str
    user_id: str = Field(..., description="發起請求的用戶 ID，用於配額和日誌記錄。")
    dynamic_fields_schema: Optional[List[DynamicFieldSchema]] = Field(
        default=None,
        description="指定批量任務使用的動態欄位標籤清單。",
    )

# --- 後台任务函数 ---
async def run_synthetic_idea_generation_task(
    draft_id: str,
    request_for_llm: Request, # 傳入 Request 對象以訪問 app.state
    supabase_service: SupabaseService, 
    llm_service: LLMService,
    user_id: str,
    dynamic_fields_schema: Optional[List[Dict[str, str]]] = None
):
    """ 
    后台任务：只生成合成的用户输入 (想法)，不生成 plan content。
    """
    logger.info(f"Starting background idea generation for draft_id: {draft_id}")
    await supabase_service.update_draft_plan(draft_id, {"status": "generating_idea"})
    
    try:
        draft = await supabase_service.get_draft_plan_by_id(draft_id)
        if not draft:
            raise ValueError("Draft not found.")

        # 從草稿信息中獲取 grant 和 template 信息
        grant = await supabase_service.get_grant_by_id(draft['grant_id'])
        template = await supabase_service.get_template_by_id(draft['template_id'],draft['grant_id'])
        sections = await supabase_service.get_sections_by_template_id(draft['template_id'],draft['grant_id'])

        if not grant or not template or not sections:
            raise ValueError("Associated grant/template/sections not found for the draft.")

        # 準備调用 internal_generate_synthetic_input 所需的参数
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
        
        # 真正调用 LLM 生成想法
        generated_user_input = await internal_generate_synthetic_input(synthetic_req, request_for_llm, llm_service,supabase_service)

        # 更新数据库，状态为 'completed'，并只存入 user_input
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


# --- API 端点 ---

@router.get("", response_model=List[Dict[str, Any]], summary="获取所有企划草稿")
async def get_all_drafts(supabase_service: SupabaseService = Depends(get_supabase_service)):
    return await llm_service.get_all_draft_plans()

@router.post("", response_model=Dict[str, Any], status_code=201, summary="创建单个企划草稿")
async def create_single_draft(req: CreateDraftRequest, supabase_service: SupabaseService = Depends(get_supabase_service)):
    draft = await supabase_service.create_draft_plan(
        name=req.name, mode=req.mode, grant_id=req.grant_id, template_id=req.template_id
    )
    if not draft:
        raise HTTPException(status_code=500, detail="Failed to create draft.")
    return draft

@router.post("/batch_synthetic", status_code=202, summary="异步批量生成 AI 企划想法")
async def create_batch_synthetic_drafts(
    req: BatchSyntheticRequest,
    request: Request, 
    background_tasks: BackgroundTasks,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
):
    created_draft_ids = []
    for i in range(req.count):
        draft_name = f"AI生成-{int(time.time())}-{i+1}"
        new_draft = await supabase_service.create_draft_plan(
            name=draft_name, mode='synthetic', grant_id=req.grant_id, template_id=req.template_id
        )
        if new_draft:
            draft_id = new_draft['id']
            created_draft_ids.append(draft_id)
            # 将 request 对象传递给后台任务
            background_tasks.add_task(
                run_synthetic_idea_generation_task,
                draft_id=draft_id,
                request_for_llm=request,
                supabase_service=supabase_service,
                llm_service=llm_service,
                user_id=req.user_id,
                dynamic_fields_schema=req.dynamic_fields_schema
            )
    return {"message": f"Started generating ideas for {len(created_draft_ids)} drafts.", "draft_ids": created_draft_ids}

@router.put("/{draft_id}", response_model=Dict[str, Any], summary="更新一个企划草稿")
async def update_draft(draft_id: str, req: DraftPlanUpdateRequest, supabase_service: SupabaseService = Depends(get_supabase_service)):
    updated_draft = await supabase_service.update_draft_plan(draft_id, req.dict(exclude_unset=True))
    if not updated_draft:
        raise HTTPException(status_code=404, detail="Draft not found.")
    return updated_draft

@router.delete("/{draft_id}", status_code=204, summary="删除一个企划草稿")
async def delete_draft(draft_id: str, supabase_service: SupabaseService = Depends(get_supabase_service)):
    success = await supabase_service.delete_draft_plan(draft_id)
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found.")
    return