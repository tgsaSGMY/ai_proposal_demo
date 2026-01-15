import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.supabase_service import SupabaseService
from .dependencies import get_supabase_service, verify_internal_user


logger = logging.getLogger(__name__)


router = APIRouter(
	prefix="/api/dynamic-sections",
	tags=["Dynamic Sections"],
)


class DynamicFieldModel(BaseModel):
	id: str
	section_id: str
	field_key: str
	title: str
	description: Optional[str] = ""
	order: int


class DynamicSectionModel(BaseModel):
	id: str
	schema_id: Optional[str] = None
	template_id: Optional[str] = None
	template_grant_id: Optional[str] = None
	section_key: str
	title: str
	order: int
	fields: List[DynamicFieldModel] = Field(default_factory=list)


class SectionCreateUpdate(BaseModel):
	schema_id: Optional[str] = Field("default", description="Schema identifier, default is 'default'.")
	template_id: Optional[str] = Field(None, description="Plan template id this section belongs to.")
	template_grant_id: Optional[str] = Field(None, description="Grant id that pairs with template_id.")
	section_key: str = Field(..., description="Unique key for this section within a schema.")
	title: str = Field(..., description="Display title of the section.")
	order: int = Field(..., description="Display order of the section.")


class FieldCreateUpdate(BaseModel):
	section_id: str = Field(..., description="Parent section id.")
	field_key: str = Field(..., description="Unique key of the field within a section.")
	title: str = Field(..., description="Display title of the field.")
	description: Optional[str] = Field("", description="Long description of the field.")
	order: int = Field(..., description="Display order of the field within a section.")


