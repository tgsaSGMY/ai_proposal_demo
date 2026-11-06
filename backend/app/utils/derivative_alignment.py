from __future__ import annotations

import logging
import re
from typing import Any, Dict, Iterator, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 衍生產品或服務在不同章節各自生成，提示詞無法保證一致（表格寫「無」、預期效益寫「共待決定項」），
# 生成後依【關鍵指標目標值】中的「衍生產品或服務」統一改寫。
# 欄位依章節 JSON schema 的欄位名稱辨識（含「衍生」），不綁定特定章節 ID：
# - 表格：type 為 array 的欄位，列內含類型／名稱欄與說明欄
# - 項數：type 為 object 的欄位，內含 效益／效應／數值 其中之一

PLACEHOLDER = "待決定"
_DERIVATIVE_KEY = "衍生"
_COUNT_VALUE_KEYS = ("效益", "效應", "數值")
_ROW_NAME_HINTS = ("類型", "名稱", "項目")
_TARGET_LINE_RE = re.compile(r"^-\s*([^：:\n]*衍生[^：:\n]*)[：:]\s*(.+)$", re.MULTILINE)
_COUNT_RE = re.compile(r"(\d+)\s*項")
_NAMES_RE = re.compile(r"[（(]([^）)]+)[）)]")

Target = Tuple[str, int, List[str]]


def parse_derivative_target(targets_text: str) -> Optional[Target]:
    """從【關鍵指標目標值】段落取出衍生產品或服務的目標值。

    回傳 ("tbd", 0, [])、("zero", 0, [])、("count", N, 名稱清單)，找不到時回傳 None。
    """
    match = _TARGET_LINE_RE.search(targets_text or "")
    if not match:
        return None
    value = match.group(2).strip()
    if PLACEHOLDER in value:
        return ("tbd", 0, [])
    count_match = _COUNT_RE.search(value)
    if value.startswith("無") or (count_match and int(count_match.group(1)) == 0):
        return ("zero", 0, [])
    if not count_match:
        return None
    names_match = _NAMES_RE.search(value)
    names = [n.strip() for n in re.split(r"[、,，;；]", names_match.group(1)) if n.strip()] if names_match else []
    return ("count", int(count_match.group(1)), names)


_MAIN_PRODUCT_KEY = "產出新產品"
# generate_plan 在用戶回答之後附加的段落；備援檢查只看用戶回答，避免附件或背景資料卡片誤觸發
_APPENDED_BLOCK_MARKERS = ("【來自 Commands 的額外上下文】", "【專案附件資料")


def _answers_only(user_input: str) -> str:
    text = user_input or ""
    cut = min((i for i in (text.find(m) for m in _APPENDED_BLOCK_MARKERS) if i >= 0), default=len(text))
    return text[:cut]


def _names_in(value: str) -> List[str]:
    match = _NAMES_RE.search(value)
    return [n.strip() for n in re.split(r"[、,，;；]", match.group(1)) if n.strip()] if match else []


def _same_name(a: str, b: str) -> bool:
    a, b = re.sub(r"\s+", "", a), re.sub(r"\s+", "", b)
    return bool(a and b) and (a in b or b in a)


def enforce_derivative_target(
    targets: List[Tuple[str, str]], user_input: str, has_evidence: bool
) -> List[Tuple[str, str]]:
    """衍生目標值的兩項檢查（提示詞規則兩次無效，in-app 2026-10-05）。

    一般情況由 evidence 檢查（llm_service._apply_target_evidence）處理用戶寫「待決定」的指標。
    - 備援：衍生目標沒有 evidence 時，若用戶回答（不含附件與背景資料）有一行同時含「衍生」與
      「待決定」且沒有「N項」，目標值改為「待決定」。
    - 主產品：衍生名稱與【關鍵指標目標值】中「產出新產品或服務」的名稱相同者移除；全部移除時改為「待決定」。
      兩個 metric 名稱都由我方提示詞指定，不依賴範本或用戶用詞。
    """
    index = next((i for i, (metric, _) in enumerate(targets) if _DERIVATIVE_KEY in metric), None)
    if index is None:
        return targets
    metric, value = targets[index]
    answer_lines = _answers_only(user_input).splitlines()
    if not has_evidence and any(
        _DERIVATIVE_KEY in line and PLACEHOLDER in line and not _COUNT_RE.search(line) for line in answer_lines
    ):
        new_value = PLACEHOLDER
    else:
        main_names = [n for m, v in targets if _MAIN_PRODUCT_KEY in m for n in _names_in(v)]
        names = _names_in(value)
        kept = [n for n in names if not any(_same_name(n, m) for m in main_names)]
        if len(kept) == len(names):
            return targets
        new_value = f"{len(kept)}項（{'、'.join(kept)}）" if kept else PLACEHOLDER
    if new_value == value:
        return targets
    logger.warning(f"[DerivativeAlignment] target {metric}={value!r} replaced by {new_value!r} from user input")
    result = list(targets)
    result[index] = (metric, new_value)
    return result


