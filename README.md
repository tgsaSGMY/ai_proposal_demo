# AI 補助引擎 — Demo 版本（AI Proposal Demo）

> **免費體驗版**：讓匿名訪客無需登入即可體驗 AI 驅動的 SBIR Phase 1 計畫書生成，並在達到使用上限後無縫遷移至完整平台。

---

## 專案概述

AI 補助引擎 Demo 是完整平台（`ai_proposal_platform`）的**硬分支（hard fork）**精簡版本。與完整平台支援多補助計畫、多模板、管理後台與認證流程不同，**Demo 版本**專注於單一目的：

> **讓任何訪客免費體驗 AI 驅動的 SBIR Phase 1 計畫書生成，並在達到硬上限後無縫轉移會話至完整平台註冊使用。**

### 訪客旅程

```
匿名訪客
  ↓
進入 demo-aiproposal.tgsa.com.tw（無需登入）
  ↓
直接進入 AI 聊天工作區（僅限 SBIR Phase 1）
  ↓
與 AI 互動填寫欄位（最多 20 輪對話）
  ↓
生成計畫書草稿（每會話限 1 次）
  ↓
預覽草稿 + 註冊提示
  ↓
點擊「免費註冊」→ 導向完整平台
  ↓
會話資料遷移 → 在 aiproposal.tgsa.com.tw 繼續編輯
```

---

## 核心功能

### AI 互動引導

- 透過 WebSocket 即時對話引導使用者填寫計畫書欄位
- 自動解析隱藏回復欄位格式，將答案寫入會話狀態
- 追蹤未填欄位，智慧提示下一題
- 支援候選版本生成（多選一）與版本改寫

### 計畫書生成

- 依已填寫欄位自動生成完整 SBIR Phase 1 計畫書
- 每個章節並行生成多個候選版本供選擇
- 基於既有版本進行優化改寫（revise）
- 根據已填欄位推薦專案名稱

### 使用限制與遷移

| 限制 | 數值 | 說明 |
|------|------|------|
| 對話輪數 | 20 | 每會話上限，可透過 `.env` 調整 |
| Token 用量 | 100,000 | 累計上限，超過即觸發註冊提示 |
| 計畫書生成 | 1 次 | `has_generated_docx` 標記 |
| 下載次數 | 1 次 | `download_count` 計數 |
| IP 每小時會話 | 3 次 | 基礎防濫用（目前未啟用） |
| IP 每日會話 | 5 次 | 基礎防濫用（目前未啟用） |
| 會話保留期 | 7 天 | 過期後自動清理 |

- 達到上限後顯示「免費註冊」CTA，導向完整平台 OAuth 註冊
- 註冊後會話資料（對話歷史、已填答案、生成計畫、執行紀錄、用量紀錄）自動遷移至新帳號

---

## 系統架構

### 後端技術棧

- **FastAPI + Uvicorn** — API 與 WebSocket 服務
- **Supabase（PostgreSQL）** — 與完整平台**共用**同一資料庫，確保無縫遷移
- **SQLAlchemy** — 直接 PostgreSQL 連線（用於 rate limiter 原子操作）
- **多 LLM 供應商整合：**
  - OpenAI GPT-5 系列（`gpt-5.1-chat-latest`、`gpt-4.1-mini` 等）
  - Google Gemini（`gemini-3-flash-preview`、`gemini-3-pro-preview` 等）
- **啟動時預載** `app.state.all_grants_config` 與 `model_registry`

### 前端技術棧

- **Nuxt 3（Vue 3 + TypeScript）**
- **Tailwind CSS**
- **Nuxt Icon / Heroicons**
- `docx`（Word 文件生成）、`mammoth`（Word 解析）

### 部署架構

- Docker Compose 多容器部署
- `fastapi-backend`：後端 API（3 個 router）
- `nuxt-frontend`：前端 SSR/SPA
- `nginx-proxy`：反向代理與 TLS 入口
- CI/CD：GitHub Actions 自動部署 dev / prod 分支
- 部署設定檔：`docker-compose.yml`（生產）、`docker-compose.beta.yml`（Dev VPS）

---

## 資料庫 Schema

### 核心資料表

