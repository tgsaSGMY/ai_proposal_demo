import { supabase } from "~/utils/supabaseClient";

export const useInternalCheck = () => {
  /**
   * 檢查當前使用者是否為內部人員 (role === 'internal')
   */
  const checkIsInternal = async (): Promise<boolean> => {
    try {
      // 1. 獲取當前登入的使用者資訊
      const {
        data: { user },
      } = await supabase.auth.getUser();

      // 如果沒登入或沒 email，直接回傳 false
      if (!user || !user.email) {
        console.warn("User not logged in or email missing.");
        return false;
      }

      // 2. 查詢 whitelist 表
      // 根據截圖：table 名稱是 'whitelist'，欄位是 'email' 和 'role'
      const { data, error } = await supabase
        .from("whitelist")
        .select("role")
        .eq("email", user.email)
        .maybeSingle(); // 使用 maybeSingle 避免找不到資料時噴錯 (回傳 null)

      if (error) {
        console.error("Check internal error:", error.message);
        return false;
      }

      // 3. 驗證 role 是否為 'internal'
      // 確保 data 存在且 role 欄位內容吻合
      if (data && data.role === "internal") {
        return true;
      }

      return false;
    } catch (e) {
      console.error("Unexpected error in checkIsInternal:", e);
      return false;
    }
  };

  return {
    checkIsInternal,
  };
};
