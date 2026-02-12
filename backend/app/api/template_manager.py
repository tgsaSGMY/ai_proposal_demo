import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query, Form, UploadFile, File

from app.api.dependencies import get_supabase_service, verify_internal_user
from app.models import (
	GrantCreateRequest,
	GrantUpdateRequest,
	PlanTemplateCreateRequest,
	PlanTemplateUpdateRequest,
    SectionCreateRequest,
    SectionUpdateRequest,
)
from app.services.supabase_service import SupabaseService

SUPABASE_INTERNAL_BASE = "http://host.docker.internal:8000"
SUPABASE_PUBLIC_PROXY_BASE = "https://aiproposal.tgsa.com.tw/supabase"

logger = logging.getLogger(__name__)

router = APIRouter(
	prefix="/api/template-manager",
	tags=["Template Manager"],
)


def _normalize_logo_url(url: Optional[str]) -> Optional[str]:
    """將內部 Supabase URL 轉換成外部 HTTPS 代理網址。"""
    if not url:
        return url
    if url.startswith(SUPABASE_INTERNAL_BASE):
        return f"{SUPABASE_PUBLIC_PROXY_BASE}{url[len(SUPABASE_INTERNAL_BASE):]}"
    return url


def _extract_public_url(response: Any) -> Optional[str]:
    """兼容不同 SDK 版本的 get_public_url 回傳格式。"""
    if not response:
        return None
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        for key in ("publicUrl", "publicURL", "publicurl"):
            if response.get(key):
                return response[key]
        data = response.get("data")
        if isinstance(data, dict):
            for key in ("publicUrl", "publicURL", "publicurl"):
                if data.get(key):
                    return data[key]
    return None


def _with_cache_busting_token(url: Optional[str]) -> Optional[str]:
    """為公開網址加上時間戳，避免前端快取舊圖。"""
    if not url:
        return url
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "v"]
    query.append(("v", str(int(time.time()))))
    new_query = urlencode(query)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


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
			raise HTTPException(status_code=409, detail="Grant ID已经存在")

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
			raise HTTPException(status_code=400, detail="找不到指定的Grant")

		existing = await supabase_service.get_template_by_id(payload.id, payload.grant_id)
		if existing:
			raise HTTPException(status_code=409, detail="这个主题的模板 ID 已存在")

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