- **Schema：** `ai_proposal_platform`（與完整平台共用）
- **Demo 專用資料表：**
  - `demo` — 匿名會話核心狀態（對話歷史、答案、生成計畫、用量紀錄、遷移狀態）
  - `demo_ip_limits` — IP 速率限制計數器（小時/日視窗）

### `demo` 資料表欄位摘要

| 欄位 | 說明 |
|------|------|
| `session_id` | 瀏覽器 Cookie UUID（唯一鍵） |
| `interaction_count` | 對話輪數計數 |
| `conversation_history` | 聊天記錄 JSONB |
| `stored_answer` | 使用者答案與元資料 |
| `saved_plan` | 生成的計畫版本 |
| `pending_execution_events` | 待遷移的執行事件 |
| `pending_usage_logs` | 待遷移的用量紀錄 |
| `has_generated_docx` | 是否已生成報告 |
| `download_count` | 下載次數 |
| `title` | 使用者編輯的專案名稱 |
| `section_versions` | 章節版本快照 |
| `status` | `active` / `claimed` / `expired` |
| `expires_at` | 會話過期時間 |
| `claimed_by` / `claimed_at` / `claimed_project_id` | 遷移後標記 |

### 資料庫遷移檔案

| 檔案 | 用途 |
|------|------|
| `database-migrations/001_demo_claim_columns.sql` | 增加 `status`、`claimed_by`、`claimed_at`、`claimed_project_id` |
| `database-migrations/002_demo_download_count.sql` | 增加 `has_generated_docx`、`download_count` |
| `database-migrations/003_demo_schema_update.sql` | 增加 `section_versions` + 完整 `migrate_demo_to_project()` 函數 |

---

## 專案結構

```text
.
├── backend/                   # 後端服務
│   ├── app/
│   │   ├── api/               # API 路由（3 個 router）
│   │   │   ├── generate.py    # 生成、改寫、WebSocket 聊天、名稱推薦
│   │   │   ├── projects.py    # Demo 會話 CRUD、狀態、動態欄位
│   │   │   ├── config.py      # 配置讀取（grants / templates）
│   │   │   ├── dependencies.py # 依賴注入（Cookie session、rate limiter）
│   │   ├── core/              # 啟動生命週期
│   │   ├── services/          # LLM / Supabase 服務層
│   │   ├── utils/             # 工具（IP 提取、Rate Limiter）
│   │   ├── config.py          # 環境變數與常數
│   │   ├── main.py            # FastAPI 入口
│   │   └── models.py          # Pydantic 模型
│   ├── tests/                 # 測試（demo session、rate limiter、IP 提取）
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── frontend/                  # 前端服務
│   ├── components/            # UI 元件
│   │   ├── chat/
│   │   │   ├── DemoChatbox.vue       # Demo 聊天工作區
│   │   │   └── helper/
│   │   │       └── DemoRegisterModal.vue  # 註冊提示彈窗
│   ├── composables/           # 業務邏輯 hooks
│   │   ├── useDemoSession.ts  # 單一會話 bootstrap（防並行 mint）
│   │   ├── useAppAuth.ts      # 認證工具（無 Bearer token）
│   │   └── usePlanGenerator.ts # 計畫生成流程
│   ├── pages/                 # Nuxt 路由
│   │   └── index.vue          # 根路徑 = Demo 工作區（無 landing page）
│   ├── middleware/
│   │   └── auth.ts            # 認證中間件（放行根路徑）
│   ├── utils/                 # 工具（exportToWord、Supabase 客戶端）
│   ├── nuxt.config.ts
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
├── nginx/                     # 反向代理
│   ├── nginx.conf
│   ├── nginx.dev.conf
│   └── Dockerfile
├── database-migrations/       # 資料庫遷移腳本
├── docs-private/              # 內部文件
│   ├── specs/
│   │   └── 2026-06-16-demo-to-platform-signup-handoff-design.md
│   ├── to-do-lists.md
│   └── demo_migration.sql
├── scripts/                   # 輔助腳本
│   └── verify-demo.ps1
├── docker-compose.yml         # 生產部署
├── docker-compose.beta.yml    # Dev VPS / Beta
├── .github/workflows/          # CI/CD
│   └── deploy-dev.yml
├── STATUS.md                  # 專案狀態（最新更新）
├── dev-vps.md                 # Dev VPS 設定指南
├── next-implementation.md       # 原始實作計畫（歷史文件）
├── README.md                  # 本文件
└── .gitignore
```

