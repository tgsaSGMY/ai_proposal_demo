// ===== 导入依赖库 =====
// 导入 Supabase 认证和数据库客户端
import { supabase } from "~/utils/supabaseClient";

// ===== 内部权限检查组合式函数 =====
// 用于检查当前用户是否具有内部（管理员）权限
export const useInternalCheck = () => {
  // ===== 检查用户权限的核心方法 =====
  /**
   * 通过 Supabase 数据库函数检查当前用户是否为内部人员（管理员）
   *
   * 工作原理：
   *   1. 先检查用户是否已登录（有效会话）
   *   2. 调用 Supabase RPC (Remote Procedure Call) 函数 "is_internal"
   *   3. 该 RPC 函数会自动读取当前用户的 JWT Token 中的邮箱信息
   *   4. 在数据库中查询该邮箱是否在内部白名单中
   *   5. 返回检查结果
   *
   * 好处：
   *   - 不需要在前端暴露内部白名单表的 select 权限
   *   - 权限检查逻辑完全在服务端进行，更安全
   *   - 参数由数据库函数自动读取，无需从前端传参
   *
   * 返回值：
   *   - true: 用户是内部人员（有管理员权限）
   *   - false: 用户不是内部人员或检查失败
   */
  const checkIsInternal = async (): Promise<boolean> => {
    try {
      // ===== 第 1 步：检查用户是否已登录 =====
      // 虽然 RPC 会自动带上 Token，但先检查有没有登录
      // 这样可以省去一次不必要的网络请求
      const {
        data: { session },
      } = await supabase.auth.getSession();

      // 如果没有活跃的会话，说明用户未登录
      if (!session) {
        console.warn("User not logged in.");
        return false;
      }

      // ===== 第 2 步：调用 Supabase RPC 函数检查权限 =====
      // RPC (Remote Procedure Call) 是 Supabase 提供的服务器端函数调用机制
      // is_internal 函数会：
      //   - 自动读取当前 JWT Token 中的用户邮箱
      //   - 在数据库中查询该邮箱是否存在于内部白名单表中
      //   - 返回查询结果
      const { data, error } = await supabase.rpc("is_internal");

      // ===== 第 3 步：处理 RPC 调用结果 =====
      // 如果 RPC 调用出错，打印错误日志并返回 false
      if (error) {
        console.error("RPC check internal error:", error.message);
        return false;
      }

      // RPC 直接返回 true 或 false，将其转换为布尔值后返回
      return !!data;
    } catch (e) {
      // 捕获任何意外的错误（网络错误、解析错误等）
      console.error("Unexpected error in checkIsInternal:", e);
      // 出错时默认返回 false（不给予权限）
      return false;
    }
  };

  // ===== 导出公共 API =====
  // 返回权限检查方法
  return {
    checkIsInternal, // 检查当前用户是否为内部人员的方法
  };
};
