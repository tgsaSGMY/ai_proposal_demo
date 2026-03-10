import hmac
import json
import secrets
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, Query, Request as FastAPIRequest, status
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_supabase_service
from app.config import (
    EXTERNAL_OAUTH_AUTHORIZE_URL,
    EXTERNAL_OAUTH_CLIENT_ID,
    EXTERNAL_OAUTH_CLIENT_SECRET,
    EXTERNAL_OAUTH_ENABLED,
    EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL,
    EXTERNAL_OAUTH_PROVIDER,
    EXTERNAL_OAUTH_SCOPE,
    EXTERNAL_OAUTH_TOKEN_URL,
    EXTERNAL_OAUTH_USERINFO_URL,
)
from app.core.app_jwt import create_app_access_token
from app.services.supabase_service import SupabaseService

router = APIRouter(prefix="/api/external-auth", tags=["ExternalAuth"])

STATE_COOKIE_NAME = "external_oauth_state"


def _require_enabled() -> None:
    if not EXTERNAL_OAUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External OAuth is disabled",
        )


def _require_provider_config() -> None:
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
    return str(request.url_for("external_oauth_callback"))


def _frontend_callback_url() -> str:
    if EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL:
        return EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL
    return "http://localhost:3000/external-auth-callback"


def _json_post_form(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
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
    req = Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def _derive_profile(user_info: Dict[str, Any]) -> Dict[str, Any]:
    # 對應你截圖的格式，如果有 'data' 欄位，就拿裡面那一層；否則保持原來的那層
    profile_data = user_info.get("data") if isinstance(user_info.get("data"), dict) else user_info

    subject = profile_data.get("sub") or profile_data.get("id")
    email = profile_data.get("email")

    if not subject:
        raise HTTPException(status_code=400, detail="Unable to resolve external user subject")

    role_raw = profile_data.get("role") or "normal"
    role = role_raw if role_raw in {"normal", "internal", "vip"} else "normal"

    return {
        "subject": str(subject),
        "email": email,
        "role": role,
    }


@router.get("/redirect")
async def external_oauth_redirect(request: FastAPIRequest):
    _require_enabled()
    _require_provider_config()

    state = secrets.token_urlsafe(32)
    redirect_uri = _build_redirect_uri(request)

    query = {
        "client_id": EXTERNAL_OAUTH_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": EXTERNAL_OAUTH_SCOPE,
        "state": state,
    }
    redirect_target = f"{EXTERNAL_OAUTH_AUTHORIZE_URL}?{urlencode(query)}"

    response = RedirectResponse(url=redirect_target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie(
        key=STATE_COOKIE_NAME,
        value=state,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=600,
    )
    return response


@router.get("/callback", name="external_oauth_callback")
async def external_oauth_callback(
    request: FastAPIRequest,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
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
    redirect_query = urlencode(
        {
            "token": app_token,
            "provider": EXTERNAL_OAUTH_PROVIDER,
        }
    )

    response = RedirectResponse(
        url=f"{frontend_url}?{redirect_query}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    response.delete_cookie(STATE_COOKIE_NAME)
    return response


@router.get("/redirect-url")
async def get_external_redirect_url(request: FastAPIRequest):
    """Expose backend callback URL that must be registered on the OAuth provider."""
    _require_enabled()
    return {"redirect_url": _build_redirect_uri(request)}
