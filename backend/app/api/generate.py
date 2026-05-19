# Demo chat-guidance WebSocket endpoint.
#
# The parent platform's generate.py exposed ~7 endpoints (generate_plan,
# revise, synthetic_input, recommend_names, autofill, field_analysis, +
# the chat WS). The demo only needs the chat — visitors interact with the
# guided AI for up to N turns before being prompted to register on the
# parent platform.

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.dependencies import DEMO_SESSION_COOKIE_NAME, _coerce_uuid
from app.config import DEMO_INTERACTION_LIMIT, DEMO_REGISTER_REDIRECT_URL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Generation"])

HIDDEN_REPLY_BLOCK_PATTERN = re.compile(
    r"【回復結束】【隱藏回復欄位\+答案】(.*?)【隱藏回復結束】",
    re.DOTALL,
)


def extract_hidden_field_responses(text: Optional[str]) -> Dict[str, str]:
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
        label = q.get("label", qid)
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
            answered_list.append(f"- {label}: {display_val}")
        else:
            unanswered_list.append(q)

    questions_desc = "\n".join(
        f"- {q.get('id', q.get('label'))}: {q.get('prompt', '')}" for q in all_questions
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

    llm_service = websocket.app.state.llm_service
    model_registry = getattr(websocket.app.state, "model_registry", {}) or {}
    model_info = model_registry.get("gpt-5.1-chat-latest") or {
        "id": "gpt-5.1-chat-latest",
        "provider": "openai",
        "type": "external",
        "cost_info": {"input": 1.25, "output": 10},
    }

    conversation_history_records: List[Dict[str, Any]] = []
    stored_answer_state: Dict[str, Any] = {}
    current_answers: Dict[str, Any] = {}
    current_answer_meta: Dict[str, Dict[str, str]] = {}
    all_questions: List[Dict[str, Any]] = []
    project_title = ""
    project_summary = ""
    grant_name = ""

    demo_row = await supabase_service.get_demo_session(session_id) or {}
    interaction_count = int(demo_row.get("interaction_count") or 0)

    async def save_state_to_db():
        try:
            previous_answers = stored_answer_state.get("chat_answers") or {}
            previous_snapshot = json.dumps(previous_answers, ensure_ascii=False, sort_keys=True)
            current_snapshot = json.dumps(current_answers, ensure_ascii=False, sort_keys=True)
            answers_changed = previous_snapshot != current_snapshot

            stored_answer_state["chat_answers"] = current_answers.copy()
            stored_answer_state["chat_answers_meta"] = {
                key: (value.copy() if isinstance(value, dict) else value)
                for key, value in current_answer_meta.items()
            }
            await supabase_service.update_demo_session(
                session_id,
                {
                    "conversation_history": conversation_history_records,
                    "stored_answer": stored_answer_state,
                },
            )

            # Buffer a timeline event whenever answers diff — the parent
            # platform's AI Timeline view will replay these on claim.
            if answers_changed:
                field_changes: List[Dict[str, Any]] = []
                all_field_ids = set(previous_answers.keys()) | set(current_answers.keys())
                for field_id in sorted(all_field_ids):
                    old_val = previous_answers.get(field_id, "")
                    new_val = current_answers.get(field_id, "")
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
                        "answers_count": len(current_answers),
                        "field_changes": field_changes,
                        "changes_summary": " | ".join(c["change"] for c in field_changes),
                    },
                )
        except Exception as exc:
            logger.error("DB save error for demo session %s: %s", session_id, exc)

    async def stream_ai_reply(
        user_msg: str,
        history: list,
        client: httpx.AsyncClient,
        paused_flag: dict,
    ) -> str:
        _, answered_desc, unanswered_desc, unanswered_list = format_qa_descriptions(
            all_questions, current_answers
        )
        next_q_label = "（请检查是否还有未填项）"
        if unanswered_list:
            next_q_label = unanswered_list[0].get("id") or unanswered_list[0].get("label")

        proj_title_label = project_title or "(未提供專案名稱)"
        proj_summary_label = project_summary or "(未提供專案摘要)"
        unanswered_count = len(unanswered_list)

        system_prompt = f"""
你是一位友善的專案規劃助理，正在協助使用者填寫【{grant_name}】。

專案名稱：{proj_title_label}
專案摘要：{proj_summary_label}

【目前系統記錄狀態】
(可能略有延遲，請以最新對話為準)
已填（Do NOT ask these）：{answered_desc}
待填：{unanswered_desc}
尚未填寫題數：{unanswered_count} 題
總題數：{len(all_questions)} 題
完成百分比：{len(answered_desc.splitlines())} / {len(all_questions)}

【任務】
回應使用者的最新輸入。若使用者提供了資訊，請進行確認或摘要（例如：「好的，已記錄……」）。
摘要或者幫忙填寫的欄位内容請確保在一個段落以内，不要列點導致太長。
若使用者剛剛回答了某個【待填】問題，請自然地接續詢問下一個欄位：{next_q_label}。
若使用者的回答不清楚，請不需要直接詢問下一個欄位，先進一步追問以釐清。
每詢問一個問題的時候，可以根據上下文生成建議性的答案輔助用戶。
需要使用鼓勵方式，并且需要補充說目前還剩多少題未完成，讓用戶不那麽快放棄。
在全部問題都回答完畢之後，看系統記錄的"已填"選項。一次過列出來所有"無"，"等下填寫"，"空"之類的答案的欄位，并且建議用戶填寫他們以優化計畫書內容。
完成後，推薦用戶點擊右下角的「輸出完整推演」按鈕來產出完整計畫書文本。

【隱藏回復欄位格式】
- 當你確認某個欄位已完成或你代為生成了內容或優化內容時，請在可見回覆結束後追加一段隱藏資訊，必須要和你回復用戶的資訊一摸一樣。
- 不需要畫分割綫，首行輸出 `【回復結束】【隱藏回復欄位+答案】`，末行輸出 `【隱藏回復結束】`。
- 隱藏段落中每行輸出 `欄位ID -- 答案內容`（用雙空格加連字號來分隔），可列出多個欄位。
- 欄位 ID 請使用系統提供的問題 ID（例如 三、解決辦法::商業模式運作流程），不要自行取名。
- 這些標記只供系統讀取，前端會自動隱藏。

【排版】
排版緊凑，重點内容/副標題使用「粗體」。
參考回復模板：**完成欄位確認**（如果有）-> **還剩幾題**（並包含鼓勵語句）-> **下一題問題** -> 💡**填寫小提醒**。
只有填寫小提醒會有 💡。
在講述還剩几題的時候，使用一條長橫綫分隔來區分還剩幾題和下一題的題目。

注意：請根據對話歷史流暢回應。即使系統顯示某欄位為「待填」，只要使用者剛剛在對話中已回答，請視為已填並繼續流程。
"""

        messages = get_chat_messages(system_prompt, history, last_user_msg=user_msg, limit=10)
        await websocket.send_json({"event": "chunk_start"})
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
            await websocket.send_json({"event": "done"})
        except Exception as exc:
            logger.error("Stream error: %s", exc)
            await websocket.send_json({"event": "error", "message": str(exc)})
        return "".join(full_response).strip()

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
            db_answers = stored_answer_state.get("chat_answers") or {}
            db_meta = normalize_meta_payload(stored_answer_state.get("chat_answers_meta"))
            frontend_answers = init_data.get("current_answers", {}) or {}
            frontend_meta = normalize_meta_payload(init_data.get("current_answers_meta"))
            current_answers = {**db_answers, **frontend_answers}
            current_answer_meta = {**db_meta, **frontend_meta}

        if not conversation_history_records:
            for h in init_data.get("history") or []:
                if isinstance(h, dict) and h.get("content"):
                    conversation_history_records.append(build_history_entry(h.get("role"), h.get("content")))

        await websocket.send_json({
            "event": "ready",
            "message": "系统就绪",
            "interaction_count": interaction_count,
            "interaction_limit": DEMO_INTERACTION_LIMIT,
        })

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
                    "（用户刚进入，请根据项目名称和項目描述开始引导）",
                    conversation_history_records,
                    client,
                    paused_flag,
                )
                if first_reply:
                    # Buffer token usage from the opening turn (drained on claim).
                    await supabase_service.append_demo_usage_log(
                        session_id,
                        model_info,
                        getattr(llm_service, "_last_response_json", {}) or {},
                        action="生成對話",
                    )
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
                    for field_id, value in incoming_answers.items():
                        previous_value = current_answers.get(field_id)
                        current_answers[field_id] = value
                        if previous_value != value and field_id not in provided_meta_keys:
                            touch_meta_field(current_answer_meta, field_id)

                if not user_msg:
                    continue

                # Demo cap: refuse new turns once the visitor has hit the limit.
                if interaction_count >= DEMO_INTERACTION_LIMIT:
                    await websocket.send_json({
                        "event": "limit_reached",
                        "interaction_count": interaction_count,
                        "interaction_limit": DEMO_INTERACTION_LIMIT,
                        "register_url": DEMO_REGISTER_REDIRECT_URL,
                        "session_id": session_id,
                    })
                    continue

                user_entry = build_history_entry("user", user_msg)

                async with httpx.AsyncClient(timeout=60.0) as client:
                    ai_reply = await stream_ai_reply(
                        user_msg, conversation_history_records, client, paused_flag
                    )
                    if paused_flag.get("value"):
                        paused_flag["value"] = False
                        continue

                    # Buffer token usage for this turn (drained on claim).
                    await supabase_service.append_demo_usage_log(
                        session_id,
                        model_info,
                        getattr(llm_service, "_last_response_json", {}) or {},
                        action="生成對話",
                    )

                    conversation_history_records.append(user_entry)
                    if ai_reply:
                        conversation_history_records.append(build_history_entry("assistant", ai_reply))

                    hidden_answers = extract_hidden_field_responses(ai_reply)
                    if hidden_answers:
                        clean_filled = normalize_filled_fields(hidden_answers, all_questions)
                        current_answers.update(clean_filled)
                        for field_id in clean_filled.keys():
                            touch_meta_field(current_answer_meta, field_id)

                    interaction_count = await supabase_service.increment_demo_interaction(session_id)
                    await save_state_to_db()

                    if interaction_count >= DEMO_INTERACTION_LIMIT:
                        await websocket.send_json({
                            "event": "limit_reached",
                            "interaction_count": interaction_count,
                            "interaction_limit": DEMO_INTERACTION_LIMIT,
                            "register_url": DEMO_REGISTER_REDIRECT_URL,
                            "session_id": session_id,
                        })

        finally:
            if not reader_task.done():
                reader_task.cancel()

    except Exception as exc:
        logger.error("WebSocket endpoint error: %s", exc, exc_info=True)
        try:
            await websocket.close()
        except Exception:
            pass
