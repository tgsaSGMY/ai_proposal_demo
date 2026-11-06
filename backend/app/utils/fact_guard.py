
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

Number = Union[int, float]


SENSITIVE_FIELD_PATTERNS: Dict[str, "re.Pattern[str]"] = {
    "amounts": re.compile(r"金額|經費|成本|預算|投資額|產值|營收|單價"),
    "identifiers": re.compile(r"統一編號|統編|專利號|專利名稱|認證名稱|獎項名稱"),
    "org_names": re.compile(r"公司名稱|機構名稱|客戶名稱|合作單位|委外廠商"),
    "company_stats": re.compile(r"員工人數|資本額|成立年份|上市櫃"),
    "ratios": re.compile(r"良率|市占率|成長率|毛利率|權重|比率"),
    "dates": re.compile(r"預定完成日期|起迄期間|設立月份|時程"),
}

VALID_TRUTH_LEVELS = ("A", "B", "C")

_LABEL_SEPARATORS = ("｜", "|")
_EXPLANATION_BRACKETS = re.compile(r"[【\[(（]")


def _field_title(field: Union[str, Dict[str, Any], None]) -> str:
    if not field:
        return ""
    if isinstance(field, str):
        text = field
    else:
        text = field.get("title") or field.get("label") or ""
        if not text:
            text = str(field.get("id") or "").split("::")[-1]
    for sep in _LABEL_SEPARATORS:
        text = text.split(sep)[-1]
    return _EXPLANATION_BRACKETS.split(text)[0].strip()


def matched_sensitive_groups(field: Union[str, Dict[str, Any], None]) -> List[str]:
    title = _field_title(field)
    return [name for name, pattern in SENSITIVE_FIELD_PATTERNS.items() if pattern.search(title)]


def get_truth_level(field: Union[str, Dict[str, Any], None]) -> str:
    if isinstance(field, dict):
        manual = field.get("truth_level")
        if isinstance(manual, str) and manual.strip().upper() in VALID_TRUTH_LEVELS:
            return manual.strip().upper()
    return "A" if matched_sensitive_groups(field) else "B"



_CN_DIGITS = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "兩": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}
_CN_SMALL_UNITS = {"十": 10, "百": 100, "千": 1000}
_CN_BIG_UNITS = {"萬": 10**4, "万": 10**4, "億": 10**8, "亿": 10**8}
_ARABIC_UNITS = {"億": 10**8, "亿": 10**8, "萬": 10**4, "万": 10**4, "千": 10**3, "百": 10**2}

_CN_DIGIT_CHARS = "".join(_CN_DIGITS)
_CN_CHARS = _CN_DIGIT_CHARS + "".join(_CN_SMALL_UNITS) + "".join(_CN_BIG_UNITS)
_TOKEN = re.compile(
    r"(?:民國|民国)\s*(?P<roc>\d{1,3})\s*年"
    r"|百分之\s*(?P<pct>[" + _CN_DIGIT_CHARS + r"十百千]+|\d+(?:\.\d+)?)"
    r"|(?P<num>\d{1,3}(?:,\d{3})+|\d+)(?P<frac>\.\d+)?\s*(?P<unit>[億亿萬万千百])?"
    r"|(?P<cn>[" + _CN_CHARS + r"]{2,})"
)


def _tidy(value: Decimal) -> Number:
    return int(value) if value == value.to_integral_value() else float(value)


def _parse_chinese_number(text: str, allow_short: bool = False) -> Optional[int]:
    has_unit = any(ch in _CN_SMALL_UNITS or ch in _CN_BIG_UNITS for ch in text)
    if not has_unit:
        if (allow_short or len(text) >= 3) and all(ch in _CN_DIGITS for ch in text):
            return int("".join(str(_CN_DIGITS[ch]) for ch in text))
        return None
    total = section = digit = 0
    for ch in text:
        if ch in _CN_DIGITS:
            digit = _CN_DIGITS[ch]
        elif ch in _CN_SMALL_UNITS:
            section += (digit or 1) * _CN_SMALL_UNITS[ch]
            digit = 0
        else:
            section += digit
            total += (section or 1) * _CN_BIG_UNITS[ch]
            section = digit = 0
    return total + section + digit


def extract_numbers(text: Any) -> List[Number]:
    if not isinstance(text, str) or not text:
        return []
    text = unicodedata.normalize("NFKC", text)
    numbers: List[Number] = []
    for match in _TOKEN.finditer(text):
        if match.group("roc"):
            numbers.append(int(match.group("roc")) + 1911)
        elif match.group("pct"):
            pct = match.group("pct")
            parsed = Decimal(pct) if pct[0].isdigit() else _parse_chinese_number(pct, allow_short=True)
            if parsed is not None:
                numbers.append(_tidy(Decimal(parsed)))
        elif match.group("num"):
            value = Decimal(match.group("num").replace(",", "") + (match.group("frac") or ""))
            unit = match.group("unit")
            numbers.append(_tidy(value * _ARABIC_UNITS[unit] if unit else value))
        else:
            parsed = _parse_chinese_number(match.group("cn"))
            if parsed is not None:
                numbers.append(parsed)
    return numbers


def normalize_number(text: Any) -> Optional[Number]:
    found = extract_numbers(text)
    return found[0] if found else None



NEEDS_REVIEW_NOTE = "AI 生成數值，未見於對話內容，請確認"

_LIST_MARKER = re.compile(r"(?m)^[ \t]*(?:[(]\d{1,2}[)]|\d{1,2}[.、)])[ \t]*")


def find_unsupported_numbers(value: Any, context_texts: List[str]) -> List[Number]:
    if not isinstance(value, str) or not value:
        return []
    known = set()
    for text in context_texts:
        known.update(extract_numbers(text))
    stated = unicodedata.normalize("NFKC", value)
    stated = _LIST_MARKER.sub("", stated)
    return [n for n in extract_numbers(stated) if n not in known]
