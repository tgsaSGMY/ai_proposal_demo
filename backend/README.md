# 補助引擎（AI Proposal, AP）Backend

本服務為補助引擎（AI Proposal, AP）的後端 API，使用 FastAPI 建置，負責：

- 計畫書內容生成與改寫
- 專案資料管理
- 模板與章節設定管理
- 資料集與模型路由管理
- 圖片生成與提示詞強化
- 使用量分析與執行時間軸
- 外部 OAuth 登入整合

## 技術棧

- Python 3.10
- FastAPI（含 WebSocket 支援）
- Uvicorn
- Supabase (PostgreSQL + Storage + Auth + Realtime；Schema：`ai_proposal_platform`)
- SQLAlchemy
- fastembed（`BAAI/bge-small-en` 向量嵌入；用於 few-shot 範例檢索）
- 多 LLM 整合：
    - OpenAI GPT-5 系列（`gpt-5`、`gpt-5-mini`、`gpt-5-nano`、`gpt-5.1-chat-latest`、`gpt-4.1-mini`、`gpt-4.1-nano`）
    - Google Gemini（`gemini-3-pro-preview`、`gemini-3-flash-preview`、`gemini-2.5-pro`、`gemini-2.5-flash-lite`）
    - Google Imagen / Gemini Image（圖片生成）
    - Ollama（本地模型，可選）
- PyJWT（內部 app token）

## 專案結構

app/

- main.py：FastAPI 入口，註冊路由與 CORS
- config.py：環境變數與系統常數（含節流上限、配額、JWT TTL 等）
- models.py：Pydantic 資料模型
- api/：API 路由模組（共 14 個 router）
    - 使用者端：`auth.py`、`external_auth.py`、`projects.py`、`generate.py`、`draft_plan.py`、`commands.py`、`images.py`、`section_recommender.py`
    - 管理端：`template_manager.py`、`dynamic_section.py`、`datasets.py`、`admin.py`、`config.py`、`usage_log.py`
    - 共用依賴：`dependencies.py`（含 `AUTH_CONTEXT_CACHE`、20 秒 TTL 認證快取）
- services/：Supabase 與 LLM 服務層
    - `supabase_service.py`：Supabase 整合（含 `get_all_grants_config()` 等核心查詢；P0 優化後快取交由 `app.state` 管理）
    - `llm_service.py`：多供應商 LLM 路由與成本計算
- core/：啟動與生命週期管理
    - `lifecycle.py`：啟動時預載入 `app.state.all_grants_config`、`model_registry`、`routing_rules`、`all_datasets`
    - `app_jwt.py`：應用層 JWT 簽發與驗證
- utils/：工具函式與格式處理（JSON 修復、節流邏輯、時間軸 PDF、token 計算等）

## 功能總覽

1. 內容生成

- 生成計畫內容
- 版本改寫
- 文件自動填寫
- 單欄位檔案分析
- 專案名稱推薦

2. 專案管理

- 建立、查詢、更新專案
- 取得章節設定
- 產生 AI 執行時間軸
- 匯出時間軸 PDF

3. 模板管理

- Grant / Template / Section CRUD
- 動態章節與欄位管理
- Template Logo 上傳

4. 資料集與模型治理

- 資料集 CRUD
- 敏感詞建議
- 模型清單與路由規則管理
- 快取刷新

5. 圖片流程

- Prompt 強化
- 圖片生成
- 圖片查詢與刪除

6. 認證與權限

- 目前登入者資訊
- 輕量登入狀態檢查
- 外部 OAuth 登入與登出

## 快速開始（本機）

### 1. 安裝套件

pip install -r requirements.txt

### 2. 建立環境變數檔

在 backend 根目錄建立 .env，至少需要：

SUPABASE_URL=
SUPABASE_SERVICE_KEY=
DATABASE_URL=

OPENAI_API_KEY=
GEMINI_API_KEY=

APP_JWT_SECRET=

EXTERNAL_OAUTH_PROVIDER=tgsa_oauth
EXTERNAL_OAUTH_CLIENT_ID=
EXTERNAL_OAUTH_CLIENT_SECRET=
EXTERNAL_OAUTH_AUTHORIZE_URL=
EXTERNAL_OAUTH_TOKEN_URL=
EXTERNAL_OAUTH_USERINFO_URL=
EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL=http://localhost:3000/external-auth-callback

EMBEDDING_MODEL_NAME=BAAI/bge-small-en

### 3. 啟動服務

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

### 4. 開發文件

Swagger UI:
http://localhost:8000/docs

OpenAPI JSON:
http://localhost:8000/openapi.json

## Docker 啟動（配合專案根目錄）

docker compose up -d

查看狀態：
docker compose ps

查看後端 log：
docker compose logs -f --tail=200 fastapi-backend

## 主要 API 分類

- Auth
  - GET /api/auth/me
  - GET /api/auth/status

- Generate
  - POST /api/generate_plan
  - POST /api/revise_plan_version
  - POST /api/generate_synthetic_input
  - POST /api/recommend_project_names
  - POST /api/autofill_from_document
  - POST /api/field_file_analysis
  - **WS /api/ws/chat_guidance** — 互動式 AI 對話引導（streaming）

- Projects
  - GET /api/projects
  - GET /api/projects/{project_id}
  - POST /api/projects
  - PUT /api/projects/{project_id}
  - GET /api/projects/{project_id}/timeline
  - GET /api/projects/{project_id}/timeline/pdf

