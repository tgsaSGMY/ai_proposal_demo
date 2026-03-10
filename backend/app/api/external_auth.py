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
    # 取得網址後，強制將 scheme 轉換為 https (避免 Nginx 反向代理導致變回 http)
    url = request.url_for("external_oauth_callback")
    return str(url.replace(scheme="https"))


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

# import hmac
# import json
# import secrets
# from typing import Any, Dict, Optional
# from urllib.parse import urlencode
# from urllib.request import Request, urlopen

# import jwt
# from fastapi import APIRouter, Depends, HTTPException, Query, Request as FastAPIRequest, status
# from fastapi.responses import RedirectResponse

# from app.api.dependencies import get_supabase_service
# from app.config import (
#     EXTERNAL_OAUTH_AUDIENCE,
#     EXTERNAL_OAUTH_AUTHORIZE_URL,
#     EXTERNAL_OAUTH_CLIENT_ID,
#     EXTERNAL_OAUTH_CLIENT_SECRET,
#     EXTERNAL_OAUTH_ENABLED,
#     EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL,
#     EXTERNAL_OAUTH_ISSUER,
#     EXTERNAL_OAUTH_PEM_PUBLIC_KEY,
#     EXTERNAL_OAUTH_PROVIDER,
#     EXTERNAL_OAUTH_REDIRECT_URI,
#     EXTERNAL_OAUTH_SCOPE,
#     EXTERNAL_OAUTH_TOKEN_URL,
#     EXTERNAL_OAUTH_USERINFO_URL,
# )
# from app.core.app_jwt import create_app_access_token
# from app.services.supabase_service import SupabaseService

# router = APIRouter(prefix="/api/external-auth", tags=["ExternalAuth"])

# STATE_COOKIE_NAME = "external_oauth_state"


# def _require_enabled() -> None:
#     if not EXTERNAL_OAUTH_ENABLED:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="External OAuth is disabled",
#         )


# def _require_provider_config() -> None:
#     missing = []
#     if not EXTERNAL_OAUTH_AUTHORIZE_URL:
#         missing.append("EXTERNAL_OAUTH_AUTHORIZE_URL")
#     if not EXTERNAL_OAUTH_TOKEN_URL:
#         missing.append("EXTERNAL_OAUTH_TOKEN_URL")
#     if not EXTERNAL_OAUTH_CLIENT_ID:
#         missing.append("EXTERNAL_OAUTH_CLIENT_ID")
#     if not EXTERNAL_OAUTH_CLIENT_SECRET:
#         missing.append("EXTERNAL_OAUTH_CLIENT_SECRET")
#     if missing:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Missing external OAuth config: {', '.join(missing)}",
#         )


# def _normalize_pem(pem: str) -> str:
#     return pem.replace("\\n", "\n").strip()


# def _build_redirect_uri(request: FastAPIRequest) -> str:
#     if EXTERNAL_OAUTH_REDIRECT_URI:
#         return EXTERNAL_OAUTH_REDIRECT_URI
#     return str(request.url_for("external_oauth_callback"))


# def _frontend_callback_url() -> str:
#     if EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL:
#         return EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL
#     return "http://localhost:3000/external-auth-callback"


# def _json_post_form(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
#     body = urlencode(payload).encode("utf-8")
#     req = Request(
#         url,
#         data=body,
#         headers={"Content-Type": "application/x-www-form-urlencoded"},
#         method="POST",
#     )
#     with urlopen(req, timeout=15) as resp:
#         raw = resp.read().decode("utf-8")
#         return json.loads(raw)


# def _json_get_with_bearer(url: str, token: str) -> Dict[str, Any]:
#     req = Request(
#         url,
#         headers={"Authorization": f"Bearer {token}"},
#         method="GET",
#     )
#     with urlopen(req, timeout=15) as resp:
#         raw = resp.read().decode("utf-8")
#         return json.loads(raw)


# def _verify_id_token(token: str) -> Dict[str, Any]:
#     if not EXTERNAL_OAUTH_PEM_PUBLIC_KEY:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="EXTERNAL_OAUTH_PEM_PUBLIC_KEY is required for id_token verification",
#         )

#     pem = _normalize_pem(EXTERNAL_OAUTH_PEM_PUBLIC_KEY)
#     header = jwt.get_unverified_header(token)
#     alg = header.get("alg")
#     if not alg:
#         raise HTTPException(status_code=401, detail="id_token missing signing algorithm")

#     kwargs: Dict[str, Any] = {
#         "algorithms": [alg],
#         "options": {"verify_signature": True, "verify_exp": True, "verify_aud": bool(EXTERNAL_OAUTH_AUDIENCE)},
#     }
#     if EXTERNAL_OAUTH_ISSUER:
#         kwargs["issuer"] = EXTERNAL_OAUTH_ISSUER
#     if EXTERNAL_OAUTH_AUDIENCE:
#         kwargs["audience"] = EXTERNAL_OAUTH_AUDIENCE

