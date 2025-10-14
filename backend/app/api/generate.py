# 使用ai生成内容功能的api

import asyncio
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request 
from fastapi.responses import JSONResponse
import logging
import json

from app.models import (
    GenerateRequest, SectionGenerateResponse, AutoFillRequest, SyntheticInputRequest
)
from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService
from .dependencies import get_llm_service, get_supabase_service
from app.utils.extract_json import extract_json_block  
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Generation"]
)

@router.post("/generate_plan")
async def generate_plan( 
    request_data: GenerateRequest,
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
):
    """主功能 -> 生成完整计划书，可生成多候选版本"""
    if not request_data.sections:
        raise HTTPException(status_code=400, detail="No sections provided to generate.")

    app_state = request.app.state
    num_candidates = getattr(request_data, "num_candidates", 1)

    async with httpx.AsyncClient() as client:
        # 每個 section 生成 num_candidates 個候選版本
        tasks = [
            llm_service.generate_section_content(
                http_session=client,
                grant_id=request_data.grant,
                template_id=request_data.template,
                section_id=s.section_id,
                user_input=request_data.user_input,
                app_state=app_state,
                user_id=request_data.user_id,
                supabase_service=supabase_service,
            )
            for s in request_data.sections
            for _ in range(num_candidates)
        ]
        results = await asyncio.gather(*tasks)

    # 組織輸出：每個 section_id -> [候選內容...]
    plan_content = {}
    for res in results:
        section_id = res.section_id
        if section_id not in plan_content:
            plan_content[section_id] = []
        plan_content[section_id].append(res.dict())

    return plan_content



