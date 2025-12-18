# 使用ai生成内容功能的api

import asyncio
import httpx
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
import logging
import json
from pathlib import Path

from app.models import (
    GenerateRequest,
    SectionGenerateResponse,
    AutoFillRequest,
    SyntheticInputRequest,
    ChatGuidanceRequest,
    ChatGuidanceResponse,
)
from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService
from .dependencies import get_llm_service, get_supabase_service
from app.utils.extract_json import extract_json_block  
from typing import Dict, Any
from app.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

OPENAI_FILES_ENDPOINT = "https://api.openai.com/v1/files"
OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"
ALLOWED_FILE_SUFFIXES = {".pdf", ".txt"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB hard cap

# ========== Helper Functions for System Prompts ==========

def _get_word_import_system_prompt(sections: list) -> str:
    """生成 Word 導入模式的系統提示"""
    section_list = "\n".join(f"- {i+1}. {s.section_id} ({s.section_name})" for i, s in enumerate(sections))
    return f"""
你是一個"高精度、零臆測"的文檔→JSON 映射引擎。

【任務】
根據 Word 文檔內容，將文本逐字映射進 JSON。  
你可以推斷文本段落應屬於哪個章節，但你**絕對禁止創造內容**。

【最重要原則】
- ✅ 你可以判斷哪段文本屬於哪個 section
- ✅ 只能複製文檔中的字，逐字填入
- ❌ 不得補內容
- ❌ 不得改寫
- ❌ 不得解釋
- ✅ 找不到 → `""` 或 `null`（永遠不要猜）

【章節清單】（共 {len(sections)} 個章節）
{section_list}

【違規定義】
以下行為視為「輸出失敗」：
- 添加文檔中沒有的字
- 改寫語句
- 為了填滿欄位而推斷內容
- 生成摘要、重述或合併句子

【操作流程】
1. 找到章節標題
2. 判斷每段文字屬於哪個 section（允許推斷章節對應）
3. 將原文逐字貼入對應字段
    - 若找不到 → `""` 或 `null`
4. 只輸出 JSON，禁止解釋、註解、額外文字

【校驗】
輸出前你必須自查：
- ❓ 是否每字都來自原文？
- ❓ 是否沒有添加任何推論或補文字？
- ✅ 若有不確定 → 使用 `""`

若你違反上述規則，你的輸出將被丟棄。
最後，在main_idea或者summary類的字段中，你可以適當地對內容進行小幅度的總結和概括**。

輸出格式：JSON 物件，各章節映射如下
```json
{{
  "section_id_1": {{...}},
  "section_id_2": {{...}},
  ...
}}
```
"""

def _get_default_system_prompt(sections: list) -> str:
    """生成默認模式的系統提示"""
    return f"""
你是一個高精度、有上下文感知能力的文本提取引擎。你的唯一任務是將一份結構化良好的文檔，**逐個章節地、精確地**映射到對應的 JSON 結構中。你必須像一個遵循嚴格程序的機器人，盡量將章節内的内容全部一一對應，絕不跨越章節邊界提取信息，也絕不對文本內容做任何形式的解讀。

**重要提醒：你必須為以下所有章節生成輸出（共 {len(sections)} 個章節）：**
{chr(10).join(f'- {i+1}. {s.section_id} ({s.section_name})' for i, s in enumerate(sections))}

**絕對核心指令 (不可違背)：**

1.  **絕對原文主義——你是複製機器，不是作家**:
    *   所有填入 JSON 字段的值，**必須是從原始文檔中 100% 完全複製的文本**。
    *   **內容的無差別對待 (Indiscriminate Treatment of Content):** 你必須將文檔中所有可見的字符都視為純文本進行複製。這條規則沒有例外，尤其包括：
        *   **圖片佔位符:** 任何形式的圖片描述或佔位符，例如 **`【圖：企業的外觀】`** 或 `[Chart: Q3 Revenue]`，都**必須**被一字不差地當作普通字符串複製下來。它們是文本的一部分。
        *   **任何註釋或標記:** 只要是文本形式存在於文檔中的內容，就要複製。
    *   **【極度嚴禁】** 進行任何形式的摘要、總結、重寫、釋義或風格調整。
    *   **【極度嚴禁】** 創造、推斷或補充原文沒有明確寫出的任何信息。
    *   **【極度嚴禁】** 修正原文的任何錯字、語法錯誤或格式。原文是什麼，你就複製什麼。

2.  **JSON Schema 是唯一藍圖 - 必須為所有章節生成內容**:
    *   你必須為輸入中提供的**每一個** `section_id` 生成一個對應的 JSON 對象。
    *   生成的 JSON 必須**完美無瑕**地符合該 `section_id` 對應的 JSON Schema 結構。
    *   **沒有例外：即使某個章節在文檔中找不到完全對應的內容，你也應該返回該章節的 JSON 結構，並將字段設為空字符串或 null**。

2.  **你能增加的只有numbering或者bullet point**:
    *   你可以為了更好地匹配 JSON Schema 的要求，**在複製的文本前添加編號或項目符號**（例如 "1.", "•" 等）。
    *   你也能夠在table文字轉化成string的途中排版整理順序
    *   但你絕對不能改動文本本身的內容**，包括文字、標點符號、大小寫等。

3.  **結構化對應與範圍鎖定 (Structural Correspondence and Scope Locking)**:
    *   **核心假設：** 輸入文檔的章節結構與你收到的 `sections` 列表（包含 `section_id` 和 `section_name`）是**一一對應**的。
    *   **工作流程：** 你的工作是**隔離地、逐個章節**進行的，絕不混合信息。
        1.  **定位：** 處理第一個 `section_id`。首先在文檔中找到與其 `section_name` 完全對應的章節標題。
        2.  **鎖定範圍：** 該章節的有效內容範圍是**從這個標題開始，到下一個主要章節標題出現之前的所有文本**。這就是你的「工作區」。
        3.  **範圍內提取：** **只能**使用這個「工作區」內的文本來填充當前 `section_id` 的 JSON 字段。
        4.  **禁止越界：** **嚴禁**在填充當前章節的 JSON 時，去查看或提取其他章節內的任何文字。
        5.  **重複：** 完成一個章節後，移動到下一個 `section_id`，並重複以上「定位->鎖定->提取」的過程。

4.  **空值處理的機械規則**:
    *   如果在**當前鎖定的章節範圍內**，確定**沒有**能對應某個 Schema 字段的文本，該字段的值必須設為 `null`。如果 Schema 要求該字段為 string 類型，則設為空字符串 `""`。

5.  **最終輸出格式的絕對純淨**:
    *   你的最終輸出**只能是**一個單一的、格式完全正確的 JSON 對象。
    *   這個 JSON 對象的 `key` 是 `section_id`，`value` 是填充好的、符合 schema 的 JSON 對象。
    *   **必須包含所有 {len(sections)} 個章節的輸出**。
    *   **絕不**在 JSON 輸出之外附加任何說明、註釋或任何額外文本。

    **示例輸出結構 (你的最終產出必須是這個樣子，沒有其他任何文字):**
    ```json
    {{
        "section_id_1": {{...完整的 JSON 內容...}},
        "section_id_2": {{...完整的 JSON 內容...}},
        "section_id_3": {{...完整的 JSON 內容...}}
    }}
    ```
    """

router = APIRouter(
    prefix="/api",
    tags=["Generation"]
)


def _build_field_analysis_prompt(
    field_title: str,
    field_description: str,
    subfield_label: str,
    current_value: str,
) -> str:
    readable_title = field_title or "未命名欄位"
    readable_desc = field_description or "無額外描述"
    readable_label = subfield_label or readable_title
    preserved_value = current_value.strip() or "(目前沒有使用者輸入)"

    return f"""
你是一位嚴謹的計畫書欄位輔助編輯助手。根據使用者上傳的 PDF / TXT 文件（內含可供 OCR 的圖像），請完成以下任務：

1. 針對欄位〈{readable_title}〉，理解欄位說明「{readable_desc}」與子欄位標籤「{readable_label}」。
2. 生成更新後的 subfield 文字（enhanced_value）。新的文字不要包含原始輸入的文字意思以免文字重叠：
<<<ORIGINAL_VALUE_START>>>
<<<ORIGINAL_VALUE_END>>>

規則：
- enhanced_value 可以根據用戶輸入的文件來寫，但不要包含原始輸入的文字意思以免文字重叠。
- 請記住， enhanced value 將會直接stack在original value後面，因此必須是用戶輸入全新的內容，不能與原始輸入的內容重複。
- 僅根據文件所提供的內容進行推論，不要臆測不存在的資訊。
- 以繁體中文輸出。

請輸出唯一一個 JSON 物件，格式如下：
{{
  "enhanced_value": "..."
}}
"""


def _extract_output_text(payload: Dict[str, Any]) -> str:
    direct_text = payload.get("output_text")
    if direct_text:
        if isinstance(direct_text, list):
            return "\n".join(direct_text)
        return str(direct_text)

    for block in payload.get("output", []):
        for content in block.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]

    raise ValueError("OpenAI Responses payload did not include text output.")


