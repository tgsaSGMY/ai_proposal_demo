# 集中管理所有 Service 的依賴注入

from fastapi import Request, Depends, HTTPException, Header, status
from app.services.supabase_service import SupabaseService
from app.services.llm_service import LLMService
from typing import Optional

def get_supabase_service(request: Request) -> SupabaseService:
    # 從應用狀態中獲取 Supabase Service 實例
    return request.app.state.supabase_service

def get_llm_service(request: Request) -> LLMService:
    # 從應用狀態中獲取 LLM Service 實例
    return request.app.state.llm_service

async def get_current_user_id(
    authorization: Optional[str] = Header(None),
    supabase_service: SupabaseService = Depends(get_supabase_service)
) -> str:
    """
    從 Authorization Header 解析 Token 並驗證使用者，回傳 user_id
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    user_response = supabase_service.client.auth.get_user(token)
    
    if not user_response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired token"
        )
        
    return user_response.user.id

async def verify_internal_user(
    authorization: Optional[str] = Header(None),
    supabase_service: SupabaseService = Depends(get_supabase_service)
):
    """
    Dependency:
    1. 解析 Authorization Token 驗證是否登入
    2. 查詢 Whitelist 表檢查是否為 'internal'
    3. 如果通過，回傳 user 物件；不通過則拋出 403 錯誤
    """
    
    # --- 1. 基礎驗證 (Authentication) ---
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    # 呼叫 Supabase Auth 驗證 Token 有效性
    try:
        user_response = supabase_service.client.auth.get_user(token)
        user = user_response.user
        
        if not user or not user.email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid or expired token"
            )
    except Exception as e:
        # Token 解析失敗
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Authentication failed: {str(e)}"
        )

    # --- 2. 權限驗證 (Authorization) ---
    # 使用 Service Key 去查詢 whitelist 表 (無視 RLS)
    try:
        result = (
            supabase_service.client.from_("whitelist")
            .select("role")
            .eq("email", user.email)
            .maybe_single()  # 使用 maybe_single 避免查無資料時報錯
            .execute()
        )
        whitelist_data = result.data

    except Exception as e:
        print(f"Database error checking whitelist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying permissions"
        )

    # --- 3. 判斷結果 ---
    is_internal = whitelist_data and whitelist_data.get("role") == "internal"

    if not is_internal:
        # 403 Forbidden: 伺服器理解請求但拒絕執行 (權限不足)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission Denied: This action is restricted to internal staff."
        )

    # 驗證通過，回傳使用者資訊 (API 可能會用到)
    return user