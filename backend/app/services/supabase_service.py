# 處理所有與 Supabase 數據庫和 Storage 的交互。
import os
import json
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

from app.config import (
    SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_BUCKET_NAME, DATABASE_URL
)
from app.models import GrantConfig, TemplateConfig, SectionConfig, RoutingRule 

class SupabaseService:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase URL or Key not set in environment variables.")
        
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.bucket_name = SUPABASE_BUCKET_NAME
        
        # for SQLAlchemy direct SQL access (e.g., for seed script or complex queries)
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager # 很方便地创建可以配合 with 语法的上下文管理器。
    def get_db_session(self):
        session = self.Session()
        try:
            yield session
        finally:
            session.close()

    async def _fetch_all(self, table_name: str) -> List[Dict[str, Any]]:
        response = self.client.from_(table_name).select("*").execute()
        if response.data:
            return response.data
        return []

    async def get_all_grants_config(self) -> List[GrantConfig]:
        grants_data = await self._fetch_all("grants")
        templates_data = await self._fetch_all("plan_templates")
        sections_data = await self._fetch_all("sections")

        grants_map = {g['id']: GrantConfig(id=g['id'], name=g['name'], templates=[]) for g in grants_data}
        templates_map = {(t['id'], t['grant_id']): TemplateConfig(id=t['id'], grant_id=t['grant_id'], name=t['name'], sections=[]) for t in templates_data}

        sections_data.sort(key=lambda s: s.get("order", 0))
        
        for s in sections_data:       
            section_config = SectionConfig(
                id=s['id'],
                template_id=s['template_id'],
                grant_id=s['grant_id'],
                name=s['name'],
                json_schema=s.get('json_schema'),
                system_prompt=s.get('system_prompt'),
                critic_prompt=s.get('critic_prompt'), 
                rewrite_prompt=s.get('rewrite_prompt'),
                custom_prompt_list=s.get('custom_prompt_list') or []
            )
            if (s['template_id'], s['grant_id']) in templates_map:
                templates_map[(s['template_id'], s['grant_id'])].sections.append(section_config)

        for t in templates_map.values():
            if t.grant_id in grants_map:
                grants_map[t.grant_id].templates.append(t)

        return list(grants_map.values())

    async def get_section_details(self, grant_id: str, template_id: str, section_id: str) -> Optional[SectionConfig]:
        response = self.client.from_("sections").select("*").eq("grant_id", grant_id).eq("template_id", template_id).eq("id", section_id).single().execute()
        if response.data:
            return SectionConfig(
                id=response.data['id'],
                template_id=response.data['template_id'],
                grant_id=response.data['grant_id'],
                name=response.data['name'],
                json_schema=response.data.get('json_schema'),
                system_prompt=response.data.get('system_prompt'),
                critic_prompt=response.data.get('critic_prompt'), 
                rewrite_prompt=response.data.get('rewrite_prompt'),
                custom_prompt_list=response.data.get('custom_prompt_list') or []
            )
        return None

    async def log_sft_data_point(self, grant_id: str, template_id: str,section_id: str, prompt: str, final_answer: dict, source_type: str):
        """记录一个可用于 SFT 的数据点"""
        try:
            with self.get_db_session() as session:
                stmt = text("""
                    INSERT INTO datasets (source_type, grant_id, template_id, section_id,prompt, final_answer)
                    VALUES (:source_type,  :grant_id, :template_id, :section_id, :prompt, :final_answer);
                """)
                session.execute(stmt, {
                    "grant_id": grant_id,
                    "template_id": template_id,
                    "section_id": section_id,
                    "source_type": source_type,
                    "prompt": prompt,
                    "final_answer": json.dumps(final_answer)
                })
                session.commit() 
            print(f"SFT data point from '{source_type}' logged to datasets table.")
        except Exception as e:
             pass
    
    async def log_actor_critic_run(self, prompt: str, grant_id: str, template_id: str,section_id: str,initial_answer: dict, critic_json: dict, final_answer: dict):
        """记录一次完整的 Actor-Critic 流程数据"""
        try:
            with self.get_db_session() as session:
                stmt = text("""
                    INSERT INTO datasets (
                        source_type, grant_id, template_id, section_id,
                        prompt, initial_answer, critic_json, final_answer
                    )
                    VALUES (
                        'actor_critic', :grant_id, :template_id, :section_id,
                        :prompt, :initial_answer, :critic_json, :final_answer
                    );
                """)

                session.execute(stmt, {
                    "grant_id": grant_id,
                    "template_id": template_id,
                    "section_id": section_id,
                    "prompt": prompt,
                    "initial_answer": json.dumps(initial_answer),
                    "critic_json": json.dumps(critic_json),
                    "final_answer": json.dumps(final_answer)
                })
                session.commit()
            print("Actor-Critic run logged to datasets table.")
        except Exception as e:
            print(f"Error logging Actor-Critic run: {e}")
            
    def register_new_model(self, model_id: str, display_name: str, base_model_id: str, adapter_path: str, tags: list = None):
        """将新训练的模型注册到数据库"""

        print(f"Registering new model '{model_id}' to database...")
        try:
            with self.get_db_session() as session:
                stmt = text("""
                    INSERT INTO models (id, display_name, provider, type, base_model_id, adapter_path, tags, description,updated_at)
                    VALUES (:id, :display_name, 'internal_lora', 'internal', :base_model_id, :adapter_path, :tags, :description,NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        adapter_path = EXCLUDED.adapter_path,
                        updated_at = NOW(); 
                """)
                session.execute(stmt, {
                    "id": model_id,
                    "display_name": display_name,
                    "base_model_id": base_model_id,
                    "adapter_path": adapter_path,
                    "tags": tags if tags else [],
                    "description": f"Fine-tuned model based on {base_model_id}"
                })
                session.commit()
            print("Model registration successful.")
        except Exception as e:
            print(f"Failed to register model: {e}")

    async def get_all_models(self) -> List[Dict[str, Any]]:
        return await self._fetch_all("models")

    async def get_all_routing_rules(self) -> List[Dict[str, Any]]:
        # 按照 priority 升序获取，确保高优先级的规则在前
        response = self.client.from_("routing_rules").select("*").order("priority", desc=False).execute()
        if response.data:
            return response.data
        return []

   
    # async def find_latest_finetuned_model_for_section(self, section_id: str) -> Optional[Dict[str, Any]]:
    #     """
    #     为给定的 section 查找最新训练的、provider 为 'internal_lora' 的模型。
    #     """
    #     # 模型 ID 格式为 {section_id}-{task_type}-{timestamp}， 并且 provider 必须是 'internal_lora'
    #     response = self.client.from_("models") \
    #         .select("*") \
    #         .eq("provider", "internal_lora") \
    #         .like("id", f"{section_id}%") \
    #         .order("updated_at", desc=True) \
    #         .limit(1) \
    #         .execute() 
        
    #     if response.data:
    #         logger.info(f"Found a fine-tuned LoRA model for section '{section_id}': {response.data[0]['id']}")
    #         return response.data[0]
        
    #     logger.info(f"No specific fine-tuned LoRA model found for section '{section_id}'.")
    #     return None


    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        response = self.client.from_("users").select("*").eq("id", user_id).single().execute()
        return response.data if response.data else None

    async def get_user_usage(self, user_id: str) -> Dict[str, int]:
        """获取用户的 internal 和 external 总用量"""
        # PostgREST v10+ 支持 .rpc() 调用存储过程，更高效, 但这里简化
        query = self.client.from_("usage_logs").select("model_type, tokens_used").eq("user_id", user_id)
        response = query.execute()
        
        usage = {"internal": 0, "external": 0}
        if response.data:
            for log in response.data:
                usage[log['model_type']] += log['tokens_used']
        return usage

    async def check_quota(self, user_id: str, model_type: str) -> tuple[bool, str]:
        """检查用户是否有足够的配额使用指定类型的模型"""
        if user_id == "admin":
            return True, "Admin user has unlimited quota."
        
        user = await self.get_user_by_id(user_id)
        if not user:
            return False, "User not found."

        usage = await self.get_user_usage(user_id)

        if model_type == 'external':
            remaining = user['external_quota'] - usage['external']
            if remaining <= 0:
                return False, "External quota exhausted."
        elif model_type == 'internal':
            remaining = user['internal_quota'] - usage['internal']
            if remaining <= 0:
                return False, "Internal quota exhausted."
        
        return True, "Quota available."

    async def log_usage(self, user_id: str, model_info: Dict[str, Any], tokens_used: int):
        """记录一次模型使用"""
        model_type = model_info.get('type', 'internal')
        cost = 0.0
        # 简单估算成本，只用external modal 的 output token
        if model_type == 'external' and model_info.get('cost_info'):
            cost_per_million = model_info['cost_info'].get('output', 0)
            cost = (tokens_used / 1_000_000) * cost_per_million

        new_log = {
            "user_id": user_id,
            "model_id": model_info['id'],
            "model_type": model_type,
            "tokens_used": tokens_used,
            "cost": cost
        }
        
        self.client.from_("usage_logs").insert(new_log).execute()
        print(f"Logged usage for user {user_id}: {tokens_used} tokens for {model_type} model.")

    async def upsert_routing_rule(self, rule: RoutingRule) -> Dict[str, Any]:
        """
        新增或更新路由規則。
        我們基於 (grant_id, section_id) 的組合來判斷是更新還是插入。
        """
        # 準備要插入/更新的數據
        data_to_upsert = {
            "grant_id": rule.grant_id, 
            "section_id": rule.section_id,
            "template_id": rule.template_id,
            "model_id": rule.model_id,
            "priority": rule.priority,
            "description": rule.description or f"Rule for {rule.section_id or rule.grant_id or 'all sections'}"
        }

        # PostgREST 的 upsert 語法，on_conflict 指定了衝突的列
        # preference=resolution=merge-duplicates 會合併衝突並更新
        response = self.client.from_("routing_rules").upsert(
            data_to_upsert, 
            on_conflict="grant_id,template_id, section_id" 
        ).execute()

        if response.data:
            return response.data[0]
        else:
            raise Exception("Failed to upsert routing rule. Check unique constraints.")
    

    async def add_dataset_entry(
        self,
        source_type: str,
        grant_id: str,
        template_id: str,
        section_id: str,
        prompt: str,
        final_answer: dict
    ) -> Dict[str, Any]:
        """向 datasets 表中插入一条新的记录"""
        try:
            response = self.client.from_("datasets").insert({
                "source_type": source_type,
                "grant_id": grant_id,
                "template_id": template_id,
                "section_id": section_id,
                "prompt": prompt,
                "final_answer": final_answer, # Supabase client 會自動處理 jsonb
            }).execute()
            
            if response.data: 
                print(f"Successfully inserted {source_type} entry for section {section_id}.")
                return response.data[0]
            else:
                raise Exception("No data returned after insert.")
        except Exception as e:
            print(f"Error adding dataset entry: {e}")
            raise


    async def get_all_datasets(
        self,
        grant_id: Optional[str] = None,
        template_id: Optional[str] = None,
        section_id: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        從 datasets 表中獲取數據，並支持動態篩選。
        """
        try:
            query = self.client.from_("datasets").select("*")

            # 動態添加篩選條件
            if grant_id:
                query = query.eq("grant_id", grant_id)
            if template_id:
                query = query.eq("template_id", template_id)
            if section_id:
                query = query.eq("section_id", section_id)
            if source_type:
                query = query.eq("source_type", source_type)
            
            # 按創建時間降序排序
            response = query.order("created_at", desc=True).execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching datasets with filters: {e}")
            raise

    async def update_dataset_by_id(self, dataset_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """根據 ID 更新 datasets 表中的記錄"""
        response = self.client.from_("datasets").update(data).eq("id", dataset_id).execute()
        return response.data[0] if response.data else None

    async def delete_dataset_by_id(self, dataset_id: int) -> bool:
        """根據 ID 刪除 datasets 表中的記錄"""
        response = self.client.from_("datasets").delete().eq("id", dataset_id).execute()
        return len(response.data) > 0

    async def update_section_prompts(self, section_id: str, prompts: List[str]) -> bool:
        """更新指定 section 的 custom_prompt_list"""
        try:
            response = self.client.from_("sections").update({
                "custom_prompt_list": prompts
            }).eq("id", section_id).execute()
            
            # 檢查是否有行被更新
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Failed to update prompts for section {section_id}: {e}")
            return False