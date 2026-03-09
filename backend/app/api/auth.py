from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user_context

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get("/me")
async def get_me(user_ctx: Dict[str, Any] = Depends(get_current_user_context)):
    """Return canonical user profile resolved from the current bearer token."""
    return user_ctx