#     try:
#         return jwt.decode(token, pem, **kwargs)
#     except jwt.InvalidTokenError as exc:
#         raise HTTPException(status_code=401, detail="Invalid id_token") from exc


# def _derive_profile(token_payload: Dict[str, Any], user_info: Optional[Dict[str, Any]]) -> Dict[str, Any]:
#     profile = user_info or {}
#     profile_sub = profile.get("sub") or profile.get("id")
#     token_sub = token_payload.get("sub")
#     subject = profile_sub or token_sub
#     email = profile.get("email") or token_payload.get("email")

#     if not subject:
#         raise HTTPException(status_code=400, detail="Unable to resolve external user subject")

#     role_raw = profile.get("role") or token_payload.get("role") or "normal"
#     role = role_raw if role_raw in {"normal", "internal", "vip"} else "normal"

#     return {
#         "subject": str(subject),
#         "email": email,
#         "role": role,
#     }


# @router.get("/redirect")
# async def external_oauth_redirect(request: FastAPIRequest):
#     _require_enabled()
#     _require_provider_config()

#     state = secrets.token_urlsafe(32)
#     redirect_uri = _build_redirect_uri(request)

#     query = {
#         "client_id": EXTERNAL_OAUTH_CLIENT_ID,
#         "redirect_uri": redirect_uri,
#         "response_type": "code",
#         "scope": EXTERNAL_OAUTH_SCOPE,
#         "state": state,
#     }
#     redirect_target = f"{EXTERNAL_OAUTH_AUTHORIZE_URL}?{urlencode(query)}"

#     response = RedirectResponse(url=redirect_target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
#     response.set_cookie(
#         key=STATE_COOKIE_NAME,
#         value=state,
#         httponly=True,
#         secure=False,
#         samesite="lax",
#         max_age=600,
#     )
#     return response


# @router.get("/callback", name="external_oauth_callback")
# async def external_oauth_callback(
#     request: FastAPIRequest,
#     code: Optional[str] = Query(None),
#     state: Optional[str] = Query(None),
#     error: Optional[str] = Query(None),
#     supabase_service: SupabaseService = Depends(get_supabase_service),
# ):
#     _require_enabled()
#     _require_provider_config()

#     if error:
#         raise HTTPException(status_code=400, detail=f"OAuth provider returned error: {error}")

#     if not code:
#         raise HTTPException(status_code=400, detail="Missing authorization code")

#     expected_state = request.cookies.get(STATE_COOKIE_NAME)
#     if not expected_state or not state or not hmac.compare_digest(expected_state, state):
#         raise HTTPException(status_code=400, detail="Invalid OAuth state")

#     token_payload = _json_post_form(
#         EXTERNAL_OAUTH_TOKEN_URL,
#         {
#             "grant_type": "authorization_code",
#             "client_id": EXTERNAL_OAUTH_CLIENT_ID,
#             "client_secret": EXTERNAL_OAUTH_CLIENT_SECRET,
#             "redirect_uri": _build_redirect_uri(request),
#             "code": code,
#         },
#     )

#     id_token = token_payload.get("id_token")
#     access_token = token_payload.get("access_token")
#     if not id_token:
#         raise HTTPException(status_code=400, detail="Token exchange succeeded but id_token is missing")
#     if not access_token and not EXTERNAL_OAUTH_USERINFO_URL:
#         # access_token can be optional when profile fields are fully provided by id_token.
#         pass

#     verified_token_claims: Dict[str, Any] = _verify_id_token(id_token)

#     user_info = None
#     if EXTERNAL_OAUTH_USERINFO_URL and access_token:
#         user_info = _json_get_with_bearer(EXTERNAL_OAUTH_USERINFO_URL, access_token)

#     profile = _derive_profile(verified_token_claims, user_info)

#     canonical_user = await supabase_service.resolve_or_create_user_by_external_identity(
#         provider=EXTERNAL_OAUTH_PROVIDER,
#         provider_subject=profile["subject"],
#         email=profile.get("email"),
#         role=profile.get("role"),
#     )

#     app_token = create_app_access_token(
#         subject=canonical_user["id"],
#         email=canonical_user.get("email"),
#         role=canonical_user.get("role", "normal"),
#         provider=EXTERNAL_OAUTH_PROVIDER,
#     )

#     frontend_url = _frontend_callback_url()
#     redirect_query = urlencode(
#         {
#             "token": app_token,
#             "provider": EXTERNAL_OAUTH_PROVIDER,
#         }
#     )

#     response = RedirectResponse(
#         url=f"{frontend_url}?{redirect_query}",
#         status_code=status.HTTP_307_TEMPORARY_REDIRECT,
#     )
#     response.delete_cookie(STATE_COOKIE_NAME)
#     return response


# @router.get("/redirect-url")
# async def get_external_redirect_url(request: FastAPIRequest):
#     """Expose backend callback URL that must be registered on the OAuth provider."""
#     _require_enabled()
#     return {"redirect_url": _build_redirect_uri(request)}
