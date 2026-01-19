import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query

from app.api.dependencies import get_supabase_service, verify_internal_user
from app.models import (
	GrantCreateRequest,
	GrantUpdateRequest,
	PlanTemplateCreateRequest,
	PlanTemplateUpdateRequest,
)
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(
	prefix="/api/template-manager",
	tags=["Template Manager"],
)


async def _refresh_grant_cache(request: Request, supabase_service: SupabaseService) -> None:
	"""重新載入內存中的 Grant/Template 配置快取。"""
	try:
		request.app.state.all_grants_config = await supabase_service.get_all_grants_config()
	except Exception as exc:  # pragma: no cover - 非關鍵錯誤
		logger.warning("Failed to refresh grant cache after mutation: %s", exc)


@router.get(
	"/grants",
	response_model=List[Dict[str, Any]],
	summary="取得所有 Grants",
)
async def list_grants(
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	try:
		return await supabase_service.list_grants()
	except Exception as exc:
		logger.error("Failed to list grants: %s", exc, exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to retrieve grants")


@router.post(
	"/grants",
	status_code=status.HTTP_201_CREATED,
	response_model=Dict[str, Any],
	summary="新增 Grant",
)
async def create_grant(
	request: Request,
	payload: GrantCreateRequest,
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	try:
		existing = await supabase_service.get_grant_by_id(payload.id)
		if existing:
			raise HTTPException(status_code=409, detail="Grant ID already exists")

		record = await supabase_service.create_grant_record(payload.model_dump())
		if not record:
			raise HTTPException(status_code=500, detail="Failed to create grant")

		await _refresh_grant_cache(request, supabase_service)
		return record
	except HTTPException:
		raise
	except Exception as exc:
		logger.error("Failed to create grant %s: %s", payload.id, exc, exc_info=True)
		raise HTTPException(status_code=500, detail="Unexpected error while creating grant")


@router.put(
	"/grants/{grant_id}",
	response_model=Dict[str, Any],
	summary="更新 Grant",
)
async def update_grant(
	request: Request,
	grant_id: str,
	payload: GrantUpdateRequest,
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	update_data = payload.model_dump(exclude_none=True)
	if not update_data:
		raise HTTPException(status_code=400, detail="No fields provided for update")

	try:
		record = await supabase_service.update_grant_record(grant_id, update_data)
		if not record:
			raise HTTPException(status_code=404, detail="Grant not found")

		await _refresh_grant_cache(request, supabase_service)
		return record
	except HTTPException:
		raise
	except Exception as exc:
		logger.error("Failed to update grant %s: %s", grant_id, exc, exc_info=True)
		raise HTTPException(status_code=500, detail="Unexpected error while updating grant")


@router.get(
	"/templates",
	response_model=List[Dict[str, Any]],
	summary="取得計畫模板列表",
)
async def list_templates(
	grant_id: Optional[str] = Query(default=None),
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	try:
		return await supabase_service.list_plan_templates(grant_id)
	except Exception as exc:
		logger.error("Failed to list plan templates: %s", exc, exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to retrieve plan templates")


@router.post(
	"/templates",
	status_code=status.HTTP_201_CREATED,
	response_model=Dict[str, Any],
	summary="新增計畫模板",
)
async def create_template(
	request: Request,
	payload: PlanTemplateCreateRequest,
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	try:
		grant = await supabase_service.get_grant_by_id(payload.grant_id)
		if not grant:
			raise HTTPException(status_code=400, detail="Grant not found")

		existing = await supabase_service.get_template_by_id(payload.id, payload.grant_id)
		if existing:
			raise HTTPException(status_code=409, detail="Template ID already exists for this grant")

		record = await supabase_service.create_plan_template_record(payload.model_dump())
		if not record:
			raise HTTPException(status_code=500, detail="Failed to create template")

		await _refresh_grant_cache(request, supabase_service)
		return record
	except HTTPException:
		raise
	except Exception as exc:
		logger.error("Failed to create template %s/%s: %s", payload.grant_id, payload.id, exc, exc_info=True)
		raise HTTPException(status_code=500, detail="Unexpected error while creating template")


@router.put(
	"/templates/{grant_id}/{template_id}",
	response_model=Dict[str, Any],
	summary="更新計畫模板",
)
async def update_template(
	request: Request,
	grant_id: str,
	template_id: str,
	payload: PlanTemplateUpdateRequest,
	supabase_service: SupabaseService = Depends(get_supabase_service),
	_=Depends(verify_internal_user),
):
	update_data = payload.model_dump(exclude_none=True)
	if not update_data:
		raise HTTPException(status_code=400, detail="No fields provided for update")

	try:
		existing = await supabase_service.get_template_by_id(template_id, grant_id)
		if not existing:
			raise HTTPException(status_code=404, detail="Template not found")

		record = await supabase_service.update_plan_template_record(template_id, grant_id, update_data)
		if not record:
			raise HTTPException(status_code=404, detail="Template not found")

		await _refresh_grant_cache(request, supabase_service)
		return record
	except HTTPException:
		raise
	except Exception as exc:
		logger.error(
			"Failed to update template %s/%s: %s",
			grant_id,
			template_id,
			exc,
			exc_info=True,
		)
		raise HTTPException(status_code=500, detail="Unexpected error while updating template")