@router.post(
    "/chat_guidance",
    response_model=ChatGuidanceResponse,
    summary="產生對話式引導問題",
)
async def generate_chat_guidance_message(
    request_data: ChatGuidanceRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
):
    """使用 GPT-4o-mini 生成更自然的提問內容，協助蒐集欄位答案。"""

    model_registry = getattr(request.app.state, "model_registry", {}) or {}
    model_info = model_registry.get("gpt-4o-mini")
    if not model_info:
        model_info = {
            "id": "gpt-4o-mini",
            "provider": "openai",
            "type": "external",
        }

    answer_lines = [
        f"- {label}: {value.strip()}"
        for label, value in (request_data.answers or {}).items()
        if value and value.strip()
    ]
    answers_summary = (
        "\n".join(answer_lines) if answer_lines else "尚未收集到其他欄位的答案。"
    )

    history_lines = []
    for entry in request_data.history[-8:]:
        content = (entry.content or "").strip()
        if not content:
            continue
        role_label = "使用者" if entry.role == "user" else "AI"
        history_lines.append(f"{role_label}: {content}")
    history_summary = (
        "\n".join(history_lines) if history_lines else "尚未開始任何對話。"
    )

    system_prompt = (
        "You are a proposal-planning coach that interviews the user field by field. "
        "Respond in Traditional Chinese, keep the tone friendly and concise, and always conclude with a single open question. "
        "Reference prior context when useful, but never invent information or ask about multiple fields at once."
    )

    user_prompt = f"""
專案主題：{request_data.grant_name or request_data.grant_id}
模板：{request_data.template_name or request_data.template_id}

目前要蒐集的欄位：
- ID: {request_data.question.id}
- 名稱: {request_data.question.label}
- 引導說明: {request_data.question.prompt}

已完成的其他欄位答案：
{answers_summary}

最近的對話摘要：
{history_summary}

請根據上述資訊產生下一句 AI 要說的話。語氣親切自然，先銜接上一則內容，再清楚請求使用者補充與該欄位相關的細節，最後用一個問題作結。僅詢問單一欄位。
請以 JSON 物件輸出：
{{
  "message": "<AI 要說的繁體中文句子>"
}}
    """.strip()

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            raw_output, llm_error = await llm_service.call_external_api(
                client,
                model_info,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                is_json_output=True,
            )
    except Exception as exc:
        logger.error("Chat guidance request failed: %s", exc, exc_info=True)
        raw_output, llm_error = None, {"error": str(exc)}

    if llm_error or not raw_output:
        fallback_message = (
            request_data.question.prompt.strip()
            if request_data.question.prompt
            else "請分享更多細節，協助我理解。"
        )
        return ChatGuidanceResponse(
            question_id=request_data.question.id,
            message=fallback_message,
        )

    try:
        parsed = json.loads(raw_output)
        ai_message = (parsed.get("message") or "").strip()
    except json.JSONDecodeError:
        ai_message = (raw_output or "").strip()

    if not ai_message:
        ai_message = (
            request_data.question.prompt.strip()
            if request_data.question.prompt
            else "請分享更多細節，協助我理解。"
        )

    return ChatGuidanceResponse(
        question_id=request_data.question.id,
        message=ai_message,
    )

