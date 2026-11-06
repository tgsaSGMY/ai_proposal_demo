from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

WEIGHT_TABLES: Dict[str, Tuple[Tuple[str, ...], str, Optional[str]]] = {
    "schedule_and_checkpoints_local": (
        ("執行步驟及方法", "[]", "細分方法", "[]"),
        "計劃權重",
        "預定投入人月",
    ),
    "execution_plan_and_checkpoints_transform": (("計畫架構", "[]"), "計畫權重", None),
    "plan_content_and_implementation_rt_s": (("實施方式", "分項計畫", "[]"), "權重", None),
    # rt_l 與 imdp 的 schema 寫以分項計算，但實際計畫皆以整份計畫加總 100%，刻意採整份計畫
    "implementation_method_rt_l": (("分項計劃", "[]", "工作重點", "[]"), "權重(%)", None),
    "project_objectives": (("實施策略與實施方法", "分項計劃", "[]", "細項", "[]"), "占比", None),
    "project_objectives_test": (("實施策略與實施方法", "分項計劃", "[]", "細項", "[]"), "占比", None),
}

_WEIGHT_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*[%％]?\s*$")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
_PLACEHOLDER = "待決定"


def _collect_rows(node: Any, path: Tuple[str, ...]) -> List[Dict[str, Any]]:
    if not path:
        return [node] if isinstance(node, dict) else []
    head, rest = path[0], path[1:]
    if head == "[]":
        if not isinstance(node, list):
            return []
        return [row for item in node for row in _collect_rows(item, rest)]
    if not isinstance(node, dict):
        return []
    return _collect_rows(node.get(head), rest)


def _parse_weight(value: Any) -> Optional[float]:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0
    match = _WEIGHT_RE.match(text)
    return float(match.group(1)) if match else None


def _parse_effort(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    match = _NUMBER_RE.search(str(value or ""))
    return float(match.group(0)) if match else 0.0


def _collect_groups(content: Any, path: Tuple[str, ...]) -> List[List[Any]]:
    # 同一層清單（如同一執行步驟下的各細分方法）為一組
    if len(path) < 2 or path[-1] != "[]":
        return []
    parents = _collect_rows(content, path[:-2])
    return [p.get(path[-2]) for p in parents if isinstance(p.get(path[-2]), list)]


def _format_effort(value: float, original: Any) -> Any:
    number = int(value) if float(value).is_integer() else round(value, 1)
    if isinstance(original, (int, float)) and not isinstance(original, bool):
        return number
    return str(number)


def _share_group_rows(section_id: str, content: Any, path: Tuple[str, ...], weight_key: str,
                      effort_key: Optional[str]) -> None:
    """同組中沒有獨立數值的列（權重寫「（包含於本步驟總權重）」，或權重與人月皆為 0）改為與同組平分。

    in-app 2026-10-05 第十次：每個步驟的第二列寫「（包含於本步驟總權重）」、人月 0，提示詞規則無效；
    原本整張表因權重無法解析而不調整。不刪除列，避免移除該列在內文中的說明。
    """
    for group in _collect_groups(content, path):
        rows = [row for row in group if isinstance(row, dict)]
        if len(rows) < 2:
            continue
        weights = [_parse_weight(row.get(weight_key)) for row in rows]
        efforts = [_parse_effort(row.get(effort_key)) if effort_key else 0.0 for row in rows]
        # 「待決定」代表數值未知，不視為包含於同組；沒有人月欄位時無法判斷 0% 列是否為空列
        shared = [
            i for i, row in enumerate(rows)
            if (
                weights[i] is None
                and not _NUMBER_RE.search(str(row.get(weight_key) or ""))
                and _PLACEHOLDER not in str(row.get(weight_key))
            )
            or (effort_key and weights[i] == 0 and efforts[i] == 0)
        ]
        known = [i for i in range(len(rows)) if i not in shared and weights[i] is not None]
        # 有權重但人月為 0 的列（in-app 2026-10-05 第十二次：「10.3% / 0 人月」）：
        # 依權重比例分配同組人月，權重不變
        if not shared and effort_key and None not in weights:
            group_effort, group_weight = sum(efforts), sum(weights)
            if group_effort > 0 and group_weight > 0 and any(e == 0 and w > 0 for e, w in zip(efforts, weights)):
                before = [row.get(effort_key) for row in rows]
                for row, weight in zip(rows, weights):
                    row[effort_key] = _format_effort(round(group_effort * weight / group_weight, 1), row.get(effort_key))
                logger.info(
                    f"[WeightNormalizer] {section_id}: person-months spread by weight: {before} -> "
                    f"{[row.get(effort_key) for row in rows]}"
                )
            continue
        if not shared or not known:
            continue

        group_weight = sum(weights[i] for i in known)
        group_effort = sum(efforts)
        style = _detect_style([rows[i].get(weight_key) for i in known])
        before = [(row.get(weight_key), row.get(effort_key) if effort_key else None) for row in rows]
        if effort_key and group_effort > 0 and any(e == 0 for e in efforts):
            share = group_effort / len(rows)
            efforts = [share] * len(rows)
            for row in rows:
                row[effort_key] = _format_effort(share, row.get(effort_key))
        total_effort = sum(efforts)
        for i, row in enumerate(rows):
            portion = efforts[i] / total_effort if total_effort > 0 else 1 / len(rows)
            row[weight_key] = _format_weight(round(group_weight * portion, 1), style)
        logger.info(
            f"[WeightNormalizer] {section_id}: shared step totals across {len(rows)} rows: {before} -> "
            f"{[(row.get(weight_key), row.get(effort_key) if effort_key else None) for row in rows]}"
        )


def _detect_style(values: List[Any]) -> Tuple[bool, str, Optional[int]]:
    filled = [v for v in values if v is not None and str(v).strip()]
    numeric = bool(filled) and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in filled)
    texts = [str(v).strip() for v in filled if isinstance(v, str)]
    suffix = "％" if any("％" in t for t in texts) else ("%" if any("%" in t for t in texts) else "")
    decimals = {len(m.group(1)) for t in texts if (m := re.search(r"\.(\d+)", t))}
    fixed = next(iter(decimals)) if texts and len(decimals) == 1 and all("." in t for t in texts) else None
    return numeric, suffix, fixed


