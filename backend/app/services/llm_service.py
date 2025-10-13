# 封裝所有 LLM API 的呼叫邏輯
import httpx
import json
import re
from typing import Dict, Any, Tuple, Optional, List, Callable, Awaitable
from app.config import OPENAI_API_KEY, OLLAMA_BASE_URL
from app.services.qdrant_service import QdrantService
from app.models import SectionConfig, SectionGenerateResponse 
from app.utils.extract_json import extract_json_block
from app.models import SectionGenerateResponse
import asyncio
import logging
from app.utils.routing import resolve_model
from app.utils.formatting import format_section_output

logger = logging.getLogger(__name__)

# 定義一個可呼叫的類型別名，讓程式碼更清晰， 這個類型代表一個能生成文字的異步函數
GenerationFunc = Callable[..., Awaitable[Tuple[Optional[str], Optional[Dict]]]]

class LLMService:
    def __init__(self, qdrant_service: QdrantService):
        self.qdrant_service = qdrant_service # 注入 QdrantService
        self.openai_api_key = OPENAI_API_KEY
        self.ollama_base_url = OLLAMA_BASE_URL

    def _format_few_shot_examples(self, exemplars: List[Dict[str, Any]]) -> str:
        if not exemplars:
            return ""
        
        formatted_examples = ["以下是几个你可以参考的优秀范例："]
        for i, ex in enumerate(exemplars):
            topic = ex.get('topic', '无主题')
            output_json = json.dumps(ex.get('output', {}), ensure_ascii=False, indent=2)
            formatted_examples.append(f"\n--- 范例 {i+1} ---")
            formatted_examples.append(f"主题: {topic}")
            formatted_examples.append(f"期望输出格式 (JSON): \n{output_json}")
        formatted_examples.append("\n--- 范例结束 ---\n")
        return "\n".join(formatted_examples)

    def _build_initial_actor_messages(self, user_input: str, section_details: SectionConfig) -> List[Dict]:
        """建立 Actor 首次生成時的 messages"""
        exemplars = self.qdrant_service.retrieve_exemplars(f"{user_input} {section_details.name}")
        few_shot_str = self._format_few_shot_examples(exemplars)
        schema_str = json.dumps(section_details.json_schema, ensure_ascii=False)
        return [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": f"{few_shot_str}\n用户需求: {user_input}\n请一定要根据以下 JSON schema 生成内容:\n{schema_str}"}
        ]

    def _build_critic_messages(self, user_input: str, section_details: SectionConfig, initial_answer: Dict) -> List[Dict]:
        """建立 Critic 評審時的 messages"""
        critic_prompt = section_details.critic_prompt.format(
            section_name=section_details.name,
            user_input=user_input,
            schema_json=json.dumps(section_details.json_schema, ensure_ascii=False),
            initial_answer_json=json.dumps(initial_answer, ensure_ascii=False)
        )
        return [{"role": "user", "content": critic_prompt}]

    def _build_rewrite_messages(self, user_input: str, section_details: SectionConfig, initial_answer: Dict, critic_json: Dict) -> List[Dict]:
        """建立 Actor 重寫時的 messages"""
        rewrite_prompt = section_details.rewrite_prompt.format(
            section_name=section_details.name,
            user_input=user_input,
            schema_json=json.dumps(section_details.json_schema, ensure_ascii=False),
            initial_answer_json=json.dumps(initial_answer, ensure_ascii=False),
            critic_json=json.dumps(critic_json, ensure_ascii=False)
        )
        return [
            {"role": "system", "content": "You are a professional writer tasked with revising a draft based on feedback."},
            {"role": "user", "content": rewrite_prompt}
        ]
    
    def _build_api_request(self, model_info: Dict, messages: List[Dict], is_json_output: bool) -> Tuple[str, Dict, Dict]:
        """根據 model_info 建立 API 請求的 URL, headers, 和 payload"""
        provider = model_info.get("provider")
        model_id = model_info.get("id")
        
        if provider == "openai":
            if not self.openai_api_key: raise ValueError("OPENAI_API_KEY not set.")
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
            payload = {"model": model_id, "messages": messages, "temperature": 0.3}
            if is_json_output: payload["response_format"] = {"type": "json_object"}
            return url, headers, payload

        elif provider == "ollama":
            url = f"{self.ollama_base_url}/chat/completions"
            headers = {"Content-Type": "application/json"}
            payload = {"model": model_id, "messages": messages, "stream": False, "options": {"temperature": 0.3}}
            if is_json_output: payload["format"] = "json"
            return url, headers, payload
            
        raise ValueError(f"Unsupported external provider: {provider}")

    async def call_external_api(self, session: httpx.AsyncClient, model_info: Dict, messages: List[Dict], is_json_output: bool = True) -> Tuple[Optional[str], Optional[Dict]]:
        """REFACTOR: 重構後更具擴展性的外部 API 呼叫函數"""
        try:
            api_url, headers, payload = self._build_api_request(model_info, messages, is_json_output)
            response = await session.post(api_url, json=payload, headers=headers, timeout=300)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"], None
        except (httpx.HTTPStatusError, ValueError) as e:
            error_msg = f"API call failed for model {model_info.get('id')}: {e}"
            logger.error(error_msg, exc_info=True)
            return None, {"error": error_msg}
        except Exception as e:
            error_msg = f"An unexpected error occurred during API call: {repr(e)}"
            logger.error(error_msg, exc_info=True)
            return None, {"error": error_msg}

    async def generate_with_loaded_model(self, model: Any, tokenizer: Any, messages: List[Dict]) -> Tuple[Optional[str], Optional[Dict]]:
        try:
            prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)
            outputs = model.generate(
                **inputs, max_new_tokens=2048, do_sample=True, temperature=0.3,
                top_p=0.9, eos_token_id=tokenizer.eos_token_id
            )
            response_text = tokenizer.decode(outputs[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            return response_text, None
        except Exception as e:
            logger.error(f"Error during local model generation: {repr(e)}", exc_info=True)
            return None, {"error": "Failed to generate text with the local model."}

    # --- 3. Workflow Unification: 統一 Actor-Critic 流程 --- 
    async def _execute_generation_step(self, *, generation_func: GenerationFunc, messages: List[Dict], error_context: str, section_id_for_parsing: str) -> Tuple[Optional[Dict], Optional[str]]:
        """'呼叫->解析->回報錯誤' 的步驟"""
        raw_output, error = await generation_func(messages=messages)
        if error:
            return None, f"[{error_context}] Generation failed: {error.get('error', 'Unknown error')}"
        
        parsed_json, parsing_error = extract_json_block(raw_output, section_id_for_parsing)
        if parsing_error:
            return None, f"[{error_context}] Output parsing failed: {parsing_error.get('error', 'Unknown parsing error')}"
            
        return parsed_json, None

    async def _run_actor_critic_workflow(
        self,
        http_session: httpx.AsyncClient,
        actor_func: GenerationFunc, 
        critic_model_info: Dict,
        section_details: SectionConfig,
        user_input: str
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        actor_func 是一個可呼叫的對象，可以是本地生成函數，也可以是 API 呼叫函數。
        """
        # --- Step 1: Actor generates initial answer ---
        logger.info("-> [Workflow] Step 1: Actor generating initial answer...")
        initial_messages = self._build_initial_actor_messages(user_input, section_details)
        initial_answer, error = await self._execute_generation_step(
            generation_func=actor_func,
            messages=initial_messages,
            error_context="Actor-Initial",
            section_id_for_parsing=section_details.id
        )
        if error: return None, error

        # --- Step 2: Critic reviews the answer ---
        logger.info(f"-> [Workflow] Step 2: Critic ({critic_model_info['id']}) reviewing...")
        critic_messages = self._build_critic_messages(user_input, section_details, initial_answer)
        critic_func = partial(self.call_external_api, http_session, critic_model_info)
        critic_json, error = await self._execute_generation_step(
            generation_func=critic_func,
            messages=critic_messages,
            error_context="Critic",
            section_id_for_parsing="critic"
        )
        if error: return None, error
        
        # --- Step 3: Actor rewrites based on critique ---
        logger.info("-> [Workflow] Step 3: Actor rewriting based on critique...")
        rewrite_messages = self._build_rewrite_messages(user_input, section_details, initial_answer, critic_json)
        final_answer, error = await self._execute_generation_step(
            generation_func=actor_func,
            messages=rewrite_messages,
            error_context="Actor-Rewrite",
            section_id_for_parsing=section_details.id
        )
        if error: return None, error

        return {
            "initial_answer": initial_answer,
            "critic_json": critic_json,
            "final_answer": final_answer
        }, None

    # --- 4. Public-Facing Methods: 簡潔的公開接口 ---
    async def run_actor_critic_flow(self, http_session: httpx.AsyncClient, actor_model_bundle: Dict, critic_model_info: Dict, section_details: SectionConfig, user_input: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        執行 Actor-Critic 流程，Actor 使用加載的本地模型。
        """
        # 使用 functools.partial 來固定 actor_func 的 model 和 tokenizer 參數
        actor_func = partial(self.generate_with_loaded_model, actor_model_bundle["model"], actor_model_bundle["tokenizer"])
        return await self._run_actor_critic_workflow(
            http_session=http_session,
            actor_func=actor_func,
            critic_model_info=critic_model_info,
            section_details=section_details,
            user_input=user_input
        )
    
    async def run_actor_critic_flow_via_api(self, http_session: httpx.AsyncClient, actor_model_info: Dict, critic_model_info: Dict, section_details: SectionConfig, user_input: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        執行 Actor-Critic 流程，Actor 是通過 API (如 Ollama) 呼叫的。
        """
        # 使用 functools.partial 來固定 actor_func 的 session 和 model_info 參數
        actor_func = partial(self.call_external_api, http_session, actor_model_info)
        return await self._run_actor_critic_workflow(
            http_session=http_session,
            actor_func=actor_func,
            critic_model_info=critic_model_info,
            section_details=section_details,
            user_input=user_input
        )

    async def generate_section_content(
        self,  
        http_session: httpx.AsyncClient, 
        grant_id: str, 
        template_id: str, 
        section_id: str, 
        user_input: str,
        app_state: Any,
        user_id: str,
        supabase_service: "SupabaseService"
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

            exemplars = self.qdrant_service.retrieve_exemplars(f"{user_input} {section_details.name}")
            few_shot_str = self._format_few_shot_examples(exemplars)
            user_content = f"{few_shot_str}\n用户需求: {user_input}\n请根据以下 JSON schema 生成内容:\n{json.dumps(section_details.json_schema, ensure_ascii=False)}"
        
            # 檢查是否有自定義指令，並將它們附加到 user_content
            if section_details.custom_prompt_list:
                custom_prompts_str = "\n".join(f"- {p}" for p in section_details.custom_prompt_list)
                user_content += f"\n\n请额外遵循以下客製化指令：\n{custom_prompts_str}"

            messages = [
                {"role": "system", "content": section_details.system_prompt},
                {"role": "user", "content": user_content} 
            ]

            raw_output, llm_error = await self.call_external_api(http_session, model_to_use, messages)
            
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
            
            ac_data, ac_error = await self.run_actor_critic_flow_via_api(
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
            #     ac_data, ac_error = await self.run_actor_critic_flow(
            #         http_session=http_session,
            #         actor_model_bundle=actor_model_bundle, 
            #         critic_model_info=critic_model_info,
            #         section_details=section_details,
            #         user_input=user_input
            #     )
            #     print("already done actor critic flow")

            # elif provider == 'ollama':
            #     # --- 分支 B2: Actor 是通过 Ollama API 调用的基础模型 ---
            #     ac_data, ac_error = await self.run_actor_critic_flow_via_api(
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

