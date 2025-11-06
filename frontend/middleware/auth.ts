/**
 * Auth Middleware - 保護需要認證的頁面
 * 如果用户未登入，會重新導向到登入頁面
 */
import { supabase } from "~/utils/supabaseClient";

export default defineNuxtRouteMiddleware(async (to, from) => {
  // 如果要訪問的就是登入或邀請頁面，允許訪問
  if (to.path === "/login" || to.path === "/signup") {
    return;
  }

  // 檢查 Supabase 中的認證狀態
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    // 如果沒有 session 或沒有用戶，重新導向到登入頁面
    if (!session || !session.user) {
      return navigateTo("/login");
    }

    // 如果有有效的 session，允許訪問
    return;
  } catch (error) {
    console.error("Auth middleware error:", error);
    // 發生錯誤時也導向到登入頁面
    return navigateTo("/login");
  }
});
