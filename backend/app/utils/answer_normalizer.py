
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.models import StoredAnswerEntry

_VALID_SOURCES = {"user_input", "ai_generated", "system_estimate", "guided_derived", "pending"}
_CHAT_ANSWER_KEYS = ("chat_answers", "chatAnswers")
_OVERRIDABLE = ("source", "needs_review", "review_note", "confirmed")


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _clean_str(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and value.strip() else None


def normalize_answer_entry(raw: Any, updated_at: Optional[str] = None) -> StoredAnswerEntry:
    if isinstance(raw, StoredAnswerEntry):
        return raw
    if isinstance(raw, dict) and ("value" in raw or "reply" in raw):
        value = raw["value"] if "value" in raw else raw["reply"]
        source = raw.get("source")
        return StoredAnswerEntry(
            value=_to_text(value),
            source=source if source in _VALID_SOURCES else "user_input",
            updated_at=_clean_str(raw.get("updated_at") or raw.get("updatedAt")) or updated_at,
            needs_review=bool(raw.get("needs_review") or raw.get("needsReview")),
            review_note=_clean_str(raw.get("review_note") or raw.get("reviewNote")),
            confirmed=bool(raw.get("confirmed")),
        )
    return StoredAnswerEntry(value=_to_text(raw), updated_at=updated_at)


def answer_text(raw: Any) -> str:
    return normalize_answer_entry(raw).value


def normalize_answer_map(raw_map: Any) -> Dict[str, StoredAnswerEntry]:
    if not isinstance(raw_map, dict):
        return {}
    entries: Dict[str, StoredAnswerEntry] = {}
    for field_id, raw in raw_map.items():
        if not field_id:
            continue
        entry = normalize_answer_entry(raw)
        if entry.value.strip():
            entries[field_id] = entry
    return entries


def extract_chat_answer_entries(stored_answer: Any) -> Dict[str, StoredAnswerEntry]:
    if not isinstance(stored_answer, dict):
        return {}
    for key in _CHAT_ANSWER_KEYS:
        if isinstance(stored_answer.get(key), dict):
            return normalize_answer_map(stored_answer[key])
    return {}


def flatten_answers(raw_map: Any) -> Dict[str, str]:
    return {field_id: entry.value for field_id, entry in normalize_answer_map(raw_map).items()}


def flatten_stored_answer(stored_answer: Any) -> Any:
    if not isinstance(stored_answer, dict):
        return stored_answer
    flattened = dict(stored_answer)
    for key in _CHAT_ANSWER_KEYS:
        if isinstance(flattened.get(key), dict):
            flattened[key] = flatten_answers(flattened[key])
    return flattened


def build_entries(
    current_answers: Dict[str, Any],
    prior_entries: Dict[str, StoredAnswerEntry],
    meta: Optional[Dict[str, Any]] = None,
    overrides: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, StoredAnswerEntry]:
    meta = meta or {}
    overrides = overrides or {}
    entries: Dict[str, StoredAnswerEntry] = {}
    for field_id, raw_value in current_answers.items():
        value = _to_text(raw_value)
        if not field_id or not value.strip():
            continue
        prior = prior_entries.get(field_id)
        if prior is not None and prior.value.strip() == value.strip():
            entry = prior.model_copy(update={"value": value})
        else:
            entry = StoredAnswerEntry(value=value)
        stamp = meta.get(field_id)
        stamp = _clean_str(stamp.get("updated_at") if isinstance(stamp, dict) else stamp)
        if stamp:
            entry.updated_at = stamp
        tag = {
            k: v for k, v in (overrides.get(field_id) or {}).items()
            if k in _OVERRIDABLE and (k != "source" or v in _VALID_SOURCES)
        }
        if tag:
            entry = entry.model_copy(update=tag)
        entries[field_id] = entry
    return entries


def serialize_entries(entries: Dict[str, StoredAnswerEntry]) -> Dict[str, Dict[str, Any]]:
    return {field_id: entry.model_dump() for field_id, entry in entries.items()}
