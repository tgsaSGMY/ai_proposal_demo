"""
章節推薦 API，利用共享的 LLM 服務生成章節改版建議。（動態欄位配置中心的AI推薦）
"""
import json
import logging
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import get_llm_service
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Section Recommender"])

MAX_DOCUMENT_PREVIEW_CHARS = 20000
MODEL_INFO = {"id": "gpt-5-mini", "provider": "openai", "type": "external"}
SYSTEM_PROMPT = (
    "你是專精於科技研發計畫書的資深顧問，擅長分析章節與欄位結構，"
    "並以條列、具體的方式提供改版建議。"
    "參考現在的結構，只做微調建議，并且内容風格務求簡潔明瞭易懂。"
    "你不需要提供更進一步的建議，像是“若要，我可以...”"
)


class SectionRecommenderRequest(BaseModel):
    document_text: str = Field(..., description="純文字內容")
    schema_info: Any = Field(..., description="前端傳入的章節/欄位資訊")


class SectionRecommenderResponse(BaseModel):
    status: str
    recommendations: str


@router.post("/section-recommender", response_model=SectionRecommenderResponse)
async def recommend_sections(
    payload: SectionRecommenderRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    # 根據 Word 文檔和現有 Schema 生成章節改版建議，使用 LLM 分析並提供具體的修改意見
    document_text = (payload.document_text or "").strip()
    if not document_text:
        raise HTTPException(status_code=400, detail="document_text 不可為空")

    schema_data = _normalize_schema(payload.schema_info)
    schema_description = _format_schema_for_prompt(schema_data)

    truncated_text = document_text[:MAX_DOCUMENT_PREVIEW_CHARS]
    user_prompt = _build_user_prompt(schema_description, truncated_text)
    print("Section Recommender User Prompt:", user_prompt)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            llm_output, llm_error, _ = await llm_service.call_external_api(
                client, MODEL_INFO, messages, is_json_output=False
            )
    except Exception as exc:  # pragma: no cover - log unexpected runtime issues
        logger.error("LLM service call failed", exc_info=True)
        raise HTTPException(status_code=500, detail=f"LLM 呼叫失敗: {exc}")

    if llm_error:
        raise HTTPException(
            status_code=502,
            detail=llm_error.get("error", "LLM 未返回有效內容"),
        )

    recommendations = (llm_output or "").strip() or "AI 未提供建議，請稍後重試"
    print("Section Recommender LLM output:", recommendations)
    return SectionRecommenderResponse(status="success", recommendations=recommendations)


def _normalize_schema(schema_info: Any) -> Dict[str, Any]:
    # 規範化 Schema 資料，支持 Dict 或 JSON 字符串兩種格式
    if isinstance(schema_info, dict):
        return schema_info
    if isinstance(schema_info, str):
        try:
            return json.loads(schema_info)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="schema_info 不是有效的 JSON") from exc
    raise HTTPException(status_code=400, detail="schema_info 需要為物件或 JSON 字串")


def _format_schema_for_prompt(schema_data: Dict[str, Any]) -> str:
    # 將 Schema 資料格式化為易讀的文本，用於 LLM 提示詞，包含所有章節和欄位信息
    sections: List[Dict[str, Any]] = schema_data.get("sections", [])
    if not sections:
        return "目前尚未定義任何章節。"

    formatted_lines = ["當前 Schema 結構："]
    for section in sections:
        formatted_lines.append("")
        formatted_lines.append(f"【{section.get('title', '未命名章節')}】 (Key: {section.get('key', 'N/A')})")
        fields = section.get("fields", [])
        if not fields:
            formatted_lines.append("  (暫無欄位)")
            continue
        formatted_lines.append("  欄位：")
        for field in fields:
            formatted_lines.append(
                f"    - {field.get('title', '未命名欄位')} (Key: {field.get('key', 'N/A')})"
            )
            description = (field.get("description") or "").strip()
            if description:
                formatted_lines.append(f"      說明: {description}")

    return "\n".join(formatted_lines)


def _build_user_prompt(schema_description: str, document_text: str) -> str:
    # 構建用戶提示詞，指示 LLM 只能修改欄位說明而不能改變章節結構
    return f"""
請協助我檢視動態章節設定，但**只能**針對「說明 (description)」內容提出具體調整建議。

嚴格規範：
1. 章節與欄位的顯示標題、順序與數量一律保持不變。
2. 不可新增或刪除章節／欄位，欄位的 key 也禁止修改。
3. 只允許更改“説明”的部分，每個欄位若需要更新，僅回傳調整後的 description，並加粗需要修改的文字片段，讓使用者更易理解。

以下為當前 Schema：
{schema_description}

使用者提供的 Word 內容摘要：
--------------------
{document_text}
--------------------

請依「原有結構」輸出結果，只針對 description 做改善建議。
""".strip()