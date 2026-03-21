# 補助引擎（AI Proposal, AP）- API 與資料模型文件

## 文件目的

本文件用於說明補助引擎後端 API 規格查閱方式、第三方依賴清單與核心資料模型，提供接手開發與維運工程師快速掌握介接邏輯與資料結構。

## 1. RESTful API 規格與測試導覽

本系統後端採 Python FastAPI 開發，OpenAPI 文件由系統自動生成。建議優先透過 Swagger UI 進行測試與查閱，不再維護獨立靜態路由表。

- 本地端 Swagger UI：`http://localhost:8000/docs`
- 本地端 ReDoc：`http://localhost:8000/redoc`

### 1.1 API 測試原則

- 所有 API 的 Request/Response Schema 以 Swagger 生成內容為準。
- 權限型 API（例如管理端、內部頁面）需帶正確登入上下文測試。
- 檔案上傳型 API（如欄位分析）需使用 `multipart/form-data` 測試。

### 1.2 主要 API 群組（補助引擎專屬）

#### A. 生成與分析（/api）

- `POST /api/generate_plan`：生成提案章節內容
- `POST /api/revise_plan_version`：改寫既有版本
- `POST /api/generate_synthetic_input`：生成合成輸入
- `POST /api/recommend_project_names`：推薦專案名稱
- `POST /api/autofill_from_document`：從文件自動填入章節
- `POST /api/field_file_analysis`：針對單欄位做檔案輔助分析
- `POST /api/section-recommender`：動態章節說明優化建議

#### B. 專案管理（/api/projects）

- `GET /api/projects`：取得使用者專案列表
- `GET /api/projects/{project_id}`：取得單一專案
- `GET /api/projects/{project_id}/sections`：取得專案章節設定
- `POST /api/projects`：建立專案
- `PUT /api/projects/{project_id}`：更新專案
- `PATCH /api/projects/{project_id}`：軟刪除專案
- `GET /api/projects/{project_id}/timeline`：查詢 AI 執行時間軸
- `GET /api/projects/{project_id}/timeline/pdf`：下載時間軸 PDF

#### C. 模板與章節管理

- `GET /api/config`：取得完整 Grant/Template/Section 組態
- `POST /api/config/refresh`：刷新配置快取
- `GET /api/plan_templates`：取得模板列表
- `GET/POST/PUT /api/template-manager/*`：Grant、Template、Section 管理
- `GET/POST/PUT/DELETE /api/dynamic-sections/*`：動態章節/欄位管理

#### D. 資料集治理（/api/datasets）

- `POST /api/datasets`：保存資料集條目
- `GET /api/datasets`：查詢資料集條目
- `PUT /api/datasets/{dataset_id}`：更新資料集條目
- `DELETE /api/datasets/{dataset_id}`：刪除資料集條目
- `POST /api/datasets/sensitive-terms/suggest`：AI 建議敏感詞

#### E. 圖片與多媒體（/api/images）

- `GET /api/images`：查詢專案圖片
- `POST /api/images/enrich-prompt`：圖片提示詞強化
- `POST /api/images/generate`：立即生成圖片
- `DELETE /api/images/{image_id}`：刪除圖片

#### F. 使用量與指令庫

- `GET /api/usage-log/analytics`：使用量分析
- `GET/POST/PUT/DELETE /api/commands`：使用者指令庫 CRUD

#### G. 認證與登入

- `GET /api/auth/me`：取得目前登入者資訊
- `GET /api/auth/status`：登入狀態檢查
- `GET /api/external-auth/redirect`：外部 OAuth 授權導向
- `GET /api/external-auth/callback`：外部 OAuth 回呼
- `POST /api/external-auth/logout`：登出

### 1.3 管理端 API（內部權限）

- `GET /api/models`：模型清單
- `GET /api/routing-rules`：路由規則清單
- `POST /api/routing-rules`：新增/更新路由規則
- `DELETE /api/routing-rules/{rule_id}`：刪除路由規則
- `PUT /api/sections/{section_id}/prompts`：更新章節 prompt 設定
- `POST /api/refresh-datasets`：手動刷新 datasets 快取

## 2. 第三方 API 與外部依賴清單

本系統核心依賴外部 AI 與資料平台，所有敏感金鑰皆由環境變數管理。

### 2.1 大型語言模型與內容分析

#### OpenAI API

- 主要用途：
  - 提案文字生成
  - 章節改寫
  - 欄位檔案分析（文件/圖片）
- 常用模型（依目前程式）：
  - `gpt-5-mini`（主流程）
  - `gpt-4.1-mini`（檔案欄位分析流程）
- 應用端點：
  - `/api/generate_plan`
  - `/api/revise_plan_version`
  - `/api/field_file_analysis`
- 注意事項：
  - 模型回傳可能有 JSON 偏差，後端有解析修復機制。
  - 成本與 token 會寫入 `usage_logs`，需持續監控。

#### Google Gemini API

- 主要用途：
  - 文字分析與生成備援
  - 圖片生成流程
- 注意事項：
  - 與 OpenAI 屬雙供應商架構，需注意速率限制與可用性差異。

### 2.2 Supabase 平台

- PostgreSQL：核心業務資料儲存。
- Storage：Logo、圖片與檔案資源儲存。
- 主要用途：
  - 提供組態、專案、治理日誌、資料集與身份資料。

