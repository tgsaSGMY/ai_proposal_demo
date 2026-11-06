# 封裝所有 LLM API 的呼叫邏輯

import httpx
import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple, Optional, List, Callable, Awaitable, TYPE_CHECKING
from app.config import OPENAI_API_KEY, OLLAMA_BASE_URL, GEMINI_API_KEY
from app.models import SectionConfig, SectionGenerateResponse 
from app.utils.extract_json import extract_json_block
from app.models import SectionGenerateResponse
import asyncio
import logging
from app.utils.routing import resolve_model
from app.utils.model_helper import normalize_provider
from app.utils.feature_models import get_feature_override
from app.utils.formatting import format_section_output
from app.utils.weight_normalizer import normalize_plan_weights
from app.utils.revision_guard import restore_emptied_fields
from app.utils.derivative_alignment import enforce_derivative_target
from google import genai
import io
from PIL import Image

if TYPE_CHECKING:
    from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

# 一個能生成文字的異步函數
GenerationFunc = Callable[..., Awaitable[Tuple[Optional[str], Optional[Dict]]]]


class FactCheckError(Exception):
    # 事實整理（時態清單、關鍵指標、conflicts）呼叫失敗；計畫書生成需停止，
    # 否則各章節在沒有一致性依據的情況下照常產出（in-app 2026-10-05 第六次：網路逾時後 13 週再現、衍生矛盾）
    pass

# 內部用的【事項時態清單】名稱不可出現在計畫書內文（版本更新會沿用舊內容，僅靠提示詞無法移除）
_INTERNAL_LABEL_PATTERNS = [
    re.compile(r"[（(]\s*依?\s*(?:事項時態清單|關鍵指標目標值)\s*[）)]"),
    re.compile(r"依?\s*【?事項時態清單】?"),
    re.compile(r"依?\s*【關鍵指標目標值[^】]*】"),
    re.compile(r"【與計畫執行期間不符的原文[^】]*】"),
    # 【事項時態清單】的狀態標籤被照抄成括號註記（in-app 2026-10-05：「約 78%（已完成）」）；
    # 只移除括號內僅有狀態標籤者，「（已完成以 500 筆 FAQ 驗證）」等有內容的括號與「（目標值）」保留
    re.compile(r"[（(]\s*(?:已完成|規劃中|尚未完成|現況|以預計／將／目標語氣撰寫)\s*[）)]"),
    # 只有時態用語的括號（in-app 2026-10-05 第八次：「功能開發（預計）」、「營收來源（將/預計）」）；
    # 「（預計 2027 年上線）」、「（目標值）」等有內容的括號保留
    # 「將」後可接兩字以內的動詞（in-app 2026-10-05 第九次：「（將執行）」、「（將採用）」）
    re.compile(
        r"[（(]\s*(?:預計|目標|將[一-鿿]{0,2})"
        r"(?:\s*[／/、]\s*(?:預計|目標|將[一-鿿]{0,2}))*\s*[）)]"
    ),
    # 時態指示被抄進句子（in-app 2026-10-05 第八次：「將以預計／將／目標語氣規劃」）；只移除指示本身
    re.compile(r"以?預計\s*[／/、]\s*將\s*[／/、]\s*目標\s*語氣(?:撰寫)?"),
    # 括號內說明事項時態（in-app 2026-10-05 第十一次：「（此為已完成項目，將作為本計畫研發基礎）」）
    re.compile(r"[（(]\s*此為(?:已完成|規劃中|尚未完成|現況)[^（）()]*[）)]"),
    # 清單的「事項：狀態」格式被照抄進句子（in-app 2026-10-06 第十三次：「約 78%：已完成。」、
    # 「尚未提出專利申請：現況。」）；只移除位於子句結尾的「：狀態」，「已完成之 PoC」等正常用法保留
    re.compile(r"\s*[：:]\s*(?:已完成|規劃中|尚未完成|現況)\s*(?=[。，,；;、！？）)\n]|$)"),
    # 括號內總結時態（in-app 2026-10-06 第十三次：「（以上屬已完成事項）」）
    re.compile(r"[（(]\s*以上(?:均|皆)?(?:屬|為|係)(?:已完成|規劃中|尚未完成|現況)[^（）()]{0,10}[）)]"),
    # in-app 2026-10-06 第十三次：「（重複項目備註）成本降低主要透過…」
    re.compile(r"[（(]\s*重[複覆]項目(?:備註|說明)?\s*[）)]"),
]


# 判為「已完成」的事項，其原文依據必須含下列完成性字眼之一
# 已成功／已累積／已建立／已具備：in-app 2026-10-05「已成功拓展歐美市場」被降為規劃中
_COMPLETION_WORDS = (
    "已完成", "已於", "已取得", "已簽約", "已上線", "已量產",
    "已導入", "已驗證", "已達成", "經測試達", "曾於",
    "已成功", "已累積", "已建立", "已具備",
)


def _compact_for_match(text: str) -> str:
    # 逐字比對用：統一全形／半形並去除空白與標點，文字本身仍須相同
    # （in-app 2026-10-05：模型把原文結尾的「。」抄成「.」，已完成的 PoC 因此被降為規劃中）
    normalized = unicodedata.normalize("NFKC", text or "")
    return "".join(ch for ch in normalized if not unicodedata.category(ch)[0] in ("P", "Z", "C"))


_SENTENCE_SPLIT_PATTERN = re.compile(r"[。！？!?\n]")


def _last_index(text: str, words: Tuple[str, ...]) -> int:
    return max((text.rfind(word) for word in words), default=-1)


def _has_completion_evidence(evidence: str, user_input: str) -> bool:
    # 依據須逐字出現在用戶輸入中（忽略空白與標點），且含完成性字眼，否則不可判為已完成
    compact_evidence = _compact_for_match(evidence)
    if not compact_evidence:
        return False
    if compact_evidence not in _compact_for_match(user_input):
        return False
    if any(word in compact_evidence for word in _COMPLETION_WORDS):
        return True
    # 依據本身沒有完成性字眼時，看原文同一句中依據之前的部分（in-app 2026-10-05 第十次：
    # 「公司已於…進行 PoC，以 500 筆 FAQ 測試，初步準確率約 78%」被拆成多項，後兩項不含「已於」）；
    # 完成性字眼之後若出現規劃用語（如「已完成 PoC，預計達成 85%」）則不採用
    for sentence in _SENTENCE_SPLIT_PATTERN.split(user_input or ""):
        compact_sentence = _compact_for_match(sentence)
        position = compact_sentence.find(compact_evidence)
        if position < 0:
            continue
        prefix = compact_sentence[: position + len(compact_evidence)]
        if _last_index(prefix, _COMPLETION_WORDS) > _last_index(prefix, _PLANNING_WORDS):
            return True
    return False


# 「現況」的依據不可含規劃用語，避免把未來規劃當成目前狀態
_PLANNING_WORDS = ("預計", "規劃", "計畫將", "未來", "目標", "將於", "將會", "擬")


def _has_state_evidence(evidence: str, user_input: str) -> bool:
    # 「現況」（目前持續的狀態，如「與 Google 維持多年合作關係」，in-app 2026-10-05 被降為規劃中並造成時態指示外洩）：
    # 依據須逐字出現在用戶輸入中（忽略空白與標點），且不含規劃用語
    compact_evidence = _compact_for_match(evidence)
    if not compact_evidence or compact_evidence not in _compact_for_match(user_input):
        return False
    if any(word in compact_evidence for word in _PLANNING_WORDS):
        return False
    # 原文同一句中依據之前有規劃用語時（如「預計明年達成準確率 85%」只取後半）不是現況；跨句的依據不檢查上下文
    sentence_prefixes = []
    for sentence in _SENTENCE_SPLIT_PATTERN.split(user_input or ""):
        compact_sentence = _compact_for_match(sentence)
        position = compact_sentence.find(compact_evidence)
        if position >= 0:
            sentence_prefixes.append(compact_sentence[:position])
    if not sentence_prefixes:
        return True
    return any(_last_index(prefix, _PLANNING_WORDS) < 0 for prefix in sentence_prefixes)


def _normalize_target_text(text: str) -> str:
    compact = re.sub(r"\s+", "", text or "")
    for src, dst in (("<=", "≤"), ("≦", "≤"), (">=", "≥"), ("≧", "≥"), ("％", "%")):
        compact = compact.replace(src, dst)
    return compact


def _target_value_in_text(value: str, text: str) -> bool:
    core = _normalize_target_text(value).lstrip("≤≥<>=約達至少最多")
    return bool(core) and core in _normalize_target_text(text)


def _parse_targets(parsed: Dict[str, Any]) -> List[Tuple[str, str]]:
    targets = []
    for entry in parsed.get("targets") or []:
        if not isinstance(entry, dict):
            continue
        metric = str(entry.get("metric") or "").strip()
        value = str(entry.get("value") or "").strip()
        if metric and value:
            targets.append((metric, value))
    return targets


def _apply_target_evidence(parsed: Dict[str, Any], user_input: str) -> Tuple[List[Tuple[str, str]], set]:
    """依 evidence 修正目標值；適用所有指標，不依賴範本或用戶用詞。

    evidence 須逐字出現在用戶輸入中（忽略空白與標點）才算數，回傳 (targets, 有依據的 metric 集合)。
    有依據且依據寫「待決定」、但目標值本身不在依據中時（模型自行訂定），目標值改為「待決定」。
    """
    compact_input = _compact_for_match(user_input)
    targets, verified = [], set()
    for entry in parsed.get("targets") or []:
        if not isinstance(entry, dict):
            continue
        metric = str(entry.get("metric") or "").strip()
        value = str(entry.get("value") or "").strip()
        if not metric or not value:
            continue
        # 比對是否出現在輸入中用去除標點的版本；目標值比對保留原文（含「%」等符號）
        evidence = re.sub(r"\s+", "", str(entry.get("evidence") or ""))
        compact_evidence = _compact_for_match(evidence)
        if compact_evidence and compact_evidence in compact_input:
            verified.add(metric)
            if "待決定" in evidence and value != "待決定" and not _target_value_in_text(value, evidence):
                logger.warning(f"[FactTense] target {metric}={value!r} replaced by 待決定 (evidence={evidence!r})")
                value = "待決定"
        targets.append((metric, value))
    return targets, verified


