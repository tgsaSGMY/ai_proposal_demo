# 集中管理所有 Service 的依賴注入

from fastapi import Request, Depends, HTTPException, Header, status
from app.services.supabase_service import SupabaseService
from app.services.llm_service import LLMService
from typing import Optional, Dict, Any
import time

from app.core.app_jwt import decode_app_access_token

AUTH_CONTEXT_CACHE: Dict[str, Dict[str, Any]] = {}
AUTH_CONTEXT_CACHE_TTL_SECONDS = 20

def get_supabase_service(request: Request) -> SupabaseService:
    # 從應用狀態中獲取 Supabase Service 實例
    return request.app.state.supabase_service

def get_llm_service(request: Request) -> LLMService:
    # 從應用狀態中獲取 LLM Service 實例
    return request.app.state.llm_service

async def get_current_user_id(
    authorization: Optional[str] = Header(None),
    supabase_service: SupabaseService = Depends(get_supabase_service)
) -> str:
    """
    從 Authorization Header 解析 Token 並驗證使用者，回傳 user_id
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    user_ctx = await _resolve_user_context_from_auth(
        authorization=authorization,
        supabase_service=supabase_service,
    )
    return user_ctx["id"]


async def get_current_user_context(
    authorization: Optional[str] = Header(None),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Dict[str, Any]:
    """
    Resolve and return canonical user context from Bearer token.
    """
    return await _resolve_user_context_from_auth(
        authorization=authorization,
        supabase_service=supabase_service,
    )


async def _resolve_user_context_from_auth(
    *,
    authorization: Optional[str],
    supabase_service: SupabaseService,
) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = authorization.split(" ")[1]
    now = time.time()
    cached = AUTH_CONTEXT_CACHE.get(token)
    if cached and cached.get("expires_at", 0) > now:
        return cached["user_ctx"]

    auth_user = None
    try:
        user_response = supabase_service.client.auth.get_user(token)
        auth_user = user_response.user
    except Exception:
        auth_user = None

    if auth_user:
        canonical_user = await supabase_service.resolve_or_create_user_by_supabase_identity(
            auth_user_id=auth_user.id,
            email=auth_user.email,
        )
        user_ctx = {
            "id": canonical_user["id"],
            "email": canonical_user.get("email"),
            "role": canonical_user.get("role", "normal"),
            "auth_user_id": auth_user.id,
            "provider": "supabase",
        }
    else:
        payload = decode_app_access_token(token)
        canonical_user_id = payload.get("sub")
        if not canonical_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid app token subject",
            )
        user_row = await supabase_service.get_user_by_id(canonical_user_id)
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found for app token",
            )
        user_ctx = {
            "id": user_row["id"],
            "email": user_row.get("email") or payload.get("email"),
            "role": user_row.get("role", payload.get("role", "normal")),
            "auth_user_id": None,
            "provider": payload.get("provider", "external"),
        }

    AUTH_CONTEXT_CACHE[token] = {
        "user_ctx": user_ctx,
        "expires_at": now + AUTH_CONTEXT_CACHE_TTL_SECONDS,
    }
    return user_ctx

async def verify_internal_user(
    authorization: Optional[str] = Header(None),
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """
    Dependency:
    1. 解析 Authorization Token 驗證是否登入
    2. 解析 canonical user 並檢查 users.role 是否為 'internal'
    3. 如果通過，回傳 user 物件；不通過則拋出 403 錯誤
    """
    
    user_ctx = await get_current_user_context(
        authorization=authorization,
        supabase_service=supabase_service,
    )

    is_internal = user_ctx.get("role") == "internal"
    if not is_internal:
        # 403 Forbidden: 伺服器理解請求但拒絕執行 (權限不足)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission Denied: This action is restricted to internal staff."
        )

    # 驗證通過，回傳 canonical user context
    return user_ctx