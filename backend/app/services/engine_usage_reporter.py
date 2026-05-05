# 用途：把每筆 usage_logs 回報給母平台 /api/engine-usage/report，並 cache
# 母平台回傳的 is_blocked / blocked_by 狀態給 quota gate 用。
#
# 流程概念（mirror mode，我們是 SOT）：
#   * usage_logs 寫進 DB → fire-and-forget 呼叫 report_for_usage_log_id()
#   * Reporter 解析 user 是否該回報 (Q4 決議的決策樹):
#       - external/mixed + 有 valid token → 真的呼叫母平台
#       - internal → skip + 標 reported_to_mother=true / report_error='skipped:internal'
#       - 純 supabase → skip + 標 'skipped:supabase_only'
#       - external 但沒 token / refresh_failed → skip + 標 'skipped:no_token'
#   * 母平台回 200 + status:0 → 標成功
#   * 母平台回 200 + is_blocked:true → 仍標成功（report 已被收下），但更新 block cache
#   * 母平台回 4xx (token revoked) → 標 refresh_failed，row 維持 unreported 給重試 worker 看
#   * 母平台 5xx / timeout → row 維持 unreported，increment report_attempts
#
# Quota gate (Q5: hard block, env-var configurable):
#   * Quota gate 用 BLOCK_CACHE 判斷使用者是否該擋。
#   * cache 由 report 回應或單獨 status() 呼叫填入。
#   * is_user_blocked() 不會打網路；超時資料視為 not blocked (fail-open)。

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from app.config import (
    ENGINE_USAGE_BLOCK_CACHE_TTL_SECONDS,
    ENGINE_USAGE_ENABLED,
    ENGINE_USAGE_ENFORCE_BLOCK,
    ENGINE_USAGE_MAX_RETRIES,
    ENGINE_USAGE_REPORT_URL,
    ENGINE_USAGE_RETRY_BATCH_SIZE,
    ENGINE_USAGE_RETRY_INTERVAL_SECONDS,
    ENGINE_USAGE_STATUS_URL,
    ENGINE_USAGE_TIMEOUT_SECONDS,
)
from app.services import mother_token_storage
from app.services.provider_model_mapper import map_to_mother_provider_model
from app.services.supabase_service import SupabaseService
from app.utils.http_client import post_json, get_json_with_bearer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Block cache (in-memory; resets on container restart, fail-open by design)
# ---------------------------------------------------------------------------


@dataclass
class _BlockEntry:
    is_blocked: bool
    blocked_by: Optional[str]
    fetched_at: float
    snapshot: Dict[str, Any]  # 完整的母平台回應 JSON，給 frontend 顯示用


_BLOCK_CACHE: Dict[str, _BlockEntry] = {}


def _cache_block_state(user_id: str, body: Dict[str, Any]) -> None:
    if not user_id:
        return
    _BLOCK_CACHE[user_id] = _BlockEntry(
        is_blocked=bool(body.get("is_blocked")),
        blocked_by=body.get("blocked_by"),
        fetched_at=time.time(),
        snapshot=body,
    )


def get_cached_block_state(user_id: str) -> Optional[Dict[str, Any]]:
    """回傳 user 的母平台配額狀態 snapshot（含 daily/weekly/monthly + is_blocked），
    沒有 cache 或 cache 過期則回 None。"""
    if not user_id:
        return None
    entry = _BLOCK_CACHE.get(user_id)
    if not entry:
        return None
    if (time.time() - entry.fetched_at) > ENGINE_USAGE_BLOCK_CACHE_TTL_SECONDS:
        return None
    return {
        "is_blocked": entry.is_blocked,
        "blocked_by": entry.blocked_by,
        "snapshot": entry.snapshot,
        "fetched_at": entry.fetched_at,
    }


def is_user_blocked(user_id: str) -> Tuple[bool, Optional[str]]:
    """Quota gate 介面：回傳 (should_block, blocked_by)。
    若 ENGINE_USAGE_ENFORCE_BLOCK = false 永遠回 (False, None)。
    若沒 cache 也回 (False, None) — fail-open，避免母平台沒回應時誤擋使用者。"""
    if not ENGINE_USAGE_ENFORCE_BLOCK:
        return False, None
    state = get_cached_block_state(user_id)
    if not state:
        return False, None
    return bool(state.get("is_blocked")), state.get("blocked_by")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


