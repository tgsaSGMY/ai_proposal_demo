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