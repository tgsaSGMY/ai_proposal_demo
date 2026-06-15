# Dependency injection for the demo backend.
# No authentication — every visitor is identified by an opaque demo session
# cookie (UUID, 30-day lifetime). The cookie is minted server-side on first
# request and used as the scoping key everywhere user_id was used in the
# parent platform.

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response

from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService
from app.utils.demo_rate_limiter import DemoRateLimiter
from app.utils.ip_extractor import get_client_ip
from app.config import DEMO_SESSION_EXPIRY_MINUTES

DEMO_SESSION_COOKIE_NAME = "demo_session_id"
DEMO_SESSION_COOKIE_MAX_AGE_SECONDS = DEMO_SESSION_EXPIRY_MINUTES * 60


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


async def get_demo_session_id(
    request: Request,
    response: Response,
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> str:
    """
    Return the visitor's demo session ID, minting and setting the cookie on
    first request or when the existing cookie maps to a row that's been
    claimed or expired. The returned value is the scoping key for every
    read/write against ai_proposal_platform.demo.

    On the mint branch only, enforce a per-IP rate limit so a single source
    can't burn through arbitrary numbers of fresh sessions. A returning
    visitor whose row was claimed is treated as a fresh mint and counts
    against the IP limit.
    """
    existing = _coerce_uuid(request.cookies.get(DEMO_SESSION_COOKIE_NAME))
    if existing:
        # Only reuse the cookie if it still maps to an active row.
        # get_demo_session filters status='active' as of Task 4, so a None
        # response here means the row was claimed, expired, or never existed.
        if await supabase_service.get_demo_session(existing):
            return existing

    ip = get_client_ip(request)
    if ip:
        result = await DemoRateLimiter(supabase_service).check_and_increment(ip)
        if not result.allowed:
            raise HTTPException(
                status_code=429,
                detail={"code": result.reason, "retry_after": result.retry_after},
                headers={"Retry-After": str(result.retry_after)},
            )

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
