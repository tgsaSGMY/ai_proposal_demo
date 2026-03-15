/**
 * Redirect If Authenticated Middleware
 * 如果用户已登入，會重新導向到首頁
 */
import { getAppSession } from "~/composables/useAppAuth";

export default defineNuxtRouteMiddleware(async (to, from) => {
  // 只在客戶端運行
  if (process.server) return;

  // 檢查 Supabase 中的認證狀態
  try {
    const session = await getAppSession();
    // 如果已經有有效的 session 和用戶，導向到首頁
    if (session.isAuthenticated) {
      return navigateTo("/");
    }
  } catch (error) {
    console.error("Redirect middleware error:", error);
  }
});
