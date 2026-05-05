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
THROTTLING_VIP_PROJECTS = 5
THROTTLING_NORMAL_IMAGES = 5
THROTTLING_VIP_IMAGES = 16

# External OAuth provider settings
EXTERNAL_OAUTH_ENABLED = True
EXTERNAL_OAUTH_PROVIDER = os.getenv("EXTERNAL_OAUTH_PROVIDER", "tgsa_oauth")
EXTERNAL_OAUTH_CLIENT_ID = os.getenv("EXTERNAL_OAUTH_CLIENT_ID", "")
EXTERNAL_OAUTH_CLIENT_SECRET = os.getenv("EXTERNAL_OAUTH_CLIENT_SECRET", "")
EXTERNAL_OAUTH_AUTHORIZE_URL = os.getenv("EXTERNAL_OAUTH_AUTHORIZE_URL", "")
EXTERNAL_OAUTH_TOKEN_URL = os.getenv("EXTERNAL_OAUTH_TOKEN_URL", "")
EXTERNAL_OAUTH_USERINFO_URL = os.getenv("EXTERNAL_OAUTH_USERINFO_URL", "")
EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL = os.getenv("EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL", "http://localhost:3000/external-auth-callback")

# ----------------------------------------------------------------------------
# Mother Platform Engine Usage Reporting (Outbound)
# ----------------------------------------------------------------------------
# 用途：每次 AI 呼叫完成後，把 token 用量回報給母平台 (TGSA Portal) 的
# /api/engine-usage/report；定期重送失敗的回報。
#
# 我們的 usage_logs 是 Source of Truth (Mirror mode)。失敗的回報只會影響母平台
# 看到的數字，不會影響我們的任何核心流程。
ENGINE_USAGE_ENABLED = os.getenv("ENGINE_USAGE_ENABLED", "true").lower() in {"1", "true", "yes"}

# 母平台基底 URL；登入用的 EXTERNAL_OAUTH_TOKEN_URL/AUTHORIZE_URL 已存在。
MOTHER_PLATFORM_BASE_URL = os.getenv("MOTHER_PLATFORM_BASE_URL", "https://portal.tgsaapp.com").rstrip("/")
ENGINE_USAGE_REPORT_URL = f"{MOTHER_PLATFORM_BASE_URL}/api/engine-usage/report"
ENGINE_USAGE_STATUS_URL = f"{MOTHER_PLATFORM_BASE_URL}/api/engine-usage/status"

# 重送與逾時設定。
ENGINE_USAGE_TIMEOUT_SECONDS = int(os.getenv("ENGINE_USAGE_TIMEOUT_SECONDS", "10"))
ENGINE_USAGE_MAX_RETRIES = int(os.getenv("ENGINE_USAGE_MAX_RETRIES", "5"))
ENGINE_USAGE_RETRY_INTERVAL_SECONDS = int(os.getenv("ENGINE_USAGE_RETRY_INTERVAL_SECONDS", "60"))
ENGINE_USAGE_RETRY_BATCH_SIZE = int(os.getenv("ENGINE_USAGE_RETRY_BATCH_SIZE", "50"))

# 配額執法開關 (Q5 決議：預設 hard block；可由環境變數 toggle 為 soft warn)。
# True  → 母平台回 is_blocked=true 時，下一次 AI 呼叫直接拒絕 (HTTP 429)。
# False → 只記 log，不拒絕呼叫 (mirror mode 諮詢)。
ENGINE_USAGE_ENFORCE_BLOCK = os.getenv("ENGINE_USAGE_ENFORCE_BLOCK", "true").lower() in {"1", "true", "yes"}

# 配額狀態快取 TTL：避免每次 AI 呼叫前都打 mother 的 status endpoint。
ENGINE_USAGE_BLOCK_CACHE_TTL_SECONDS = int(os.getenv("ENGINE_USAGE_BLOCK_CACHE_TTL_SECONDS", "60"))

# Token 提前刷新閾值：access_token 還剩多少秒就主動 refresh。
ENGINE_USAGE_TOKEN_REFRESH_LEEWAY_SECONDS = int(os.getenv("ENGINE_USAGE_TOKEN_REFRESH_LEEWAY_SECONDS", "120"))

