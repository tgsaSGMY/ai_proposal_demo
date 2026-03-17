// ===== 导入依赖库 =====
import { authenticatedFetch } from "~/composables/useAppAuth";

// ===== 内部权限检查组合式函数 =====
// 用于检查当前用户是否具有内部（管理员）权限
export const useInternalCheck = () => {
  // ===== 检查用户权限的核心方法 =====
  /**
   * 通过 Supabase 数据库函数检查当前用户是否为内部人员（管理员）
   *
   * 工作原理：
   *   1. 调用后端 /api/auth/me
   *   2. 后端会解析 Bearer token，并同步 users/user_identities
   *   3. 读取 users.role 判断是否为 internal
   *   4. 返回检查结果
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
      const config = useRuntimeConfig();
      const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

      const response = await authenticatedFetch(`${API_BASE_URL}/auth/me`);

      if (!response.ok) {
        console.error("Failed to fetch /api/auth/me:", response.status);
        return false;
      }

      const me = await response.json();
      return me?.role === "internal";
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
