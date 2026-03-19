# 補助引擎（AI Proposal, AP）

補助引擎（AI Proposal, AP）是一套以 AI 驅動的提案與計畫書生成平台，利用大型語言模型與結構化 Schema 流程，支援多模板、多章節、版本管理、資料集治理與模型路由，提供從內容生成到部署維運的完整能力。

## 核心功能

### 內容生成

- 依 Grant / Template / Section 生成計畫內容
- 支援多候選版本（candidate）與版本改寫（revise）
- 依 JSON Schema 產生可驗證的結構化輸出
- 支援從文件自動填寫章節內容與欄位分析

### 計畫與模板管理

- 多層級結構管理：Grant -> Template -> Section
- 章節設定版本化（schema/prompt version）
- 動態章節與動態欄位管理（Dynamic Sections / Fields）
- Template Logo 與視覺配置管理

### 數據集與模型治理

- 資料集 CRUD（含來源類型與內容更新）
- 敏感詞建議與資料清理輔助
- 模型路由規則（Routing Rules）與優先序管理
- 使用量分析（成本、Token、趨勢）

### 專案管理與可追溯性

- 專案 CRUD 與章節配置對應
- AI 執行時間軸（timeline）查詢
- 時間軸 PDF 匯出
- execution logs 與 usage logs 追蹤

### 圖片與輔助能力

- 圖片提示詞強化（Prompt Enrichment）
- 圖片生成與專案圖片管理
- 外部 OAuth 登入流程整合

## 系統架構

### 後端技術棧

- FastAPI + Uvicorn
- Supabase（PostgreSQL + Storage）
- SQLAlchemy
- fastembed（向量嵌入）
- OpenAI / Gemini API
- PyJWT

### 前端技術棧

- Nuxt 3（Vue 3 + TypeScript）
- Tailwind CSS
- Supabase JS SDK
- Nuxt Icon / Heroicons

### 部署架構

- Docker Compose 多容器部署
- `fastapi-backend`：後端 API
- `nuxt-frontend`：前端 SSR/SPA
- `nginx-proxy`：反向代理與 TLS 入口

## 專案結構