async def _load_usage_log_with_user(
    supabase_service: SupabaseService, usage_log_id: int
) -> Optional[Dict[str, Any]]:
    """讀 usage_logs row + 對應 users.role/auth_source。"""
    def _do():
        from sqlalchemy import text

        sql = text("""
            SELECT
                ul.id,
                ul.user_id,
                ul.model_id,
                ul.model_type,
                ul.input_token,
                ul.output_token,
                ul.image_token,
                ul.action,
                ul.created_at,
                ul.report_attempts,
                ul.reported_to_mother,
                u.role         AS user_role,
                u.auth_source  AS user_auth_source
              FROM ai_proposal_platform.usage_logs ul
              LEFT JOIN ai_proposal_platform.users u ON u.id = ul.user_id
             WHERE ul.id = :id
             LIMIT 1
        """)
        with supabase_service.get_db_session() as session:
            row = session.execute(sql, {"id": usage_log_id}).mappings().first()
            return dict(row) if row else None

    try:
        return await asyncio.to_thread(_do)
    except Exception as exc:
        logger.error("Failed to load usage_logs id=%s: %s", usage_log_id, exc, exc_info=True)
        return None


async def _mark_reported(
    supabase_service: SupabaseService,
    usage_log_id: int,
    *,
    success: bool,
    error_text: Optional[str],
    increment_attempts: bool,
) -> None:
    def _do():
        from sqlalchemy import text

        if success:
            sql = text("""
                UPDATE ai_proposal_platform.usage_logs
                   SET reported_to_mother = true,
                       reported_at = now(),
                       report_error = NULLIF(:error_text, ''),
                       report_attempts = report_attempts + CASE WHEN :inc THEN 1 ELSE 0 END
                 WHERE id = :id
            """)
        else:
            sql = text("""
                UPDATE ai_proposal_platform.usage_logs
                   SET report_error = :error_text,
                       report_attempts = report_attempts + CASE WHEN :inc THEN 1 ELSE 0 END
                 WHERE id = :id
            """)
        with supabase_service.get_db_session() as session:
            session.execute(
                sql,
                {
                    "id": usage_log_id,
                    "error_text": error_text or "",
                    "inc": increment_attempts,
                },
            )
            session.commit()

    try:
        await asyncio.to_thread(_do)
    except Exception as exc:
        logger.error("Failed to update usage_logs id=%s tracking: %s", usage_log_id, exc, exc_info=True)


# ---------------------------------------------------------------------------
# Main report path
# ---------------------------------------------------------------------------


def _classify_user(user_role: Optional[str], user_auth_source: Optional[str]) -> str:
    """
    回傳：
      'reportable'   外部使用者，要打 mother
      'skip_internal' 內部員工不回報
      'skip_supabase' 純 Supabase 帳號不回報
      'skip_unknown' 沒 user 或缺欄位
    """
    if not user_role:
        return "skip_unknown"
    if user_role == "internal":
        return "skip_internal"
    if user_auth_source in ("external", "mixed"):
        return "reportable"
    if user_auth_source == "supabase":
        return "skip_supabase"
    return "skip_unknown"


