# 使用ai生成内容功能的api

from io import BytesIO
import asyncio
import httpx
from datetime import datetime, timezone
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
from uuid import uuid4
import re
from pathlib import Path

from app.models import (
    GenerateRequest,
    PlanRevisionRequest,
    SectionGenerateResponse,
    AutoFillRequest,
    SyntheticInputRequest,
)
from app.core.app_jwt import decode_app_access_token
from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService
from .dependencies import get_llm_service, get_supabase_service, get_current_user_id
from app.utils.extract_json import extract_json_block  
from typing import Dict, Any, Optional, List
from app.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

OPENAI_FILES_ENDPOINT = "https://api.openai.com/v1/files"
OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"
ALLOWED_FILE_SUFFIXES = {
    ".pdf",
    ".txt",
    ".ppt",
    ".pptx",
    ".jpg",
    ".jpeg",
    ".png",
}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB hard cap

HIDDEN_REPLY_BLOCK_PATTERN = re.compile(
    r"【回復結束】【隱藏回復欄位\+答案】(.*?)【隱藏回復結束】",
    re.DOTALL,
)
RESPONSE_END_MARKER = "【回復結束】"

def extract_hidden_field_responses(text: Optional[str]) -> Dict[str, str]:
    # 從 LLM 回應中提取隱藏欄位的值，根據特定格式解析出欄位 ID 和對應的值，返回一個字典。
    if not text:
        return {}
    match = HIDDEN_REPLY_BLOCK_PATTERN.search(text)
    if not match:
        return {}
    block_content = match.group(1)
    extracted: Dict[str, str] = {}
    for raw_line in block_content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("-"):
            line = line[1:].strip()
        if not line:
            continue
        if " -- " not in line:
            continue
        field_id, value = line.split(" -- ", 1)
        field_key = field_id.strip()
        field_value = value.strip()
        if field_key:
            extracted[field_key] = field_value
    return extracted

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
    # 根據欄位資訊生成分析提示，指導 LLM 生成增強內容，要求完全避免與原始輸入重疊。
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
    # 從 LLM 回應的 payload 中提取文本輸出，優先尋找 direct_text 字段，若無則從 output blocks 中提取，最後嘗試從特定格式的隱藏欄位中提取。
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


@router.post("/generate_plan")
async def generate_plan( 
    request_data: GenerateRequest,
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
    user_id: str = Depends(get_current_user_id),
):
    # 生成完整計畫書，根據指定的 grant 和 template，為每個章節非同步生成多個候選版本，支援外部模型和自訂選擇
    """主功能 -> 生成完整計畫書，可生成多候选版本"""
    
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
    
    project_section_versions: Dict[str, int] = {}
    if request_data.project_id:
        project_record = await supabase_service.get_project_by_id(
            request_data.project_id,
            user_id,
        )
        if not project_record:
            raise HTTPException(status_code=404, detail="Project not found or permission denied")
        project_section_versions = project_record.get("section_versions") or {}

    # 從 template_config 獲取所有 sections
    sections = template_config.sections
    if project_section_versions:
        sections = await supabase_service.hydrate_section_configs_with_versions(
            sections=sections,
            grant_id=request_data.grant,
            template_id=request_data.template,
            section_versions=project_section_versions,
        )
    if not sections:
        raise HTTPException(status_code=400, detail="No sections found in the selected template.")

    
    revision_started_at = datetime.now(timezone.utc)
    revision_context = {
        "grant_id": request_data.grant,
        "template_id": request_data.template,
        "num_candidates": request_data.num_candidates,
        "is_external": request_data.is_external,
        "selected_model": request_data.selected_model,
    }

    if request_data.project_id:
        await supabase_service.log_execution_event(
            project_id=request_data.project_id,
            user_id=user_id,
            event_type="plan_revision_started",
            payload={**revision_context, "started_at": revision_started_at.isoformat()},
        )
    
    generation_started_at = datetime.now(timezone.utc)
    generation_context = {
        "grant_id": request_data.grant,
        "template_id": request_data.template,
        "num_candidates": request_data.num_candidates,
        "is_external": request_data.is_external,
        "selected_model": request_data.selected_model,
    }

    if request_data.project_id:
        await supabase_service.log_execution_event(
            project_id=request_data.project_id,
            user_id=user_id,
            event_type="plan_generation_started",
            payload={**generation_context, "started_at": generation_started_at.isoformat()},
        )

    num_candidates = request_data.num_candidates

    # 獲取該用戶的所有開啟狀態的 commands
    commands_data = await supabase_service.get_commands_by_user_id(user_id)
    
    # 組合 commands 資料和 user_input
    final_user_input = request_data.user_input or ""
    
    if commands_data:
        # 將 commands 資料轉換為文本形式並追加到 user_input
        commands_text = "\n".join([
            f"- {cmd.get('title', '')}: {cmd.get('description', '')}"
            for cmd in commands_data
            if cmd.get('title') or cmd.get('description')
        ])
        
        if commands_text:
            final_user_input = f"{final_user_input}\n\n【來自 Commands 的額外上下文】\n{commands_text}"

    async with httpx.AsyncClient() as client:
        # 每個 section 生成 num_candidates 個候選版本
        tasks = [
            llm_service.generate_section_content(  
                http_session=client,
                grant_id=request_data.grant,
                template_id=request_data.template,
                section_id=s.id,
                user_input=final_user_input,
                app_state=app_state,
                user_id=user_id,
                supabase_service=supabase_service,
                is_external=request_data.is_external,
                selected_model=request_data.selected_model,
                project_id=request_data.project_id,
                section_details_override=s,
            )
            for s in sections
            for _ in range(num_candidates)
        ]
        # 使用 return_exceptions=True 來捕獲個別失敗，避免一個失敗導致整體失敗
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # 組織輸出：每個 section_id -> [候選內容...]
    plan_content = {}
    section_success_stats = {}
    
    for res in results:
        # 檢查是否是異常
        if isinstance(res, Exception):
            logger.error(f"Task raised exception: {res}", exc_info=False)
            continue
        
        if isinstance(res, SectionGenerateResponse):
            section_id = res.section_id
            
            # 初始化該 section 的統計
            if section_id not in section_success_stats:
                section_success_stats[section_id] = {"success": 0, "failed": 0}
                plan_content[section_id] = []
            
            # 記錄成功或失敗
            if res.error:
                section_success_stats[section_id]["failed"] += 1
                logger.warning(f"Candidate for section {section_id} failed: {res.error}")
            else:
                section_success_stats[section_id]["success"] += 1
                plan_content[section_id].append(res.dict())
    
    # 檢測哪些 section 完全失敗（所有候選都生成失敗）
    failed_sections = [
        sid for sid, stats in section_success_stats.items()
        if stats["success"] == 0
    ]
    
    if failed_sections:
        logger.error(f"⚠️  {len(failed_sections)} sections failed completely: {failed_sections}")

    if request_data.project_id:
        finished_at = datetime.now(timezone.utc)
        duration_ms = int((finished_at - generation_started_at).total_seconds() * 1000)
        await supabase_service.log_execution_event(
            project_id=request_data.project_id,
            user_id=user_id,
            event_type="plan_generation_completed",
            payload={
                **generation_context,
                "duration_ms": duration_ms,
                "section_count": len(sections),
                "successful_sections": len(sections) - len(failed_sections),
                "failed_sections": failed_sections,
                "finished_at": finished_at.isoformat(),
            },
        )

    return plan_content


