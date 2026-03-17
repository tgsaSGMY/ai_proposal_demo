# 生成 AI 執行履歷的 PDF，包含事件和對話記錄，並保持良好的排版和格式 （timeline render的東西生成pdf）。

from __future__ import annotations

from datetime import timezone, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

from fpdf import FPDF

from app.utils.timeline import parse_iso_timestamp

_FONT_PATH = Path(__file__).parent / "NotoSansTC-VariableFont_wght.ttf"
_FONT_NAME = "NotoSansTC"
_DEFAULT_FONT = "Helvetica"
_DEFAULT_TITLE = "AI 執行履歷"
_TAIWAN_TZ = timezone(timedelta(hours=8))

_EVENT_TYPE_LABELS = {
    "stored_answer_updated": "已更新答案",
    "plan_revision_started": "開始修訂計畫書名字",
    "plan_generation_started": "開始生成計畫書",
    "plan_generation_completed": "計畫書生成完成",
    "section_generated": "章節生成完成",
}


def _format_timestamp(raw_value: Any) -> str | None:
    parsed = parse_iso_timestamp(raw_value)
    if not parsed:
        return None
    dt = parsed
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(_TAIWAN_TZ)
    return dt.strftime("%Y-%m-%d %H:%M")


class TimelinePDF(FPDF):
    """Light wrapper to keep typography settings in one place."""

    def __init__(self, font_path: Path | None):
        super().__init__(orientation="P", unit="pt", format="A4")
        self.set_auto_page_break(auto=True, margin=40)
        self.set_margins(40, 40, 40)
        self.font_family = _DEFAULT_FONT
        self._register_font(font_path)
        self.add_page()

    def _register_font(self, font_path: Path | None) -> None:
        if not font_path:
            return
        try:
            if font_path.exists():
                self.add_font(_FONT_NAME, "", str(font_path), uni=True)
                self.font_family = _FONT_NAME
        except Exception as exc:
            print(f"Failed to register font: {exc}")

    def write_block(
        self,
        text: str,
        *,
        size: float,
        indent: float = 0,
        line_height: float | None = None,
        color: tuple[int, int, int] = (40, 40, 40),
        spacing: float = 2,
    ) -> None:
        if not text:
            return
        width = self.w - self.l_margin - self.r_margin - indent
        if width <= 0:
            width = self.w - self.l_margin - self.r_margin
        self.set_text_color(*color)
        self.set_font(self.font_family, size=size)
        self.set_x(self.l_margin + indent)
        resolved_line_height = line_height or size * 1.4
        self.multi_cell(width, resolved_line_height, str(text), border=0)
        if spacing:
            self.ln(spacing)


def _build_event_details(entry: Dict[str, Any]) -> List[str]:
    details: List[str] = []

    section_id = entry.get("section_id")
    if section_id:
        details.append(f"章節: {section_id}")

    payload = entry.get("payload") or {}
    if isinstance(payload, dict):
        model_id = payload.get("model_id")
        mode = payload.get("mode")
        answers_count = payload.get("answers_count")
        # if model_id:
        #     details.append(f"模型: {model_id}")
        # if mode:
        #     details.append(f"流程: {mode}")
        if answers_count is not None:
            details.append(f"已填欄位: {answers_count}")

        field_changes = payload.get("field_changes") or []
        if isinstance(field_changes, list):
            for change in field_changes:
                if isinstance(change, dict):
                    field_id = change.get("field_id")
                    old_value = change.get("old_value") or "空"
                    new_value = change.get("new_value")
                    if field_id:
                        details.append(f"欄位: {field_id}")
                        if old_value is not None:
                            details.append(f"原值: {old_value}")
                        if new_value is not None:
                            details.append(f"新值: {new_value}")


    external_sources = entry.get("external_sources") or []
    sources_collected: List[str] = []
    if isinstance(external_sources, list):
        for source in external_sources:
            if not isinstance(source, dict):
                continue
            label = source.get("title") or source.get("url")
            if label:
                sources_collected.append(str(label))
            if len(sources_collected) == 2:
                break
    if sources_collected:
        details.append(f"來源: {', '.join(sources_collected)}")

    return details


def _write_event_entry(pdf: TimelinePDF, entry: Dict[str, Any]) -> None:
    formatted_ts = _format_timestamp(entry.get("timestamp"))
    timestamp = formatted_ts or entry.get("timestamp", "--")
    event_type_key = entry.get("event_type") or "未知"
    event_type_label = _EVENT_TYPE_LABELS.get(event_type_key, event_type_key)
    header = f"[{timestamp}] 事件：{event_type_label}"
    pdf.write_block(header, size=11, line_height=16, color=(0, 92, 175), spacing=3)

    for line in _build_event_details(entry):
        pdf.write_block(line, size=9, indent=16, line_height=12, spacing=1.5)

    pdf.ln(4)


def _write_message_entry(pdf: TimelinePDF, entry: Dict[str, Any]) -> None:
    formatted_ts = _format_timestamp(entry.get("timestamp"))
    timestamp = formatted_ts or entry.get("timestamp", "--")
    role_label = "用戶" if entry.get("role") == "user" else "AI"
    header = f"[{timestamp}] 對話：{role_label}"
    pdf.write_block(header, size=11, line_height=16, color=(0, 92, 175), spacing=3)

    content = entry.get("content") or ""
    pdf.write_block(content, size=9, indent=16, line_height=12, spacing=2)
    pdf.ln(4)


def _extract_message_timestamp(entry: Dict[str, Any], fallback_idx: int) -> str:
    for key in ("timestamp", "created_at", "createdAt", "time"):
        value = entry.get(key)
        formatted = _format_timestamp(value)
        if formatted:
            return formatted
        if value:
            return str(value)
    return f"第{fallback_idx + 1}筆"


def _write_conversation_history(pdf: TimelinePDF, history: List[Dict[str, Any]] | None) -> None:
    normalized: List[Dict[str, str]] = []
    for idx, item in enumerate(history or []):
        if not isinstance(item, dict):
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        role_label = "用戶" if item.get("role") == "user" else "AI"
        timestamp = _extract_message_timestamp(item, idx)
        normalized.append({
            "timestamp": timestamp,
            "role_label": role_label,
            "content": content,
        })

    if not normalized:
        return

    pdf.ln(8)
    pdf.write_block("對話記錄", size=14, line_height=20, color=(30, 30, 30), spacing=6)

    for item in normalized:
        header = f"[{item['timestamp']}] 對話：{item['role_label']}"
        pdf.write_block(header, size=11, line_height=16, color=(0, 92, 175), spacing=3)
        pdf.write_block(item["content"], size=9, indent=16, line_height=12, spacing=2)
        pdf.ln(4)


def render_timeline_pdf(title: str, entries: List[Dict[str, Any]], conversation_history: List[Dict[str, Any]] | None = None) -> BytesIO:
    pdf = TimelinePDF(_FONT_PATH)

    pdf.write_block(title or _DEFAULT_TITLE, size=16, line_height=22, color=(20, 20, 20), spacing=6)

    for entry in entries:
        if entry.get("type") == "event":
            _write_event_entry(pdf, entry)
        else:
            _write_message_entry(pdf, entry)

    _write_conversation_history(pdf, conversation_history)

    raw_output = pdf.output(dest="S")
    pdf_bytes = raw_output.encode("latin1") if isinstance(raw_output, str) else bytes(raw_output)
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer
