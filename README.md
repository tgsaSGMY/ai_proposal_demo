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
- Supabase（PostgreSQL + Storage + Auth + Realtime）
- SQLAlchemy
- fastembed（`BAAI/bge-small-en` 向量嵌入；用於 few-shot 範例檢索）
- 多 LLM 供應商整合：
    - OpenAI GPT-5 系列（`gpt-5`、`gpt-5-mini`、`gpt-5-nano`、`gpt-5.1-chat-latest`、`gpt-4.1-mini`、`gpt-4.1-nano`）
    - Google Gemini（`gemini-3-pro-preview`、`gemini-3-flash-preview`、`gemini-2.5-pro`、`gemini-2.5-flash-lite`）
    - Google Imagen（`imagen-4.0-generate-001`、`gemini-3-pro-image-preview`）— 圖片生成
    - Ollama（本地模型，可選）
- PyJWT（內部 app token）
- 啟動時預載入 `app.state.all_grants_config` 快取（catalog cascade 已於 P0 優化中解決）

### 前端技術棧

- Nuxt 3（Vue 3 + TypeScript）
- Tailwind CSS
- Supabase JS SDK
- Nuxt Icon / Heroicons
- `docx`（Word 文件生成）、`mammoth`（Word 解析）、`pdfjs-dist`（PDF 解析）

### 部署架構

- Docker Compose 多容器部署
- `fastapi-backend`：後端 API
- `nuxt-frontend`：前端 SSR/SPA
- `nginx-proxy`：反向代理與 TLS 入口（生產環境）；Dev VPS 使用 Nginx Proxy Manager（NPM）
- CI/CD：GitHub Actions 自動部署 dev / prod 分支
- 部署設定檔：`docker-compose.yml`（生產）、`docker-compose.beta.yml`（Dev VPS / Beta）

## 資料庫 Schema

- **Schema 名稱：** `ai_proposal_platform`（Test / Dev VPS 已遷移；Live 待遷移自 `public`）
- **資料表：** 共 18 個應用資料表
    - 使用者類：`users`、`user_identities`、`whitelist`
    - 專案類：`projects`、`commands`、`draft_plans`、`images`
    - 配置類：`grants`、`plan_templates`、`sections`、`section_schema_versions`、`dynamic_sections`、`dynamic_fields`、`models`、`routing_rules`
    - 資料 / 紀錄類：`datasets`、`usage_logs`、`execution_logs`
- **複合主鍵設計：**
    - `plan_templates`: `(id, grant_id)`
    - `sections`: `(id, template_id, grant_id)`
    - 章節 ID 為可複用的字串（如 `company_overview`），靠複合鍵保證唯一性
- **遷移指南：** 參見 `database-backup-migrate-schema.md`

## 專案結構

```text
.
├── backend/                   # 後端服務專案根目錄
│   ├── app/
│   │   ├── api/               # API 路由（14 個 router 模組）
│   │   ├── core/              # 啟動生命週期與核心流程
│   │   ├── services/          # LLM / Supabase 服務層
│   │   ├── utils/             # 共用工具（JSON 修復、節流、時間軸 PDF 等）
│   │   ├── config.py          # 環境變數與常數
│   │   ├── main.py            # FastAPI 入口
│   │   └── models.py          # Pydantic 模型
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── frontend/                  # 前端服務專案根目錄
│   ├── components/            # UI 元件（chat、word-editor、template-manager、global）
│   ├── composables/           # 業務邏輯 hooks（auth、Word 編號、敏感資料遮罩）
│   ├── layouts/               # 全域版型（頁面框架）
│   ├── middleware/            # 認證與導向守衛
│   ├── pages/                 # Nuxt 路由頁面（含 _builder/* 管理端）
│   ├── plugins/               # Nuxt 插件（client/server 注入）
│   ├── utils/                 # 前端工具函式（exportToWord、Supabase 客戶端等）
│   ├── app.vue
│   ├── nuxt.config.ts
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
├── nginx/                     # 反向代理設定與映像建置檔
│   ├── nginx.conf             # Nginx 路由、SSL、proxy 規則
│   └── Dockerfile
├── stress-tests/              # 壓力測試與效能驗證
│   ├── *.js / *.py            # k6（REST/WebSocket）+ Locust（AI Generation）測試腳本
│   ├── reports/               # Phase 1 / 優化前後測試報告與基準資料
│   ├── test-plans/            # 測試規劃、端點覆蓋表、優化路線圖
│   ├── .env.testing           # 測試環境變數（不入版）
│   └── README.md
├── docker-compose.yml         # 生產部署設定
├── docker-compose.beta.yml    # Dev VPS / Beta 部署設定
├── docker-compose.dev.yml     # 本機開發設定
├── STATUS.md                  # 專案開發狀態（最新更新）
├── dev-vps.md                 # 開發 VPS 設定指南
├── database-backup-migrate-schema.md  # 資料庫備份與 schema 遷移指南
├── Stress-Test-Proposal.md    # 壓力測試提案
└── README.md
```

## 前後端結構細化

### Backend 模組重點（14 個 Router 模組）

#### 使用者端
- `app/api/auth.py`：目前登入者資訊與輕量狀態檢查
- `app/api/external_auth.py`：外部 OAuth（TGSA Provider）登入流程
- `app/api/projects.py`：專案 CRUD、章節設定、時間軸、PDF
- `app/api/generate.py`：生成、改寫、文件填寫、欄位分析、專案名稱推薦、互動聊天（WebSocket `/ws/chat_guidance`）
- `app/api/draft_plan.py`：草稿計畫 CRUD 與批次合成生成
- `app/api/commands.py`：使用者自訂背景資料（指令）
- `app/api/images.py`：圖片查詢、生成、Prompt 強化、刪除
- `app/api/section_recommender.py`：章節推薦

#### 管理端
- `app/api/template_manager.py`：Grant / Template / Section CRUD + Schema 版本管理 + Word 視覺化編輯器設定
- `app/api/dynamic_section.py`：動態章節與欄位管理
- `app/api/datasets.py`：資料集 CRUD + 敏感詞建議
- `app/api/admin.py`：模型登錄（model registry）、路由規則、章節 prompt、使用統計
- `app/api/config.py`：應用配置（grants/templates/sections 快取讀取、刷新）
- `app/api/usage_log.py`：使用量分析與統計

### Frontend 模組重點

#### 使用者端頁面
- `pages/index.vue`：首頁與計畫類型選擇
- `pages/login.vue`：登入頁
- `pages/projects/[id].vue`：專案 AI 工作區（互動聊天 / 生成 / 改寫）
- `pages/plan-library.vue`：計畫庫
- `pages/command-library.vue`：背景資料庫（自訂指令）
- `pages/external-auth-callback.vue`：OAuth 回呼

#### 管理端頁面（`role=internal` 才可存取）
- `pages/_builder/template-manager.vue`：模板與章節管理 + Word 視覺化編輯器
- `pages/_builder/section.vue`：章節編輯器
- `pages/_builder/dataset.vue`：資料集（DPO / 訓練資料）管理
- `pages/_builder/model.vue`：模型路由配置
- `pages/_builder/management.vue`：管理面板總覽
- `pages/_builder/usage-analytics.vue`：使用分析儀表板
- `pages/_builder/login.vue`、`signup.vue`、`forgot-password.vue`、`reset-password.vue`：管理員身份相關頁面

#### 共用元件與邏輯
- `components/chat/*`：互動聊天區塊（streaming WebSocket 對話）
- `components/word-editor/*`：Word 視覺化模板樹狀編輯器
- `components/template-manager/*`：模板管理 UI
- `components/global/*`：全域元件（Loading、通知等）
- `composables/useAppAuth.ts`：登入會話與 token 流程
- `composables/usePlanGenerator.ts`：計畫產生流程整合
- `composables/useWordNumbering.ts`：Word 章節 / 子標題編號邏輯
- `composables/useSensitiveMasking.ts`：敏感資料遮罩
- `composables/useLoading.ts`、`useNotifications.ts`：全域 UX 工具
- `utils/exportToWord.ts`：Word 文件匯出引擎
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
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

## 效能與測試

平台已完成 **Phase 1 完整壓力測試**（4 個 tier，342,000 次請求，27 個獨立測試 run）並於 2026-04-28 部署 P0 後端優化。

### 測試覆蓋
| Tier | 測試範圍 | 結果 |
|------|---------|------|
| Tier 1 | Auth / 控制端點（auth/me、auth/status、commands） | ✅ 通過 |
| Tier 2 | DB 讀取（projects/{id}、draft_plans、plan_templates） | ✅ 通過 |
| Tier 3 | 診斷（config — 確認 catalog cascade 假設） | ✅ 通過 |
| Tier 4 | AI Generation（Locust）+ WebSocket（k6 50/100/200 VU） | ✅ 通過 |
| 優化後 | `/api/projects` + `/api/config` + WebSocket 重新測試 | ✅ 通過 |

### P0 優化成果（已部署）
- `/api/projects` p95（50 VU）：19,579 ms → **1,311 ms**（15× 加速）
- `/api/config` p95（50 VU）：16,572 ms → **1,938 ms**（8.5× 加速）
- WebSocket cold p95（100 VU）：2,864 ms → **513 ms**（5.6× 加速）
- 快取端點 RPS 上限：3 RPS → **25-41 RPS**

### 生產就緒狀態
- **目標使用者規模：** 300 名使用者（2 個月內）
- **狀態：** ✅ 生產就緒，現有 Dev VPS 硬體（2 vCPU / 4 GB RAM）對 300 人目標保有充裕餘裕
- **詳細報告：** `stress-tests/reports/Phase1-production-readiness-summary.md`、`Post-Optimization-DBH-stress-test-report.md`
- **未來優化路線圖：** `stress-tests/test-plans/optimization-roadmap.md`（含 P1/P2/P3 觸發條件）

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