@router.post("/revise_plan_version")
async def revise_plan_version(
    request_data: PlanRevisionRequest,
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
    user_id: str = Depends(get_current_user_id),
):
    # 根據現有版本內容進行修訂，結合更新的問答摘要與用戶輸入，為每個章節生成改進的候選版本，同時記錄執行事件
    if not request_data.current_version or not isinstance(request_data.current_version, dict):
        raise HTTPException(status_code=400, detail="current_version is required for revision.")

    app_state = request.app.state
    all_grants_config = getattr(app_state, "all_grants_config", [])

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
            detail=f"Template {request_data.template} not found in Grant {request_data.grant}.",
        )

    sections = template_config.sections
    
    # 加载 section_versions 并 hydrate sections
    project_section_versions: Dict[str, int] = {}
    if request_data.project_id:
        project_record = await supabase_service.get_project_by_id(
            request_data.project_id,
            user_id,
        )
        if not project_record:
            raise HTTPException(status_code=404, detail="Project not found or permission denied")
        project_section_versions = project_record.get("section_versions") or {}

    if project_section_versions:
        sections = await supabase_service.hydrate_section_configs_with_versions(
            sections=sections,
            grant_id=request_data.grant,
            template_id=request_data.template,
            section_versions=project_section_versions,
        )
    
    if not sections:
        raise HTTPException(status_code=400, detail="No sections found in the selected template.")

    revision_started_at = datetime.now(timezone.utc)
    revision_context = {
        "grant_id": request_data.grant,
        "template_id": request_data.template,
        "num_candidates": request_data.num_candidates,
        "is_external": request_data.is_external,
        "selected_model": request_data.selected_model,
    }

    if request_data.project_id:
        await supabase_service.log_execution_event(
            project_id=request_data.project_id,
            user_id=user_id,
            event_type="plan_revision_started",
            payload={**revision_context, "started_at": revision_started_at.isoformat()},
        )

    answers_summary = _format_revision_answers(request_data.stored_answer)
    user_input_summary = _format_user_input_summary(request_data.stored_answer)
    commands_data = await supabase_service.get_commands_by_user_id(user_id)

    project_title = request_data.project_title or "未提供"
    project_summary = request_data.project_summary or "尚未提供摘要"

    base_prompt = f"""
你是一位資深的計畫書編輯，任務是基於現有版本進行「版本更新」。請遵循：
- 維持章節 JSON Schema 結構與欄位順序，保留 80~90% 原始內容骨架。
- 對語句不順、細節不足或缺乏佐證的段落進行精煉、補強與具體化。
- 若需補充無法確定的資訊，請以 OOO 作為暫時佔位符。
- 問答摘要可能已經更新了，請根據問答摘要補齊內容，但仍需與整體脈絡一致。
- 完成後輸出純 JSON，不要添加說明文字。

計畫名稱：{project_title}
計畫摘要：{project_summary}

【使用者問答摘要】
{answers_summary}
"""

    if user_input_summary:
        base_prompt += f"\n\n【使用者輸入摘要】\n{user_input_summary}"

    if commands_data:
        commands_text = "\n".join(
            [
                f"- {cmd.get('title', '')}: {cmd.get('description', '')}"
                for cmd in commands_data
                if cmd.get('title') or cmd.get('description')
            ]
        )
        if commands_text:
            base_prompt += f"\n\n【啟用中的 Commands】\n{commands_text}"

    version_map = request_data.current_version

    async with httpx.AsyncClient() as client:
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
                        user_id=user_id,
                        supabase_service=supabase_service,
                        is_external=request_data.is_external,
                        selected_model=request_data.selected_model,
                        project_id=request_data.project_id,
                        section_context=section_context,
                        disable_few_shot=True,
                        section_details_override=section,
                    )
                )

        # 使用 return_exceptions=True 來捕獲個別失敗
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # 組織輸出：每個 section_id -> [候選內容...]
    plan_content = {}
    section_success_stats = {}
    
    for res in results:
        # 檢查是否是異常
        if isinstance(res, Exception):
            logger.error(f"Task raised exception: {res}", exc_info=False)
            continue
        
        if isinstance(res, SectionGenerateResponse):
            section_id = res.section_id
            
            # 初始化該 section 的統計
            if section_id not in section_success_stats:
                section_success_stats[section_id] = {"success": 0, "failed": 0}
                plan_content[section_id] = []
            
            # 記錄成功或失敗
            if res.error:
                section_success_stats[section_id]["failed"] += 1
                logger.warning(f"Revision candidate for section {section_id} failed: {res.error}")
            else:
                section_success_stats[section_id]["success"] += 1
                plan_content[section_id].append(res.dict())
    
    # 檢測哪些 section 完全失敗
    failed_sections = [
        sid for sid, stats in section_success_stats.items()
        if stats["success"] == 0
    ]
    
    if failed_sections:
        logger.error(f"⚠️  {len(failed_sections)} sections failed completely during revision: {failed_sections}")

    if request_data.project_id:
        finished_at = datetime.now(timezone.utc)
        duration_ms = int((finished_at - revision_started_at).total_seconds() * 1000)
        await supabase_service.log_execution_event(
            project_id=request_data.project_id,
            user_id=user_id,
            event_type="plan_revision_completed",
            payload={
                **revision_context,
                "duration_ms": duration_ms,
                "section_count": len(sections),
                "successful_sections": len(sections) - len(failed_sections),
                "failed_sections": failed_sections,
                "finished_at": finished_at.isoformat(),
            },
        )

    return plan_content


