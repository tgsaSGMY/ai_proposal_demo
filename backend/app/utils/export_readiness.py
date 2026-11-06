from typing import Any, Dict, List

from app.models import StoredAnswerEntry
from app.utils.question_logic import compute_applicable_questions

_USER_SOURCES = ("user_input", "guided_derived")


def compute_export_readiness(
	questions: List[Dict[str, Any]],
	entries: Dict[str, StoredAnswerEntry],
	apply_skip_logic: bool = True,
) -> Dict[str, Any]:
	answers = {field_id: entry.value for field_id, entry in entries.items()}

	if questions:
		applicable = compute_applicable_questions(questions, answers) if apply_skip_logic else list(questions)
	else:
		applicable = [{"id": field_id, "label": field_id} for field_id in entries]

	user_filled = 0
	ai_generated = 0
	needs_review = 0
	system_estimate = 0
	unconfirmed = 0
	fields: List[Dict[str, Any]] = []

	for question in applicable:
		qid = question.get("id")
		entry = entries.get(qid)
		if entry is None or not entry.value.strip():
			continue

		if entry.source == "system_estimate":
			system_estimate += 1
			continue

		if entry.source == "ai_generated":
			ai_generated += 1
		elif entry.source in _USER_SOURCES:
			user_filled += 1

		if entry.needs_review:
			needs_review += 1

		if entry.source == "ai_generated" or entry.needs_review:
			if not entry.confirmed:
				unconfirmed += 1
			fields.append(
				{
					"id": qid,
					"label": question.get("label") or qid,
					"source": entry.source,
					"needs_review": entry.needs_review,
					"review_note": entry.review_note,
					"confirmed": entry.confirmed,
				}
			)

	return {
		"total_applicable": len(applicable),
		"user_filled": user_filled,
		"ai_generated": ai_generated,
		"needs_review": needs_review,
		"system_estimate": system_estimate,
		"unconfirmed": unconfirmed,
		"fields": fields,
	}
