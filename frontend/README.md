# 補助引擎（AI Proposal, AP）Frontend

本專案為補助引擎（AI Proposal, AP）的前端介面，使用 Nuxt 3（Vue 3 + TypeScript）開發，負責：

- 使用者登入與權限導向
- 計畫書生成流程互動
- 專案管理與內容編修
- 模板與章節管理頁面
- 圖片生成與預覽
- 使用量分析頁面呈現

## 技術棧

- Nuxt 3
- Vue 3
- TypeScript
- Tailwind CSS
- Supabase JS SDK
- Nuxt Icon / Heroicons

## 目錄重點

- `pages/`：頁面路由（共 16 個路由）
    - 使用者端：`index.vue`、`login.vue`、`projects/[id].vue`、`plan-library.vue`、`command-library.vue`、`external-auth-callback.vue`
    - 管理端 `_builder/*`（需 `role=internal`）：`template-manager.vue`、`section.vue`、`dataset.vue`、`model.vue`、`management.vue`、`usage-analytics.vue`、`login.vue`、`signup.vue`、`forgot-password.vue`、`reset-password.vue`
- `components/`：功能元件
    - `chat/*`：互動聊天區塊（streaming WebSocket 對話）
    - `word-editor/*`：Word 視覺化模板樹狀編輯器
    - `template-manager/*`：模板管理 UI
    - `global/*`：全域元件（Loading、通知等）
- `composables/`：可重用邏輯
    - `useAppAuth.ts`：登入會話與 token 流程
    - `usePlanGenerator.ts`：計畫產生流程整合
    - `useWordNumbering.ts`：Word 章節 / 子標題 / 段落編號
    - `useSensitiveMasking.ts`：敏感資料遮罩
    - `useLoading.ts`、`useNotifications.ts`：全域 UX 工具
    - `useInternalCheck.ts`：內部角色檢查
- `middleware/`：路由守衛（登入檢查、`role=internal` 檢查）
- `utils/`：
    - `exportToWord.ts`：Word 文件匯出引擎
    - `supabaseClient.ts`：Supabase JS SDK 初始化（含 schema 設定 `ai_proposal_platform`）
    - 其他：文字映射、認證 fetch wrapper（`authenticatedFetch`）等

## Word 視覺化編輯器

`components/word-editor/*` 提供樹狀模板節點編輯器，配合 `utils/exportToWord.ts` 完成 Word 文件匯出。

支援節點類型：

- `sectionTitle`：章節標題（會重置編號計數器）
- `subHeading`：子標題（中文逗號 / 句號 / 括號 / bullet 等多種格式）
- `paragraph`：段落（資料綁定 + 可選編號）
- `table`：資料驅動表格（支援 transpose / groupBy / sortBy）
- `customTable`：固定佈局表格（任意儲存格內容）
- `list`：資料驅動清單（含 sub-node 渲染）
- `customText`：靜態 / 模板文字
- `imagePlaceholder`：圖片佔位符（黃色高亮）

設定以版本快照儲存於 `plan_templates.word_export_config` JSONB 欄位，每次儲存皆建立時間戳記版本。詳情參閱 `STATUS.md` Word Export Template System 章節。

## 環境需求

- Node.js 20+
- npm 10+（建議）

## 安裝與啟動

### 1. 安裝依賴

```bash
npm install
```

### 2. 環境變數

請於 `frontend/.env`（或 `.env.local`）設定：

```env
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

說明：

- `NUXT_PUBLIC_API_BASE_URL`：後端 API 入口（不含 `/api`，程式會自行拼接）
- `SUPABASE_URL` / `SUPABASE_ANON_KEY`：前端 Supabase 連線資訊

### 3. 開發模式

```bash
npm run dev
```

預設開發網址：
`http://localhost:3000`

### 4. 生產建置

```bash
npm run build
npm run preview
```

## Docker

本專案採多階段建置，正式環境使用 Node 20 Alpine 執行 Nuxt Server。

