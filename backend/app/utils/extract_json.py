from typing import Dict, Any, Tuple, Optional
import json

def extract_json_block(raw_content: str, section_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """从模型返回的字符串中，提取出合法的 JSON 对象"""

    if not raw_content:
        return None, {"section_id": section_id, "error": "LLM returned empty content."}
    
    try:
        data = json.loads(raw_content)
        return data, None
    except json.JSONDecodeError:
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if json_match:
            json_string = json_match.group(0)
            try:
                data = json.loads(json_string)
                return data, None
            except json.JSONDecodeError:
                error_msg = f"Extracted block is not valid JSON: {json_string[:200]}..."
                return None, {"section_id": section_id, "error": error_msg}
        else:
            error_msg = f"AI returned invalid content (no JSON block found): {raw_content[:200]}..."
            return None, {"section_id": section_id, "error": error_msg}