def build_targets_block(targets: List[Tuple[str, str]], tense_block: str = "") -> str:
    completed_lines = [line for line in (tense_block or "").splitlines() if "：已完成" in line]
    lines = []
    for metric, value in targets:
        if any(_target_value_in_text(value, line) for line in completed_lines):
            logger.warning(f"[FactTense] dropped target matching a completed item: {metric}={value!r}")
            continue
        lines.append(f"- {metric}：{value}")
    if not lines:
        return ""
    logger.info(f"[FactTense] key targets ({len(lines)}):\n" + "\n".join(lines))
    return "【關鍵指標目標值（全文所有章節必須一致）】\n" + "\n".join(lines)


def build_conflicts_block(parsed: Dict[str, Any], user_input: str) -> str:
    """與計畫執行期間不符的原文（如附件寫「13 週內完成」）逐條點名為不可沿用。

    通用提示詞規則無效（in-app 2026-10-05），改為點名具體原文；原文須逐字出現在用戶輸入中才採用。
    """
    compact_input = _compact_for_match(user_input)
    quotes = []
    for raw in parsed.get("conflicts") or []:
        quote = str(raw or "").strip()
        compact_quote = _compact_for_match(quote)
        if compact_quote and compact_quote in compact_input and quote not in quotes:
            quotes.append(quote)
    if not quotes:
        return ""
    logger.info(f"[FactTense] duration conflicts ({len(quotes)}): {quotes}")
    lines = "\n".join(f"- 「{q}」" for q in quotes)
    return (
        "【與計畫執行期間不符的原文（不可沿用）】\n"
        f"{lines}\n"
        "以上時程與【關鍵指標目標值】的「計畫執行期間」不符，內文不可沿用其中的週數或月數，"
        "一律改以計畫執行期間及進度表撰寫；內文不可提及此段名稱。"
    )


def _strip_internal_labels(value: Any) -> Any:
    # 遞迴移除章節 JSON 所有文字欄位中的內部清單名稱
    if isinstance(value, str):
        for pattern in _INTERNAL_LABEL_PATTERNS:
            value = pattern.sub("", value)
        return value
    if isinstance(value, list):
        return [_strip_internal_labels(v) for v in value]
    if isinstance(value, dict):
        return {k: _strip_internal_labels(v) for k, v in value.items()}
    return value

# 模型對用戶說的話（協助提議、補件提醒、資料來源說明）不是計畫書內容，提示詞之外再以程式移除整句
_USER_NOTE_PATTERNS = [
    re.compile(r"若需[^。！？\n]*我方可(?:協助|提供)"),
    re.compile(r"建議由申請單位"),
    re.compile(r"請於後續[^。！？\n]*補件"),
    re.compile(r"以實際(?:檔案|資料)替換\s*待決定"),
    re.compile(r"請填入(?:實際)?資料"),
    # in-app 2026-10-05 第十次：「若需補充特定執行證明…目前尚未取得，請以「待決定」處理。」
    re.compile(r"請以「?待決定」?(?:處理|填寫|標示|表示)"),
    re.compile(r"重[複覆](?:欄位|鍵位)"),
    # in-app 2026-10-05 第十一次：「（備註：本欄位已於上方說明成本降低之來源…）」，上方並無說明
    re.compile(r"本欄位"),
    re.compile(r"已於上方(?:說明|列出|敘述)"),
    re.compile(r"欄位(?:填寫|填)為"),
    re.compile(r"事實性資料"),
    re.compile(r"(?:附件|背景資料|問答內容|對話內容)(?:中)?(?:尚)?未(?:提供|記載|提及)"),
]
_SENTENCE_PATTERN = re.compile(r"[^。！？\n]*(?:[。！？]|\n|$)")
# 括號內的資料來源說明（如「（依申請單位提供之說明）」）只移除括號本身，保留句子內容；
# 「（詳見附件一）」等計畫書附件編號不在此限
# 說明佔位符本身的子句（如「…尚未取得，故標示為待決定」）只移除該子句；需有「故／因此／所以」才移除，
# 避免誤刪「專利狀態列為待決定」等正常敘述
# 「故」與「待決定」之間的用詞不限（「故金額為」、「故目前填為」、「故件數」，in-app 2026-10-05）
_PLACEHOLDER_NOTE_PATTERN = re.compile(r"[，,]?\s*(?:故|因此|所以)[^，,。；;！？\n]{0,12}?「?待決定」?")
# 句首說明資料來源未提供的子句（如「因申請資料中未提供具體客戶數與單價，」）只移除該子句，保留其餘內容
_MISSING_SOURCE_CLAUSE_PATTERN = re.compile(
    r"(?:因|由於)\s*(?:申請資料|申請單位|附件|背景資料|用戶|使用者|問答內容?|對話內容?)"
    r"[^，,。！？\n]{0,30}未(?:提供|記載|提及)[^，,。！？\n]{0,20}[，,]\s*"
)
# 主詞不限的「因／由於…（尚）未提供…，」子句（如「因具體預算編列尚未提供，」）；需有「未提供」才移除，
# 「因市場需求未明，」等正常子句不受影響
_MISSING_DATA_CLAUSE_PATTERN = re.compile(
    r"(?:因|由於)[^，,。！？\n]{0,30}?未提供[^，,。！？\n]{0,30}[，,]\s*"
)
# 括號內提到內部規則名稱的說明（如「（客戶數、單價等事實性資料：待決定）」）整個移除
_INTERNAL_RULE_NOTE_PATTERN = re.compile(r"[（(][^（）()]{0,40}事實性資料[^（）()]{0,20}[）)]")
# 括號外的同類說明（in-app 2026-10-05 第八次：「…推動專案；需補充之具體人力名單或職稱等事實性資料為待決定。」）
# 只移除該子句，保留前半句；位於句首的由 _USER_NOTE_PATTERNS 整句移除
_INTERNAL_RULE_CLAUSE_PATTERN = re.compile(r"[，,；;][^，,；;。！？\n]*事實性資料[^，,；;。！？\n]*")
_SOURCE_NOTE_PATTERN = re.compile(
    r"[（(]\s*(?:依|根據|據)\s*(?:申請單位|申請資料|申請書|用戶|使用者|附件(?![一二三四五六七八九十\d])|背景資料|問答內容?|對話內容?)[^（）()]{0,20}[）)]"
)


def _strip_user_notes(value: Any) -> Any:
    # 遞迴移除章節 JSON 文字欄位中對用戶說話的句子；整段都被移除時改填「待決定」
    if isinstance(value, str):
        # 佔位符統一為「待決定」；few-shot 範例以 OOO 遮罩敏感詞，模型可能照抄
        value = value.replace("OOO", "待決定")
        value = _SOURCE_NOTE_PATTERN.sub("", value)
        # 先移除「因…未提供，」子句，再移除其後的「故…待決定」，否則前者會失去結尾逗號
        value = _MISSING_SOURCE_CLAUSE_PATTERN.sub("", value)
        value = _MISSING_DATA_CLAUSE_PATTERN.sub("", value)
        value = _PLACEHOLDER_NOTE_PATTERN.sub("", value)
        value = _INTERNAL_RULE_NOTE_PATTERN.sub("", value)
        value = _INTERNAL_RULE_CLAUSE_PATTERN.sub("", value)
        # 子句移除後殘留的標點（如「；。」）
        value = re.sub(r"[，,；;、]\s*(?=[。！？])", "", value)
        sentences = [s for s in _SENTENCE_PATTERN.findall(value) if s]
        kept = [s for s in sentences if not any(p.search(s) for p in _USER_NOTE_PATTERNS)]
        if len(kept) == len(sentences):
            return value
        cleaned = "".join(kept).strip()
        return cleaned or "待決定"
    if isinstance(value, list):
        return [_strip_user_notes(v) for v in value]
    if isinstance(value, dict):
        return {k: _strip_user_notes(v) for k, v in value.items()}
    return value


