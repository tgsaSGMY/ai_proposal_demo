# Dependency injection for the demo backend.
# No authentication — every visitor is identified by an opaque demo session
# cookie (UUID, 30-day lifetime). The cookie is minted server-side on first
# request and used as the scoping key everywhere user_id was used in the
# parent platform.

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Request, Response

from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService

DEMO_SESSION_COOKIE_NAME = "demo_session_id"
DEMO_SESSION_COOKIE_MAX_AGE_SECONDS = 30 * 24 * 60 * 60  # 30 days, matches demo.expires_at


def get_supabase_service(request: Request) -> SupabaseService:
    return request.app.state.supabase_service


def get_llm_service(request: Request) -> LLMService:
    return request.app.state.llm_service


def _coerce_uuid(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError):
        return None


async def get_demo_session_id(request: Request, response: Response) -> str:
    """
    Return the visitor's demo session ID, minting and setting the cookie on
    first request. The returned value is the scoping key for every read/write
    against ai_proposal_platform.demo.
    """
    existing = _coerce_uuid(request.cookies.get(DEMO_SESSION_COOKIE_NAME))
    if existing:
        return existing

    new_id = str(uuid.uuid4())
    response.set_cookie(
        key=DEMO_SESSION_COOKIE_NAME,
        value=new_id,
        max_age=DEMO_SESSION_COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False,  # flip to True once the demo is served over HTTPS only
        path="/",
    )
    return new_id
