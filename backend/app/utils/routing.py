from typing import Dict, Any, Optional
from app.config import DEFAULT_MODEL_ID
import logging

logger = logging.getLogger(__name__)

def resolve_model(grant_id: str, template_id: str, section_id: str, app_state: Any, is_external: Optional[bool] = None) -> Optional[Dict[str, Any]]:
    """寻找路由模型"""
    logger.debug(
        "Resolving model for grant '%s', template '%s', section '%s', is_external=%s",
        grant_id,
        template_id,
        section_id,
        is_external,
    )
    # 路由规则已经按优先级排序
    for rule in app_state.routing_rules:
        grant_match = (rule['grant_id'] is None or rule['grant_id'] == grant_id)
        template_match = (rule.get('template_id') is None or rule['template_id'] == template_id)
        section_match = (rule['section_id'] is None or rule['section_id'] == section_id)
        external_match = (is_external is None or rule.get('is_external') == is_external)
        
        if grant_match and template_match and section_match and external_match:
            model_id = rule["model_id"]
            model_info = app_state.model_registry.get(model_id)
            if model_info:
                logger.info(
                    "Routing '%s/%s/%s' (is_external=%s) to model: %s (Priority: %s)",
                    grant_id,
                    template_id,
                    section_id,
                    is_external,
                    model_id,
                    rule['priority'],
                )
                return model_info
            else:
                logger.warning(f"Routing rule points to a non-existent model '{model_id}'.")
    
    # 如果没有规则匹配，使用默认模型
    default_model_info = app_state.model_registry.get(DEFAULT_MODEL_ID)
    if default_model_info:
        logger.info(
            "No matching rule for %s/%s/%s (is_external=%s), falling back to default model: %s",
            grant_id,
            template_id,
            section_id,
            is_external,
            DEFAULT_MODEL_ID,
        )
        return default_model_info
    
    logger.error(f"Default model '{DEFAULT_MODEL_ID}' not found in registry.")
    return None