@router.get(
	"/templates/{grant_id}/{template_id}",
	response_model=Dict[str, Any],
	summary="取得計畫模板詳細資訊",
)
async def get_template(
	grant_id: str,
	template_id: str,
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
	try:
		record = await supabase_service.get_template_by_id(template_id, grant_id)
		if not record:
			raise HTTPException(status_code=404, detail="Template not found")
		return record
	except HTTPException:
		raise
	except Exception as exc:
		logger.error(
			"Failed to get template %s/%s: %s",
			grant_id,
			template_id,
			exc,
			exc_info=True,
		)
		raise HTTPException(status_code=500, detail="Unexpected error while retrieving template")


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


@router.get(
    "/sections",
    response_model=List[Dict[str, Any]],
    summary="取得指定模板的章節列表",
)
async def list_sections(
    grant_id: str = Query(..., description="Grant ID"),
    template_id: str = Query(..., description="Template ID"),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _: Any = Depends(verify_internal_user),
):
    try:
        return await supabase_service.get_sections_by_template_id(template_id, grant_id)
    except Exception as exc:
        logger.error(
            "Failed to list sections for %s/%s: %s", grant_id, template_id, exc, exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve sections")


@router.post(
    "/sections",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, Any],
    summary="新增章節",
)
async def create_section(
    request: Request,
    payload: SectionCreateRequest,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _: Any = Depends(verify_internal_user),
):
    template = await supabase_service.get_template_by_id(
        payload.template_id, payload.grant_id
    )
    if not template:
        raise HTTPException(status_code=400, detail="Template not found")

    existing = await supabase_service.get_section_details(
        payload.grant_id, payload.template_id, payload.id
    )
    if existing:
        raise HTTPException(status_code=409, detail="Section ID already exists")

    try:
        record = await supabase_service.create_section_record(payload.model_dump())
        if not record:
            raise HTTPException(status_code=500, detail="Failed to create section")

        await _refresh_grant_cache(request, supabase_service)
        return record
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to create section %s/%s/%s: %s",
            payload.grant_id,
            payload.template_id,
            payload.id,
            exc,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Unexpected error while creating section")


@router.put(
    "/sections/{grant_id}/{template_id}/{section_id}",
    response_model=Dict[str, Any],
    summary="更新章節",
)
async def update_section(
    request: Request,
    grant_id: str,
    template_id: str,
    section_id: str,
    payload: SectionUpdateRequest,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _: Any = Depends(verify_internal_user),
):
    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    existing = await supabase_service.get_section_details(grant_id, template_id, section_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Section not found")

    try:
        record = await supabase_service.update_section_record(
            section_id,
            template_id,
            grant_id,
            update_data,
        )
        if not record:
            raise HTTPException(status_code=404, detail="Section not found")

        await _refresh_grant_cache(request, supabase_service)
        return record
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to update section %s/%s/%s: %s",
            grant_id,
            template_id,
            section_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Unexpected error while updating section")


@router.delete(
    "/sections/{grant_id}/{template_id}/{section_id}",
    response_model=Dict[str, str],
    summary="刪除章節",
)
async def delete_section(
    request: Request,
    grant_id: str,
    template_id: str,
    section_id: str,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _: Any = Depends(verify_internal_user),
):
    try:
        deleted = await supabase_service.delete_section_record(section_id, template_id, grant_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Section not found")

        await _refresh_grant_cache(request, supabase_service)
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to delete section %s/%s/%s: %s",
            grant_id,
            template_id,
            section_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Unexpected error while deleting section")

@router.post(
    "/templates/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, Any],
    summary="新增計畫模板（含文件上傳）",
)
async def create_template_with_upload(
    request: Request,
    id: str = Form(...),
    grant_id: str = Form(...),
    name: str = Form(...),
    subtitle: str = Form(default=""),
    description: str = Form(default=""),
    iconBg: str = Form(default="#F8FAFC"),
    isOpen: str = Form(default="true"),
    logo_file: Optional[UploadFile] = File(None),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _: Any = Depends(verify_internal_user),
):
    """新增計畫模板，支援上傳 Logo 文件"""
    try:
        # 1. 檢查 Grant 是否存在
        grant = await supabase_service.get_grant_by_id(grant_id)
        if not grant:
            raise HTTPException(status_code=400, detail="Grant not found")

        # 2. 檢查模板 ID 是否重複
        existing = await supabase_service.get_template_by_id(id, grant_id)
        if existing:
            raise HTTPException(status_code=409, detail="Template ID already exists for this grant")

        logo_storage_path = None
        
        # 3. 如果有上傳文件，處理上傳
        if logo_file:
            try:
                file_content = await logo_file.read()
                # 獲取副檔名，如果沒有則預設 png
                file_extension = logo_file.filename.split(".")[-1].lower() if logo_file.filename and "." in logo_file.filename else "png"
                object_path = f"{id}_logo.{file_extension}"
                
                # 上傳到 Supabase Storage
                # 使用 upsert='true' 以防萬一有殘留文件
                supabase_service.client.storage.from_("logos").upload(
                    path=object_path,
                    file=file_content,
                    file_options={
                        "content-type": logo_file.content_type or f"image/{file_extension}",
                        "upsert": "true" 
                    }
                )

                # 獲取公開 URL 並加入快取破壞參數
                public_url_resp = supabase_service.client.storage.from_("logos").get_public_url(object_path)
                public_url = _extract_public_url(public_url_resp)
                if not public_url:
                    raise HTTPException(status_code=500, detail="Failed to obtain logo public URL")
                normalized_url = _normalize_logo_url(public_url)
                logo_storage_path = _with_cache_busting_token(normalized_url)
                
            except Exception as e:
                logger.error("Failed to upload logo file: %s", e, exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to upload logo: {str(e)}")

        # 4. 構建 Payload (修復了此處原本缺失的定義)
        payload = {
            "id": id,
            "grant_id": grant_id,
            "name": name,
            "subtitle": subtitle or None,
            "description": description or None,
            "logo_storage_path": logo_storage_path,
            "iconBg": iconBg,
            "isOpen": isOpen.lower() == "true",
        }

        # 5. 寫入資料庫
        record = await supabase_service.create_plan_template_record(payload)
        if not record:
            raise HTTPException(status_code=500, detail="Failed to create template")

        await _refresh_grant_cache(request, supabase_service)
        return record

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to create template with upload %s/%s: %s", grant_id, id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error while creating template")


@router.put(
    "/templates/{grant_id}/{template_id}/upload",
    response_model=Dict[str, Any],
    summary="更新計畫模板（含文件上傳）",
)
async def update_template_with_upload(
    request: Request,
    grant_id: str,
    template_id: str,
    # 注意：這裡的 id 如果是允許修改的，請保留；如果不允許修改 ID，通常不建議在 Update 中接收 id
    id: str = Form(...), 
    name: str = Form(...),
    subtitle: str = Form(default=""),
    description: str = Form(default=""),
    iconBg: str = Form(default="#F8FAFC"),
    isOpen: str = Form(default="true"),
    logo_file: Optional[UploadFile] = File(None),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    _: Any = Depends(verify_internal_user),
):
    """更新計畫模板，支援上傳 Logo 文件"""
    try:
        # 1. 檢查模板是否存在
        existing = await supabase_service.get_template_by_id(template_id, grant_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Template not found")

        logo_storage_path = _normalize_logo_url(existing.get("logo_storage_path"))
        
        # 2. 如果有上傳新文件，上傳並覆蓋
        if logo_file:
            try:
                file_content = await logo_file.read()
                file_extension = logo_file.filename.split(".")[-1].lower() if logo_file.filename and "." in logo_file.filename else "png"
                # 使用 template_id 保持文件名一致性
                object_path = f"{template_id}_logo.{file_extension}"
                
                # 上傳到 Supabase Storage
                # 關鍵修復：更新時必須加入 "upsert": "true" 才能覆蓋舊圖
                supabase_service.client.storage.from_("logos").upload(
                    path=object_path,
                    file=file_content,
                    file_options={
                        "content-type": logo_file.content_type or f"image/{file_extension}",
                        "upsert": "true" 
                    }
                )

                # 獲取公開 URL 並加入快取破壞參數
                public_url_resp = supabase_service.client.storage.from_("logos").get_public_url(object_path)
                public_url = _extract_public_url(public_url_resp)
                if not public_url:
                    raise HTTPException(status_code=500, detail="Failed to obtain logo public URL")
                normalized_url = _normalize_logo_url(public_url)
                logo_storage_path = _with_cache_busting_token(normalized_url)

            except Exception as e:
                logger.error("Failed to upload logo file: %s", e, exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to upload logo: {str(e)}")

        # 3. 準備更新資料
        update_data = {
            "name": name,
            "subtitle": subtitle or None,
            "description": description or None,
            "logo_storage_path": logo_storage_path,
            "iconBg": iconBg,
            "isOpen": isOpen.lower() == "true",
            # 如果允許修改 ID，這裡可能需要處理，如果不允許，通常不放入 update_data
            # "id": id 
        }

        # 4. 更新資料庫
        record = await supabase_service.update_plan_template_record(template_id, grant_id, update_data)
        if not record:
            raise HTTPException(status_code=404, detail="Template not found or update failed")

        await _refresh_grant_cache(request, supabase_service)
        return record

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to update template with upload %s/%s: %s",
            grant_id,
            template_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Unexpected error while updating template")