@router.post("/generate_synthetic_input", response_model=Dict[str, Any])
async def generate_synthetic_input(
    req: SyntheticInputRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
):
    """根據模式生成用戶輸入，現在支持填充動態字段"""
    model_info = request.app.state.model_registry.get("gpt-4.1")
    if not model_info:
        raise HTTPException(status_code=500, detail="GPT-3.5 Turbo model not configured for synthetic generation.")

    prompt = ""
    if req.mode == 'random' and req.dynamic_fields_schema:
        # 這是核心的 prompt 升級
        field_labels = "\n".join([f"- {field.label}" for field in req.dynamic_fields_schema])
        
        prompt = f"""
        你是一位嚴謹的商業策略專家，負責生成高品質的 AI 訓練資料。

        ---

        ### 任務說明
        1. 你需要**先構思一個與「{req.grant_name}」相關的新穎且具吸引力的商業／專案構想**。
        2. 然後，**僅根據你構思的這個點子**，依序回答下列所有問題。
        3. **所有問題都必須回答，不得遺漏、不得省略任何一題。**
        4. **問題的鍵名（key）必須與以下提供的文字完全相同，不得改寫、增刪、重新編號或重新命名。**

        ---

        ### 關於「鍵名」的嚴格規則
        - 鍵名必須**完全一致**（包含標點符號、括號、數字、中文序號、空格）。
        - 不可自行添加或刪除任何編號（例如「（一）」「（二）」）。
        - 不可更改任何鍵名（例如「創新性說明」→「創新說明」會視為錯誤）。
        - 如果有 N 個問題，你的輸出中 **dynamic_fields 物件也必須包含 N 個鍵**，一題都不能少。

        ---

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
        
        📚 背景資訊
        補助主題：{req.grant_name}

        計畫書模板：{req.template_name}

        📝 問題清單（這些是 dynamic_fields 的鍵名，請逐一完整回答）：
        {field_labels}

        ⚠️ 請再次確認：

        你的回答必須包含所有上述問題的鍵名。

        鍵名不可被改動、不可新增或刪除。

        JSON 需可被標準 JSON parser 正確解析。

        若任一問題遺漏、鍵名變動或格式錯誤，任務即視為失敗。

        現在，請直接生成最終的 JSON。
        """
    elif req.mode == 'reverse' and req.json_output:
        # --- 核心修改：重寫 'reverse' 模式的 Prompt ---
        json_str = json.dumps(req.json_output, ensure_ascii=False, indent=2)
        
        prompt = f"""
        你是一位頂級的數據結構轉換與內容摘要專家。
        你的任務是根據一份詳細的、結構化的 JSON 輸入，完成兩件事：
        1.  為整個 JSON 內容生成一個簡潔的核心思想摘要 (`main_idea`)。
        2.  對 JSON 內的 `dynamic_fields` 部分進行結構保留式的值轉換與摘要。

        **轉換規則 (針對 `dynamic_fields`)：**
        1.  **保留結構**: 最終輸出的 `dynamic_fields` 必須保留與輸入完全相同的 key 和層級結構。絕不能新增、刪除或重命名任何 key。
        2.  **摘要 `string` 值**: 如果一個字段的值是字符串，請將其內容摘要成更簡潔的核心短語或句子。
        3.  **轉換 `array` 為 `string`**: 如果一個字段的值是數組 (Array)，無論數組內是字符串還是對象，你都必須將整個數組的內容總結成一段通順、連貫的描述性文字 (String)。
        4.  **保留其他類型**: 如果字段的值是數字 (Number)、布爾值 (Boolean) 或 `null`，請保持原樣。

        **最終輸出格式：**
        你的回應必須是一個單一且有效的 JSON 物件，其結構如下：
        ```json
        {{
            "main_idea": "<這裡是你生成的、對整體內容的核心思想摘要，約 30-50 字>",
            "dynamic_fields": {{
                // 這裡是你轉換和摘要後的內容，
                // 結構與輸入的 json_output 完全一致，
                // 但 string 值被摘要，array 值被轉換成了 string。
            }}
        }}
        ```

        ---
        **待處理的原始 JSON 輸入 (`json_output`)：**
        ```json
        {json_str}
        ```
        ---

        現在，請根據上述規則生成完整的 JSON 回應。不要包含任何額外的解釋或註釋。
        """

    else:
        raise HTTPException(status_code=400, detail="Invalid mode or missing required fields.")

    # 異步調用和返回邏輯現在是共享的
    async with httpx.AsyncClient() as client:
        messages = [{"role": "user", "content": prompt}]
        raw_output, error = await llm_service.call_external_api(client, model_info, messages, is_json_output=True)

        if error:
            raise HTTPException(status_code=500, detail=error.get("error", "Failed to generate input."))
         
        response_json, parse_error = extract_json_block(raw_output, "synthetic_input")
        if parse_error:
            raise HTTPException(status_code=500, detail=f"Failed to parse LLM JSON output: {parse_error}")

        # 確保返回的 dynamic_fields 是個對象，而不是字符串
        if req.mode == 'reverse' and isinstance(response_json.get("dynamic_fields"), dict):
            # 遍歷原始 json_output 的結構，確保返回的結構與之匹配
            original_structure = req.json_output
            returned_structure = response_json["dynamic_fields"]
            
            # 我們期望 returned_structure 的 key 集合是 original_structure 的 key 集合的子集或相等
            if not set(returned_structure.keys()).issubset(set(original_structure.keys())):
                logger.warning("AI may have returned an incorrect structure for dynamic_fields in reverse mode.")
            return response_json
        elif req.mode == 'reverse':
            # 如果 AI 返回的 dynamic_fields 不是一個字典，說明它沒有遵循指令
            raise HTTPException(status_code=500, detail="LLM failed to return a valid dictionary for 'dynamic_fields'.")

        return response_json
      
