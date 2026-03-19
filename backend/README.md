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
- FastAPI
- Uvicorn
- Supabase (PostgreSQL + Storage)
- SQLAlchemy
- fastembed (向量嵌入)
- OpenAI / Gemini API
- PyJWT

## 專案結構

app/

- main.py：FastAPI 入口，註冊路由與 CORS
- config.py：環境變數與系統常數
- models.py：Pydantic 資料模型
- api/：API 路由模組
- services/：Supabase 與 LLM 服務層
- core/：啟動與生命週期管理
- utils/：工具函式與格式處理

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

服務啟動時會預載以下資料到記憶體：

- model registry
- routing rules
- grant/template/section config
- datasets

若後台有改設定，請呼叫：

- POST /api/config/refresh
- POST /api/refresh-datasets

## 資料儲存重點

主要資料在 Supabase PostgreSQL，包含：

- users, user_identities
- grants, plan_templates, sections, section_schema_versions
- projects, execution_logs
- datasets, usage_logs, routing_rules
- commands, images
- dynamic_sections, dynamic_fields
- draft_plans, whitelist

Storage buckets：

- datasets
- logos

## 權限模型（概念）

- 一般使用者：以登入 token 存取自己的專案與資源
- 內部管理：部分管理 API 需 verify_internal_user
- 外部 OAuth 使用者：由 external-auth 流程換發 app_access_token

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

## License

Internal use only.
