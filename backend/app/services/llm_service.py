# 封裝所有 LLM API 的呼叫邏輯

import httpx
import json
import re
from functools import partial
from typing import Dict, Any, Tuple, Optional, List, Callable, Awaitable
from app.config import OPENAI_API_KEY, OLLAMA_BASE_URL, IMAGE_MODEL, GEMINI_API_KEY
from app.models import SectionConfig, SectionGenerateResponse 
from app.utils.extract_json import extract_json_block
from app.models import SectionGenerateResponse
import asyncio
import logging
from app.utils.routing import resolve_model
from app.utils.formatting import format_section_output
import base64
from google import genai
import io
from PIL import Image

logger = logging.getLogger(__name__)

# 一個能生成文字的異步函數
GenerationFunc = Callable[..., Awaitable[Tuple[Optional[str], Optional[Dict]]]]

class LLMService:
    PLACEHOLDER_VALUES = {"OOO", "未提供", "無", "暫無", "无"}

    def __init__(self):
        self.openai_api_key = OPENAI_API_KEY
        self.ollama_base_url = OLLAMA_BASE_URL
        self.max_retries = 3
        self.initial_retry_delay = 1  # 秒
        self.request_semaphore = asyncio.Semaphore(200)  # 同时最多 20 个请求（允许更多并发）
        self._last_response_json = {}  # 用於儲存最後一次API呼叫的完整響應
        self.GENERATION_TIMEOUT = 120  # 單個章節生成超時 120 秒
        self.TOTAL_GENERATION_TIMEOUT = 600  # 整個計畫生成超時 10 分鐘

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

    async def _attempt_json_repair(
        self,
        raw_text: str,
        session: httpx.AsyncClient,
        model_info: Dict,
        section_id: str,
        max_attempts: int = 2
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
                repaired_text, error, _ = await self.call_external_api(
                    session, model_info, messages, is_json_output=True
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
    
    def _get_provider_for_model(self, model_id: str) -> str:
        """根據 model_id 判斷屬於哪個 provider"""
        if model_id.startswith("gemini-"):
            return "gemini"
        elif model_id.startswith("gpt-") or model_id.startswith("gpt4") or model_id.startswith("gpt-5") or model_id.startswith("gpt-4"):
            return "openai"
        else:
            return "openai"  # Default to openai

    def _get_model_cost_info(self, model_id: str) -> Dict[str, float]:
        """取得模型的成本資訊（每百萬tokens的美元成本）
        
        Returns:
            {
                "input": input_cost_per_million,
                "output": output_cost_per_million
            }
        """
        # OpenAI 模型成本（USD per 1M tokens）
        openai_costs = {
            "gpt-5.2": {"input": 1.75, "output": 14.00},
            "gpt-5.1": {"input": 1.25, "output": 10.00},
            "gpt-5": {"input": 1.25, "output": 10.00},
            "gpt-5-mini": {"input": 0.25, "output": 2.00},
            "gpt-5-nano": {"input": 0.05, "output": 0.40},
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
            "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
        }
        
        # Gemini 模型成本（USD per 1M tokens）
        gemini_costs = {
            "gemini-3-pro-preview": {"input": 2.00, "output": 12.00},
            "gemini-3-flash-preview": {"input": 0.50, "output": 3.00},
            "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
            "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
        }
        
        # 合併所有成本資訊
        all_costs = {**openai_costs, **gemini_costs}
        
        # 優先精確匹配，然後嘗試前綴匹配
        if model_id in all_costs:
            return all_costs[model_id]
        
        # 前綴匹配（例如 "gpt-5-mini" 匹配 "gpt-5-mini"）
        for model_name, cost in all_costs.items():
            if model_id.startswith(model_name):
                return cost
        
        # 默認成本（如果找不到）
        logger.warning(f"Cost info not found for model {model_id}, using default")
        return {"input": 0.0, "output": 0.0}


    async def _format_few_shot_examples(self, user_input: str, section_details: SectionConfig, supabase_service: "SupabaseService") -> str:
        exemplars = await supabase_service.retrieve_similar_datasets(
            query_prompt=user_input,
            grant_id=section_details.grant_id,
            template_id=section_details.template_id,
            section_id=section_details.id,
            limit=3
        )
        if not exemplars:
            return ""
        
        formatted_examples = []
        for ex in exemplars:
            prompt = ex.get('prompt', '')
            answer = json.dumps(ex.get('final_answer', {}), ensure_ascii=False)
            formatted_examples.append(f"{answer}")
        
        # ⚠️ 添加防数据泄露和防止直接复制的提示
        few_shot_warning = """【重要：範例使用指南】
以下是一些高質量的輸出範例。請注意：
1. ⚠️ 範例中的具體資料（公司名稱、人名、數據、聯絡資訊等）只是示例，絕對不要直接複製到你的輸出中
2. ✅ 你應該學習範例的「格式、邏輯組織方式」，但使用「新的、相關的內容」
3. 🔒 保護隱私：不要在生成的內容中包含任何範例中的具體個人或公司資訊
4. 🎯 根據當前的用戶輸入和背景，生成完全不同的、新鮮的內容
5. 如果不確定某些資訊，請使用佔位符（如 OOO）而不是複製範例中的內容
6. 結構可能會和範例不同，那就根據需求調整，學習的是範例邏輯和組織方式，而不是死搬硬套。

【結構參考範例】
"""
        return few_shot_warning + "\n\n---\n\n".join(formatted_examples) + "\n\n【現在根據上述格式，為當前用戶生成新的、原創的內容】\n\n"

    def _build_api_request(
        self, 
        model_info: Dict,
        messages: List[Dict],
        is_json_output: bool,
        enable_grounding: bool = False,
        reasoning_effort: Optional[str] = None,
    ) -> Tuple[str, Dict, Dict]:
        """根據 model_info 建立 API 請求的 URL, headers, 和 payload"""
        provider = model_info.get("provider")
        model_id = model_info.get("id")
        
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
            if enable_grounding:
                payload["tools"] = [{"type": "web_search"}]

            return url, headers, payload

        elif provider == "ollama":
            url = f"{self.ollama_base_url}/chat/completions"
            headers = {"Content-Type": "application/json"}
            payload = {"model": model_id, "messages": messages, "stream": False, "options": {"temperature": 0.3}}
            if is_json_output: payload["format"] = "json"
            return url, headers, payload
        
        elif provider == "gemini":
            from app.config import GEMINI_API_KEY
            if not GEMINI_API_KEY: raise ValueError("GEMINI_API_KEY not set.")

            # 1. URL 設定 (使用 v1beta 以獲得最新功能支持)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}

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
            if is_json_output:
                payload["generationConfig"]["responseMimeType"] = "application/json"

            # 4. 加入 Grounding (Google Search)
            # 對應官方 SDK: tools=[types.Tool(google_search=types.GoogleSearch())]
            if enable_grounding:
                payload["tools"] = [
                    {
                        "googleSearch": {}  # 注意：這裡是 googleSearch (駝峰式)，值為空物件即可
                    }
                ]

            return url, headers, payload
            
        raise ValueError(f"Unsupported external provider: {provider}")

    async def stream_external_api(self, session: httpx.AsyncClient, model_info: Dict, messages: List[Dict]):
        """流式調用 OpenAI GPT-4o-mini，逐段推送 delta。
        
        為了支持成本記錄，此方法返回一個包含：
        - 文本塊（通過 yield）
        - 最終響應對象（設置到 self._last_response_json）
        """
        provider = model_info.get("provider")
        if provider != "openai":
            raise ValueError(f"Streaming only supported for OpenAI, got {provider}")
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set.")
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model_info.get("id"),
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True}
            # "temperature": 0.7,
        }
        
        try:
            last_response_json = {}
            async with session.stream("POST", url, json=payload, headers=headers, timeout=300) as response:
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
                    response = await session.post(api_url, json=payload, headers=headers, timeout=300)
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
        """Pull citation/grounding URLs from provider payloads."""

        print(payload)
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

    async def generate_with_loaded_model(self, model: Any, tokenizer: Any, messages: List[Dict]) -> Tuple[Optional[str], Optional[Dict]]:
        try:
            prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)
            outputs = model.generate(
                **inputs, max_new_tokens=2048, do_sample=True, temperature=0.3,
                top_p=0.9, eos_token_id=tokenizer.eos_token_id
            )
            response_text = tokenizer.decode(outputs[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            return response_text, None
        except Exception as e:
            logger.error(f"Error during local model generation: {repr(e)}", exc_info=True)
            return None, {"error": "Failed to generate text with the local model."}

    # --- 3. 統一 Actor-Critic 流程 --- 
    async def _execute_generation_step(self, *, generation_func: GenerationFunc, messages: List[Dict], error_context: str, section_id_for_parsing: str) -> Tuple[Optional[Dict], Optional[str]]:
        """'呼叫->解析->回報錯誤' 的步驟"""
        raw_output, error = await generation_func(messages=messages)
        if error:
            return None, f"[{error_context}] Generation failed: {error.get('error', 'Unknown error')}"
        
        parsed_json, parsing_error = extract_json_block(raw_output, section_id_for_parsing)
        if parsing_error:
            return None, f"[{error_context}] Output parsing failed: {parsing_error.get('error', 'Unknown parsing error')}"
            
        return parsed_json, None

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
    ) -> tuple[Optional[bytes], Optional[str], Optional[Dict]]:
        """使用 Google Gemini API 呼叫圖片生成（imagen-4.0-generate-001）
        
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
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=contents
            )
            
            # 從生成結果中獲取圖像
            image_bytes = None
            for part in response.parts:
                print(part)
                if part.inline_data is not None:
                    image_bytes = part.inline_data.data
                    print(f"Generated image of size: {len(image_bytes)} bytes")
                    break
            
            if not image_bytes:
                return None, "No image generated", None
            
            # 構建響應 JSON 格式（用於成本記錄）
            response_json = {}
            try:
                if hasattr(response, 'usage_metadata'):
                    response_json = {
                        "usageMetadata": {
                            "promptTokenCount": response.usage_metadata.prompt_token_count,
                            "candidatesTokenCount": response.usage_metadata.candidates_token_count,
                        }
                    }
            except Exception as e:
                logger.warning(f"Failed to extract usage metadata: {e}")
            
            return image_bytes, None, response_json
                
        except Exception as e:
            error_msg = f"Failed to generate image: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg, None
    
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
    ) -> SectionGenerateResponse:
        
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
            provider = self._get_provider_for_model(selected_model)
            cost_info = self._get_model_cost_info(selected_model)
            original_model_info = {
                "id": selected_model,
                "provider": provider,
                "type": "external",
                "cost_info": cost_info
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
        if not disable_few_shot:
            few_shot_str = await self._format_few_shot_examples(
                user_input, section_details, supabase_service
            )

        user_content_parts = []
        if few_shot_str:
            user_content_parts.append(few_shot_str.strip())
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

        system_prompt_for_all = section_details.system_prompt + """

========== 內容生成指南 ==========
【圖片佔位符】若需要表示應插入圖片的位置，請使用 【圖：<圖片的簡單描述>】 的格式。例如：【圖：本公司研發之開片機實品操作展示照片】。

【數據/名稱佔位符】當遇到不確定的公司名稱、人名、或具體數據時，請統一使用 OOO 作為替代文字。

【內容質量要求】用戶的輸入若是無或是相關資料量不夠，可以自己發散思維來寫作內容，客觀内容可以用OOO代替。

【⚠️ 嚴格禁止】
❌ 不要從上面的範例中直接複製任何資料（人名、公司名、聯絡資訊、具體數據等）
❌ 不要生成空白或只有佔位符的內容
❌ 不要只複製範例的結構而不填充實際內容
✅ 必須生成有實質內容的、相關的、原創的文本
✅ 每個字段都應該包含有意義的信息（至少 30% 的字段需要有實質內容）

【內容驗證】生成完成後，檢查：
1. 是否所有重要字段都有內容（不是空白或只有 OOO）
2. 是否內容來自於用戶輸入和你的知識，而非複製範例
3. 是否內容邏輯清晰、相關性強
4. 如果無法確定資訊，使用 OOO 而非留空"""
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
            
            if llm_error:
                raise ValueError(f"LLM API call failed: {llm_error.get('error', 'Unknown error')}")
            
            # 嘗試直接解析 JSON
            parsed_json, parse_error = extract_json_block(raw_output, section_id)
            
            if parse_error:
                # 首先嘗試使用 LLM 修復 JSON
                logger.warning(f"Initial JSON parsing failed for {section_id}, attempting repair...")
                parsed_json, repair_error = await self._attempt_json_repair(
                    raw_output, http_session, model_to_use, section_id
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
            final_content_json, response_json = result
        
        # Log cost usage with response JSON that contains token counts
        if response_json and model_to_use.get('type') == 'external':
            try:
                await supabase_service.log_cost_usage(
                    user_id, model_to_use, response_json, 
                    project_id=project_id, 
                    action="生成企劃書章節"
                )
            except Exception as e:
                logger.warning(f"Failed to log cost usage: {e}")
                  
        # 4. --- 返回结果 ---
        if error_message:
            return SectionGenerateResponse(section_id=section_id, error=error_message)
        
        if not final_content_json:
            return SectionGenerateResponse(
                section_id=section_id, 
                error="Generation resulted in empty content."
            )
        
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


    # 先暫時不使用，未來有使用内部模型才使用

    #  async def _build_initial_actor_messages(self, user_input: str, section_details: SectionConfig, supabase_service: "SupabaseService") -> List[Dict]:
    #     """建立 Actor 首次生成時的 messages"""
    #     few_shot_str = await self._format_few_shot_examples(user_input, section_details, supabase_service )
    #     schema_str = json.dumps(section_details.json_schema, ensure_ascii=False)
    #     return [
    #         {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
    #         {"role": "user", "content": f"{few_shot_str}\n用户需求: {user_input}\n请一定要根据以下 JSON schema 生成内容:\n{schema_str}"}
    #     ]

    # def _build_critic_messages(self, user_input: str, section_details: SectionConfig, initial_answer: Dict) -> List[Dict]:
    #     """建立 Critic 評審時的 messages"""
    #     critic_prompt = section_details.critic_prompt.format(
    #         section_name=section_details.name,
    #         user_input=user_input,
    #         schema_json=json.dumps(section_details.json_schema, ensure_ascii=False),
    #         initial_answer_json=json.dumps(initial_answer, ensure_ascii=False)
    #     )
    #     return [{"role": "user", "content": critic_prompt}]

    # def _build_rewrite_messages(self, user_input: str, section_details: SectionConfig, initial_answer: Dict, critic_json: Dict) -> List[Dict]:
    #     """建立 Actor 重寫時的 messages"""
    #     rewrite_prompt = section_details.rewrite_prompt.format(
    #         section_name=section_details.name,
    #         user_input=user_input,
    #         schema_json=json.dumps(section_details.json_schema, ensure_ascii=False),
    #         initial_answer_json=json.dumps(initial_answer, ensure_ascii=False),
    #         critic_json=json.dumps(critic_json, ensure_ascii=False)
    #     )
    #     return [
    #         {"role": "system", "content": "You are a professional writer tasked with revising a draft based on feedback."},
    #         {"role": "user", "content": rewrite_prompt}
    #     ]
    
    
    # async def _run_actor_critic_workflow(
    #     self,
    #     http_session: httpx.AsyncClient,
    #     actor_func: GenerationFunc, 
    #     critic_model_info: Dict,
    #     section_details: SectionConfig,
    #     user_input: str,
    #     supabase_service: "SupabaseService"
    # ) -> Tuple[Optional[Dict], Optional[str]]:
    #     """actor_func 是一個可呼叫的對象，可以是本地生成函數，也可以是 API 呼叫函數。 """
    #     # --- Step 1: Actor generates initial answer ---
    #     logger.info("-> [Workflow] Step 1: Actor generating initial answer...")
    #     initial_messages = self._build_initial_actor_messages(user_input, section_details,supabase_service)
    #     initial_answer, error = await self._execute_generation_step(
    #         generation_func=actor_func,
    #         messages=initial_messages,
    #         error_context="Actor-Initial",
    #         section_id_for_parsing=section_details.id
    #     )
    #     if error: return None, error

    #     # --- Step 2: Critic reviews the answer ---
    #     logger.info(f"-> [Workflow] Step 2: Critic ({critic_model_info['id']}) reviewing...")
    #     critic_messages = self._build_critic_messages(user_input, section_details, initial_answer)
    #     critic_func = partial(self.call_external_api, http_session, critic_model_info)
    #     critic_json, error = await self._execute_generation_step(
    #         generation_func=critic_func,
    #         messages=critic_messages,
    #         error_context="Critic",
    #         section_id_for_parsing="critic"
    #     )
    #     if error: return None, error
        
    #     # --- Step 3: Actor rewrites based on critique ---
    #     logger.info("-> [Workflow] Step 3: Actor rewriting based on critique...")
    #     rewrite_messages = self._build_rewrite_messages(user_input, section_details, initial_answer, critic_json)
    #     final_answer, error = await self._execute_generation_step(
    #         generation_func=actor_func,
    #         messages=rewrite_messages,
    #         error_context="Actor-Rewrite",
    #         section_id_for_parsing=section_details.id
    #     )
    #     if error: return None, error

    #     return {
    #         "initial_answer": initial_answer,
    #         "critic_json": critic_json,
    #         "final_answer": final_answer
    #     }, None


      # # --- 4. 公開接口 ---
    # async def run_actor_critic_flow(self, http_session: httpx.AsyncClient, actor_model_bundle: Dict, critic_model_info: Dict, section_details: SectionConfig, user_input: str,supabase_service:"SupabaseService") -> Tuple[Optional[Dict], Optional[str]]:
    #     """執行 Actor-Critic 流程，Actor 使用加載的本地模型。"""
    #     # 使用 functools.partial 來固定 actor_func 的 model 和 tokenizer 參數
    #     actor_func = partial(self.generate_with_loaded_model, actor_model_bundle["model"], actor_model_bundle["tokenizer"])
    #     return await self._run_actor_critic_workflow(
    #         http_session=http_session,
    #         actor_func=actor_func,
    #         critic_model_info=critic_model_info,
    #         section_details=section_details,
    #         user_input=user_input,
    #         supabase_service=supabase_service
    #     )

    # async def run_actor_critic_flow_via_api(self, http_session: httpx.AsyncClient, actor_model_info: Dict, critic_model_info: Dict, section_details: SectionConfig, user_input: str,supabase_service:"SupabaseService") -> Tuple[Optional[Dict], Optional[str]]:
    #     """
    #     執行 Actor-Critic 流程，Actor 是通過 API (如 Ollama) 呼叫的。
    #     """
    #     # 使用 functools.partial 來固定 actor_func 的 session 和 model_info 參數
    #     actor_func = partial(self.call_external_api, http_session, actor_model_info)
    #     return await self._run_actor_critic_workflow(
    #         http_session=http_session,
    #         actor_func=actor_func,
    #         critic_model_info=critic_model_info,
    #         section_details=section_details,
    #         user_input=user_input,
    #         supabase_service=supabase_service
    #     ) 
    
    
    
    # async def generate_section_content(
    #     self,  
    #     http_session: httpx.AsyncClient, 
    #     grant_id: str, 
    #     template_id: str, 
    #     section_id: str, 
    #     user_input: str,
    #     app_state: Any,
    #     user_id: str,
    #     supabase_service: "SupabaseService",
    #     use_actor_critic: bool = False,
    #     is_external: Optional[bool] = None,
    #     selected_model: Optional[str] = None,
    #     project_id: Optional[str] = None,
    #     section_context: Optional[str] = None,
    #     disable_few_shot: bool = False,
    #     section_details_override: Optional[SectionConfig] = None,
    # ) -> SectionGenerateResponse:
        
    #     # 1. --- 获取配置 ---
    #     section_details = section_details_override or await supabase_service.get_section_details(
    #         grant_id,
    #         template_id,
    #         section_id,
    #     )
    #     if not section_details or not section_details.json_schema or not section_details.system_prompt:
    #         return SectionGenerateResponse(section_id=section_id, error="Configuration error for section.")

    #     section_grounding_enabled = bool(getattr(section_details, "search_external", False))

    #     # 2. --- 路由与配额检查 ---
    #     # 如果提供了 selected_model，直接创建该模型的 info 对象；否则使用原有的 resolve_model 逻辑
    #     if selected_model:
    #         # 根据 model_id 判断 provider
    #         provider = self._get_provider_for_model(selected_model)
    #         original_model_info = {
    #             "id": selected_model,
    #             "provider": provider,
    #             "type": "external"
    #         }
    #     else:
    #         original_model_info = resolve_model(grant_id, template_id, section_id, app_state, is_external=is_external)
        
    #     if not original_model_info:
    #         return SectionGenerateResponse(section_id=section_id, error="Model routing failed.")
        
    #     model_to_use = original_model_info
    #     model_type = model_to_use.get('type', 'internal')
    #     captured_external_sources: List[Dict[str, Any]] = []

    #     def capture_response_sources(payload: Dict[str, Any]):
    #         references = self._extract_external_sources(model_to_use.get("provider"), payload)
    #         if references:
    #             captured_external_sources.extend(references)

    #     # has_quota, reason = await supabase_service.check_quota(user_id, model_type)
        
    #     # 配额降级逻辑
    #     # if model_type == 'external' and not has_quota:
    #     #     print(f"   ⚠️ External quota exhausted for user {user_id}. Attempting downgrade.")
    #     #     internal_fallback = next((m for m in app_state.model_registry.values() if m['type'] == 'internal'), None)
            
    #     #     if internal_fallback:
    #     #         has_internal_quota, _ = await supabase_service.check_quota(user_id, 'internal')
    #     #         if has_internal_quota:
    #     #             print(f"   -> Downgrading to internal model: {internal_fallback['id']}")
    #     #             model_to_use = internal_fallback
    #     #             model_type = 'internal'
    #     #         else:
    #     #             return SectionGenerateResponse(section_id=section_id, error="All quotas (external and internal) exhausted.")
    #     #     else:
    #     #         return SectionGenerateResponse(section_id=section_id, error="External quota exhausted, no internal fallback available.")
    #     # elif not has_quota:
    #     #     return SectionGenerateResponse(section_id=section_id, error=reason)
        
    #     # 3. --- 根据模型类型选择生成流程 ---
    #     final_content_json = None; error_message = None
        
    #     if model_type == 'external':
    #         # --- 流程 A: 外部调用 ---
    #         logger.info(f"-> Using API generation with model: {model_to_use['id']}")
    #         enable_grounding = section_grounding_enabled and model_to_use.get("provider") in {"openai", "gemini"}

    #         few_shot_str = ""
    #         if not disable_few_shot:
    #             few_shot_str = await self._format_few_shot_examples(
    #                 user_input, section_details, supabase_service
    #             )

    #         user_content_parts = []
    #         if few_shot_str:
    #             user_content_parts.append(few_shot_str.strip())
    #         user_content_parts.append(f"用户需求: {user_input}")
    #         if section_context:
    #             user_content_parts.append(
    #                 "章節參考內容：\n" + section_context.strip()
    #             )
    #         user_content_parts.append(
    #             f"请根据以下 JSON schema 生成内容:\n{json.dumps(section_details.json_schema, ensure_ascii=False)}"
    #         )
    #         user_content = "\n\n".join(user_content_parts)
        

    #         # 檢查是否有自定義指令，並將它們附加到 user_content
    #         if section_details.custom_prompt_list:
    #             custom_prompts_str = "\n".join(f"- {p}" for p in section_details.custom_prompt_list)
    #             user_content += f"\n\n请额外遵循以下客製化指令：\n{custom_prompts_str}\n如果允許使用web search工具，請務必使用最新的網路資訊來補充回答內容。"

    #         system_prompt_for_all = section_details.system_prompt + "\n內容生成指南：\n圖片佔位符：若需要表示應插入圖片的位置，請使用 【圖：<圖片的簡單描述>】 的格式。例如：【圖：本公司研發之開片機實品操作展示照片】。\n數據/名稱佔位符：當遇到不確定的公司名稱、人名、或具體數據時，請統一使用 OOO 作為替代文字。\n用戶的輸入若是無或是相關資料量不夠，可以自己發散思維來寫作內容，客觀内容可以用OOO代替。"
    #         messages = [
    #             {"role": "system", "content": system_prompt_for_all},
    #             {"role": "user", "content": user_content} 
    #         ]

    #         response_hook = capture_response_sources if enable_grounding else None

    #         raw_output, llm_error = await self.call_external_api(
    #             http_session,
    #             model_to_use,
    #             messages,
    #             enable_grounding=enable_grounding,
    #             response_hook=response_hook,
    #         )
            
    #         if llm_error:
    #             error_message = llm_error.get("error")
    #         else:
    #             final_content_json, parse_error = extract_json_block(raw_output, section_id)
    #             # await supabase_service.log_cost_usage(user_id, model_to_use, messages, raw_output)
    #             if parse_error:
    #                 error_message = parse_error.get("error")
    #             else:
    #                 full_prompt = f"User Input: {user_input}\nSystem Prompt: {section_details.system_prompt}"
                  
    #     elif model_type == 'internal':
    #         if use_actor_critic:
    #             # 使用完整的 Actor-Critic 工作流
    #             critic_model_info = app_state.model_registry.get("gpt-4-turbo")
    #             if not critic_model_info:
    #                 return SectionGenerateResponse(section_id=section_id, error="Critic model 'gpt-4-turbo' not found.")
                
    #             ac_data, ac_error = await self.run_actor_critic_flow_via_api(
    #                 http_session=http_session,
    #                 actor_model_info=model_to_use, 
    #                 critic_model_info=critic_model_info,
    #                 section_details=section_details,
    #                 user_input=user_input,
    #                 supabase_service=supabase_service
    #             )
                
    #             if ac_error:
    #                 error_message = ac_error
    #             else:
    #                 final_content_json = ac_data["final_answer"]
    #                 actor_initial_len = len(json.dumps(ac_data["initial_answer"]))
    #                 critic_len = len(json.dumps(ac_data["critic_json"]))
    #                 actor_final_len = len(json.dumps(ac_data["final_answer"]))
                    
    #                 # 记录 Actor 的总用量
    #                 actor_tokens = (actor_initial_len + actor_final_len) // 2
    #                 asyncio.create_task(supabase_service.log_usage(user_id, model_to_use,actor_tokens, actor_tokens))
                    
    #                 # 记录 Critic 的用量
    #                 critic_tokens = critic_len // 2
    #                 asyncio.create_task(supabase_service.log_usage(user_id, critic_model_info, critic_tokens, critic_tokens))
        
    #                 # 异步记录完整的 Actor-Critic 微调数据
    #                 print("   - Scheduling background task to log Actor-Critic run...")
    #                 full_prompt = f"User Input: {user_input}\nSystem Prompt: {section_details.system_prompt}"
    #                 asyncio.create_task(
    #                     supabase_service.log_actor_critic_run(
    #                         grant_id=grant_id,
    #                         template_id=template_id,
    #                         section_id=section_id,
    #                         prompt=full_prompt,
    #                         initial_answer=ac_data["initial_answer"],
    #                         critic_json=ac_data["critic_json"],
    #                         final_answer=ac_data["final_answer"]
    #                     )
    #                 )
    #         else:
    #             # 仅使用 Actor，跳过 Critic - 更快地生成多个 sections
    #             logger.info(f"-> Using fast Actor-only generation for section: {section_id}")
    #             few_shot_str = ""
    #             if not disable_few_shot:
    #                 few_shot_str = await self._format_few_shot_examples(
    #                     user_input, section_details, supabase_service
    #                 )

    #             user_content_parts = []
    #             if few_shot_str:
    #                 user_content_parts.append(few_shot_str.strip())
    #             user_content_parts.append(f"用户需求: {user_input}")
    #             if section_context:
    #                 user_content_parts.append(
    #                     "章節參考內容：\n" + section_context.strip()
    #                 )
    #             user_content_parts.append(
    #                 f"请根据以下 JSON schema 生成内容:\n{json.dumps(section_details.json_schema, ensure_ascii=False)}"
    #             )
    #             user_content = "\n\n".join(user_content_parts)
            
    #             # 檢查是否有自定義指令，並將它們附加到 user_content
    #             if section_details.custom_prompt_list:
    #                 custom_prompts_str = "\n".join(f"- {p}" for p in section_details.custom_prompt_list)
    #                 user_content += f"\n\n请额外遵循以下客製化指令：\n{custom_prompts_str}"

    #             system_prompt_for_all = section_details.system_prompt + "\n內容生成指南：\n圖片佔位符：若需要表示應插入圖片的位置，請使用 【圖：<圖片的簡單描述>】 的格式。例如：【圖：本公司研發之開片機實品操作展示照片】。\n數據/名稱佔位符：當遇到不確定的公司名稱、人名、或具體數據時，請統一使用 OOO 作為替代文字。"
    #             messages = [
    #                 {"role": "system", "content": system_prompt_for_all},
    #                 {"role": "user", "content": user_content} 
    #             ]

    #             enable_grounding = section_grounding_enabled and model_to_use.get("provider") in {"openai", "gemini"}

    #             response_hook = capture_response_sources if enable_grounding else None

    #             raw_output, llm_error = await self.call_external_api(
    #                 http_session,
    #                 model_to_use,
    #                 messages,
    #                 enable_grounding=enable_grounding,
    #                 response_hook=response_hook,
    #             )
                
    #             if llm_error:
    #                 error_message = llm_error.get("error")
    #             else:
    #                 final_content_json, parse_error = extract_json_block(raw_output, section_id)
    #                 await supabase_service.log_cost_usage(user_id, model_to_use, messages, raw_output)
    #                 if parse_error:
    #                     error_message = parse_error.get("error")

    #     # 4. --- 返回结果 ---
    #     if error_message: return SectionGenerateResponse(section_id=section_id, error=error_message)
    #     if not final_content_json: return SectionGenerateResponse(section_id=section_id, error="Generation resulted in empty content.")
        
    #     formatted_content = format_section_output(final_content_json, section_details.json_schema)

    #     if project_id:
    #         try:
    #             await supabase_service.log_execution_event(
    #                 project_id=project_id,
    #                 user_id=user_id,
    #                 event_type="section_generated",
    #                 section_id=section_id,
    #                 external_sources=captured_external_sources or None,
    #                 payload={
    #                     "model_id": model_to_use.get("id"),
    #                     "model_type": model_type,
    #                     "mode": "actor_critic" if use_actor_critic else "single_pass",
    #                 },
    #             )
    #         except Exception:
    #             logger.warning("Failed to log section_generated event", exc_info=True)
    #     return SectionGenerateResponse(section_id=section_id, content=formatted_content,raw_json_content=final_content_json)