---

## 前後端模組細化

### Backend 模組（3 個 Router）

#### `app/api/generate.py` — 生成與 AI 對話

- `POST /api/generate_plan` — 生成完整計畫書（多候選版本）
- `POST /api/revise_plan_version` — 基於既有版本重新優化
- `POST /api/recommend_project_names` — 推薦專案名稱
- `WebSocket /ws/chat_guidance` — 即時引導對話（Streaming）

#### `app/api/projects.py` — Demo 會話管理

- `GET /api/demo` — 取得/建立會話（mint cookie）
- `PUT /api/demo` — 更新會話資料（答案、計畫、標題等）
- `DELETE /api/demo` — 重置會話
- `GET /api/demo/status` — 會話狀態與限制計數
- `GET /api/demo/dynamic-fields` — 動態欄位查詢
- `POST /api/demo/download` — 增加下載計數
- `GET /api/template-manager/templates/{grant_id}/{template_id}` — 模板詳情

#### `app/api/config.py` — 配置讀取

- `GET /api/config` — 讀取 grants / templates / sections catalog
- `POST /api/config/refresh` — 手動刷新配置快取

### Frontend 模組

#### 頁面

- `pages/index.vue` — **Demo 聊天工作區**（根路徑，無需登入）

#### 元件

- `components/chat/DemoChatbox.vue` — 聊天介面、欄位填寫、生成按鈕、限制提示
- `components/chat/helper/DemoRegisterModal.vue` — 註冊提示彈窗（上限觸發）

#### Composables

- `composables/useDemoSession.ts` — 單一會話 bootstrap（Promise memoization，防止並行 mint 造成 cookie 分叉）
- `composables/useAppAuth.ts` — 認證工具（已改為無 Bearer token，使用 Cookie）
- `composables/usePlanGenerator.ts` — 計畫生成流程整合

---

## 快速開始

### 前置需求

- Docker + Docker Compose v2
- 本機開發：Python 3.10+、Node.js 20+
- Supabase 專案與 Service Key
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

---

## 環境變數配置

### backend/.env

```env
# Supabase
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_KEY=<service_key>
DATABASE_URL=postgresql://...

# LLM
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Demo 配置
DEMO_GRANT_ID=sbir
DEMO_TEMPLATE_ID=sbir_p1
DEMO_MAX_PROMPTS_PER_SESSION=20
DEMO_MAX_TOKENS_PER_SESSION=100000
DEMO_MAX_GENERATIONS_PER_SESSION=1
DEMO_SESSION_EXPIRY_DAYS=7
DEMO_SESSION_EXPIRY_MINUTES=10080
DEMO_IP_HOURLY_LIMIT=3
DEMO_IP_DAILY_LIMIT=5
DEMO_REGISTER_REDIRECT_URL=https://aiproposal.tgsa.com.tw/api/external-auth/redirect
FULL_PLATFORM_URL=https://aiproposal.tgsa.com.tw
DEMO_FRONTEND_URL=https://demo-aiproposal.tgsa.com.tw
```

### frontend/.env

```env
NUXT_PUBLIC_API_BASE_URL=https://demo-aiproposal.tgsa.com.tw/api
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<anon_key>

NUXT_PUBLIC_PLATFORM_HOME_URL=https://aiproposal.tgsa.com.tw/api/external-auth/redirect
NUXT_PUBLIC_DEMO_GRANT_ID=sbir
NUXT_PUBLIC_DEMO_TEMPLATE_ID=sbir_p1
NUXT_PUBLIC_DEMO_SESSION_EXPIRY_MINUTES=10080
```

---

## API 端點概要

### Demo 會話

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/demo` | GET | 建立/取得會話（mint cookie） |
| `/api/demo` | PUT | 更新會話資料 |
| `/api/demo` | DELETE | 重置會話 |
| `/api/demo/status` | GET | 會話狀態與限制 |
| `/api/demo/dynamic-fields` | GET | 動態欄位查詢 |
| `/api/demo/download` | POST | 增加下載計數 |

### 生成

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/generate_plan` | POST | 生成完整計畫書 |
| `/api/revise_plan_version` | POST | 優化既有版本 |
| `/api/recommend_project_names` | POST | 推薦專案名稱 |
| `/ws/chat_guidance` | WS | AI 即時引導對話 |

