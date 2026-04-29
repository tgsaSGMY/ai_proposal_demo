// 主要運用在 Supabase 客戶端的初始化和配置，確保前端應用能夠安全且有效地與 Supabase 後端服務進行通信。

import { createClient } from "@supabase/supabase-js";
import type { SupabaseClient } from "@supabase/supabase-js";

// ===== 环境变量和配置 =====
/**
 * Supabase 项目的公开 URL
 *   - 公开信息，可以安全地暴露在前端代码中
 */
const supabaseUrl: string =
  process.env.SUPABASE_URL || useRuntimeConfig().public.supabaseUrl;

/**
 * Supabase 匿名公钥（Anon Key）
 */
const supabaseAnonKey: string =
  process.env.SUPABASE_ANON_KEY || useRuntimeConfig().public.supabaseAnonKey;

// ===== 配置验证 =====
/**
 * 验证必需的配置变量是否存在
 */
if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Supabase URL and Anon Key must be provided.");
}

// ===== Supabase 客户端初始化 =====
/**
 * 创建并导出 Supabase 客户端实例
 *
 * 功能：
 *   - 初始化与 Supabase 后端的连接
 *   - 配置认证和会话管理
 *   - 提供数据库操作、认证、RPC 等功能
 */
export const supabase: SupabaseClient = createClient(
  supabaseUrl,
  supabaseAnonKey,
  {
    auth: {
      autoRefreshToken: true, // 自动刷新令牌
      persistSession: true, // 持久化会话信息
      detectSessionInUrl: true, // 检测 URL 中的会话信息（OAuth 回调）
    },
    db: {
      schema: "ai_proposal_platform", // 指定資料庫 schema（從 public 遷移至 ai_proposal_platform）
    },
  },
);
