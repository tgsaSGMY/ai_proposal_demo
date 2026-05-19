"""Environment variables and runtime constants for the demo backend."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_BUCKET_NAME = "datasets"

# Direct Postgres connection for SQLAlchemy (engine usage in supabase_service).
DATABASE_URL = os.getenv("DATABASE_URL")
BACKEND_ROOT = Path(__file__).resolve().parent.parent

# LLM providers
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_BASE_URL = "http://localhost:11434/v1"

IMAGE_MODEL = "imagen-4.0-generate-001"
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en")
DEFAULT_MODEL_ID = "gpt-5-mini"

# --- Demo-specific knobs --------------------------------------------------
# Hard cap on chat turns before the frontend is told to prompt registration.
DEMO_INTERACTION_LIMIT = int(os.getenv("DEMO_INTERACTION_LIMIT", "10"))

# Where the visitor is redirected when they hit the cap — points at the
# parent platform's register page. Include `?ref=<session_id>` server-side
# when emitting the redirect so the parent can claim the demo row.
DEMO_REGISTER_REDIRECT_URL = os.getenv(
    "DEMO_REGISTER_REDIRECT_URL",
    "https://portal.tgsaapp.com/register",
)
