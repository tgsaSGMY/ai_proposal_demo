# 用途：管理使用者在母平台 (TGSA Portal) 的 OAuth access_token / refresh_token，
# 並用 pgsodium 在 DB 端做 AEAD 加密。
#
# 流程：
#   1. external_auth callback 拿到 access_token (有時也有 refresh_token) →
#      呼叫 store_token() 寫進 user_oauth_tokens。
#   2. engine_usage_reporter 要打母平台前 → 呼叫 get_valid_access_token()，
#      自動處理 expires_at 檢查與 refresh。
#   3. 若 refresh 失敗 (4xx) → 標 refresh_failed = true，下次 reporter 看到
#      會跳過該使用者，等使用者重新登入。

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.config import (
    ENGINE_USAGE_TOKEN_REFRESH_LEEWAY_SECONDS,
    EXTERNAL_OAUTH_CLIENT_ID,
    EXTERNAL_OAUTH_CLIENT_SECRET,
    EXTERNAL_OAUTH_PROVIDER,
    EXTERNAL_OAUTH_TOKEN_URL,
)
from app.services.supabase_service import SupabaseService
from app.utils.http_client import post_form

logger = logging.getLogger(__name__)

TABLE = "user_oauth_tokens"
PROVIDER_TGSA = "tgsa_oauth"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _compute_expires_at(expires_in: Optional[int]) -> datetime:
    # 若 mother 沒回 expires_in，先給 1 小時保守值。下次 reporter 用到會再判斷。
    seconds = int(expires_in) if expires_in is not None and int(expires_in) > 0 else 3600
    return _now_utc() + timedelta(seconds=seconds)


