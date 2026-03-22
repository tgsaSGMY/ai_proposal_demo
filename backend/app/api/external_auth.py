# 用途：提供外部 OAuth 認證相關的 API，供前台使用者登入與授權。

import hmac
import json
import logging
import secrets
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, Query, Request as FastAPIRequest, status
from fastapi.responses import RedirectResponse, Response

from app.api.dependencies import get_supabase_service
from app.config import (
    EXTERNAL_OAUTH_AUTHORIZE_URL,
    EXTERNAL_OAUTH_CLIENT_ID,
    EXTERNAL_OAUTH_CLIENT_SECRET,
    EXTERNAL_OAUTH_ENABLED,
    EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL,
    EXTERNAL_OAUTH_PROVIDER,
    EXTERNAL_OAUTH_TOKEN_URL,
    EXTERNAL_OAUTH_USERINFO_URL,
)
from app.core.app_jwt import create_app_access_token
from app.services.supabase_service import SupabaseService

router = APIRouter(prefix="/api/external-auth", tags=["ExternalAuth"])
logger = logging.getLogger(__name__)

STATE_COOKIE_NAME = "external_oauth_state"
APP_TOKEN_COOKIE_NAME = "app_access_token"
VIP_PLAN_IDS = {2, 3}


def _require_enabled() -> None:
    # 確保外部 OAuth 功能已啟用；未啟用時直接回 503。
    if not EXTERNAL_OAUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External OAuth is disabled",
        )


def _require_provider_config() -> None:
    # 檢查 OAuth 必要設定是否齊全，避免登入流程進行到一半才失敗。
    missing = []
    if not EXTERNAL_OAUTH_AUTHORIZE_URL:
        missing.append("EXTERNAL_OAUTH_AUTHORIZE_URL")
    if not EXTERNAL_OAUTH_TOKEN_URL:
        missing.append("EXTERNAL_OAUTH_TOKEN_URL")
    if not EXTERNAL_OAUTH_CLIENT_ID:
        missing.append("EXTERNAL_OAUTH_CLIENT_ID")
    if not EXTERNAL_OAUTH_CLIENT_SECRET:
        missing.append("EXTERNAL_OAUTH_CLIENT_SECRET")
    if missing:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Missing external OAuth config: {', '.join(missing)}",
        )


def _build_redirect_uri(request: FastAPIRequest) -> str:
    # 產生後端 callback URL，並強制轉成 https（避免反向代理下被還原成 http）。
    url = request.url_for("external_oauth_callback")
    return str(url.replace(scheme="https"))


def _frontend_callback_url() -> str:
    # 取得前端 callback URL；未設定時退回本機預設值。
    if EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL:
        return EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL
    return "http://localhost:3000/external-auth-callback"


def _is_secure_request(request: FastAPIRequest) -> bool:
    # 判斷是否應設定 secure cookie（同時考慮反向代理 header 與前端 callback 設定）。
    proto = request.headers.get("x-forwarded-proto", "")
    frontend_callback = (_frontend_callback_url() or "").lower()
    callback_requires_https = frontend_callback.startswith("https://")
    return request.url.scheme == "https" or proto == "https" or callback_requires_https


