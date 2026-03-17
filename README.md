# AI 計畫書平台

AI 提案平台是一個智能化的計畫書生成系統，利用先進的大型語言模型（LLM）和向量檢索技術，自動化地為用戶生成高品質的計畫書和提案內容。該平台支持多模板、多章節的靈活配置，並提供合成數據生成、批量生成和版本管理等功能。

## 核心功能

### 內容生成

- 利用 AI 模型自動生成計畫書內容，支持多版本（候選版本）並行生成
- 基於 JSON Schema 的結構化內容生成
- 支持自訂提示詞和評論優化流程
- 集成網頁抓取功能，從外部資源自動提取相關信息

### 計畫書管理

- 支持多層級結構：計畫書（Grant）→ 模板（Template）→ 章節（Section）
- 靈活的配置管理系統，支持動態配置更新
- 計畫書的版本控制和內容編輯

### 數據集與訓練

- 完整的數據集管理，支持多種數據來源（合成數據、黃金樣本、模型輸出）
- 批量合成數據生成功能
- 支持動態字段的智能輸入生成
- 反向模式：根據已有輸出反推高品質的用戶輸入

### 模型路由

- 靈活的模型路由規則系統，支持按計畫書、模板、章節等維度配置
- 動態模型選擇，支持優先級管理

### 文檔處理

- 支持多種文檔格式的自動解析
- 根據上傳的文檔，自動填充相應章節內容
- 內容導出功能

## 系統架構

### 後端技術棧

- FastAPI：高性能的 Python Web 框架
- SQLAlchemy：ORM 數據庫操作
- Supabase：PostgreSQL 托管服務，作為主要數據庫
- Tiktoken / FastEmbed：文本編碼和嵌入生成
- Scikit-learn：機器學習工具

### 前端技術棧

- Nuxt 3：Vue.js 全棧框架
- TypeScript：增強型 JavaScript
- Tailwind CSS：實用程序優先的 CSS 框架
- Supabase JS SDK：客戶端數據庫操作

## 快速開始

### 前置要求

- Python 3.8 以上
- Node.js 18 以上（npm 或 yarn）
- Supabase 帳戶（用於數據庫服務）
- LLM API 密鑰（OpenAI 或其他支持的模型提供商）

### 後端部署

#### 1. 安裝依賴

進入 `backend` 目錄：

```bash
cd backend
pip install -r requirements.txt
```

#### 2. 環境配置

在 `backend` 根目錄創建 `.env` 文件，配置以下變數：

```
# 數據庫配置
DATABASE_URL=postgresql://user:password@host:port/database
SUPABASE_URL=https://your-supabase-url.supabase.co
SUPABASE_KEY=your-supabase-anon-key


# LLM 模型配置
OPENAI_API_KEY=your-openai-api-key
DEFAULT_MODEL=gpt-4

# 應用配置
DEBUG=True
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
```

#### 3. 啟動伺服器

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文檔將在 `http://localhost:8000/docs` 可用（Swagger UI）

### 前端部署

#### 1. 安裝依賴

進入 `frontend` 目錄：

```bash
cd frontend
npm install
```

#### 2. 環境配置

在 `frontend` 根目錄創建 `.env.local` 文件：

```
NUXT_PUBLIC_SUPABASE_URL=https://your-supabase-url.supabase.co
NUXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
NUXT_PUBLIC_API_URL=http://localhost:8000
```

#### 3. 開發服務器

```bash
npm run dev
```

應用將在 `http://localhost:3000` 運行

#### 4. 生產構建

```bash
npm run build
npm run preview
```

## API 端點

### 核心生成 API

#### POST /api/generate_plan

生成完整的計畫書內容

請求體：

```json
{
  "user_id": "user123",
  "grant": "grant_id",
  "template": "template_id",
  "user_input": "用戶的核心需求",
  "sections": [
    {
      "section_id": "section_1"
    }
  ],
  "num_candidates": 2
}
```

#### POST /api/generate_synthetic_input

生成合成訓練數據

請求體：

```json
{
  "mode": "random",
  "grant_name": "計畫書名稱",
  "template_name": "模板名稱",
  "section_name": "章節名稱",
  "user_id": "user123",
  "dynamic_fields_schema": [
    {
      "label": "問題描述"
    }
  ]
}
```

### 數據集管理 API

#### POST /api/datasets/save

保存數據集條目

#### GET /api/datasets

查詢數據集

#### DELETE /api/datasets/{id}

刪除數據集條目

### 配置管理 API

#### GET /api/config/grant/{grant_id}

獲取計畫書配置

#### PUT /api/config/section/{section_id}

更新章節配置

## 項目結構

### 後端結構

