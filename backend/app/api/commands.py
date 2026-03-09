import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user_id, get_supabase_service
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/commands", tags=["Commands"])


class CommandCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    is_open: bool = True
    is_company: bool = False


class CommandUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, min_length=1)
    is_open: Optional[bool] = None
    is_company: Optional[bool] = None


@router.get("", response_model=List[Dict[str, Any]], summary="取得目前使用者指令")
async def list_commands(
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    return await supabase_service.list_user_commands(user_id)


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED, summary="建立指令")
async def create_command(
    payload: CommandCreateRequest,
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    now = datetime.now(timezone.utc).isoformat()
    record = await supabase_service.create_user_command(
        user_id=user_id,
        data={
            "title": payload.title.strip(),
            "description": payload.description.strip(),
            "is_open": payload.is_open,
            "is_company": payload.is_company,
            "last_updated": now,
        },
    )
    if not record:
        raise HTTPException(status_code=500, detail="Failed to create command")
    return record


@router.put("/{command_id}", response_model=Dict[str, Any], summary="更新指令")
async def update_command(
    command_id: str,
    payload: CommandUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    data = payload.dict(exclude_none=True)
    if "title" in data:
        data["title"] = data["title"].strip()
    if "description" in data:
        data["description"] = data["description"].strip()

    if not data:
        raise HTTPException(status_code=400, detail="No fields provided")

    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    record = await supabase_service.update_user_command(
        command_id=command_id,
        user_id=user_id,
        data=data,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Command not found or permission denied")
    return record


@router.delete("/{command_id}", status_code=status.HTTP_200_OK, summary="刪除指令")
async def delete_command(
    command_id: str,
    user_id: str = Depends(get_current_user_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    ok = await supabase_service.delete_user_command(command_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Command not found or permission denied")
    return {"message": "Command deleted"}
