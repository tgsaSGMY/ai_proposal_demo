# 集中管理所有 Service 的依賴注入

from fastapi import Request, Depends, HTTPException, Header, status
from app.services.supabase_service import SupabaseService
from app.services.llm_service import LLMService
from typing import Optional, Dict, Any
import time

from app.core.app_jwt import decode_app_access_token
from app.config import EXTERNAL_OAUTH_PROVIDER

AUTH_CONTEXT_CACHE: Dict[str, Dict[str, Any]] = {}
AUTH_CONTEXT_CACHE_TTL_SECONDS = 20
APP_TOKEN_COOKIE_NAME = "app_access_token"

def get_supabase_service(request: Request) -> SupabaseService:
    # 從應用狀態中獲取 Supabase Service 實例
    return request.app.state.supabase_service

def get_llm_service(request: Request) -> LLMService:
    # 從應用狀態中獲取 LLM Service 實例
    return request.app.state.llm_service

async def get_current_user_id(
    request: Request,
    authorization: Optional[str] = Header(None),
    supabase_service: SupabaseService = Depends(get_supabase_service)
) -> str:
    """
    從 Authorization Header 解析 Token 並驗證使用者，回傳 user_id
    """
    user_ctx = await _resolve_user_context_from_auth(
        request=request,
        authorization=authorization,
        supabase_service=supabase_service,
    )
    return user_ctx["id"]


async def get_current_user_context(
    request: Request,
    authorization: Optional[str] = Header(None),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> Dict[str, Any]:
    """
    Resolve and return canonical user context from Bearer token.
    """
    return await _resolve_user_context_from_auth(
        request=request,
        authorization=authorization,
        supabase_service=supabase_service,
    )


async def _resolve_user_context_from_auth(
    *,
    request: Request,
    authorization: Optional[str],
    supabase_service: SupabaseService,
) -> Dict[str, Any]:
    header_token: Optional[str] = None
    if authorization and authorization.startswith("Bearer "):
        candidate = authorization.split(" ")[1].strip()
        if candidate and candidate.lower() not in {"null", "undefined"}:
            header_token = candidate

    cookie_token = request.cookies.get(APP_TOKEN_COOKIE_NAME)

    candidate_tokens = [token for token in [header_token, cookie_token] if token]

    if not candidate_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token in Authorization header or app_access_token cookie"
        )

    last_error: Optional[Exception] = None
    for token in candidate_tokens:
        now = time.time()
        cached = AUTH_CONTEXT_CACHE.get(token)
        if cached and cached.get("expires_at", 0) > now:
            return cached["user_ctx"]

        try:
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
                    "provider": payload.get("provider", EXTERNAL_OAUTH_PROVIDER),
                }

            AUTH_CONTEXT_CACHE[token] = {
                "user_ctx": user_ctx,
                "expires_at": now + AUTH_CONTEXT_CACHE_TTL_SECONDS,
            }
            return user_ctx
        except Exception as exc:
            last_error = exc
            continue

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
    ) from last_error

async def verify_internal_user(
    request: Request,
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
        request=request,
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