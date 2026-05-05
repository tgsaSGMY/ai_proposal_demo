# 用途：Quota gate — 在進入 AI 生成路徑前檢查母平台是否回報 is_blocked。
#
# Q5 決議：
#   * ENGINE_USAGE_ENFORCE_BLOCK = true (預設) 時，若 cache 顯示 is_blocked=true
#     直接拋 HTTPException(429) 並提供清楚的中文錯誤訊息。
#   * ENGINE_USAGE_ENFORCE_BLOCK = false (soft mode) 時這個 helper 不做事。
#   * cache miss → fail-open：母平台沒回過任何訊號就放行。

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, status

from app.config import ENGINE_USAGE_ENFORCE_BLOCK
from app.services import engine_usage_reporter

logger = logging.getLogger(__name__)

_BLOCK_BY_LABEL_ZH = {
    "daily": "每日",
    "weekly": "本週",
    "monthly": "本月",
}


def _format_blocked_message(blocked_by: Optional[str]) -> str:
    label = _BLOCK_BY_LABEL_ZH.get((blocked_by or "").lower(), "")
    if label:
        return f"您{label}的 AI 用量已達 TGSA 平台上限，請待重置時間後再試或聯繫客服升級方案。"
    return "您的 AI 用量已達 TGSA 平台上限，請待重置時間後再試或聯繫客服升級方案。"


def enforce_mother_quota_or_429(user_id: str) -> None:
    """若 ENFORCE_BLOCK 啟動且 user 被擋，拋 HTTPException(429)。否則回 None。"""
    if not ENGINE_USAGE_ENFORCE_BLOCK:
        return
    blocked, blocked_by = engine_usage_reporter.is_user_blocked(user_id)
    if not blocked:
        return
    logger.info("Quota gate: refusing AI call for user=%s blocked_by=%s", user_id, blocked_by)
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=_format_blocked_message(blocked_by),
    )
