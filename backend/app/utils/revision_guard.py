from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_PLACEHOLDER_VALUES = {"待決定", "未提供", "無", "暫無", "无", "-", "—", "N/A"}

MIN_PREVIOUS_FILLED = 3
EMPTIED_RATIO = 0.5


def count_filled(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, dict):
        return sum(count_filled(v) for v in value.values())
    if isinstance(value, list):
        return sum(count_filled(v) for v in value)
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return 1
    text = str(value).strip()
    return 1 if text and text not in _PLACEHOLDER_VALUES else 0


def restore_emptied_fields(
    section_id: str,
    previous: Optional[Dict[str, Any]],
    content: Any,
) -> Tuple[Any, List[str]]:
    if not isinstance(previous, dict) or not isinstance(content, dict):
        return content, []

    restored = []
    for key, old_value in previous.items():
        old_filled = count_filled(old_value)
        if old_filled < MIN_PREVIOUS_FILLED:
            continue
        new_filled = count_filled(content.get(key))
        if new_filled < old_filled * EMPTIED_RATIO:
            content[key] = copy.deepcopy(old_value)
            restored.append(key)
            logger.warning(
                f"[RevisionGuard] {section_id}.{key}: filled {old_filled} -> {new_filled}, restored previous version"
            )
    return content, restored