async def report_for_usage_log_id(
    supabase_service: SupabaseService,
    usage_log_id: int,
) -> None:
    """負責一筆 usage_logs 的回報。被 supabase_service.log_usage 與 retry loop 呼叫。"""
    if not ENGINE_USAGE_ENABLED:
        return
    if usage_log_id is None:
        return

    row = await _load_usage_log_with_user(supabase_service, int(usage_log_id))
    if not row:
        logger.debug("report_for_usage_log_id: row %s not found", usage_log_id)
        return

    if row.get("reported_to_mother"):
        return  # 早已回報；retry loop 會跳過，這裡是 race 保險。

    user_id = row.get("user_id")
    classification = _classify_user(row.get("user_role"), row.get("user_auth_source"))

    # Skip paths — mark with explicit skip reason，不再嘗試。
    if classification == "skip_internal":
        await _mark_reported(
            supabase_service, int(usage_log_id),
            success=True, error_text="skipped:internal",
            increment_attempts=False,
        )
        return
    if classification == "skip_supabase":
        await _mark_reported(
            supabase_service, int(usage_log_id),
            success=True, error_text="skipped:supabase_only",
            increment_attempts=False,
        )
        return
    if classification == "skip_unknown":
        await _mark_reported(
            supabase_service, int(usage_log_id),
            success=True, error_text="skipped:no_user",
            increment_attempts=False,
        )
        return

    # reportable → 取 token 並打母平台。
    access_token = await mother_token_storage.get_valid_access_token(
        supabase_service=supabase_service, user_id=str(user_id),
    )
    if not access_token:
        # 使用者沒 mother token (可能是先用 supabase 登入後升級成 mixed 但還沒 OAuth)
        # → 標 skip:no_token，下次使用者重新登入 OAuth 才會有 token，但屆時這
        # 筆已是 skip 狀態，不會自動補回報。可接受；mirror mode 不需要絕對一致。
        await _mark_reported(
            supabase_service, int(usage_log_id),
            success=True, error_text="skipped:no_token",
            increment_attempts=False,
        )
        return

    # 組 body：input/output tokens 必填。依母平台合約，不再傳遞 idempotency_key。
    model_info = {"id": row.get("model_id")}
    pm = map_to_mother_provider_model(model_info)

    body = {
        "input_tokens": int(row.get("input_token") or 0),
        "output_tokens": int(row.get("output_token") or 0),
        "model_provider": pm.provider,
        "model_name": pm.name,
    }

    # 安全網：母平台要求 input + output > 0。
    if (body["input_tokens"] + body["output_tokens"]) <= 0:
        await _mark_reported(
            supabase_service, int(usage_log_id),
            success=True, error_text="skipped:zero_tokens",
            increment_attempts=False,
        )
        return

    def _do_post():
        return post_json(
            ENGINE_USAGE_REPORT_URL, body, access_token,
            timeout=ENGINE_USAGE_TIMEOUT_SECONDS,
        )

    try:
        status_code, resp_body = await asyncio.to_thread(_do_post)
    except Exception as exc:
        status_code, resp_body = -1, {"error": f"unexpected: {exc}"}

    # 200 → 寫快取 + 標成功；is_blocked=true 也算「成功收到」，因為 mother 已紀錄。
    if status_code == 200 and isinstance(resp_body, dict) and resp_body.get("status") == 0:
        _cache_block_state(str(user_id), resp_body)
        await _mark_reported(
            supabase_service, int(usage_log_id),
            success=True, error_text=None,
            increment_attempts=True,
        )
        if resp_body.get("is_blocked"):
            logger.warning(
                "Mother quota blocked user=%s blocked_by=%s daily=%s",
                user_id, resp_body.get("blocked_by"), (resp_body.get("daily") or {}).get("used"),
            )
        return

    # 401 / 403 → token 失效，標 refresh_failed，row 留 unreported 但 retry 也不會成功。
    if status_code in (401, 403):
        try:
            await mother_token_storage._mark_refresh_failed(
                supabase_service, str(user_id), f"http_{status_code}",
            )
        except Exception:
            logger.exception("mark_refresh_failed indirect call failed")
        # 標 row 為 skip:auth — 因為等使用者重新登入也無法回頭補這筆。
        await _mark_reported(
            supabase_service, int(usage_log_id),
            success=True, error_text=f"skipped:auth_{status_code}",
            increment_attempts=True,
        )
        return

    # 422 validation_error → 永久失敗，標成功且寫詳細錯誤。再重送也不會通過。
    if status_code == 422:
        msg = ""
        try:
            msg = json.dumps(resp_body)[:500]
        except Exception:
            msg = "validation_error"
        await _mark_reported(
            supabase_service, int(usage_log_id),
            success=True, error_text=f"failed:validation:{msg}",
            increment_attempts=True,
        )
        logger.warning("Mother rejected report id=%s validation: %s", usage_log_id, msg)
        return

    # 其他錯誤（5xx / 網路）→ 留 unreported_to_mother=false，retry loop 會重試。
    attempts = int(row.get("report_attempts") or 0) + 1
    err_summary = f"http_{status_code}"
    if isinstance(resp_body, dict) and resp_body.get("error"):
        err_summary = f"{err_summary}:{str(resp_body.get('error'))[:200]}"

    if attempts >= ENGINE_USAGE_MAX_RETRIES:
        # 達上限：標成功 (放棄)，記 final_failed 給 ops 查。
        await _mark_reported(
            supabase_service, int(usage_log_id),
            success=True, error_text=f"final_failed:{err_summary}",
            increment_attempts=True,
        )
        logger.error(
            "Giving up on usage_logs id=%s after %s attempts (last err: %s)",
            usage_log_id, attempts, err_summary,
        )
        return

    # 還可重試。
    await _mark_reported(
        supabase_service, int(usage_log_id),
        success=False, error_text=err_summary,
        increment_attempts=True,
    )
    logger.info(
        "Engine usage report transient failure id=%s attempt=%s err=%s; will retry",
        usage_log_id, attempts, err_summary,
    )


