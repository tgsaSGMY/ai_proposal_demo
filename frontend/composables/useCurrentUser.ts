// ===== 导入依赖库 =====
// 导入 Vue 类型定义
import type { Ref } from "vue";
import { authenticatedFetch, getAppSession } from "~/composables/useAppAuth";

// ===== 返回值类型定义 =====
// 定义 useCurrentUser 函数的返回值接口
interface UseCurrentUserResult {
  userId: Ref<string | null>; // 当前用户的 ID（响应式）
  isFetchingUser: Ref<boolean>; // 是否正在获取用户信息的标志
  refreshUser: (force?: boolean) => Promise<string | null>; // 刷新用户信息的方法
}

// ===== 当前用户管理组合式函数 =====
/**
 * 管理当前认证用户的会话信息
 *
 * 功能：
 *   - 存储当前用户的 ID（全局共享状态）
 *   - 从 Supabase 认证会话中获取用户 ID
 *   - 防止重复的用户信息获取（通过加载标志）
 *   - 支持刷新用户会话信息
 */
export function useCurrentUser(): UseCurrentUserResult {
  // ===== 全局共享状态 =====
  // 使用 useState 创建全局共享的用户 ID
  // 在服务器端渲染和客户端渲染之间保持一致
  const userId = useState<string | null>("currentUserId", () => null);

  // 用户信息加载标志，防止同时发起多个加载请求
  const isFetchingUser = useState<boolean>("currentUserIdLoading", () => false);
  const lastResolvedAt = useState<number>("currentUserResolvedAt", () => 0);
  const lastResolvedToken = useState<string | null>(
    "currentUserResolvedToken",
    () => null,
  );
  const ME_CACHE_TTL_MS = 30 * 1000;

  // ===== 刷新用户信息的方法 =====
  /**
   * 从 Supabase 获取当前用户的会话信息
   *
   * 特点：
   *   1. 检查是否在浏览器环境中（防止服务器端出错）
   *   2. 防止重复加载（如果已经在加载，则返回缓存的用户 ID）
   *   3. 从 Supabase 认证会话中读取用户 ID
   *   4. 更新全局用户状态
   *   5. 错误情况下将用户 ID 设为 null
   *
   * 返回值：
   *   - 成功：返回用户 ID（字符串）
   *   - 失败：返回 null
   *   - 重复调用：返回已缓存的用户 ID
   */
  const refreshUser = async (force = false): Promise<string | null> => {
    // 检查是否在浏览器环境中运行
    // 如果在服务器端，则返回 null（避免服务器端错误）
    if (typeof window === "undefined") {
      return null;
    }

    // 防止重复加载：如果已经在加载用户信息，则直接返回缓存的用户 ID
    if (isFetchingUser.value) {
      return userId.value;
    }

    // 设置加载标志为 true
    isFetchingUser.value = true;
    try {
      // ===== 获取 Supabase 会话信息 =====
      // 从 Supabase 认证系统获取当前用户的会话
      const session = await getAppSession();

      if (!session.isAuthenticated) {
        userId.value = null;
        lastResolvedAt.value = 0;
        lastResolvedToken.value = null;
        return userId.value;
      }

      const cacheKey = session.accessToken || "external-cookie";
      const now = Date.now();
      if (
        !force &&
        lastResolvedToken.value === cacheKey &&
        now - lastResolvedAt.value < ME_CACHE_TTL_MS
      ) {
        return userId.value;
      }

      // Use backend canonical identity (public.users.id) instead of auth.users.id.
      const config = useRuntimeConfig();
      const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
      const response = await authenticatedFetch(`${API_BASE_URL}/auth/me`);

      if (!response.ok) {
        console.error("Failed to resolve canonical user id", response.status);
        userId.value = null;
        return userId.value;
      }

      const me = await response.json();
      userId.value = me?.id ?? null;
      lastResolvedToken.value = cacheKey;
      lastResolvedAt.value = now;
    } catch (error) {
      // 捕获任何错误（网络错误、会话过期等）
      console.error("Failed to load current user session", error);
      // 出错时将用户 ID 设为 null
      userId.value = null;
      lastResolvedAt.value = 0;
      lastResolvedToken.value = null;
    } finally {
      // 无论成功还是失败，都关闭加载标志
      isFetchingUser.value = false;
    }

    // 返回当前的用户 ID（可能是 null）
    return userId.value;
  };

  // ===== 导出公共 API =====
  // 返回用户状态和刷新方法
  return {
    userId, // 当前用户的 ID（响应式数据）
    isFetchingUser, // 是否正在加载用户信息的标志
    refreshUser, // 刷新用户信息的方法
  };
}