# --- 輔助函數 ---
def get_current_timestamp():
    return datetime.now(timezone.utc).isoformat()

def build_history_entry(role: str, content: str):
    return {
        "id": f"{role}-{uuid4().hex[:8]}",
        "role": role,
        "type": "text",
        "content": content,
        "timestamp": get_current_timestamp(),
    }

def normalize_meta_payload(meta_payload: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    # 將原始的 meta_payload 轉換為統一格式的字典，提取每個欄位的 updated_at 時間戳，並以欄位 ID 為鍵，包含 updated_at 的字典為值。
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
        if not timestamp:
            continue
        normalized[field_id] = {"updated_at": timestamp}
    return normalized

def touch_meta_field(meta_map: Dict[str, Dict[str, str]], field_id: str, timestamp: Optional[str] = None) -> None:
    
    if not field_id:
        return
    final_timestamp = (timestamp or get_current_timestamp()).strip()
    if not final_timestamp:
        return
    existing = meta_map.get(field_id) or {}
    meta_map[field_id] = {**existing, "updated_at": final_timestamp}

def normalize_filled_fields(filled_data: dict, all_questions: list) -> dict:
    """
    將 LLM 提取的 Key (通常是 Label) 強制轉換為 all_questions 中定義的標準 ID。
    策略：忽略空格，並允許忽略 Label 中的說明性括號內容 (【, (, [)。
    """
    # 1. 建立 "指紋" -> "標準 ID" 的映射表
    fingerprint_map = {}
    
    # 定義需要切割的括號符號 (包含全形與半形)
    # 用於移除如 "【說明】", "(備註)" 等後綴
    split_pattern = r'[【\[(（]' 
    
    for q in all_questions:
        real_id = q.get('id')         # e.g. "十、經費::材料費"
        label = q.get('label')        # e.g. "十、經費｜2.每月研發材料費【研發所需...】"
        
        if not real_id:
            continue
            
        # 1. 存 ID 本身
        fingerprint_map[real_id.replace(" ", "")] = real_id
        
        if label:
            # 2. 存完整 Label (去掉空格)
            clean_label = label.replace(" ", "")
            fingerprint_map[clean_label] = real_id
            
            # 3. 存 "簡化版" Label (去掉括號後的說明文字)
            # 例如: "題目【說明】" -> 映射為 "題目"
            # 使用 re.split 切割，只取第一部分
            short_label = re.split(split_pattern, label)[0]
            clean_short_label = short_label.replace(" ", "")
            
            # 如果簡化版與原版不同，且不為空，則加入映射
            if clean_short_label and clean_short_label != clean_label:
                fingerprint_map[clean_short_label] = real_id

    # 2. 清洗 filled_data 並映射
    normalized = {}
    
    for key, value in filled_data.items():
        # 1. 預處理 Key
        clean_key = key.replace("::reply", "").strip()
        
        # 2. 製作指紋 (去掉所有空格)
        key_fingerprint = clean_key.replace(" ", "")
        
        # 3. 查找映射
        if key_fingerprint in fingerprint_map:
            standard_id = fingerprint_map[key_fingerprint]
            normalized[standard_id] = value
        else:
            # 進階容錯：如果 LLM 回傳的 Key 自己也帶有括號，嘗試去掉括號後再匹配一次
            # (雖然這種情況較少，但以防萬一)
            short_key_fingerprint = re.split(split_pattern, key_fingerprint)[0]
            
            if short_key_fingerprint in fingerprint_map:
                standard_id = fingerprint_map[short_key_fingerprint]
                normalized[standard_id] = value
            else:
                logger.warning(f"Field mismatch: '{key}' maps to nothing. Kept original.")
                normalized[clean_key] = value
            
    return normalized

def format_qa_descriptions(all_questions, current_answers):
    """
    生成 Prompt 用的問答描述 (支持 ::reply 後綴查找 & 模糊匹配)
    """
    
    # 1. 建立 Lookup Map: 處理 current_answers 裡的 Key
    answer_lookup = {}
    
    for k, v in current_answers.items():
        if not v or not str(v).strip():
            continue
            
        # 存原始 Key
        answer_lookup[k] = v
        
        # 處理 "::reply" 後綴
        clean_k = k.replace("::reply", "")
        answer_lookup[clean_k] = v
        
        # 處理空格 (徹底標準化)
        answer_lookup[clean_k.replace(" ", "")] = v

    answered_list = []
    unanswered_list = []

    for q in all_questions:
        qid = q.get('id')   # e.g. "二、研發動機::市 場規模"
        label = q.get('label', qid)
        
        # 準備查找用的 Key
        # 我們主要用 qid 找，因為上面已經把 answer_lookup 的 key 變成 qid 風格了
        qid_no_space = qid.replace(" ", "")
        label_no_space = label.replace(" ", "")

        val = None
        
        # --- 多重查找策略 ---
        # 1. 用 ID 找
        if qid in answer_lookup:
            val = answer_lookup[qid]
        # 2. 用 去空格ID 找
        elif qid_no_space in answer_lookup:
            val = answer_lookup[qid_no_space]
        # 3. 用 Label 找 (fallback)
        elif label in answer_lookup:
            val = answer_lookup[label]
        # 4. 用 去空格Label 找
        elif label_no_space in answer_lookup:
            val = answer_lookup[label_no_space]

        # 構建描述
        if val:
            val_str = str(val).strip()
            display_val = val_str[:100] + "..." if len(val_str) > 100 else val_str
            # 這裡顯示 Label 給 AI 看，比較友善
            answered_list.append(f"- {label}: {display_val}")
        else:
            unanswered_list.append(q)

    # 生成文本
    questions_desc = "\n".join([
        f"- {q.get('id', q.get('label'))}: {q.get('prompt', '')}" 
        for q in all_questions
    ])
    
    answered_desc = "\n".join(answered_list) or "（無）"
    
    unanswered_desc = "\n".join([
        f"- {q.get('id', q.get('label'))}"
        for q in unanswered_list
    ]) or "（全部已填）"
    return questions_desc, answered_desc, unanswered_desc, unanswered_list

# --- 新增：历史记录注入工具 ---

def get_chat_messages(system_prompt: str, history_records: list, last_user_msg: str = None, limit: int = 10):
    """
    构建发送给 LLM 的 messages 列表。
    1. System Prompt
    2. 最近 N 条历史 (去除最后一条如果它和 current_user_msg 重复)
    3. Current User Message
    """
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # 1. 提取并清洗历史记录 (OpenAI 只接受 role 和 content)
    # limit 控制注入的历史条数，防止 Token 溢出
    clean_history = []
    start_index = max(0, len(history_records) - limit)
    
    subset_history = history_records[start_index:]
    if last_user_msg and subset_history and subset_history[-1]['content'] == last_user_msg:
         subset_history = subset_history[:-1]

    for h in subset_history:
        role = h.get("role", "user")
        content = h.get("content", "")
        if role in ["user", "assistant", "system"]:
            messages.append({"role": role, "content": content})

    # 2. 添加当前的 User Input
    if last_user_msg:
        messages.append({"role": "user", "content": last_user_msg})
        
    return messages


def _extract_chat_answers_from_stored(stored_answer: Dict[str, Any]) -> Dict[str, Any]:
    if not stored_answer or not isinstance(stored_answer, dict):
        return {}
    for key in ("chat_answers", "chatAnswers"):
        value = stored_answer.get(key)
        if isinstance(value, dict):
            return value.copy()
    return {}


def _format_revision_answers(
    stored_answer: Optional[Dict[str, Any]]
) -> str:
    merged = _extract_chat_answers_from_stored(stored_answer or {})
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

    sections = []
    main_idea = user_input.get("main_idea") or user_input.get("mainIdea")
    if main_idea:
        sections.append(f"【核心構想】\n{main_idea}")

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
            sections.append("【動態欄位摘要】\n" + "\n".join(field_lines))
    return "\n\n".join(sections)


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

# --- 主要 WebSocket Endpoint ---

@router.websocket("/ws/chat_guidance")
async def websocket_chat_guidance(websocket: WebSocket):
    # WebSocket 即時聊天引導，根據對話歷史和已填欄位動態推薦下一題，並自動提取填寫的欄位並同步至資料庫
    await websocket.accept()
    
    # Extract user_id from WebSocket query parameter or headers
    user_id = ""
    supabase_service = getattr(websocket.app.state, "supabase_service", None)
    
    # Try to get token from query parameters (passed as ?token=...)
    token = websocket.query_params.get("token", "")
    
    # Fall back to authorization header if not in query params
    if not token:
        auth_header = websocket.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    # Fall back to app access token cookie for external login users.
    if not token:
        token = websocket.cookies.get("app_access_token", "")
    
    if token and supabase_service:
        try:
            user_response = supabase_service.client.auth.get_user(token)
            if user_response.user:
                canonical_user = await supabase_service.resolve_or_create_user_by_supabase_identity(
                    auth_user_id=user_response.user.id,
                    email=user_response.user.email,
                )
                user_id = canonical_user["id"]
        except Exception as e:
            try:
                payload = decode_app_access_token(token)
                canonical_user_id = payload.get("sub")
                if canonical_user_id:
                    user_row = await supabase_service.get_user_by_id(canonical_user_id)
                    if user_row and user_row.get("id"):
                        user_id = user_row["id"]
            except Exception as decode_error:
                logger.warning(f"Failed to extract user from WebSocket token: {e}; app token decode error: {decode_error}")
    
    llm_service = websocket.app.state.llm_service
    model_registry = getattr(websocket.app.state, "model_registry", {}) or {}
    model_info = model_registry.get("gpt-5.1-chat-latest") or {
        "id": "gpt-5.1-chat-latest",
        "provider": "openai",
        "type": "external",
        "cost_info":{
            "input": 1.25,
            "output": 10
        }
    }
    
    project_id = ""
    conversation_history_records = []
    stored_answer_state = {}
    current_answers = {}
    current_answer_meta: Dict[str, Dict[str, str]] = {}
    all_questions = []
    project_title = ""
    project_summary = ""

    async def save_state_to_db():
        if not project_id or not supabase_service:
            return
        try:
            previous_answers = stored_answer_state.get("chat_answers") or {}
            previous_meta = stored_answer_state.get("chat_answers_meta") or {}
            previous_answers_snapshot = json.dumps(
                previous_answers,
                ensure_ascii=False,
                sort_keys=True,
            )
            current_answers_snapshot = json.dumps(current_answers, ensure_ascii=False, sort_keys=True)
            answers_changed = previous_answers_snapshot != current_answers_snapshot
            stored_answer_state["chat_answers"] = current_answers.copy()
            stored_answer_state["chat_answers_meta"] = {
                key: (value.copy() if isinstance(value, dict) else value)
                for key, value in current_answer_meta.items()
            }
            payload = {
                "conversation_history": conversation_history_records,
                "stored_answer": stored_answer_state,
            }
            await supabase_service.update_project_record(project_id, user_id, payload)
            if answers_changed and user_id:
                # 計算詳細的字段變化
                field_changes = []
                all_field_ids = set(previous_answers.keys()) | set(current_answers.keys())
                for field_id in sorted(all_field_ids):
                    old_value = previous_answers.get(field_id, "")
                    new_value = current_answers.get(field_id, "")
                    if old_value != new_value:
                        # 確保元資料存在
                        meta_entry = current_answer_meta.get(field_id)
                        if not meta_entry or not meta_entry.get("updated_at"):
                            fallback = previous_meta.get(field_id, {}).get("updated_at") if isinstance(previous_meta.get(field_id), dict) else None
                            touch_meta_field(current_answer_meta, field_id, fallback)
                        # 找到欄位標籤（如果可用）
                        field_label = None
                        for q in all_questions:
                            if q.get("id") == field_id:
                                field_label = q.get("label", field_id)
                                break
                        field_display = field_label or field_id
                        field_changes.append({
                            "field_id": field_id, 
                            "field_label": field_display,
                            "old_value": old_value,
                            "new_value": new_value,
                            "change": f"{field_display}：《{old_value}》→《{new_value}》"
                        })
                
                await supabase_service.log_execution_event(
                    project_id=project_id,
                    user_id=user_id,
                    event_type="stored_answer_updated",
                    payload={
                        "answers_count": len(current_answers),
                        "field_changes": field_changes,
                        "changes_summary": " | ".join([f["change"] for f in field_changes])
                    },
                )
        except Exception as exc:
            logger.error(f"DB Save Error: {exc}")
 
    # --- 生成回答 (注入历史) ---
    async def stream_ai_reply(user_msg: str, history: list, needs_clarification: bool, client: httpx.AsyncClient, grant_name: str, paused_flag: dict):
      
        _, a_desc, ua_desc, ua_list = format_qa_descriptions(all_questions, current_answers)
     
        
        next_q_label = "（请检查是否还有未填项）"
        if ua_list:
            next_q_label = ua_list[0].get("id") or ua_list[0].get("label")

        # Include project title/summary in system prompt to provide context to the model
        proj_title_label = project_title or "(未提供專案名稱)"
        proj_summary_label = project_summary or "(未提供專案摘要)"

        unanswered_count = len(ua_list)
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
    - 這段文字僅供系統讀取，前端會自動隱藏，因此務必精準輸出。

    【排版】
    排版不要那麽鬆散，盡量維持緊凑。
    如果是重點内容/副標題，請使用「粗體」標記。
    爲了讓用戶能夠直觀理解内容，你可以參考如下回復模板：**完成欄位確認**（如果有）-> **還剩幾題**（并且包含鼓勵語句）->**下一題問題**->💡**填寫小提醒** （指導該填什麽/給範例建議）。
    這個回復模板是參考，你也可以自由發展，重點是要自然語言和能夠直觀理解哪裏是重點
    只有填寫小提醒會有💡,其他的不要有icon
    在講述還剩几題的時候，需要使用一條長橫綫分隔來區分還剩几題和下一題的題目。
    

    注意：請根據對話歷史流暢回應。即使系統顯示某欄位為「待填」，只要使用者剛剛在對話中已回答，請視為已填並繼續流程。
    """
        
        # 构建 Messages：System -> History -> User
        # limit=10 表示带上最近 10 句对话作为上下文，让 AI 回答更连贯
        messages = get_chat_messages(system_prompt, history, last_user_msg=user_msg, limit=10)

        await websocket.send_json({"event": "chunk_start"})

        full_response = []
        try:
            async for chunk in llm_service.stream_external_api(
                client, model_info, messages
            ):
                # If paused_flag is set, cancel the current streaming reply
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
        except Exception as e:
            logger.error(f"Stream error: {e}")
            await websocket.send_json({"event": "error", "message": str(e)})

        return "".join(full_response).strip()

    try:
        init_data = await websocket.receive_json()
        project_id = init_data.get("project_id", "")
        project_title = init_data.get("project_title", "")
        project_summary = init_data.get("project_summary", "")
        grant_name = init_data.get("grant_name", "")
        all_questions = init_data.get("all_questions", [])
        # 加载 DB 状态
        if project_id and supabase_service:
            try:
                rec = await supabase_service.get_project_by_id(project_id)
                if rec:
                    conversation_history_records = rec.get("conversation_history") or []
                    stored_answer_state = rec.get("stored_answer") or {}
                    db_answers = stored_answer_state.get("chat_answers", {})
                    db_meta = normalize_meta_payload(stored_answer_state.get("chat_answers_meta"))
                    frontend_answers = init_data.get("current_answers", {})
                    frontend_meta = normalize_meta_payload(init_data.get("current_answers_meta"))
                    current_answers = {**db_answers, **frontend_answers}
                    current_answer_meta = {**db_meta, **frontend_meta}
            except Exception as e:
                logger.error(f"Load project error: {e}")

        # 初始化历史
        if not conversation_history_records:
            raw_history = init_data.get("history") or []
            for h in raw_history:
                if isinstance(h, dict) and h.get("content"):
                    conversation_history_records.append(build_history_entry(h.get("role"), h.get("content")))

        await websocket.send_json({"event": "ready", "message": "系统就绪"})


        # --- 生成开场白 (如果是新对话) ---
        last_is_assistant = False
        if conversation_history_records:
             last_entry = conversation_history_records[-1]
             if str(last_entry.get("id", "")).startswith("assistant") or last_entry.get("role") == "assistant":
                 last_is_assistant = True

        # control flag for cancelling ongoing streams
        paused_flag = {"value": False}

        if not last_is_assistant:
            async with httpx.AsyncClient(timeout=60.0) as client:
                first_reply = await stream_ai_reply(
                    "（用户刚进入，请根据项目名称和項目描述开始引导）",
                    conversation_history_records,
                    False,
                    client,
                    grant_name,
                    paused_flag,
                )
                
                # 記錄成本使用
                if user_id:
                    try:
                        response_json = getattr(llm_service, '_last_response_json', {})
                      
                        if response_json:
                            await supabase_service.log_cost_usage(user_id, model_info, response_json, project_id=project_id, action="生成對話")
                    except Exception as e:
                        logger.warning(f"Failed to log cost usage for initial greeting: {e}", exc_info=True)
                
                if first_reply:
                    conversation_history_records.append(build_history_entry("assistant", first_reply))
                    await save_state_to_db()

        # --- 主循环 ---
        # Use a single websocket reader task that dispatches incoming payloads into an asyncio.Queue
        incoming_user_queue: asyncio.Queue = asyncio.Queue()

        async def websocket_reader():
            try:
                while True:
                    payload = await websocket.receive_json()
                    # Control action
                    if payload.get("action") == "pause":
                        # Set paused flag so any ongoing stream can detect it
                        paused_flag["value"] = True
                        try:
                            await websocket.send_json({"event": "paused_ack"})
                        except Exception:
                            pass
                        # do not enqueue pause as a user message
                        continue

                    # Normal user payloads go to the queue
                    await incoming_user_queue.put(payload)
            except WebSocketDisconnect:
                await incoming_user_queue.put({"_disconnect": True})
            except Exception as e:
                logger.error(f"Reader error: {e}")
                await incoming_user_queue.put({"_disconnect": True})

        reader_task = asyncio.create_task(websocket_reader())

        try:
            while True:
                payload = await incoming_user_queue.get()
                if payload.get("_disconnect"):
                    logger.info("Client disconnected (from queue)")
                    break

                user_msg = payload.get("user_message", "").strip()
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

                # prepare user entry but DO NOT append yet — only persist if stream completes
                user_entry = build_history_entry("user", user_msg)

                async with httpx.AsyncClient(timeout=60.0) as client:
                    ai_reply = await stream_ai_reply(
                        user_msg,
                        conversation_history_records,
                        False,
                        client,
                        grant_name,
                        paused_flag,
                    )

                    # 記錄成本使用
                    if user_id and model_info.get('type') == 'external':
                        try:
                            response_json = getattr(llm_service, '_last_response_json', {})
                            if response_json:
                                await supabase_service.log_cost_usage(user_id, model_info, response_json, project_id=project_id, action="生成對話")
                        except Exception as e:
                            logger.warning(f"Failed to log cost usage: {e}", exc_info=True)

                    # If paused_flag was triggered during streaming, the stream has been cancelled
                    if paused_flag.get("value"):
                        # reset the flag and skip saving this user/assistant exchange
                        paused_flag["value"] = False
                        continue

                    # append the user's message now that the stream completed
                    conversation_history_records.append(user_entry)

                    if ai_reply:
                        conversation_history_records.append(build_history_entry("assistant", ai_reply))

                    # Background extraction
                    hidden_answers = extract_hidden_field_responses(ai_reply)
                    if hidden_answers:
                        clean_filled = normalize_filled_fields(hidden_answers, all_questions)
                        logger.info(f"Normalized fields: {clean_filled}")
                        current_answers.update(clean_filled)
                        for field_id in clean_filled.keys():
                            touch_meta_field(current_answer_meta, field_id)

                    await save_state_to_db()

        finally:
            # ensure reader task is cleaned up
            if not reader_task.done():
                reader_task.cancel()

    except Exception as e:
        logger.error(f"Endpoint error: {e}", exc_info=True)
        await websocket.close()

@router.post("/generate_synthetic_input", response_model=Dict[str, Any])
async def generate_synthetic_input(
    req: SyntheticInputRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    # 根據 random 或 reverse 模式生成合成用戶輸入，支援隨機生成新構想或反推現有計畫書內容，統一返回 main_idea 和 dynamic_fields 格式
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
            response, error, _ = await llm_service.call_external_api(client, model_info, messages, is_json_output=True)

            
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
      
@router.post("/recommend_project_names", summary="根據已填寫的欄位推薦五個專案名稱")
async def recommend_project_names(
    payload: Dict[str, Any],
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    user_id: str = Depends(get_current_user_id),
):
    # 根據補助主題、已填寫欄位和參考範例，使用 LLM 推薦最多 5 個符合計畫書風格的創新專案名稱
    """根據 current_answers 和其他上下文推薦最多 5 個專案名稱，回傳 JSON { names: [...] }"""
    model_registry = request.app.state.model_registry or {}
    model_info = model_registry.get("gemini-3-flash-preview") or model_registry.get("gpt-4.1-mini")
    if not model_info:
        raise HTTPException(status_code=500, detail="Model not configured for recommendation.")

    current_answers = payload.get("current_answers", {}) or {}
    project_title = payload.get("project_title", "") or ""
    grant_name = payload.get("grant_name", "") or ""
    template_name = payload.get("template_name", "") or ""
    grant_id = payload.get("grant_id", "") or ""
    template_id = payload.get("template_id", "") or ""
    project_id = payload.get("project_id", "") or ""

    name_config: Optional[Dict[str, Any]] = None
    if grant_id and template_id:
        try:
            template_record = await supabase_service.get_template_by_id(
                template_id, grant_id
            )
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

    # build a compact context
    filled_items = []
    for k, v in current_answers.items():
        if v and str(v).strip():
            filled_items.append(f"- {k}: {str(v)[:120]}")
    filled_text = "\n".join(filled_items) or "（無已填寫欄位）"  

    selected_examples = custom_examples
    few_shot_text = (
        "\n".join([f"  - {ex}" for ex in selected_examples])
        if selected_examples
        else "  - （尚未提供範例）"
    )

    custom_trait_block = (
        f"\n6. **模板自訂特性**：{custom_traits}"
        if custom_traits
        else ""
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
        f"\n**模板命名特性說明**：\n{custom_traits}\n"
        if custom_traits
        else ""
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

    try:
        async with httpx.AsyncClient() as client:
            print(user_prompt,system_prompt )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response, error, response_json = await llm_service.call_external_api(
                client, model_info, messages, is_json_output=True
            )

            if error:
                logger.error(f"Recommend names failed: {error}")
                raise HTTPException(status_code=502, detail="Recommendation service error")

            try:
                data = json.loads(response)
                names = data.get("names") or []
                # ensure unique & trimmed & up to 5
                cleaned = []
                for n in names:
                    if not n:
                        continue
                    s = str(n).strip()
                    if s and s not in cleaned:
                        cleaned.append(s)
                    if len(cleaned) >= 5:
                        break
                
                # Log cost usage
                if response_json and model_info.get('type') == 'external':
                    await supabase_service.log_cost_usage(user_id, model_info, response_json, project_id=project_id, action="推薦企劃書名稱")
                
                return {"names": cleaned}
            except Exception as ex:
                logger.error(f"Failed to parse recommendation response: {ex}")
                raise HTTPException(status_code=500, detail="Failed to parse recommendation response")
    except Exception as e:
        logger.error(f"Error in recommend_project_names: {e}")
        raise HTTPException(status_code=500, detail="Recommendation service error")


@router.post("/autofill_from_document", summary="從文檔自動填充計畫書內容")
async def autofill_from_document(
    request_data: AutoFillRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    user_id: str = "dba4dabc-a24d-4e1a-aa2b-b239d06a8cf5"
):
    # 根據文檔文本和多個章節 Schema，使用強大的 LLM 解析並填充結構化的 JSON，支援預設和 Word 導入等提示模式
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
    這是需要你處理的計畫書文檔全文：
    --- DOCUMENT START ---
    {request_data.document_text}
    --- DOCUMENT END ---

    這是你需要填充的目標 JSON 結構定義：
    {all_schemas_info}

    請根據以上文檔內容和結構定義，生成最終的 JSON 輸出。
    """

    model_registry = request.app.state.model_registry
    model_to_use =  model_registry.get("gpt-5-mini") or model_registry.get("gemini-3-flash-preview")
    if not model_to_use:
        raise HTTPException(status_code=500, detail="A powerful model like GPT-4/5 is required for this feature.")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            raw_output, llm_error, response_json = await llm_service.call_external_api(
                client, 
                model_to_use,  
                messages,  
                is_json_output=True,
                reasoning_effort="low",
            )

        if llm_error:
            raise HTTPException(status_code=500, detail=f"LLM API Error: {llm_error}")

        
        # 容錯解析返回的 JSON 字串
        filled_data, parse_error = extract_json_block(
            raw_output,
            "autofill_from_document",
        )
        if parse_error:
            logger.error(f"AutoFill JSON parse error: {parse_error}")
            raise HTTPException(status_code=500, detail="LLM did not return a valid JSON object.")

        if not isinstance(filled_data, dict):
            raise HTTPException(status_code=500, detail="LLM returned unexpected JSON format.")

        # 確保所有章節都有內容，缺少的設為空
        formatted_result = {}
        for section in request_data.sections:
            section_id = section.section_id
            if section_id in filled_data:
                formatted_result[section_id] = {"content": filled_data[section_id]}
            else:
                logger.warning(f"Missing section in LLM output: {section_id}")
                formatted_result[section_id] = {"content": {}}

        # if response_json and model_to_use.get('type') == 'external':
        #     await supabase_service.log_cost_usage(user_id, model_to_use, response_json)

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
    project_id: str = Form(""),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    user_id: str = Depends(get_current_user_id),
):
    # 上傳 PDF / TXT / PPT / PPTX / JPG / JPEG / PNG 等檔案，使用 OpenAI Responses API 針對指定欄位進行 AI 輔助分析，生成豐富的欄位內容
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key is not configured.")

    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="請至少上傳一個檔案。")
    
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="最多只能同時上傳 5 個檔案。")

    for file in files:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_FILE_SUFFIXES:
            raise HTTPException(
                status_code=400,
                detail="僅支援 PDF / TXT / PPT / PPTX / JPG / JPEG / PNG 檔案格式。",
            )

    # 區分圖像與文檔
    image_suffixes = {".jpg", ".jpeg", ".png"}
    
    # 分類檔案：(file_id, file_type) 其中 file_type 為 "image" 或 "document"
    uploaded_files = []
    
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
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
                
                suffix = Path(upload_file.filename or "").suffix.lower()
                is_image = suffix in image_suffixes
                purpose = "vision" if is_image else "assistants"
                
                upload_resp = await client.post(
                    OPENAI_FILES_ENDPOINT,
                    headers=headers,
                    data={"purpose": purpose},
                    files={
                        "file": (
                            upload_file.filename,
                            BytesIO(file_bytes),
                            upload_file.content_type or "application/octet-stream",
                        )
                    },
                )
                upload_resp.raise_for_status()
                file_id = upload_resp.json().get("id")
                if not file_id:
                    raise HTTPException(status_code=500, detail=f"OpenAI file upload failed for {upload_file.filename}.")
                
                uploaded_files.append({
                    "file_id": file_id,
                    "file_type": "image" if is_image else "document",
                    "filename": upload_file.filename
                })

            # 構建 content_items：圖像用 input_image，文檔用 input_file
            content_items = [{"type": "input_text", "text": prompt}]
            for file_info in uploaded_files:
                if file_info["file_type"] == "image":
                    content_items.append({
                        "type": "input_image",
                        "file_id": file_info["file_id"]
                    })
                else:
                    content_items.append({
                        "type": "input_file",
                        "file_id": file_info["file_id"]
                    })

            model_info = {
                "id": "gpt-4.1-mini",
                "provider": "openai",
                "type": "external",
                "cost_info":{
                    "input": 0.40,
                    "output": 1.60
                }
            }

            responses_resp = await client.post(
                OPENAI_RESPONSES_ENDPOINT,
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "model": model_info["id"],
                    "input": [
                        {
                            "role": "user",
                            "content": content_items,
                        }
                    ],
                    "max_output_tokens": 900,
                    "temperature": 0.2,
                    "metadata": {"feature": "field_file_analysis"},
                },
            )
            responses_resp.raise_for_status()

            response_json = responses_resp.json()
            output_text = _extract_output_text(response_json)
            parsed = json.loads(output_text)
            
            # Log cost usage for file analysis
            if response_json and model_info.get('type') == 'external':
                await supabase_service.log_cost_usage(user_id, model_info, response_json, project_id=project_id, action="欄位OCR分析")

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
        if uploaded_files:
            try:
                async with httpx.AsyncClient(timeout=30.0) as cleaner:
                    for file_info in uploaded_files:
                        await cleaner.delete(
                            f"{OPENAI_FILES_ENDPOINT}/{file_info['file_id']}",
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

