/**
 * Auth Middleware - 保護需要認證的頁面
 * 1. 未登入 -> 導向 /login
 * 2. 已登入但非內部人員嘗試訪問 /_builder -> 導向 /
 */
import { supabase } from "~/utils/supabaseClient";

export default defineNuxtRouteMiddleware(async (to, from) => {
  // 1. 公開頁面：如果是登入或註冊頁面，直接允許
  if (to.path === "/login" || to.path === "/signup") {
    return;
  }

  // 避免在 Server 端執行 (保留你原本的設定)
  if (process.server) return;

  try {
    // 2. 檢查登入狀態
    const {
      data: { session },
    } = await supabase.auth.getSession();

    // 如果沒有 session 或沒有用戶，重新導向到登入頁面
    if (!session || !session.user) {
      return navigateTo("/login");
    }

    // ============================================================
    // 新增邏輯：保護 _builder 路徑
    // ============================================================
    if (to.path.startsWith("/_builder")) {
      // 查詢 whitelist 資料表
      const { data, error } = await supabase
        .from("whitelist")
        .select("role")
        .eq("email", session.user.email)
        .maybeSingle(); // 使用 maybeSingle 避免查無資料時報錯

      const isInternal = data?.role === "internal";

      // 如果發生錯誤、找不到資料、或是角色不是 internal
      if (error || !isInternal) {
        // console.warn(
        //   `User ${session.user.email} tried to access builder but is not internal.`
        // );
        // 自動返回 home page
        return navigateTo("/");
      }
    }
    // ============================================================

    // 驗證全部通過，允許訪問
    return;
  } catch (error) {
    console.error("Auth middleware error:", error);
    // 發生嚴重錯誤時導向到登入頁面
    return navigateTo("/login");
  }
});