@router.post("/generate_plan")
async def generate_plan( 
    request_data: GenerateRequest,
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
):
    """主功能 -> 生成完整計劃書，可生成多候选版本"""
    
    # 從 app_state 獲取所有配置
    app_state = request.app.state
    all_grants_config = getattr(app_state, "all_grants_config", [])
    
    # 查找指定的 grant 和 template
    grant_config = None
    template_config = None
    
    for grant in all_grants_config:
        if grant.id == request_data.grant:
            grant_config = grant
            for template in grant.templates:
                if template.id == request_data.template:
                    template_config = template
                    break
            break
    
    if not template_config:
        raise HTTPException(
            status_code=400, 
            detail=f"Template {request_data.template} not found in Grant {request_data.grant}."
        )
    
    # 從 template_config 獲取所有 sections
    sections = template_config.sections
    if not sections:
        raise HTTPException(status_code=400, detail="No sections found in the selected template.")
    
    num_candidates = request_data.num_candidates

    async with httpx.AsyncClient() as client:
        # 每個 section 生成 num_candidates 個候選版本
        tasks = [
            llm_service.generate_section_content(
                http_session=client,
                grant_id=request_data.grant,
                template_id=request_data.template,
                section_id=s.id,
                user_input=request_data.user_input,
                app_state=app_state,
                user_id=request_data.user_id,
                supabase_service=supabase_service,
                is_external=request_data.is_external,
            )
            for s in sections
            for _ in range(num_candidates)
        ]
        results = await asyncio.gather(*tasks)

    # 組織輸出：每個 section_id -> [候選內容...]
    plan_content = {}
    for res in results:
        section_id = res.section_id
        if section_id not in plan_content:
            plan_content[section_id] = []
        plan_content[section_id].append(res.dict())

    return plan_content


