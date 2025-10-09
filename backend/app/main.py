import asyncio
import json
import httpx
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import DEFAULT_MODEL_ID
from app.models import (
    GenerateRequest, SectionGenerateResponse, GrantConfig,
)
from app.services.supabase_service import SupabaseService
from app.services.qdrant_service import QdrantService
from app.services.llm_service import LLMService,extract_json_block
from app.services.model_manager import LoRAModelManager
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

async def get_model_manager(request: Request) -> LoRAModelManager:
    return request.app.state.model_manager

@app.on_event("startup")
async def startup_event():
    print("正在加载服务器配置...")
    
    # 初始化服务
    app.state.supabase_service = SupabaseService()
    app.state.qdrant_service = QdrantService()
    app.state.llm_service = LLMService(app.state.qdrant_service)
    app.state.model_manager = LoRAModelManager()

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
    supabase_service: SupabaseService,
    llm_service: LLMService,
    model_manager: LoRAModelManager, 
    app_state: Any,
    user_id: str
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
        messages = [
            {"role": "system", "content": section_details.system_prompt},
            {"role": "user", "content": f"{few_shot_str}\n用户需求: {user_input}\n请根据以下 JSON schema 生成内容:\n{json.dumps(section_details.json_schema, ensure_ascii=False)}"}
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
                asyncio.create_task(
                    supabase_service.log_sft_data_point(
                        grant_id=grant_id,
                        template_id=template_id,
                        section_id=section_id,
                        prompt=full_prompt,
                        final_answer=final_content_json,
                        source_type='external_direct' 
                    )
                )

    elif model_type == 'internal': 
        # --- 流程 B: 所有 INTERNAL 模型都走 Actor-Critic (DPO 数据收集) ---
        provider = model_to_use.get("provider")
        logger.info(f"-> Starting Actor-Critic flow for INTERNAL model: {model_to_use['id']} (Provider: {provider})")

        critic_model_info = app_state.model_registry.get("gpt-4-turbo")
        if not critic_model_info:
            return SectionGenerateResponse(section_id=section_id, error="Critic model 'gpt-4-turbo' not found.")

        finetuned_lora_info = await supabase_service.find_latest_finetuned_model_for_section(section_id)
        if finetuned_lora_info:
            logger.info(f"   -> Upgrading to fine-tuned LoRA model: {finetuned_lora_info['id']}")
            model_to_use = finetuned_lora_info
            provider = 'internal_lora'
        else:
            logger.info(f"   -> Using base internal model as fallback: {model_to_use['id']}")

        # Actor 的执行方式根据 provider 决定
        if provider == 'internal_lora':
            # --- 分支 B1: Actor 是已加载的 LoRA 模型 ---
            actor_model_bundle = model_manager.get_lora_model(model_to_use)
            if not actor_model_bundle:
                return SectionGenerateResponse(section_id=section_id, error=f"Failed to load LoRA model '{model_to_use['id']}'.")
            
            # 使用加载的模型执行 A-C 流程
            ac_data, ac_error = await llm_service.run_actor_critic_flow(
                http_session=http_session,
                actor_model_bundle=actor_model_bundle, 
                critic_model_info=critic_model_info,
                section_details=section_details,
                user_input=user_input
            )
            print("already done actor critic flow")

        elif provider == 'ollama':
            # --- 分支 B2: Actor 是通过 Ollama API 调用的基础模型 ---
            ac_data, ac_error = await llm_service.run_actor_critic_flow_via_api(
                http_session=http_session,
                actor_model_info=model_to_use, 
                critic_model_info=critic_model_info,
                section_details=section_details,
                user_input=user_input
            )
        
        else:
            return SectionGenerateResponse(section_id=section_id, error=f"Unsupported provider for internal model: {provider}")
        
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

    else:
        error_message = f"Unknown provider type: {provider}"

    # 4. --- 返回结果 ---
    if error_message: return SectionGenerateResponse(section_id=section_id, error=error_message)
    if not final_content_json: return SectionGenerateResponse(section_id=section_id, error="Generation resulted in empty content.")
    
    formatted_content = format_section_output(final_content_json, section_details.json_schema)
    return SectionGenerateResponse(section_id=section_id, content=formatted_content)



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
    model_manager: LoRAModelManager = Depends(get_model_manager)
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
                model_manager=model_manager,
                supabase_service=supabase_service,
                llm_service=llm_service,
                app_state=app.state 
            )
            for s in request.sections
        ]
        results = await asyncio.gather(*tasks)
    
    plan_content = {res.section_id: res for res in results}
    
    return JSONResponse(content={k: v.dict() for k, v in plan_content.items()})