def _format_weight(value: float, style: Tuple[bool, str, Optional[int]]) -> Any:
    numeric, suffix, fixed = style
    if numeric:
        return int(value) if float(value).is_integer() else value
    text = f"{value:.{fixed}f}" if fixed else f"{value:.1f}".rstrip("0").rstrip(".")
    return f"{text}{suffix}"


def normalize_plan_weights(section_id: str, content: Any) -> Any:
    spec = WEIGHT_TABLES.get(section_id)
    if not spec or not isinstance(content, dict):
        return content
    path, weight_key, effort_key = spec

    _share_group_rows(section_id, content, path, weight_key, effort_key)
    rows = _collect_rows(content, path)
    if not rows:
        return content

    weights: List[float] = []
    for row in rows:
        weight = _parse_weight(row.get(weight_key))
        if weight is None:
            logger.warning(
                f"[WeightNormalizer] {section_id}: unparseable {weight_key}={row.get(weight_key)!r}, table left unchanged"
            )
            return content
        weights.append(weight)
    efforts = [_parse_effort(row.get(effort_key)) if effort_key else 0.0 for row in rows]

    original = [row.get(weight_key) for row in rows]
    original_total = sum(weights)
    zero_with_effort = [i for i, w in enumerate(weights) if w == 0 and efforts[i] > 0]
    if abs(original_total - 100) < 0.05 and not zero_with_effort:
        return content

    if zero_with_effort:
        weighted = [i for i, w in enumerate(weights) if w > 0]
        weighted_effort = sum(efforts[i] for i in weighted)
        if not weighted:
            rate = 1.0
        elif weighted_effort > 0:
            rate = sum(weights[i] for i in weighted) / weighted_effort
        else:
            rate = 0.0
        for i in zero_with_effort:
            weights[i] = efforts[i] * rate

    total = sum(weights)
    if total <= 0:
        logger.warning(f"[WeightNormalizer] {section_id}: all weights and efforts are 0, table left unchanged")
        return content

    scaled = [round(w * 100 / total, 1) for w in weights]
    largest = max(range(len(scaled)), key=lambda i: scaled[i])
    scaled[largest] = round(scaled[largest] + round(100 - sum(scaled), 1), 1)

    style = _detect_style(original)
    for row, value in zip(rows, scaled):
        row[weight_key] = _format_weight(value, style)

    logger.info(
        f"[WeightNormalizer] {section_id}: total {original_total:g}% -> 100% "
        f"({len(zero_with_effort)} zero rows filled): {original} -> {[row[weight_key] for row in rows]}"
    )
    return content
