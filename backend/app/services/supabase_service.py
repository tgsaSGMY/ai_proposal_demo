# 處理所有與 Supabase 數據庫和 Storage 的交互。
import os
import json
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import asyncio 
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)
from app.config import (
    SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_BUCKET_NAME, DATABASE_URL
)
from app.models import GrantConfig, TemplateConfig, SectionConfig, RoutingRule, SourceType 

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
        """提供一個 SQLAlchemy session 上下文管理器。"""
        session = self.Session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _execute_sql(self, statement: str, params: Dict[str, Any]):
        """執行一個帶參數的原生 SQL 語句。"""
        try:
            with self.get_db_session() as session:
                session.execute(text(statement), params)
                session.commit()
        except Exception as e:
            logger.error(f"SQL execution failed. Error: {e}", exc_info=True)
    
    async def _fetch_all(self, table_name: str, order_by: Optional[str] = None, ascending: bool = True) -> List[Dict[str, Any]]:
        """從指定表中獲取所有數據的通用輔助函數。"""
        query = self.client.from_(table_name).select("*")
        if order_by:
            query = query.order(order_by, desc=not ascending)
        
        response = await asyncio.to_thread(query.execute) 
        return response.data or []
    
    async def get_all_grants_config(self) -> List[GrantConfig]:
        """
        併發獲取所有 grants, templates, 和 sections 的配置，並將它們組合成嵌套結構。
        """
        grants_data, templates_data, sections_data = await asyncio.gather(
            self._fetch_all("grants"),
            self._fetch_all("plan_templates"),
            self._fetch_all("sections", order_by="order") 
        )

        sections_by_template = defaultdict(list)
        for s_data in sections_data:
            sections_by_template[(s_data['template_id'], s_data['grant_id'])].append(SectionConfig(**s_data))

        templates_by_grant = defaultdict(list)
        for t_data in templates_data:
            template_id_tuple = (t_data['id'], t_data['grant_id'])
            t_data['sections'] = sections_by_template[template_id_tuple]
            templates_by_grant[t_data['grant_id']].append(TemplateConfig(**t_data))

        # 3. 組裝最終結果
        all_grants = []
        for g_data in grants_data:
            g_data['templates'] = templates_by_grant[g_data['id']]
            all_grants.append(GrantConfig(**g_data))
            
        return all_grants

    async def get_section_details(self, grant_id: str, template_id: str, section_id: str) -> Optional[SectionConfig]:
        """獲取單個 section 的詳細信息。"""
        response = await asyncio.to_thread(
            self.client.from_("sections")
            .select("*")
            .eq("grant_id", grant_id)
            .eq("template_id", template_id)
            .eq("id", section_id)
            .single()
            .execute
        )
        if response.data:
            return SectionConfig(**response.data)
        return None

    async def log_sft_data_point(self, grant_id: str, template_id: str,section_id: str, prompt: str, final_answer: dict, source_type: str):
        """记录一个可用于 SFT 的数据点"""
        stmt = text("""
            INSERT INTO datasets (source_type, grant_id, template_id, section_id,prompt, final_answer)
            VALUES (:source_type,  :grant_id, :template_id, :section_id, :prompt, :final_answer);
        """)
        params = {
            "source_type": source_type,
            "grant_id": grant_id,
            "template_id": template_id,
            "section_id": section_id,
            "prompt": prompt,
            "final_answer": json.dumps(final_answer)
        }
        await asyncio.to_thread(self._execute_sql, stmt, params)
        print(f"SFT data point from '{source_type}' logged to datasets table.")
    
    async def log_actor_critic_run(self, prompt: str, grant_id: str, template_id: str, section_id: str, initial_answer: dict, critic_json: dict, final_answer: dict):
        """記錄一次完整的 Actor-Critic 流程數據。"""
        stmt = """
            INSERT INTO datasets (
                source_type, grant_id, template_id, section_id,
                prompt, initial_answer, critic_json, final_answer
            )
            VALUES (
                'actor_critic', :grant_id, :template_id, :section_id,
                :prompt, :initial_answer, :critic_json, :final_answer
            );
        """
        params = {
            "grant_id": grant_id, "template_id": template_id, "section_id": section_id,
            "prompt": prompt,
            "initial_answer": json.dumps(initial_answer),
            "critic_json": json.dumps(critic_json),
            "final_answer": json.dumps(final_answer)
        }
        await asyncio.to_thread(self._execute_sql, stmt, params)
        print("Actor-Critic run logged to datasets table.")
            
    def register_new_model(self, model_id: str, display_name: str, base_model_id: str, adapter_path: str, tags: list = None):
        """将新训练的模型注册到数据库"""
        print(f"Registering new model '{model_id}' to database...")
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
    #         return response.data[0]
        
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

    async def update_section_settings(
        self, 
        section_id: str, 
        prompts: List[str], 
        source_type: SourceType,
        system_prompt: Optional[str] = None,
    ) -> bool:
        """更新指定 section 的 system_prompt, source_type 和 custom_prompt_list"""
        try:
            update_data = {
                "custom_prompt_list": prompts,
                "source_type":source_type
            }
            # 只有當 system_prompt 不是 None 時才更新它
            if system_prompt is not None:
                update_data["system_prompt"] = system_prompt

            response = self.client.from_("sections").update(update_data).eq("id", section_id).execute()
            
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Failed to update settings for section {section_id}: {e}")
            return False