class LLMService:
    PLACEHOLDER_VALUES = {"待決定", "未提供", "無", "暫無", "无"}

    def __init__(self):
        self.openai_api_key = OPENAI_API_KEY
        self.ollama_base_url = OLLAMA_BASE_URL
        self.max_retries = 3
        self.initial_retry_delay = 1  # 秒
        self.request_semaphore = asyncio.Semaphore(200)  # 同时最多 20 个请求（允许更多并发）
        self._last_response_json = {}  # 用於儲存最後一次API呼叫的完整響應
        self.GENERATION_TIMEOUT = 300  # 單個章節生成超時 300 秒
        self.TOTAL_GENERATION_TIMEOUT = 1800  # 整個計畫生成超時 30 分鐘

    # ========== 重試與容錯機制 ==========
    
    async def _retry_with_exponential_backoff(
        self,
        operation: Callable,
        max_retries: int = 3,
        error_types: tuple = (ValueError, json.JSONDecodeError),
        base_delay: float = 1.0,
        operation_name: str = "Operation"
    ) -> Tuple[Optional[Any], Optional[str]]:
        """統一的重試邏輯，支援指數退避
        
        Args:
            operation: 要執行的異步操作
            max_retries: 最多重試次數
            error_types: 需要重試的錯誤類型
            base_delay: 基礎延遲時間（秒）
            operation_name: 操作名稱（用於日誌）
            
        Returns:
            (result, error_message) - 成功返回結果，失敗返回錯誤信息
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = await operation()
                return result, None
            except error_types as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(
                        f"[{operation_name}] Attempt {attempt + 1}/{max_retries} failed: {e}. "
                        f"Retrying after {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"[{operation_name}] Final attempt ({max_retries}/{max_retries}) failed: {e}"
                    )
            except Exception as e:
                # 非預期的錯誤，不重試
                logger.error(f"[{operation_name}] Unexpected error: {e}")
                return None, str(e)
        
        return None, last_error

    async def _buffer_demo_usage(
        self,
        supabase_service: Optional["SupabaseService"],
        demo_session_id: Optional[str],
        model_info: Dict[str, Any],
        response_json: Optional[Dict[str, Any]],
        action: str,
    ) -> None:
        """Append one usage entry to demo.pending_usage_logs.

        Every external LLM call (initial, retry, JSON repair) must go
        through here so the demo's DEMO_MAX_TOKENS_PER_SESSION cap
        reflects total token spend, not just the successful attempt.
        """
        if not response_json or supabase_service is None or not demo_session_id:
            return
        if (model_info or {}).get("type") != "external":
            return
        try:
            await supabase_service.append_demo_usage_log(
                demo_session_id, model_info, response_json, action=action
            )
        except Exception as e:
            logger.warning("Failed to buffer demo usage: %s", e)

    async def _attempt_json_repair(
        self,
        raw_text: str,
        session: httpx.AsyncClient,
        model_info: Dict,
        section_id: str,
        supabase_service: Optional["SupabaseService"] = None,
        demo_session_id: Optional[str] = None,
        action: str = "JSON修復",
        max_attempts: int = 2,
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """嘗試修復格式不正確的 JSON
        
        首先試著直接解析，失敗則讓 LLM 修復 JSON
        
        Args:
            raw_text: 原始文本
            session: HTTP 會話
            model_info: 使用的模型信息
            section_id: 章節 ID
            max_attempts: 最多修復嘗試次數
            
        Returns:
            (parsed_json, error_message)
        """
        # 第一次：嘗試直接解析
        try:
            parsed = json.loads(raw_text)
            return parsed, None
        except json.JSONDecodeError:
            pass
        
        # 第二次：尋找首個完整的大括號區塊
        try:
            json_string = self._extract_first_json_object(raw_text)
            if not json_string:
                json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                json_string = json_match.group(0) if json_match else None
            if json_string:
                parsed = json.loads(json_string)
                return parsed, None
        except json.JSONDecodeError:
            pass
        
        # 第三次：讓 LLM 修復 JSON（如果允許）
        if max_attempts > 1 and model_info.get("provider") in {"openai", "gemini"}:
            repair_prompt = f"""以下 JSON 格式不正確，請修復並只返回有效的 JSON（不要有任何其他文字）：

{raw_text[:2000]}

要求：
1. 只返回有效的 JSON 物件
2. 確保所有括號、引號、逗號都是正確的
3. 保留原始的數據和結構
4. 不要添加任何解釋文字"""
            
            messages = [
                {"role": "system", "content": "你是 JSON 修復專家。严格只返回有效的 JSON，不要有任何其他文字。"},
                {"role": "user", "content": repair_prompt}
            ]
            
            try:
                logger.info(f"Attempting to repair JSON for section {section_id} using LLM...")
                repaired_text, error, repair_resp_json = await self.call_external_api(
                    session, model_info, messages, is_json_output=True
                )

                # Repair calls bill real tokens too; buffer them so the
                # demo's 100K cap reflects total spend, not just the
                # initial attempt.
                await self._buffer_demo_usage(
                    supabase_service, demo_session_id, model_info,
                    repair_resp_json, f"{action}(JSON修復)"
                )

                if error:
                    logger.warning(f"JSON repair failed: {error.get('error')}")
                    return None, f"JSON repair attempt failed: {error.get('error')}"
                
                if repaired_text:
                    try:
                        parsed = json.loads(repaired_text)
                        logger.info(f"✅ Successfully repaired JSON for section {section_id}")
                        return parsed, None
                    except json.JSONDecodeError as e:
                        logger.warning(f"Repaired JSON is still invalid: {e}")
                        return None, f"LLM-repaired JSON is still invalid: {str(e)}"
            except Exception as e:
                logger.warning(f"JSON repair attempt raised exception: {e}")
                return None, f"JSON repair exception: {str(e)}"
        
        # 修復失敗
        return None, f"Unable to parse or repair JSON. First 500 chars: {raw_text[:500]}"

    @staticmethod
    def _extract_first_json_object(raw_text: str) -> Optional[str]:
        """利用括號深度追蹤擷取第一個完整的 JSON 物件。"""
        depth = 0
        start_idx = None
        in_string = False
        escape = False

        for idx, ch in enumerate(raw_text):
            if in_string:
                if escape:
                    escape = False
                    continue
                if ch == "\\":
                    escape = True
                    continue
                if ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
                continue

            if ch == '{':
                if depth == 0:
                    start_idx = idx
                depth += 1
            elif ch == '}':
                if depth == 0:
                    continue
                depth -= 1
                if depth == 0 and start_idx is not None:
                    return raw_text[start_idx:idx + 1]

        return None

    def _validate_generated_content(self, content_json: Dict, section_id: str) -> Tuple[bool, Optional[str]]:
        """驗證生成的內容是否有實質內容，不只是空枚舉
        
        Args:
            content_json: 生成的JSON對象
            section_id: 章節ID
            
        Returns:
            (is_valid, error_message)
        """
        if not content_json:
            return False, "Generated content is empty (None)"
        
        if not isinstance(content_json, dict):
            return False, f"Generated content is not a dict: {type(content_json)}"
        
        if len(content_json) == 0:
            return False, "Generated content dict is empty"
        
        # 檢查是否所有值都是空的
        non_empty_fields = 0
        for key, value in content_json.items():
            if self._has_substantial_content(value):
                non_empty_fields += 1
        
        if non_empty_fields == 0:
            return False, f"Generated content has no substantial data. All fields are empty or just placeholders."
        
        # 至少30%的字段應該有內容
        content_ratio = non_empty_fields / len(content_json)
        if content_ratio < 0.3:
            return False, f"Generated content is too sparse. Only {non_empty_fields}/{len(content_json)} fields have substance."
        
        return True, None

    @classmethod
    def _has_substantial_content(cls, value: Any) -> bool:
        """遞迴檢查任意型別是否有實質內容，避免僅計數非空結構。"""
        if value is None:
            return False

        if isinstance(value, str):
            stripped = value.strip()
            return bool(stripped and stripped not in cls.PLACEHOLDER_VALUES)

        if isinstance(value, dict):
            return any(cls._has_substantial_content(v) for v in value.values())

        if isinstance(value, list):
            return any(cls._has_substantial_content(item) for item in value)

        if isinstance(value, (int, float)):
            return True

        if isinstance(value, bool):
            return value

        return True

    @staticmethod
    def _extract_openai_response_text(payload: Dict[str, Any]) -> str:
        """解析 OpenAI Responses API 回傳的文字內容。"""
        output_blocks = payload.get("output") or []
        collected_text: List[str] = []

        for block in output_blocks:
            block_type = block.get("type")
            if block_type in {"output_text", "text"}:
                text_value = block.get("text")
                if isinstance(text_value, list):
                    collected_text.extend([str(t) for t in text_value])
                elif text_value:
                    collected_text.append(str(text_value))
            elif block_type == "message":
                for content in block.get("content", []):
                    if content.get("type") in {"output_text", "text"} and content.get("text"):
                        collected_text.append(str(content["text"]))

        if collected_text:
            return "\n".join(collected_text)

        # Responses API 也可能透過 choices/message fallback
        choices = payload.get("choices") or []
        if choices:
            message = choices[0].get("message", {})
            if isinstance(message, dict):
                return message.get("content", "") or ""

        raise ValueError("OpenAI Responses payload did not contain textual output.")
    
    def _get_provider_for_model(self, model_id: str, app_state: Any = None) -> str:
        """根據 model_id 判斷屬於哪個 provider"""
        if app_state is not None:
            registry = getattr(app_state, "model_registry", None) or {}
            model_info = registry.get(model_id)
            if model_info and model_info.get("provider"):
                return normalize_provider(model_info["provider"])

        logger.warning(
            f"Provider registry lookup missed for model_id={model_id!r}; "
            f"falling back to prefix heuristic."
        )
        if model_id.startswith("gemini-"):
            return "gemini"
        elif model_id.startswith("gpt-") or model_id.startswith("gpt4") or model_id.startswith("gpt-5") or model_id.startswith("gpt-4"):
            return "openai"
        else:
            return "openai"  # Default to openai

    def _get_model_cost_info(self, model_id: str, app_state: Any = None) -> Dict[str, float]:
        """Read cost_info from DB-loaded model_registry instead of hardcoded dicts.
        
        Args:
            model_id: The model identifier.
            app_state: FastAPI app.state containing model_registry.
        
        Returns:
            {"input": input_cost_per_million, "output": output_cost_per_million}
        """
        # 1. Try to read from DB-loaded registry first
        if app_state and hasattr(app_state, 'model_registry'):
            registry = app_state.model_registry
            
            # Exact match
            model_info = registry.get(model_id)
            if model_info and model_info.get('cost_info'):
                return model_info['cost_info']
            
            # Prefix match (e.g., "gpt-5-mini-latest" matches "gpt-5-mini")
            for mid, minfo in registry.items():
                if model_id.startswith(mid) and minfo.get('cost_info'):
                    return minfo['cost_info']
        
        # 2. Fallback to hardcoded defaults (legacy safety net)
        legacy_costs = {
            "gpt-5.4-nano": {"input": 0.10, "output": 0.40},
            "gpt-5.2": {"input": 1.75, "output": 14.00},
            "gpt-5.1": {"input": 1.25, "output": 10.00},
            "gpt-5-mini": {"input": 0.25, "output": 2.00},
            "gpt-5-nano": {"input": 0.05, "output": 0.40},
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
            "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
            "gemini-3.1-pro-preview": {"input": 2.00, "output": 12.00},
            "gemini-3.1-flash-lite": {"input": 0.10, "output": 0.40},
            "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
            "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
            "gemini-3.1-flash-lite-image": {"input": 0.25, "output": 1.50},
            "chat-latest": {"input": 5.00, "output": 30.00},
        }
        
        if model_id in legacy_costs:
            return legacy_costs[model_id]
        
        for mid, cost in legacy_costs.items():
            if model_id.startswith(mid):
                return cost
        
        logger.warning(f"Cost info not found for model {model_id}, using default")
        return {"input": 0.0, "output": 0.0}

    def _get_model_capabilities(self, model_id: str, app_state: Any = None) -> Dict[str, Any]:
        if not app_state:
            return {}
        registry = getattr(app_state, "model_registry", None) or {}
        model_info = registry.get(model_id)
        if model_info and model_info.get("capabilities"):
            return model_info["capabilities"]
        return {}


    async def _format_few_shot_examples(self, user_input: str, section_details: SectionConfig, supabase_service: "SupabaseService") -> str:
        exemplars = await supabase_service.retrieve_similar_datasets(
            query_prompt=user_input,
            grant_id=section_details.grant_id,
            template_id=section_details.template_id,
            section_id=section_details.id,
            limit=3
        )
        if not exemplars:
            logger.info(f"[Few-Shot] Section '{section_details.id}': no exemplars retrieved, skipping few-shot injection")
            return ""
        
        exemplar_ids = [ex.get('id') for ex in exemplars]
        logger.info(f"[Few-Shot] Section '{section_details.id}': formatting {len(exemplars)} exemplars (IDs={exemplar_ids}) for prompt injection")

        formatted_examples = []
        for ex in exemplars:
            answer = json.dumps(ex.get('final_answer', {}), ensure_ascii=False)
            formatted_examples.append(f"{answer}")
        
        # ⚠️ 添加防数据泄露和防止直接复制的提示
        few_shot_warning = """【重要：範例使用指南】
