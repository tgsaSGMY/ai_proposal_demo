# 將對話歷史和執行日誌合併成一個時間線，並提供時間解析和版本正規化的工具函數。

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

_TAIWAN_TZ = timezone(timedelta(hours=8))
_TW_LOCALE_PATTERN = re.compile(
    r"^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})\s*(?P<period>上午|下午)(?P<hour>\d{1,2}):(?P<minute>\d{2})(?::(?P<second>\d{2}))?$"
)


def _parse_taiwan_locale_timestamp(candidate: str) -> Optional[datetime]:
    match = _TW_LOCALE_PATTERN.match(candidate)
    if not match:
        return None

    parts = match.groupdict()
    year = int(parts["year"])
    month = int(parts["month"])
    day = int(parts["day"])
    hour = int(parts["hour"])
    minute = int(parts["minute"])
    second = int(parts.get("second") or 0)
    period = parts["period"]

    if period == "上午":
        hour = 0 if hour == 12 else hour
    else:  # 下午
        hour = 12 if hour == 12 else hour + 12

    try:
        return datetime(year, month, day, hour, minute, second, tzinfo=_TAIWAN_TZ)
    except ValueError:
        return None


def parse_iso_timestamp(value: Optional[Any]) -> Optional[datetime]:
    """Parse ISO-like timestamp strings safely (with TW locale fallback)."""

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        candidate = str(value)
    else:
        candidate = value

    candidate = candidate.strip()
    if not candidate:
        return None

    # Normalize trailing Z to +00:00 for datetime.fromisoformat
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        pass

    # legacy locale string like 2026/1/14 上午10:47:19
    legacy = _parse_taiwan_locale_timestamp(candidate)
    if legacy:
        return legacy

    return None


def _coerce_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            import json

            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _coerce_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    if isinstance(value, str):
        try:
            import json

            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


def build_timeline_entries(
    conversation_history: Any,
    execution_logs: List[Dict[str, Any]],
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Merge conversation and execution log events into a single timeline."""

    entries: List[Dict[str, Any]] = []

    def in_window(ts: Optional[datetime]) -> bool:
        if ts is None:
            return False
        if start_time and ts < start_time:
            return False
        if end_time and ts > end_time:
            return False
        return True

    for log in execution_logs or []:
        ts = parse_iso_timestamp(log.get("created_at"))
        if not in_window(ts):
            continue
        entries.append(
            {
                "type": "event",
                "timestamp": ts.isoformat(),
                "event_type": log.get("event_type"),
                "section_id": log.get("section_id"),
                "version_id": log.get("version_id"),
                "external_sources": _coerce_list(log.get("external_sources")),
                "payload": _coerce_dict(log.get("payload")),
            }
        )

    for message in conversation_history or []:
        if not isinstance(message, dict):
            continue
        ts = parse_iso_timestamp(message.get("timestamp") or message.get("created_at"))
        if not in_window(ts):
            continue
        entries.append(
            {
                "type": "conversation",
                "timestamp": ts.isoformat(),
                "role": message.get("role"),
                "message_id": message.get("id"),
                "content": message.get("content"),
            }
        )

    entries.sort(key=lambda item: item["timestamp"])
    return entries


def normalize_versions(saved_plan: Any) -> List[Dict[str, Any]]:
    """Always treat saved_plan as a list of version dicts."""

    if saved_plan is None:
        return []
    if isinstance(saved_plan, list):
        return saved_plan
    if isinstance(saved_plan, dict):
        return [saved_plan]
    return []
