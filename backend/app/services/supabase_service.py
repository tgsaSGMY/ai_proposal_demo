# 處理所有與 Supabase 數據庫和 Storage 的交互。

import os
import json
from typing import List, Dict, Any, Optional, Union
from fastapi import Request
from supabase import create_client, Client
from sqlalchemy import create_engine, text 
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import asyncio 
from collections import defaultdict
import logging
import time
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

    def _execute_sql(self, statement: Union[str, TextClause], params: Dict[str, Any]):
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

    async def get_section_details(
        self,
        grant_id: str,
        template_id: str,
        section_id: str,
    ) -> Optional[SectionConfig]:
        """獲取單個 section 的詳細信息。"""
        try:
            response = (
                self.client.from_("sections")
                .select("*")
                .eq("grant_id", grant_id)
                .eq("template_id", template_id)
                .eq("id", section_id)
                .limit(1)
                .execute()
            )
            if response.data:
                return SectionConfig(**response.data[0])
            return None
        except Exception as error:
            logger.error(
                "Failed to fetch section %s/%s/%s: %s",
                grant_id,
                template_id,
                section_id,
                error,
                exc_info=True,
            )
            return None

    async def log_execution_event(
        self,
        *,
        project_id: Optional[str],
        user_id: Optional[str],
        event_type: str,
        section_id: Optional[str] = None,
        version_id: Optional[str] = None,
        external_sources: Optional[List[Dict[str, Any]]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append an execution timeline entry for AI transparency."""
        try:
            canonical_user_id = await self.ensure_canonical_user_id(user_id)
            insert_data = {
                "project_id": project_id,
                "user_id": canonical_user_id,
                "event_type": event_type,
                "section_id": section_id,
                "version_id": version_id,
                "external_sources": external_sources,  # Supabase handles JSON serialization
                "payload": payload or {},
            }
            response = self.client.from_("execution_logs").insert(insert_data).execute()
            if response.data:
                logger.debug(f"Execution event logged: {event_type} for project {project_id}")
        except Exception:
            logger.error("Failed to log execution event", exc_info=True)    

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


    async def list_grants(self) -> List[Dict[str, Any]]:
        """取得所有 Grant 記錄。"""
        response = (
            self.client
            .from_("grants")
            .select("*")
            .order("id", desc=False)
            .execute()
        )
        return response.data or []

    async def create_grant_record(self, grant_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """新增 Grant 記錄。"""
        response = self.client.from_("grants").insert(grant_data).execute()
        return response.data[0] if response.data else None

    async def update_grant_record(self, current_grant_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新既有 Grant，允許更改主鍵。"""
        payload = {k: v for k, v in data.items() if v is not None}
        if not payload:
            return None
        response = (
            self.client
            .from_("grants")
            .update(payload)
            .eq("id", current_grant_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def list_plan_templates(self, grant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """取得所有計畫模板，可依 Grant 過濾。"""
        query = (
            self.client
            .from_("plan_templates")
            .select("*")
            .order("order", desc=False)
            .order("grant_id", desc=False)
            .order("name", desc=False)
        )
        if grant_id:
            query = query.eq("grant_id", grant_id)
        response = query.execute()
        return response.data or []

    async def create_plan_template_record(self, template_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """新增計畫模板。"""
        payload = {k: v for k, v in template_data.items() if v is not None}

        # plan_templates.order 為 NOT NULL；若前端未傳，補上目前最大值 + 1
        if payload.get("order") is None:
            max_order_resp = (
                self.client
                .from_("plan_templates")
                .select("order")
                .order("order", desc=True)
                .limit(1)
                .execute()
            )
            max_order = 0
            if max_order_resp.data:
                current = max_order_resp.data[0].get("order")
                if isinstance(current, (int, float)):
                    max_order = int(current)
            payload["order"] = max_order + 1

        response = self.client.from_("plan_templates").insert(payload).execute()
        return response.data[0] if response.data else None

    async def update_plan_template_record(
        self,
        template_id: str,
        grant_id: str,
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """更新既有模板，依照 (id, grant_id) 鎖定。"""
        payload = {k: v for k, v in data.items() if v is not None}
        if not payload:
            return None
        response = (
            self.client
            .from_("plan_templates")
            .update(payload)
            .eq("id", template_id)
            .eq("grant_id", grant_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def create_section_record(self, section_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """新增章節記錄。"""
        payload = {k: v for k, v in section_data.items() if v is not None}
        if not payload:
            return None
        if "current_version" not in payload:
            payload["current_version"] = 1
        if not payload.get("system_prompt"):
            payload["system_prompt"] = self._compose_system_prompt(
                grant_id=payload.get("grant_id", ""),
                template_id=payload.get("template_id", ""),
                section_id=payload.get("id", ""),
                section_name=payload.get("name"),
                schema_json=payload.get("json_schema"),
            )
        response = self.client.from_("sections").insert(payload).execute()
        record = response.data[0] if response.data else None
        if record:
            await self._insert_section_schema_version(
                section_id=record["id"],
                template_id=record["template_id"],
                grant_id=record["grant_id"],
                version=record.get("current_version") or 1,
                json_schema=record.get("json_schema"),
                system_prompt=record.get("system_prompt"),
            )
        return record

    async def update_section_record(
        self,
        section_id: str,
        template_id: str,
        grant_id: str,
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """更新指定章節。"""
        payload = {k: v for k, v in data.items() if v is not None}
        if not payload:
            return None
        existing = await self.get_section_details(grant_id, template_id, section_id)
        if not existing:
            return None

        schema_changed = "json_schema" in payload and payload["json_schema"] != existing.json_schema
        prompt_changed = "system_prompt" in payload and payload["system_prompt"] != existing.system_prompt
        if schema_changed and "system_prompt" not in payload:
            payload["system_prompt"] = self._compose_system_prompt(
                grant_id=grant_id,
                template_id=template_id,
                section_id=section_id,
                section_name=existing.name,
                schema_json=payload.get("json_schema", existing.json_schema),
                existing_prompt=existing.system_prompt,
            )
            prompt_changed = payload["system_prompt"] != existing.system_prompt
        if schema_changed or prompt_changed:
            current_version = existing.current_version or 0
            new_version = current_version + 1
            await self._insert_section_schema_version(
                section_id=section_id,
                template_id=template_id,
                grant_id=grant_id,
                version=new_version,
                json_schema=payload.get("json_schema", existing.json_schema),
                system_prompt=payload.get("system_prompt", existing.system_prompt),
            )
            payload["current_version"] = new_version
        response = (
            self.client
            .from_("sections")
            .update(payload)
            .eq("id", section_id)
            .eq("template_id", template_id)
            .eq("grant_id", grant_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def _insert_section_schema_version(
        self,
        *,
        section_id: str,
        template_id: str,
        grant_id: str,
        version: int,
        json_schema: Optional[Dict[str, Any]],
        system_prompt: Optional[str],
        created_by: Optional[str] = None,
    ) -> None:
        """插入章節 Schema 版本記錄。"""
        # 檢查版本是否已存在以避免重複插入
        def check_version_exists():
            response = (
                self.client
                .from_("section_schema_versions")
                .select("id")
                .eq("section_id", section_id)
                .eq("template_id", template_id)
                .eq("grant_id", grant_id)
                .eq("version", version)
                .execute()
            )
            return len(response.data) > 0

        version_exists = await asyncio.to_thread(check_version_exists)
        if version_exists:
            # 版本已存在，跳過插入
            return

        payload: Dict[str, Any] = {
            "section_id": section_id,
            "template_id": template_id,
            "grant_id": grant_id,
            "version": version,
            "json_schema": json_schema,
            "system_prompt": system_prompt,
        }
        if created_by:
            payload["created_by"] = created_by
        await asyncio.to_thread(
            lambda: self.client.from_("section_schema_versions").insert(payload).execute()
        )

    def _compose_system_prompt(
        self,
        *,
        grant_id: str,
        template_id: str,
        section_id: str,
        section_name: Optional[str],
        schema_json: Optional[Dict[str, Any]],
        existing_prompt: Optional[str] = None,
    ) -> str:
        example_structure = self._schema_to_description_example(schema_json)
        schema_str = json.dumps(example_structure, ensure_ascii=False, indent=2)
        if existing_prompt:
            block_start = existing_prompt.find("```json")
            if block_start != -1:
                block_end = existing_prompt.find("```", block_start + len("```json"))
                if block_end != -1:
                    prefix = existing_prompt[:block_start].rstrip()
                    suffix = existing_prompt[block_end + 3 :].lstrip()
                    parts = [part for part in [prefix, f"```json\n{schema_str}\n```", suffix] if part]
                    return "\n\n".join(parts).strip()

        section_label = section_name or section_id or "指定章節"
        base_intro = (
            f"你是一位頂尖的政府補助案計畫書撰寫專家。你的任務是為一份主題爲「{grant_id}」，模板為 「{template_id}」的計畫書，生成「{section_label}」章節的內容。\n\n"
            "請嚴格依照以下 JSON Schema 結構與說明進行輸出，除了 JSON 物件本身，不得包含任何額外的說明、開頭、或結尾文字。"
        )
        return f"{base_intro}\n\n```json\n{schema_str}\n```".strip()

    def _schema_to_description_example(self, schema_json: Optional[Dict[str, Any]]) -> Any:
        """將 JSON Schema 轉為僅保留描述文字的示例結構。"""
        if not schema_json:
            return {}

        schema_type = (schema_json.get("type") or "object").lower()

        if schema_type == "object":
            properties = schema_json.get("properties") or {}
            if properties:
                return {
                    key: self._schema_to_description_example(value)
                    for key, value in properties.items()
                }
            desc = schema_json.get("description") or schema_json.get("title")
            return desc or {}

        if schema_type == "array":
            items = schema_json.get("items")
            if items:
                return [self._schema_to_description_example(items)]
            desc = schema_json.get("description") or schema_json.get("title")
            return [desc] if desc else []

        return (
            schema_json.get("description")
            or schema_json.get("title")
            or "請填寫此欄位內容。"
        )

    async def delete_section_record(self, section_id: str, template_id: str, grant_id: str) -> bool:
        """刪除指定章節。"""
        response = (
            self.client
            .from_("sections")
            .delete()
            .eq("id", section_id)
            .eq("template_id", template_id)
            .eq("grant_id", grant_id)
            .execute()
        )
        return len(response.data) > 0


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
        """获取所有計畫草稿"""
        response = self.client.from_("draft_plans").select("*").order("created_at", desc=True).execute()
        return response.data if response.data else []

    async def create_draft_plan(self, name: str, mode: str, grant_id: Optional[str] = None, template_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """创建一个新的計畫草稿"""
        
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
        """更新一个計畫草稿"""
        if "updated_at" not in data:
            # 设置为东八区时间
            tz = timezone(timedelta(hours=8))
            data["updated_at"] = datetime.now(tz).strftime('%Y-%m-%dT%H:%M:%S%z')

        response = self.client.from_("draft_plans").update(data).eq("id", draft_id).execute()
        return response.data[0] if response.data else None

    async def delete_draft_plan(self, draft_id: str) -> bool:
        """删除一个計畫草稿"""
        response = self.client.from_("draft_plans").delete().eq("id", draft_id).execute()
        return len(response.data) > 0

    async def _get_section_current_versions(self, grant_id: Optional[str], template_id: Optional[str]) -> Dict[str, int]:
        """
        獲取指定 grant 和 template 下所有 sections 的當前版本號。
        返回格式：{ "section_id": version_number, ... }
        """
        if not grant_id or not template_id:
            return {}
        
        try:
            # 從 sections 表獲取所有屬於此 grant+template 的 section
            sections_response = (
                self.client.from_("sections")
                .select("id, current_version")
                .eq("grant_id", grant_id)
                .eq("template_id", template_id)
                .execute()
            )
            
            if not sections_response.data:
                return {}
            
            # 構建版本號映射表
            section_versions = {}
            for section in sections_response.data:
                section_id = section.get("id")
                current_version = section.get("current_version")
                if section_id and current_version:
                    section_versions[section_id] = current_version
            
            return section_versions
        except Exception as error:
            logger.error(
                "Failed to get section versions for grant %s, template %s: %s",
                grant_id,
                template_id,
                error,
                exc_info=True,
            )
            return {}

    async def get_section_version_overrides(
        self,
        *,
        grant_id: Optional[str],
        template_id: Optional[str],
        section_versions: Optional[Dict[str, int]],
    ) -> Dict[str, Dict[str, Any]]:
        """取得指定章節版本對應的 schema 與 prompt 設定。"""
        if not grant_id or not template_id or not section_versions:
            return {}

        overrides: Dict[str, Dict[str, Any]] = {}
        for section_id, version in section_versions.items():
            if not section_id or version is None:
                continue
            try:
                response = (
                    self.client.from_("section_schema_versions")
                    .select("section_id, version, json_schema, system_prompt")
                    .eq("grant_id", grant_id)
                    .eq("template_id", template_id)
                    .eq("section_id", section_id)
                    .eq("version", version)
                    .limit(1)
                    .execute()
                )
                if response.data:
                    overrides[section_id] = response.data[0]
            except Exception as error:
                logger.error(
                    "Failed to fetch schema version for %s/%s/%s@%s: %s",
                    grant_id,
                    template_id,
                    section_id,
                    version,
                    error,
                    exc_info=True,
                )
        return overrides

    async def hydrate_section_configs_with_versions(
        self,
        *,
        sections: List[SectionConfig],
        grant_id: str,
        template_id: str,
        section_versions: Optional[Dict[str, int]],
    ) -> List[SectionConfig]:
        """將指定 sections 套用歷史版本 schema/prompt。"""
        overrides = await self.get_section_version_overrides(
            grant_id=grant_id,
            template_id=template_id,
            section_versions=section_versions,
        )
        if not overrides:
            return sections

        hydrated: List[SectionConfig] = []
        for section in sections:
            override = overrides.get(section.id)
            if not override:
                hydrated.append(section)
                continue

            payload = section.model_dump()
            if override.get("json_schema") is not None:
                payload["json_schema"] = override["json_schema"]
            if override.get("system_prompt") is not None:
                payload["system_prompt"] = override["system_prompt"]
            payload["current_version"] = override.get("version") or (section_versions or {}).get(section.id)
            hydrated.append(SectionConfig(**payload))

        return hydrated

    async def hydrate_section_payloads_with_versions(
        self,
        *,
        sections: List[Dict[str, Any]],
        grant_id: str,
        template_id: str,
        section_versions: Optional[Dict[str, int]],
    ) -> List[Dict[str, Any]]:
        """將原始 section 字典套用歷史版本資訊，供 API 回傳使用。"""
        overrides = await self.get_section_version_overrides(
            grant_id=grant_id,
            template_id=template_id,
            section_versions=section_versions,
        )
        if not overrides:
            return sections

        hydrated: List[Dict[str, Any]] = []
        for section in sections:
            section_id = section.get("id")
            override = overrides.get(section_id)
            if not override:
                hydrated.append(section)
                continue

            payload = {**section}
            if override.get("json_schema") is not None:
                payload["json_schema"] = override["json_schema"]
            if override.get("system_prompt") is not None:
                payload["system_prompt"] = override["system_prompt"]
            payload["applied_version"] = override.get("version") or (section_versions or {}).get(section_id)
            hydrated.append(payload)

        return hydrated

    async def create_project_record(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        在 projects 表中新增一筆記錄。
        自動記錄當前的 section 版本號到 section_versions 欄位。
        """
        # 獲取當前的 section 版本號
        grant_id = data.get("grant_id")
        template_id = data.get("template_id")
        section_versions = await self._get_section_current_versions(grant_id, template_id)
        
        # 添加版本號資訊到 data
        data["section_versions"] = section_versions
        
        response = (
            self.client.from_("projects")
            .insert({k: v for k, v in data.items() if v is not None})
            .execute()
        )
        return response.data[0] if response.data else None

    async def get_project_by_id(self, project_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """取得單一專案。若提供 user_id，則只返回該使用者擁有的專案。排除已刪除的專案。"""
        try:
            query = (
                self.client.from_("projects")
                .select("*")
                .eq("id", project_id)
                .eq("is_deleted", False)
            )
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = query.single().execute()
            return response.data if response.data else None
        except Exception as error:
            logger.error("Failed to fetch project %s: %s", project_id, error, exc_info=True)
            return None

    async def get_projects_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """取得指定使用者的所有專案（排除已刪除的），依更新時間排序。補充 grant/template 顯示資訊。"""
        response = (
            self.client.from_("projects")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_deleted", False)
            .order("updated_at", desc=True)
            .execute()
        )
        
        if not response.data:
            return []
        
        # 獲取所有 grants 配置以查詢 grant name 和 template name
        all_grants = await self.get_all_grants_config()
        
        # 建立快速查詢表：{grant_id: grant_config}
        grants_lookup = {g.id: g for g in all_grants}
        
        # 建立快速查詢表：{(grant_id, template_id): template_config}
        templates_lookup = {}
        for grant in all_grants:
            for template in grant.templates:
                templates_lookup[(grant.id, template.id)] = template
        
        # 為每個專案補充 grant_name、template_name 和 template_icon_bg
        projects = response.data
        for project in projects:
            grant_id = project.get("grant_id")
            template_id = project.get("template_id")
            
            # 從查詢表中找到對應的 grant name 和 template name
            if grant_id and grant_id in grants_lookup:
                project["grant_name"] = grants_lookup[grant_id].name
            else:
                project["grant_name"] = None
            
            if grant_id and template_id and (grant_id, template_id) in templates_lookup:
                project["template_name"] = templates_lookup[(grant_id, template_id)].name
                project["template_icon_bg"] = templates_lookup[(grant_id, template_id)].iconBg
            else:
                project["template_name"] = None
                project["template_icon_bg"] = None
        
        return projects

    async def update_project_record(self, project_id: str, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新指定專案（只有擁有者能更新）。
        注意：section_versions 是在項目創建時的版本快照，不應在更新時自動改變。
        如需更改 section_versions，必須明確傳入。
        """
        # 不要自動更新 section_versions - 它應該保持為創建時的版本快照
        # 只有當明確在 data 中傳入 section_versions 時，才會更新
        
        response = (
            self.client.from_("projects")
            .update({k: v for k, v in data.items() if v is not None})
            .eq("id", project_id)
            .eq("user_id", user_id)
            .execute()
        )
        return response.data[0] if response.data else None

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

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if not email:
            return None
        try:
            response = (
                self.client.from_("users")
                .select("*")
                .eq("email", email)
                .limit(1)
                .execute()
            )
            rows = response.data or []
            return rows[0] if rows else None
        except Exception:
            logger.warning("Failed to query user by email", exc_info=True)
            return None

    async def _is_internal_email(self, email: Optional[str]) -> bool:
        if not email:
            return False
        try:
            result = (
                self.client.from_("whitelist")
                .select("role")
                .eq("email", email)
                .limit(1)
                .execute()
            )
            rows = result.data or []
            row = rows[0] if rows else None
            return bool(row and row.get("role") == "internal")
        except Exception:
            logger.warning("Failed to check internal email in whitelist", exc_info=True)
            return False

    async def resolve_or_create_user_by_supabase_identity(
        self,
        *,
        auth_user_id: str,
        email: Optional[str],
    ) -> Dict[str, Any]:
        """
        依 Supabase Auth 身分解析（或建立）對應的系統使用者。

        保證事項：
        - public.users 一定存在對應紀錄。
        - provider='supabase' 的 public.user_identities 映射一定存在。
        - 會依 whitelist 的內部帳號規則同步 users.role。
        - 若找不到身分映射，會以 email 嘗試合併既有帳號以避免重複。
        """
        try:
            identity_resp = (
                self.client.from_("user_identities")
                .select("user_id,email")
                .eq("provider", "supabase")
                .eq("provider_subject", auth_user_id)
                .limit(1)
                .execute()
            )
            identity_rows = identity_resp.data or []
            identity = identity_rows[0] if identity_rows else None
        except Exception:
            logger.warning("Failed to query user identity mapping", exc_info=True)
            identity = None

        user_row: Optional[Dict[str, Any]] = None
        if identity and identity.get("user_id"):
            user_row = await self.get_user_by_id(identity["user_id"])

        # 若查無身分映射，改用 email 嘗試關聯既有 canonical user。
        if not user_row and email:
            user_row = await self.get_user_by_email(email)

        if not user_row:
            preferred_email = email
            insert_payload = {
                "email": preferred_email,
                "role": "normal",
                "auth_source": "supabase",
                "status": "active",
                "last_login_at": datetime.now(timezone.utc).isoformat(),
            }

            inserted = self.client.from_("users").insert(insert_payload).execute()

            if not inserted.data:
                raise ValueError("Failed to create canonical user record")
            user_row = inserted.data[0]

        # 僅在映射資料變動時才 upsert，避免每次請求都寫入造成延遲。
        mapped_email = email or user_row.get("email")
        if (not identity) or identity.get("email") != mapped_email or identity.get("user_id") != user_row.get("id"):
            self.client.from_("user_identities").upsert(
                {
                    "user_id": user_row["id"],
                    "provider": "supabase",
                    "provider_subject": auth_user_id,
                    "email": mapped_email,
                },
                on_conflict="provider,provider_subject",
            ).execute()

        is_internal = await self._is_internal_email(email)
        target_role = "internal" if is_internal else (user_row.get("role") or "normal")

        update_payload: Dict[str, Any] = {}
        now_dt = datetime.now(timezone.utc)

        if user_row.get("auth_source") != "supabase":
            update_payload["auth_source"] = "supabase"

        try:
            last_login_raw = user_row.get("last_login_at")
            last_login_dt = None
            if isinstance(last_login_raw, str) and last_login_raw:
                last_login_dt = datetime.fromisoformat(last_login_raw.replace("Z", "+00:00"))
            if not last_login_dt or (now_dt - last_login_dt) >= timedelta(minutes=10):
                update_payload["last_login_at"] = now_dt.isoformat()
        except Exception:
            update_payload["last_login_at"] = now_dt.isoformat()

        if user_row.get("role") != target_role:
            update_payload["role"] = target_role

        if update_payload:
            updated = (
                self.client.from_("users")
                .update(update_payload)
                .eq("id", user_row["id"])
                .execute()
            )
            if updated.data:
                return updated.data[0]
        return await self.get_user_by_id(user_row["id"]) or user_row

    async def ensure_canonical_user_id(self, user_id: Optional[str]) -> Optional[str]:
        """
        將輸入的 user_id 正規化為 public.users.id。

        - 若本身已是 users.id，直接回傳。
        - 若為 Supabase Auth UID，透過 user_identities 轉換。
        - 若無法解析，回傳 None 以維持外鍵安全寫入。
        """
        if not user_id:
            return None

        existing = await self.get_user_by_id(user_id)
        if existing:
            return user_id

        try:
            response = (
                self.client.from_("user_identities")
                .select("user_id")
                .eq("provider", "supabase")
                .eq("provider_subject", user_id)
                .limit(1)
                .execute()
            )
            rows = response.data or []
            mapped_user_id = rows[0].get("user_id") if rows else None
            if mapped_user_id:
                return mapped_user_id
        except Exception:
            logger.warning("Failed to map user_id to canonical users.id", exc_info=True)

        logger.warning("Unresolvable user_id '%s'; storing NULL for FK-safe log write", user_id)
        return None

    async def resolve_or_create_user_by_external_identity(
        self,
        *,
        provider: str,
        provider_subject: str,
        email: Optional[str],
        role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        依外部 OAuth 身分解析（或建立）對應的系統使用者。

        保證事項：
        - public.users 一定存在對應紀錄。
        - 指定 provider/provider_subject 的 user_identities 映射一定存在。
        - 除非明確提供合法 role，否則保留原有角色設定。
        """
        try:
            identity_resp = (
                self.client.from_("user_identities")
                .select("user_id,email")
                .eq("provider", provider)
                .eq("provider_subject", provider_subject)
                .limit(1)
                .execute()
            )
            identity_rows = identity_resp.data or []
            identity = identity_rows[0] if identity_rows else None
        except Exception:
            logger.warning("Failed to query external user identity mapping", exc_info=True)
            identity = None

        user_row: Optional[Dict[str, Any]] = None
        if identity and identity.get("user_id"):
            user_row = await self.get_user_by_id(identity["user_id"])

        if not user_row and email:
            user_row = await self.get_user_by_email(email)

        normalized_role = role if role in {"normal", "internal", "vip"} else None

        if not user_row:
            placeholder = f"{provider}-{provider_subject}@placeholder.local"
            preferred_email = email or placeholder
            insert_payload = {
                "email": preferred_email,
                "role": normalized_role or "normal",
                # users.auth_source 只記錄來源類型；provider 細節保存在 user_identities。
                "auth_source": "external",
                "status": "active",
                "last_login_at": datetime.now(timezone.utc).isoformat(),
            }
            
            inserted = self.client.from_("users").insert(insert_payload).execute()

            if not inserted.data:
                raise ValueError("Failed to create canonical user record for external identity")
            user_row = inserted.data[0]

        mapped_email = email or user_row.get("email")
        if (not identity) or identity.get("email") != mapped_email or identity.get("user_id") != user_row.get("id"):
            self.client.from_("user_identities").upsert(
                {
                    "user_id": user_row["id"],
                    "provider": provider,
                    "provider_subject": provider_subject,
                    "email": mapped_email,
                },
                on_conflict="provider,provider_subject",
            ).execute()

        update_payload: Dict[str, Any] = {
            "last_login_at": datetime.now(timezone.utc).isoformat(),
        }
        if user_row.get("auth_source") != "external":
            update_payload["auth_source"] = "external"
        if normalized_role and user_row.get("role") != "internal" and user_row.get("role") != normalized_role:
            update_payload["role"] = normalized_role

        updated = (
            self.client.from_("users")
            .update(update_payload)
            .eq("id", user_row["id"])
            .execute()
        )
        if updated.data:
            return updated.data[0]
        return await self.get_user_by_id(user_row["id"]) or user_row

    async def get_user_usage(self, user_id: str) -> Dict[str, int]:
        """获取用户的 internal 和 external 总用量"""
        query = self.client.from_("usage_logs").select("model_type, cost").eq("user_id", user_id)
        response = query.execute()
        
        usage = 0
        if response.data:
            for log in response.data:
                usage += log['cost']
        return usage

    async def log_usage(self, user_id: str, model_info: Dict[str, Any], input_token: int, output_token: int, project_id: Optional[str] = None, action: Optional[str] = None):
        """记录一次模型使用"""
        canonical_user_id = await self.ensure_canonical_user_id(user_id)

        model_type = model_info.get('type', 'internal') 
        cost = 0.0
        # 简单估算成本，只用external modal 的 output token
        if model_type == 'external' and model_info.get('cost_info'):
            cost_per_million = model_info['cost_info'].get('output', 0)
            cost = (output_token / 1_000_000) * cost_per_million

        new_log = {
            "user_id": canonical_user_id,
            "model_id": model_info['id'],
            "model_type": model_type,
            "input_token": input_token,
            "output_token":  output_token,
            "cost": cost,
        }
        
        if project_id:
            new_log["project_id"] = project_id
        if action:
            new_log["action"] = action
        
        self.client.from_("usage_logs").insert(new_log).execute()
        print(f"Logged usage for user {canonical_user_id or 'NULL'}: ${cost} for {model_type} model.")

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

    async def get_execution_logs(
        self,
        project_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch execution log entries for a project within an optional time window."""

        query = (
            self.client
            .from_("execution_logs")
            .select("*")
            .eq("project_id", project_id)
            .order("created_at", desc=False)
        )

        if start_time:
            query = query.gte("created_at", start_time)
        if end_time:
            query = query.lte("created_at", end_time)

        response = await asyncio.to_thread(query.execute)
        return response.data or []

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
                existing = await self.get_section_details(grant_id, template_id, section_id)
                if not existing:
                    return False
                if system_prompt != existing.system_prompt:
                    current_version = existing.current_version or 0
                    new_version = current_version + 1
                    await self._insert_section_schema_version(
                        section_id=section_id,
                        template_id=template_id,
                        grant_id=grant_id,
                        version=new_version,
                        json_schema=existing.json_schema,
                        system_prompt=system_prompt,
                    )
                    update_data["current_version"] = new_version
                    
                    # 同時更新 section_schema_version 表中最新版本的 system_prompt
                    try:
                        self.client.from_("section_schema_versions").update(
                            {"system_prompt": system_prompt}
                        ).eq("grant_id", grant_id).eq("template_id", template_id).eq("section_id", section_id).eq("version", new_version).execute()
                    except Exception as version_update_error:
                        logger.warning(
                            "Failed to update system_prompt in section_schema_versions for %s/%s/%s@%s: %s",
                            grant_id,
                            template_id,
                            section_id,
                            new_version,
                            version_update_error,
                        )
                
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
        
    async def log_cost_usage(self, user_id: str, model_to_use: Dict, response_json: Dict, project_id: Optional[str] = None, action: Optional[str] = None):
        """記錄模型使用成本。從 API 響應中直接提取 token 計數。
        
        支持 OpenAI 和 Gemini 的响应格式：
        - OpenAI (非流式): response_json['usage']['input_tokens'] 和 ['output_tokens']
        - OpenAI (流式): response_json['usage']['prompt_tokens'] 和 ['completion_tokens']
        - Gemini: response_json['usageMetadata']['promptTokenCount'] 和 ['candidatesTokenCount']
        """
        input_token = 0
        output_token = 0
        
        provider = model_to_use.get('provider', 'unknown')
        
        try:
            if provider == 'openai':
                # OpenAI 格式（同時支援流式和非流式）
                usage = response_json.get('usage', {})
                print(usage)
                # 優先使用 input_tokens/output_tokens（非流式），如果沒有則使用 prompt_tokens/completion_tokens（流式）
                input_token = usage.get('input_tokens') or usage.get('prompt_tokens', 0)
                output_token = usage.get('output_tokens') or usage.get('completion_tokens', 0)
            elif provider == 'gemini':
                # Gemini 格式
                usage = response_json.get('usageMetadata', {})
                print(usage)
                input_token = usage.get('promptTokenCount', 0)
                output_token = usage.get('candidatesTokenCount', 0)
            else:
                # Ollama 或其他提供者可能有不同的格式
                usage = response_json.get('usage', {})
                input_token = usage.get('input_tokens', usage.get('prompt_tokens', 0))
                output_token = usage.get('output_tokens', usage.get('completion_tokens', 0))
        except Exception as e:
            logger.error(f"Failed to extract token counts from response: {e}", exc_info=True)
            return
        
        asyncio.create_task(self.log_usage(user_id, model_to_use, input_token, output_token, project_id=project_id, action=action))

    async def get_daily_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """
        獲取使用者當日的統計數據 (台北時間 UTC+8)。
        包含：今日建立的專案數、今日消耗的總 token 數。
        """
        from app.config import THROTTLING_PROJECT_THRESHOLD

        # 取得台北時間今日 00:00:00
        tz_taipei = timezone(timedelta(hours=8))
        now_taipei = datetime.now(tz_taipei)
        today_start = now_taipei.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_iso = today_start.isoformat()

        # 1. 統計今日建立的專案數 (排除已刪除)
        projects_resp = (
            self.client.from_("projects")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .gte("created_at", today_start_iso)
            .execute()
        )
        projects_today = projects_resp.count or 0

        # 2. 統計今日使用的 Token 數
        usage_resp = (
            self.client.from_("usage_logs")
            .select("input_token, output_token")
            .eq("user_id", user_id)
            .gte("created_at", today_start_iso)
            .execute()
        )
        
        total_tokens = 0
        if usage_resp.data:
            for log in usage_resp.data:
                total_tokens += (log.get("input_token") or 0) + (log.get("output_token") or 0)

        return {
            "projects_today": projects_today,
            "total_tokens_today": total_tokens,
            "needs_throttling": projects_today > THROTTLING_PROJECT_THRESHOLD
        }

    async def check_project_slot_availability(self, user_id: str, role: str) -> bool:
        """
        檢查使用者是否還能建立新專案。
        - normal: 只能有 1 個非刪除專案。
        - vip/internal: 依配置上限 (目前配置為 50)。
        """
        from app.config import SLOT_NORMAL_MAX_PROJECTS, SLOT_VIP_MAX_PROJECTS

        # 獲取所有非刪除的專案總數
        resp = (
            self.client.from_("projects")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("is_deleted", False)
            .execute()
        )
        active_count = resp.count or 0

        limit = SLOT_NORMAL_MAX_PROJECTS
        if role in ("vip", "internal"):
            limit = SLOT_VIP_MAX_PROJECTS

        return active_count < limit

    async def is_latest_project(self, user_id: str, project_id: str) -> bool:
        """
        檢查指定的 project_id 是否為該使用者最新建立且未刪除的專案。
        用於 Normal 使用者降級後的編輯權限判斷。
        """
        resp = (
            self.client.from_("projects")
            .select("id")
            .eq("user_id", user_id)
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        if not resp.data:
            return False
        
        return str(resp.data[0]["id"]) == str(project_id)

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

    async def list_user_commands(self, user_id: str) -> List[Dict[str, Any]]:
        """取得指定使用者的所有 commands，依 last_updated 由新到舊排序。"""
        if not user_id:
            return []
        response = (
            self.client.from_("commands")
            .select("*")
            .eq("user_id", user_id)
            .order("last_updated", desc=True)
            .execute()
        )
        return response.data or []

    async def create_user_command(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """為指定使用者建立 command。"""
        if not user_id:
            return None
        payload = {k: v for k, v in data.items() if v is not None}
        payload["user_id"] = user_id
        response = self.client.from_("commands").insert(payload).execute()
        return response.data[0] if response.data else None

    async def update_user_command(
        self,
        command_id: str,
        user_id: str,
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """更新指定使用者擁有的 command。"""
        if not command_id or not user_id:
            return None
        payload = {k: v for k, v in data.items() if v is not None}
        response = (
            self.client.from_("commands")
            .update(payload)
            .eq("id", command_id)
            .eq("user_id", user_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def delete_user_command(self, command_id: str, user_id: str) -> bool:
        """刪除指定使用者擁有的 command。"""
        if not command_id or not user_id:
            return False
        response = (
            self.client.from_("commands")
            .delete()
            .eq("id", command_id)
            .eq("user_id", user_id)
            .execute()
        )
        return len(response.data or []) > 0

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