以下是一些高質量的輸出範例。請注意：
1. ⚠️ 範例中的具體資料（公司名稱、人名、數據、聯絡資訊等）只是示例，絕對不要直接複製到你的輸出中
2. ✅ 你應該學習範例的「格式、邏輯組織方式」，但使用「新的、相關的內容」
3. 🔒 保護隱私：不要在生成的內容中包含任何範例中的具體個人或公司資訊
4. 🎯 根據當前的用戶輸入和背景，生成完全不同的、新鮮的內容
5. 如果不確定某些資訊，請使用佔位符「待決定」而不是複製範例中的內容
6. 結構可能會和範例不同，那就根據需求調整，學習的是範例邏輯和組織方式，而不是死搬硬套。

【結構參考範例】
"""
        result = few_shot_warning + "\n\n---\n\n".join(formatted_examples) + "\n\n【現在根據上述格式，為當前用戶生成新的、原創的內容】\n\n"
        logger.info(f"[Few-Shot] Section '{section_details.id}': few-shot string built ({len(result):,} chars)")
        return result

    def _build_api_request(
        self, 
        model_info: Dict,
        messages: List[Dict],
        is_json_output: bool,
        enable_grounding: bool = False,
        reasoning_effort: Optional[str] = None,
    ) -> Tuple[str, Dict, Dict]:
        """根據 model_info 建立 API 請求的 URL, headers, 和 payload"""
        provider = normalize_provider(model_info.get("provider"))
        model_id = model_info.get("id")
        capabilities = model_info.get("capabilities") or {}
        json_mode_enabled = is_json_output and capabilities.get("supports_json_mode", True)
        grounding_enabled = enable_grounding and capabilities.get("supports_grounding", True)

        if provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY not set.")

            url = "https://api.openai.com/v1/responses"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            }

            # 將 Chat messages 轉成 Responses API 的 input
            # OpenAI 官方建議
            input_messages = []
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")

                if not content or not str(content).strip():
                    continue

                normalized_role = role if role in {"system", "user", "assistant"} else "user"

                input_messages.append({
                    "role": normalized_role,
                    "content": str(content) 
                })

            payload = {
                "model": model_id,
                "input": input_messages, # 這裡傳入簡化後的列表
            }

            if (
                reasoning_effort in {"low", "medium", "high"}
                and isinstance(model_id, str)
                and model_id.startswith("gpt-5")
            ):
                payload["reasoning"] = {"effort": reasoning_effort}

            # Web Search
            if grounding_enabled:
                payload["tools"] = [{"type": "web_search"}]

            if json_mode_enabled:
                payload["text"] = {"format": {"type": "json_object"}}

            return url, headers, payload

        elif provider == "ollama":
            url = f"{self.ollama_base_url}/chat/completions"
            headers = {"Content-Type": "application/json"}
            payload = {"model": model_id, "messages": messages, "stream": False, "options": {"temperature": 0.3}}
            if json_mode_enabled: payload["format"] = "json"
            return url, headers, payload
        
        elif provider == "gemini":
            from app.config import GEMINI_API_KEY
            if not GEMINI_API_KEY: raise ValueError("GEMINI_API_KEY not set.")

            # 1. URL 設定 (使用 v1beta 以獲得最新功能支持)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
            headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}

            gemini_contents = []
            system_instruction = None

            # 2. 訊息處理 (分離 System Instruction 與 對話歷史)
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                
                # Gemini 的 System Prompt 是獨立欄位，不能放在 contents 裡
                if role == "system":
                    system_instruction = {
                        "parts": [{"text": content}]
                    }
                    continue

                # 對話歷史
                gemini_role = "user" if role == "user" else "model"
                gemini_contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })

            # 3. 構建 Payload
            payload = {
                "contents": gemini_contents,
                "generationConfig": {
                    "temperature": 0.3
                }
            }

            # 加入 System Instruction (如果有的話)
            if system_instruction:
                payload["systemInstruction"] = system_instruction

            # 加入 JSON Mode
            if json_mode_enabled:
                payload["generationConfig"]["responseMimeType"] = "application/json"

            # 4. 加入 Grounding (Google Search)
            # 對應官方 SDK: tools=[types.Tool(google_search=types.GoogleSearch())]
            if grounding_enabled:
                payload["tools"] = [
                    {
                        "googleSearch": {}  # 注意：這裡是 googleSearch (駝峰式)，值為空物件即可
                    }
                ]

            return url, headers, payload
            
        raise ValueError(f"Unsupported external provider: {provider}")

    async def stream_external_api(
        self,
        session: httpx.AsyncClient,
        model_info: Dict,
        messages: List[Dict],
        is_json_output: bool = False,
    ):
        """流式調用 OpenAI，逐段推送 delta。

        為了支持成本記錄，此方法返回一個包含：
        - 文本塊（通過 yield）
        - 最終響應對象（設置到 self._last_response_json）

        is_json_output=True 時會要求 OpenAI 以 JSON 物件格式回傳。注意：串流中的每個
        delta 僅是該 JSON 文件的片段，呼叫端（WS handler）必須完整緩衝後才能解析，
        不可逐塊嘗試解析 JSON。
        """
        provider = normalize_provider(model_info.get("provider"))
        model_id = model_info.get("id")
        if provider != "openai":
            raise ValueError(f"Streaming only supported for OpenAI, got {provider}")

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set.")

        capabilities = model_info.get("capabilities") or {}
        if not capabilities.get("supports_streaming", True):
            raise ValueError(f"Model '{model_id}' does not support streaming.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model_id,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True}
            # "temperature": 0.7,
        }
        if is_json_output and capabilities.get("supports_json_mode", True):
            payload["response_format"] = {"type": "json_object"}

        try:
            last_response_json = {}
            async with session.stream("POST", url, json=payload, headers=headers, timeout=900) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise ValueError(f"OpenAI API error {response.status_code}: {error_text}")
                
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data_str)
                        # 保存最後一條包含usage的響應（包括choices為空但有usage的最後chunk）
                        if "usage" in chunk:
                            last_response_json = chunk
                        
                        # 安全地提取delta內容，處理空choices陣列
                        choices = chunk.get("choices", [])
                        if choices and len(choices) > 0:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
            
            # 保存最終響應供外部使用
            self._last_response_json = last_response_json
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            raise

    async def call_external_api(
        self,
        session: httpx.AsyncClient,
        model_info: Dict,
        messages: List[Dict],
        is_json_output: bool = False,
        enable_grounding: bool = False,
        response_hook: Optional[Callable[[Dict[str, Any]], None]] = None,
        reasoning_effort: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[Dict], Optional[Dict]]:
        """呼叫外部 LLM API (如 OpenAI, Ollama, Gemini)，並處理重試邏輯和錯誤。
        
        支持以下錯誤類型的自動重試：
        - 429 Rate Limit: 使用 Retry-After 或指數退避
        - 5xx 服務器錯誤: 使用指數退避
        - 超時錯誤: 使用指數退避
        - 連接錯誤: 使用指數退避
        
        Returns:
            Tuple of (text_output, error_dict, response_json)
            - text_output: 提取的文本輸出
            - error_dict: 錯誤信息（如果有）
            - response_json: 完整的 API 響應（用於提取 token 計數）
        """
        async with self.request_semaphore:  # 限制并发请求数
            for attempt in range(self.max_retries): 
                try:
                    api_url, headers, payload = self._build_api_request(
                        model_info,
                        messages,
                        is_json_output,
                        enable_grounding=enable_grounding,
                        reasoning_effort=reasoning_effort,
                    )
                    response = await session.post(api_url, json=payload, headers=headers, timeout=900)
                    response.raise_for_status()
                    
                    # 根據 provider 解析響應
                    provider = model_info.get("provider")
                    try:
                        response_json = response.json()
                    except json.JSONDecodeError as decode_error:
                        raw_body = (response.text or "")[:2000]
                        logger.error(
                            "Provider response is not valid JSON for model %s: %s | Body snippet: %s",
                            model_info.get("id"),
                            decode_error,
                            raw_body,
                            exc_info=True,
                        )
                        return None, {"error": "Provider returned invalid JSON payload."}, None

                    if response_hook:
                        try:
                            response_hook(response_json)
                        except Exception:
                            logger.warning("Response hook failed", exc_info=True)
                    
                    if provider == "gemini":
                        # Gemini 響應格式
                        content = response_json.get("candidates", [{}])[0].get("content", {})
                        parts = content.get("parts", [{}])
                        text = parts[0].get("text", "") if parts else ""
                        return text, None, response_json
                    elif provider == "openai":
                        text_output = self._extract_openai_response_text(response_json)
                        return text_output, None, response_json
                    else:
                        # Ollama 或其他 Chat-Completions 相容 API
                        return response_json["choices"][0]["message"]["content"], None, response_json
                    
                except httpx.HTTPStatusError as e:
                    status_code = e.response.status_code
                    
                    # === 429 Speed Rate Limit ===
                    if status_code == 429:
                        if attempt < self.max_retries - 1:
                            # 从响应头获取 Retry-After，如果没有则使用指数退避
                            retry_after = e.response.headers.get("Retry-After")
                            if retry_after:
                                try:
                                    wait_time = int(retry_after)
                                except ValueError:
                                    wait_time = self.initial_retry_delay * (2 ** attempt)
                            else:
                                wait_time = self.initial_retry_delay * (2 ** attempt)  # 指数退避: 1, 2, 4 秒
                            
                            logger.warning(
                                f"[Attempt {attempt + 1}/{self.max_retries}] Rate limited (429) for model {model_info.get('id')}. "
                                f"Retrying after {wait_time}s..."
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_msg = f"API rate limited (429) for model {model_info.get('id')} after {self.max_retries} attempts"
                            logger.error(error_msg)
                            return None, {"error": error_msg}, None
                    
                    # === 5xx Server Errors (可重試) ===
                    elif status_code >= 500 and status_code < 600:
                        if attempt < self.max_retries - 1:
                            wait_time = self.initial_retry_delay * (2 ** attempt)
                            logger.warning(
                                f"[Attempt {attempt + 1}/{self.max_retries}] Server error ({status_code}) for model {model_info.get('id')}. "
                                f"Retrying after {wait_time}s..."
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_msg = f"API server error ({status_code}) for model {model_info.get('id')} after {self.max_retries} attempts"
                            logger.error(error_msg)
                            return None, {"error": error_msg}, None
                    
                    # === 4xx Client Errors (不可重試，除了 429) ===
                    else:
                        error_msg = f"API client error ({status_code}) for model {model_info.get('id')}: {e}"
                        logger.error(error_msg, exc_info=True)
                        return None, {"error": error_msg}, None
                    
                except asyncio.TimeoutError as e:
                    # 超時錯誤可重試
                    if attempt < self.max_retries - 1:
                        wait_time = self.initial_retry_delay * (2 ** attempt)
                        logger.warning(
                            f"[Attempt {attempt + 1}/{self.max_retries}] Request timeout for model {model_info.get('id')}. "
                            f"Retrying after {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_msg = f"API request timeout for model {model_info.get('id')} after {self.max_retries} attempts"
                        logger.error(error_msg)
                        return None, {"error": error_msg}, None
                
                except (httpx.ConnectError, httpx.NetworkError) as e:
                    # 連接錯誤可重試
                    if attempt < self.max_retries - 1:
                        wait_time = self.initial_retry_delay * (2 ** attempt)
                        logger.warning(
                            f"[Attempt {attempt + 1}/{self.max_retries}] Network error for model {model_info.get('id')}: {e}. "
                            f"Retrying after {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_msg = f"Network error for model {model_info.get('id')} after {self.max_retries} attempts: {e}"
                        logger.error(error_msg)
                        return None, {"error": error_msg}, None
                    
                except ValueError as e:
                    # 配置錯誤，不重試
                    error_msg = f"Configuration error for model {model_info.get('id')}: {e}"
                    logger.error(error_msg, exc_info=True)
                    return None, {"error": error_msg}, None
                    
                except Exception as e:
                    # 非預期的錯誤
                    error_msg = f"Unexpected error during API call for model {model_info.get('id')}: {repr(e)}"
                    logger.error(error_msg, exc_info=True)
                    return None, {"error": error_msg}, None
        
        # 應該不會到達這裡（已在迴圈中返回）
        return None, {"error": f"API call exhausted all {self.max_retries} attempts"}, None

    @staticmethod
    def _extract_external_sources(provider: Optional[str], payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """從提供者的 payload 中提取引用/來源 URL。"""

        sources: List[Dict[str, Any]] = []
        if not isinstance(payload, dict):
            return sources

        provider_label = provider or "unknown"

        def append_source(url: Optional[str], title: Optional[str] = None, snippet: Optional[str] = None):
            if not url:
                return
            sources.append(
                {
                    "provider": provider_label,
                    "url": url,
                    "title": title,
                    "snippet": snippet,
                }
            )

        def iter_list(items):
            return items if isinstance(items, list) else []

        # OpenAI style metadata
        metadata = payload.get("metadata") or payload.get("response_metadata") or {}
        for entry in iter_list(metadata.get("citations") or metadata.get("references") or []):
            append_source(entry.get("url") or entry.get("source"), entry.get("title"), entry.get("snippet") or entry.get("quote"))

        # Responses API tool outputs may be embedded inside output blocks
        for block in iter_list(payload.get("output")):
            for content in iter_list(block.get("content")):
                for citation in iter_list(content.get("citations")):
                    append_source(citation.get("url") or citation.get("source"), citation.get("title"), citation.get("snippet"))
                for annotation in iter_list(content.get("annotations")):
                    append_source(
                        annotation.get("url") or annotation.get("source"),
                        annotation.get("title"),
                        annotation.get("snippet") or annotation.get("text"),
                    )

        # Choices[].message.content annotations fallback
        for choice in iter_list(payload.get("choices")):
            message = choice.get("message") or {}
            for part in iter_list(message.get("content")):
                for annotation in iter_list(part.get("annotations")):
                    append_source(
                        annotation.get("url") or annotation.get("source"),
                        annotation.get("title"),
                        annotation.get("snippet") or annotation.get("text"),
                    )

        # Gemini grounding metadata
        gemini_grounding = payload.get("groundingMetadata") or payload.get("grounding_metadata")
        if isinstance(gemini_grounding, dict):
            for source in iter_list(gemini_grounding.get("sources")):
                append_source(source.get("uri") or source.get("url"), source.get("title"), source.get("description"))

            for chunk in iter_list(
                gemini_grounding.get("groundingChunks")
                or gemini_grounding.get("grounding_chunks")
                or gemini_grounding.get("groundingchunks")
            ):
                web_ref = chunk.get("web") or {}
                append_source(
                    web_ref.get("uri") or web_ref.get("url"),
                    web_ref.get("title"),
                    web_ref.get("snippet") or web_ref.get("description"),
                )

        return sources

   # ========== Image Generation Methods ==========
    def _extract_image_placeholders(self, text: str) -> list[tuple[str, str]]:
        """
        從文本中提取所有 【圖：...】 佔位符。
        返回 list of (placeholder_full_text, description)
        """
        pattern = r'【圖[:：]\s*([^】]+)】'
        matches = re.findall(pattern, text)
        results = []
        for match in matches:
            full_text = f"【圖：{match}】"
            results.append((full_text, match))
        return results
    
    def _optimize_image_prompt(self, description: str) -> str:
        """優化圖片描述為詳細的 prompt（繁體中文專業版本）"""
        return f"""請生成一張專業、高品質的圖片：