- Datasets
  - POST /api/datasets
  - GET /api/datasets
  - PUT /api/datasets/{dataset_id}
  - DELETE /api/datasets/{dataset_id}
  - POST /api/datasets/sensitive-terms/suggest

- Template Manager
  - /api/template-manager/grants
  - /api/template-manager/templates
  - /api/template-manager/sections

- Dynamic Sections
  - /api/dynamic-sections
  - /api/dynamic-sections/sections
  - /api/dynamic-sections/fields

- Images
  - GET /api/images
  - POST /api/images/enrich-prompt
  - POST /api/images/generate
  - DELETE /api/images/{image_id}

- Usage Analytics
  - GET /api/usage-log/analytics

- External Auth
  - GET /api/external-auth/redirect
  - GET /api/external-auth/callback
  - POST /api/external-auth/logout

## 啟動流程與快取機制

服務啟動時會預載以下資料到 `app.state`：

- `app.state.model_registry`：模型登錄表
- `app.state.routing_rules`：模型路由規則
- `app.state.all_grants_config`：grant / template / section 完整配置（**Phase 1 P0 優化的核心快取**）
- `app.state.all_datasets`：few-shot 範例資料集

**P0 優化後的快取讀取流程：**

- `GET /api/projects`、`GET /api/config`、`POST /api/generate_plan` 等高頻端點優先從 `app.state.all_grants_config` 讀取，跳過昂貴的 catalog 查詢
- `template_manager.py` 在所有 grant / template / section CRUD 後自動呼叫 `_refresh_grant_cache()` 確保快取與 DB 同步
- WebSocket 端點 `/ws/chat_guidance` 與 REST 端點共用 `AUTH_CONTEXT_CACHE`（20 秒 TTL），跨協定避免重複的 JWT 驗證

**手動刷新快取：**

- `POST /api/config/refresh`：重新載入 grants / templates / sections + models + routing rules + datasets
- `POST /api/refresh-datasets`：僅刷新資料集

## 資料儲存重點

主要資料在 Supabase PostgreSQL，**Schema：`ai_proposal_platform`**（共 18 個應用資料表）：

- 使用者類：`users`、`user_identities`、`whitelist`
- 配置類：`grants`、`plan_templates`、`sections`、`section_schema_versions`、`dynamic_sections`、`dynamic_fields`、`models`、`routing_rules`
- 專案類：`projects`、`commands`、`draft_plans`、`images`
- 紀錄類：`datasets`、`usage_logs`、`execution_logs`

**複合主鍵注意事項：**

- `plan_templates`：複合鍵 `(id, grant_id)`
- `sections`：複合鍵 `(id, template_id, grant_id)` — 章節 ID 為可複用字串

Storage buckets：

- datasets
- logos

Schema 遷移指南：`../database-backup-migrate-schema.md`

## 權限模型（概念）

- **混合身份驗證：** Supabase Auth（Email / Password）+ 外部 OAuth（TGSA Provider）
- **角色（user role）：**
    - `normal`：一般使用者，1 個專案配額，每日 1,000,000 token 上限，達閾值後 30 秒節流
    - `vip`：付費使用者，50 個專案配額，token 無上限（節流閾值設為 99999 等同停用）
    - `internal`：內部 / 員工，由 `whitelist` 表自動判定，可存取 `/_builder/*` 管理工具
- **依賴函式：**
    - `get_current_user_id` / `get_current_user_context`：解析 token 並回傳標準化 user context
    - `verify_internal_user`：驗證 `role == 'internal'`，用於管理 API
- **認證快取：** `AUTH_CONTEXT_CACHE`（dict，20 秒 TTL）跨 REST 與 WebSocket 共用，避免重複的 Supabase 驗證
- **外部 OAuth 流程：** `/api/external-auth/redirect` -> 第三方授權 -> `/api/external-auth/callback` -> 換發 `app_access_token` cookie

## 常見維運指令

重啟後端：
docker compose restart fastapi-backend

查看錯誤：
docker compose logs fastapi-backend --tail=300

重新部署後健康檢查：

- GET /
- GET /docs
- GET /api/auth/status

## 故障排查建議

1. 啟動失敗

- 檢查 .env 是否缺少必要變數
- 檢查 DATABASE_URL 與 SUPABASE_SERVICE_KEY 是否可用

2. 生成失敗

- 檢查 OPENAI_API_KEY / GEMINI_API_KEY
- 檢查模型路由規則與 model registry 是否已載入

3. OAuth 失敗

- 檢查 EXTERNAL*OAUTH*\* 相關設定
- 檢查 callback URL 與 provider 設定是否一致

4. 圖片或 logo 連結異常

- 檢查 Supabase Storage bucket 權限
- 檢查反向代理路徑 /supabase 是否正常

## 安全注意事項

- 不要提交任何 .env 到版本庫
- 不要在 log 中輸出敏感金鑰
- 建議定期輪替 API 金鑰與服務憑證
- 對管理端 API 使用最小權限原則

## 效能基準

後端已完成 Phase 1 完整壓力測試與 P0 優化（catalog cascade cache + WebSocket auth cache）。最新成果：

- `/api/projects` p95（50 VU）：1,311 ms
- `/api/config` p95（50 VU）：1,938 ms
- WebSocket cold（100 VU）：513 ms
- `/api/auth/me` p95（100 VU）：135 ms

完整測試報告與優化路線圖：`../stress-tests/README.md` 與 `../stress-tests/reports/`

## License

Internal use only.
