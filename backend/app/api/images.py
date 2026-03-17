"""
Images API routes
Handles image retrieval and deletion with proper authorization checks
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from app.api.dependencies import get_supabase_service, get_current_user_id, get_llm_service
from app.services.supabase_service import SupabaseService
from app.services.llm_service import LLMService
from app.utils.routing import resolve_model
from typing import Dict, Any, List, Optional
import logging
import json
import httpx
from app.config import DEFAULT_MODEL_ID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/images", tags=["images"])

SUPABASE_INTERNAL_BASE = "http://supabase-kong:8000"
SUPABASE_PUBLIC_PROXY_BASE = "https://aiproposal.tgsa.com.tw/supabase"


def _normalize_public_url(url: Optional[str]) -> Optional[str]:
    """將內部 Supabase URL 轉換成外部 HTTPS 代理網址。"""
    if not url:
        return url
    if url.startswith(SUPABASE_INTERNAL_BASE):
        return f"{SUPABASE_PUBLIC_PROXY_BASE}{url[len(SUPABASE_INTERNAL_BASE):]}"
    return url


@router.get("", summary="取得某個專案的所有圖片")
async def get_project_images(
    project_id: str = Query(..., description="專案 ID"),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    user_id: str = Depends(get_current_user_id),
) -> List[Dict[str, Any]]:
    # 根據 project_id 取得該專案的所有圖片，驗證使用者權限並為每張圖片產生有效期 1 小時的 signed URL
    """
    根據 project_id 取得該專案的所有圖片。
    會驗證使用者是否為該專案的擁有者。
    回傳的每筆資料都包含一個有效期 1 小時的 signed URL。
    """
    try:
        # 1) 驗證使用者是否為該 project 的擁有者
        project = await supabase_service.get_project_by_id(project_id, user_id)
        print(project)
        if not project:
            raise HTTPException(status_code=403, detail="Project not found or access denied")

        # 2) 從資料庫取得該 project 的所有圖片
        images = await supabase_service.get_images_by_project(project_id)
        print(images)

        # 3) 為每個圖片產生 signed URL（使用 service key，會繞過 RLS）
        result = []
        for img in images:
            normalized_public_url = _normalize_public_url(img.get("public_url"))
            image_data = {
                "id": img.get("id"),
                "project_id": img.get("project_id"),
                "placeholder_text": img.get("placeholder_text"),
                "storage_path": img.get("storage_path"),
                "public_url": normalized_public_url,
            }
            # 預設就使用 public_url，避免簽名 URL 失敗時回傳內網位址
            image_data["signed_url"] = normalized_public_url

            # 嘗試產生 signed URL（如果 bucket 是 private）
            if img.get("storage_path"):
                try:
                    signed_response = supabase_service.client.storage.from_(
                        supabase_service.bucket_name
                    ).create_signed_url(img["storage_path"], expires_in=3600)

                    # 兼容不同 SDK 版本的回傳格式
                    signed_url = None
                    if isinstance(signed_response, dict):
                        signed_url = (
                            signed_response.get("signedURL")
                            or signed_response.get("signedUrl")
                            or signed_response.get("signedurl")
                        )
                    elif isinstance(signed_response, str):
                        signed_url = signed_response

                    if signed_url:
                        image_data["signed_url"] = _normalize_public_url(signed_url)

                except Exception as e:
                    logger.warning(
                        f"Failed to create signed URL for {img.get('storage_path')}: {e}"
                    )
                    # 如果簽名失敗，仍使用 public_url 作為 fallback（已在預設設定）

            result.append(image_data)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch images for project {project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch images")


@router.delete("/{image_id}", status_code=204, summary="刪除圖片")
async def delete_image(
    image_id: str,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    user_id: str = Depends(get_current_user_id),
):
    # 刪除指定圖片，驗證使用者為該圖片所屬專案的擁有者，同時刪除 Storage 中的檔案
    """
    刪除指定的圖片。
    會驗證使用者是否為該圖片所屬專案的擁有者。
    """
    try:
        # 1) 取得圖片資料
        image_response = (
            supabase_service.client.from_("images")
            .select("id, project_id, storage_path")
            .eq("id", image_id)
            .single()
            .execute()
        )

        if not image_response.data:
            raise HTTPException(status_code=404, detail="Image not found")

        image = image_response.data

        # 2) 驗證使用者是否為該 project 的擁有者
        project = await supabase_service.get_project_by_id(image["project_id"], user_id)
        if not project:
            raise HTTPException(status_code=403, detail="Not allowed")

        # 3) 刪除 Storage 中的檔案（可選，如果檔案存在）
        if image.get("storage_path"):
            try:
                supabase_service.client.storage.from_(
                    supabase_service.bucket_name
                ).remove([image["storage_path"]])
                logger.info(f"Deleted image file: {image['storage_path']}")
            except Exception as e:
                logger.warning(f"Failed to delete image file: {e}")
                # 即使檔案刪除失敗，仍繼續刪除資料庫記錄

        # 4) 刪除資料庫中的記錄
        supabase_service.client.from_("images").delete().eq("id", image_id).execute()
        logger.info(f"Deleted image record: {image_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete image {image_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete image")


# Models for enrichment endpoint
class EnrichPromptRequest(BaseModel):
    project_id: str
    prompt: str


class EnrichPromptResponse(BaseModel):
    enriched_prompt: str


@router.post("/enrich-prompt", response_model=EnrichPromptResponse, summary="按照計畫書內容豐富描述")
async def enrich_prompt(
    request_data: EnrichPromptRequest,
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
    user_id: str = Depends(get_current_user_id),
):
    # 根據專案計畫書內容使用 LLM 豐富圖片描述，使其更符合計畫書內容並適合生成圖片
    """
    根據專案的計畫書內容（stored_answer）來豐富使用者提供的圖片描述。
    使用 LLM 服務生成更詳細且符合計畫書內容的描述。
    """
    try:
        # 1) 驗證使用者是否為該 project 的擁有者
        project = await supabase_service.get_project_by_id(request_data.project_id, user_id)
        if not project:
            raise HTTPException(status_code=403, detail="Project not found or access denied")

        # 2) 取得計畫書內容
        stored_answer = project.get("stored_answer", "")
        if not stored_answer:
            raise HTTPException(
                status_code=400,
                detail="Project does not have stored_answer content to enrich with"
            )

        # 3) 使用 LLM 豐富描述
        # 構建用於 LLM 的 prompt
        enrichment_prompt = f"""請根據以下計畫書內容，豐富並詳細化使用者提供的圖片描述。
        