@router.websocket("/ws/chat_guidance")
async def websocket_chat_guidance(websocket: WebSocket):
    """WebSocket 端點：智能多轮对话，自动识别并填充字段。"""
    await websocket.accept()
    llm_service = websocket.app.state.llm_service
    
    try:
        # 接收初始 payload（第一次握手）
        data = await websocket.receive_json()
        
        grant_id = data.get("grant_id", "")
        template_id = data.get("template_id", "")
        grant_name = data.get("grant_name", "")
        template_name = data.get("template_name", "")
        all_questions = data.get("all_questions", [])  # 所有问题列表
        current_answers = data.get("current_answers", {})  # 已填答案
        history = data.get("history", [])  # 聊天历史
        
        if not all_questions:
            await websocket.send_json({"event": "error", "message": "Missing all_questions"})
            await websocket.close()
            return
        
        model_registry = getattr(websocket.app.state, "model_registry", {}) or {}
        model_info = model_registry.get("gpt-5.1-chat-latest") or {
            "id": "gpt-5.1-chat-latest",
            "provider": "openai",
            "type": "external",
        }
        
        # 发送初始提示
        await websocket.send_json({
            "event": "ready",
            "message": "系统已连接，等待您的回答..."
        })
        
        # 生成第一个问题
        first_question_prompt = f"""
你是一个友好的项目规划助手。用户刚刚开始填写一个关于"{grant_name or grant_id}"的项目企划。

请用友好、自然的语气提问，帮助用户开始这个过程。

只输出你要说的一句话或两句话，不要包含任何JSON或结构化数据。例如："你好！我是你的项目规划助手。为了帮助你更好地制定这个计划，我想先了解一下你的核心想法。能告诉我这个项目的主要创意或目标是什么吗？"
"""
        
        # 流式生成第一个问题
        await websocket.send_json({"event": "chunk_start"})
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async for chunk in llm_service.stream_external_api(
                    client,
                    model_info,
                    [{"role": "user", "content": first_question_prompt}]
                ):
                    await websocket.send_json({"event": "chunk", "data": chunk})
                
                await websocket.send_json({"event": "done"})
            except Exception as e:
                logger.error(f"Initial question error: {e}", exc_info=True)
                await websocket.send_json({"event": "error", "message": str(e)})
        
        # 主对话循环：持续接收用户消息并进行分析
        while True:
            try:
                # 接收用户消息
                user_data = await websocket.receive_json()
                user_message = user_data.get("user_message", "").strip()
                
                if not user_message:
                    await websocket.send_json({
                        "event": "error", 
                        "message": "请输入有效的消息"
                    })
                    continue
                
                # 更新当前答案（用户可能在 UI 中更新了）
                current_answers = user_data.get("current_answers", current_answers)
                
                # 构建所有问题的列表描述
                questions_desc = "\n".join([
                    f"- {q.get('label', q.get('id'))}: {q.get('prompt', '')}"
                    for q in all_questions
                ])
                
                answered_desc = "\n".join([
                    f"- {label}: {value[:100]}..." if len(value) > 100 else f"- {label}: {value}"
                    for label, value in current_answers.items()
                    if value and value.strip()
                ]) or "（无）"
                
                unanswered = [
                    q for q in all_questions
                    if q.get("id") not in current_answers or not current_answers.get(q.get("id"), "").strip()
                ]
                unanswered_desc = "\n".join([
                    f"- {q.get('label', q.get('id'))}"
                    for q in unanswered
                ]) or "（全部已填）"
                
                # 第一步：分析用户消息并提取字段
                analyze_prompt = f"""
你是一个智能项目规划助手。用户刚刚说了一句话，请分析他的回答对应了哪些字段。

【所有可填字段】
{questions_desc}

【已填字段】
{answered_desc}

【待填字段】
{unanswered_desc}

【用户最后说的话】
{user_message}

请完成以下任务：
1. 分析用户的话对应了哪些字段（可能是0个、1个或多个）
2. 提取用户对这些字段的回答内容（直接从用户的话中提取，不要改写）
3. 决定是否需要追问（如果回答不够详细或不够清楚）

请输出 JSON：
{{
  "filled_fields": {{
    "field_id_1": "用户提供的答案内容",
    "field_id_2": "..."
  }},
  "needs_clarification": true or false,
  "reasoning": "简要说明为什么这样分析"
}}
"""
                
                # 调用 GPT 分析用户消息
                async with httpx.AsyncClient(timeout=60.0) as client:
                    analysis_response, error = await llm_service.call_external_api(
                        client,
                        model_info,
                        [{"role": "user", "content": analyze_prompt}],
                        is_json_output=True
                    )
                
                if error or not analysis_response:
                    logger.error(f"Failed to analyze user message: {error}")
                    filled_fields = {}
                    needs_clarification = False
                else:
                    try:
                        import json as json_lib
                        analysis = json_lib.loads(analysis_response)
                        filled_fields = analysis.get("filled_fields", {})
                        needs_clarification = analysis.get("needs_clarification", False)
                    except Exception as e:
                        logger.error(f"Failed to parse analysis: {e}")
                        filled_fields = {}
                        needs_clarification = False
                
                # 发送填充的字段信息
                await websocket.send_json({
                    "event": "filled",
                    "data": filled_fields
                })
                
                # 更新 current_answers 中被识别出来的字段
                for field_id, value in filled_fields.items():
                    if value and str(value).strip():
                        current_answers[field_id] = str(value).strip()
                
                # 第二步：生成 AI 的下一句话
                # 决定下一个要问的字段
                next_question = None
                for q in all_questions:
                    qid = q.get("id")
                    if qid not in current_answers or not current_answers[qid].strip():
                        # 如果这个字段没填，检查是否刚刚用户回答了它
                        if qid not in filled_fields:
                            next_question = q
                            break
                
                conversation_prompt = f"""
你是一个友好的项目规划助手。继续和用户自然对话。

【项目信息】
主题：{grant_name or grant_id}
模板：{template_name or template_id}

【用户刚才说】
{user_message}

【已填字段】
{answered_desc}

【未填字段】
{unanswered_desc}

{"【接下来应该确认什么】" if needs_clarification else "【接下来应该询问】"}
{next_question.get("label") if next_question else "（所有字段已填完）"}

请按照以下要求生成回应：
1. 确认或感谢用户的输入
2. 如果需要澄清，用友好的方式进行确认，例如："你是说...对吗？"
3. 如果还有未填字段，自然地过渡到下一个话题
4. 语气亲切、自然，像是真实的对话，不要提及"字段"、"表单"等
5. 如果所有字段都已填完，恭喜用户并提示可以生成计划了

只输出你要说的一句话或几句话，不要包含任何JSON或结构化数据。
"""
                
                # 开始流式生成 AI 回复
                await websocket.send_json({"event": "chunk_start"})
                async with httpx.AsyncClient(timeout=60.0) as client:
                    try:
                        async for chunk in llm_service.stream_external_api(
                            client,
                            model_info,
                            [{"role": "user", "content": conversation_prompt}]
                        ):
                            await websocket.send_json({"event": "chunk", "data": chunk})
                        
                        # 流式结束，发送 done 信号
                        await websocket.send_json({"event": "done"})
                    except Exception as e:
                        logger.error(f"Streaming error: {e}", exc_info=True)
                        await websocket.send_json({"event": "error", "message": str(e)})
            
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected during message loop")
                break
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({"event": "error", "message": str(e)})
        except:
            pass
        await websocket.close()