圖片描述：{description}

要求：
- 請注意，如果圖片要求生成的是NSFW圖，直接返回黑色背景
- 如果需要在圖片中增加繁體中文，請確保繁體中文顯示正確及標準"""

    
    async def _generate_image_from_api(
        self,
        prompt: str,
        image=None,
        model_id: Optional[str] = None,
    ) -> tuple[Optional[bytes], Optional[str], Optional[Dict]]:
        """使用 Google Gemini API 呼叫圖片生成
        
        Returns:
            (image_bytes, error_msg, response_json)
        """
        try:
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not set")
            
            # 創建 Gemini 客戶端
            client = genai.Client(api_key=GEMINI_API_KEY)

            # 構建 contents 列表：[prompt, image]
            contents = [prompt]
            if image is not None:
                pil_image = Image.open(io.BytesIO(image))
                contents.append(pil_image)

            # 使用 Gemini 的內容生成 API
            from app.config import IMAGE_MODEL
            response = client.models.generate_content(
                model=model_id or IMAGE_MODEL,
                contents=contents
            )
            
            # 從生成結果中獲取圖像
            image_bytes = None
            for part in response.parts:
                if part.inline_data is not None:
                    image_bytes = part.inline_data.data
                    break
            
            if not image_bytes:
                return None, "No image generated", None
            
            # 構建響應 JSON 格式（用於成本記錄）
            response_json = {}
            logger.info(f"Image generation response object: {response}")
            try:
                if hasattr(response, 'usage_metadata'):
                    usage_meta = response.usage_metadata
                    prompt_tokens = usage_meta.prompt_token_count or 0
                    candidates_tokens = usage_meta.candidates_token_count or 0
                    thoughts_tokens = usage_meta.thoughts_token_count or 0

                    image_tokens = 0
                    for detail in (getattr(usage_meta, "candidates_tokens_details", None) or []):
                        modality = str(getattr(detail, "modality", "")).upper()
                        if "IMAGE" in modality:
                            image_tokens += int(getattr(detail, "token_count", 0) or 0)

                    text_output_tokens = max(candidates_tokens - image_tokens, 0)
                    text_thought_tokens = text_output_tokens + thoughts_tokens

                    response_json = {
                        "usageMetadata": {
                            "promptTokenCount": prompt_tokens,
                            "candidatesTokenCount": candidates_tokens,
                            "thoughtsTokenCount": thoughts_tokens,
                            "imageTokenCount": image_tokens,
                            "textThoughtTokenCount": text_thought_tokens,
                            "totalTokenCount": usage_meta.total_token_count or (prompt_tokens + candidates_tokens + thoughts_tokens),
                        }
                    }
                else:
                    logger.warning("Response object does not have usage_metadata attribute")
            except Exception as e:
                logger.warning(f"Failed to extract usage metadata: {e}", exc_info=True)
            
            return image_bytes, None, response_json
                
        except Exception as e:
            error_msg = f"Failed to generate image: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg, None

    async def classify_fact_tense(
        self,
        http_session: httpx.AsyncClient,
        grant_id: str,
        template_id: str,
        section_id: str,
        user_input: str,
        app_state: Any,
        user_id: str,
        supabase_service: "SupabaseService",
        is_external: Optional[bool] = None,
        selected_model: Optional[str] = None,
        project_id: Optional[str] = None,
        include_targets: bool = True,
        strict: bool = False,
    ) -> str:
        # 生成各章節前先統一判定事項時態（已完成／規劃中），避免各章節分別判斷而時態不一致。
        # 失敗時回傳空字串，不影響後續生成；strict 時改為拋出 FactCheckError，由呼叫端停止生成。
        if not (user_input or "").strip():
            return ""

        system_prompt = """你是計畫書事實整理助理。請從用戶輸入中找出所有「具體事項」（測試、驗證、認證、專利、獲獎、合作、導入、開發、上線、量產、政府計畫等），以及所有「性能或成果數字」（如準確率、效率、良率、節省成本比例等），逐一判定時態：
