import asyncio
import json
import httpx
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 依赖注入的函数：提供 SupabaseService 实例
async def get_supabase_service(request: Request) -> SupabaseService:
    return request.app.state.supabase_service

# 依赖注入的函数：提供 QdrantService 实例
async def get_qdrant_service(request: Request) -> QdrantService:
    return request.app.state.qdrant_service

# 依赖注入的函数：提供 LLMService 实例
async def get_llm_service(request: Request) -> LLMService:
    return request.app.state.llm_service

async def get_model_manager(request: Request) -> LoRAModelManager:
    return request.app.state.model_manager

@app.on_event("startup")
async def startup_event():
    print("正在加载服务器配置...")
    print("服务器配置加载完成。")
