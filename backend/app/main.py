import datetime
import asyncio
import json
import httpx
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import DEFAULT_MODEL_ID
from app.models import (
    GenerateRequest, SectionGenerateResponse, GrantConfig, RoutingRule, SaveDatasetRequest, DatasetEntry,
    SyntheticInputRequest,UserInputGenRequest,DatasetUpdateRequest,UpdatePromptsRequest,AutoFillRequest
)
from app.services.supabase_service import SupabaseService
from app.services.qdrant_service import QdrantService
from app.services.llm_service import LLMService,extract_json_block
import logging

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 依赖注入的函数：提供 SupabaseService 实例
async def get_supabase_service(request: Request) -> SupabaseService:
    return request.app.state.supabase_service

# 依赖注入的函数：提供 QdrantService 实例
async def get_qdrant_service(request: Request) -> QdrantService:
    return request.app.state.qdrant_service

# 依赖注入的函数：提供 LLMService 实例
async def get_llm_service(request: Request) -> LLMService:
    return request.app.state.llm_service

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://ai-proposal-platform-v1-0.pages.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("正在加载服务器配置...")
    
    # 初始化服务
    app.state.supabase_service = SupabaseService()
    app.state.qdrant_service = QdrantService()
    app.state.llm_service = LLMService(app.state.qdrant_service)

    # 从 Supabase 加载所有配置
    app.state.model_registry = {m['id']: m for m in await app.state.supabase_service.get_all_models()}
    app.state.routing_rules = await app.state.supabase_service.get_all_routing_rules()
    app.state.all_grants_config = await app.state.supabase_service.get_all_grants_config()
   

    print("服务器配置加载完成。") 

def resolve_model(grant_id: str, section_id: str, app_state: Any) -> Optional[Dict[str, Any]]:
    """寻找路由模型"""
    # 路由规则已经按优先级排序
    for rule in app_state.routing_rules:
        grant_match = (rule['grant_id'] is None or rule['grant_id'] == grant_id)
        section_match = (rule['section_id'] is None or rule['section_id'] == section_id)
        
        if grant_match and section_match:
            model_id = rule["model_id"]
            model_info = app_state.model_registry.get(model_id)
            if model_info:
                print(f"Routing '{grant_id}/{section_id}' to model: {model_id} (Priority: {rule['priority']})")
                return model_info
            else:
                print(f"路由规则指向不存在的模型 '{model_id}'。")
    
    # 如果没有规则匹配，使用默认模型
    default_model_info = app_state.model_registry.get(DEFAULT_MODEL_ID)
    if default_model_info:
        print(f"   -> 无匹配规则，回退到默认模型: {DEFAULT_MODEL_ID}")
        return default_model_info
    
    print(f"错误: 默认模型 '{DEFAULT_MODEL_ID}' 不存在。")
    return None

    
def format_section_output(data: Dict[str, Any], json_schema: Dict[str, Any]) -> str:
    formatted_content = []
    
    # 使用 schema 的 properties 字段进行格式化
    if 'properties' in json_schema:
        for key, prop_info in json_schema['properties'].items():
            if key in data:
                title = prop_info.get('title', key.replace('_', ' ').title())
                description = prop_info.get('description', '')
                value = data[key]

                section_text = f"**{description if description else title}**\n"
                
                if isinstance(value, list):
                    list_text = []
                    item_schema_props = prop_info.get("items", {}).get("properties", {})
                    for i, item in enumerate(value, start=1):
                        if isinstance(item, dict):
                            item_lines = [f"{i}. {item.get('name', f'项目{i}')}".strip()]
                            for sub_key, sub_val in item.items():
                                if sub_key == "name": continue
                                sub_title = item_schema_props.get(sub_key, {}).get("description", sub_key)
                                item_lines.append(f"   - {sub_title}：{sub_val}")
                            list_text.append("\n".join(item_lines))
                        else:
                            list_text.append(f"{i}. {item}")
                    value_text = "\n".join(list_text)
                elif isinstance(value, dict):
                    value_text = "\n".join(f"- {k}：{v}" for k, v in value.items())
                else:
                    value_text = str(value)
                
                section_text += f"{value_text}\n"
                formatted_content.append(section_text)
    else:
        # 如果 schema 没有 properties 字段，则通用处理
        for key, value in data.items():
            title = key.replace('_', ' ').title()
            if isinstance(value, list):
                list_text = "\n".join(f"- {v}" for v in value)
                formatted_content.append(f"**{title}**\n{list_text}\n")
            else:
                formatted_content.append(f"**{title}**\n{value}\n")

    return "\n".join(formatted_content)

