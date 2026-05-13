/**
 * Auth Middleware - 保護需要認證的頁面
 * 1. 未登入 -> 導向 /login
 * 2. 已登入但非內部人員嘗試訪問 /_builder -> 導向 /
 */
import { authenticatedFetch, getAppSession } from "~/composables/useAppAuth";

export default defineNuxtRouteMiddleware(async (to, from) => {
  if (to.path === "/login") return;

  if (process.server) return;

  try {
    const session = await getAppSession();
    if (!session.isAuthenticated) {
      return navigateTo("/login");
    }
    return;
  } catch (error) {
    console.error("Auth middleware error:", error);
    return navigateTo("/login");
  }
});
