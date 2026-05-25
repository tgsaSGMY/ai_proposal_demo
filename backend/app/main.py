# FastAPI entrypoint for the demo backend.
#
# No authentication — every request is identified by the demo_session_id
# cookie minted in app.api.dependencies.get_demo_session_id.

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import config as api_config
from app.api import generate, projects
from app.core.lifecycle import shutdown_event_handler, startup_event_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Proposal Demo API",
    description="Unauthenticated demo of the AI grant-proposal generator.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://demo-dev.172.233.79.222.nip.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await startup_event_handler(app)


@app.on_event("shutdown")
async def on_shutdown():
    await shutdown_event_handler(app)


app.include_router(generate.router)
app.include_router(api_config.router)
app.include_router(projects.router)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "AI Proposal Demo API — unauthenticated, cookie-scoped."}
