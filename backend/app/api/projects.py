import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import get_supabase_service, get_current_user_id
from app.services.supabase_service import SupabaseService

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
    plan_metadata: Optional[Dict[str, Any]] = None





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
    plan_metadata: Optional[Dict[str, Any]] = None


@router.get("", response_model=List[Dict[str, Any]], summary="取得使用者的所有專案")
async def list_projects(
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    return await supabase_service.get_projects_by_user(user_id)


@router.get("/{project_id}", response_model=Dict[str, Any], summary="取得單一專案")
async def get_project(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
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
    # 將 project_id 和 user_id 一起傳給 Service
    success = await supabase_service.delete_project_record(project_id, user_id)
    
    if not success:
        # 如果刪除失敗（可能是找不到 ID，或是 ID 存在但 user_id 不對）
        # 為了安全，通常統一回傳 404，不讓駭客知道該 ID 是否存在
        raise HTTPException(status_code=404, detail="Project not found or permission denied")
    return None