@router.post("/generate_synthetic_input", response_model=Dict[str, Any])
async def generate_synthetic_input(
    req: SyntheticInputRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """根據模式生成用戶輸入，使用統一的動態字段格式。
    
    支持兩種模式：
    - 'random': 根據補助主題和模板生成新的隨機用戶輸入
    - 'reverse': 根據已填充的動態字段內容生成摘要
    
    返回格式統一為 { main_idea, dynamic_fields: { label: value } }
    """
    model_info = request.app.state.model_registry.get("gpt-5-mini")
    if not model_info:
        raise HTTPException(status_code=500, detail="GPT-5-mini model not configured for synthetic generation.")

    # 驗證請求模式
    if req.mode not in ['random', 'reverse']:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'random' or 'reverse'.")
    
    # Reverse 模式需要 plan_content
    if req.mode == 'reverse' and not req.plan_content:
        raise HTTPException(status_code=400, detail="plan_content is required for 'reverse' mode.")

    # 使用統一的動態字段標籤格式
    field_labels = "\n".join([f"- {field.label}" for field in req.dynamic_fields_schema])
    
    prompt = ""
    if req.mode == 'random':
        # 隨機生成模式：根據補助主題生成新的用戶輸入
        prompt = f"""
        你是一位嚴謹的商業策略專家，負責生成高品質的 AI 訓練資料。

        ---

        ### 任務說明
        1. 你需要**先構思一個與「{req.grant_name}」相關的新穎且具吸引力的商業／專案構想**。
        2. 然後，**僅根據你構思的這個點子**，依序回答下列所有問題。
        3. **所有問題都必須回答，不得遺漏、不得省略任何一題。**
        4. **問題的鍵名（key）必須與以下提供的文字完全相同，不得改寫、增刪、重新編號或重新命名。**

        ---

        ### 關於「鍵名」的嚴格規則
        - 鍵名必須**完全一致**（包含標點符號、括號、數字、中文序號、空格）。
        - 不可自行添加或刪除任何編號。
        - 不可更改任何鍵名。
        - 如果有 N 個問題，你的輸出中 **dynamic_fields 物件也必須包含 N 個鍵**，一題都不能少。

        ---

        ### 輸出格式（請嚴格遵守 JSON 結構）
        你必須回傳**單一有效 JSON 物件**，且前後不能有任何額外文字或註解。  
        結構如下：

        ```json
        {{
        "main_idea": "<核心專案構想（單段文字）>",
        "dynamic_fields": {{
            "<question_label_1>": "<針對問題 1 的詳細文字回答>",
            "<question_label_2>": "<針對問題 2 的詳細文字回答>",
            ...
        }}
        }}
        ```
        
        📚 背景資訊
        補助主題：{req.grant_name}
        計畫書模板：{req.template_name}

        📝 問題清單（這些是 dynamic_fields 的鍵名，請逐一完整回答）：
        {field_labels}

        ⚠️ 重要提醒：
        - 你的回答必須包含所有上述問題的鍵名
        - 鍵名不可被改動、不可新增或刪除
        - JSON 需可被標準 JSON parser 正確解析
        - 若任一問題遺漏、鍵名變動或格式錯誤，任務即視為失敗

        現在，請直接生成最終的 JSON。
        """
    elif req.mode == 'reverse' and req.plan_content:
        # Reverse 模式：根據計畫書內容反推動態字段
        plan_content_str = json.dumps(req.plan_content, ensure_ascii=False, indent=2)
        
        prompt = f"""
        你是一位頂級的商業內容分析和反推專家。
        你的任務是根據已生成的計畫書內容，反推出原始的核心思想和動態字段內容。
        
        **任務說明：**
        1. 為整個計畫書內容生成一個簡潔的核心想法摘要 (`main_idea`)。
        2. 根據計畫書內容，為每個提供的動態字段標籤生成對應的內容。
        3. 生成的內容應該是對計畫書內容的有效總結，而不是逐字複製。

        **生成規則：**
        1. **使用提供的標籤作為鍵**: 輸出必須包含所有提供的標籤，且鍵名必須完全相同。
        2. **提煉核心內容**: 將計畫書的相關內容提煉成簡潔、核心的表述。
        3. **保留邏輯完整性**: 每個字段的內容應該邏輯清晰，能獨立理解。
        4. **統一格式**: 所有值都應保持為 string 類型。

        **必須使用的動態字段標籤（鍵名）：**
        {field_labels}

        **最終輸出格式：**
        你必須回傳一個有效的 JSON 物件，結構如下：
        ```json
        {{
            "main_idea": "<對計畫書的核心想法摘要，約 30-50 字>",
            "dynamic_fields": {{
                "<label_1>": "<根據計畫書內容提煉的內容>",
                "<label_2>": "<根據計畫書內容提煉的內容>",
                ...
            }}
        }}
        ```

        ---
        **待分析的計畫書內容：**
        ```json
        {plan_content_str}
        ```
        ---

        ### 重要提醒：
        - 所有 key 必須與上述提供的標籤完全一致
        - 必須包含所有提供的標籤，一個都不能少
        - 只進行總結和提煉，不改變內容的原意
        - JSON 必須有效且可被標準 parser 解析
        - 不要包含額外的解釋或註釋

        現在請生成最終的 JSON。
        """
    else:
        raise HTTPException(status_code=400, detail="Invalid mode or missing required fields.")

    try:
        async with httpx.AsyncClient() as client:
            messages = [{"role": "user", "content": prompt}]
            response, error = await llm_service.call_external_api(client, model_info, messages, is_json_output=True)

            
            response_text = response
            # 使用統一的提取邏輯
            extracted_json, parse_error = extract_json_block(response_text, "synthetic_input")
            
            if parse_error:
                raise HTTPException(status_code=500, detail=f"Failed to parse LLM JSON output: {parse_error}")
            
            # 返回統一格式
            return {
                "main_idea": extracted_json.get("main_idea", ""),
                "dynamic_fields": extracted_json.get("dynamic_fields", {})
            }
    except Exception as e:
        logger.error(f"Error in generate_synthetic_input: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating synthetic input: {str(e)}")
      
@router.post("/autofill_from_document", summary="從文檔自動填充計劃書內容")
async def autofill_from_document(
    request_data: AutoFillRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    user_id: str = "dba4dabc-a24d-4e1a-aa2b-b239d06a8cf5"
):
    """
    接收文檔純文字和多個章節的 schema，
    調用強大的 LLM 來解析文本並填充成結構化的 JSON。
    
    prompt_mode 支持：
    - "default": 用于一般文檔自動填充
    - "word_import": 用于從 Word 文件導入，優化為最大化文本利用率
    """
    all_schemas_info = "\n\n".join(
        f"--- 章節 ID: {s.section_id} | 章節名稱: {s.section_name} ---\n"
        f"JSON Schema:\n{json.dumps(s.json_schema, ensure_ascii=False, indent=2)}"
        for s in request_data.sections
    )

    # 根據 prompt_mode 選擇不同的系統提示
    if request_data.prompt_mode == "word_import":
        system_prompt = _get_word_import_system_prompt(request_data.sections)
    else:
        system_prompt = _get_default_system_prompt(request_data.sections)

    # 構建 User Prompt
    user_prompt = f"""
    這是需要你處理的計劃書文檔全文：
    --- DOCUMENT START ---
    {request_data.document_text}
    --- DOCUMENT END ---

    這是你需要填充的目標 JSON 結構定義：
    {all_schemas_info}

    請根據以上文檔內容和結構定義，生成最終的 JSON 輸出。
    """

    model_registry = request.app.state.model_registry
    model_to_use = model_registry.get("gpt-4.1") or model_registry.get("gpt-5-mini")
    if not model_to_use:
        raise HTTPException(status_code=500, detail="A powerful model like GPT-4/5 is required for this feature.")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            raw_output, llm_error = await llm_service.call_external_api(
                client, 
                model_to_use,  
                messages,  
                is_json_output=True 
            )

        if llm_error:
            raise HTTPException(status_code=500, detail=f"LLM API Error: {llm_error}")

        
        # 解析返回的 JSON 字符串
        filled_data = json.loads(raw_output)
        # 確保所有章節都有內容，缺少的設為空
        formatted_result = {}
        for section in request_data.sections:
            section_id = section.section_id
            if section_id in filled_data:
                formatted_result[section_id] = {"content": filled_data[section_id]}
            else:
                logger.warning(f"Missing section in LLM output: {section_id}")
                formatted_result[section_id] = {"content": {}}

        await supabase_service.log_cost_usage(user_id, model_to_use, messages, raw_output)

        return formatted_result

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        logger.error(f"Raw output: {raw_output}")
        raise HTTPException(status_code=500, detail="LLM did not return a valid JSON object.")
    except Exception as e:
        logger.error(f"Error during document auto-fill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/field_file_analysis", summary="針對單一欄位進行檔案輔助分析")
async def field_file_analysis(
    request: Request,
    files: list[UploadFile] = File(...),
    field_title: str = Form(...),
    field_description: str = Form(""),
    subfield_label: str = Form(""),
    current_value: str = Form(""),
):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key is not configured.")

    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="請至少上傳一個檔案。")
    
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="最多只能同時上傳 5 個檔案。")

    for file in files:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_FILE_SUFFIXES:
            raise HTTPException(status_code=400, detail="僅支援 PDF / TXT 檔案格式。")

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    uploaded_file_ids = []
    prompt = _build_field_analysis_prompt(
        field_title=field_title,
        field_description=field_description,
        subfield_label=subfield_label,
        current_value=current_value,
    )

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            for upload_file in files:
                file_bytes = await upload_file.read()
                if not file_bytes:
                    raise HTTPException(status_code=400, detail=f"檔案 {upload_file.filename} 內容為空。")
                if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                    raise HTTPException(status_code=400, detail="檔案過大，請控制在 20MB 以內。")
                
                upload_resp = await client.post(
                    OPENAI_FILES_ENDPOINT,
                    headers=headers,
                    data={"purpose": "assistants"},
                    files={
                        "file": (
                            upload_file.filename,
                            file_bytes,
                            upload_file.content_type or "application/octet-stream",
                        )
                    },
                )
                upload_resp.raise_for_status()
                file_id = upload_resp.json().get("id")
                if not file_id:
                    raise HTTPException(status_code=500, detail=f"OpenAI file upload failed for {upload_file.filename}.")
                uploaded_file_ids.append(file_id)

            content_items = [{"type": "input_text", "text": prompt}]
            for fid in uploaded_file_ids:
                content_items.append({"type": "input_file", "file_id": fid})

            responses_resp = await client.post(
                OPENAI_RESPONSES_ENDPOINT,
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "model": "gpt-4.1-mini",
                    "input": [
                        {
                            "role": "user",
                            "content": content_items,
                        }
                    ],
                    # "modalities": ["text"],
                    "max_output_tokens": 900,
                    "temperature": 0.2,
                    "metadata": {"feature": "field_file_analysis"},
                },
            )
            responses_resp.raise_for_status()

            output_text = _extract_output_text(responses_resp.json())
            print("Extracted output text:", output_text)
            parsed = json.loads(output_text)

    except httpx.HTTPStatusError as e:
        detail = e.response.text if e.response else str(e)
        logger.error("OpenAI API returned an error: %s", detail)
        raise HTTPException(status_code=502, detail="分析服務暫時無法使用，請稍後再試。")
    except json.JSONDecodeError:
        logger.error("OpenAI response parsing failed", exc_info=True)
        raise HTTPException(status_code=500, detail="AI 回傳的格式無法解析。")
    except Exception as e:
        logger.error("Unexpected error during field file analysis: %s", repr(e))
        raise HTTPException(status_code=500, detail="分析過程發生未知錯誤。")
    finally:
        if uploaded_file_ids:
            try:
                async with httpx.AsyncClient(timeout=30.0) as cleaner:
                    for fid in uploaded_file_ids:
                        await cleaner.delete(
                            f"{OPENAI_FILES_ENDPOINT}/{fid}",
                            headers=headers,
                        )
            except Exception:
                logger.warning("Failed to delete temporary OpenAI files")

    enhanced_value = parsed.get("enhanced_value", "").strip()
    original_value = current_value.strip()
    if original_value and original_value not in enhanced_value:
        enhanced_value = f"{original_value}\n\n{enhanced_value}".strip()

    filenames = ", ".join([f.filename for f in files])
    return JSONResponse({"value": enhanced_value, "filenames": filenames})

