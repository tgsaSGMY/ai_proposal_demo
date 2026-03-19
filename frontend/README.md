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

- `pages/`：頁面路由（含 `projects`、`plan-library`、`command-library`）
- `components/`：功能元件（chat、template-manager、global 元件等）
- `composables/`：可重用邏輯（auth、loading、notifications、plan generator）
- `middleware/`：路由守衛（登入檢查、角色檢查）
- `utils/`：匯出、文字映射、Supabase 客戶端等工具

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
- 公開頁面：`/login`、`/_builder/login`、`/_builder/signup` 等
- 受保護頁面：其餘路由需登入
- 內部權限頁面：`/_builder/**` 需 `role=internal`

## 與後端整合重點

- 前端透過 `runtimeConfig.public.apiBaseUrl` 呼叫後端 API
- API 主要路徑為 `${NUXT_PUBLIC_API_BASE_URL}/api/*`
- Supabase 客戶端由 `utils/supabaseClient.ts` 初始化

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

- 反向代理由 Nginx 統一處理
- 前端入口通常為根路徑 `/`
- 後端 API 走 `/api/`
- 如有跨網域部署，需同時確認後端 CORS 與前端 API Base URL 設定

## License

Internal use only.
