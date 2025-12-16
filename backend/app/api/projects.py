import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.dependencies import get_supabase_service
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class ProjectBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    mode: str = Field(..., description="互動/生成模式標記")
    saved_plan: Optional[Dict[str, Any]] = None
    conversation_history: Optional[Any] = None
    stored_answer: Optional[Dict[str, Any]] = None
    grant_id: Optional[str] = Field(default=None, max_length=255)
    template_id: Optional[str] = Field(default=None, max_length=255)
    plan_type_id: Optional[str] = Field(default=None, max_length=255)
    plan_metadata: Optional[Dict[str, Any]] = None


class ProjectCreateRequest(ProjectBase):
    user_id: str = Field(..., description="Supabase 使用者 ID")


class ProjectUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    mode: Optional[str] = None
    saved_plan: Optional[Dict[str, Any]] = None
    conversation_history: Optional[Any] = None
    stored_answer: Optional[Dict[str, Any]] = None
    grant_id: Optional[str] = Field(default=None, max_length=255)
    template_id: Optional[str] = Field(default=None, max_length=255)
    plan_type_id: Optional[str] = Field(default=None, max_length=255)
    plan_metadata: Optional[Dict[str, Any]] = None


@router.get("", response_model=List[Dict[str, Any]], summary="取得使用者的所有專案")
async def list_projects(
    user_id: str = Query(..., description="Supabase 使用者 ID"),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    return await supabase_service.get_projects_by_user(user_id)


@router.get("/{project_id}", response_model=Dict[str, Any], summary="取得單一專案")
async def get_project(
    project_id: str,
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    record = await supabase_service.get_project_by_id(project_id)
    if not record:
        raise HTTPException(status_code=404, detail="Project not found")
    return record


@router.post("", response_model=Dict[str, Any], status_code=201, summary="新增專案記錄")
async def create_project(
    payload: ProjectCreateRequest,
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    record = await supabase_service.create_project_record(payload.dict(exclude_none=True))
    if not record:
        raise HTTPException(status_code=500, detail="Failed to create project record")
    return record


@router.put("/{project_id}", response_model=Dict[str, Any], summary="更新專案")
async def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    record = await supabase_service.update_project_record(project_id, payload.dict(exclude_none=True))
    if not record:
        raise HTTPException(status_code=404, detail="Project not found")
    return record


@router.delete("/{project_id}", status_code=204, summary="刪除專案")
async def delete_project(
    project_id: str,
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    success = await supabase_service.delete_project_record(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return None
