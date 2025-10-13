# app/utils/routing.py

from typing import Dict, Any, Optional
from app.config import DEFAULT_MODEL_ID
import logging

logger = logging.getLogger(__name__)

def resolve_model(grant_id: str, section_id: str, app_state: Any) -> Optional[Dict[str, Any]]:
    """寻找路由模型"""
    logger.debug(f"Resolving model for grant '{grant_id}', section '{section_id}'")
    # 路由规则已经按优先级排序
    for rule in app_state.routing_rules:
        grant_match = (rule['grant_id'] is None or rule['grant_id'] == grant_id)
        section_match = (rule['section_id'] is None or rule['section_id'] == section_id)
        
        if grant_match and section_match:
            model_id = rule["model_id"]
            model_info = app_state.model_registry.get(model_id)
            if model_info:
                logger.info(f"Routing '{grant_id}/{section_id}' to model: {model_id} (Priority: {rule['priority']})")
                return model_info
            else:
                logger.warning(f"Routing rule points to a non-existent model '{model_id}'.")
    
    # 如果没有规则匹配，使用默认模型
    default_model_info = app_state.model_registry.get(DEFAULT_MODEL_ID)
    if default_model_info:
        logger.info(f"No matching rule, falling back to default model: {DEFAULT_MODEL_ID}")
        return default_model_info
    
    logger.error(f"Default model '{DEFAULT_MODEL_ID}' not found in registry.")
    return None