import { supabase } from "~/utils/supabaseClient";

export const useInternalCheck = () => {
  /**
   * 透過資料庫函數檢查當前使用者是否為內部人員
   * 不需要開放 whitelist table 的 select 權限
   */
  const checkIsInternal = async (): Promise<boolean> => {
    try {
      // 1. 雖然 RPC 會自動帶 Token，但先檢查有沒有登入可以省一次網路請求
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        console.warn("User not logged in.");
        return false;
      }

      // 2. 呼叫 Supabase RPC (Remote Procedure Call)
      // is_internal 函數內部會自動讀取 auth.jwt() 裡的 email，不需要從前端傳參數
      const { data, error } = await supabase.rpc("is_internal");

      if (error) {
        console.error("RPC check internal error:", error.message);
        return false;
      }

      // 3. RPC 直接回傳 true 或 false
      return !!data;
    } catch (e) {
      console.error("Unexpected error in checkIsInternal:", e);
      return false;
    }
  };

  return {
    checkIsInternal,
  };
};