```text
.
├── backend/                   # 後端服務專案根目錄
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── core/              # 啟動生命週期與核心流程
│   │   ├── services/          # LLM / Supabase 服務層
│   │   ├── utils/             # 共用工具
│   │   ├── config.py          # 環境變數與常數
│   │   ├── main.py            # FastAPI 入口
│   │   └── models.py          # Pydantic 模型
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── frontend/                  # 前端服務專案根目錄
│   ├── components/            # UI 元件（chat、manager、global）
│   ├── composables/           # 業務邏輯 hooks
│   ├── layouts/               # 全域版型（頁面框架）
│   ├── middleware/            # 認證與導向守衛
│   ├── pages/                 # Nuxt 路由頁面
│   ├── plugins/               # Nuxt 插件（client/server 注入）
│   ├── utils/                 # 前端工具函式
│   ├── app.vue
│   ├── nuxt.config.ts
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
├── nginx/                     # 反向代理設定與映像建置檔
│   ├── nginx.conf             # Nginx 路由、SSL、proxy 規則
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 前後端結構細化

### Backend 模組重點

- `app/api/generate.py`：生成、改寫、文件填寫、欄位分析
- `app/api/projects.py`：專案 CRUD、時間軸、PDF
- `app/api/template_manager.py`：Grant/Template/Section 管理
- `app/api/datasets.py`：資料集與敏感詞建議
- `app/api/dynamic_section.py`：動態章節欄位管理
- `app/api/images.py`：圖片查詢、生成、刪除
- `app/api/usage_log.py`：使用量分析
- `app/api/external_auth.py`：外部 OAuth 流程

### Frontend 模組重點

- `pages/projects/*`：專案操作與編修流程
- `pages/plan-library.vue`：計畫庫管理
- `pages/command-library.vue`：指令庫管理
- `components/chat/*`：互動生成區塊
- `components/template-manager/*`：模板管理 UI
- `composables/useAppAuth.ts`：登入會話與 token 流程
- `middleware/auth.ts`：登入與內部角色檢查

## 快速開始

### 前置需求

- Docker + Docker Compose v2
- 本機開發：Python 3.10、Node.js 20+
- Supabase 專案與 API Key
- OpenAI / Gemini API Key

### 方式一：Docker Compose（建議）

```bash
docker compose up -d
docker compose ps
docker compose logs -f --tail=200 fastapi-backend nuxt-frontend nginx-proxy
```

### 方式二：本機分開啟動

1. 後端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. 前端

```bash
cd frontend
npm install
npm run dev
```

## 環境變數配置

### backend/.env（主要）

```env
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
```

### frontend/.env（主要）

```env
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

## API 端點（概要）

### 生成相關

- `POST /api/generate_plan`
- `POST /api/revise_plan_version`
- `POST /api/generate_synthetic_input`
- `POST /api/autofill_from_document`
- `POST /api/field_file_analysis`

### 專案相關

- `GET /api/projects`
- `GET /api/projects/{project_id}`
- `POST /api/projects`
- `PUT /api/projects/{project_id}`
- `GET /api/projects/{project_id}/timeline`
- `GET /api/projects/{project_id}/timeline/pdf`

### 配置與管理

- `GET /api/config`
- `POST /api/config/refresh`
- `POST /api/refresh-datasets`
- `GET /api/template-manager/*`
- `GET /api/dynamic-sections`

### 分析與認證

- `GET /api/usage-log/analytics`
- `GET /api/auth/me`
- `GET /api/auth/status`
- `GET /api/external-auth/redirect`

## 主要工作流程

### 1. 計畫書生成流程

1. 使用者輸入核心需求與專案背景
2. 依後端 Grant/Template/Section 與路由規則選擇模型
3. 並行生成候選版本與格式化內容
4. 使用者選擇版本、再改寫或手動編修
5. 內容回寫專案與執行紀錄

### 2. 設定載入流程

1. 啟動時初始化 SupabaseService / LLMService
2. 載入 models、routing rules、grants config、datasets 到 app state
3. 後續 API 依快取與即時查詢混合運行
4. 設定調整後透過 refresh API 手動刷新

### 3. 批次與資料集流程

1. 產生 synthetic input 或批次草稿
2. 生成內容後寫入 datasets
3. 由管理頁進行篩選、更新、刪除

## 數據流（摘要）

```text
前端請求 -> API 路由 -> 模型路由/LLM 服務 -> 結果解析格式化
        -> Supabase 寫入（projects/datasets/logs） -> 前端回顯
```

## 部署與維運

### 服務入口

- 前端：`/`
- 後端 API：`/api/`
- Supabase 代理：`/supabase/`、`/auth/v1/`

### 例行維運指令

```bash
docker compose ps
docker compose restart fastapi-backend
docker compose logs -f --tail=200 fastapi-backend
docker compose logs -f --tail=200 nuxt-frontend
docker compose logs -f --tail=200 nginx-proxy
```

### 備份方案（建議）

- 使用 Rclone + Cron 定時將 PostgreSQL 備份上傳 Google Drive
- 建議每日執行，至少保留 30 天滾動版本
- 備份腳本可拆分 roles/schema/data 以利還原

## 常見問題

### 前端 API 請求失敗

- 檢查 `NUXT_PUBLIC_API_BASE_URL` 是否正確
- 檢查 Nginx `/api/` 轉發與後端服務狀態

### 登入後被導回登入頁

- 檢查 `/api/auth/status` 是否正常
- 檢查 cookie 與 token 是否正確

### 內部頁面 `/_builder` 無法進入

- 檢查 `/api/auth/me` 回傳 role 是否為 `internal`

### 資料庫連線錯誤

- 檢查 `DATABASE_URL` 與 `SUPABASE_SERVICE_KEY`
- 確認 Supabase 網路連通性

## 文件索引

- 後端詳細文件：`backend/README.md`
- 前端詳細文件：`frontend/README.md`

## License

Internal use only.

## Version

### v1.0.0

初始版本包含：

- 計畫書生成
- 數據集管理
- 模型路由
- 配置管理
- 合成數據生成
