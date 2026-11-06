"""
Model helper utilities for resolving models from the DB registry.

This module provides a single source of truth for model resolution,
replacing scattered hardcoded model_registry.get(...) calls across the API layer.
"""

import logging
from typing import Any, Dict, Optional

from app.config import DEFAULT_MODEL_ID

logger = logging.getLogger(__name__)


def normalize_provider(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return raw

    value = str(raw).strip().lower()
    if value == "gemini" or value.startswith("google"):
        return "gemini"
    if value == "openai":
        return "openai"
    if value == "ollama":
        return "ollama"
    return value


def get_default_model(app_state: Any, preferred_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Resolve a model from the DB-loaded model_registry with a fallback chain.

    Resolution order:
    1. preferred_id (if provided and exists in registry)
    2. DEFAULT_MODEL_ID from config
    3. First model in registry (last resort)

    Returns None if the registry is completely empty (should never happen in production).
    """
    registry = getattr(app_state, "model_registry", {}) or {}

    # 1. Preferred model
    if preferred_id and preferred_id in registry:
        return registry[preferred_id]

    # 2. Config default
    if DEFAULT_MODEL_ID in registry:
        return registry[DEFAULT_MODEL_ID]

    # 3. Last resort: any model in registry
    if registry:
        first = next(iter(registry.values()))
        logger.warning(
            f"Model lookup fallback: preferred={preferred_id} and default={DEFAULT_MODEL_ID} "
            f"not found in registry, using first available model ({first.get('id')})."
        )
        return first

    logger.error("Model registry is empty — no models available.")
    return None
