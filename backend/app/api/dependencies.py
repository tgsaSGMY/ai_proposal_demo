# 集中管理所有 Service 的依賴注入

from fastapi import Request
from app.services.supabase_service import SupabaseService
from app.services.qdrant_service import QdrantService
from app.services.llm_service import LLMService

def get_supabase_service(request: Request) -> SupabaseService:
    return request.app.state.supabase_service

def get_qdrant_service(request: Request) -> QdrantService:
    return request.app.state.qdrant_service

def get_llm_service(request: Request) -> LLMService:
    return request.app.state.llm_service