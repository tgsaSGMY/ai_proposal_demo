# Project Status: AI Proposal Platform (AI 企劃書平台)

## Project Context
This platform is an AI-powered workspace designed to help users generate structured project proposals and government grant applications (e.g., SIIR, IMDP, CITD). It utilizes a hierarchical structure of **Grants** -> **Templates** -> **Sections** to organize complex document generation.

## Tech Stack
- **Frontend:** Nuxt 3, Vue 3, Tailwind CSS, Headless UI.
- **Backend:** FastAPI (Python 3.10+), SQLAlchemy (PostgreSQL).
- **Database & Auth:** Supabase (Auth, Storage, and Real-time PostgreSQL).
- **AI Integration:** Multi-LLM routing (OpenAI GPT-4/5, Google Gemini, Ollama).
- **Document Processing:** PDF/Word parsing and professional Word docx export.

## Functional Logic
1.  **Grant/Template Selection:** Users choose a specific subsidy program which loads a predefined JSON Schema for various document sections.
2.  **AI Workspace:** 
    *   **Interactive Mode:** A WebSocket-based chat (`/ws/chat_guidance`) that asks targeted questions to fill required fields.
    *   **Generator Mode:** Batch generation of an entire proposal based on a summary or uploaded files.
3.  **Section Management:** AI generates multiple "Candidates" for each section. Users can compare, edit, and save specific versions.
4.  **Token Tracking:** Every AI generation is logged in a `usage_logs` table, tracking `input_tokens`, `output_tokens`, and estimated `cost` per `user_id`.

## Authentication & Authorization
- **Method:** Hybrid Auth supporting **Supabase Auth** (Email/Password) and **External OAuth** (TGSA Provider).
- **Roles:**
    *   `normal`: Basic access; restricted from VIP templates in the UI. 1 Project slot, 1,000,000 daily token limit. Max 2 projects/day & 5 images/day before 30s throttling kicks in.
    *   `vip`: Paid access; determined by plan IDs during OAuth login. 50 Project slots, unlimited daily tokens. Max 5 projects/day & 16 images/day before 30s throttling kicks in.
    *   `internal`: Staff/Developer access; bypassed via a `whitelist` table, granting access to the `/template-manager` admin tools. No limits.
- **Session Management:** Uses `Authorization: Bearer` headers and an `app_access_token` cookie. Recently fortified against 401 caching loops with strict `Cache-Control` and local storage cleanup.

## Project TODO List

### High Priority
- [ ] **Testing Real-time Sync Logic:**
    *   Verify role transition (Normal ↔ VIP) during External OAuth callback.
    *   Test system behavior/UI updates when a user's role is updated in the database while they are in an active session.

### Medium Priority
- [ ] **Enhanced Error Handling:** Improve "JSON Repair" logic for LLM outputs to handle edge cases in complex nested schemas.

## Recently Completed
- [x] **Implement New User Limitations & Throttling Logic:**
    *   Updated Normal user token limit to 1,000,000 in `config.py`.
    *   Split throttling logic into independent trackers (`needs_project_throttling`, `needs_image_throttling`) based on user role limits (Normal: 2 projects/5 images, VIP: 5 projects/16 images).
    *   Applied universal 30s delays in LLM and Image Generation API calls when daily thresholds are met.
    *   Added a humorous 15s timeout loading message in the frontend (e.g., "稍等片刻，目前系統詠唱量較大...") in `useLoading.ts`, `Chatbox.vue`, and `PlanImageGeneratorModal.vue` to improve UX during 30s throttles.
    *   Fixed `KeyError: needs_throttling` crash in WebSocket chat endpoints by updating deprecated dictionary keys.
- [x] **Auth Stability Fix (401 Infinite Loop):**
    *   Fixed an issue where cached `/auth/status` requests and stale Supabase local storage tokens caused infinite redirects between `/login` and the app. 
    *   Added `Cache-Control: no-store` headers and forceful `localStorage` cleanup to guarantee clean session invalidation.
- [x] **Token Limiting & Quota Management:**
    *   Implement daily reset logic for token usage (Daily Quota) using Taipei Time.
    *   Differentiate limits based on User Type (`normal`: 1,000,000, `vip`: unlimited).
    *   Implemented `SupabaseService.get_daily_usage_stats` to validate usage before allowing LLM calls.
- [x] **Project Slot Enforcement:**
    *   Implemented 1-slot limit for Normal users.
    *   Added "Read-only" mode for non-latest projects for downgraded users.
- [x] **Performance Throttling:**
    *   Implemented universal 30s delay logic based on project/image creation frequency.
    *   Limits scale by user type (Normal: 2 projects/5 images, VIP: 5 projects/16 images).
- [x] **Backend Validation:** Added server-side role checks for `/api/projects` and AI generation endpoints to enforce plan limits.
- [x] **Frontend UI Sync:**
    *   Added "Read Only" banner in the project workspace for downgraded users.
    *   Disabled chat input, file uploads, and generation buttons when in Read Only mode.
    *   Disabled the "Enter Workspace" button for Normal users who already have 1 active project.
    *   Added error message fallbacks in the chat UI when hitting quotas or attempting to generate in a locked project.