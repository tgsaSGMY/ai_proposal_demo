# Demo session CRUD.
#
# Replaces the parent platform's per-user project router. The demo only has
# one "project" per visitor — the row in ai_proposal_platform.demo keyed by
# the demo_session_id cookie.

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import get_demo_session_id, get_supabase_service
from app.services.supabase_service import SupabaseService
from app.config import (
    DEMO_GRANT_ID,
    DEMO_TEMPLATE_ID,
    DEMO_INTERACTION_LIMIT,
    DEMO_MAX_GENERATIONS_PER_SESSION,
    DEMO_REGISTER_REDIRECT_URL,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["Demo"])


async def _force_session_template(
    session_id: str,
    supabase_service: SupabaseService,
    session_row: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """When DEMO_GRANT_ID / DEMO_TEMPLATE_ID are configured, overwrite the
    session row so it always matches the .env values. Returns the updated row.
    """
    if not DEMO_GRANT_ID or not DEMO_TEMPLATE_ID:
        return session_row
    if not session_row:
        return session_row
    if (
        session_row.get("grant_id") == DEMO_GRANT_ID
        and session_row.get("template_id") == DEMO_TEMPLATE_ID
    ):
        return session_row
    return await supabase_service.update_demo_session(
        session_id,
        {"grant_id": DEMO_GRANT_ID, "template_id": DEMO_TEMPLATE_ID},
    )


class DemoSessionUpdate(BaseModel):
    grant_id: Optional[str] = Field(default=None, max_length=255)
    template_id: Optional[str] = Field(default=None, max_length=255)
    saved_plan: Optional[Any] = None
    stored_answer: Optional[Dict[str, Any]] = None
    conversation_history: Optional[Any] = None
    has_generated_docx: Optional[bool] = None
    download_count: Optional[int] = None


@router.get("", summary="Get the current visitor's demo session")
async def get_demo_session(
    session_id: str = Depends(get_demo_session_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Dict[str, Any]:
    """Return the visitor's row from `ai_proposal_platform.demo`. Creates an
    empty row on first request so the frontend always sees a session object.
    If DEMO_GRANT_ID / DEMO_TEMPLATE_ID are configured, the session row is
    patched to match them so old sessions migrate automatically."""
    row = await supabase_service.ensure_demo_session(session_id)
    row = await _force_session_template(session_id, supabase_service, row)
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


@router.get("/status", summary="Get demo status and configured template")
async def get_demo_status(
    session_id: str = Depends(get_demo_session_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Dict[str, Any]:
    """Return the currently configured demo template IDs and the visitor's
    session usage counters. The frontend uses the returned grant_id / template_id
    to select the exact template from the catalog — no fallback is allowed.
    If DEMO_GRANT_ID / DEMO_TEMPLATE_ID are configured, the session row is
    patched to match them so old sessions migrate automatically."""
    session = await supabase_service.get_demo_session(session_id)
    session = await _force_session_template(session_id, supabase_service, session)
    interaction_count = session.get("interaction_count", 0) if session else 0
    chat_limit_reached = interaction_count >= DEMO_INTERACTION_LIMIT
    has_generated_docx = session.get("has_generated_docx", False) if session else False
    generation_limit_reached = has_generated_docx
    download_count = session.get("download_count", 0) if session else 0
    download_limit_reached = download_count >= 1  # hard-coded 1 download per session
    all_limits_reached = chat_limit_reached and generation_limit_reached and download_limit_reached

    return {
        "grant_id": DEMO_GRANT_ID or None,
        "template_id": DEMO_TEMPLATE_ID or None,
        "interaction_limit": DEMO_INTERACTION_LIMIT,
        "interaction_count": interaction_count,
        "limit_reached": chat_limit_reached,
        "chat_limit_reached": chat_limit_reached,
        "generation_limit_reached": generation_limit_reached,
        "download_limit_reached": download_limit_reached,
        "all_limits_reached": all_limits_reached,
        "has_generated_docx": has_generated_docx,
        "download_count": download_count,
        "register_url": DEMO_REGISTER_REDIRECT_URL,
    }


@router.get("/dynamic-fields", summary="Get dynamic questions for a template")
async def get_dynamic_fields(
    grant_id: str,
    template_id: str,
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Dict[str, Any]:
    """Return dynamic_sections + dynamic_fields for the given template.

    The frontend uses this to build the exact question list that matches
    the full platform's _builder configuration. If no dynamic fields
    exist for this template, returns an empty sections array so the
    frontend falls back to the static sections.json_schema path."""
    fields = await supabase_service.get_dynamic_fields_for_template(
        template_id, grant_id
    )
    return {
        "grant_id": grant_id,
        "template_id": template_id,
        "sections": fields,
        "count": sum(len(s.get("fields", [])) for s in fields),
    }


@router.post("/download", summary="Increment the demo session download count")
async def increment_download_count(
    session_id: str = Depends(get_demo_session_id),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Dict[str, Any]:
    """Atomically bump download_count. Returns 429 if the session has already
    reached the per-session download limit (hard-coded to 1)."""
    session = await supabase_service.get_demo_session(session_id)
    current = session.get("download_count", 0) if session else 0
    if current >= 1:
        raise HTTPException(
            status_code=429,
            detail="下載次數已達上限，免費註冊即可繼續使用。",
        )
    new_count = await supabase_service.increment_demo_download_count(session_id)
    return {"download_count": new_count}
