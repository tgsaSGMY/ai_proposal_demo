import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_supabase_service, get_current_user_id
from app.services.supabase_service import SupabaseService
from app.utils.timeline import build_timeline_entries, normalize_versions, parse_iso_timestamp
from app.utils.timeline_pdf import render_timeline_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class ProjectBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    mode: str = Field(..., description="互動/生成模式標記")
    saved_plan: Optional[Any] = None  # 可以是字典或列表（版本数组）
    conversation_history: Optional[Any] = None
    stored_answer: Optional[Dict[str, Any]] = None
    grant_id: Optional[str] = Field(default=None, max_length=255)
    template_id: Optional[str] = Field(default=None, max_length=255)
    plan_type_id: Optional[str] = Field(default=None, max_length=255)

class ProjectUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    mode: Optional[str] = None
    saved_plan: Optional[Any] = None  # 可以是字典或列表（版本数组）
    conversation_history: Optional[Any] = None
    stored_answer: Optional[Dict[str, Any]] = None
    grant_id: Optional[str] = Field(default=None, max_length=255)
    template_id: Optional[str] = Field(default=None, max_length=255)
    plan_type_id: Optional[str] = Field(default=None, max_length=255)


def _resolve_version_index(
    versions: List[Dict[str, Any]],
    version_id: Optional[str],
    version_number: Optional[int],
) -> Optional[int]:
    # 根據版本 ID 或版本編號解析對應的版本索引，支持多種格式（v1、1、ID 字符串）
    if version_number and version_number > 0:
        candidate = version_number - 1
        if 0 <= candidate < len(versions):
            return candidate

    if version_id:
        vid = version_id.strip()
        if vid.lower().startswith("v") and vid[1:].isdigit():
            candidate = int(vid[1:]) - 1
            if 0 <= candidate < len(versions):
                return candidate
        if vid.isdigit():
            candidate = int(vid) - 1
            if 0 <= candidate < len(versions):
                return candidate
        for idx, version in enumerate(versions):
            if str(version.get("id")) == vid or str(version.get("number")) == vid:
                return idx
    return None


def _compute_version_window(
    versions: List[Dict[str, Any]],
    target_index: int,
) -> Tuple[Optional[datetime], Optional[datetime], Dict[str, Any]]:
    # 計算指定版本的時間窗口，用於篩選該版本期間的執行日誌和聊天記錄
    version = versions[target_index]

    def version_timestamp(entry: Dict[str, Any]) -> Optional[datetime]:
        return parse_iso_timestamp(entry.get("timestamp") or entry.get("created_at"))

    prev_ts = version_timestamp(versions[target_index - 1]) if target_index > 0 else None
    next_ts = (
        version_timestamp(versions[target_index + 1])
        if target_index + 1 < len(versions)
        else None
    )
    current_ts = version_timestamp(version)

    start_time = prev_ts
    end_time = current_ts or next_ts

    return start_time, end_time, version


async def _build_timeline_response(
    *,
    project_id: str,
    user_id: str,
    supabase_service: SupabaseService,
    version_id: Optional[str],
    version_number: Optional[int],
):
    # 構建時間軸回應資料，包含指定版本的聊天記錄、執行日誌和時間窗口信息
    record = await supabase_service.get_project_by_id(project_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="Project not found or permission denied")

    versions = normalize_versions(record.get("saved_plan"))
    target_index = _resolve_version_index(versions, version_id, version_number)

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    version_meta: Optional[Dict[str, Any]] = None

    if target_index is not None and 0 <= target_index < len(versions):
        start_time, end_time, version_meta = _compute_version_window(versions, target_index)

    execution_logs = await supabase_service.get_execution_logs(
        project_id=project_id,
        start_time=start_time.isoformat() if start_time else None,
        end_time=end_time.isoformat() if end_time else None,
    )

    raw_history = record.get("conversation_history") or []

    def in_window(ts: Optional[datetime]) -> bool:
        if ts is None:
            return False
        if start_time and ts < start_time:
            return False
        if end_time and ts > end_time:
            return False
        return True

    filtered_history: List[Dict[str, Any]] = []
    for message in raw_history:
        if not isinstance(message, dict):
            continue
        ts = parse_iso_timestamp(
            message.get("timestamp")
            or message.get("created_at")
            or message.get("createdAt")
            or message.get("time")
        )
        if not in_window(ts):
            continue
        filtered_history.append(message)

    entries = build_timeline_entries(
        conversation_history=filtered_history,
        execution_logs=execution_logs,
        start_time=start_time,
        end_time=end_time,
    )

    return {
        "project_id": project_id,
        "version_index": target_index,
        "version": version_meta,
        "time_window": {
            "start": start_time.isoformat() if start_time else None,
            "end": end_time.isoformat() if end_time else None,
        },
        "entries": entries,
        "conversation_history": filtered_history,
    }