- 「已完成」：用戶描述中包含明確的完成性字眼（如已完成、已取得、已簽約、已上線、已量產、已導入、曾於某時完成）。若有提供時間點，填入 time。
- 「現況」：用戶以現在式描述公司目前持續存在的狀態，而非已完成的單一事件或未來規劃（如「與某公司維持多年合作關係」、「目前擁有某通路」）。
- 「規劃中」：其他所有情況，包括只描述內容或做法（如「進行某項測試」、「導入某系統」、「取得某認證」）而沒有完成性字眼者。性能或成果數字若沒有「已達成」、「經測試達」、「已驗證」等完成性字眼，一律判為「規劃中」，item 註明為目標值（如「鯨聲辨識準確率 97.3%（目標值）」）。無法確定時一律判為「規劃中」。
只整理用戶輸入中出現的事項，不可自行新增。每個 item 只能包含一件事實，不可把不同句子或不同來源（如問答與附件）的事實合併成一項；同一事實在多處出現時，任選一處的原文。item 必須忠於原文用語，不可加上原文沒有的限定詞（例如原文只寫「鯨聲辨識演算法準確率 97.3%」，不可寫成「浮標端鯨聲辨識演算法準確率 97.3%」）。描述現行市場作業方式（如「現行作業流程」）或競爭者的內容不是本公司事項，不要列入。
判為「已完成」時，evidence 必須逐字複製用戶輸入中含完成性字眼的原文片段（不可改寫或摘要）；判為「現況」時，evidence 必須逐字複製描述該狀態的原文片段；evidence 只能取自同一句原文，不可拼接或增刪任何字（如原文寫「已於 3 月完成測試」，不可寫成「已完成測試」）；判為「規劃中」時 evidence 填空字串。"""
        if include_targets:
            system_prompt += """
另外請訂出本計畫 5～8 項「關鍵指標目標值」（targets），供全文各章節統一引用，避免不同章節寫出不同數字：
- 選擇計畫最核心的性能指標（如準確率、延遲、續航時間）與產出數量（如衍生產品或服務項數、導入客戶數）。
- 每項只給一個明確的目標值；用戶輸入已提供的數字必須原樣使用，未提供的由你訂定合理的規劃目標值。用戶輸入寫明「待決定」的指標視為已提供，value 須原樣填「待決定」，不可自行訂定。
- 金額類指標（產值、營收、經費、預算、成本、投資額等）只有在用戶輸入已提供該金額時才可列入，且須原樣使用；用戶未提供時不可列入，也不可自行訂定金額。
- 必須列入一項 metric 為「衍生產品或服務」，value 寫出項數與名稱（如「2項（AI 報關文件助理、跨境法規查詢服務）」）；用戶有提供時（含寫明「待決定」）原樣使用，未提供時由你規劃；若本計畫確實沒有衍生產品或服務，value 填「0項」。衍生產品或服務是主產品以外延伸出的產品或服務，不可將本計畫的主要產品或服務（即「產出新產品或服務」）列為衍生項目。
- 必須列入一項 metric 為「產出新產品或服務」，value 寫出項數與名稱（如「1項（RAG 智能客服平台）」）；用戶有提供時原樣使用。
- 每項 targets 都要填 evidence：逐字複製用戶輸入中與此指標相關的原文片段（不可改寫或摘要），包含只寫「待決定」的回答（如「衍生商品或服務數：待決定」）；用戶完全沒有提及、由你自行訂定時才填空字串。
- 必須列入一項 metric 為「計畫執行期間」，value 寫出起訖年月與總月數（如「2026年11月～2027年04月，共6個月」）；用戶有提供期間或總週數時須與其相符，未提供時由你規劃，起始月份須晚於今天（{today}）。
- conflicts：逐字複製用戶輸入（含附件）中與你訂出的「計畫執行期間」不符的總時程描述（如期間為 6 個月，原文卻寫「於 13 週內完成」、「三階段共 13 週」），每項一段原文、不可改寫；沒有時為空陣列。
- 指標名稱要具體到不會混淆（如「端到端回報延遲」與「單次推論時間」是不同指標）。
- 已完成的成果數字不列入 targets（已列在 items）。
輸出純 JSON：{"items": [{"item": "事項簡述", "status": "已完成"、"現況" 或 "規劃中", "time": "時間點或空字串", "evidence": "原文片段或空字串"}], "targets": [{"metric": "指標名稱", "value": "目標值（含單位）", "evidence": "原文片段或空字串"}], "conflicts": ["原文片段"]}"""
            # 提示詞含 JSON 大括號無法用 .format，改以 replace 帶入今日日期（台灣時間）
            today_tw = datetime.now(timezone(timedelta(hours=8)))
            system_prompt = system_prompt.replace("{today}", f"{today_tw:%Y-%m-%d}")
        else:
            system_prompt += """