@router.get("", response_model=List[DynamicSectionModel], summary="取得指定 schema 或 template 的所有章節與欄位")
async def get_dynamic_schema(
	template_id: Optional[str] = None,
	template_grant_id: Optional[str] = None,
	schema_id: str = "default",
	supabase_service: SupabaseService = Depends(get_supabase_service)
):
	"""回傳指定 schema 的章節列表，包含底下的所有欄位。

	這裡直接使用 SupabaseService 上的 client（使用 service key），
	繞過 RLS 方便後台管理，但仍透過 verify_internal_user 限制為內部人員。
	"""
	# 根據 template 或 schema ID 查詢動態章節資料，並返回完整的章節和欄位結構

	try:
		query = (
			supabase_service.client
			.from_("dynamic_sections")
			.select("*")
		)
		if template_id:
			query = query.eq("template_id", template_id)
			if template_grant_id:
				query = query.eq("template_grant_id", template_grant_id)
		else:
			query = query.eq("schema_id", schema_id)

		sections_resp = query.order("order", desc=False).execute()

		sections_data = sections_resp.data or []
		if not sections_data:
			return []

		section_ids = [s["id"] for s in sections_data]

		fields_resp = (
			supabase_service.client
			.from_("dynamic_fields")
			.select("*")
			.in_("section_id", section_ids)
			.order("order", desc=False)
			.execute()
		)

		fields_data = fields_resp.data or []
		fields_by_section: dict[str, List[DynamicFieldModel]] = {}
		for f in fields_data:
			model = DynamicFieldModel(
				id=f["id"],
				section_id=f["section_id"],
				field_key=f["field_key"],
				title=f["title"],
				description=f.get("description") or "",
				order=f["order"],
			)
			fields_by_section.setdefault(model.section_id, []).append(model)

		result: List[DynamicSectionModel] = []
		for s in sections_data:
			section_fields = sorted(
				fields_by_section.get(s["id"], []), key=lambda f: f.order
			)
			result.append(
				DynamicSectionModel(
					id=s["id"],
					schema_id=s.get("schema_id"),
					template_id=s.get("template_id"),
					template_grant_id=s.get("template_grant_id"),
					section_key=s["section_key"],
					title=s["title"],
					order=s["order"],
					fields=section_fields,
				)
			)

		return result

	except Exception as e:
		logger.error("Failed to fetch dynamic schema: %s", e, exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to fetch dynamic schema")


@router.post(
	"/sections",
	response_model=DynamicSectionModel,
	status_code=status.HTTP_201_CREATED,
	summary="新增一個章節",
)
async def create_section(
	payload: SectionCreateUpdate,
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	# 創建新的動態章節，包含所有必要的元數據（schema、template、標題、排序等）
	try:
		insert_resp = (
			supabase_service.client
			.from_("dynamic_sections")
			.insert(
				{
					"schema_id": payload.schema_id,
					"template_id": payload.template_id,
					"template_grant_id": payload.template_grant_id,
					"section_key": payload.section_key,
					"title": payload.title,
					"order": payload.order,
				}
			)
			.execute()
		)

		if not insert_resp.data:
			raise HTTPException(status_code=500, detail="Failed to create section")

		row = insert_resp.data[0]
		return DynamicSectionModel(
			id=row["id"],
			schema_id=row.get("schema_id"),
			template_id=row.get("template_id"),
			template_grant_id=row.get("template_grant_id"),
			section_key=row["section_key"],
			title=row["title"],
			order=row["order"],
			fields=[],
		)
	except HTTPException:
		raise
	except Exception as e:
		logger.error("Failed to create section: %s", e, exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to create section")


@router.put(
	"/sections/{section_id}",
	response_model=DynamicSectionModel,
	summary="更新一個章節",
)
async def update_section(
	section_id: str,
	payload: SectionCreateUpdate,
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	# 更新指定章節的資料，包括標題、排序、template 關聯等信息
	try:
		update_resp = (
			supabase_service.client
			.from_("dynamic_sections")
			.update(
				{
					"schema_id": payload.schema_id,
					"template_id": payload.template_id,
					"template_grant_id": payload.template_grant_id,
					"section_key": payload.section_key,
					"title": payload.title,
					"order": payload.order,
				}
			)
			.eq("id", section_id)
			.execute()
		)

		if not update_resp.data:
			raise HTTPException(status_code=404, detail="Section not found")

		row = update_resp.data[0]

		fields_resp = (
			supabase_service.client
			.from_("dynamic_fields")
			.select("*")
			.eq("section_id", section_id)
			.order("order", desc=False)
			.execute()
		)
		fields_data = fields_resp.data or []
		fields = [
			DynamicFieldModel(
				id=f["id"],
				section_id=f["section_id"],
				field_key=f["field_key"],
				title=f["title"],
				description=f.get("description") or "",
				order=f["order"],
			)
			for f in fields_data
		]

		return DynamicSectionModel(
			id=row["id"],
			schema_id=row.get("schema_id"),
			template_id=row.get("template_id"),
			template_grant_id=row.get("template_grant_id"),
			section_key=row["section_key"],
			title=row["title"],
			order=row["order"],
			fields=fields,
		)
	except HTTPException:
		raise
	except Exception as e:
		logger.error("Failed to update section %s: %s", section_id, e, exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to update section")


@router.delete(
	"/sections/{section_id}",
	status_code=status.HTTP_200_OK,
	summary="刪除一個章節（會同時刪除底下欄位）",
)
async def delete_section(
	section_id: str,
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	# 刪除指定章節及其所有子欄位，執行級聯刪除操作
	try:
		delete_resp = (
			supabase_service.client
			.from_("dynamic_sections")
			.delete()
			.eq("id", section_id)
			.execute()
		)

		if not delete_resp.data:
			raise HTTPException(status_code=404, detail="Section not found")

		return {"message": "Section deleted successfully"}
	except HTTPException:
		raise
	except Exception as e:
		logger.error("Failed to delete section %s: %s", section_id, e, exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to delete section")


@router.post(
	"/fields",
	response_model=DynamicFieldModel,
	status_code=status.HTTP_201_CREATED,
	summary="新增一個欄位",
)
async def create_field(
	payload: FieldCreateUpdate,
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	# 在指定章節下創建新的動態欄位，包含標題、描述、排序等信息
	try:
		insert_resp = (
			supabase_service.client
			.from_("dynamic_fields")
			.insert(
				{
					"section_id": payload.section_id,
					"field_key": payload.field_key,
					"title": payload.title,
					"description": payload.description,
					"order": payload.order,
				}
			)
			.execute()
		)

		if not insert_resp.data:
			raise HTTPException(status_code=500, detail="Failed to create field")

		row = insert_resp.data[0]
		return DynamicFieldModel(
			id=row["id"],
			section_id=row["section_id"],
			field_key=row["field_key"],
			title=row["title"],
			description=row.get("description") or "",
			order=row["order"],
		)
	except HTTPException:
		raise
	except Exception as e:
		logger.error("Failed to create field: %s", e, exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to create field")


@router.put(
	"/fields/{field_id}",
	response_model=DynamicFieldModel,
	summary="更新一個欄位",
)
async def update_field(
	field_id: str,
	payload: FieldCreateUpdate,
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	# 更新指定欄位的資料，包括標題、描述、所屬章節、排序等信息
	try:
		update_resp = (
			supabase_service.client
			.from_("dynamic_fields")
			.update(
				{
					"section_id": payload.section_id,
					"field_key": payload.field_key,
					"title": payload.title,
					"description": payload.description,
					"order": payload.order,
				}
			)
			.eq("id", field_id)
			.execute()
		)

		if not update_resp.data:
			raise HTTPException(status_code=404, detail="Field not found")

		row = update_resp.data[0]
		return DynamicFieldModel(
			id=row["id"],
			section_id=row["section_id"],
			field_key=row["field_key"],
			title=row["title"],
			description=row.get("description") or "",
			order=row["order"],
		)
	except HTTPException:
		raise
	except Exception as e:
		logger.error("Failed to update field %s: %s", field_id, e, exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to update field")


@router.delete(
	"/fields/{field_id}",
	status_code=status.HTTP_200_OK,
	summary="刪除一個欄位",
)
async def delete_field(
	field_id: str,
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	# 刪除指定欄位，從章節中移除此欄位定義
	try:
		delete_resp = (
			supabase_service.client
			.from_("dynamic_fields")
			.delete()
			.eq("id", field_id)
			.execute()
		)

		if not delete_resp.data:
			raise HTTPException(status_code=404, detail="Field not found")

		return {"message": "Field deleted successfully"}
	except HTTPException:
		raise
	except Exception as e:
		logger.error("Failed to delete field %s: %s", field_id, e, exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to delete field")

 