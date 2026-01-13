# 處理所有與 Supabase 數據庫和 Storage 的交互。

import os
import json
from typing import List, Dict, Any, Optional
from fastapi import Request
from supabase import create_client, Client
from sqlalchemy import create_engine, text 
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import asyncio 
from collections import defaultdict
import logging
import time
from app.utils.token_calculator import calculate_openai_tokens
from datetime import datetime, timezone, timedelta
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)
from app.config import (
    SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_BUCKET_NAME, DATABASE_URL, EMBEDDING_MODEL_NAME
)
from app.models import GrantConfig, TemplateConfig, SectionConfig, RoutingRule, SourceType 

class SupabaseService:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase URL or Key not set in environment variables.")
        
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.bucket_name = SUPABASE_BUCKET_NAME
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.embedding_model: Optional[TextEmbedding] = None

        try:
            self.embedding_model = TextEmbedding(EMBEDDING_MODEL_NAME)
            logger.info("Embedding model initialized for SupabaseService.")
        except Exception as e:
            logger.warning(f"Failed to initialize embedding model '{EMBEDDING_MODEL_NAME}': {e}")

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
    
    
    async def get_grant_by_id(self, grant_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取单个 grant 的信息。"""
        if not grant_id:
            return None
        try:
            response = (
                self.client
                .from_("grants")
                .select("*")
                .eq("id", grant_id)
                .limit(1)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error fetching grant by id '{grant_id}': {e}")
            return None


    async def get_template_by_id(self, template_id: str, grant_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取单个 plan_template 的信息。"""
        if not template_id:
            return None
        try:
            response = (
                self.client
                .from_("plan_templates")
                .select("*")
                .eq("id", template_id)
                .eq("grant_id", grant_id)
                .limit(1)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0] 
            return None
        except Exception as e:
            print(f"Error fetching template by id '{template_id}': {e}")
            return None


    async def get_sections_by_template_id(self, template_id: str, grant_id: str) -> List[Dict[str, Any]]:
        """根据 template_id 获取其下所有 sections，并按 order 排序。"""
        if not template_id:
            return []
        try:
            response = (
                self.client
                .from_("sections")
                .select("*")
                .eq("template_id", template_id)
                .eq("grant_id", grant_id)
                .order("order", desc=False)
                .execute()
            )
            return response.data or []  
        except Exception as e:
            print(f"Error fetching sections by template_id '{template_id}': {e}")
            return []


    async def get_all_draft_plans(self) -> List[Dict[str, Any]]:
        """获取所有企划草稿"""
        response = self.client.from_("draft_plans").select("*").order("created_at", desc=True).execute()
        return response.data if response.data else []

    async def create_draft_plan(self, name: str, mode: str, grant_id: Optional[str] = None, template_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """创建一个新的企划草稿"""
        
        # 检查同名草稿
        existing_response = self.client.from_("draft_plans").select("id").eq("name", name).execute()
        if existing_response.data:
            # 如果存在同名，添加一个时间戳后缀
            name = f"{name}-{int(time.time())}"

        insert_data = {
            "name": name,
            "mode": mode,
            "status": "pending",
            "grant_id": grant_id,
            "template_id": template_id,
            "user_input": {}, # 初始化为空对象
            "plan_content": {}  # 初始化为空对象
        }
        response = self.client.from_("draft_plans").insert(insert_data).execute()
        return response.data[0] if response.data else None

    async def get_draft_plan_by_id(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取单个草稿"""
        response = self.client.from_("draft_plans").select("*").eq("id", draft_id).single().execute()
        return response.data if response.data else None
    
    async def update_draft_plan(self, draft_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新一个企划草稿"""
        if "updated_at" not in data:
            # 设置为东八区时间
            tz = timezone(timedelta(hours=8))
            data["updated_at"] = datetime.now(tz).strftime('%Y-%m-%dT%H:%M:%S%z')

        response = self.client.from_("draft_plans").update(data).eq("id", draft_id).execute()
        return response.data[0] if response.data else None

    async def delete_draft_plan(self, draft_id: str) -> bool:
        """删除一个企划草稿"""
        response = self.client.from_("draft_plans").delete().eq("id", draft_id).execute()
        return len(response.data) > 0

    async def create_project_record(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """在 projects 表中新增一筆記錄。"""
        response = (
            self.client.from_("projects")
            .insert({k: v for k, v in data.items() if v is not None})
            .execute()
        )
        return response.data[0] if response.data else None

    async def get_project_by_id(self, project_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """取得單一專案。若提供 user_id，則只返回該使用者擁有的專案。"""
        try:
            query = (
                self.client.from_("projects")
                .select("*")
                .eq("id", project_id)
            )
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = query.single().execute()
            return response.data if response.data else None
        except Exception as error:
            logger.error("Failed to fetch project %s: %s", project_id, error, exc_info=True)
            return None

    async def get_projects_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """取得指定使用者的所有專案，依更新時間排序。"""
        response = (
            self.client.from_("projects")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return response.data if response.data else []

    async def update_project_record(self, project_id: str, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新指定專案（只有擁有者能更新）。"""
        response = (
            self.client.from_("projects")
            .update({k: v for k, v in data.items() if v is not None})
            .eq("id", project_id)
            .eq("user_id", user_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def delete_project_record(self, project_id: str, user_id: str) -> bool:
        """刪除指定專案。"""
        response = self.client.from_("projects").delete().eq("id", project_id).eq("user_id", user_id).execute()
        return len(response.data) > 0

    async def get_all_models(self) -> List[Dict[str, Any]]:
        return await self._fetch_all("models")

    async def get_all_routing_rules(self) -> List[Dict[str, Any]]:
        # 按照 priority 升序获取，确保高优先级的规则在前
        response = self.client.from_("routing_rules").select("*").order("priority", desc=False).execute()
        if response.data:
            return response.data
        return []
        
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        response = self.client.from_("users").select("*").eq("id", user_id).single().execute()
        return response.data if response.data else None

    async def get_user_usage(self, user_id: str) -> Dict[str, int]:
        """获取用户的 internal 和 external 总用量"""
        query = self.client.from_("usage_logs").select("model_type, cost").eq("user_id", user_id)
        response = query.execute()
        
        usage = 0
        if response.data:
            for log in response.data:
                usage += log['cost']
        return usage

    async def check_quota(self, user_id: str, model_type: str) -> tuple[bool, str]:
        """检查用户是否有足够的配额使用指定类型的模型"""
        if user_id == "admin":
            return True, "Admin user has unlimited quota."
        
        user = await self.get_user_by_id(user_id)
        if not user:
            return False, "User not found."

        usage = await self.get_user_usage(user_id)

        remaining = user['external_quota'] - usage
        if remaining <= 0:
            return False, "External quota exhausted."
        
        return True, "Quota available." 

    async def log_usage(self, user_id: str, model_info: Dict[str, Any], input_token: int,output_token: int):
        """记录一次模型使用"""
        model_type = model_info.get('type', 'internal') 
        cost = 0.0
        # 简单估算成本，只用external modal 的 output token
        if model_type == 'external' and model_info.get('cost_info'):
            cost_per_million = model_info['cost_info'].get('output', 0)
            cost = (output_token / 1_000_000) * cost_per_million

        new_log = {
            "user_id": user_id,
            "model_id": model_info['id'],
            "model_type": model_type,
            "input_token": input_token,
            "output_token":  output_token,
            "cost": cost
        }
        
        self.client.from_("usage_logs").insert(new_log).execute()
        print(f"Logged usage for user {user_id}: ${cost} for {model_type} model.")

    async def upsert_routing_rule(self, rule: RoutingRule) -> Dict[str, Any]:
        """
        新增或更新路由規則。
        基於 (grant_id, section_id, template_id, is_external) 的組合來判斷是更新還是插入。
        """
        # 準備要插入/更新的數據
        data_to_upsert = {
            "grant_id": rule.grant_id, 
            "section_id": rule.section_id,
            "template_id": rule.template_id,
            "model_id": rule.model_id,
            "priority": rule.priority,
            "description": rule.description or f"Rule for {rule.section_id or rule.grant_id or 'all sections'}",
            "is_external": rule.is_external
        }

        # on_conflict 指定衝突的列,會合併衝突並更新
        response = self.client.from_("routing_rules").upsert(
            data_to_upsert, 
            on_conflict="grant_id,template_id,section_id,is_external" 
        ).execute()

        if response.data:
            return response.data[0]
        else:
            raise Exception("Failed to upsert routing rule. Check unique constraints.")
    
    async def delete_routing_rule(self, rule_id: str) -> bool:
        """根據 ID 刪除路由規則"""
        try:
            response = self.client.from_("routing_rules").delete().eq("id", rule_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Failed to delete routing rule with id '{rule_id}': {e}", exc_info=True)
            raise Exception(f"Failed to delete routing rule: {str(e)}")
    

    async def retrieve_similar_datasets(
        self,
        query_prompt: str,
        grant_id: str,
        template_id: str,
        section_id: str,
        limit: int = 3,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        if not self.embedding_model:
            logger.warning("Embedding model is not available, cannot retrieve similar datasets.")
            return []

        try:
            # 1. 为查询文本生成嵌入
            query_embedding_ndarray = list(self.embedding_model.embed(query_prompt))[0]
            query_embedding = query_embedding_ndarray.tolist()

            # 2. 调用我们之前创建的 PostgreSQL 函数
            params = {
                'query_embedding': query_embedding,
                'match_grant_id': grant_id,
                'match_template_id': template_id,
                'match_section_id': section_id,
                'match_threshold': threshold,
                'match_count': limit
            }
            response = self.client.rpc('match_datasets', params).execute()
            
            if response.data:
                logger.info(f"Found {len(response.data)} similar datasets for section '{section_id}'.")
                return response.data
            else:
                logger.info(f"No similar datasets found for section '{section_id}'.")
                return []
        except Exception as e:
            logger.error(f"Error retrieving similar datasets via RPC: {e}")
            return []
        
    async def add_dataset_entry(
        self,
        source_type: str,
        grant_id: str,
        template_id: str,
        section_id: str,
        prompt: str,
        final_answer: dict,
        rejected_answer: Optional[dict] = None
    ) -> Dict[str, Any]:
        """向 datasets 表中插入一条新的记录"""
        try:
            prompt_embedding_ndarray = list(self.embedding_model.embed(prompt))[0]
            prompt_embedding = prompt_embedding_ndarray.tolist()

            response = self.client.from_("datasets").insert({
                "source_type": source_type,
                "grant_id": grant_id,
                "template_id": template_id,
                "section_id": section_id,
                "prompt": prompt,
                "final_answer": final_answer,
                "embedding": prompt_embedding,
                "rejected_answer": rejected_answer
            }).execute()
            insert_data = response.data  
            
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
        """根據 ID 更新 datasets 表中的記錄，並同步更新向量嵌入"""
        if "prompt" in data and data["prompt"]:
            try:
                prompt_embedding_ndarray = list(self.embedding_model.embed(data["prompt"]))[0]
                query_embedding = prompt_embedding_ndarray.tolist()

                data["embedding"] = query_embedding
            except Exception as e:
                logger.error(f"Failed to regenerate embedding for dataset {dataset_id}: {e}", exc_info=True)
                data.pop("embedding", None)

        response = self.client.from_("datasets").update(data).eq("id", dataset_id).execute()
        return response.data[0] if response.data else None

    async def delete_dataset_by_id(self, dataset_id: int) -> bool:
        """根據 ID 刪除 datasets 表中的記錄"""
        response = self.client.from_("datasets").delete().eq("id", dataset_id).execute()
        return len(response.data) > 0

    async def update_section_settings(
        self,
        request: Request,
        section_id: str,
        template_id: str,
        grant_id: str,
        custom_prompt_list: List[str],
        system_prompt: Optional[str] = None,
        search_external: Optional[bool] = None,
    ) -> bool:
        """更新指定 section 的 system_prompt, source_type 和 custom_prompt_list"""
        try:
            update_data = {
                "custom_prompt_list": custom_prompt_list,
            }
            # 只有當 system_prompt 不是 None 時才更新它
            if system_prompt is not None:
                update_data["system_prompt"] = system_prompt

            if search_external is not None:
                update_data["search_external"] = search_external

            response = (
                self.client
                .from_("sections")
                .update(update_data)
                .eq("id", section_id)
                .eq("template_id", template_id)
                .eq("grant_id", grant_id)
                .execute()
            )

            request.app.state.all_grants_config = await self.get_all_grants_config()
            
            return len(response.data) > 0
        except Exception as e:
            logger.error(
                "Failed to update settings for section %s (template %s, grant %s): %s",
                section_id,
                template_id,
                grant_id,
                e,
                exc_info=True,
            )
            return False
        
    async def log_cost_usage(self, user_id: str, model_to_use: Dict, messages: List[Dict], raw_output: str):
        token_counts = calculate_openai_tokens(
            messages=messages, 
            model_name=model_to_use['id'], 
            raw_output_text=raw_output
        )
        input_token = token_counts["input_tokens"]
        output_token = token_counts["output_tokens"]
        asyncio.create_task(self.log_usage(user_id, model_to_use, input_token, output_token))

    async def get_exemplars_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """
        根據提供的 ID 列表，從 dataset_entries 表中高效地獲取多條範例記錄。
        """
        if not ids:
            return []
            
        try:
            query = self.client.from_("datasets").select("prompt, final_answer").in_("id", ids)
            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            print(f"Error fetching exemplars by IDs {ids} from Supabase: {e}")
            return []

    async def get_commands_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """
        根據 user_id 獲取所有開啟狀態（is_open = true）的 commands 記錄。
        """
        if not user_id:
            return []
        
        try:
            response = (
                self.client.from_("commands")
                .select("*")
                .eq("user_id", user_id)
                .eq("is_open", True)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching commands for user {user_id}: {e}", exc_info=True)
            return []

    # ========== Image Generation & Storage Methods ==========
    
    async def upload_image_bytes(
        self,
        project_id: str,
        img_bytes: bytes,
        content_type: str = "image/png"
    ) -> tuple[Optional[str], Optional[str]]:
        """
        上傳圖片到 Supabase Storage，返回 (public_url, storage_path)。
        若直接取得 public url 失敗，會嘗試建立 signed url 作為 fallback。
        """
        try:
            from uuid import uuid4
            filename = f"{uuid4().hex}.png"
            path = f"images/projects/{project_id}/{filename}"

            # 上傳（注意：upload 可能回傳 dict/error -> 但不一定有統一格式）
            upload_resp = self.client.storage.from_(self.bucket_name).upload(
                path,
                img_bytes,
                {"content-type": content_type}
            )
            logger.debug(f"Supabase upload response: {upload_resp}")

            # 嘗試以不同方式解析 public url（兼容不同 SDK 版本）
            public_resp = self.client.storage.from_(self.bucket_name).get_public_url(path)
            logger.debug(f"Supabase get_public_url raw response: {public_resp}")

            public_url = None
            if isinstance(public_resp, dict):
                public_url = public_resp.get("publicURL") or public_resp.get("publicUrl") or public_resp.get("publicurl")
            elif isinstance(public_resp, str):
                public_url = public_resp
            else:
                public_url = None

            # 若沒拿到 public_url（例如 bucket 是 private），嘗試 signed url 作為 fallback
            if not public_url:
                try:
                    signed_resp = self.client.storage.from_(self.bucket_name).create_signed_url(path, expires_in=3600)
                    logger.debug(f"Signed url response: {signed_resp}")
                    if isinstance(signed_resp, dict):
                        public_url = signed_resp.get("signedURL") or signed_resp.get("signedUrl") or signed_resp.get("signedurl")
                    elif isinstance(signed_resp, str):
                        public_url = signed_resp
                except Exception as e:
                    logger.warning(f"Failed to create signed URL for {path}: {e}", exc_info=True)

            if not public_url:
                logger.error(f"Could not obtain public_url or signed URL for uploaded image at {path}")
                return None, None

            logger.info(f"Image uploaded successfully: {path}, url: {public_url}")
            return public_url, path

        except Exception as e:
            logger.error(f"Failed to upload image for project {project_id}: {e}", exc_info=True)
            return None, None
        
    async def create_image_record(
        self,
        project_id: str,
        placeholder_text: str,
        storage_path: str,
        public_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        在 images 表中新增一筆記錄。
        """
        try:
            response = self.client.from_("images").insert({
                "project_id": project_id,
                "placeholder_text": placeholder_text,
                "storage_path": storage_path,
                "public_url": public_url,
            }).execute()
            
            if response.data:
                logger.info(f"Image record created for project {project_id}: {placeholder_text}")
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to create image record: {e}", exc_info=True)
            return None
    
    async def get_images_by_project(
        self,
        project_id: str
    ) -> List[Dict[str, Any]]:
        """
        根據 project_id 取得該專案的所有圖片記錄。
        """
        try:
            response = (
                self.client.from_("images")
                .select("*")
                .eq("project_id", project_id)
                .order("created_at", desc=True)
                .execute()
            )
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Failed to fetch images for project {project_id}: {e}", exc_info=True)
            return []