def schedule_report_for_usage_log_id(
    supabase_service: SupabaseService,
    usage_log_id: int,
) -> None:
    """fire-and-forget wrapper — 從 supabase_service.log_usage 進來呼叫。
    避免回報失敗影響原本的 AI 生成 latency。"""
    if not ENGINE_USAGE_ENABLED:
        return
    try:
        asyncio.create_task(report_for_usage_log_id(supabase_service, usage_log_id))
    except RuntimeError:
        # 沒 running loop（測試 / startup）→ skip，retry loop 之後會撿到。
        logger.debug("schedule_report_for_usage_log_id: no running loop")


# ---------------------------------------------------------------------------
# Optional: prefetch quota status (for future use; not wired in by default)
# ---------------------------------------------------------------------------


async def refresh_user_block_state(
    supabase_service: SupabaseService, user_id: str,
) -> Optional[Dict[str, Any]]:
    """主動打 mother /api/engine-usage/status 更新 block cache。"""
    if not ENGINE_USAGE_ENABLED or not user_id:
        return None
    token = await mother_token_storage.get_valid_access_token(
        supabase_service=supabase_service, user_id=user_id,
    )
    if not token:
        return None

    def _do():
        return get_json_with_bearer(ENGINE_USAGE_STATUS_URL, token, ENGINE_USAGE_TIMEOUT_SECONDS)

    try:
        status_code, body = await asyncio.to_thread(_do)
    except Exception as exc:
        logger.warning("refresh_user_block_state failed for %s: %s", user_id, exc)
        return None

    if status_code == 200 and isinstance(body, dict) and body.get("status") == 0:
        _cache_block_state(user_id, body)
        return body
    return None


# ---------------------------------------------------------------------------
# Retry loop
# ---------------------------------------------------------------------------


async def _fetch_unreported_batch(
    supabase_service: SupabaseService, limit: int,
) -> Any:
    def _do():
        from sqlalchemy import text

        sql = text("""
            SELECT id
              FROM ai_proposal_platform.usage_logs
             WHERE reported_to_mother = false
               AND created_at < (now() - interval '30 seconds')
               AND report_attempts < :max_attempts
             ORDER BY created_at ASC
             LIMIT :limit
        """)
        with supabase_service.get_db_session() as session:
            return [r[0] for r in session.execute(
                sql,
                {"max_attempts": ENGINE_USAGE_MAX_RETRIES, "limit": limit},
            ).fetchall()]

    try:
        return await asyncio.to_thread(_do)
    except Exception as exc:
        logger.error("Retry loop fetch failed: %s", exc, exc_info=True)
        return []


async def retry_loop(supabase_service: SupabaseService) -> None:
    """無窮迴圈：每 N 秒掃一次未回報的 usage_logs 重送。lifecycle.py 啟動。"""
    interval = max(5, int(ENGINE_USAGE_RETRY_INTERVAL_SECONDS))
    batch = max(1, int(ENGINE_USAGE_RETRY_BATCH_SIZE))
    logger.info("Engine usage retry loop started: interval=%ss batch=%s", interval, batch)
    while True:
        try:
            ids = await _fetch_unreported_batch(supabase_service, batch)
            if ids:
                logger.info("Engine usage retry: %s rows pending", len(ids))
                for rid in ids:
                    try:
                        await report_for_usage_log_id(supabase_service, int(rid))
                    except Exception as exc:
                        logger.warning("Retry of id=%s raised: %s", rid, exc)
        except asyncio.CancelledError:
            logger.info("Engine usage retry loop cancelled")
            raise
        except Exception as exc:
            logger.error("Engine usage retry loop top-level error: %s", exc, exc_info=True)

        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            raise
