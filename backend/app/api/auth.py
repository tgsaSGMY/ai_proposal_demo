from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, Request

from app.api.dependencies import (
    get_current_user_context,
    get_supabase_service,
    _resolve_user_context_from_auth,
)
from app.services.supabase_service import SupabaseService

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/me")
async def get_me(user_ctx: Dict[str, Any] = Depends(get_current_user_context)):
    """Return canonical user profile resolved from the current bearer token."""
    return user_ctx


@router.get("/status")
async def get_auth_status(
    request: Request,
    authorization: Optional[str] = Header(None),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """
    Lightweight auth probe endpoint that always returns 200.
    Used by login-page middleware to avoid noisy 401 logs.
    """
    try:
        user_ctx = await _resolve_user_context_from_auth(
            request=request,
            authorization=authorization,
            supabase_service=supabase_service,
        )
        return {
            "authenticated": True,
            "provider": user_ctx.get("provider"),
            "role": user_ctx.get("role"),
            "id": user_ctx.get("id"),
        }
    except Exception:
        return {
            "authenticated": False,
            "provider": None,
            "role": None,
            "id": None,
        }
