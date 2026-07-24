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
DEFAULT_MODEL_ID = "gpt-5.3-chat-latest"

# --- Demo-specific knobs --------------------------------------------------

# Hard-coded grant/template IDs that the demo will load.
# When both are set (non-empty), the demo ALWAYS uses this exact pair
# and never falls back to the first item in the catalog.
DEMO_GRANT_ID = os.getenv("DEMO_GRANT_ID", "").strip()
DEMO_TEMPLATE_ID = os.getenv("DEMO_TEMPLATE_ID", "").strip()

# Hard cap on chat turns (a.k.a. user prompts) per session before the
# frontend is told to prompt registration. DEMO_MAX_PROMPTS_PER_SESSION is
# the canonical name; DEMO_INTERACTION_LIMIT is kept as a legacy alias so
# older .env files still work.
DEMO_INTERACTION_LIMIT = int(
    os.getenv("DEMO_MAX_PROMPTS_PER_SESSION")
    or os.getenv("DEMO_INTERACTION_LIMIT")
    or "20"
)

# Token cap per session — backend sums pending_usage_logs after each LLM
# call and trips limit_reached once the cumulative input+output tokens
# exceed this value.
DEMO_MAX_TOKENS_PER_SESSION = int(os.getenv("DEMO_MAX_TOKENS_PER_SESSION", "100000"))

# Max .docx report generations per session (default 1).
DEMO_MAX_GENERATIONS_PER_SESSION = int(os.getenv("DEMO_MAX_GENERATIONS_PER_SESSION", "1"))

# --- Session Expiry (dual env var support) ---
# DEMO_SESSION_EXPIRY_MINUTES takes priority for dev testing.
# If not set, falls back to DEMO_SESSION_EXPIRY_DAYS (default 7 days).
# Bad values are silently corrected to 7 days to prevent startup crashes.
try:
    minutes_env = os.getenv("DEMO_SESSION_EXPIRY_MINUTES")
    if minutes_env:
        DEMO_SESSION_EXPIRY_MINUTES = int(minutes_env)
    else:
        days = int(os.getenv("DEMO_SESSION_EXPIRY_DAYS", "7"))
        DEMO_SESSION_EXPIRY_MINUTES = days * 24 * 60
except ValueError:
    DEMO_SESSION_EXPIRY_MINUTES = 7 * 24 * 60  # 7 days fallback

# Keep the legacy variable available for backward compatibility, but it
# reflects the canonical minutes value converted back to days.
DEMO_SESSION_EXPIRY_DAYS = DEMO_SESSION_EXPIRY_MINUTES / (24 * 60)

# Where the visitor is redirected when they hit the cap — points at the
# parent platform's register page. Include `?ref=<session_id>` server-side
# when emitting the redirect so the parent can claim the demo row.
DEMO_REGISTER_REDIRECT_URL = os.getenv(
    "DEMO_REGISTER_REDIRECT_URL",
    "https://aiproposal.tgsa.com.tw/api/external-auth/redirect",
)

# Full platform URL (used for CORS and signup redirects).
FULL_PLATFORM_URL = os.getenv("FULL_PLATFORM_URL", "https://aiproposal.tgsa.com.tw")

# Demo subdomain (used for CORS allowlist).
DEMO_FRONTEND_URL = os.getenv("DEMO_FRONTEND_URL", "https://demo-aiproposal.tgsa.com.tw")

# Per-IP cap on demo session creation (mint-time only).
# Tuned for casual-abuse friction, not a security boundary.
DEMO_IP_HOURLY_LIMIT = int(os.getenv("DEMO_IP_HOURLY_LIMIT", "10"))
DEMO_IP_DAILY_LIMIT = int(os.getenv("DEMO_IP_DAILY_LIMIT", "20"))
    