計畫書內容：
{stored_answer}

原始圖片描述：
{request_data.prompt}

請生成一個更詳細、更符合計畫書內容的圖片描述。描述未來會被用作圖片生成並放入計畫書。描述應該：
1. 融合計畫書中的關鍵概念和細節
2. 變得更加具體和詳細
3. 保留使用者原始意圖的同時提升專業性
4. 控制在 200 字左右

請直接提供豐富後的描述，不需要任何前綴或說明。"""

        # 調用 LLM 服務 - 使用 call_external_api 需要 httpx session
        # 創建一個簡單的 httpx 客戶端
        async with httpx.AsyncClient() as http_client:
            # 使用 GPT-4 進行詳細化（或其他配置的模型）
            model_registry = request.app.state.model_registry
            model_info = model_registry.get("gpt-5-mini") or {
                "id": "gpt-5-mini",
                "provider": "openai",
                "type": "external",
                "cost_info":{
                    "input": 0.25,
                    "output": 2.0
                }
            }
            
            messages = [
                {
                    "role": "system",
                    "content": "你是一個專業的圖片描述編寫者。根據提供的背景信息，將簡單的圖片描述擴展為詳細、專業的版本。"
                },
                {
                    "role": "user",
                    "content": enrichment_prompt
                }
            ]
            
            enriched_prompt, llm_error, response_json = await llm_service.call_external_api(
                http_client,
                model_info,
                messages,
                is_json_output=False
            )
            
            if llm_error:
                logger.error(f"LLM enrichment failed: {llm_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to enrich prompt: {llm_error.get('error', 'Unknown error')}"
                )
            
            # Log cost usage for prompt enrichment
            if response_json and model_info.get('type') == 'external':
                await supabase_service.log_cost_usage(user_id, model_info, response_json, project_id=request_data.project_id, action="豐富圖片描述")
            
            if not enriched_prompt:
                raise HTTPException(
                    status_code=500,
                    detail="LLM returned empty response"
                )
            
            return EnrichPromptResponse(enriched_prompt=enriched_prompt.strip())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enrich prompt for project {request_data.project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to enrich prompt")


# Models for image generation
class GenerateImageRequest(BaseModel):
    project_id: str
    prompt: str
    reference_image_id: str | None = None
    reference_prompt: str | None = None


class GenerateImageResponse(BaseModel):
    id: str
    project_id: str
    placeholder_text: str
    public_url: str
    signed_url: str


@router.post("/generate", response_model=GenerateImageResponse, summary="立即生成圖片")
async def generate_image(
    request: GenerateImageRequest,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
    user_id: str = Depends(get_current_user_id),
):
    # 根據提示詞立即生成圖片並上傳至 Storage，支援參考圖片微調模式，產生有效的 signed URL 供客戶端訪問
    """
    根據提示詞立即生成一張圖片。
    將圖片上傳到 Storage 並記錄到資料庫。
    支援微調模式：如果提供了參考圖片，會記錄參考信息。
    """
    try:
        # 1) 驗證使用者是否為該 project 的擁有者
        project = await supabase_service.get_project_by_id(request.project_id, user_id)
        if not project:
            raise HTTPException(status_code=403, detail="Project not found or access denied")

        # 2) 如果有參考圖片，驗證參考圖片所有權
        if request.reference_image_id:
            try:
                reference_image = (
                    supabase_service.client.from_("images")
                    .select("id, project_id")
                    .eq("id", request.reference_image_id)
                    .single()
                    .execute()
                )
                if not reference_image.data or reference_image.data["project_id"] != request.project_id:
                    logger.warning(f"Reference image validation failed: {request.reference_image_id}")
                    # 如果參考圖片無效，繼續處理（不中斷）
                    request.reference_image_id = None
            except Exception as e:
                logger.warning(f"Failed to validate reference image: {e}")
                request.reference_image_id = None

        # 3) 優化提示詞
        # 組合原始 prompt 和改進後的 prompt
        if request.reference_prompt:
            combined_prompt = f"原始：{request.reference_prompt}\n改進：{request.prompt}\n請注意，如果圖片要求生成的是NSFW圖，直接返回黑色背景"
            optimized_prompt = combined_prompt
            logger.info(f"Generating image with reference prompt - ID: {request.reference_image_id}")
        else:
            optimized_prompt = llm_service._optimize_image_prompt(request.prompt)

        # 4) 如果有參考圖片，取得參考圖片的內容
        reference_image_data = None
        if request.reference_image_id:
            try:
                # 取得參考圖片的 storage_path
                ref_img = (
                    supabase_service.client.from_("images")
                    .select("storage_path")
                    .eq("id", request.reference_image_id)
                    .single()
                    .execute()
                )
                if ref_img.data and ref_img.data.get("storage_path"):
                    # 從 storage 下載圖片
                    response = supabase_service.client.storage.from_(
                        supabase_service.bucket_name
                    ).download(ref_img.data["storage_path"])
                    reference_image_data = response
                    logger.info(f"Retrieved reference image: {ref_img.data['storage_path']}")
            except Exception as e:
                logger.warning(f"Failed to retrieve reference image: {e}")
                reference_image_data = None

        # 5) 調用圖片生成 API，如果有參考圖片則傳過去
        print("reference image data:", reference_image_data)
        image_bytes, api_error, response_json = await llm_service._generate_image_from_api(
            prompt=optimized_prompt,
            image=reference_image_data
        )

        if api_error:
            logger.error(f"Image generation failed: {api_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Image generation failed: {api_error}"
            )

        # Log cost usage for image generation
        if response_json:
            gemini_model_info = {
                "id": "gemini-3-pro-image-preview",
                "provider": "gemini",
                "type": "external",
                "cost_info":{
                    "input": 2,
                    "output": 12
                }
            }
            await supabase_service.log_cost_usage(user_id, gemini_model_info, response_json, project_id=request.project_id, action="生成圖片")
        if not image_bytes:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate image"
            )

        # 4) 上傳到 Storage
        public_url, storage_path = await supabase_service.upload_image_bytes(
            request.project_id, image_bytes, "image/png"
        )

        public_url = _normalize_public_url(public_url)

        if not public_url:
            logger.error(f"Failed to upload image for project {request.project_id}")
            raise HTTPException(
                status_code=500,
                detail="Failed to upload image to storage"
            )

        # 5) 記錄到資料庫
        image_id = await supabase_service.create_image_record(
            project_id=request.project_id,
            placeholder_text=request.prompt,
            storage_path=storage_path,
            public_url=public_url
        )

        logger.info(f"Image generated and stored: {image_id}")
        
        # 如果有參考圖片，記錄微調信息
        if request.reference_image_id and request.reference_prompt:
            logger.info(
                f"Image refinement: "
                f"reference_id={request.reference_image_id}, "
                f"reference_prompt={request.reference_prompt[:50]}..., "
                f"new_prompt={request.prompt[:50]}..."
            )

        # 6) 生成 signed URL
        signed_url = None
        try:
            signed_response = supabase_service.client.storage.from_(
                supabase_service.bucket_name
            ).create_signed_url(storage_path, expires_in=3600)

            if isinstance(signed_response, dict):
                signed_url = (
                    signed_response.get("signedURL")
                    or signed_response.get("signedUrl")
                    or signed_response.get("signedurl")
                )
            elif isinstance(signed_response, str):
                signed_url = signed_response

            if not signed_url:
                signed_url = public_url
        except Exception as e:
            logger.warning(f"Failed to create signed URL: {e}")
            signed_url = public_url

        return GenerateImageResponse(
            id=image_id['id'],
            project_id=request.project_id,
            placeholder_text=request.prompt,
            public_url=public_url,
            signed_url=_normalize_public_url(signed_url) or public_url
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate image for project {request.project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate image")