@router.post("/autofill_from_document", summary="從文檔自動填充計劃書內容")
async def autofill_from_document(
    request_data: AutoFillRequest,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service) 
):
    """
    接收文檔純文字和多個章節的 schema，
    調用強大的 LLM 來解析文本並填充成結構化的 JSON。
    """
    # 組合所有 schema，方便 LLM 一次性處理
    all_schemas_info = "\n\n".join(
        f"--- 章節 ID: {s.section_id} | 章節名稱: {s.section_name} ---\n"
        f"JSON Schema:\n{json.dumps(s.json_schema, ensure_ascii=False, indent=2)}"
        for s in request_data.sections
    )

    # 構建一個強有力的 System Prompt
    system_prompt = """
    你是一位頂級的數據提取與結構化專家。你的唯一任務是將一份非結構化的文檔，嚴格且精確地映射到多個預定義的 JSON 結構中。你必須像一個精密的機器一樣工作，只處理和轉換信息，絕不創造、解釋或添加任何原文不存在的內容。

    **核心指令與規則：**

    1.  **JSON Schema 絕對至上**: 
        - 你必須為輸入中提供的每一個 `section_id` 生成一個對應的 JSON 對象。
        - 生成的 JSON 必須**100%**符合該 `section_id` 對應的 JSON Schema 結構，包括字段名稱、數據類型（字符串、數字、數組、對象等）。

    2.  **內容來源的唯一性——忠於原文**:
        - 所有填充到 JSON 字段的值，都**必須**直接來源於提供的文檔原文。
        - **嚴禁**進行任何形式的摘要、重寫、擴寫或杜撰。直接複製粘貼相關文句是最佳策略。
        - 如果文檔中明確沒有提到某個字段的信息，該字段的值必須設為 `null` 或者一個空字符串 `""` (如果 schema 要求 string 類型)。

    3.  **結構化映射的順序性與完整性**:
        - 你必須按照文檔內容的自然順序，將信息依次映射到對應的 JSON 結構中。例如，文檔開頭的內容應優先填充到像 `company_overview` 這樣的早期章節，文檔末尾的內容應填充到像 `budget_plan` 這樣的後期章節。
        - 努力將文檔中的**所有**相關信息都填充進去，不要遺漏任何細節。對於較長的段落描述，直接將整段文字（包含換行符 `\n`）放入對應的字符串字段中。

    4.  **最終輸出格式的嚴格性**:
        - 你的最終輸出**必須**是一個單一的、格式正確的 JSON 對象。
        - 這個 JSON 對象的 `key` 必須是文檔中提供的 `section_id` (例如 `"company_overview"`, `"execution_plan"`)。
        - 這個 JSON 對象的 `value` 必須是與 `key` 對應的、已填充內容的 JSON 對象。
        - **絕不**在最終的 JSON 輸出之外添加任何解釋、註釋或額外文本。

    **示例輸出結構:**
    ```json
    {
        "company_overview": {
            "company_name": "從文檔中提取的公司名稱",
            "mission_statement": "從文檔中提取的使命宣言段落..."
        },
        "execution_plan": {
            "tasks": [
            {
                "task_name": "從文檔中提取的任務一",
                "description": "關於任務一的詳細描述..."
            }
            ],
            ...
        }
    }
    """

    # 構建 User Prompt
    user_prompt = f"""
    這是需要你處理的計劃書文檔全文：
    --- DOCUMENT START ---
    {request_data.document_text}
    --- DOCUMENT END ---

    這是你需要填充的目標 JSON 結構定義：
    {all_schemas_info}

    請根據以上文檔內容和結構定義，生成最終的 JSON 輸出。
    """

    model_registry = request.app.state.model_registry
    model_to_use = model_registry.get("gpt-3.5-turbo-1106") or model_registry.get("gpt-4.5-turbo")
    if not model_to_use:
        raise HTTPException(status_code=500, detail="A powerful model like GPT-4/3.5 is required for this feature.")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            raw_output, llm_error = await llm_service.call_external_api(
                client, 
                model_to_use, 
                messages,  
                is_json_output=True 
            )

        if llm_error:
            raise HTTPException(status_code=500, detail=f"LLM API Error: {llm_error}")

        # 解析返回的 JSON 字符串
        filled_data = json.loads(raw_output)
        formatted_result = {}
        for section_id, content in filled_data.items():
            formatted_result[section_id] = {"content": content}

        return formatted_result

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM did not return a valid JSON object.")
    except Exception as e:
        logger.error(f"Error during document auto-fill: {e}")
        raise HTTPException(status_code=500, detail=str(e))