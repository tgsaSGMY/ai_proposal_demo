# 調取完整主題、模板和分項

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from app.models import GrantConfig

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Configuration"]
)

@router.get("/config", response_model=List[GrantConfig])
async def get_all_configs(request: Request):
    """
    從應用程式狀態中獲取已加載的所有 Grant、Template 和 Section 配置，直接返回內存中的數據。
    """
    try:
        if not hasattr(request.app.state, 'all_grants_config'):
             raise HTTPException(status_code=503, detail="Configurations are not yet loaded or failed to load.")
        return request.app.state.all_grants_config 
    except Exception as e:
        logger.error(f"Failed to retrieve configurations from app state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching configurations.")