def _is_expiring_soon(expires_at_iso: str) -> bool:
    """判斷 token 是否快過期（含 leeway buffer）。"""
    try:
        # Supabase returns timestamptz as ISO string with timezone.
        ts = datetime.fromisoformat(expires_at_iso.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return True
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts <= (_now_utc() + timedelta(seconds=ENGINE_USAGE_TOKEN_REFRESH_LEEWAY_SECONDS))


# ---------------------------------------------------------------------------
# Storage operations
# ---------------------------------------------------------------------------


async def store_token(
    *,
    supabase_service: SupabaseService,
    user_id: str,
    access_token: str,
    refresh_token: Optional[str],
    expires_in: Optional[int],
    scope: Optional[str],
) -> None:
    """寫入或覆寫使用者的 mother access/refresh token (加密)。"""
    if not user_id or not access_token:
        return

    expires_at = _compute_expires_at(expires_in)

    def _do_upsert():
        # 用原生 SQL 經過 SQLAlchemy 進去，直接呼叫 pgsodium helper 加密。
        # 不走 PostgREST 是因為 bytea + 自訂 SQL function 比較難在 PostgREST
        # query builder 裡組出來。
        from sqlalchemy import text

        sql = text("""
            INSERT INTO ai_proposal_platform.user_oauth_tokens
                (user_id, provider, access_token, refresh_token, expires_at, scope, refresh_failed)
            VALUES (
                :user_id,
                :provider,
                ai_proposal_platform.encrypt_mother_token(:access_token, :user_id),
                CASE
                    WHEN :refresh_token IS NULL THEN NULL
                    ELSE ai_proposal_platform.encrypt_mother_token(:refresh_token, :user_id)
                END,
                :expires_at,
                :scope,
                false
            )
            ON CONFLICT (user_id, provider) DO UPDATE
            SET access_token  = EXCLUDED.access_token,
                refresh_token = COALESCE(EXCLUDED.refresh_token, ai_proposal_platform.user_oauth_tokens.refresh_token),
                expires_at    = EXCLUDED.expires_at,
                scope         = COALESCE(EXCLUDED.scope, ai_proposal_platform.user_oauth_tokens.scope),
                refresh_failed = false,
                last_refresh_at = now()
        """)

        with supabase_service.get_db_session() as session:
            session.execute(
                sql,
                {
                    "user_id": user_id,
                    "provider": PROVIDER_TGSA,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at,
                    "scope": scope,
                },
            )
            session.commit()

    try:
        await asyncio.to_thread(_do_upsert)
        logger.info("Stored mother OAuth token for user %s (expires_at=%s)", user_id, expires_at.isoformat())
    except Exception as exc:
        logger.error("Failed to store mother OAuth token for user %s: %s", user_id, exc, exc_info=True)


async def _read_token_row(
    supabase_service: SupabaseService,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    """讀取一筆 token row 並 decrypt access/refresh token。"""
    def _do_read():
        from sqlalchemy import text

        sql = text("""
            SELECT user_id,
                   provider,
                   ai_proposal_platform.decrypt_mother_token(access_token, user_id)  AS access_token,
                   CASE
                       WHEN refresh_token IS NULL THEN NULL
                       ELSE ai_proposal_platform.decrypt_mother_token(refresh_token, user_id)
                   END AS refresh_token,
                   expires_at,
                   scope,
                   refresh_failed
              FROM ai_proposal_platform.user_oauth_tokens
             WHERE user_id = :user_id AND provider = :provider
             LIMIT 1
        """)

        with supabase_service.get_db_session() as session:
            row = session.execute(
                sql,
                {"user_id": user_id, "provider": PROVIDER_TGSA},
            ).mappings().first()
            return dict(row) if row else None

    try:
        return await asyncio.to_thread(_do_read)
    except Exception as exc:
        logger.error("Failed to read mother OAuth token for user %s: %s", user_id, exc, exc_info=True)
        return None


async def _mark_refresh_failed(supabase_service: SupabaseService, user_id: str, reason: str) -> None:
    def _do_mark():
        from sqlalchemy import text

        sql = text("""
            UPDATE ai_proposal_platform.user_oauth_tokens
               SET refresh_failed = true,
                   last_refresh_at = now()
             WHERE user_id = :user_id AND provider = :provider
        """)
        with supabase_service.get_db_session() as session:
            session.execute(sql, {"user_id": user_id, "provider": PROVIDER_TGSA})
            session.commit()

    try:
        await asyncio.to_thread(_do_mark)
        logger.warning("Marked mother OAuth token refresh_failed for user %s: %s", user_id, reason)
    except Exception as exc:
        logger.error("Could not mark refresh_failed for user %s: %s", user_id, exc, exc_info=True)


async def _refresh_with_mother(refresh_token: str) -> Optional[Dict[str, Any]]:
    """呼叫母平台 token endpoint 用 refresh_token 換新 access_token。"""
    if not EXTERNAL_OAUTH_TOKEN_URL or not EXTERNAL_OAUTH_CLIENT_ID or not EXTERNAL_OAUTH_CLIENT_SECRET:
        logger.warning("Cannot refresh mother token: external OAuth config incomplete")
        return None

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": EXTERNAL_OAUTH_CLIENT_ID,
        "client_secret": EXTERNAL_OAUTH_CLIENT_SECRET,
    }

    def _do_post():
        return post_form(EXTERNAL_OAUTH_TOKEN_URL, payload)

    try:
        return await asyncio.to_thread(_do_post)
    except Exception as exc:
        logger.warning("Mother token refresh unexpected error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public API used by reporter
# ---------------------------------------------------------------------------


async def get_valid_access_token(
    *,
    supabase_service: SupabaseService,
    user_id: str,
) -> Optional[str]:
    """
    回傳一個還沒過期的 access_token，或 None 表示「沒有可用 token」。
    在 expiry leeway 內會主動嘗試 refresh。
    """
    if not user_id:
        return None

    row = await _read_token_row(supabase_service, user_id)
    if not row:
        return None

    if row.get("refresh_failed"):
        # 已知失效，等使用者重新登入。reporter 會 skip 並 mark usage_logs。
        return None

    expires_at = row.get("expires_at")
    expires_at_str = expires_at.isoformat() if isinstance(expires_at, datetime) else str(expires_at or "")

    if not _is_expiring_soon(expires_at_str):
        return row.get("access_token")

    # 過期或快過期：嘗試 refresh。
    refresh_token = row.get("refresh_token")
    if not refresh_token:
        # 沒有 refresh token 可用，標失效。
        await _mark_refresh_failed(supabase_service, user_id, "no_refresh_token")
        return None

    refreshed = await _refresh_with_mother(refresh_token)
    if not refreshed or not refreshed.get("access_token"):
        await _mark_refresh_failed(supabase_service, user_id, "refresh_call_failed_or_empty")
        return None

    # 寫回 (refresh response 通常含新的 refresh_token，沒有就沿用舊的)。
    await store_token(
        supabase_service=supabase_service,
        user_id=user_id,
        access_token=refreshed["access_token"],
        refresh_token=refreshed.get("refresh_token"),
        expires_in=refreshed.get("expires_in"),
        scope=refreshed.get("scope") or row.get("scope"),
    )

    return refreshed["access_token"]


async def has_token(supabase_service: SupabaseService, user_id: str) -> bool:
    """快查使用者是否有可用 token (不做 refresh)。reporter 跳過判斷用。"""
    if not user_id:
        return False

    def _do_check():
        from sqlalchemy import text

        sql = text("""
            SELECT 1
              FROM ai_proposal_platform.user_oauth_tokens
             WHERE user_id = :user_id
               AND provider = :provider
               AND refresh_failed = false
             LIMIT 1
        """)
        with supabase_service.get_db_session() as session:
            return session.execute(
                sql,
                {"user_id": user_id, "provider": PROVIDER_TGSA},
            ).first() is not None

    try:
        return await asyncio.to_thread(_do_check)
    except Exception as exc:
        logger.error("has_token check failed for user %s: %s", user_id, exc)
        return False
