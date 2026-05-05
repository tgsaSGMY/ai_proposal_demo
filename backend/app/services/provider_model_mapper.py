# 用途：把我們內部 models.id (gpt-5-mini, gemini-3-pro-preview ...) 翻譯成
# 母平台 /api/engine-usage/report 期待的 (model_provider, model_name) 組合。
#
# 母平台 model_provider 允許值（依 doc 2026-04-30）：
#   openai / google / anthropic / azure_openai / meta / mistral / cohere /
#   xai / deepseek / local / other
#
# model_name 是 free-form (≤120 字)；我們直接傳我們的內部 id，這樣 mother 的
# 後台 dashboard 也看得到實際模型版本。

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# 母平台允許的 provider enum（依官方 API 文件）。
ALLOWED_PROVIDERS = {
    "openai",
    "google",
    "anthropic",
    "azure_openai",
    "meta",
    "mistral",
    "cohere",
    "xai",
    "deepseek",
    "local",
    "other",
}


@dataclass(frozen=True)
class ProviderModel:
    provider: str
    name: str


def _normalize_internal_provider(raw: Optional[str]) -> str:
    """把我們 models.provider 欄位的值正規化成母平台 enum。"""
    if not raw:
        return "other"
    val = raw.strip().lower()
    # 我們內部會出現的值：openai / google / gemini / ollama / anthropic / claude / 等等。
    if val in ALLOWED_PROVIDERS:
        return val
    if val in {"gemini", "google_gemini", "google-gemini"}:
        return "google"
    if val in {"claude"}:
        return "anthropic"
    if val in {"ollama"}:
        return "local"
    if val.startswith("azure"):
        return "azure_openai"
    return "other"


def _provider_from_model_id(model_id: str) -> str:
    """從 model_id 字串猜 provider，作為 cost_info 沒填 provider 時的 fallback。"""
    mid = (model_id or "").lower()
    if not mid:
        return "other"
    if mid.startswith("gpt") or mid.startswith("o1") or mid.startswith("o3") or mid.startswith("o4"):
        return "openai"
    if "gemini" in mid or mid.startswith("imagen"):
        return "google"
    if "claude" in mid:
        return "anthropic"
    if "llama" in mid:
        return "meta"
    if "mistral" in mid or "mixtral" in mid:
        return "mistral"
    if "cohere" in mid or "command" in mid:
        return "cohere"
    if "grok" in mid:
        return "xai"
    if "deepseek" in mid:
        return "deepseek"
    if "ollama" in mid:
        return "local"
    return "other"


def map_to_mother_provider_model(model_info: Dict[str, Any]) -> ProviderModel:
    """
    把 supabase_service.log_usage 拿到的 model_info dict，轉成 mother 期待的
    provider+model_name pair。

    model_info 預期含：id (text), provider (text, optional), type (text)。
    若兩種都判不出來，fallback 'other' / 'unknown'。
    """
    raw_id = str(model_info.get("id") or "").strip()
    raw_provider = model_info.get("provider")

    provider = _normalize_internal_provider(raw_provider) if raw_provider else _provider_from_model_id(raw_id)
    if provider not in ALLOWED_PROVIDERS:
        logger.debug("Provider %s not in allowed enum, defaulting to 'other'", provider)
        provider = "other"

    # model_name 直接用我們內部 id；mother 會原樣存。截到 120 字以防超界。
    name = (raw_id or "unknown")[:120]

    return ProviderModel(provider=provider, name=name)