### 2.3 外部 OAuth 提供者

- 主要用途：外部登入授權與回呼。
- 注意事項：
  - 需維護 callback URL 一致性。
  - 建議限制來源與維護 token 安全策略。

## 3. 核心領域模型（Data Models）

本系統所有持久化資料儲存於 Supabase（PostgreSQL），核心可分為五大領域：組態、專案、治理、身份、內容資源。

### 3.1 組態模型（補助主題/模板/章節）

#### grants

- 用途：補助主題主檔。
- 核心欄位：
  - `id`（PK）
  - `name`

#### plan_templates

- 用途：隸屬於 grant 的提案模板。
- 核心欄位：
  - `id`、`grant_id`（組合識別）
  - `name`、`subtitle`、`description`
  - `logo_storage_path`、`iconBg`、`isOpen`

#### sections

- 用途：模板章節定義與生成規格。
- 核心欄位：
  - `id`、`grant_id`、`template_id`
  - `name`、`order`
  - `json_schema`
  - `system_prompt`、`custom_prompt_list`
  - `current_version`

#### section_schema_versions

- 用途：章節 schema 與 prompt 版本歷史。
- 核心欄位：
  - `section_id`、`grant_id`、`template_id`
  - `version`
  - `json_schema`、`system_prompt`

### 3.2 專案與流程追溯模型

#### projects

- 用途：專案主資料與生成結果載體。
- 核心欄位：
  - `id`（PK）
  - `user_id`
  - `title`、`description`
  - `grant_id`、`template_id`
  - `saved_plan`（版本內容）
  - `stored_answer`、`conversation_history`

#### execution_logs

- 用途：AI 執行時間軸與流程事件追蹤。
- 核心欄位：
  - `id`（PK）
  - `project_id`
  - `user_id`
  - `event_type`
  - `payload`、`external_sources`
  - `created_at`

### 3.3 治理與品質模型

#### datasets

- 用途：資料集條目（訓練/評估/回放用途）。
- 核心欄位：
  - `id`（PK）
  - `source_type`
  - `grant_id`、`template_id`、`section_id`
  - `prompt`、`final_answer`、`rejected_answer`
  - `embedding`（向量）

#### routing_rules

- 用途：模型路由策略。
- 核心欄位：
  - `id`（PK）
  - `grant_id`、`template_id`、`section_id`
  - `model_id`
  - `priority`
  - `is_external`

#### usage_logs

- 用途：模型用量、成本與行為追蹤。
- 核心欄位：
  - `id`（PK）
  - `user_id`、`project_id`
  - `model_id`、`model_type`
  - `input_token`、`output_token`
  - `cost`、`action`

### 3.4 身份與權限模型

#### users

- 用途：使用者主資料。
- 核心欄位：
  - `id`（PK）
  - `email`
  - `role`（如 internal / normal / vip）

#### user_identities

- 用途：外部身份映射（OAuth provider 對應）。
- 核心欄位：
  - `id`（PK）
  - `user_id`（FK -> users.id）
  - `provider`、`provider_subject`

#### whitelist

- 用途：內部授權或特定帳號白名單控制。

### 3.5 內容資源與管理模型

#### images

- 用途：專案圖片與生成圖管理。
- 核心欄位：
  - `id`（PK）
  - `project_id`（FK -> projects.id）
  - `storage_path`、`public_url`
  - `placeholder_text`

#### commands

- 用途：使用者自訂指令庫。
- 核心欄位：
  - `id`（PK）
  - `user_id`（FK -> users.id）
  - `title`、`description`

#### draft_plans

- 用途：草稿與批次 synthetic 中間資料。

#### dynamic_sections / dynamic_fields

- 用途：動態章節與欄位配置，支援管理端可配置式輸入架構。

## 4. 重點資料關聯總結（Entity Relationships）

- 一個 `grant` 可對應多個 `plan_templates`（一對多）。
- 一個 `plan_template` 可對應多個 `sections`（一對多）。
- 一個 `project` 綁定單一 `grant/template`，但可有多版本 `saved_plan`（一對多版本）。
- 一個 `project` 可對應多筆 `execution_logs`（一對多）。
- 一個 `user` 可擁有多個 `projects`、`commands`、`usage_logs`（一對多）。
- 一個 `project` 可對應多張 `images`（一對多）。
- 一個 `dynamic_section` 可對應多個 `dynamic_fields`（一對多）。

## 5. API 介接與測試建議

### 5.1 建議測試順序

1. 認證狀態：`/api/auth/status`、`/api/auth/me`
2. 讀取配置：`/api/config`
3. 建立專案：`POST /api/projects`
4. 執行生成：`POST /api/generate_plan`
5. 查詢時間軸：`GET /api/projects/{project_id}/timeline`
6. 成本驗證：`GET /api/usage-log/analytics`

### 5.2 常見錯誤排查

- 401/403：先確認 token 與角色權限。
- 422：檢查 request payload 欄位與型別。
- 500（生成流程）：檢查外部模型金鑰與供應商狀態。
- 500（資料層）：檢查 Supabase 連線、資料表權限與 schema 一致性。

---

以上內容為補助引擎專屬 API 與資料模型文件，不含名片掃描系統之資料表與流程定義。
