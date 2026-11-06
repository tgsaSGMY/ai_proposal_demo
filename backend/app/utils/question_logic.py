# 用途：程式化題目控制的純函式（跳題邏輯、下一題計算、進度計算）。
# Phase 3 (Model-Robustness-Implementation-Handoff.md §6). No I/O, no DB calls —
# callers pass in already-fetched data so this module stays independently testable.
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Characters that end the "leading token" of an answer. The model tends to
# elaborate gate answers into sentences ("否，本專案無硬體開發需求。"), so
# eq/in also compare the first token rather than only the whole string.
_TOKEN_DELIMITERS = set("，,。.、；;：:！!？? \t\n")


def _leading_token(text: str) -> str:
	for i, ch in enumerate(text):
		if ch in _TOKEN_DELIMITERS:
			return text[:i]
	return text


def evaluate_skip_condition(condition: Optional[Dict[str, Any]], current_answers: Dict[str, Any]) -> bool:
	"""Evaluate one field's skip_condition against the current answers.

	Returns True when the field SHOULD be skipped. `condition` is the JSONB
	shape stored on `dynamic_fields.skip_condition`:
	{"depends_on": "<id>", "operator": "in|eq|not_empty", "values": [...]}.

	Operators: "eq" — answer equals values[0]; "in" — answer is one of
	values; "not_empty" — depends_on already has a non-blank answer.
	eq/in also match on the answer's leading token (text before the first
	punctuation/space), so "否，本專案無硬體開發需求。" matches "否" but
	"否認" does not.
	An unknown operator fails open (treated as no-skip) with a warning log,
	so a malformed condition can never silently hide a question.
	"""
	if not condition:
		return False

	depends_on = condition.get("depends_on")
	operator = condition.get("operator")
	values = condition.get("values") or []

	raw_answer = current_answers.get(depends_on)
	answer = raw_answer.strip() if isinstance(raw_answer, str) else raw_answer

	if operator == "not_empty":
		return bool(answer)
	if operator == "eq":
		target = str(values[0]).strip() if values else ""
		if answer == target:
			return True
		return isinstance(answer, str) and bool(target) and _leading_token(answer) == target
	if operator == "in":
		targets = {str(v).strip() for v in values}
		if answer in targets:
			return True
		return isinstance(answer, str) and _leading_token(answer) in (targets - {""})

	logger.warning(
		"evaluate_skip_condition: unknown operator '%s' for depends_on '%s' — treating as no-skip",
		operator, depends_on,
	)
	return False


def compute_applicable_questions(
	questions: List[Dict[str, Any]], current_answers: Dict[str, Any]
) -> List[Dict[str, Any]]:
	"""Return the subset of `questions` (same order) that should be asked,
	given `current_answers`.

	Fields are walked in order so a skip decision earlier in the list can
	feed later ones: when a field is rule-skipped, its `skip_output_text`
	(or "" if none) stands in as its answer for the rest of this pass, so a
	downstream skip_condition depending on it evaluates against that
	resolved value — this is what lets skip chains (A -> B -> C) work.
	"""
	working_answers = dict(current_answers)
	applicable: List[Dict[str, Any]] = []

	for q in questions:
		if evaluate_skip_condition(q.get("skip_condition"), working_answers):
			qid = q.get("id")
			if qid and not working_answers.get(qid):
				working_answers[qid] = q.get("skip_output_text") or ""
			continue
		applicable.append(q)

	return applicable


def _is_answered(question_id: Optional[str], current_answers: Dict[str, Any]) -> bool:
	answer = current_answers.get(question_id)
	if isinstance(answer, str):
		answer = answer.strip()
	return bool(answer)


def compute_next_question_id(
	applicable: List[Dict[str, Any]], current_answers: Dict[str, Any]
) -> Optional[str]:
	"""Id of the first applicable question with no answer yet; None once
	every applicable question has a non-blank answer."""
	for q in applicable:
		if not _is_answered(q.get("id"), current_answers):
			return q.get("id")
	return None


def compute_progress(
	applicable: List[Dict[str, Any]], current_answers: Dict[str, Any]
) -> Dict[str, int]:
	"""Exact answered/total/percent over the applicable question set.

	Counts non-blank answers directly, so an empty conversation reports
	0 answered (not the pre-Phase-3 `len(a_desc.splitlines())` bug, which
	counted the "（無）" placeholder line as 1 answered)."""
	total = len(applicable)
	answered = sum(1 for q in applicable if _is_answered(q.get("id"), current_answers))
	percent = round((answered / total) * 100) if total else 0
	return {"answered": answered, "total": total, "percent": percent}


def validate_skip_conditions(questions: List[Dict[str, Any]]) -> List[str]:
	"""Validate that every skip_condition.depends_on references an earlier
	question in the same flattened, globally-ordered list (no forward refs).

	`questions` items need at least: id (str, "section_key::field_key"),
	order (int, global sequential position), skip_condition (optional dict
	shaped {"depends_on": "<id>", "operator": "in|eq|not_empty", "values": [...]}).

	Returns a list of human-readable error strings; empty list = all valid.
	"""
	errors: List[str] = []
	order_by_id = {q["id"]: q.get("order") for q in questions}

	for q in questions:
		condition = q.get("skip_condition")
		if not condition:
			continue

		depends_on = condition.get("depends_on")
		if not depends_on:
			errors.append(f"skip_condition for '{q['id']}' is missing 'depends_on'")
			continue

		if depends_on not in order_by_id:
			errors.append(f"skip_condition for '{q['id']}' references unknown field '{depends_on}'")
			continue

		if depends_on == q["id"] or order_by_id[depends_on] >= q["order"]:
			errors.append(
				f"skip_condition for '{q['id']}' references '{depends_on}', "
				"which does not come before it (forward reference)"
			)

	return errors
