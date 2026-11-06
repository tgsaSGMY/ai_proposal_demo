# 提示詞註冊表服務：解析並快取 prompt_templates 資料表中的作用中版本，
# 依模型相容性挑選對應提示詞，並在 DB 無資料時回退至常數。

import asyncio
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


# Kept byte-identical to the `chat_guidance` v1 seed row in
# docs/sql/2026_09_15_create_prompt_templates.sql — this is the no-registry
# rollback path (Phase 1 Risk #1), so it must render the same prompt the
# DB-backed row does. If the seed text changes, update both together.
FALLBACK_CHAT_GUIDANCE_PROMPT = """
    你是一位友善的專案規劃助理，正在協助使用者填寫【{grant_name}】。

    專案名稱：{proj_title_label}
    專案摘要：{proj_summary_label}

    【目前系統記錄狀態】
    (可能略有延遲，請以最新對話為準)
    已填（Do NOT ask these）：{a_desc}
    待填：{ua_desc}

    【唯讀變數（系統計算，你可以在回覆中講述這些數字，但不可自行更改或重新計算）】
    next_question_id：{next_question_id_display}
    unanswered_count：{unanswered_count}
    total_questions：{total_questions}
    answered_percent：{answered_percent}%
    all_questions_answered：{all_questions_answered_label}

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
    若使用者的回答不清楚，請不需要直接詢問下一個欄位，先進一步追問以釐清。
    每詢問一個問題的時候，可以根據上下文生成建議性的答案輔助用戶。
    需要使用鼓勵方式，並在 reply_outro 中提及 unanswered_count（還剩幾題未完成），讓用戶不那麽快放棄。
    若 all_questions_answered 為「是」，請在 reply_outro 提醒用戶點擊右下角的「輸出完整推演」按鈕來產出完整計畫書文本，不需要再推薦其他事項，因爲你負責的是完善欄位，而這時候你的任務已完成。

    【下一題（系統將逐字插入，你不需要也不可以自己重新描述或改寫這段內容）】
    {next_q_prompt_text_display}

    【排版】
    reply_intro 和 reply_outro 都不要那麽鬆散，盡量維持緊凑，各自控制在一兩句話以內。
    如果是重點内容，請使用「粗體」標記。
    reply_intro 負責：確認/摘要使用者剛剛提供的內容（如果有）。
    reply_outro 負責：鼓勵語句 + 目前還剩幾題的提示（可以用 💡 提示下一步該怎麽填寫）。
    reply_intro 和 reply_outro 都不需要包含下一題的完整題目内容，系統會自動插入，你只需要自然地承上啟下。

    【輸出格式（非常重要）】
    你必須只輸出一個單一、合法的 JSON 物件，不能有任何其他文字、註解或 Markdown 標記包裹，結構如下：
    {{
      "reply_intro": "開場白，回應/確認使用者上一則訊息（一兩句話）",
      "reply_outro": "收尾語，包含鼓勵與剩餘題數提示（一兩句話）",
      "field_updates": {{"欄位ID": "答案內容"}},
      "suggested_next_question_id": "欄位ID 或 null"
    }}
    - field_updates 只需包含這一輪對話中你確認或代為填寫／優化的欄位；若這一輪沒有欄位被填寫，請給空物件 {{}}。
    - 欄位 ID 請使用系統提供的問題 ID（例如 三、解決辦法::商業模式運作流程），不要自行取名或翻譯。
    - suggested_next_question_id 請填入你建議接下來詢問的欄位 ID；若所有題目都已完成，請填 null。

    注意：請根據對話歷史流暢回應。即使系統顯示某欄位為「待填」，只要使用者剛剛在對話中已回答，請視為已填並繼續流程。
    """

_FALLBACK_PROMPTS: Dict[str, str] = {
    "chat_guidance": FALLBACK_CHAT_GUIDANCE_PROMPT,
}


class PromptRegistryService:
    """解析 `prompt_templates` 中作用中的提示詞範本。

    解析順序（resolution ladder）：
    1. 程序內快取（由 lifecycle 啟動時 / `/api/config/refresh` 時填入）。
    2. 快取未命中或與 model_id 不相容 -> 即時查詢 DB（帶 model_compatibility 篩選、依 version 取最新）。
    3. 仍找不到相容版本 -> 即時查詢 DB（不帶 model 篩選，取最新作用中版本）。
    4. DB 完全沒有作用中列（例如尚未套用 Migration M1）-> 回退至模組層級常數，並記錄警告。
    """

    def __init__(self, supabase_service: "SupabaseService"):
        self._supabase = supabase_service
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load_cache(self, rows: List[Dict[str, Any]]) -> None:
        """以一批作用中的 `prompt_templates` 列重建程序內快取。

        每個 `name` 最多一列作用中（由 `prompt_templates_one_active_per_name`
        部分唯一索引保證），因此以 `name` 為鍵即可。
        """
        self._cache = {row["name"]: row for row in rows if row.get("is_active")}

    @staticmethod
    def _row_matches_model(row: Dict[str, Any], model_id: Optional[str]) -> bool:
        if not model_id:
            return True
        compatibility = row.get("model_compatibility") or []
        return model_id in compatibility

    async def _query_active_row(
        self, name: str, model_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        query = (
            self._supabase.client.from_("prompt_templates")
            .select("*")
            .eq("name", name)
            .eq("is_active", True)
        )
        if model_id:
            query = query.contains("model_compatibility", [model_id])
        query = query.order("version", desc=True).limit(1)

        response = await asyncio.to_thread(query.execute)
        rows = response.data or []
        return rows[0] if rows else None

    async def get_active_prompt(self, name: str, model_id: Optional[str] = None) -> str:
        cached = self._cache.get(name)
        if cached is not None and self._row_matches_model(cached, model_id):
            return cached["system_prompt_template"]

        try:
            row = await self._query_active_row(name, model_id)
        except Exception:
            logger.exception(
                f"prompt_templates query failed for name={name!r}, model_id={model_id!r}"
            )
            row = None

        if row is not None:
            return row["system_prompt_template"]

        if model_id:
            try:
                row = await self._query_active_row(name, model_id=None)
            except Exception:
                logger.exception(
                    f"prompt_templates fallback query (no model filter) failed for name={name!r}"
                )
                row = None
            if row is not None:
                logger.warning(
                    f"prompt_templates: no active row for name={name!r} declares "
                    f"model_compatibility for model_id={model_id!r}; using active row "
                    f"without model filter (version={row.get('version')})."
                )
                return row["system_prompt_template"]

        if cached is not None:
            logger.warning(
                f"prompt_templates: cached row for name={name!r} does not match "
                f"model_id={model_id!r} and no better live row was found; "
                f"using cached row without model filter."
            )
            return cached["system_prompt_template"]

        fallback = _FALLBACK_PROMPTS.get(name)
        if fallback is None:
            raise KeyError(
                f"No active prompt_templates row and no fallback constant registered "
                f"for name={name!r}"
            )

        logger.warning(
            f"prompt_templates: no active row found for name={name!r} "
            f"(table missing, empty, or migration M1 not yet applied); "
            f"using module-level fallback constant."
        )
        return fallback