### 配置

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/config` | GET | 讀取配置 catalog |
| `/api/config/refresh` | POST | 刷新快取 |

---

## 主要工作流程

### 1. Demo 啟動流程

1. 訪客進入 `/`（無需登入）
2. 前端呼叫 `GET /api/demo` → 後端 mint `demo_session_id` cookie + 建立 `demo` 資料列
3. 前端呼叫 `GET /api/config` → 取得 grants / templates catalog
4. 前端根據 `DEMO_GRANT_ID` + `DEMO_TEMPLATE_ID` 選定 SBIR Phase 1 模板
5. 前端載入動態欄位（如有）或靜態 `json_schema` 問題列表
6. WebSocket 連線 `/ws/chat_guidance` → AI 開始引導填寫

### 2. AI 對話流程

1. 訪客輸入訊息 → WebSocket 傳送
2. 後端解析隱藏回復欄位，更新 `stored_answer.chat_answers`
3. 後端檢查 `interaction_count` 與 token 累計用量
4. 若未達上限 → AI 回覆並詢問下一題
5. 若達上限 → 發送 `limit_reached` 事件，前端顯示註冊提示
6. 每次對話後自動儲存 `conversation_history` 與 `stored_answer` 到 `demo` 資料列

### 3. 計畫書生成流程

1. 訪客點擊「輸出完整推演」
2. 前端呼叫 `POST /api/generate_plan`（帶入 `grant_id` + `template_id` + 使用者摘要）
3. 後端依已填寫答案過濾章節（若無答案則生成全部）
4. 每個章節並行生成 `num_candidates` 個候選版本
5. 前端顯示 `PlanCandidateSelector` → 訪客選擇每章節最佳版本
6. 選擇後呼叫 `PUT /api/demo` 儲存 `saved_plan` + `has_generated_docx = true`
7. 訪客可下載 Word 檔案（前端 `utils/exportToWord.ts`）

### 4. Demo → 平台遷移流程

1. 訪客達上限後點擊「免費註冊」
2. 前端導向：`https://aiproposal.tgsa.com.tw/api/external-auth/redirect?ref=<session_id>`
3. 完整平台將 `ref` 存入 `pending_demo_claim` cookie
4. 導向 OAuth IdP（assist_link）進行註冊/登入
5. 回呼後平台呼叫 `claim_demo_session(ref, user_id)`
6. SQL 函數 `migrate_demo_to_project()` 原子化複製資料：
   - `demo` → `projects`（含 `title`、`section_versions`、`saved_plan`、`stored_answer`、`conversation_history`）
   - `pending_execution_events` → `execution_logs`
   - `pending_usage_logs` → `usage_logs`
7. 標記 `demo` 列為 `claimed`
8. 導向 `/projects/<new_id>`，訪客繼續編輯

---

## 部署與維運

### 服務入口

- 前端：`/`
- 後端 API：`/api/`
- WebSocket：`/ws/chat_guidance`

### 例行維運指令

```bash
docker compose ps
docker compose restart fastapi-backend
docker compose logs -f --tail=200 fastapi-backend
docker compose logs -f --tail=200 nuxt-frontend
docker compose logs -f --tail=200 nginx-proxy
```

### 備份方案

- 使用 Rclone + Cron 定時將 PostgreSQL 備份上傳 Google Drive
- 建議每日執行，至少保留 30 天滾動版本
- 參見 `database-backup-migrate-schema.md`（完整平台文件）

---

## 常見問題

### 前端 API 請求失敗

- 檢查 `NUXT_PUBLIC_API_BASE_URL` 是否正確
- 檢查 Nginx `/api/` 轉發與後端服務狀態
- 確認 `demo_session_id` cookie 已正確設定

### 會話無法建立

- 檢查 `GET /api/demo` 是否正常（應回傳 `session_id` + 設定 cookie）
- 確認 `demo` 資料表已存在於 `ai_proposal_platform` schema
- 確認 `demo_ip_limits` 資料表已存在（若啟用 rate limiting）

### 資料庫連線錯誤