### 模組文件
- `backend/README.md` — 後端詳細文件
- `frontend/README.md` — 前端詳細文件
- `stress-tests/README.md` — 壓力測試與效能驗證指南

### 專案狀態與規劃
- `STATUS.md` — 專案開發狀態與最新進度（**最新狀態請以此檔為準**）
- `Stress-Test-Proposal.md` — 壓力測試提案

### 部署與運維
- `dev-vps.md` — 開發 VPS 設定與部署指南
- `database-backup-migrate-schema.md` — 資料庫備份與 Schema 遷移指南
- `custom-sql.txt` — SQL 腳本歷史紀錄
- `db_schema.txt` — 資料庫 schema 快照

### 測試與優化報告
- `stress-tests/reports/Phase1-production-readiness-summary.md` — Phase 1 整體測試彙整與生產就緒判定
- `stress-tests/reports/Post-Optimization-DBH-stress-test-report.md` — P0 優化驗證報告（5-step 整合）
- `stress-tests/test-plans/optimization-roadmap.md` — 優化路線圖（含 P1/P2/P3 觸發條件）
- `stress-tests/test-plans/endpoint-coverage-plan.md` — 端點測試策略

## License

Internal use only.

## Version

### v1.1.0（2026 Q2，當前版本）

主要新增：

- **Word 視覺化編輯器：** 樹狀模板節點編輯（sectionTitle、subHeading、paragraph、table、customTable、list、customText、imagePlaceholder），支援版本快照與「同步遺失章節」修復邏輯
- **Schema 版本管理：** `section_schema_versions` 表追蹤章節 JSON Schema 演進，專案綁定特定版本
- **混合身份驗證：** Supabase Auth + 外部 OAuth（TGSA Provider）整合
- **使用量配額系統：** 依角色（normal / vip / internal）區分的每日 token 上限與 30 秒節流邏輯
- **管理端工具：** 模板管理 / 模型路由 / 資料集 / 使用分析儀表板（`_builder/*`）
- **互動式 AI 工作區：** WebSocket 即時對話引導（`/ws/chat_guidance`）
- **批次合成資料生成：** 用於 fine-tuning / DPO 訓練資料準備
- **資料庫 schema 遷移：** 從 `public` 遷移至 `ai_proposal_platform`（Test 已完成，Live 待遷移）
- **Phase 1 壓力測試完成：** 4 個 tier 全覆蓋 + P0 後端優化已部署（catalog cascade cache + WebSocket auth cache）

### v1.0.0（初始版本）

- 計畫書生成
- 數據集管理
- 模型路由
- 配置管理
- 合成數據生成

> 完整最新進度請參考 `STATUS.md`。

## Demo → Parent Platform Claim Contract (Phase 9)

When a demo visitor clicks the upsell CTA, the demo redirects them to:

```
https://aiproposal.tgsa.com.tw/api/external-auth/redirect?ref=<demo_session_id>
```

The parent platform (`ai_proposal_platform` repo) handles `?ref` as follows:

1. `/api/external-auth/redirect` validates `ref` is a UUID, sets an HttpOnly
   `pending_demo_claim=<ref>` cookie (SameSite=Lax, max-age=900s), and
   continues the existing OAuth flow to portal.tgsaapp.com.
2. `/api/external-auth/callback` reads the cookie after auth succeeds and
   calls `claim_demo_session(ref, user_id)`, which atomically:
   - Locks the `ai_proposal_platform.demo` row.
   - Inserts a `projects` row owned by the new user, populated from
     `saved_plan`, `stored_answer`, `conversation_history`, `grant_id`,
     `template_id` on the demo row.
   - Marks the demo row `status='claimed'` with `claimed_by_user_id`,
     `claimed_project_id`, `claimed_at`.
3. On success, the user lands on `https://aiproposal.tgsa.com.tw/projects/<new_id>`.
4. On failure (not_found, already_claimed_by_other), the user lands on the
   default post-login destination with no error surfaced.

### Schema additions (run once against shared Supabase)

See `database-migrations/001_demo_claim_columns.sql`. Adds `status`,
`claimed_by_user_id`, `claimed_project_id`, `claimed_at` columns + a
partial index on `session_id WHERE status='active'`.

### Field mapping (demo → projects)

| demo column | projects column |
|---|---|
| `grant_id` | `grant_id` |
| `template_id` | `template_id` |
| `saved_plan` | `saved_plan` |
| `stored_answer` | `stored_answer` |
| `conversation_history` | `conversation_history` |
| `stored_answer->>'plan_name'` (fallback `"從 Demo 匯入的計畫書"`) | `title` |
| n/a (literal `'互動'`) | `mode` |
| `claimed_by_user_id` (set on demo row) | `user_id` (on new projects row) |
