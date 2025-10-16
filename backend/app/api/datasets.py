# 連接數據庫，CRUD數據

import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from app.models import SaveDatasetRequest, DatasetEntry, DatasetEntry
from app.services.supabase_service import SupabaseService
from app.services.qdrant_service import QdrantService
from .dependencies import get_supabase_service, get_qdrant_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/datasets",
    tags=["Datasets"]
)

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def save_dataset_entries(
    req: SaveDatasetRequest,
    background_tasks: BackgroundTasks,
    supabase_service: SupabaseService = Depends(get_supabase_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
):
    """
    異步保存數據集條目到 Supabase，並將對應的向量數據 upsert 到 Qdrant。
    此操作立即返回，並在後台執行實際的資料庫寫入。
    """
    
    async def background_task(entries: List[DatasetEntry]):
        logger.info(f"Background task started: saving {len(entries)} dataset entries.")
        qdrant_points = []
        for entry in entries:
            try:
                new_supabase_entry = await supabase_service.add_dataset_entry(
                    source_type=entry.source_type,
                    grant_id=entry.grant_id,
                    template_id=entry.template_id,
                    section_id=entry.section_id,
                    prompt=entry.prompt,
                    final_answer=entry.final_answer,
                    rejected_answer=entry.rejected_answer
                )
                
                if new_supabase_entry and 'id' in new_supabase_entry:
                    db_id = new_supabase_entry['id']
                    qdrant_points.append({
                        "db_id": db_id, 
                        "text": f"User Idea: {entry.prompt}",
                        "payload": {
                            "db_id": db_id,
                            "source_type": entry.source_type,
                            "grant_id": entry.grant_id,
                            "template_id": entry.template_id,
                            "section_id": entry.section_id,
                            "prompt": entry.prompt[:200]
                        }
                    })
                else:
                    logger.warning(f"Skipping Qdrant entry for section {entry.section_id} due to no ID from Supabase.")
            except Exception as e:
                logger.error(f"Failed to process entry for section {entry.section_id}: {e}", exc_info=True)

        if qdrant_points:
            try:
                qdrant_service.upsert_exemplars(qdrant_points)
                logger.info(f"Successfully upserted {len(qdrant_points)} points to Qdrant.")
            except Exception as e:
                logger.error(f"Failed to upsert points to Qdrant: {e}", exc_info=True)
        logger.info("Background dataset saving task finished.")

    background_tasks.add_task(background_task, req.entries)
    return {"message": "Dataset saving process has been initiated in the background."}

@router.get("", summary="獲取所有數據集條目", response_model=List[Dict[str, Any]])
async def get_all_datasets_endpoint(
    grant_id: Optional[str] = None,
    template_id: Optional[str] = None,
    section_id: Optional[str] = None,
    source_type: Optional[str] = None,
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """從 Supabase 獲取數據集記錄，支持按 grant, template, section, source_type 進行篩選。"""
    try:
        datasets = await supabase_service.get_all_datasets(
            grant_id=grant_id,
            template_id=template_id,
            section_id=section_id,
            source_type=source_type,
        )
        return datasets
    except Exception as e:
        logger.error(f"Failed to fetch datasets with filters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{dataset_id}", status_code=status.HTTP_200_OK)
async def update_dataset_entry(
    dataset_id: int,
    req: DatasetEntry,   
    supabase_service: SupabaseService = Depends(get_supabase_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
):
    """
    同步更新 Supabase 和 Qdrant 中的一筆數據集條目（Qdrant 的更新策略是「刪除舊的，再插入新的」）。
    """
    try:
        # 更新 Supabase
        updated_entry = await supabase_service.update_dataset_by_id(
            dataset_id,
            {
                "source_type": req.source_type,
                "grant_id": req.grant_id,
                "template_id": req.template_id,
                "section_id": req.section_id,
                "prompt": req.prompt,
                "final_answer": req.final_answer,
            },
        )

        if not updated_entry:
            raise HTTPException(status_code=404, detail="Dataset not found in Supabase")

        # 更新 Qdrant（單筆 upsert）
        qdrant_point = {
            "db_id": dataset_id,
            "text": f"User Idea: {req.prompt}",
            "payload": {
                "db_id": dataset_id,
                "source_type": req.source_type,
                "grant_id": req.grant_id,
                "template_id": req.template_id,
                "section_id": req.section_id,
                "prompt": req.prompt[:200],
            },
        }

        # 調用 Qdrant 單筆更新方法
        await qdrant_service.update_exemplar_by_db_id(
            db_id=dataset_id,
            new_text=qdrant_point["text"],
            new_payload=qdrant_point["payload"],
        )

        return {"message": f"Dataset {dataset_id} updated successfully in both Supabase and Qdrant."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{dataset_id}", status_code=status.HTTP_200_OK, summary="刪除一個數據集條目")
async def delete_dataset_entry(
    dataset_id: int, 
    supabase: SupabaseService = Depends(get_supabase_service),
    qdrant: QdrantService = Depends(get_qdrant_service)
):
    """同步刪除 Supabase 和 Qdrant 中的數據。"""
    try:
        # 1. 從 Qdrant 刪除
        await qdrant.delete_exemplar_by_db_id(dataset_id)
        logger.info(f"Deleted vector for dataset ID {dataset_id} from Qdrant.")

        # 2. 從 Supabase 刪除
        deleted_from_supabase = await supabase.delete_dataset_by_id(dataset_id)
        if not deleted_from_supabase:
            logger.warning(f"Dataset ID {dataset_id} not found in Supabase, but deletion was attempted (Qdrant vector may have been removed).")
        
        logger.info(f"Deleted dataset ID {dataset_id} from Supabase.")
        return {"message": "Dataset entry deleted successfully from both Supabase and Qdrant."}
    except Exception as e:
        logger.error(f"Failed to delete dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))