- 檢查 `DATABASE_URL` 與 `SUPABASE_SERVICE_KEY`
- 確認 Supabase 網路連通性
- 確認 `ai_proposal_platform` schema 已存在

### 生成計畫書失敗

- 檢查 `OPENAI_API_KEY` 或 `GEMINI_API_KEY` 是否有效
- 檢查 `model_registry` 是否包含可用模型
- 確認 `grant_id` / `template_id` 在 catalog 中存在

---

## 文件索引

### 模組文件
- `backend/README.md` — 後端詳細文件
- `frontend/README.md` — 前端詳細文件

### 專案狀態與規劃
- `STATUS.md` — 專案開發狀態與最新進度（**最新狀態請以此檔為準**）
- `next-implementation.md` — 原始實作計畫（歷史參考）

### 部署與運維
- `dev-vps.md` — 開發 VPS 設定與部署指南
- `database-backup-migrate-schema.md` — 資料庫備份與 Schema 遷移指南（完整平台文件）

### Demo 專屬文件
- `docs-private/specs/2026-06-16-demo-to-platform-signup-handoff-design.md` — 註冊遷移設計文件
- `docs-private/to-do-lists.md` — 內部任務追蹤
- `database-migrations/001_demo_claim_columns.sql` — 遷移相關欄位
- `database-migrations/002_demo_download_count.sql` — 下載計數欄位
- `database-migrations/003_demo_schema_update.sql` — 完整遷移函數

---

## Demo → 平台遷移合約（Phase 9）

當 Demo 訪客點擊註冊 CTA 時，Demo 導向：

```
https://aiproposal.tgsa.com.tw/api/external-auth/redirect?ref=<demo_session_id>
```

完整平台處理 `?ref` 流程：

1. `/api/external-auth/redirect` 驗證 `ref` 為 UUID，設定 HttpOnly `pending_demo_claim=<ref>` cookie（SameSite=Lax, max-age=900s），然後繼續現有 OAuth 流程至 portal.tgsaapp.com。
2. `/api/external-auth/callback` 在認證成功後讀取 cookie，呼叫 `claim_demo_session(ref, user_id)`，原子化：
   - 鎖定 `ai_proposal_platform.demo` 資料列。
   - 插入 `projects` 資料列（屬於新使用者），資料來自 `saved_plan`、`stored_answer`、`conversation_history`、`grant_id`、`template_id`、`title`、`section_versions`、`mode`。
   - 標記 demo 列 `status='claimed'`，記錄 `claimed_by`、`claimed_project_id`、`claimed_at`。
   - 將 `pending_execution_events` 與 `pending_usage_logs` 分別寫入 `execution_logs` 與 `usage_logs`。
3. 成功後導向 `https://aiproposal.tgsa.com.tw/projects/<new_id>`。
4. 失敗（not_found、already_claimed）則導向預設登入後目的地，不顯示錯誤。

### 欄位對應（demo → projects）

| demo 欄位 | projects 欄位 |
|---|---|
| `grant_id` | `grant_id` |
| `template_id` | `template_id` |
| `saved_plan` | `saved_plan` |
| `stored_answer` | `stored_answer` |
| `conversation_history` | `conversation_history` |
| `title`（優先）或 `stored_answer->>'plan_name'`（fallback） | `title` |
| `section_versions` | `section_versions` |
| `mode`（預設 `'interactive'`） | `mode` |
| `claimed_by` | `user_id`（新 projects 列） |

---

## License

Internal use only.

## Version

### v1.0.0-demo（2026-06-24）

主要功能：

- **匿名 AI 工作區：** 無需登入即可與 AI 互動填寫 SBIR Phase 1 計畫書
- **WebSocket 即時對話：** 串流 AI 回應，自動解析隱藏欄位答案
- **計畫書生成：** 多候選版本並行生成，支援選擇與改寫
- **使用限制：** 20 輪對話、100K token、1 次生成、1 次下載
- **會話遷移：** 達上限後無縫轉移至完整平台，資料完整保留
- **Rate Limiting 基礎建設：** IP 小時/日計數器（待啟用）
- **動態欄位支援：** 與完整平台 `_builder` 配置同步
- **測試覆蓋：** Backend 單元測試（session、rate limiter、IP 提取）

> 完整最新進度請參考 `STATUS.md`。

(End of file)