@router.get("", response_model=List[Dict[str, Any]], summary="取得使用者的所有專案")
async def list_projects(
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    # 取得當前使用者的所有專案列表
    return await supabase_service.get_projects_by_user(user_id)


@router.get("/{project_id}", response_model=Dict[str, Any], summary="取得單一專案")
async def get_project(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    # 根據專案 ID 取得單一專案詳情，須驗證使用者權限
    record = await supabase_service.get_project_by_id(project_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="Project not found or permission denied")
    return record


@router.post("", response_model=Dict[str, Any], status_code=201, summary="新增專案記錄")
async def create_project(
    payload: ProjectBase,
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    # 建立新的專案記錄，自動關聯當前使用者 ID
    data = payload.dict(exclude_none=True)
    data["user_id"] = user_id
    record = await supabase_service.create_project_record(data)
    if not record:
        raise HTTPException(status_code=500, detail="Failed to create project record")
    return record


@router.put("/{project_id}", response_model=Dict[str, Any], summary="更新專案")
async def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    # 更新指定專案的內容，須驗證使用者為專案擁有者
    record = await supabase_service.update_project_record(project_id, user_id, payload.dict(exclude_none=True))
    if not record:
        raise HTTPException(status_code=404, detail="Project not found or permission denied")
    return record


@router.delete("/{project_id}", status_code=204, summary="刪除專案")
async def delete_project(
    project_id: str,
    # 注入剛剛寫好的 get_current_user_id 獲取 user_id
    user_id: str = Depends(get_current_user_id), 
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    # 刪除指定專案，須驗證使用者為專案擁有者
    # 將 project_id 和 user_id 一起傳給 Service
    success = await supabase_service.delete_project_record(project_id, user_id)
    
    if not success:
        # 如果刪除失敗（可能是找不到 ID，或是 ID 存在但 user_id 不對）
        # 為了安全，通常統一回傳 404，不讓駭客知道該 ID 是否存在
        raise HTTPException(status_code=404, detail="Project not found or permission denied")
    return None


@router.get("/{project_id}/timeline", summary="取得專案的 AI 執行時間軸")
async def get_project_timeline(
    project_id: str,
    version_id: Optional[str] = Query(None, description="版本 ID，例如 v2"),
    version_number: Optional[int] = Query(None, ge=1, description="版本編號（1 起算）"),
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    # 取得指定專案和版本的 AI 執行時間軸，包括聊天記錄和執行日誌
    timeline_data = await _build_timeline_response(
        project_id=project_id,
        user_id=user_id,
        supabase_service=supabase_service,
        version_id=version_id,
        version_number=version_number,
    )
    return timeline_data


@router.get("/{project_id}/timeline/pdf", summary="下載 AI 執行時間軸 PDF")
async def download_project_timeline_pdf(
    project_id: str,
    version_id: Optional[str] = Query(None, description="版本 ID，例如 v2"),
    version_number: Optional[int] = Query(None, ge=1, description="版本編號（1 起算）"),
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    # 將指定版本的時間軸資料導出為 PDF 格式並返回下載
    timeline_data = await _build_timeline_response(
        project_id=project_id,
        user_id=user_id,
        supabase_service=supabase_service,
        version_id=version_id,
        version_number=version_number,
    )

    title = (
        timeline_data.get("version", {}).get("title")
        or f"Project {project_id} Timeline"
    )
    pdf_buffer = render_timeline_pdf(
        title,
        timeline_data.get("entries", []),
        timeline_data.get("conversation_history"),
    )

    filename_parts = [f"timeline-{project_id}"]
    if version_number:
        filename_parts.append(f"v{version_number}")
    elif version_id:
        filename_parts.append(version_id)
    filename = "-".join(filename_parts) + ".pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )
