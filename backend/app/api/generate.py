# Demo generation endpoints: guided chat WebSocket, project-name
# recommendation, full-plan generation and plan revision.
#
# Ported from the parent platform's generate.py (create-proposal flow) and
# scoped to the anonymous demo session cookie instead of a logged-in user
# and project. Platform features that need an account — 我的背景資料 cards,
# 專屬背景資料 attachments, template entitlements, multi-window merge saves,
# per-user quotas — are intentionally left out. Demo caps (prompt count,
# token budget, one generation per session) are enforced here instead.

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect

from app.api.dependencies import (
    DEMO_SESSION_COOKIE_NAME,
    _coerce_uuid,
    require_demo_session_id,
    get_llm_service,
    get_supabase_service,
)
from app.config import (
    CHAT_GUIDANCE_JSON_MODE,
    DEMO_INTERACTION_LIMIT,
    DEMO_MAX_TOKENS_PER_SESSION,
    DEMO_REGISTER_REDIRECT_URL,
    FACT_GUARD_ENABLED,
    QUESTION_CONTROL_ENABLED,
)
from app.models import (
    ChatGuidanceOutput,
    GenerateRequest,
    PlanRevisionRequest,
    SectionGenerateResponse,
)
from app.services.llm_service import FactCheckError, LLMService, build_targets_block
from app.services.prompt_registry_service import FALLBACK_CHAT_GUIDANCE_PROMPT
from app.services.question_loader_service import load_template_questions
from app.services.supabase_service import SupabaseService
from app.utils.answer_normalizer import (
    answer_text,
    build_entries,
    extract_chat_answer_entries,
    flatten_answers,
    serialize_entries,
)
from app.utils.derivative_alignment import align_derivatives, parse_derivative_target
from app.utils.extract_json import extract_json_block
from app.utils.fact_guard import NEEDS_REVIEW_NOTE, find_unsupported_numbers, get_truth_level
from app.utils.feature_models import get_feature_model, get_feature_override
from app.utils.formatting import format_section_output
from app.utils.question_logic import (
    compute_applicable_questions,
    compute_next_question_id,
    compute_progress,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Generation"])

AUTOFILL_USER_MESSAGE = "請AI自動幫我填寫"
# 側邊欄「重新生成」按鈕代發的訊息前綴，格式：請AI重新生成\n{label}（{field_id}）
REGENERATE_USER_PREFIX = "請AI重新生成"
# 進入對話時系統代發的開場訊息；使用者尚未回答任何問題，此回合不可寫入欄位
GREETING_USER_MESSAGE = "（用户刚进入，请根据项目名称和項目描述开始引导）"

HIDDEN_REPLY_BLOCK_PATTERN = re.compile(
    r"【回復結束】【隱藏回復欄位\+答案】(.*?)【隱藏回復結束】",
    re.DOTALL,
)
RESPONSE_END_MARKER = "【回復結束】"

# field_updates 的內容會直接進入送審的計畫書，於程式端附加，不依賴 DB 範本
# （Demo 沒有背景資料與附件，規則只以使用者提供的內容為依據）
FIELD_UPDATE_WRITING_RULES = """

    【field_updates 內容寫法】
    - field_updates 的內容會直接寫入送審的計畫書，只能寫計畫書內容本身，不可使用 Markdown 粗體符號（**）。
    - 不可提及資料來源（如「依對話內容」、「使用者未提供」）；缺少的資訊直接寫「尚未取得」或「待決定」。
    - 金額與數量（產值、營收、投資額、成本、經費、就業人數、新公司數、專利數等）若使用者沒有提供，一律填「待決定」（如「增加產值：待決定」），不可填 0、OOO，也不可自行估算。
    - 只有使用者明確寫出完成性字眼（如已完成、已取得、已上線、已導入）的事項，才能寫成已完成；其他一律以「預計」、「將」、「規劃」等語氣撰寫，不可自行寫出「已完成…」。
    - 不可在欄位內容中對使用者說話或提供建議、提醒（如「若需可協助…」、「請補充…」）；這類話請放在 reply_intro 或 reply_outro。
    """

# 平台版此規則附在「我的背景資料」段落中；Demo 沒有背景資料，只保留 AI 自動填寫規則
AUTOFILL_RULES = """

    【AI 自動填寫】
    - 若使用者要求 AI 自動填寫（例如「請AI自動幫我填寫」），只為目前這一題（系統指定的下一題）擬寫內容並放入 field_updates，不可填寫其他待填欄位，也不可聲稱已補齊全部欄位；依對話與專案內容合理擬定（系統會自動標記需使用者確認）。填完後照常進入下一題。
    """


# ---------------------------------------------------------------------------
# Chat helpers (ported from the platform)
# ---------------------------------------------------------------------------

def extract_hidden_field_responses(text: Optional[str]) -> Dict[str, str]:
    # 從 LLM 回應中提取隱藏欄位的值（舊版標記格式）
    if not text:
        return {}
    match = HIDDEN_REPLY_BLOCK_PATTERN.search(text)
    if not match:
        return {}
    extracted: Dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip().lstrip("-").strip()
        if not line or " -- " not in line:
            continue
        field_id, value = line.split(" -- ", 1)
        field_key = field_id.strip()
        if field_key:
            extracted[field_key] = value.strip()
    return extracted


async def _parse_chat_guidance_output(
    raw_text: str,
    llm_service: LLMService,
    client: httpx.AsyncClient,
    model_info: Dict,
    repair_model_info: Optional[Dict] = None,
    supabase_service: Optional[SupabaseService] = None,
    session_id: Optional[str] = None,
) -> Tuple[Optional[ChatGuidanceOutput], Optional[str]]:
    if not raw_text:
        return None, None

    parsed: Optional[Dict[str, Any]] = None
    ladder_rung: Optional[str] = None

    try:
        parsed = json.loads(raw_text)
        ladder_rung = "json.loads"
    except json.JSONDecodeError:
        pass

    if parsed is None:
        extracted, _err = extract_json_block(raw_text, section_id="chat_guidance")
        if extracted is not None:
            parsed = extracted
            ladder_rung = "extract_json_block"

    if parsed is None:
        # 功能模型配置有指定「修正 AI 回覆格式」的模型時使用該模型，否則沿用對話模型
        repaired, _err = await llm_service._attempt_json_repair(
            raw_text,
            client,
            repair_model_info or model_info,
            section_id="chat_guidance",
            supabase_service=supabase_service,
            demo_session_id=session_id,
            action="生成對話(JSON修復)",
        )
        if repaired is not None:
            parsed = repaired
            ladder_rung = "_attempt_json_repair"

    if parsed is None:
        return None, None

    try:
        output = ChatGuidanceOutput.model_validate(parsed)
    except Exception as ve:
        logger.warning(f"ChatGuidanceOutput validation failed (rung={ladder_rung}): {ve}")
        return None, None

    return output, ladder_rung


def _build_fact_context(
    history_records: List[Dict[str, Any]],
    project_title: str,
    project_summary: str,
    current_answers: Dict[str, Any],
    ai_field_ids: set,
) -> List[str]:
    texts = [project_title, project_summary]
    for record in history_records:
        if isinstance(record, dict) and record.get("role") == "user":
            texts.append(str(record.get("content") or ""))
    for field_id, value in current_answers.items():
        if field_id not in ai_field_ids:
            texts.append(str(value or ""))
    return [text for text in texts if text]


def _tag_ai_filled_fields(
    clean_filled: Dict[str, Any],
    current_answers: Dict[str, Any],
    answer_provenance: Dict[str, Dict[str, Any]],
    all_questions: Optional[List[Dict[str, Any]]] = None,
    fact_context: Optional[List[str]] = None,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    questions_by_id = {q.get("id"): q for q in (all_questions or [])}
    sources: Dict[str, str] = {}
    review_notes: Dict[str, str] = {}
    for field_id, value in clean_filled.items():
        if str(current_answers.get(field_id) or "").strip() == str(value or "").strip():
            continue
        tag: Dict[str, Any] = {"source": "ai_generated"}
        question = questions_by_id.get(field_id)
        if (
            fact_context is not None
            and question is not None
            and get_truth_level(question) == "A"
            and find_unsupported_numbers(str(value or ""), fact_context)
        ):
            tag["needs_review"] = True
            tag["review_note"] = NEEDS_REVIEW_NOTE
            review_notes[field_id] = NEEDS_REVIEW_NOTE
        answer_provenance[field_id] = tag
        sources[field_id] = "ai_generated"
    return sources, review_notes


def _unfill_stale_placeholders(
    all_questions: List[Dict[str, Any]],
    applicable_questions: List[Dict[str, Any]],
    current_answers: Dict[str, Any],
    current_answer_meta: Dict[str, Dict[str, str]],
    answer_provenance: Dict[str, Dict[str, Any]],
    saved_entries: Dict[str, Any],
    cleared_placeholders: Dict[str, str],
) -> List[str]:
    applicable_ids = {q.get("id") for q in applicable_questions}
    cleared: List[str] = []
    for q in all_questions:
        qid = q.get("id")
        if not qid or qid not in applicable_ids or not q.get("skip_condition"):
            continue
        placeholder = q.get("skip_output_text") or "（本項免填）"
        if str(current_answers.get(qid) or "").strip() != placeholder.strip():
            continue
        saved = saved_entries.get(qid)
        is_estimate = (answer_provenance.get(qid) or {}).get("source") == "system_estimate" or (
            saved is not None and saved.source == "system_estimate"
        )
        if not is_estimate:
            continue
        current_answers.pop(qid, None)
        current_answer_meta.pop(qid, None)
        answer_provenance.pop(qid, None)
        cleared_placeholders[qid] = placeholder
        cleared.append(qid)
    return cleared


def _fill_skip_placeholders(
    all_questions: List[Dict[str, Any]],
    applicable_questions: List[Dict[str, Any]],
    current_answers: Dict[str, Any],
    current_answer_meta: Dict[str, Dict[str, str]],
    answer_provenance: Dict[str, Dict[str, Any]],
) -> None:
    # Rule-skipped fields read as answered everywhere downstream (the
    # "已填" prompt block, generation/export) instead of blank or
    # model-invented filler.
    applicable_ids = {q.get("id") for q in applicable_questions}
    for q in all_questions:
        qid = q.get("id")
        if not qid or qid in applicable_ids:
            continue
        placeholder = q.get("skip_output_text") or "（本項免填）"
        existing = current_answers.get(qid)
        if not existing:
            current_answers[qid] = placeholder
            touch_meta_field(current_answer_meta, qid)
            existing = placeholder
        if FACT_GUARD_ENABLED and str(existing).strip() == placeholder.strip():
            answer_provenance[qid] = {"source": "system_estimate"}


def _drop_model_writes_to_skipped_fields(
    clean_filled: Dict[str, Any],
    prior_state: Dict[str, Tuple[Any, Any, Any]],
    skipped_ids: set,
    current_answers: Dict[str, Any],
    current_answer_meta: Dict[str, Dict[str, str]],
    answer_provenance: Dict[str, Dict[str, Any]],
    sources: Dict[str, str],
    review_notes: Dict[str, str],
) -> List[str]:
    """Undo this turn's model writes to fields that are now rule-skipped.

    Only model output is dropped: each field is restored to what it held
    before this turn, so a real user answer is never replaced.
    """
    dropped = [fid for fid in clean_filled if fid in skipped_ids]
    for fid in dropped:
        prev_value, prev_meta, prev_source = prior_state.get(fid, (None, None, None))
        for store, prev in (
            (current_answers, prev_value),
            (current_answer_meta, prev_meta),
            (answer_provenance, prev_source),
        ):
            if prev is None:
                store.pop(fid, None)
            else:
                store[fid] = prev
        clean_filled.pop(fid, None)
        sources.pop(fid, None)
        review_notes.pop(fid, None)
    return dropped


def _restrict_autofill_to_target(clean_filled: Dict[str, Any], target_id: Optional[str]) -> List[str]:
    """Keep only the current question's write on an autofill turn."""
    if not target_id:
        return []
    dropped = [fid for fid in clean_filled if fid != target_id]
    for fid in dropped:
        clean_filled.pop(fid, None)
    return dropped


def _parse_regenerate_target(user_msg: str, questions: List[Dict[str, Any]]) -> Optional[str]:
    """Return the field id a sidebar 重新生成 message targets, or None.

    The id must be a real question id; the longest match wins so an id that
    is a prefix of another one never steals the turn.
    """
    text = (user_msg or "").strip()
    if not text.startswith(REGENERATE_USER_PREFIX):
        return None
    matches = [q.get("id") for q in questions if q.get("id") and q.get("id") in text]
    if not matches:
        return None
    return max(matches, key=len)


def _build_regenerate_block(target_id: str, next_q_label: str) -> str:
    return f"""

    【本回合：重新生成欄位（優先於上方所有關於 AI 自動填寫「目前這一題」的規則）】
    使用者按下「重新生成」，要求 AI 重新撰寫已填欄位：{target_id}
    - 只為這一個欄位擬寫新內容並放入 field_updates，欄位 ID 必須完全是 {target_id}；不可填寫或修改其他任何欄位。
    - 以該欄位目前內容與對話為依據，改寫得更完整、具體、可送件；不可捏造上述資料未記載的數字、獎項、專利或客戶名稱。
    - 在回覆開頭（reply_intro）簡短說明已重新生成該欄位（可摘要新內容重點），不要重新詢問這一題。
    - 之後照常繼續詢問下一題：{next_q_label}
    """


async def _apply_legacy_hidden_markers(
    raw_text: str,
    all_questions: list,
    current_answers: Dict[str, Any],
    current_answer_meta: Dict[str, Dict[str, str]],
    websocket: WebSocket,
    autofill_turn: bool = False,
    answer_provenance: Optional[Dict[str, Dict[str, Any]]] = None,
    fact_context: Optional[List[str]] = None,
    autofill_target_id: Optional[str] = None,
    greeting_turn: bool = False,
    require_markers: bool = False,
) -> str:
    # JSON 模式的備援：沒有舊版標記代表這不是舊格式回覆，而是解析失敗的 JSON，
    # 不可原文回傳給使用者（否則原始 JSON 會直接顯示在聊天中）
    if require_markers and RESPONSE_END_MARKER not in (raw_text or ""):
        return ""
    hidden_answers = extract_hidden_field_responses(raw_text)
    if hidden_answers and greeting_turn:
        logger.info(f"Dropped field writes on the greeting turn: {list(hidden_answers)}")
    elif hidden_answers:
        clean_filled = normalize_filled_fields(hidden_answers, all_questions)
        if autofill_turn:
            dropped = _restrict_autofill_to_target(clean_filled, autofill_target_id)
            if dropped:
                logger.info(f"Dropped autofill writes outside the current question: {dropped}")
        sources: Dict[str, str] = {}
        review_notes: Dict[str, str] = {}
        if autofill_turn and answer_provenance is not None:
            sources, review_notes = _tag_ai_filled_fields(
                clean_filled, current_answers, answer_provenance, all_questions, fact_context
            )
        current_answers.update(clean_filled)
        for field_id in clean_filled.keys():
            touch_meta_field(current_answer_meta, field_id)
        filled_payload: Dict[str, Any] = {"event": "filled", "data": clean_filled}
        if sources:
            filled_payload["sources"] = sources
        if review_notes:
            filled_payload["needs_review"] = review_notes
        await websocket.send_json(filled_payload)

    return HIDDEN_REPLY_BLOCK_PATTERN.sub("", raw_text).replace(RESPONSE_END_MARKER, "").strip()


def _get_current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_history_entry(role: str, content: str) -> Dict[str, Any]:
    return {
        "id": f"{role}-{uuid4().hex[:8]}",
        "role": role,
        "type": "text",
        "content": content,
        "timestamp": _get_current_timestamp(),
    }


def normalize_meta_payload(meta_payload: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    normalized: Dict[str, Dict[str, str]] = {}
    if not isinstance(meta_payload, dict):
        return normalized
    for field_id, raw in meta_payload.items():
        if not field_id:
            continue
        timestamp = ""
        if isinstance(raw, str):
            timestamp = raw.strip()
        elif isinstance(raw, dict):
            value = raw.get("updated_at") or raw.get("updatedAt")
            if isinstance(value, str):
                timestamp = value.strip()
        if timestamp:
            normalized[field_id] = {"updated_at": timestamp}
    return normalized


def touch_meta_field(meta_map: Dict[str, Dict[str, str]], field_id: str, timestamp: Optional[str] = None) -> None:
    if not field_id:
        return
    final_timestamp = (timestamp or _get_current_timestamp()).strip()
    if not final_timestamp:
        return
    existing = meta_map.get(field_id) or {}
    meta_map[field_id] = {**existing, "updated_at": final_timestamp}


def normalize_filled_fields(filled_data: dict, all_questions: list) -> dict:
    """Map LLM-extracted field keys (often labels) onto canonical question IDs.

    Tolerates whitespace differences and explanatory-parenthetical suffixes
    in the original labels.
    """
    fingerprint_map: Dict[str, str] = {}
    split_pattern = r"[【\[(（]"

    for q in all_questions:
        real_id = q.get("id")
        label = q.get("label")
        if not real_id:
            continue
        fingerprint_map[real_id.replace(" ", "")] = real_id
        if label:
            clean_label = label.replace(" ", "")
            fingerprint_map[clean_label] = real_id
            short_label = re.split(split_pattern, label)[0].replace(" ", "")
            if short_label and short_label != clean_label:
                fingerprint_map[short_label] = real_id

    normalized: Dict[str, Any] = {}
    for key, value in filled_data.items():
        # 欄位值不保留 Markdown 粗體符號（提示詞要求回覆用粗體，模型常帶進欄位值）
        if isinstance(value, str):
            value = value.replace("**", "")
        clean_key = key.replace("::reply", "").strip()
        key_fingerprint = clean_key.replace(" ", "")
        if key_fingerprint in fingerprint_map:
            normalized[fingerprint_map[key_fingerprint]] = value
            continue
        short_key = re.split(split_pattern, key_fingerprint)[0]
        if short_key in fingerprint_map:
            normalized[fingerprint_map[short_key]] = value
        else:
            logger.warning("Field mismatch: '%s' maps to nothing. Kept original.", key)
            normalized[clean_key] = value
    return normalized


# 「還剩 N 題」等剩餘題數敘述；N 由模型自行敘述常常算錯，改用後端計算的數字取代
_REMAINING_COUNT_PATTERN = re.compile(
    r"(還剩下?|剩下|剩餘|尚餘|尚有|還有|僅剩|只剩|剩)(\s*)(\d+|[零一二兩三四五六七八九十]+)(\s*)(個問題|道題|題)"
)


def _correct_remaining_count(text: str, remaining: int) -> str:
    if not text:
        return text
    return _REMAINING_COUNT_PATTERN.sub(
        lambda m: f"{m.group(1)}{m.group(2)}{remaining}{m.group(4)}{m.group(5)}", text
    )


def _question_prompt_text(q: Optional[dict]) -> str:
    """Prompt text for one question, whichever list it came from: DB-loaded
    questions use `prompt_text`; the client-supplied list uses `prompt`."""
    if not q:
        return ""
    return q.get("prompt_text") or q.get("prompt") or q.get("label") or ""


def format_qa_descriptions(all_questions, current_answers):
    answer_lookup: Dict[str, Any] = {}
    for k, v in current_answers.items():
        if not v or not str(v).strip():
            continue
        answer_lookup[k] = v
        clean_k = k.replace("::reply", "")
        answer_lookup[clean_k] = v
        answer_lookup[clean_k.replace(" ", "")] = v

    answered_list: List[str] = []
    unanswered_list: List[Dict[str, Any]] = []

    for q in all_questions:
        qid = q.get("id") or ""
        label = q.get("label", qid) or qid
        qid_no_space = qid.replace(" ", "")
        label_no_space = label.replace(" ", "")

        val = (
            answer_lookup.get(qid)
            or answer_lookup.get(qid_no_space)
            or answer_lookup.get(label)
            or answer_lookup.get(label_no_space)
        )
        if val:
            val_str = str(val).strip()
            display_val = val_str[:100] + "..." if len(val_str) > 100 else val_str
            # 同時顯示 ID 與 Label：修改已填欄位時，模型需複製真實 ID 回傳 field_updates
            answered_list.append(f"- {qid}（{label}）: {display_val}")
        else:
            unanswered_list.append(q)

    questions_desc = "\n".join(
        f"- {q.get('id', q.get('label'))}: {_question_prompt_text(q)}" for q in all_questions
    )
    answered_desc = "\n".join(answered_list) or "（無）"
    unanswered_desc = "\n".join(f"- {q.get('id', q.get('label'))}" for q in unanswered_list) or "（全部已填）"
    return questions_desc, answered_desc, unanswered_desc, unanswered_list


def get_chat_messages(system_prompt: str, history_records: list, last_user_msg: Optional[str] = None, limit: int = 10):
    messages = [{"role": "system", "content": system_prompt}]
    start_index = max(0, len(history_records) - limit)
    subset_history = history_records[start_index:]
    if last_user_msg and subset_history and subset_history[-1].get("content") == last_user_msg:
        subset_history = subset_history[:-1]
    for h in subset_history:
        role = h.get("role", "user")
        content = h.get("content", "")
        if role in ("user", "assistant", "system"):
            messages.append({"role": role, "content": content})
    if last_user_msg:
        messages.append({"role": "user", "content": last_user_msg})
    return messages


def _resolve_session_id_from_websocket(websocket: WebSocket) -> Optional[str]:
    """Read the demo_session_id either from the cookie (browsers send it) or
    from the ?session_id=... query param (useful for testing tools)."""
    cookie_value = websocket.cookies.get(DEMO_SESSION_COOKIE_NAME)
    if cookie_value:
        coerced = _coerce_uuid(cookie_value)
        if coerced:
            return coerced
    qp_value = websocket.query_params.get("session_id")
    return _coerce_uuid(qp_value)


# ---------------------------------------------------------------------------
# Guided chat WebSocket
# ---------------------------------------------------------------------------

@router.websocket("/ws/chat_guidance")
async def websocket_chat_guidance(websocket: WebSocket):
    """Stream the guided-fill chat for a single demo session.

    The handshake expects the visitor's demo_session_id cookie (minted on
    any prior HTTP request). The session row in `ai_proposal_platform.demo`
    holds the conversation_history, stored_answer, and interaction_count.
    Once the interaction count hits DEMO_INTERACTION_LIMIT we send a
    `limit_reached` event so the frontend can prompt registration.
    """
    await websocket.accept()

    session_id = _resolve_session_id_from_websocket(websocket)
    if not session_id:
        await websocket.send_json({
            "event": "error",
            "message": "missing demo_session_id cookie — open the demo page first to mint one",
        })
        await websocket.close()
        return

    supabase_service = getattr(websocket.app.state, "supabase_service", None)
    if supabase_service is None:
        await websocket.send_json({"event": "error", "message": "supabase unavailable"})
        await websocket.close()
        return

    llm_service: LLMService = websocket.app.state.llm_service
    model_info = get_feature_model(websocket.app.state, "chat_guidance", True) or {
        "id": "chat-latest",
        "provider": "openai",
        "type": "external",
        "cost_info": {"input": 5.0, "output": 30.0},
    }
    repair_model_info = get_feature_override(websocket.app.state, "json_repair", True)

    conversation_history_records: List[Dict[str, Any]] = []
    stored_answer_state: Dict[str, Any] = {}
    current_answers: Dict[str, Any] = {}
    current_answer_meta: Dict[str, Dict[str, str]] = {}
    answer_provenance: Dict[str, Dict[str, Any]] = {}
    cleared_placeholders: Dict[str, str] = {}
    all_questions: List[Dict[str, Any]] = []
    project_title = ""
    project_summary = ""
    grant_name = ""

    demo_row = await supabase_service.get_demo_session(session_id) or {}
    interaction_count = int(demo_row.get("interaction_count") or 0)

    async def save_state_to_db():
        prior_entries = extract_chat_answer_entries(stored_answer_state)
        previous_answers = {field_id: entry.value for field_id, entry in prior_entries.items()}
        previous_snapshot = json.dumps(previous_answers, ensure_ascii=False, sort_keys=True)
        current_snapshot = json.dumps(flatten_answers(current_answers), ensure_ascii=False, sort_keys=True)
        answers_changed = previous_snapshot != current_snapshot
        unsaved_state = {key: stored_answer_state.get(key) for key in ("chat_answers", "chat_answers_meta")}

        if FACT_GUARD_ENABLED:
            stored_answer_state["chat_answers"] = serialize_entries(
                build_entries(current_answers, prior_entries, current_answer_meta, answer_provenance)
            )
        else:
            stored_answer_state["chat_answers"] = current_answers.copy()
        stored_answer_state["chat_answers_meta"] = {
            key: (value.copy() if isinstance(value, dict) else value)
            for key, value in current_answer_meta.items()
        }

        save_failed = False
        for attempt in range(3):
            try:
                await supabase_service.update_demo_session(
                    session_id,
                    {
                        "conversation_history": conversation_history_records,
                        "stored_answer": stored_answer_state,
                    },
                )
                save_failed = False
                break
            except Exception:
                save_failed = True
                if attempt < 2:
                    logger.warning("Demo session %s save attempt %d/3 failed, retrying...", session_id, attempt + 1, exc_info=True)
                    await asyncio.sleep(0.5 * (attempt + 1))
                else:
                    logger.exception("Demo session %s save failed after 2 retries", session_id)

        if save_failed:
            # 還原成上次存檔的狀態，下次存檔才會重送這次沒存進去的變動
            for key, value in unsaved_state.items():
                if value is None:
                    stored_answer_state.pop(key, None)
                else:
                    stored_answer_state[key] = value
            try:
                await websocket.send_json({
                    "event": "error",
                    "message": "答案儲存失敗，請重新傳送訊息或稍後再試。",
                })
            except Exception:
                pass
            return

        # Provenance now lives in the saved entries (build_entries keeps it).
        answer_provenance.clear()
        saved_answers = flatten_answers(current_answers)

        # Buffer a timeline event whenever answers diff — the parent
        # platform's AI Timeline view will replay these on claim.
        if answers_changed:
            try:
                field_changes: List[Dict[str, Any]] = []
                for field_id in sorted(set(previous_answers.keys()) | set(saved_answers.keys())):
                    old_val = previous_answers.get(field_id, "")
                    new_val = saved_answers.get(field_id, "")
                    if old_val == new_val:
                        continue
                    field_label = next(
                        (q.get("label", field_id) for q in all_questions if q.get("id") == field_id),
                        field_id,
                    )
                    field_changes.append({
                        "field_id": field_id,
                        "field_label": field_label,
                        "old_value": old_val,
                        "new_value": new_val,
                        "change": f"{field_label}：《{old_val}》→《{new_val}》",
                    })
                await supabase_service.append_demo_execution_event(
                    session_id,
                    "stored_answer_updated",
                    {
                        "answers_count": len(saved_answers),
                        "field_changes": field_changes,
                        "changes_summary": " | ".join(c["change"] for c in field_changes),
                    },
                )
            except Exception as exc:
                logger.error("Failed to log stored_answer_updated for demo session %s: %s", session_id, exc)

    async def stream_ai_reply(
        user_msg: str,
        history: list,
        client: httpx.AsyncClient,
        paused_flag: dict,
    ) -> str:
        regenerate_target_id = _parse_regenerate_target(user_msg, all_questions)
        autofill_turn = FACT_GUARD_ENABLED and (
            user_msg.strip() == AUTOFILL_USER_MESSAGE or regenerate_target_id is not None
        )
        greeting_turn = user_msg.strip() == GREETING_USER_MESSAGE

        fact_context: Optional[List[str]] = None
        if autofill_turn:
            ai_field_ids = {
                field_id
                for field_id, entry in extract_chat_answer_entries(stored_answer_state).items()
                if entry.source in ("ai_generated", "system_estimate")
            } | {
                field_id for field_id, tag in answer_provenance.items()
                if tag.get("source") == "ai_generated"
            }
            fact_context = _build_fact_context(
                conversation_history_records, project_title, project_summary,
                current_answers, ai_field_ids,
            )

        # The DB-loaded question list is the control source when
        # QUESTION_CONTROL_ENABLED — applicability/next-question/progress are
        # backend-computed facts, not model-narrated prose.
        applicable_questions = all_questions
        if QUESTION_CONTROL_ENABLED:
            applicable_questions = compute_applicable_questions(all_questions, current_answers)

            cleared_ids: List[str] = []
            if FACT_GUARD_ENABLED:
                saved_entries = extract_chat_answer_entries(stored_answer_state)
                while True:
                    newly_cleared = _unfill_stale_placeholders(
                        all_questions, applicable_questions, current_answers,
                        current_answer_meta, answer_provenance, saved_entries,
                        cleared_placeholders,
                    )
                    if not newly_cleared:
                        break
                    cleared_ids.extend(newly_cleared)
                    applicable_questions = compute_applicable_questions(all_questions, current_answers)
                if cleared_ids:
                    await websocket.send_json({
                        "event": "cleared",
                        "data": cleared_ids,
                        "applicable_questions": [q.get("id") for q in applicable_questions],
                    })

            _fill_skip_placeholders(
                all_questions, applicable_questions, current_answers,
                current_answer_meta, answer_provenance,
            )

        _, a_desc, ua_desc, ua_list = format_qa_descriptions(all_questions, current_answers)

        if QUESTION_CONTROL_ENABLED:
            next_question_id = compute_next_question_id(applicable_questions, current_answers)
            next_question = next(
                (q for q in applicable_questions if q.get("id") == next_question_id), None
            )
        else:
            next_question = ua_list[0] if ua_list else None
        autofill_target_id = regenerate_target_id or (next_question.get("id") if next_question else None)
        next_q_label = (next_question.get("id") or next_question.get("label")) if next_question else "（请检查是否还有未填项）"
        next_q_prompt_text = _question_prompt_text(next_question) if next_question else ""

        proj_title_label = project_title or "(未提供專案名稱)"
        proj_summary_label = project_summary or "(未提供專案摘要)"

        if QUESTION_CONTROL_ENABLED:
            progress = compute_progress(applicable_questions, current_answers)
            total_questions = progress["total"]
            unanswered_count = total_questions - progress["answered"]
            answered_percent = progress["percent"]
        else:
            unanswered_count = len(ua_list)
            total_questions = len(all_questions)
            answered_count = total_questions - unanswered_count
            answered_percent = round((answered_count / total_questions) * 100) if total_questions else 0
        all_questions_answered = unanswered_count == 0
        next_question_id_display = next_q_label if not all_questions_answered else "null"

        if not CHAT_GUIDANCE_JSON_MODE:
            system_prompt = f"""
    你是一位友善的專案規劃助理，正在協助使用者填寫【{grant_name}】。

    專案名稱：{proj_title_label}
    專案摘要：{proj_summary_label}

    【目前系統記錄狀態】
    (可能略有延遲，請以最新對話為準)
    已填（Do NOT ask these）：{a_desc}
    待填：{ua_desc}
    尚未填寫題數：{unanswered_count} 題
    總題數：{len(all_questions)} 題
    完成百分比：{len(a_desc.splitlines())} / {len(all_questions)}

    【重要規則】
    只負責幫忙填寫和完善欄位至可送件水準，不負責生成完整計畫書文本。
    絕對禁止重複詢問【已填資料】中的欄位。
    若【已填資料】中已有內容，請直接根據這些內容，詢問【待填欄位】中的下一項。
    你的首要目標是推進進度，直接引導至：{next_q_label}
    若用戶想要強調，或重新更新已填欄位，不要阻擋使用者，而是幫助用戶完善該欄位內容。
    如果現在詢問的是商業模式運作流程, 模型一定要舉出這個示例幫助用戶理解問題：“客戶登入→使用平台→取得反饋→改良產品→行銷推廣”,示例流程只是幫用戶理解問題，不是答案本身，答案還是要根據用戶的實際情況來回答。

    【欄位説明】
    若從上下文分析這專案無硬體需求，在"硬體標的規格"欄位能夠不詢問，提醒用戶類似“根據分析，此專案無硬體需求，因此欄位已自動填寫”，然後自動跳下一題。
    創新性既有流程說明，直接切入流程說明，不需要再確認痛點。

    【任務】
    回應使用者的最新輸入。若使用者提供了資訊，請進行確認或摘要（例如：「好的，已記錄……」）。
    摘要或者幫忙填寫的欄位内容請確保在一個段落以内，不要列點導致太長。
    若使用者剛剛回答了某個【待填】問題，請自然地接續詢問下一個欄位：{next_q_label}。
    若使用者的回答不清楚，請不需要直接詢問下一個欄位，先進一步追問以釐清。
    每詢問一個問題的時候，可以根據上下文生成建議性的答案輔助用戶。
    需要使用鼓勵方式，并且需要補充說目前還剩多少題未完成，讓用戶不那麽快放棄。
    在全部問題都回答完畢之後，看系統記錄的“已填”選項。一次過列出來所有“無”，“等下填寫”，“空”之類的答案的欄位，并且建議用戶填寫他們以優化計畫書內容。
    完成後，推薦用戶點擊右下角的「輸出完整推演」按鈕來產出完整計畫書文本，不需要推薦幫忙其他東西了，因爲你負責的是完善欄位，而這時候你的任務完成了。

    【隱藏回復欄位格式】
    - 當你確認某個欄位已完成或你代為生成了內容或優化內容時，請在可見回覆結束後追加一段隱藏資訊，必須要和你回復用戶的資訊一摸一樣。
    - 不需要畫分割綫，首行輸出 `【回復結束】【隱藏回復欄位+答案】`，末行輸出 `【隱藏回復結束】`。
    - 隱藏段落中每行輸出 `欄位ID -- 答案內容`（用雙空格加連字號來分隔），可列出多個欄位。
    - 欄位 ID 請使用系統提供的問題 ID（例如 三、解決辦法::商業模式運作流程），不要自行取名。
    - 這些標記只供系統讀取，前端會自動隱藏，因此務必正確輸出。

    【排版】
    排版不要那麽鬆散，盡量維持緊凑。
    如果是重點内容/副標題，請使用「粗體」標記。
    爲了讓用戶能夠直觀理解内容，你可以參考如下回復模板：**完成欄位確認**（如果有）-> **還剩幾題**（并且包含鼓勵語句）->**下一題問題**->💡**填寫小提醒** （指導該填什麽/給範例建議）。
    這個回復模板是參考，你也可以自由發展，重點是要自然語言和能夠直觀理解哪裏是重點
    只有填寫小提醒會有💡,其他的不要有icon
    在講述還剩几題的時候，需要使用一條長橫綫分隔來區分還剩几題和下一題的題目。


    注意：請根據對話歷史流暢回應。即使系統顯示某欄位為「待填」，只要使用者剛剛在對話中已回答，請視為已填並繼續流程。
    """
        else:
            prompt_vars = {
                "grant_name": grant_name,
                "proj_title_label": proj_title_label,
                "proj_summary_label": proj_summary_label,
                "a_desc": a_desc,
                "ua_desc": ua_desc,
                "next_question_id_display": next_question_id_display,
                "unanswered_count": unanswered_count,
                "total_questions": total_questions,
                "answered_percent": answered_percent,
                "all_questions_answered_label": "是" if all_questions_answered else "否",
                "next_q_label": next_q_label,
                "next_q_prompt_text_display": next_q_prompt_text or "（無，所有題目已完成）",
            }
            model_id = model_info.get("id") if model_info else None
            prompt_template = await websocket.app.state.prompt_registry_service.get_active_prompt(
                "chat_guidance", model_id
            )
            try:
                system_prompt = prompt_template.format(**prompt_vars)
            except (KeyError, IndexError, ValueError):
                logger.exception(
                    "chat_guidance prompt_templates row failed to .format(); "
                    "falling back to FALLBACK_CHAT_GUIDANCE_PROMPT."
                )
                system_prompt = FALLBACK_CHAT_GUIDANCE_PROMPT.format(**prompt_vars)

        system_prompt += AUTOFILL_RULES
        system_prompt += FIELD_UPDATE_WRITING_RULES
        if regenerate_target_id:
            system_prompt += _build_regenerate_block(
                regenerate_target_id,
                next_q_label if not all_questions_answered
                else "（所有題目已完成，請提醒使用者可點擊「輸出完整推演」）",
            )

        messages = get_chat_messages(system_prompt, history, last_user_msg=user_msg, limit=10)

        await websocket.send_json({"event": "chunk_start"})

        if not CHAT_GUIDANCE_JSON_MODE:
            full_response: List[str] = []
            try:
                async for chunk in llm_service.stream_external_api(client, model_info, messages):
                    if paused_flag.get("value"):
                        try:
                            await websocket.send_json({
                                "event": "cancelled",
                                "restore_user_message": user_msg,
                                "message": "stream_cancelled_by_user",
                            })
                        except Exception:
                            pass
                        return ""
                    if chunk:
                        full_response.append(chunk)
                        await websocket.send_json({"event": "chunk", "data": chunk})

                raw_text = "".join(full_response).strip()
                visible_text = await _apply_legacy_hidden_markers(
                    raw_text, all_questions, current_answers, current_answer_meta, websocket,
                    autofill_turn, answer_provenance, fact_context, autofill_target_id,
                    greeting_turn=greeting_turn,
                )
                await websocket.send_json({"event": "done"})
                return visible_text or raw_text
            except Exception as exc:
                logger.error("Stream error: %s", exc)
                await websocket.send_json({"event": "error", "message": str(exc)})
                return ""

        raw_chunks: List[str] = []
        try:
            async for chunk in llm_service.stream_external_api(
                client, model_info, messages, is_json_output=True
            ):
                if paused_flag.get("value"):
                    try:
                        await websocket.send_json({
                            "event": "cancelled",
                            "restore_user_message": user_msg,
                            "message": "stream_cancelled_by_user",
                        })
                    except Exception:
                        pass
                    return ""
                # JSON-mode deltas are fragments of one document — buffer only.
                if chunk:
                    raw_chunks.append(chunk)

            raw_text = "".join(raw_chunks).strip()
            # Capture the streamed turn's usage before a JSON repair call can
            # overwrite llm_service._last_response_json.
            stream_usage = getattr(llm_service, "_last_response_json", {}) or {}

            output, ladder_rung = await _parse_chat_guidance_output(
                raw_text, llm_service, client, model_info,
                repair_model_info=repair_model_info,
                supabase_service=supabase_service,
                session_id=session_id,
            )
            llm_service._last_response_json = stream_usage

            if output is not None:
                logger.info(f"ChatGuidanceOutput parsed via ladder rung: {ladder_rung}")

                # Apply this turn's field_updates BEFORE deciding which question
                # to show next, so the flow advances in the same turn.
                clean_filled: Dict[str, Any] = {}
                sources: Dict[str, str] = {}
                review_notes: Dict[str, str] = {}
                prior_state: Dict[str, Tuple[Any, Any, Any]] = {}
                if output.field_updates and greeting_turn:
                    logger.info(f"Dropped field writes on the greeting turn: {list(output.field_updates)}")
                elif output.field_updates:
                    clean_filled = normalize_filled_fields(output.field_updates, all_questions)
                    logger.info(f"Normalized fields: {clean_filled}")
                    if autofill_turn:
                        dropped = _restrict_autofill_to_target(clean_filled, autofill_target_id)
                        if dropped:
                            logger.info(f"Dropped autofill writes outside the current question: {dropped}")
                    prior_state = {
                        fid: (current_answers.get(fid), current_answer_meta.get(fid), answer_provenance.get(fid))
                        for fid in clean_filled
                    }
                    if autofill_turn:
                        sources, review_notes = _tag_ai_filled_fields(
                            clean_filled, current_answers, answer_provenance, all_questions, fact_context
                        )
                    current_answers.update(clean_filled)
                    for field_id in clean_filled.keys():
                        touch_meta_field(current_answer_meta, field_id)

                if QUESTION_CONTROL_ENABLED:
                    # Backend-computed next_question is authoritative — the
                    # model may narrate but not redirect flow.
                    updated_applicable_questions = compute_applicable_questions(all_questions, current_answers)
                    skipped_ids = (
                        {q.get("id") for q in all_questions}
                        - {q.get("id") for q in updated_applicable_questions}
                    )
                    dropped = _drop_model_writes_to_skipped_fields(
                        clean_filled, prior_state, skipped_ids, current_answers,
                        current_answer_meta, answer_provenance, sources, review_notes,
                    )
                    if dropped:
                        logger.info(f"Dropped model writes to rule-skipped fields: {dropped}")
                        updated_applicable_questions = compute_applicable_questions(all_questions, current_answers)
                    # Placeholder lands in the same turn the gate is answered.
                    _fill_skip_placeholders(
                        all_questions, updated_applicable_questions, current_answers,
                        current_answer_meta, answer_provenance,
                    )
                    updated_next_question_id = compute_next_question_id(updated_applicable_questions, current_answers)
                    target_question = next(
                        (q for q in updated_applicable_questions if q.get("id") == updated_next_question_id), None
                    )
                else:
                    updated_applicable_questions = None
                    target_question = None
                    if output.suggested_next_question_id:
                        for q in all_questions:
                            if q.get("id") == output.suggested_next_question_id:
                                target_question = q
                                break
                    if target_question is None:
                        _, _, _, updated_ua_list = format_qa_descriptions(all_questions, current_answers)
                        target_question = updated_ua_list[0] if updated_ua_list else None

                prompt_text = _question_prompt_text(target_question) if target_question else ""

                # 剩餘題數以本回合填寫後的實際狀態為準，不採用模型自行敘述的數字
                if QUESTION_CONTROL_ENABLED:
                    progress_after = compute_progress(updated_applicable_questions, current_answers)
                    remaining_after = progress_after["total"] - progress_after["answered"]
                else:
                    remaining_after = len(format_qa_descriptions(all_questions, current_answers)[3])
                reply_intro = _correct_remaining_count(output.reply_intro.strip(), remaining_after)
                reply_outro = _correct_remaining_count(output.reply_outro.strip(), remaining_after)

                parts = [p for p in [reply_intro, prompt_text, reply_outro] if p]
                for idx, part in enumerate(parts):
                    piece = part if idx == 0 else f"\n\n{part}"
                    await websocket.send_json({"event": "chunk", "data": piece})

                if clean_filled:
                    filled_payload: Dict[str, Any] = {"event": "filled", "data": clean_filled}
                    if sources:
                        filled_payload["sources"] = sources
                    if review_notes:
                        filled_payload["needs_review"] = review_notes
                    if QUESTION_CONTROL_ENABLED:
                        filled_payload["applicable_questions"] = [
                            q.get("id") for q in updated_applicable_questions
                        ]
                    await websocket.send_json(filled_payload)

                await websocket.send_json({"event": "done"})
                return "\n\n".join(parts).strip()

            logger.warning(
                "ChatGuidanceOutput parse ladder exhausted for chat_guidance; "
                f"falling back to legacy marker parsing. raw preview: {raw_text[:200]!r}"
            )
            visible_text = await _apply_legacy_hidden_markers(
                raw_text, all_questions, current_answers, current_answer_meta, websocket,
                autofill_turn, answer_provenance, fact_context, autofill_target_id,
                greeting_turn=greeting_turn, require_markers=True,
            )
            if not visible_text or visible_text.lstrip().startswith("{"):
                visible_text = "抱歉，剛才的回覆發生格式錯誤，請重新傳送訊息或稍後再試。"

            await websocket.send_json({"event": "chunk", "data": visible_text})
            await websocket.send_json({"event": "done"})
            return visible_text
        except Exception as exc:
            logger.error("Stream error: %s", exc)
            await websocket.send_json({"event": "error", "message": str(exc)})
            return ""

    async def send_limit_reached(token_total: int) -> None:
        await websocket.send_json({
            "event": "limit_reached",
            "reason": "prompts" if interaction_count >= DEMO_INTERACTION_LIMIT else "tokens",
            "interaction_count": interaction_count,
            "interaction_limit": DEMO_INTERACTION_LIMIT,
            "token_usage": token_total,
            "token_limit": DEMO_MAX_TOKENS_PER_SESSION,
            "register_url": DEMO_REGISTER_REDIRECT_URL,
            "session_id": session_id,
        })

    try:
        init_data = await websocket.receive_json()
        project_title = init_data.get("project_title", "")
        project_summary = init_data.get("project_summary", "")
        grant_name = init_data.get("grant_name", "")
        all_questions = init_data.get("all_questions", []) or []
        grant_id = init_data.get("grant_id") or demo_row.get("grant_id")
        template_id = init_data.get("template_id") or demo_row.get("template_id")

        # Make sure the demo row exists and remembers the template the visitor picked.
        await supabase_service.ensure_demo_session(
            session_id,
            grant_id=grant_id,
            template_id=template_id,
        )

        # Hydrate from existing DB row if present (page reload mid-session).
        if demo_row:
            conversation_history_records = list(demo_row.get("conversation_history") or [])
            stored_answer_state = dict(demo_row.get("stored_answer") or {})
            db_answers = {
                field_id: entry.value
                for field_id, entry in extract_chat_answer_entries(stored_answer_state).items()
            }
            db_meta = normalize_meta_payload(stored_answer_state.get("chat_answers_meta"))
            frontend_answers = {
                field_id: answer_text(value)
                for field_id, value in (init_data.get("current_answers") or {}).items()
            }
            frontend_meta = normalize_meta_payload(init_data.get("current_answers_meta"))
            current_answers = {**db_answers, **frontend_answers}
            current_answer_meta = {**db_meta, **frontend_meta}

        # The DB-loaded schema is canonical for the question list; the
        # client-supplied list is kept only as a fallback and cross-check.
        if QUESTION_CONTROL_ENABLED:
            db_questions = await load_template_questions(grant_id, template_id, supabase_service)
            if db_questions:
                client_ids = {q.get("id") for q in all_questions}
                db_ids = {q.get("id") for q in db_questions}
                if client_ids != db_ids:
                    logger.warning(
                        "chat_guidance question-list mismatch for demo session %s: client-only=%s db-only=%s",
                        session_id, sorted(client_ids - db_ids), sorted(db_ids - client_ids),
                    )
                all_questions = db_questions

        if not conversation_history_records:
            for h in init_data.get("history") or []:
                if isinstance(h, dict) and h.get("content"):
                    conversation_history_records.append(build_history_entry(h.get("role"), h.get("content")))

        ready_payload: Dict[str, Any] = {
            "event": "ready",
            "message": "系统就绪",
            "interaction_count": interaction_count,
            "interaction_limit": DEMO_INTERACTION_LIMIT,
        }
        if QUESTION_CONTROL_ENABLED:
            ready_payload["applicable_questions"] = [
                q.get("id") for q in compute_applicable_questions(all_questions, current_answers)
            ]
        await websocket.send_json(ready_payload)

        paused_flag = {"value": False}

        # Opening message (only if there's no recent assistant turn).
        last_is_assistant = False
        if conversation_history_records:
            last_entry = conversation_history_records[-1]
            if str(last_entry.get("id", "")).startswith("assistant") or last_entry.get("role") == "assistant":
                last_is_assistant = True

        if not last_is_assistant:
            async with httpx.AsyncClient(timeout=60.0) as client:
                first_reply = await stream_ai_reply(
                    GREETING_USER_MESSAGE,
                    conversation_history_records,
                    client,
                    paused_flag,
                )
                # Buffer token usage from the opening turn (drained on claim).
                await supabase_service.append_demo_usage_log(
                    session_id,
                    model_info,
                    getattr(llm_service, "_last_response_json", {}) or {},
                    action="生成對話",
                )
                if first_reply:
                    conversation_history_records.append(build_history_entry("assistant", first_reply))
                    await save_state_to_db()

        incoming_user_queue: asyncio.Queue = asyncio.Queue()

        async def websocket_reader():
            try:
                while True:
                    payload = await websocket.receive_json()
                    if payload.get("action") == "pause":
                        paused_flag["value"] = True
                        try:
                            await websocket.send_json({"event": "paused_ack"})
                        except Exception:
                            pass
                        continue
                    await incoming_user_queue.put(payload)
            except WebSocketDisconnect:
                await incoming_user_queue.put({"_disconnect": True})
            except Exception as exc:
                logger.error("Reader error: %s", exc)
                await incoming_user_queue.put({"_disconnect": True})

        reader_task = asyncio.create_task(websocket_reader())

        try:
            while True:
                payload = await incoming_user_queue.get()
                if payload.get("_disconnect"):
                    logger.info("Client disconnected from queue (session %s)", session_id)
                    break

                user_msg = (payload.get("user_message") or "").strip()
                incoming_answers = payload.get("current_answers", {}) or {}
                incoming_meta = normalize_meta_payload(payload.get("current_answers_meta"))
                provided_meta_keys = set(incoming_meta.keys())
                if incoming_meta:
                    current_answer_meta.update(incoming_meta)
                if incoming_answers:
                    for field_id, raw_value in incoming_answers.items():
                        value = answer_text(raw_value)
                        stale_placeholder = cleared_placeholders.get(field_id)
                        if stale_placeholder is not None:
                            if value.strip() == stale_placeholder.strip():
                                continue
                            cleared_placeholders.pop(field_id, None)
                        previous_value = current_answers.get(field_id)
                        current_answers[field_id] = value
                        if (previous_value or "").strip() != value.strip():
                            answer_provenance.pop(field_id, None)
                        if previous_value != value and field_id not in provided_meta_keys:
                            touch_meta_field(current_answer_meta, field_id)

                # 生成前確認：使用者逐段確認（或取消確認）AI 生成的答案；答案內容改變時確認會自動失效
                if payload.get("action") == "confirm_answers":
                    confirmed_flag = bool(payload.get("confirmed", True))
                    confirmed_ids = [
                        field_id for field_id in (payload.get("field_ids") or [])
                        if isinstance(field_id, str) and str(current_answers.get(field_id) or "").strip()
                    ]
                    for field_id in confirmed_ids:
                        answer_provenance[field_id] = {
                            **(answer_provenance.get(field_id) or {}),
                            "confirmed": confirmed_flag,
                        }
                    if confirmed_ids:
                        await save_state_to_db()
                    await websocket.send_json({
                        "event": "answers_confirmed",
                        "field_ids": confirmed_ids,
                        "confirmed": confirmed_flag,
                    })
                    continue

                if not user_msg:
                    continue

                # Demo caps: refuse new turns once either the prompt count
                # or the cumulative token usage has hit its limit.
                token_total = await supabase_service.get_demo_token_usage(session_id)
                if interaction_count >= DEMO_INTERACTION_LIMIT or token_total >= DEMO_MAX_TOKENS_PER_SESSION:
                    await send_limit_reached(token_total)
                    continue

                # prepare user entry but DO NOT append yet — only persist if stream completes
                user_entry = build_history_entry("user", user_msg)

                async with httpx.AsyncClient(timeout=60.0) as client:
                    ai_reply = await stream_ai_reply(
                        user_msg, conversation_history_records, client, paused_flag
                    )

                    # Buffer token usage for this turn (drained on claim).
                    await supabase_service.append_demo_usage_log(
                        session_id,
                        model_info,
                        getattr(llm_service, "_last_response_json", {}) or {},
                        action="生成對話",
                    )

                    if paused_flag.get("value"):
                        paused_flag["value"] = False
                        continue

                    conversation_history_records.append(user_entry)
                    if ai_reply:
                        conversation_history_records.append(build_history_entry("assistant", ai_reply))

                    interaction_count = await supabase_service.increment_demo_interaction(session_id)
                    await save_state_to_db()

                    token_total = await supabase_service.get_demo_token_usage(session_id)
                    if interaction_count >= DEMO_INTERACTION_LIMIT or token_total >= DEMO_MAX_TOKENS_PER_SESSION:
                        await send_limit_reached(token_total)

        finally:
            if not reader_task.done():
                reader_task.cancel()

    except Exception as exc:
        logger.error("WebSocket endpoint error: %s", exc, exc_info=True)
        try:
            await websocket.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Project-name recommendation
# ---------------------------------------------------------------------------

@router.post("/recommend_project_names", summary="根據已填寫的欄位推薦五個專案名稱")
async def recommend_project_names(
    payload: Dict[str, Any],
    request: Request,
    session_id: str = Depends(require_demo_session_id),
    llm_service: LLMService = Depends(get_llm_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Demo port of the platform's recommend_project_names.

    Uses the platform's per-feature model setting first (feature
    `recommend_names`), then falls back through cheap external models on
    rate limits. Token usage is captured via append_demo_usage_log.
    """
    app_state = request.app.state
    model_registry = getattr(app_state, "model_registry", {}) or {}
    seen: set = set()
    candidate_models: List[Dict[str, Any]] = []

    feature_model = get_feature_model(app_state, "recommend_names", True)
    if feature_model and feature_model.get("id"):
        candidate_models.append(feature_model)
        seen.add(feature_model["id"])
    # Fallbacks in preference order; skip any that aren't registered.
    for mid in ("gemini-3.1-flash-lite", "chat-latest", "gpt-4.1-mini"):
        m = model_registry.get(mid)
        if m and mid not in seen:
            candidate_models.append(m)
            seen.add(mid)
    # Final safety net: any other external models registered.
    for mid, m in model_registry.items():
        if mid in seen:
            continue
        if isinstance(m, dict) and m.get("type") == "external":
            candidate_models.append(m)
            seen.add(mid)
    if not candidate_models:
        raise HTTPException(status_code=500, detail="Model not configured for recommendation.")
    logger.info("Recommend names candidate models: %s", [c.get("id") for c in candidate_models])

    current_answers = {
        field_id: answer_text(value)
        for field_id, value in (payload.get("current_answers", {}) or {}).items()
    }
    project_title = payload.get("project_title", "") or ""
    grant_name = payload.get("grant_name", "") or ""
    template_name = payload.get("template_name", "") or ""
    grant_id = payload.get("grant_id", "") or ""
    template_id = payload.get("template_id", "") or ""

    name_config: Optional[Dict[str, Any]] = None
    if grant_id and template_id:
        try:
            template_record = await supabase_service.get_template_by_id(template_id, grant_id)
            if template_record:
                raw_config = template_record.get("name_recommend_config")
                if isinstance(raw_config, dict):
                    name_config = raw_config
        except Exception as exc:
            logger.warning(
                "Failed to load name recommend config for %s/%s: %s",
                grant_id,
                template_id,
                exc,
            )

    custom_traits = ""
    custom_examples: List[str] = []
    if name_config:
        traits_value = name_config.get("traits")
        if isinstance(traits_value, str):
            custom_traits = traits_value.strip()

        raw_examples = name_config.get("examples")
        if isinstance(raw_examples, list):
            for example in raw_examples:
                if not isinstance(example, str):
                    continue
                trimmed = example.strip()
                if trimmed and trimmed not in custom_examples:
                    custom_examples.append(trimmed)
                if len(custom_examples) >= 5:
                    break

    filled_items = []
    for k, v in current_answers.items():
        if v and str(v).strip():
            filled_items.append(f"- {k}: {str(v)[:120]}")
    filled_text = "\n".join(filled_items) or "（無已填寫欄位）"

    few_shot_text = (
        "\n".join([f"  - {ex}" for ex in custom_examples])
        if custom_examples
        else "  - （尚未提供範例）"
    )

    custom_trait_block = (
        f"\n6. **模板自訂特性**：{custom_traits}" if custom_traits else ""
    )

    system_prompt = f"""你是一位資深的政府補助計畫命名專家，擁有豐富的計畫書撰寫經驗。
你的任務是根據專案的核心內容、補助計畫類型和已填寫的欄位信息，生成專業、具有吸引力的計畫名稱。

## 命名原則：
1. **清晰傳達**：名稱需在一讀之間說明核心價值或成果
2. **突出創新**：凸顯技術創新、服務升級或市場拓展等亮點
3. **符合計畫特性**：依補助主題與模板特性挑選關鍵語彙，避免偏離既定範疇
4. **避免重複**：不照搬或過度相似現有計畫名稱
5. **使用繁體中文**：專業用語準確，避免生僻字{custom_trait_block}"""

    trait_section = (
        f"\n**模板命名特性說明**：\n{custom_traits}\n" if custom_traits else ""
    )

    user_prompt = f"""## 補助計畫背景

**補助主題**：{grant_name}
**計畫模板**：{template_name}
{trait_section}


## 目前專案信息

**專案目前名稱**：{project_title if project_title else "（未命名）"}

**已填寫欄位摘要**：
{filled_text}

## 參考範例（同補助主題已核准計畫）
{few_shot_text}

## 任務要求

根據上述背景信息和參考範例的命名風格，為本專案生成最多 5 個創新、專業的計畫名稱建議。
名稱應該：
- 突出本專案的核心特色與創新點
- 符合範例命名慣例與風格
- 避免與參考範例過於相似

## 輸出格式

請以純 JSON 回傳，格式如下：
{{"names": ["名稱一", "名稱二", "名稱三", "名稱四", "名稱五"]}}

**注意**：每個名稱應為完整的計畫名稱，不要只是片段關鍵字。
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response: Optional[str] = None
    response_json: Optional[Dict[str, Any]] = None
    used_model: Optional[Dict[str, Any]] = None
    last_error: Optional[Dict[str, Any]] = None

    try:
        async with httpx.AsyncClient() as client:
            for candidate in candidate_models:
                response, error, response_json = await llm_service.call_external_api(
                    client, candidate, messages, is_json_output=True
                )
                if not error:
                    used_model = candidate
                    break
                last_error = error
                err_text = str(error.get("error", "")).lower() if isinstance(error, dict) else str(error).lower()
                # Only fall through to the next candidate on rate-limit; bail on
                # other errors so we don't mask real configuration problems.
                if "rate limit" not in err_text and "429" not in err_text:
                    break
                logger.warning(
                    "Recommend names: %s rate-limited, falling back to next candidate",
                    candidate.get("id"),
                )

        if used_model is None or response is None:
            logger.error("Recommend names failed across all candidates: %s", last_error)
            raise HTTPException(status_code=502, detail="Recommendation service error")

        try:
            data = json.loads(response)
            names = data.get("names") or []
            cleaned: List[str] = []
            for n in names:
                if not n:
                    continue
                s = str(n).strip()
                if s and s not in cleaned:
                    cleaned.append(s)
                if len(cleaned) >= 5:
                    break

            if response_json and used_model.get("type") == "external":
                try:
                    await supabase_service.append_demo_usage_log(
                        session_id,
                        used_model,
                        response_json,
                        action="推薦計畫名稱",
                    )
                except Exception:
                    logger.warning("Failed to log demo usage for recommend_project_names", exc_info=True)

            return {"names": cleaned}
        except HTTPException:
            raise
        except Exception as ex:
            logger.error("Failed to parse recommendation response: %s", ex)
            raise HTTPException(status_code=500, detail="Failed to parse recommendation response")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in recommend_project_names: %s", e)
        raise HTTPException(status_code=500, detail="Recommendation service error")


# ---------------------------------------------------------------------------
# Plan generation / revision
# ---------------------------------------------------------------------------

def _find_template_config(app_state: Any, grant_id: str, template_id: str):
    for grant in getattr(app_state, "all_grants_config", []) or []:
        if grant.id == grant_id:
            for template in grant.templates:
                if template.id == template_id:
                    return template
            break
    return None


def _resolve_demo_selected_model(app_state: Any, requested: Optional[str], label: str) -> Optional[str]:
    """The demo's shared Gemini key is heavily rate-limited. If the caller
    didn't pin a model, pick the first non-Gemini external model registered
    so per-section generations don't all collide on the Gemini quota."""
    if requested:
        return requested
    model_registry = getattr(app_state, "model_registry", {}) or {}
    selected: Optional[str] = None
    for mid in ("chat-latest",):
        if mid in model_registry:
            selected = mid
            break
    if not selected:
        for mid, m in model_registry.items():
            if isinstance(m, dict) and m.get("type") == "external" and "gemini" not in mid.lower():
                selected = mid
                break
    logger.info("%s default selected_model resolved to %s", label, selected)
    return selected


def _collect_plan_content(results: List[Any], label: str) -> Tuple[Dict[str, List[Dict[str, Any]]], List[str]]:
    plan_content: Dict[str, List[Dict[str, Any]]] = {}
    section_success_stats: Dict[str, Dict[str, int]] = {}
    for res in results:
        if isinstance(res, Exception):
            logger.error("%s task raised exception: %s", label, res, exc_info=False)
            continue
        if isinstance(res, SectionGenerateResponse):
            section_id = res.section_id
            if section_id not in section_success_stats:
                section_success_stats[section_id] = {"success": 0, "failed": 0}
                plan_content[section_id] = []
            if res.error:
                section_success_stats[section_id]["failed"] += 1
                logger.warning("%s candidate for section %s failed: %s", label, section_id, res.error)
            else:
                section_success_stats[section_id]["success"] += 1
                plan_content[section_id].append(res.dict())
    failed_sections = [sid for sid, stats in section_success_stats.items() if stats["success"] == 0]
    if failed_sections:
        logger.error("⚠️  %d sections failed completely during %s: %s", len(failed_sections), label, failed_sections)
    return plan_content, failed_sections


def _extract_chat_answers_from_stored(stored_answer: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return {field_id: entry.value for field_id, entry in extract_chat_answer_entries(stored_answer or {}).items()}


def _format_revision_answers(stored_answer: Optional[Dict[str, Any]]) -> str:
    merged = _extract_chat_answers_from_stored(stored_answer)
    if not merged:
        return "（目前尚無額外問答摘要）"
    lines = []
    for key in sorted(merged.keys()):
        value = merged[key]
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            text = json.dumps(value, ensure_ascii=False)
        else:
            text = str(value)
        text = text.strip()
        if not text:
            continue
        if len(text) > 600:
            text = text[:600] + "..."
        lines.append(f"- {key}: {text}")
    return "\n".join(lines) if lines else "（目前尚無額外問答摘要）"


def _format_user_input_summary(stored_answer: Optional[Dict[str, Any]]) -> str:
    if not stored_answer or not isinstance(stored_answer, dict):
        return ""
    user_input = stored_answer.get("user_input") or stored_answer.get("userInput")
    if not isinstance(user_input, dict):
        return ""
    parts: List[str] = []
    main_idea = user_input.get("main_idea") or user_input.get("mainIdea")
    if main_idea:
        parts.append(f"【核心構想】\n{main_idea}")
    dynamic_fields = user_input.get("dynamic_fields") or user_input.get("dynamicFields")
    if isinstance(dynamic_fields, dict):
        field_lines = []
        for key, value in dynamic_fields.items():
            if value is None:
                continue
            if isinstance(value, (dict, list)):
                text = json.dumps(value, ensure_ascii=False)
            else:
                text = str(value)
            text = text.strip()
            if not text:
                continue
            field_lines.append(f"- {key}: {text}")
        if field_lines:
            parts.append("【動態欄位摘要】\n" + "\n".join(field_lines))
    return "\n\n".join(parts)


def _build_section_revision_context(section, version_map: Dict[str, Any]) -> str:
    existing_entry = None
    if version_map and isinstance(version_map, dict):
        existing_entry = version_map.get(section.id)

    if existing_entry is None:
        return (
            f"此章節（{section.name}）目前沒有內容。請根據問答摘要與 JSON Schema 補齊完整內容，"
            "同時維持原有語氣與結構邏輯。"
        )

    content_candidate = existing_entry
    if isinstance(existing_entry, dict):
        if existing_entry.get("content") is not None:
            content_candidate = existing_entry.get("content")
        elif existing_entry.get("raw_json_content") is not None:
            content_candidate = existing_entry.get("raw_json_content")

    if isinstance(content_candidate, str):
        formatted_content = content_candidate
    else:
        try:
            formatted_content = json.dumps(content_candidate, ensure_ascii=False, indent=2)
        except Exception:
            formatted_content = str(content_candidate)

    return (
        f"以下為【{section.name}】章節的既有內容，請在此基礎上進行微調：\n{formatted_content}\n"
        "請保留核心脈絡與欄位排列，只針對語句、缺漏與佐證進行補強，必要時可新增具體數據或示例。"
    )


def _extract_previous_section_content(section, version_map: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    existing_entry = version_map.get(section.id) if isinstance(version_map, dict) else None
    content_candidate = existing_entry
    if isinstance(existing_entry, dict):
        if existing_entry.get("content") is not None:
            content_candidate = existing_entry.get("content")
        elif existing_entry.get("raw_json_content") is not None:
            content_candidate = existing_entry.get("raw_json_content")
    return content_candidate if isinstance(content_candidate, dict) else None


def _align_derivative_candidates(plan_content: Dict[str, List[Dict[str, Any]]], sections, targets_text: str) -> None:
    # 衍生產品或服務在各章節分開生成，依【關鍵指標目標值】統一所有候選版本，並重新產生格式化文字
    target = parse_derivative_target(targets_text)
    if target is None:
        return
    schemas = {s.id: s.json_schema for s in sections if getattr(s, "json_schema", None)}
    for section_id, candidates in plan_content.items():
        schema = schemas.get(section_id)
        if not schema:
            continue
        for candidate in candidates:
            raw = candidate.get("raw_json_content")
            if align_derivatives(section_id, raw, schema, target):
                candidate["content"] = format_section_output(raw, schema)


def _format_existing_plan_text(sections, version_map: Dict[str, Any]) -> str:
    def collect(value: Any, out: List[str]) -> None:
        if isinstance(value, dict):
            for v in value.values():
                collect(v, out)
        elif isinstance(value, list):
            for v in value:
                collect(v, out)
        elif value is not None and str(value).strip():
            out.append(str(value).strip())

    blocks = []
    for section in sections:
        content = _extract_previous_section_content(section, version_map)
        if not content:
            continue
        texts: List[str] = []
        collect(content, texts)
        if texts:
            blocks.append(f"【{section.name}】\n" + "\n".join(texts))
    return "\n\n".join(blocks)


@router.post("/generate_plan", summary="生成完整計畫書，多候選版本")
async def generate_plan(
    request_data: GenerateRequest,
    request: Request,
    session_id: str = Depends(require_demo_session_id),
    llm_service: LLMService = Depends(get_llm_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Demo port of the platform's generate_plan.

    Removes per-user quota / throttling / project-tracking — visitors are
    capped by the chat interaction limit upstream and one generation per
    session. Facts are classified once (tense + key targets) before the
    sections are generated, as on the platform.
    """
    session = await supabase_service.get_demo_session(session_id)
    if session and session.get("has_generated_docx"):
        raise HTTPException(
            status_code=429,
            detail="報告生成次數已達上限，免費註冊即可繼續使用。",
        )

    app_state = request.app.state
    template_config = _find_template_config(app_state, request_data.grant, request_data.template)
    if not template_config:
        raise HTTPException(
            status_code=400,
            detail=f"Template {request_data.template} not found in Grant {request_data.grant}.",
        )

    sections = template_config.sections
    if not sections:
        raise HTTPException(status_code=400, detail="No sections found in the selected template.")

    # ── Demo: only generate sections the visitor actually answered ──
    # Chat answer field keys follow the pattern "section_id::field_key".
    # If the user answered nothing and confirmed the warning dialog, we
    # fall back to generating all sections.
    stored_answer = (session or {}).get("stored_answer") or {}
    chat_answers = _extract_chat_answers_from_stored(stored_answer)
    answered_section_ids: set = set()
    for field_key in chat_answers.keys():
        if "::" in field_key:
            sid = field_key.split("::")[0]
            if sid:
                answered_section_ids.add(sid)
    if answered_section_ids:
        filtered = [s for s in sections if s.id in answered_section_ids]
        if filtered:
            logger.info(
                "Demo generate_plan: filtering sections %d → %d based on chat answers",
                len(sections), len(filtered),
            )
            sections = filtered
        else:
            logger.warning(
                "Demo generate_plan: answered section IDs did not match any "
                "template section, falling back to all sections"
            )

    num_candidates = request_data.num_candidates
    final_user_input = request_data.user_input or ""
    selected_model = _resolve_demo_selected_model(app_state, request_data.selected_model, "generate_plan")

    async with httpx.AsyncClient() as client:
        # 先統一判定事項時態，再傳給所有章節，避免各章節時態不一致
        # 失敗時停止生成（沒有時態清單、關鍵指標與 conflicts 的計畫書會前後矛盾），請使用者重試
        try:
            tense_block = await llm_service.classify_fact_tense(
                http_session=client,
                grant_id=request_data.grant,
                template_id=request_data.template,
                section_id=sections[0].id,
                user_input=final_user_input,
                app_state=app_state,
                user_id=session_id,
                supabase_service=supabase_service,
                is_external=request_data.is_external,
                selected_model=selected_model,
                project_id=None,
                strict=True,
            )
        except FactCheckError as e:
            logger.error(f"[FactTense] plan generation stopped: {e}")
            raise HTTPException(status_code=502, detail="計畫書事實整理步驟暫時失敗（可能是網路逾時），請稍後重新產生。")
        if tense_block:
            final_user_input = f"{final_user_input}\n\n{tense_block}"

        tasks = [
            llm_service.generate_section_content(
                http_session=client,
                grant_id=request_data.grant,
                template_id=request_data.template,
                section_id=s.id,
                user_input=final_user_input,
                app_state=app_state,
                user_id=session_id,
                supabase_service=supabase_service,
                is_external=request_data.is_external,
                selected_model=selected_model,
                project_id=None,
                section_details_override=s,
            )
            for s in sections
            for _ in range(num_candidates)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    plan_content, _failed_sections = _collect_plan_content(results, "generation")
    _align_derivative_candidates(plan_content, sections, tense_block)

    await supabase_service.update_demo_session(session_id, {"has_generated_docx": True})

    return plan_content


@router.post("/revise_plan_version", summary="基於既有版本重新優化計畫書，多候選版本")
async def revise_plan_version(
    request_data: PlanRevisionRequest,
    request: Request,
    session_id: str = Depends(require_demo_session_id),
    llm_service: LLMService = Depends(get_llm_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Demo port of the platform's revise_plan_version.

    Removes auth/quota/throttling/project tracking. Builds the same revision
    prompt as the platform (tense list + existing key targets) and reuses
    generate_section_content per section.
    """
    session = await supabase_service.get_demo_session(session_id)
    if session and session.get("has_generated_docx"):
        raise HTTPException(
            status_code=429,
            detail="報告生成次數已達上限，免費註冊即可繼續使用。",
        )

    if not request_data.current_version or not isinstance(request_data.current_version, dict):
        raise HTTPException(status_code=400, detail="current_version is required for revision.")

    app_state = request.app.state
    template_config = _find_template_config(app_state, request_data.grant, request_data.template)
    if not template_config:
        raise HTTPException(
            status_code=400,
            detail=f"Template {request_data.template} not found in Grant {request_data.grant}.",
        )

    sections = template_config.sections
    if not sections:
        raise HTTPException(status_code=400, detail="No sections found in the selected template.")

    answers_summary = _format_revision_answers(request_data.stored_answer)
    user_input_summary = _format_user_input_summary(request_data.stored_answer)
    project_title = request_data.project_title or "未提供"
    project_summary = request_data.project_summary or "尚未提供摘要"

    base_prompt = f"""
你是一位資深的計畫書編輯，任務是基於現有版本進行「版本更新」。請遵循：
- 維持章節 JSON Schema 結構與欄位順序，保留 80~90% 原始內容骨架。
- 對語句不順、細節不足或缺乏佐證的段落進行精煉、補強與具體化。
- 若需補充無法確定的資訊，請以「待決定」作為暫時佔位符，不可使用 OOO。
- 問答摘要可能已經更新了，請根據問答摘要補齊內容，但仍需與整體脈絡一致。
- 完成後輸出純 JSON，不要添加說明文字。

計畫名稱：{project_title}
計畫摘要：{project_summary}

【使用者問答摘要】
{answers_summary}
"""
    if user_input_summary:
        base_prompt += f"\n\n【使用者輸入摘要】\n{user_input_summary}"

    selected_model = _resolve_demo_selected_model(app_state, request_data.selected_model, "revise_plan_version")
    version_map = request_data.current_version

    async with httpx.AsyncClient() as client:
        # 先統一判定事項時態，再傳給所有章節，同時修正現有版本中不一致的時態
        # 時態判定不可看到現有版本（否則已完成事項會被降級），指標目標值另由現有版本取得，兩個呼叫分開
        fact_kwargs = dict(
            http_session=client,
            grant_id=request_data.grant,
            template_id=request_data.template,
            section_id=sections[0].id,
            app_state=app_state,
            user_id=session_id,
            supabase_service=supabase_service,
            is_external=request_data.is_external,
            selected_model=selected_model,
            project_id=None,
        )
        tense_block, existing_targets = await asyncio.gather(
            llm_service.classify_fact_tense(user_input=base_prompt, include_targets=False, **fact_kwargs),
            llm_service.extract_existing_targets(
                existing_content=_format_existing_plan_text(sections, version_map), **fact_kwargs
            ),
        )
        targets_block = build_targets_block(existing_targets, tense_block)
        for block in (tense_block, targets_block):
            if block:
                base_prompt += f"\n\n{block}"

        tasks = []
        for section in sections:
            section_context = _build_section_revision_context(section, version_map)
            for _ in range(request_data.num_candidates):
                tasks.append(
                    llm_service.generate_section_content(
                        http_session=client,
                        grant_id=request_data.grant,
                        template_id=request_data.template,
                        section_id=section.id,
                        user_input=base_prompt,
                        app_state=app_state,
                        user_id=session_id,
                        supabase_service=supabase_service,
                        is_external=request_data.is_external,
                        selected_model=selected_model,
                        project_id=None,
                        section_context=section_context,
                        disable_few_shot=True,
                        section_details_override=section,
                        action="修訂企劃書章節",
                        previous_content=_extract_previous_section_content(section, version_map),
                    )
                )
        results = await asyncio.gather(*tasks, return_exceptions=True)

    plan_content, _failed_sections = _collect_plan_content(results, "revision")
    return plan_content