```
backend/
├── app/
│   ├── main.py                 # FastAPI 應用入口
│   ├── models.py               # Pydantic 數據模型
│   ├── config.py               # 應用配置
│   ├── api/                    # API 路由模組
│   │   ├── generate.py         # 內容生成相關端點
│   │   ├── datasets.py         # 數據集管理端點
│   │   ├── admin.py            # 管理後台端點
│   │   ├── draft_plan.py       # 計畫書編輯端點
│   │   ├── config.py           # 配置管理端點
│   │   └── dependencies.py     # 依賴注入
│   ├── core/                   # 核心業務邏輯
│   │   ├── generation_logic.py # 生成算法
│   │   └── lifecycle.py        # 應用生命週期
│   ├── services/               # 外部服務集成
│   │   ├── llm_service.py      # LLM 調用服務
│   │   ├── supabase_service.py # Supabase 數據庫服務
│   └── utils/                  # 工具函數
│       ├── extract_json.py     # JSON 提取工具
│       ├── formatting.py       # 文本格式化
│       ├── routing.py          # 模型路由邏輯
│       ├── scrape_website_text.py # 網頁抓取
│       └── token_calculator.py # Token 計算
├── requirements.txt            # Python 依賴
└── Procfile                    # Procfile 部署配置
```

### 前端結構

```
frontend/
├── pages/                      # 頁面組件
│   ├── index.vue              # 主頁
│   └── _builder/              # 計畫書編輯器子頁面
│       ├── dataset.vue        # 數據集管理
│       ├── model.vue          # 模型配置
│       └── management.vue     # 通用管理界面
├── components/                # 可復用組件
│   ├── PlanInputPanel.vue    # 輸入面板
│   ├── PlanOutputPanel.vue   # 輸出面板
│   ├── DraftPlanList.vue     # 計畫書列表
│   ├── BatchSyntheticModal.vue # 批量生成對話框
│   └── ...                    # 其他組件
├── composables/               # Vue 組合式 API 邏輯
│   ├── usePlanGenerator.ts    # 計畫書生成邏輯
│   ├── useNotifications.ts    # 通知管理
│   ├── useLoading.ts          # 加載狀態
│   └── useConfirm.ts          # 確認對話框
├── utils/                     # 工具函數
│   ├── supabaseClient.ts      # Supabase 客戶端
│   ├── exportToWord.ts        # 文檔導出
│   ├── contentRenderer.ts     # 內容渲染
│   └── textMapping.ts         # 文本映射
└── nuxt.config.ts             # Nuxt 配置文件
```

## 主要工作流程

### 1. 計畫書生成流程

1. 用戶輸入核心需求（user_input）
2. 系統根據配置選擇相應的模型和提示詞
3. 並行生成多個候選版本
4. 返回結構化和格式化的內容
5. 用戶選擇最優版本或進行編輯

### 2. 合成數據生成流程

1. 定義動態字段架構（用戶需要回答的問題）
2. AI 根據字段生成高品質的用戶輸入
3. 相應地生成結構化的輸出（JSON）
4. 保存為訓練數據，用於模型微調

### 3. 批量生成流程

1. 用戶指定計畫書、模板和生成數量
2. 系統自動生成多個合成輸入
3. 針對每個輸入生成對應的計畫書內容
4. 批量保存數據集

## 數據流

### 生成請求流

```
用戶請求 → API 端點 → 模型路由 → LLM 服務 → 向量檢索 →
LLM API 調用 → 結果提取與格式化 → 數據庫保存 → 響應返回
```

### 配置加載流

```
啟動應用 → 從 Supabase 加載配置 → 構建配置樹 →
內存緩存 → 路由規則初始化 → 準備就緒
```

## 部署選項

### 本地開發

直接運行開發伺服器，支持熱重載

### Docker 部署

使用提供的 `Procfile` 配置進行容器化部署

### Cloudflare Workers（前端）

前端已配置支持 Cloudflare Workers 部署，可通過 Wrangler CLI 部署

### Vercel 或其他 Jamstack 平台

Nuxt 應用可部署到 Vercel、Netlify 等平台

## 環境變數配置

### 後端主要變數

- `DATABASE_URL`：PostgreSQL 連接字符串
- `SUPABASE_URL`、`SUPABASE_KEY`：Supabase 配置
- `OPENAI_API_KEY`：LLM API 密鑰
- `DEBUG`：調試模式開關

### 前端主要變數

- `NUXT_PUBLIC_SUPABASE_URL`、`NUXT_PUBLIC_SUPABASE_ANON_KEY`：Supabase 配置
- `NUXT_PUBLIC_API_URL`：後端 API 地址

### 常見問題

#### 前端 API 請求失敗

驗證 CORS 配置是否正確，確保 API_URL 指向正確的後端地址

#### Token 限制錯誤

檢查用戶配額設置和 LLM API 的 token 限制

#### 數據庫連接錯誤

確認 DATABASE_URL 和 SUPABASE_KEY 配置無誤，檢查網絡連接

## 許可證

本項目採用 MIT 許可證。詳見 LICENSE 文件。

### v1.0.0

初始發佈版本，包含核心功能：

- 計畫書生成
- 數據集管理
- 模型路由
- 配置管理
- 合成數據生成
