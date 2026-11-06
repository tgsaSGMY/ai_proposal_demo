"""
功能模型配置：決定章節以外的每個 AI 功能使用哪個模型。

設定存在 feature_model_settings 資料表（啟動 / 刷新配置時載入到 app_state.feature_model_settings）。
每一列是一個明確的選擇；沒有列時使用「預設模型」（feature_key='_default'），
再沒有時使用程式原本寫死的模型，因此資料表為空時所有功能的行為與以前相同。
"""

import logging
from typing import Any, Dict, List, Optional

from app.config import IMAGE_MODEL
from app.utils.model_helper import get_default_model, normalize_provider

logger = logging.getLogger(__name__)

DEFAULT_FEATURE_KEY = "_default"

# requirement:
#   text             任何文字模型（非圖片模型）
#   cloud_text       OpenAI 或 Gemini 文字模型（JSON 修復只會呼叫這兩家）
#   openai           只限 OpenAI（程式直接呼叫 OpenAI API）
#   openai_streaming 只限支援串流的 OpenAI 模型
#   image            Gemini 圖片生成模型
# follows_sections: 沒有設定時跟隨計畫書章節的模型，不使用預設模型
# internal_only:    只有內部人員會用到，一律使用內部模型設定
FEATURES: Dict[str, Dict[str, Any]] = {
    "chat_guidance": {"requirement": "openai_streaming", "fallback_model_id": "chat-latest"},
    "recommend_names": {"requirement": "text", "fallback_model_id": "gemini-3.1-flash-lite"},
    "fact_tense": {"requirement": "text", "follows_sections": True},
    "existing_targets": {"requirement": "text", "follows_sections": True},
    "json_repair": {"requirement": "cloud_text", "follows_sections": True},
    "autofill_document": {"requirement": "text", "fallback_model_id": "chat-latest"},
    "plan_review_analyze": {"requirement": "text", "fallback_model_id": "chat-latest"},
    "plan_review_consistency": {"requirement": "text", "fallback_model_id": "chat-latest"},
    "field_file_analysis": {"requirement": "openai", "fallback_model_id": "chat-latest"},
    "image_ocr": {"requirement": "openai", "fallback_model_id": "chat-latest"},
    "enrich_image_prompt": {"requirement": "text", "fallback_model_id": "chat-latest"},
    "image_generation": {"requirement": "image", "fallback_model_id": IMAGE_MODEL},
    "section_recommender": {"requirement": "text", "fallback_model_id": "chat-latest", "internal_only": True},
    "sensitive_terms": {"requirement": "text", "fallback_model_id": "chat-latest", "internal_only": True},
    "synthetic_input": {"requirement": "text", "fallback_model_id": "chat-latest", "internal_only": True},
    "batch_synthetic_input": {"requirement": "text", "fallback_model_id": "chat-latest", "internal_only": True},
}


def model_fits(model: Optional[Dict[str, Any]], requirement: str) -> bool:
    """判斷模型能否用於某種需求。"""
    if not model:
        return False
    provider = normalize_provider(model.get("provider"))
    capabilities = model.get("capabilities") or {}
    is_image_model = bool(capabilities.get("supports_image_generation"))

    if requirement == "image":
        return provider == "gemini" and is_image_model
    if is_image_model:
        return False
    if requirement == "text":
        return True
    if requirement == "cloud_text":
        return provider in {"openai", "gemini"}
    if requirement == "openai":
        return provider == "openai"
    if requirement == "openai_streaming":
        return provider == "openai" and capabilities.get("supports_streaming", True) is not False
    return False


def _setting(app_state: Any, feature_key: str, is_external: bool) -> Optional[str]:
    for row in getattr(app_state, "feature_model_settings", None) or []:
        if row.get("feature_key") == feature_key and bool(row.get("is_external")) == is_external:
            return row.get("model_id")
    return None


def _fitting_model(app_state: Any, model_id: Optional[str], requirement: str, label: str) -> Optional[Dict[str, Any]]:
    if not model_id:
        return None
    registry = getattr(app_state, "model_registry", {}) or {}
    model = registry.get(model_id)
    if model_fits(model, requirement):
        return model
    logger.warning(f"[FeatureModel] {label}: model '{model_id}' is missing or unsuitable ({requirement}); ignoring it.")
    return None


def get_feature_override(app_state: Any, feature_key: str, is_external: Optional[bool]) -> Optional[Dict[str, Any]]:
    """只回傳該功能明確選擇的模型；沒有選擇（或不適用）時回傳 None。用於跟隨章節模型的功能。"""
    feature = FEATURES[feature_key]
    side = False if feature.get("internal_only") else (True if is_external is None else bool(is_external))
    model_id = _setting(app_state, feature_key, side)
    return _fitting_model(app_state, model_id, feature["requirement"], feature_key)


def get_feature_model(app_state: Any, feature_key: str, is_external: bool) -> Optional[Dict[str, Any]]:
    """
    依序取用：功能的設定 → 預設模型 → 程式原本使用的模型。
    不適用於該功能的模型會被略過。圖片功能找不到圖片模型時回傳 None，由呼叫端使用 IMAGE_MODEL。
    """
    feature = FEATURES[feature_key]
    requirement = feature["requirement"]
    side = False if feature.get("internal_only") else bool(is_external)

    model = _fitting_model(app_state, _setting(app_state, feature_key, side), requirement, feature_key)
    if model:
        return model

    default_id = _setting(app_state, DEFAULT_FEATURE_KEY, side)
    if default_id:
        registry = getattr(app_state, "model_registry", {}) or {}
        default_model = registry.get(default_id)
        if model_fits(default_model, requirement):
            return default_model

    fallback_id = feature.get("fallback_model_id")
    registry = getattr(app_state, "model_registry", {}) or {}
    if fallback_id in registry:
        return registry[fallback_id]
    if requirement == "image":
        return None
    return get_default_model(app_state, fallback_id)


def describe_features(app_state: Any) -> Dict[str, Any]:
    """提供給功能模型配置頁面的資料：每個功能可選的模型、原本的模型與目前的設定。"""
    registry = getattr(app_state, "model_registry", {}) or {}
    features: List[Dict[str, Any]] = []
    for key, feature in FEATURES.items():
        requirement = feature["requirement"]
        # 原本的模型不在模型清單時，回報實際會改用的模型（圖片功能直接使用 IMAGE_MODEL）
        fallback_id = feature.get("fallback_model_id")
        if fallback_id and fallback_id not in registry and requirement != "image":
            fallback_id = (get_default_model(app_state, fallback_id) or {}).get("id")
        features.append({
            "key": key,
            "internal_only": bool(feature.get("internal_only")),
            "follows_sections": bool(feature.get("follows_sections")),
            "fallback_model_id": fallback_id,
            "allowed_model_ids": [mid for mid, m in registry.items() if model_fits(m, requirement)],
        })
    return {
        "features": features,
        "default_allowed_model_ids": [mid for mid, m in registry.items() if model_fits(m, "text")],
        "settings": [
            {"feature_key": r.get("feature_key"), "is_external": bool(r.get("is_external")), "model_id": r.get("model_id")}
            for r in getattr(app_state, "feature_model_settings", None) or []
        ],
    }
