# 封裝所有 LLM API 的呼叫邏輯
import httpx
import json
import re
from typing import Dict, Any, Tuple, Optional, List
import logging

from app.config import OPENAI_API_KEY, OLLAMA_BASE_URL
from app.services.qdrant_service import QdrantService # 用于few-shot
from app.models import SectionConfig


logger = logging.getLogger(__name__)

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

    async def _call_api_internal(self, session: httpx.AsyncClient, api_url: str, headers: Dict, payload: Dict) -> Tuple[Optional[str], Optional[Dict]]:
        try:
            response = await session.post(api_url, json=payload, headers=headers, timeout=300)
            response.raise_for_status()
            
            raw_content = response.json()["choices"][0]["message"]["content"]
            return raw_content, None

        except httpx.HTTPStatusError as e:
            error_msg = f"LLM API HTTP error ({e.response.status_code}): {e.response.text}"
            return None, {"error": error_msg}
        except Exception as e:
            error_msg = f"An unexpected error occurred during LLM API call: {repr(e)}"
            return None, {"error": error_msg}

    async def call_external_api(self, session: httpx.AsyncClient, model_info: Dict, messages: List[Dict], is_json_output: bool = True) -> Tuple[Optional[str], Optional[Dict]]:
        """
        专门用于调用外部 API (OpenAI) 或基础 Ollama 模型的函数。
        """
        provider = model_info.get("provider")
        api_url = None; headers = {}; payload = {}

        if provider == "openai":
            api_key = self.openai_api_key 
            if not api_key: return None, {"error": "API_KEY not set."}
            api_url = "https://api.openai.com/v1/chat/completions" 
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"model": model_info.get("id"), "messages": messages, "temperature": 0.3}
            if is_json_output: payload["response_format"] = {"type": "json_object"}

        elif provider == "ollama":
            api_url = f"{self.ollama_base_url}/chat/completions"
            headers = {"Content-Type": "application/json"}
            payload = { "model": model_info.get("id"), "messages": messages, "stream": False, "options": {"temperature": 0.3}}
            if is_json_output: payload["format"] = "json"
        else:
            return None, {"error": f"Unsupported external provider: {provider}"}
            
        try:
            response = await session.post(api_url, json=payload, headers=headers, timeout=300)
            
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"], None
        except Exception as e:
            logger.error(f"Error calling external API for {provider}: {repr(e)}", exc_info=True)
            return None, {"error": f"External API call failed: {repr(e)}"}

    async def generate_with_loaded_model(self, model: Any, tokenizer: Any, messages: List[Dict]) -> Tuple[Optional[str], Optional[Dict]]:
        """
        使用一个已经加载好的本地 LoRA 模型和 Tokenizer 进行推理。
        """
        try:
            # 1. 应用聊天模板，模型交互
            prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

            # 2. Tokenize 输入
            inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)

            # 3. 生成输出
            outputs = model.generate(
                **inputs,
                max_new_tokens=2048,
                do_sample=True,
                temperature=0.3,
                top_p=0.9,
                eos_token_id=tokenizer.eos_token_id
            )
            
            # 4. 解码 (只解码新生成的部分)
            response_text = tokenizer.decode(outputs[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            
            return response_text, None
        except Exception as e:
            logger.error(f"Error during local model generation: {repr(e)}", exc_info=True)
            return None, {"error": "Failed to generate text with the local model."}
        
    async def run_actor_critic_flow(self, http_session: httpx.AsyncClient, actor_model_bundle: Dict, critic_model_info: Dict, section_details: SectionConfig, user_input: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        执行 Actor-Critic 流程，Actor 使用加载的本地模型，Critic 使用外部 API。
        """
        actor_model, actor_tokenizer = actor_model_bundle["model"], actor_model_bundle["tokenizer"]
        
        # 1. --- Actor: 生成初稿 （调用 generate_with_loaded_model） ---
        print("-> [Actor] Generating initial answer using loaded LoRA model...")
        exemplars = self.qdrant_service.retrieve_exemplars(f"{user_input} {section_details.name}")
        few_shot_str = self._format_few_shot_examples(exemplars)
        actor_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{few_shot_str}\n用户需求: {user_input}\n请一定要根据以下 JSON schema 生成内容:\n{json.dumps(section_details.json_schema, ensure_ascii=False)}"}
        ]
        initial_answer_str, error = await self.generate_with_loaded_model(actor_model, actor_tokenizer, actor_messages)
        if error: return None, f"Actor failed: {error['error']}"
        initial_answer, p_err = extract_json_block(initial_answer_str, section_details.id); 
        if p_err: return None, f"Actor output parsing failed: {p_err['error']}"

        # 2. --- Critic: 评审初稿 ---
        print(f"-> [Critic] Reviewing initial answer using external API: {critic_model_info['id']}...")
        critic_prompt = section_details.critic_prompt.format(section_name=section_details.name, user_input=user_input, schema_json=json.dumps(section_details.json_schema, ensure_ascii=False), initial_answer_json=json.dumps(initial_answer, ensure_ascii=False))
        critic_messages = [{"role": "user", "content": critic_prompt}]
        critic_json_str, error = await self.call_external_api(http_session, critic_model_info, critic_messages)
        if error: return None, f"Critic failed: {error['error']}"
        critic_json, p_err = extract_json_block(critic_json_str, "critic")
        if p_err: return None, f"Critic output parsing failed: {p_err['error']}"
        
        # 3. --- Actor: 根据评审重写 ---
        print("-> [Actor] Rewriting based on critique using loaded LoRA model...")
        rewrite_prompt = section_details.rewrite_prompt.format(section_name=section_details.name, user_input=user_input, schema_json=json.dumps(section_details.json_schema, ensure_ascii=False), initial_answer_json=json.dumps(initial_answer, ensure_ascii=False), critic_json=json.dumps(critic_json, ensure_ascii=False))
        rewrite_messages = [{"role": "system", "content": "You are a professional writer tasked with revising a draft based on feedback."}, {"role": "user", "content": rewrite_prompt}]
        final_answer_str, error = await self.generate_with_loaded_model(actor_model, actor_tokenizer, rewrite_messages)
        if error: return None, f"Rewrite failed: {error['error']}"
        final_answer, p_err = extract_json_block(final_answer_str, section_details.id)
        if p_err: return None, f"Rewrite output parsing failed: {p_err['error']}"

        return {
            "initial_answer": initial_answer,
            "critic_json": critic_json,
            "final_answer": final_answer
        }, None
    
    async def run_actor_critic_flow_via_api(self, http_session: httpx.AsyncClient, actor_model_info: Dict, critic_model_info: Dict, section_details: SectionConfig, user_input: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        执行 Actor-Critic 流程，其中 Actor 是通过 API (如 Ollama) 调用的。
        """
        # 1. --- Actor: 生成初稿 ---
        print(f"-> [Actor API] Generating initial answer using API model: {actor_model_info['id']}...")
        exemplars = self.qdrant_service.retrieve_exemplars(f"{user_input} {section_details.name}")
        few_shot_str = self._format_few_shot_examples(exemplars)
        actor_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{few_shot_str}\n用户需求: {user_input}\n请一定要根据以下 JSON schema 生成内容:\n{json.dumps(section_details.json_schema, ensure_ascii=False)}"}
        ]
        
        # -----调用 call_external_api------
        initial_answer_str, error = await self.call_external_api(http_session, actor_model_info, actor_messages)
        if error: return None, f"Actor (API) failed: {error['error']}"
        initial_answer, p_err = extract_json_block(initial_answer_str, section_details.id); 
        if p_err: return None, f"Actor (API) output parsing failed: {p_err['error']}"

        # 2. --- Critic: 评审初稿 ---
        print(f"-> [Critic] Reviewing initial answer using external API: {critic_model_info['id']}...")
        critic_prompt = section_details.critic_prompt.format(section_name=section_details.name, user_input=user_input, schema_json=json.dumps(section_details.json_schema, ensure_ascii=False), initial_answer_json=json.dumps(initial_answer, ensure_ascii=False))
        critic_messages = [{"role": "user", "content": critic_prompt}]
        critic_json_str, error = await self.call_external_api(http_session, critic_model_info, critic_messages)
        if error: return None, f"Critic failed: {error['error']}"
        critic_json, p_err = extract_json_block(critic_json_str, "critic")
        if p_err: return None, f"Critic output parsing failed: {p_err['error']}"
        
        # 3. --- Actor: 根据评审重写 ---
        print(f"-> [Actor API] Rewriting based on critique using API model: {actor_model_info['id']}...")
        rewrite_prompt = section_details.rewrite_prompt.format(section_name=section_details.name, user_input=user_input, schema_json=json.dumps(section_details.json_schema, ensure_ascii=False), initial_answer_json=json.dumps(initial_answer, ensure_ascii=False), critic_json=json.dumps(critic_json, ensure_ascii=False))
        rewrite_messages = [{"role": "system", "content": "You are a professional writer tasked with revising a draft based on feedback."}, {"role": "user", "content": rewrite_prompt}]

        # --------调用 call_external_api------
        final_answer_str, error = await self.call_external_api(http_session, actor_model_info, rewrite_messages)
        if error: return None, f"Rewrite (API) failed: {error['error']}"
        final_answer, p_err = extract_json_block(final_answer_str, section_details.id)
        if p_err: return None, f"Rewrite (API) output parsing failed: {p_err['error']}"

        return {
            "initial_answer": initial_answer,
            "critic_json": critic_json,
            "final_answer": final_answer
        }, None