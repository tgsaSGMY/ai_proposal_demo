# 存放環境變數和常數。
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL") 
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET_NAME = "datasets" # Supabase Storage Bucket 名稱

# 資料庫配置 (用於 SQLAlchemy) - 直接连接Supabase 项目底层 PostgreSQL 数据库的连接字符串
DATABASE_URL = os.getenv("DATABASE_URL") 
BACKEND_ROOT = Path(__file__).resolve().parent.parent

# LLM API 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_BASE_URL = "http://localhost:11434/v1" # Ollama 的預設 API endpoint

# 圖片生成配置
IMAGE_MODEL = "imagen-4.0-generate-001"  # Google Gemini 圖片生成模型

# 向量嵌入配置
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en")

# 預設模型 ID
DEFAULT_MODEL_ID = "gpt-5-mini"


# App-issued JWT (used for external OAuth users)
APP_JWT_SECRET = os.getenv("APP_JWT_SECRET", "")
APP_JWT_ISSUER = "ai-proposal-platform"
APP_JWT_EXPIRES_SECONDS = 86400

# Plan Limits & Quotas
# Token limits (Daily)
QUOTA_NORMAL_DAILY_TOKENS = 1000000
QUOTA_VIP_DAILY_TOKENS = 999999999  # Practically unlimited

# Project Slot Limits
SLOT_NORMAL_MAX_PROJECTS = 1
SLOT_VIP_MAX_PROJECTS = 50

# Throttling
THROTTLING_DELAY_SECONDS = 30
THROTTLING_NORMAL_PROJECTS = 2
THROTTLING_VIP_PROJECTS = 99999
THROTTLING_NORMAL_IMAGES = 5
THROTTLING_VIP_IMAGES = 99999

# External OAuth provider settings
EXTERNAL_OAUTH_ENABLED = True
EXTERNAL_OAUTH_PROVIDER = os.getenv("EXTERNAL_OAUTH_PROVIDER", "tgsa_oauth")
EXTERNAL_OAUTH_CLIENT_ID = os.getenv("EXTERNAL_OAUTH_CLIENT_ID", "")
EXTERNAL_OAUTH_CLIENT_SECRET = os.getenv("EXTERNAL_OAUTH_CLIENT_SECRET", "")
EXTERNAL_OAUTH_AUTHORIZE_URL = os.getenv("EXTERNAL_OAUTH_AUTHORIZE_URL", "")
EXTERNAL_OAUTH_TOKEN_URL = os.getenv("EXTERNAL_OAUTH_TOKEN_URL", "")
EXTERNAL_OAUTH_USERINFO_URL = os.getenv("EXTERNAL_OAUTH_USERINFO_URL", "")
EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL = os.getenv("EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL", "http://localhost:3000/external-auth-callback")