def _json_post_form(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # 以 x-www-form-urlencoded 送出 POST，並解析 JSON 回應。
    body = urlencode(payload).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def _json_get_with_bearer(url: str, token: str) -> Dict[str, Any]:
    # 以 Bearer token 送出 GET，並解析 JSON 回應。
    req = Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def _resolve_role_from_plan(profile_data: Dict[str, Any]) -> str:
    # 根據訂閱方案決定角色：VIP 方案映射為 vip，其餘為 normal。
    subscription = profile_data.get("subscription")
    if not isinstance(subscription, dict):
        return "normal"

    plan = subscription.get("plan")
    if not isinstance(plan, dict):
        return "normal"

    plan_id = plan.get("id")
    try:
        plan_id_int = int(str(plan_id)) if plan_id is not None else -1
    except (TypeError, ValueError):
        return "normal"

    return "vip" if plan_id_int in VIP_PLAN_IDS else "normal"


def _derive_profile(user_info: Dict[str, Any]) -> Dict[str, Any]:
    # 抽取外部 provider 的 user profile，兼容 data 包裹與平面兩種格式。
    logger.info("User info received from OAuth provider: %s", user_info)
    data_field = user_info.get("data")
    profile_data: Dict[str, Any] = data_field if isinstance(data_field, dict) else user_info

    subject = profile_data.get("sub") or profile_data.get("id")
    email = profile_data.get("email")

    if not subject:
        raise HTTPException(status_code=400, detail="Unable to resolve external user subject")

    role = _resolve_role_from_plan(profile_data)

    return {
        "subject": str(subject),
        "email": email,
        "role": role,
    }


@router.get("/redirect", summary="導向外部 OAuth 授權頁")
async def external_oauth_redirect(request: FastAPIRequest):
    # 建立授權連結與 state cookie，並導向 provider 授權頁。
    _require_enabled()
    _require_provider_config()

    state = secrets.token_urlsafe(32)
    redirect_uri = _build_redirect_uri(request)

    query = {
        "client_id": EXTERNAL_OAUTH_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
    }
    redirect_target = f"{EXTERNAL_OAUTH_AUTHORIZE_URL}?{urlencode(query)}"

    response = RedirectResponse(url=redirect_target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie(
        key=STATE_COOKIE_NAME,
        value=state,
        httponly=True,
        secure=_is_secure_request(request),
        samesite="lax",
        max_age=600,
    )
    return response


@router.get("/callback", name="external_oauth_callback", summary="處理外部 OAuth 回呼並登入")
async def external_oauth_callback(
    request: FastAPIRequest,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    # 驗證 callback 參數，完成 token 交換、取得使用者資訊並簽發 app token。
    _require_enabled()
    _require_provider_config()

    if error:
        raise HTTPException(status_code=400, detail=f"OAuth provider returned error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    expected_state = request.cookies.get(STATE_COOKIE_NAME)
    if not expected_state or not state or not hmac.compare_digest(expected_state, state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token_payload = _json_post_form(
        EXTERNAL_OAUTH_TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "client_id": EXTERNAL_OAUTH_CLIENT_ID,
            "client_secret": EXTERNAL_OAUTH_CLIENT_SECRET,
            "redirect_uri": _build_redirect_uri(request),
            "code": code,
        },
    )

    access_token = token_payload.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Token exchange succeeded but access_token is missing")

    if not EXTERNAL_OAUTH_USERINFO_URL:
        raise HTTPException(status_code=500, detail="EXTERNAL_OAUTH_USERINFO_URL is missing in config.")

    user_info = _json_get_with_bearer(EXTERNAL_OAUTH_USERINFO_URL, access_token)
    profile = _derive_profile(user_info)

    canonical_user = await supabase_service.resolve_or_create_user_by_external_identity(
        provider=EXTERNAL_OAUTH_PROVIDER,
        provider_subject=profile["subject"],
        email=profile.get("email"),
        role=profile.get("role"),
    )

    app_token = create_app_access_token(
        subject=canonical_user["id"],
        email=canonical_user.get("email"),
        role=canonical_user.get("role", "normal"),
        provider=EXTERNAL_OAUTH_PROVIDER,
    )

    frontend_url = _frontend_callback_url()
    response = RedirectResponse(
        url=frontend_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    response.set_cookie(
        key=APP_TOKEN_COOKIE_NAME,
        value=app_token,
        httponly=True,
        secure=_is_secure_request(request),
        samesite="lax",
        max_age=86400,
        path="/",
    )
    response.delete_cookie(STATE_COOKIE_NAME)
    return response


@router.post("/logout", summary="登出外部 OAuth 使用者")
async def external_oauth_logout(request: FastAPIRequest):
    # 清除登入相關 cookie，回傳 204 表示登出完成。
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        key=APP_TOKEN_COOKIE_NAME,
        path="/",
        secure=_is_secure_request(request),
        samesite="lax",
        httponly=True,
    )
    response.delete_cookie(
        key=STATE_COOKIE_NAME,
        path="/",
        secure=_is_secure_request(request),
        samesite="lax",
        httponly=True,
    )
    return response


@router.get("/redirect-url", summary="取得需註冊到 OAuth 供應商的回呼網址")
async def get_external_redirect_url(request: FastAPIRequest):
    """回傳後端 callback URL，供外部 OAuth 平台白名單設定使用。"""
    # 此端點主要用於部署檢查或後台設定頁顯示 callback URL。
    _require_enabled()
    return {"redirect_url": _build_redirect_uri(request)}
