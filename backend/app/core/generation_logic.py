import json
import httpx
import logging
from typing import Dict, Any, List
from fastapi import Request, HTTPException,Depends

from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService
from app.utils.extract_json import extract_json_block 
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal 
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)
 
class SyntheticInputRequest(BaseModel): 
    mode: str
    grant_name: str
    template_name: str
    user_id: str 
    section_name: Optional[str] = None
    json_output: Optional[Dict[str, Any]] = None
    dynamic_fields_schema: Optional[List[Dict[str, str]]] = None

async def internal_generate_synthetic_input(
    req: SyntheticInputRequest,
    request: Request,
    llm_service: LLMService,
    supabase_service: SupabaseService,
) -> Dict[str, Any]:
    """
    可重用的内部函数，用于生成合成的用户输入。
    """
    model_info = request.app.state.model_registry.get("gpt-4.1")
    if not model_info:
        raise HTTPException(status_code=500, detail="GPT-4.1 model not configured for synthetic generation.")

    prompt = ""
    if req.mode == 'random' and req.dynamic_fields_schema:
        field_labels = "\n".join([f"- {field['label']}" for field in req.dynamic_fields_schema])
        prompt = f"""
        你是一位嚴謹的商業策略專家，負責生成高品質的 AI 訓練資料。

        ### 任務說明
        1. 你需要**先構思一個與「{req.grant_name}」相關的新穎且具吸引力的商業／專案構想**。
        2. 然後，**僅根據你構思的這個點子**，依序回答下列所有問題。
        3. **所有問題都必須回答，不得遺漏、不得省略任何一題。**
        4. **問題的鍵名（key）必須與以下提供的文字完全相同，不得改寫、增刪、重新編號或重新命名。**

        ### 輸出格式（請嚴格遵守 JSON 結構）
        你必須回傳**單一有效 JSON 物件**，且前後不能有任何額外文字或註解。  
        結構如下（請完全照抄鍵名與層級）：
        ```json
        {{
            "main_idea": "<在此輸入你生成的核心專案構想（單段文字）>",
            "dynamic_fields": {{
                "<question_label_1>": "<針對問題 1 的詳細文字回答>",
                "<question_label_2>": "<針對問題 2 的詳細文字回答>",
                ...
            }}
        }}
        ```
        
        📚 背景資訊
        補助主題：{req.grant_name}

        📝 問題清單（這些是 dynamic_fields 的鍵名，請逐一完整回答）：
        {field_labels}
        """
    else:
        raise HTTPException(status_code=400, detail="This internal function currently only supports 'random' mode.")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        messages = [{"role": "user", "content": prompt}]
        raw_output, error = await llm_service.call_external_api(client, model_info, messages, is_json_output=True)

        if error:
            raise HTTPException(status_code=500, detail=error.get("error", "Failed to generate synthetic input."))
         
        response_json, parse_error = extract_json_block(raw_output, "synthetic_input")
        if parse_error:
            raise HTTPException(status_code=500, detail=f"Failed to parse LLM JSON output: {parse_error}")

        await supabase_service.log_cost_usage(req.user_id, model_info, messages, raw_output)

        return response_json