```bash
# 於專案根目錄
docker compose up -d
```

僅重建前端：

```bash
docker compose build nuxt-frontend
docker compose up -d nuxt-frontend
```

查看前端 log：

```bash
docker compose logs -f --tail=200 nuxt-frontend
```

## 主要 npm Scripts

- `npm run dev`：啟動開發伺服器
- `npm run build`：建置生產版本
- `npm run preview`：本機預覽生產版本
- `npm run generate`：產生靜態頁面
- `npm run postinstall`：Nuxt prepare

## 路由與認證機制

- 認證中介層：`middleware/auth.ts`
- 公開頁面：`/login`、`/_builder/login`、`/_builder/signup`、`/_builder/forgot-password`、`/_builder/reset-password`、`/external-auth-callback`
- 受保護頁面：其餘路由需登入
- 內部權限頁面：`/_builder/**` 需 `role=internal`（透過 `useInternalCheck.ts` 驗證）

### 混合身份驗證
平台支援兩種登入方式：

- **Supabase Auth：** Email / Password 直接註冊登入
- **外部 OAuth（TGSA Provider）：** 透過 `/api/external-auth/redirect` 流程取得 `app_access_token` cookie

兩種方式均使用後端 `Authorization: Bearer` header 進行 API 請求，後端統一解析為 canonical user context（包含 `id`、`email`、`role`）。

## 與後端整合重點

- 前端透過 `runtimeConfig.public.apiBaseUrl` 呼叫後端 API
- API 主要路徑為 `${NUXT_PUBLIC_API_BASE_URL}/api/*`
- WebSocket 端點：`${NUXT_PUBLIC_API_BASE_URL}/api/ws/chat_guidance`（互動式 AI 對話）
- Supabase 客戶端由 `utils/supabaseClient.ts` 初始化（含 `db.schema = 'ai_proposal_platform'` 設定）
- 認證 fetch：使用 `authenticatedFetch()` 工具自動帶入 Bearer token
- Realtime 訂閱：`Chatbox.vue`、`_builder/dataset.vue` 透過 Supabase Realtime 訂閱 `ai_proposal_platform` schema 資料變動

## 常見問題排查

1. 啟動失敗（缺少環境變數）

- 檢查 `SUPABASE_URL`、`SUPABASE_ANON_KEY`、`NUXT_PUBLIC_API_BASE_URL`

2. 登入後仍被導向 `/login`

- 檢查後端 `/api/auth/status` 是否可連線
- 檢查 cookie 是否正確帶入

3. `/_builder` 無法進入

- 檢查 `/api/auth/me` 回傳的 `role` 是否為 `internal`

4. API 呼叫 404/500

- 確認 API Base URL 正確且後端容器已啟動

## 部署備註

- 反向代理由 Nginx 統一處理（生產）/ Nginx Proxy Manager（Dev VPS）
- 前端入口通常為根路徑 `/`
- 後端 API 走 `/api/`
- WebSocket 走 `/api/ws/`（NPM 需開啟 Websockets Support）
- 如有跨網域部署，需同時確認後端 CORS 與前端 API Base URL 設定
- Dev VPS 部署使用 `docker-compose.beta.yml`（拉取 `tgsataiwan/ai_proposal_frontend:dev` 預構建鏡像）

## 主要功能模組

- **AI 互動式工作區（`pages/projects/[id].vue`）：** WebSocket 對話 + 多候選版本生成 + 章節版本管理
- **計畫庫（`pages/plan-library.vue`）：** 使用者專案管理、AI 配圖生成入口
- **背景資料庫（`pages/command-library.vue`）：** 使用者自訂指令 / 背景資料卡片
- **管理員模板編輯器（`pages/_builder/template-manager.vue`）：** Grant / Template / Section CRUD + Word 視覺化編輯器
- **使用分析儀表板（`pages/_builder/usage-analytics.vue`）：** Token 用量趨勢、使用者明細、專案層級分析

## License

Internal use only.