async def generate_single_section(
    http_session: httpx.AsyncClient, 
    grant_id: str, 
    template_id: str, 
    section_id: str, 
    user_input: str,
    app_state: Any,
    user_id: str,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
) -> SectionGenerateResponse:
    
    # 1. --- 获取配置 ---
    section_details = await supabase_service.get_section_details(grant_id, template_id, section_id)
    if not section_details or not section_details.json_schema or not section_details.system_prompt:
        return SectionGenerateResponse(section_id=section_id, error="Configuration error for section.")

    # 2. --- 路由与配额检查 ---
    original_model_info = resolve_model(grant_id, section_id, app_state)
    if not original_model_info:
        return SectionGenerateResponse(section_id=section_id, error="Model routing failed.")
    
    model_to_use = original_model_info
    model_type = model_to_use.get('type', 'internal')

    has_quota, reason = await supabase_service.check_quota(user_id, model_type)
    
    # 配额降级逻辑
    if model_type == 'external' and not has_quota:
        print(f"   ⚠️ External quota exhausted for user {user_id}. Attempting downgrade.")
        internal_fallback = next((m for m in app_state.model_registry.values() if m['type'] == 'internal'), None)
        
        if internal_fallback:
            has_internal_quota, _ = await supabase_service.check_quota(user_id, 'internal')
            if has_internal_quota:
                print(f"   -> Downgrading to internal model: {internal_fallback['id']}")
                model_to_use = internal_fallback
                model_type = 'internal'
            else:
                return SectionGenerateResponse(section_id=section_id, error="All quotas (external and internal) exhausted.")
        else:
            return SectionGenerateResponse(section_id=section_id, error="External quota exhausted, no internal fallback available.")
    elif not has_quota:
        return SectionGenerateResponse(section_id=section_id, error=reason)
    
    # 3. --- 根据模型类型选择生成流程 ---
    final_content_json = None; error_message = None
    
    if model_type == 'external':
        # --- 流程 A: 外部或基础 Ollama API 调用 ---
        logger.info(f"-> Using API generation with model: {model_to_use['id']}")

        exemplars = llm_service.qdrant_service.retrieve_exemplars(f"{user_input} {section_details.name}")
        few_shot_str = llm_service._format_few_shot_examples(exemplars)
        user_content = f"{few_shot_str}\n用户需求: {user_input}\n请根据以下 JSON schema 生成内容:\n{json.dumps(section_details.json_schema, ensure_ascii=False)}"
    
        # 檢查是否有自定義指令，並將它們附加到 user_content
        if section_details.custom_prompt_list:
            custom_prompts_str = "\n".join(f"- {p}" for p in section_details.custom_prompt_list)
            user_content += f"\n\n请额外遵循以下客製化指令：\n{custom_prompts_str}"

        messages = [
        {"role": "system", "content": section_details.system_prompt},
        {"role": "user", "content": user_content} 
        ]

        raw_output, llm_error = await llm_service.call_external_api(http_session, model_to_use, messages)
        
        if llm_error:
            error_message = llm_error.get("error")
        else:
            final_content_json, parse_error = extract_json_block(raw_output, section_id)
            if parse_error:
                error_message = parse_error.get("error")
            else:
                asyncio.create_task(supabase_service.log_usage(user_id, model_to_use, len(raw_output) // 2))
                full_prompt = f"User Input: {user_input}\nSystem Prompt: {section_details.system_prompt}"
                # asyncio.create_task(
                #     supabase_service.log_sft_data_point(
                #         grant_id=grant_id,
                #         template_id=template_id,
                #         section_id=section_id,
                #         prompt=full_prompt,
                #         final_answer=final_content_json,
                #         source_type='external_direct' 
                #     )
                # )

    elif model_type == 'internal': 
        critic_model_info = app_state.model_registry.get("gpt-4-turbo")
        if not critic_model_info:
            return SectionGenerateResponse(section_id=section_id, error="Critic model 'gpt-4-turbo' not found.")
        
        ac_data, ac_error = await llm_service.run_actor_critic_flow_via_api(
            http_session=http_session,
            actor_model_info=model_to_use, 
            critic_model_info=critic_model_info,
            section_details=section_details,
            user_input=user_input
        )
        # --- 流程 B: 所有 INTERNAL 模型都走 Actor-Critic (DPO 数据收集) ---
        # provider = model_to_use.get("provider")
        # logger.info(f"-> Starting Actor-Critic flow for INTERNAL model: {model_to_use['id']} (Provider: {provider})")

        # critic_model_info = app_state.model_registry.get("gpt-4-turbo")
        # if not critic_model_info:
        #     return SectionGenerateResponse(section_id=section_id, error="Critic model 'gpt-4-turbo' not found.")

        # finetuned_lora_info = await supabase_service.find_latest_finetuned_model_for_section(section_id)
        # if finetuned_lora_info:
        #     logger.info(f"   -> Upgrading to fine-tuned LoRA model: {finetuned_lora_info['id']}")
        #     model_to_use = finetuned_lora_info
        #     provider = 'internal_lora'
        # else:
        #     logger.info(f"   -> Using base internal model as fallback: {model_to_use['id']}")

        # # Actor 的执行方式根据 provider 决定
        # if provider == 'internal_lora':
        #     # --- 分支 B1: Actor 是已加载的 LoRA 模型 ---
        #     actor_model_bundle = model_manager.get_lora_model(model_to_use)
        #     if not actor_model_bundle:
        #         return SectionGenerateResponse(section_id=section_id, error=f"Failed to load LoRA model '{model_to_use['id']}'.")
            
        #     # 使用加载的模型执行 A-C 流程
        #     ac_data, ac_error = await llm_service.run_actor_critic_flow(
        #         http_session=http_session,
        #         actor_model_bundle=actor_model_bundle, 
        #         critic_model_info=critic_model_info,
        #         section_details=section_details,
        #         user_input=user_input
        #     )
        #     print("already done actor critic flow")

        # elif provider == 'ollama':
        #     # --- 分支 B2: Actor 是通过 Ollama API 调用的基础模型 ---
        #     ac_data, ac_error = await llm_service.run_actor_critic_flow_via_api(
        #         http_session=http_session,
        #         actor_model_info=model_to_use, 
        #         critic_model_info=critic_model_info,
        #         section_details=section_details,
        #         user_input=user_input
        #     )
        
        # else:
        #     return SectionGenerateResponse(section_id=section_id, error=f"Unsupported provider for internal model: {provider}")
        
        if ac_error:
            error_message = ac_error
        else:
            final_content_json = ac_data["final_answer"]
            actor_initial_len = len(json.dumps(ac_data["initial_answer"]))
            critic_len = len(json.dumps(ac_data["critic_json"]))
            actor_final_len = len(json.dumps(ac_data["final_answer"]))
            
            # 记录 Actor 的总用量
            actor_tokens = (actor_initial_len + actor_final_len) // 2
            asyncio.create_task(supabase_service.log_usage(user_id, model_to_use, actor_tokens))
            
            # 记录 Critic 的用量
            critic_tokens = critic_len // 2
            asyncio.create_task(supabase_service.log_usage(user_id, critic_model_info, critic_tokens))

            # 异步记录完整的 Actor-Critic 微调数据
            print("   - Scheduling background task to log Actor-Critic run...")
            full_prompt = f"User Input: {user_input}\nSystem Prompt: {section_details.system_prompt}"
            asyncio.create_task(
                supabase_service.log_actor_critic_run(
                    grant_id=grant_id,
                    template_id=template_id,
                    section_id=section_id,
                    prompt=full_prompt,
                    initial_answer=ac_data["initial_answer"],
                    critic_json=ac_data["critic_json"],
                    final_answer=ac_data["final_answer"]
                )
            )

  

    # 4. --- 返回结果 ---
    if error_message: return SectionGenerateResponse(section_id=section_id, error=error_message)
    if not final_content_json: return SectionGenerateResponse(section_id=section_id, error="Generation resulted in empty content.")
    
    formatted_content = format_section_output(final_content_json, section_details.json_schema)
    return SectionGenerateResponse(section_id=section_id, content=formatted_content,raw_json_content=final_content_json)



@app.get("/api/models", response_model=List[Dict[str, Any]])
async def get_all_models(request: Request):
    """獲取所有可用的模型列表"""
    return list(request.app.state.model_registry.values())

@app.get("/api/routing-rules", response_model=List[Dict[str, Any]])
async def get_all_routing_rules(request: Request):
    """獲取所有路由規則"""
    return request.app.state.routing_rules

@app.post("/api/routing-rules", response_model=Dict[str, Any])
async def set_routing_rule(
    rule: RoutingRule, # 使用 Pydantic 模型進行驗證
    supabase_service: SupabaseService = Depends(get_supabase_service),
    request: Request = None
):
    """新增或更新一個路由規則"""
    try:
        # 這裡需要一個 SupabaseService 的方法來處理 UPSERT
        # 假設我們在 SupabaseService 中添加一個名為 upsert_routing_rule 的方法
        new_rule_data = await supabase_service.upsert_routing_rule(rule)
        
        # 更新應用程式的實時狀態
        request.app.state.routing_rules = await supabase_service.get_all_routing_rules()
        
        return {"status": "success", "rule": new_rule_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config", response_model=List[GrantConfig])
async def get_all_configs_from_supabase(supabase_service: SupabaseService = Depends(get_supabase_service)):
    """
    从 Supabase 数据库加载所有 Grant、Template 和 Section 配置。
    """
    try:
        # startup 时加载 app.state config的数据
        return app.state.all_grants_config 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load configurations from Supabase: {e}")


@app.post("/api/generate_plan", response_model=Dict[str, SectionGenerateResponse])
async def generate_plan( 
    request: GenerateRequest,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
):
    """主功能->生成完整计划书"""
    if not request.sections:
        raise HTTPException(status_code=400, detail="No sections provided to generate.")

    async with httpx.AsyncClient() as client:
        tasks = [
            generate_single_section(
                user_id=request.user_id,
                http_session=client,
                grant_id=request.grant,
                template_id=request.template,
                section_id=s.section_id,
                user_input=request.user_input,
                supabase_service=supabase_service,
                llm_service=llm_service,
                app_state=app.state 
            )
            for s in request.sections
        ]
        results = await asyncio.gather(*tasks)
    
    plan_content = {res.section_id: res for res in results}
    
    return JSONResponse(content={k: v.dict() for k, v in plan_content.items()})

# @app.get("/api/datasets", response_model=List[Dict[str, Any]])
# async def get_datasets(supabase: SupabaseService = Depends(get_supabase_service)):
#     return await supabase.get_all_datasets()

# @app.delete("/api/datasets/{dataset_id}")
# async def delete_dataset(
#     dataset_id: int,
#     supabase: SupabaseService = Depends(get_supabase_service),
#     qdrant: QdrantService = Depends(get_qdrant_service)
# ):
#     success = await supabase.delete_dataset_by_id(dataset_id)
#     if not success:
#         # 這裡可以選擇性地返回 404，但即使記錄不存在，操作也算 "完成"
#         pass
    
#     # 無論數據庫中是否存在，都嘗試從 Qdrant 刪除
#     qdrant.delete_exemplar(dataset_id)
        
#     return {"status": "success", "deleted_id": dataset_id}

@app.post("/api/generate_synthetic_input", response_model=Dict[str, Any]) # <-- 返回類型改為 Dict[str, Any]
async def generate_synthetic_input(
    req: SyntheticInputRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    """根據模式生成用戶輸入，現在支持填充動態字段"""
    model_info = app.state.model_registry.get("gpt-4-turbo")
    if not model_info:
        raise HTTPException(status_code=500, detail="GPT-4 Turbo model not configured for synthetic generation.")

    prompt = ""
    if req.mode == 'random' and req.dynamic_fields_schema:
        # 這是核心的 prompt 升級
        field_labels = "\n".join([f"- {field.label}" for field in req.dynamic_fields_schema])
        
        prompt = f"""
        你是一位具有創意且注重細節的商業策略專家，負責生成高品質的訓練數據。

        **你的目標：**
        首先，構思一個與「{req.grant_name}」相關的新穎且具吸引力的商業或專案構想。
        其次，僅根據你剛構思的點子，詳細回答以下特定問題。

        **輸出格式：**
        你必須回傳一個單一且有效的 JSON 物件。請勿在 JSON 區塊前後加入任何額外文字。
        JSON 物件的結構必須完全符合以下格式：
        {{
        "main_idea": "<在此輸入你生成的核心專案構想（單段文字）>",
        "dynamic_fields": {{
            "<question_label_1>": "<針對問題 1 的詳細回答>",
            "<question_label_2>": "<針對問題 2 的詳細回答>",
            ...
        }}
        }}

        ---
        **背景資訊：**
        - 補助主題：{req.grant_name}
        - 計劃書模板：{req.template_name}

        **需要回答的問題（請使用以下字串作為 dynamic_fields 物件的鍵名）：**
        {field_labels}
        ---

        現在，請生成完整的 JSON 回應。
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

        # --- 關鍵檢查 ---
        # 確保返回的 dynamic_fields 是個對象，而不是字符串
        if req.mode == 'reverse' and isinstance(response_json.get("dynamic_fields"), dict):
            # 遍歷原始 json_output 的結構，確保返回的結構與之匹配
            # 這是為了防止 AI 返回扁平化的 dynamic_fields
            original_structure = req.json_output
            returned_structure = response_json["dynamic_fields"]
            
            # 我們期望 returned_structure 的 key 集合是 original_structure 的 key 集合的子集或相等
            if not set(returned_structure.keys()).issubset(set(original_structure.keys())):
                # 如果 AI 創造了新的 sectionId，這可能是一個問題
                logger.warning("AI may have returned an incorrect structure for dynamic_fields in reverse mode.")
                # 這裡可以選擇拋出錯誤，或者繼續（取決於您想要的嚴格程度）

            return response_json
        elif req.mode == 'reverse':
            # 如果 AI 返回的 dynamic_fields 不是一個字典，說明它沒有遵循指令
            raise HTTPException(status_code=500, detail="LLM failed to return a valid dictionary for 'dynamic_fields'.")

        return response_json
        

@app.post("/api/datasets", status_code=202)
async def save_dataset_entries(
    req: SaveDatasetRequest,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
):
    """異步保存數據集條目到 Supabase 和 Qdrant"""
    
    async def background_task():
        qdrant_points = []
        for entry in req.entries:
            try:
                # 1. 保存到 Supabase
                new_supabase_entry = await supabase_service.add_dataset_entry(
                    source_type=entry.source_type,
                    grant_id=entry.grant_id,
                    template_id=entry.template_id,
                    section_id=entry.section_id,
                    prompt=entry.prompt,
                    final_answer=entry.final_answer
                )
                
                # 2. 準備 Qdrant 數據
                if new_supabase_entry and 'id' in new_supabase_entry:
                    db_id = new_supabase_entry['id']
                    
                    # 2. 準備 Qdrant 數據，並將 db_id 加入
                    qdrant_points.append({
                        # `db_id` 傳給 upsert_exemplars 用作 Point ID
                        "db_id": db_id, 
                        # `text` 用於生成向量
                        "text": f"User Idea: {entry.prompt}",
                        # `payload` 是向量的元數據
                        "payload": {
                            "db_id": db_id, #在 payload 中也保存 db_id
                            "source_type": entry.source_type,
                            "grant_id": entry.grant_id,
                            "template_id": entry.template_id,
                            "section_id": entry.section_id,
                            "prompt": entry.prompt[:200] # 截斷以避免 payload 過大
                        }
                    })
                else:
                    print(f"Skipping Qdrant entry for section {entry.section_id} because no ID was returned from Supabase.")
            except Exception as e:
                print(f"Failed to process entry for section {entry.section_id}: {e}") 

        # 3. 批量寫入 Qdrant
        if qdrant_points:
            qdrant_service.upsert_exemplars(qdrant_points)

    # 立即返回，並在後台運行任務
    asyncio.create_task(background_task())
    return {"message": "Dataset saving process started in the background."}

@app.get("/api/datasets", summary="獲取所有數據集條目")
async def get_all_datasets_endpoint(
    supabase_service: SupabaseService = Depends(get_supabase_service),
    # 從查詢參數接收篩選條件
    grant_id: Optional[str] = None,
    template_id: Optional[str] = None,
    section_id: Optional[str] = None,
    source_type: Optional[str] = None
):
    """
    從 Supabase 獲取數據集記錄，支持按 grant, template, section, source_type 篩選。
    """
    try:
        datasets = await supabase_service.get_all_datasets(
            grant_id=grant_id,
            template_id=template_id,
            section_id=section_id,
            source_type=source_type,
        )
        return datasets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.put("/api/datasets/{dataset_id}", summary="更新一個數據集條目")
# async def update_dataset_entry(
#     dataset_id: int,
#     payload: DatasetUpdateRequest,
#     supabase_service: SupabaseService = Depends(get_supabase_service), 
#     qdrant_service: QdrantService = Depends(get_qdrant_service),
#     ):
#     """
#     同步更新 Supabase 和 Qdrant 中的數據。
#     注意：Qdrant 的更新策略是 "刪除舊的，插入新的"。
#     """
#     try:
#         # 1. 更新 Supabase 中的記錄
#         updated_supabase_entry = await supabase_service.update_dataset_by_id(
#             dataset_id, 
#             {"prompt": payload.prompt, "final_answer": json.dumps(payload.final_answer)}
#         )
#         if not updated_supabase_entry:
#             raise HTTPException(status_code=404, detail="Dataset not found in Supabase")

#         # 2. 更新 Qdrant 中的向量
#         # 確保 payload 中包含 Supabase ID，以便 upsert 時能正確關聯
#         qdrant_payload = {
#             "db_id": dataset_id, #在 payload 中也保存 db_id
#             "source_type": payload.source_type,
#             "grant_id": payload.grant_id,
#             "template_id": payload.template_id,
#             "section_id": payload.section_id,
#             "prompt": payload.prompt[:200] 
#         }
#         await qdrant_service.update_exemplar_by_db_id( 
#             db_id=dataset_id, 
#             new_text=payload.prompt, 
#             new_payload=qdrant_payload
#         )
        
#         return {"message": "Dataset updated successfully in both Supabase and Qdrant."}
#     except Exception as e:
#         logger.error(f"Failed to update dataset {dataset_id}: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/datasets/{dataset_id}", status_code=200)
async def update_dataset_entry(
    dataset_id: int,
    req: DatasetEntry,   
    supabase_service: SupabaseService = Depends(get_supabase_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
):
    """
    同步更新 Supabase 和 Qdrant 中的一筆數據集條目。
    注意：Qdrant 的更新策略是「刪除舊的，再插入新的」。
    """
    try:
        # 更新 Supabase
        updated_entry = await supabase_service.update_dataset_by_id(
            dataset_id,
            {
                "source_type": req.source_type,
                "grant_id": req.grant_id,
                "template_id": req.template_id,
                "section_id": req.section_id,
                "prompt": req.prompt,
                "final_answer": req.final_answer,
            },
        )

        if not updated_entry:
            raise HTTPException(status_code=404, detail="Dataset not found in Supabase")

        # 更新 Qdrant（單筆 upsert）
        qdrant_point = {
            "db_id": dataset_id,
            "text": f"User Idea: {req.prompt}",
            "payload": {
                "db_id": dataset_id,
                "source_type": req.source_type,
                "grant_id": req.grant_id,
                "template_id": req.template_id,
                "section_id": req.section_id,
                "prompt": req.prompt[:200],
            },
        }

        # 調用 Qdrant 單筆更新方法
        await qdrant_service.update_exemplar_by_db_id(
            db_id=dataset_id,
            new_text=qdrant_point["text"],
            new_payload=qdrant_point["payload"],
        )

        return {"message": f"Dataset {dataset_id} updated successfully in both Supabase and Qdrant."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/datasets/{dataset_id}", summary="刪除一個數據集條目")
async def delete_dataset_entry(dataset_id: int, 
    supabase: SupabaseService = Depends(get_supabase_service),
    qdrant: QdrantService = Depends(get_qdrant_service)):

    """同步刪除 Supabase 和 Qdrant 中的數據。"""
    try:
        # 1. 從 Qdrant 刪除 (先刪除向量，避免 Supabase 刪除後找不到關聯)
        await qdrant.delete_exemplar_by_db_id(dataset_id)

        # 2. 從 Supabase 刪除
        deleted = await supabase.delete_dataset_by_id(dataset_id)
        if not deleted:
            # 即使 Supabase 沒找到，也可能只是數據不一致，回傳成功
            logger.warning(f"Dataset ID {dataset_id} not found in Supabase but deletion was attempted.")
        
        return {"message": "Dataset entry deleted successfully from both Supabase and Qdrant."}
    except Exception as e:
        logger.error(f"Failed to delete dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/sections/{section_id}/prompts", status_code=200, summary="更新章節的自定義指令列表")
async def update_section_prompts_endpoint(
    section_id: str, 
    request: UpdatePromptsRequest,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    success = await supabase_service.update_section_prompts(section_id, request.prompts)
    if not success:
        raise HTTPException(status_code=404, detail="Section not found or update failed.")
    return {"message": "Custom prompts updated successfully."}

@app.post("/api/autofill_from_document", summary="從文檔自動填充計劃書內容")
async def autofill_from_document(
    request: AutoFillRequest,
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
        for s in request.sections
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
    {request.document_text}
    --- DOCUMENT END ---

    這是你需要填充的目標 JSON 結構定義：
    {all_schemas_info}

    請根據以上文檔內容和結構定義，生成最終的 JSON 輸出。
    """

    model_to_use = app.state.model_registry.get("gpt-3.5-turbo-1106")
    if not model_to_use:
        # 如果沒有 gpt-4-turbo，可以回退到 gpt-4
        model_to_use = app.state.model_registry.get("gpt-3.5-turbo-1106")
        if not model_to_use:
           raise HTTPException(status_code=500, detail="A powerful model like GPT-4 is required for this feature.")

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

        # 將結果格式化為前端需要的 { section_id: { content: {...} } } 格式
        formatted_result = {}
        for section_id, content in filled_data.items():
            formatted_result[section_id] = {"content": content}

        return formatted_result

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM did not return a valid JSON object.")
    except Exception as e:
        logger.error(f"Error during document auto-fill: {e}")
        raise HTTPException(status_code=500, detail=str(e))