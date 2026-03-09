// ===== 导入依赖库 =====
// 导入 Supabase 客户端创建函数和类型定义
import { createClient } from "@supabase/supabase-js";
import type { SupabaseClient } from "@supabase/supabase-js";

// ===== 环境变量和配置 =====
/**
 * Supabase 项目的公开 URL
 *
 * 来源优先级：
 *   1. 环境变量 SUPABASE_URL
 *   2. 运行时配置 useRuntimeConfig().public.supabaseUrl
 *
 * 说明：
 *   - 这是 Supabase 项目的 API 端点
 *   - 公开信息，可以安全地暴露在前端代码中
 */
const supabaseUrl: string =
  process.env.SUPABASE_URL || useRuntimeConfig().public.supabaseUrl;

/**
 * Supabase 匿名公钥（Anon Key）
 *
 * 来源优先级：
 *   1. 环境变量 SUPABASE_ANON_KEY
 *   2. 运行时配置 useRuntimeConfig().public.supabaseAnonKey
 *
 * 说明：
 *   - 用于客户端认证的公开密钥
 *   - 权限受限（根据 Supabase RLS 策略）
 *   - 可以安全地暴露在前端代码中
 */
const supabaseAnonKey: string =
  process.env.SUPABASE_ANON_KEY || useRuntimeConfig().public.supabaseAnonKey;

// ===== 配置验证 =====
/**
 * 验证必需的配置变量是否存在
 *
 * 说明：
 *   - Supabase 客户端需要 URL 和密钥才能初始化
 *   - 如果缺少任何配置，应用无法正常工作
 *   - 早期抛出错误比在运行时遇到问题更好
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
 *
 * 认证配置说明：
 *   - autoRefreshToken: 自动刷新过期的会话令牌
 *   - persistSession: 将会话信息保存到本地存储（支持页面刷新后保持登录状态）
 *   - detectSessionInUrl: 检测 URL 中的会话信息（用于 OAuth 重定向）
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
  },
);

const EXTERNAL_APP_TOKEN_KEY = "app_access_token";

export function getExternalAppToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(EXTERNAL_APP_TOKEN_KEY);
}

export function setExternalAppToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(EXTERNAL_APP_TOKEN_KEY, token);
}

export function clearExternalAppToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(EXTERNAL_APP_TOKEN_KEY);
}

// Keep existing code unchanged by falling back to external token when Supabase has no session.
const originalGetSession = supabase.auth.getSession.bind(supabase.auth);
(supabase.auth as any).getSession = async () => {
  const result = await originalGetSession();
  const existingToken = result?.data?.session?.access_token;
  if (existingToken) {
    return result;
  }

  const externalToken = getExternalAppToken();
  if (!externalToken) {
    return result;
  }

  return {
    data: {
      session: {
        access_token: externalToken,
        user: {
          id: "external",
          email: null,
        },
      },
    },
    error: null,
  };
};

const originalSignOut = supabase.auth.signOut.bind(supabase.auth);
(supabase.auth as any).signOut = async () => {
  clearExternalAppToken();
  return originalSignOut();
};