def _find_fields(schema: Any, path: Tuple[str, ...] = ()) -> Iterator[Tuple[str, Tuple[str, ...], Dict[str, Any]]]:
    """走訪 schema，回傳 ("table" | "count", 路徑, 欄位 schema)。"""
    if not isinstance(schema, dict):
        return
    props = schema.get("properties")
    if not isinstance(props, dict):
        return
    for key, prop in props.items():
        if not isinstance(prop, dict):
            continue
        sub_path = path + (key,)
        if _DERIVATIVE_KEY in key:
            if prop.get("type") == "array" and isinstance((prop.get("items") or {}).get("properties"), dict):
                yield ("table", sub_path, prop["items"]["properties"])
                continue
            inner = prop.get("properties")
            if prop.get("type") == "object" and isinstance(inner, dict) and any(k in inner for k in _COUNT_VALUE_KEYS):
                yield ("count", sub_path, inner)
                continue
        yield from _find_fields(prop, sub_path)


def _get_path(node: Any, path: Tuple[str, ...]) -> Any:
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def _set_path(node: Dict[str, Any], path: Tuple[str, ...], value: Any) -> None:
    for key in path[:-1]:
        child = node.get(key)
        if not isinstance(child, dict):
            child = {}
            node[key] = child
        node = child
    node[path[-1]] = value


def _row_keys(item_props: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    keys = list(item_props)
    name_key = next((k for k in keys if any(h in k for h in _ROW_NAME_HINTS)), None)
    desc_key = next((k for k in keys if "說明" in k), None)
    if not name_key or not desc_key or name_key == desc_key:
        return None
    return name_key, desc_key


def _aligned_table(rows: Any, target: Target, name_key: str, desc_key: str) -> Any:
    kind, count, names = target
    if kind == "tbd":
        return [{name_key: PLACEHOLDER, desc_key: PLACEHOLDER}]
    if kind == "zero":
        return [{name_key: "無", desc_key: "無"}]
    existing = [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []
    real_rows = [r for r in existing if str(r.get(name_key) or "").strip() not in ("", "無", PLACEHOLDER)]
    if len(real_rows) == count or not names:
        return rows
    by_name = {str(r.get(name_key) or "").strip(): r for r in real_rows}
    return [{name_key: name, desc_key: (by_name.get(name) or {}).get(desc_key) or PLACEHOLDER} for name in names]


def _aligned_count(node: Any, target: Target, value_key: str, desc_key: Optional[str], numeric: bool) -> Any:
    kind, count, _ = target
    node = dict(node) if isinstance(node, dict) else {}
    if kind == "tbd":
        node[value_key] = PLACEHOLDER
    else:
        node[value_key] = count if numeric else str(count)
    if kind == "zero" and desc_key:
        node[desc_key] = "無"
    # 待決定時不可列出可能項目（in-app 2026-10-05：「潛在衍生項目包含…」）
    if kind == "tbd" and desc_key:
        node[desc_key] = PLACEHOLDER
    return node


def align_derivatives(section_id: str, content: Any, schema: Any, target: Optional[Target]) -> bool:
    """依目標值改寫章節中所有衍生產品或服務欄位；有改動時回傳 True。"""
    if target is None or not isinstance(content, dict):
        return False
    changed = False
    for field_kind, path, props in _find_fields(schema):
        current = _get_path(content, path)
        if field_kind == "table":
            keys = _row_keys(props)
            if not keys:
                continue
            aligned = _aligned_table(current, target, *keys)
        else:
            value_key = next(k for k in _COUNT_VALUE_KEYS if k in props)
            desc_key = next((k for k in props if "說明" in k), None)
            numeric = (props.get(value_key) or {}).get("type") in ("number", "integer")
            aligned = _aligned_count(current, target, value_key, desc_key, numeric)
        if aligned != current:
            _set_path(content, path, aligned)
            changed = True
    if changed:
        logger.info(f"[DerivativeAlignment] {section_id}: aligned to target {target}")
    return changed
