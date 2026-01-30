# main page, 主接口
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 導入路由器和生命週期事件
from app.api import (
    generate,
    datasets,
    admin,
    config as api_config,
    draft_plan,
    projects,
    images,
    dynamic_section,
    section_recommender,
    template_manager,
)
from app.core.lifecycle import startup_event_handler, shutdown_event_handler

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Proposal Platform API",
    description="API for generating and managing grant proposals.",
    version="1.0.0"
)

# 添加中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://ai-proposal-platform-v1-0.pages.dev","https://ai-proposal-platform.smtt.workers.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊生命週期事件
@app.on_event("startup")
async def on_startup():
    await startup_event_handler(app)

@app.on_event("shutdown")
async def on_shutdown():
    await shutdown_event_handler(app)


# 包含所有路由器
app.include_router(generate.router)
app.include_router(datasets.router)
app.include_router(admin.router)
app.include_router(api_config.router)
app.include_router(draft_plan.router)
app.include_router(projects.router)
app.include_router(images.router)
app.include_router(dynamic_section.router)
app.include_router(section_recommender.router)
app.include_router(template_manager.router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the AI Proposal Platform API!"}