輸出純 JSON：{"items": [{"item": "事項簡述", "status": "已完成"、"現況" 或 "規劃中", "time": "時間點或空字串", "evidence": "原文片段或空字串"}]}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"用戶輸入：\n{user_input}"},
        ]

        try:
            parsed = await self._call_fact_json(
                http_session, grant_id, template_id, section_id, app_state, user_id, supabase_service,
                is_external, selected_model, project_id, messages, action="判定事項時態", tag="FactTense",
                feature_key="fact_tense",
            )
            if parsed is None:
                if strict:
                    raise FactCheckError("fact tense call failed")
                return ""

            lines = []
            for entry in parsed.get("items") or []:
                if not isinstance(entry, dict):
                    continue
                item = str(entry.get("item") or "").strip()
                if not item:
                    continue
                raw_status = entry.get("status")
                status = raw_status if raw_status in ("已完成", "現況") else "規劃中"
                evidence = str(entry.get("evidence") or "")
                # 事項本身逐字出現在用戶輸入中時也可作為依據（in-app 2026-10-05 第十次：evidence 漏字而不符原文，
                # 但事項「並與 Google 維持多年合作關係」與問答原文相同）
                candidates = (evidence, item)
                if status == "已完成" and not any(_has_completion_evidence(c, user_input) for c in candidates):
                    # 沒有完成性字眼但原文描述目前持續的狀態時（如「維持多年合作關係」）改為現況，不降為規劃中
                    status = "現況" if any(_has_state_evidence(c, user_input) for c in candidates) else "規劃中"
                    logger.warning(
                        f"[FactTense] downgraded to {status} (no completion evidence): {item} | evidence={evidence!r}"
                    )
                elif status == "現況" and not any(_has_state_evidence(c, user_input) for c in candidates):
                    logger.warning(f"[FactTense] downgraded to 規劃中 (no state evidence): {item} | evidence={evidence!r}")
                    status = "規劃中"
                time_text = str(entry.get("time") or "").strip()
                if status == "已完成":
                    label = f"已完成（{time_text}）" if time_text else "已完成"
                elif status == "現況":
                    label = "現況"
                else:
                    label = "尚未完成（以預計／將／目標語氣撰寫）"
                lines.append(f"- {item}：{label}")

            targets = []
            if include_targets:
                targets, verified = _apply_target_evidence(parsed, user_input)
                derivative_metric = next((m for m, _ in targets if "衍生" in m), "")
                targets = enforce_derivative_target(targets, user_input, derivative_metric in verified)
        except FactCheckError:
            raise
        except Exception as e:
            logger.warning(f"[FactTense] classification error: {e}")
            if strict:
                raise FactCheckError(str(e)) from e
            return ""

        blocks = []
        if lines:
            logger.info(f"[FactTense] classified {len(lines)} items:\n" + "\n".join(lines))
            blocks.append("【事項時態清單（全文所有章節必須依此撰寫）】\n" + "\n".join(lines))
        targets_block = build_targets_block(targets, "\n".join(lines))
        if targets_block:
            blocks.append(targets_block)
            conflicts_block = build_conflicts_block(parsed, user_input)
            if conflicts_block:
                blocks.append(conflicts_block)
        return "\n\n".join(blocks)

    async def extract_existing_targets(
        self,
        http_session: httpx.AsyncClient,
        grant_id: str,
        template_id: str,
        section_id: str,
        existing_content: str,
        app_state: Any,
        user_id: str,
        supabase_service: "SupabaseService",
        is_external: Optional[bool] = None,
        selected_model: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[Tuple[str, str]]:
        if not (existing_content or "").strip():
            return []

        system_prompt = """你是計畫書指標整理助理。以下是一份計畫書現有版本的內文，請找出其中 5～8 項最核心的「關鍵指標目標值」（性能指標如準確率、延遲、續航時間；產出數量如部署數量、衍生產品或服務項數），供版本更新時全文統一引用：
- value 必須逐字沿用內文的寫法（含比較符號與單位），不可訂定新的數值。
- 金額類指標（產值、營收、經費、預算、成本、投資額等）不列入，金額依用戶輸入另行處理。
- 若內文寫有計畫執行期間（起訖年月）或衍生產品或服務的項數，請分別以 metric「計畫執行期間」、「衍生產品或服務」列入，value 同樣逐字沿用內文寫法。
- 若不同段落對同一指標寫了不同數值，採用出現次數最多的數值。
- 只列規劃中的目標值；已完成測試的實測成果（如已於某時完成測試並達成的準確率）不列入。
- 指標名稱要具體到不會混淆（如「端到端回報延遲」與「單次推論時間」是不同指標）。
輸出純 JSON：{"targets": [{"metric": "指標名稱", "value": "目標值（含單位）"}]}"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"【現有版本內容】\n{existing_content}"},
        ]

        try:
            parsed = await self._call_fact_json(
                http_session, grant_id, template_id, section_id, app_state, user_id, supabase_service,
                is_external, selected_model, project_id, messages, action="整理既有指標", tag="ExistingTargets",
                feature_key="existing_targets",
            )
            if parsed is None:
                return []
            targets = []
            for metric, value in _parse_targets(parsed):
                if not _target_value_in_text(value, existing_content):
                    logger.warning(f"[ExistingTargets] dropped target not in existing version: {metric}={value!r}")
                    continue
                targets.append((metric, value))
            return targets
        except Exception as e:
            logger.warning(f"[ExistingTargets] extraction error: {e}")
            return []

    async def _call_fact_json(
        self,
        http_session: httpx.AsyncClient,
        grant_id: str,
        template_id: str,
        section_id: str,
        app_state: Any,
        user_id: str,
        supabase_service: "SupabaseService",
        is_external: Optional[bool],
        selected_model: Optional[str],
        project_id: Optional[str],
        messages: List[Dict[str, str]],
        action: str,
        tag: str,
        feature_key: str,
    ) -> Optional[Dict[str, Any]]:
        # 功能模型配置有指定模型時使用該模型，否則與計畫書章節使用相同模型
        override = get_feature_override(app_state, feature_key, is_external)
        if override:
            model_info = override
        elif selected_model:
            model_info = {
                "id": selected_model,
                "provider": self._get_provider_for_model(selected_model, app_state),
                "type": "external",
                "cost_info": self._get_model_cost_info(selected_model, app_state),
                "capabilities": self._get_model_capabilities(selected_model, app_state),
            }
        else:
            model_info = resolve_model(grant_id, template_id, section_id, app_state, is_external=is_external)
        if not model_info:
            return None

        raw_output, llm_error, resp_json = await self.call_external_api(
            http_session, model_info, messages, is_json_output=True,
            reasoning_effort="low",
        )
        if llm_error or not raw_output:
            logger.warning(f"[{tag}] call failed: {llm_error}")
            return None

        # Demo: user_id is the demo session id; buffer usage into the demo row
        # so the per-session token cap counts these pre-generation calls too.
        await self._buffer_demo_usage(supabase_service, user_id, model_info, resp_json, action)

        parsed, parse_error = extract_json_block(raw_output, tag)
        if parse_error or not isinstance(parsed, dict):
            logger.warning(f"[{tag}] could not parse output: {parse_error}")
            return None
        return parsed

    async def generate_section_content(
        self,  
        http_session: httpx.AsyncClient, 
        grant_id: str, 
        template_id: str, 
        section_id: str, 
        user_input: str,
        app_state: Any,
        user_id: str,
        supabase_service: "SupabaseService",
        use_actor_critic: bool = False,
        is_external: Optional[bool] = None,
        selected_model: Optional[str] = None,
        project_id: Optional[str] = None,
        section_context: Optional[str] = None,
        disable_few_shot: bool = False,
        section_details_override: Optional[SectionConfig] = None,
        action: str = "生成企劃書章節",
        previous_content: Optional[Dict[str, Any]] = None,
    ) -> SectionGenerateResponse:
        # 主要的內容生成流程，支持多模型路由、Grounding、Few-Shot
        # 1. --- 获取配置 ---
        section_details = section_details_override or await supabase_service.get_section_details(
            grant_id,
            template_id,
            section_id,
        )
        if not section_details or not section_details.json_schema or not section_details.system_prompt:
            return SectionGenerateResponse(section_id=section_id, error="Configuration error for section.")

        section_grounding_enabled = bool(getattr(section_details, "search_external", False))

        # 2. --- 路由与配额检查 ---
        if selected_model:
            # 根据 model_id 判断 provider，並取得成本資訊
            provider = self._get_provider_for_model(selected_model, app_state)
            cost_info = self._get_model_cost_info(selected_model, app_state)
            capabilities = self._get_model_capabilities(selected_model, app_state)
            original_model_info = {
                "id": selected_model,
                "provider": provider,
                "type": "external",
                "cost_info": cost_info,
                "capabilities": capabilities
            }
        else:
            original_model_info = resolve_model(grant_id, template_id, section_id, app_state, is_external=is_external)
        
        if not original_model_info:
            return SectionGenerateResponse(section_id=section_id, error="Model routing failed.")
        
        model_to_use = original_model_info
        model_type = model_to_use.get('type', 'internal')
        captured_external_sources: List[Dict[str, Any]] = []

        def capture_response_sources(payload: Dict[str, Any]):
            references = self._extract_external_sources(model_to_use.get("provider"), payload)
            if references:
                captured_external_sources.extend(references)

        # 3. --- 根据模型类型选择生成流程 ---
        final_content_json = None
        error_message = None
        response_json = None

        enable_grounding = section_grounding_enabled and model_to_use.get("provider") in {"openai", "gemini"}

        few_shot_str = ""
        if disable_few_shot:
            logger.info(f"[Few-Shot] Section '{section_details.id}': disabled (revision mode)")
        else:
            few_shot_str = await self._format_few_shot_examples(
                user_input, section_details, supabase_service
            )

        user_content_parts = []
        if few_shot_str:
            logger.info(f"[Few-Shot] Section '{section_details.id}': injecting few-shot examples into prompt")
            user_content_parts.append(few_shot_str.strip())
        elif not disable_few_shot:
            logger.info(f"[Few-Shot] Section '{section_details.id}': no examples available, proceeding without few-shot")
        user_content_parts.append(f"用户需求: {user_input}")
        if section_context:
            user_content_parts.append(
                "章節參考內容：\n" + section_context.strip()
            )
        user_content_parts.append(
            f"请根据以下 JSON schema 生成内容:\n{json.dumps(section_details.json_schema, ensure_ascii=False)}"
        )
        user_content = "\n\n".join(user_content_parts)
    
        # 檢查是否有自定義指令，並將它們附加到 user_content
        if section_details.custom_prompt_list:
            custom_prompts_str = "\n".join(f"- {p}" for p in section_details.custom_prompt_list)
            user_content += f"\n\n请额外遵循以下客製化指令：\n{custom_prompts_str}\n如果允許使用web search工具，請務必使用最新的網路資訊來補充回答內容。"

        # 提供今日日期（台灣時間，固定 UTC+8 以免 Windows 缺 tzdata），避免模型把計畫時程排在過去
        today_tw = datetime.now(timezone(timedelta(hours=8)))
        today_label = f"{today_tw:%Y-%m-%d}（民國{today_tw.year - 1911}年）"

        system_prompt_for_all = section_details.system_prompt + f"""

========== 內容生成指南 ==========
【今天日期】{today_label}

【圖片佔位符】若需要表示應插入圖片的位置，請使用 【圖：<圖片的簡單描述>】 的格式。例如：【圖：本公司研發之開片機實品操作展示照片】。

【數據/名稱佔位符】當遇到不確定的公司名稱、人名、或具體數據時，請統一使用「待決定」作為替代文字，不可使用 OOO 或其他佔位符。

【事實性資料（嚴格）】以下資訊只能來自用戶輸入（含問答摘要與背景資料），用戶未提供時一律使用「待決定」，絕對不可自行編造：
- 獲獎紀錄（獎項名稱、年度）
- 專利（名稱、編號、年度、類型）
- 曾參與之政府計畫實績（計畫名稱、執行期間、補助款、自籌款、人力、績效數字）
- 公司成立時間、資本額、員工人數
- 客戶、合作單位或供應商之名稱
- 執行單位、負責單位等公司或單位名稱（含進度表、查核點、人力配置）：只能使用用戶輸入中出現的名稱，不可自行虛構或改寫成新的公司名稱（如子公司、關係企業）
- 既有的客戶、合作關係、合作網路或通路（即使沒有具名，如「既有國際合作關係」、「既有合作網路」、「現有通路夥伴」）；用戶未提供時，只能寫成規劃（如「將拓展國際合作」），不可描述為已存在
- 已完成的測試、驗證或實際達成的成果數字
- 已進行的專利檢索、FTO 評估、市場或技術調查，以及其檢索範圍與結果（如「經初步檢索未發現相同專利」）；用戶未提供時，只能寫成規劃（如「將進行專利檢索與 FTO 評估」），不可描述為已進行或寫出結論
- 公司現有的產品原型、樣品、模組或系統，及其完成程度
- 公司或團隊的測試經驗、場域經驗，以及既有的測試資料或紀錄（如錄音、標註檔、評估報告）
- 團隊現有成員的具體組成（職稱、人數、個人經歷）；用戶未提供時，可概括描述公司具備的技術能力領域（如「具備聲學與軟體開發能力」），但不可列出具體職稱、人數或成員組成
- 金額數字：研發經費或預算（含人事費等各項細項）、產值、營收、降低成本、降低投資額、增加投資額等；用戶未提供時填「待決定」（如「產值：待決定」），可說明估算方式（如「依導入客戶數 × 平均合約金額估算」），但不可填入具體金額
僅限「獲獎紀錄」、「專利」、「曾參與之政府計畫實績」這三類表格：若用戶完全沒有提供資料，只輸出一列，各欄（含說明欄）都填「待決定」。

【比較表格】競爭力分析等比較型表格不適用上述「只輸出一列」規則，必須完整填寫所有比較項目與所有比較對象（包含本計畫及至少 2 家競爭者）：
- 用戶有提供競爭者名稱時必須使用；未提供時，可列出真實存在、公開知名的同業（如國際大型科技公司或該領域的知名產品），並依一般產業知識描述其產品與定位；不可虛構不存在的公司或產品，無法確定時以「待決定（同業）」等代稱。
- 技術優勢、市場區隔、行銷管道等描述性比較可依一般產業知識撰寫。
- 具體價格、市占率等數字若用戶未提供，一律使用「待決定」。

【內容質量要求】用戶的輸入若是無或是相關資料量不夠，可以針對描述性、規劃性內容（研發動機、做法、策略、預期規劃等）發散思維來寫作；上述事實性資料不在此限，仍須使用「待決定」。

【只寫計畫書內容】內文是要送審的計畫書，讀者是審查委員，不是用戶：
- 不可對用戶說話或提供協助、建議、補件提醒（如「若需，我方可協助彙整…」、「建議由申請單位補列…」、「請於後續資料補件中以實際檔案替換佔位內容…」、「請填入實際資料」、「具體金額待客戶提供…後再行量化」）；需要用戶補充的資訊直接填「待決定」即可，不可說明要等誰提供。
- 不可提及資料來源（如「附件未提供」、「背景資料未記載」、「依問答內容」、「用戶未提供」）；缺少的資訊直接寫「尚未取得」或「待決定」。

【時程】所有「預定」的日期（進度表、查核點、預定開始/結束時間等）都必須晚於今天日期，不可排在過去。若用戶輸入附有【關鍵指標目標值】中的「計畫執行期間」，全文的起訖月份都必須與其相同；內文的各階段週數或月數加總必須等於該期間（如共 4 個月約 17 週，不可寫成三階段共 13 週），進度表的起訖月份也必須相同。用戶輸入或附件中與「計畫執行期間」不符的週數或月數（如期間為 6 個月，附件卻寫「於 13 週內完成」）不可沿用，一律改以計畫執行期間表述。進度表的人月合計不可超過「計畫月數 × 投入人數」，投入人數須與用戶提供的團隊規模相符；用戶未提供時，以小型團隊的合理人數估算，不可為了填滿人月而虛增。進度表每一項工作的權重與人月都必須大於 0；沒有分配資源的工作不可單獨列項，應併入相關工作項目。

【百分比加總】若內容包含「計劃權重%」等代表整體分配的百分比欄位，所有項目加總必須剛好等於 100%。

【時態一致】只有用戶輸入明確寫出「已完成」（或「已於某年某月完成」等同義表述）的事項，才能寫成已完成；未明確說明的，一律以「預計」、「將」、「目標」等語氣撰寫。判斷方式：用戶的描述必須包含明確的「完成性字眼」（如已完成、已取得、已簽約、已上線、已量產、已導入、曾於某時完成），才能寫成已完成，若用戶有提供時間點則一併寫出；只描述內容或做法（如「進行某項測試」、「導入某系統」、「取得某認證」、「與某客戶合作」、「開發某產品」）而沒有完成性字眼者，一律視為規劃中。同一事項在全文所有章節都必須使用相同時態，不可在任何段落寫成已完成、另一段落寫成規劃中。若用戶輸入附有【事項時態清單】，清單中的事項必須嚴格依清單標示的時態撰寫，優先於你自己的判斷；清單標示「現況」的事項是公司目前持續存在的狀態，以現在式自然描述（如「公司與某公司維持多年合作關係」），不可寫成規劃（如「規劃延續…」、「將予以維繫」），也不可加註「（現況）」；清單的狀態詞（「現況」、「已完成」、「尚未完成」）只供判斷時態，不可寫進內文句子（如不可寫「現況測試良率約 90%」）；若章節參考內容的時態與清單不符，請依清單修正。【事項時態清單】僅供撰寫時參考，內文不可提及此清單名稱；若章節參考內容中已出現此名稱，請一併刪除。撰寫規劃中的事項時，請以「預計」、「將」、「目標」等自然用語融入句子，不可在句子、條列項目或表格欄位後加註「規劃中」或「（規劃中）」；如需說明整體狀態，每章節最多於開頭說明一次；已完成的事項也以「已於某年某月完成…」等自然句子表達，不可加註「（已完成）」；也不可為了支撐某個數字而虛構已進行的測試或驗證（如「初步測試達…」）。

【完成狀態不可延伸】用戶只說明某一事項已完成時，只能寫該事項本身已完成，不可推論相關的原型、模組、團隊、紀錄或經驗也已存在或完成（例如「已完成 30 天海上測試」不代表「已有產品原型」或「已完成模組驗證」）。成果數字只能歸屬於用戶描述的那次測試，不可轉用到其他尚未完成的事項，也不可冠上尚未完成的部署形式或位置（例如海上測試的準確率不可寫成「浮標端」、「端側」或「邊緣端」的辨識準確率）。已完成的測試也不可推論出用戶未提及的產出或能力（如「累積錄音樣本與標註資料」、「取得通訊參數」、「已具備浮標端辨識能力」），且須沿用用戶描述的測試方式與地點，不可改寫（如實海域測試不可寫成離線驗證）。描述計劃前狀況時，若用戶未說明現有的測試或資料，請寫「尚未進行」或使用「待決定」，不可自行描述（如「目前僅有室內或小規模測試資料」）。

【指標一致】若用戶輸入附有【關鍵指標目標值】，內文提到清單中的指標時，必須使用清單中的數值，不可改寫成其他數字，也不可降低或保留彈性（如清單為「完成 2 家企業導入」，不可寫成「至少 1 家」或「1～2 家」）。若章節需要清單以外、更細的指標，請使用不會與清單指標混淆的具體名稱（如清單為「端到端回報延遲」時，另寫「單次推論時間」），且數值須與清單合理一致。清單中的「衍生產品或服務」：衍生產品或服務表格與所有提及處（如預期效益、衍生商品或服務數）都必須使用相同的項數與名稱，不可一處寫「無」、另一處列出項目；清單為「0項」時，所有提及處都寫「無」；清單為「待決定」或用戶輸入寫明待決定時，衍生產品或服務表格與所有提及處都寫「待決定」，不可一處寫「無」、另一處寫「待決定」或列出可能項目。此清單僅供撰寫時參考，內文不可提及此清單名稱。

【⚠️ 嚴格禁止】
❌ 不要從上面的範例中直接複製任何資料（人名、公司名、聯絡資訊、具體數據等）
❌ 不要生成空白或只有佔位符的內容（上述事實性資料欄位除外）
❌ 不要只複製範例的結構而不填充實際內容
✅ 必須生成有實質內容的、相關的、原創的文本
✅ 每個字段都應該包含有意義的信息（至少 30% 的字段需要有實質內容）

【內容驗證】生成完成後，檢查：
1. 是否所有重要字段都有內容（不是空白或只有「待決定」；事實性資料欄位除外）
2. 是否內容來自於用戶輸入和你的知識，而非複製範例
3. 是否沒有編造任何事實性資料（獎項、專利、政府計畫實績、金額、年份）
4. 是否內容邏輯清晰、相關性強
5. 如果無法確定資訊，使用「待決定」而非留空"""
        messages = [
            {"role": "system", "content": system_prompt_for_all},
            {"role": "user", "content": user_content} 
        ]

        response_hook = capture_response_sources if enable_grounding else None

        # ========== 使用重試機制包裝 API 調用和 JSON 處理 ==========
        async def generate_and_parse_with_retry():
            """調用 API 並解析 JSON，支持重試。包括內容驗證，避免生成空白計畫書"""
            raw_output, llm_error, resp_json = await self.call_external_api(
                http_session,
                model_to_use,
                messages,
                enable_grounding=enable_grounding,
                is_json_output=True,
                response_hook=response_hook,
            )

            # Buffer this attempt's usage immediately — failed retries
            # still bill real tokens and must count toward the demo cap.
            await self._buffer_demo_usage(
                supabase_service, user_id, model_to_use, resp_json, action
            )

            if llm_error:
                raise ValueError(f"LLM API call failed: {llm_error.get('error', 'Unknown error')}")

            # 嘗試直接解析 JSON
            parsed_json, parse_error = extract_json_block(raw_output, section_id)

            if parse_error:
                # 首先嘗試使用 LLM 修復 JSON
                logger.warning(f"Initial JSON parsing failed for {section_id}, attempting repair...")
                # 功能模型配置有指定「修正 AI 回覆格式」的模型時使用該模型，否則沿用章節模型
                repair_model = get_feature_override(app_state, "json_repair", is_external) or model_to_use
                parsed_json, repair_error = await self._attempt_json_repair(
                    raw_output,
                    http_session,
                    repair_model,
                    section_id,
                    supabase_service=supabase_service,
                    demo_session_id=user_id,
                    action=action,
                )

                if repair_error:
                    raise ValueError(f"JSON parsing and repair failed: {repair_error}")
            
            # ========== 驗證生成的內容是否有實質內容 ==========
            is_valid, validation_error = self._validate_generated_content(parsed_json, section_id)
            if not is_valid:
                logger.warning(f"Content validation failed for {section_id}: {validation_error}. Retrying...")
                raise ValueError(f"Generated content validation failed: {validation_error}")
            
            logger.info(f"✅ Content validation passed for section {section_id}")
            return parsed_json, resp_json
        
        # 執行生成並自動重試
        result, retry_error = await self._retry_with_exponential_backoff(
            operation=generate_and_parse_with_retry,
            max_retries=3,
            error_types=(ValueError, json.JSONDecodeError, httpx.HTTPError),
            base_delay=1.0,
            operation_name=f"Section({section_id})"
        )
        
        if retry_error:
            return SectionGenerateResponse(
                section_id=section_id,
                error=f"Generation failed after retries: {retry_error}"
            )
        
        if result:
            final_content_json, _response_json = result

        # 4. --- 返回结果 ---
        if error_message:
            return SectionGenerateResponse(section_id=section_id, error=error_message)
        
        if not final_content_json:
            return SectionGenerateResponse(
                section_id=section_id, 
                error="Generation resulted in empty content."
            )
        
        final_content_json, _ = restore_emptied_fields(section_id, previous_content, final_content_json)
        final_content_json = _strip_internal_labels(final_content_json)
        final_content_json = _strip_user_notes(final_content_json)
        final_content_json = normalize_plan_weights(section_id, final_content_json)
        formatted_content = format_section_output(final_content_json, section_details.json_schema)

        if project_id:
            try:
                await supabase_service.log_execution_event(
                    project_id=project_id,
                    user_id=user_id,
                    event_type="section_generated",
                    section_id=section_id,
                    external_sources=captured_external_sources or None,
                    payload={
                        "model_id": model_to_use.get("id"),
                        "model_type": model_type,
                        "mode": "actor_critic" if use_actor_critic else "single_pass",
                    },
                )
            except Exception:
                logger.warning("Failed to log section_generated event", exc_info=True)
        
        return SectionGenerateResponse(
            section_id=section_id, 
            content=formatted_content,
            raw_json_content=final_content_json
        )