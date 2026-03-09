import time
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status

from app.config import APP_JWT_EXPIRES_SECONDS, APP_JWT_ISSUER, APP_JWT_SECRET


def _require_secret() -> str:
    if not APP_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APP_JWT_SECRET is not configured",
        )
    return APP_JWT_SECRET


def create_app_access_token(*, subject: str, email: str | None, role: str, provider: str) -> str:
    secret = _require_secret()
    now = int(time.time())
    payload: Dict[str, Any] = {
        "sub": subject,
        "email": email,
        "role": role,
        "provider": provider,
        "iss": APP_JWT_ISSUER,
        "iat": now,
        "exp": now + APP_JWT_EXPIRES_SECONDS,
        "typ": "access",
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_app_access_token(token: str) -> Dict[str, Any]:
    secret = _require_secret()
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=APP_JWT_ISSUER,
            options={"require": ["sub", "exp", "iat", "iss"]},
        )
        return payload
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired app token",
        ) from exc
