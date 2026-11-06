# 用途：將範本對應的動態章節/欄位定義，攤平為 WS 題目控制流程使用的問題清單。
#
# Demo port of the platform's question_loader_service. The platform resolves
# the template through a projects row; the demo has no projects, so callers
# pass the demo session's grant_id / template_id directly. The output format
# is identical to the platform's so question_logic / export_readiness work
# unchanged.
import logging
from typing import Any, Dict, List, Optional

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


async def load_template_questions(
	grant_id: Optional[str],
	template_id: Optional[str],
	supabase_service: SupabaseService,
) -> List[Dict[str, Any]]:
	"""grant_id + template_id -> dynamic schema -> flattened question list.

	Each item: {id, label, prompt_text, skip_condition, skip_output_text, truth_level}.
	id/label/prompt_text match the client's composite-key format
	(frontend/utils/dynamicSchema.ts: `${sectionId}::${propertyKey}`, label
	`${sectionName}｜${title}`), so the DB-driven and client-supplied lists
	line up 1:1.

	Returns [] when no template is set or on any lookup failure — callers
	should fall back to the client-supplied question list.
	"""
	if not template_id or not grant_id:
		return []

	try:
		sections = await supabase_service.get_dynamic_fields_for_template(template_id, grant_id)
	except Exception as e:
		logger.error(
			"load_template_questions: failed to fetch dynamic schema for %s/%s: %s",
			grant_id, template_id, e, exc_info=True,
		)
		return []

	questions: List[Dict[str, Any]] = []
	for section in sections or []:
		section_key = section.get("section_key")
		section_title = section.get("title") or ""
		for field in section.get("fields") or []:
			field_key = field.get("field_key")
			if not section_key or not field_key:
				continue
			title = field.get("title") or ""
			description = (field.get("description") or "").strip()
			prompt_text = f"{title}\n{description}".strip() if description else title
			questions.append(
				{
					"id": f"{section_key}::{field_key}",
					"label": f"{section_title}｜{title}",
					"prompt_text": prompt_text,
					"skip_condition": field.get("skip_condition"),
					"skip_output_text": field.get("skip_output_text"),
					"truth_level": field.get("truth_level"),
				}
			)
	return questions
