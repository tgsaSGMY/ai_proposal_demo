/**
 * Auth Middleware - 保護需要認證的頁面
 * 1. 未登入 -> 導向 /login
 * 2. 已登入但非內部人員嘗試訪問 /_builder -> 導向 /
 */
import { authenticatedFetch, getAppSession } from "~/composables/useAppAuth";

export default defineNuxtRouteMiddleware(async (to, from) => {
  // 1. 公開頁面：如果是登入或註冊頁面，直接允許
  const publicPaths = new Set([
    "/login",
    "/_builder/login",
    "/_builder/signup",
    "/_builder/forgot-password",
    "/_builder/reset-password",
  ]);
  if (publicPaths.has(to.path)) {
    return;
  }

  if (process.server) return;

  try {
    // 2. 檢查登入狀態
    const session = await getAppSession();

    // 如果沒有 session 或沒有用戶，重新導向到登入頁面
    if (!session.isAuthenticated) {
      return navigateTo("/login");
    }

    // 3. 內部人員檢查：只有訪問 /_builder 才需要打 /auth/me。
    if (to.path.startsWith("/_builder")) {
      const config = useRuntimeConfig();
      const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
      const meResponse = await authenticatedFetch(`${API_BASE_URL}/auth/me`);

      if (!meResponse.ok) {
        return navigateTo("/login");
      }

      const me = await meResponse.json();
      if (me?.role !== "internal") {
        // 自動返回 home page
        return navigateTo("/");
      }
    }

    // 驗證全部通過，允許訪問
    return;
  } catch (error) {
    console.error("Auth middleware error:", error);
    // 發生嚴重錯誤時導向到登入頁面
    return navigateTo("/login");
  }
});
