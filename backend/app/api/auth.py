from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, Request

from app.api.dependencies import (
    get_current_user_context,
    get_supabase_service,
    _resolve_user_context_from_auth,
)
from app.services.supabase_service import SupabaseService

# 認證相關 API 路由：提供目前登入者資訊與輕量驗證狀態檢查。
router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/me")
async def get_me(user_ctx: Dict[str, Any] = Depends(get_current_user_context)):
    """回傳由 Bearer Token 解析出的標準化使用者資訊。"""
    return user_ctx


@router.get("/status")
async def get_auth_status(
    request: Request,
    authorization: Optional[str] = Header(None),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """
    輕量認證探針端點，固定回傳 200。
    主要給前端登入頁 middleware 使用，避免產生大量 401 噪音。
    """
    try:
        # 成功解析 token 時僅回傳前端需要的最小身份資訊。
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
        # 探針 API 設計為不拋認證錯誤，統一回傳未登入狀態。
        return {
            "authenticated": False,
            "provider": None,
            "role": None,
            "id": None,
        }
