# 連接數據庫，CRUD數據

import json
import logging
from typing import List, Optional, Dict, Any
import httpx

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from app.models import SaveDatasetRequest, DatasetEntry, DatasetEntry
from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService
from app.utils.extract_json import extract_json_block
from .dependencies import get_supabase_service, verify_internal_user, get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/datasets",
    tags=["Datasets"]
)


@router.post("/sensitive-terms/suggest", summary="AI 建議敏感詞")
async def suggest_sensitive_terms(
    req: Dict[str, Any],
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    _=Depends(verify_internal_user),
):
    """根據 prompt 與 final_answer 建議可脫敏的詞，回傳去重後的詞列表。"""
    prompt_text = str(req.get("prompt") or "").strip()
    final_answer = req.get("final_answer") or {}
    existing_terms = req.get("existing_terms") or []

    if not isinstance(final_answer, dict):
        raise HTTPException(status_code=400, detail="final_answer must be an object")

    model_info = request.app.state.model_registry.get("gpt-5-mini")
    if not model_info:
        model_info = next(
            (
                m
                for m in request.app.state.model_registry.values()
                if m.get("provider") in {"openai", "gemini"}
            ),
            None,
        )

    if not model_info:
        raise HTTPException(status_code=500, detail="No available model for sensitive-term suggestion")

    final_answer_str = json.dumps(final_answer, ensure_ascii=False)
    existing_terms_str = json.dumps(existing_terms, ensure_ascii=False)

    instruction = (
        "你是一個資料脫敏助手。請找出下列內容中可能屬於敏感資訊、"
        "且適合被替換成 OOO 的短詞，重點包含人名、公司名、地址、電話、email、帳號、網址、統編、身分證字號、具體數字、公司策略。\n"
        "請只輸出 JSON，格式必須是：{\"terms\": [\"詞1\", \"詞2\"]}。\n"
        "規則：\n"
        "1) 只回傳具體詞彙，不要回傳描述句。\n"
        "2) 不要回傳單字元或純符號。\n"
        "3) 不要重複。\n"
        "4) 最多 20 個，可少於20個。\n"
        "5) 已經使用 OOO 去除敏感資訊的詞匯不再標記為敏感詞。那些常用的詞語也不需要被標記。\n"
        f"已存在詞清單（避免重複）：{existing_terms_str}\n\n"
        f"輸出 JSON：{final_answer_str}"
    )

    async with httpx.AsyncClient(timeout=120.0) as client:
        raw_output, llm_error, _ = await llm_service.call_external_api(
            session=client,
            model_info=model_info,
            messages=[{"role": "user", "content": instruction}],
            is_json_output=True,
            enable_grounding=False,
        )

    if llm_error:
        raise HTTPException(status_code=500, detail=llm_error.get("error", "suggestion failed"))

    parsed_json, parse_error = extract_json_block(raw_output or "", "sensitive_terms")
    if parse_error:
        raise HTTPException(status_code=500, detail=parse_error.get("error", "invalid suggestion format"))

    terms = parsed_json.get("terms") if isinstance(parsed_json, dict) else []
    if not isinstance(terms, list):
        terms = []

    deduped: List[str] = []
    seen = set()
    for item in terms:
        value = str(item or "").strip()
        if len(value) < 2:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(value)

    return {"terms": deduped[:20]}

@router.post("", status_code=status.HTTP_202_ACCEPTED, summary="保存數據集條目")
async def save_dataset_entries(
    req: SaveDatasetRequest,
    background_tasks: BackgroundTasks,
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """
    異步保存數據集條目到 Supabase。
    此操作立即返回，並在後台執行實際的資料庫寫入。
    （保存至最終數據集）
    """
    
    async def background_task(entries: List[DatasetEntry]):
        logger.info(f"Background task started: saving {len(entries)} dataset entries.")
        for entry in entries:
            try:
                await supabase_service.add_dataset_entry(
                    source_type=entry.source_type,
                    grant_id=entry.grant_id,
                    template_id=entry.template_id,
                    section_id=entry.section_id,
                    prompt=entry.prompt,
                    final_answer=entry.final_answer,
                    rejected_answer=entry.rejected_answer
                )
            except Exception as e:
                logger.error(f"Failed to process entry for section {entry.section_id}: {e}", exc_info=True)
        logger.info("Background dataset saving task finished.")

    background_tasks.add_task(background_task, req.entries)
    return {"message": "Dataset saving process has been initiated in the background."}

@router.get("", summary="獲取所有數據集條目", response_model=List[Dict[str, Any]])
async def get_all_datasets_endpoint(
    grant_id: Optional[str] = None,
    template_id: Optional[str] = None,
    section_id: Optional[str] = None,
    source_type: Optional[str] = None,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _=Depends(verify_internal_user),
):
    """從 Supabase 獲取數據集記錄，支持按 grant, template, section, source_type 進行篩選。"""
    try:
        datasets = await supabase_service.get_all_datasets(
            grant_id=grant_id,
            template_id=template_id,
            section_id=section_id,
            source_type=source_type,
        )
        return datasets
    except Exception as e:
        logger.error(f"Failed to fetch datasets with filters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{dataset_id}", status_code=status.HTTP_200_OK)
async def update_dataset_entry(
    dataset_id: int,
    req: DatasetEntry,   
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _=Depends(verify_internal_user),
):
    """
    更新 Supabase 中的一筆數據集條目，並重新計算向量嵌入。
    """
    try:
        # 更新 Supabase
        updated_entry = await supabase_service.update_dataset_by_id(
            dataset_id,
            {
                "source_type": req.source_type,
                "grant_id": req.grant_id,
                "template_id": req.template_id,
                "section_id": req.section_id,
                "prompt": req.prompt,
                "final_answer": req.final_answer,
            },
        )

        if not updated_entry:
            raise HTTPException(status_code=404, detail="Dataset not found in Supabase")

        return {"message": f"Dataset {dataset_id} updated successfully."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{dataset_id}", status_code=status.HTTP_200_OK, summary="刪除一個數據集條目")
async def delete_dataset_entry(
    dataset_id: int, 
    supabase: SupabaseService = Depends(get_supabase_service),
    _=Depends(verify_internal_user),
):
    """刪除 Supabase 中的數據集紀錄。"""
    try:
        deleted_from_supabase = await supabase.delete_dataset_by_id(dataset_id)
        if not deleted_from_supabase:
            logger.warning(f"Dataset ID {dataset_id} not found in Supabase, deletion skipped.")

        logger.info(f"Deleted dataset ID {dataset_id} from Supabase.")
        return {"message": "Dataset entry deleted successfully."}
    except Exception as e:
        logger.error(f"Failed to delete dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))