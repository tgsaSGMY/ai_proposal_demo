import time
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status

from app.config import APP_JWT_EXPIRES_SECONDS, APP_JWT_ISSUER, APP_JWT_SECRET


def _require_secret() -> str:
    # 確保 JWT 簽章密鑰已設定；若未設定，直接回傳 500 以避免發出無法驗證的 token。
    if not APP_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APP_JWT_SECRET is not configured",
        )
    return APP_JWT_SECRET


def create_app_access_token(*, subject: str, email: str | None, role: str, provider: str) -> str:
    # 建立應用層 access token：包含身份、角色、登入來源與標準時間欄位。
    secret = _require_secret()
    now = int(time.time())
    # payload 內容需與 decode 端的 require 欄位對齊，避免驗證階段缺欄位失敗。
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
    # 使用 HS256 對 payload 進行簽章。
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_app_access_token(token: str) -> Dict[str, Any]:
    # 驗證並解碼 access token：同時檢查簽章演算法、issuer 與必要聲明欄位。
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
        # 統一轉為 401，避免洩漏過多驗證細節。
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired app token",
        ) from exc
