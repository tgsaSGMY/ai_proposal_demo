# Demo session CRUD.
#
# Replaces the parent platform's per-user project router. The demo only has
# one "project" per visitor — the row in ai_proposal_platform.demo keyed by
# the demo_session_id cookie.

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import get_demo_session_id, get_supabase_service
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["Demo"])


class DemoSessionUpdate(BaseModel):
    grant_id: Optional[str] = Field(default=None, max_length=255)
    template_id: Optional[str] = Field(default=None, max_length=255)
    saved_plan: Optional[Any] = None
    stored_answer: Optional[Dict[str, Any]] = None
    conversation_history: Optional[Any] = None


@router.get("", summary="Get the current visitor's demo session")
async def get_demo_session(
    session_id: str = Depends(get_demo_session_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Dict[str, Any]:
    """Return the visitor's row from `ai_proposal_platform.demo`. Creates an
    empty row on first request so the frontend always sees a session object."""
    row = await supabase_service.ensure_demo_session(session_id)
    return row or {"session_id": session_id}


@router.put("", summary="Update the demo session payload")
async def update_demo_session(
    payload: DemoSessionUpdate,
    session_id: str = Depends(get_demo_session_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Dict[str, Any]:
    data = payload.dict(exclude_none=True)
    if not data:
        return await supabase_service.get_demo_session(session_id) or {"session_id": session_id}
    return await supabase_service.update_demo_session(session_id, data) or {"session_id": session_id}


@router.delete("", summary="Reset the current demo session")
async def reset_demo_session(
    session_id: str = Depends(get_demo_session_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Dict[str, str]:
    """Wipe the row so a fresh demo starts. The deleted row is gone, so the
    next GET will see a missing row and mint a new session ID (cookie rotated)."""
    await supabase_service.delete_demo_session(session_id)
    return {"status": "reset", "session_id": session_id}
