// ===== 导入依赖库 =====
// 导入 uuid 库用于生成唯一的通知 ID
import { v4 as uuidv4 } from "uuid";

// ===== 类型定义 =====
// 定义通知的类型：成功、错误、信息、警告
export type NotificationType = "success" | "error" | "info" | "warning";

// ===== 通知接口定义 =====
// 定义单个通知对象的结构
export interface Notification {
  id: string; // 通知的唯一标识符
  type: NotificationType; // 通知类型（success/error/info/warning）
  message: string; // 通知显示的消息内容
  duration?: number; // 可选的显示持续时间（毫秒），默认 5000ms
}

// ===== 通知组合式函数 =====
export const useNotifications = () => {
  // 使用 useState 创建一个全局共享的通知数组
  // 所有组件都可以访问和修改这个共享的通知列表
  const notifications = useState<Notification[]>("notifications", () => []);

  // ===== 添加通知的核心方法 =====
  // 向通知列表添加一条新的通知消息
  // 参数:
  //   - type: 通知类型
  //   - message: 通知内容
  //   - duration: 显示持续时间（默认 5000ms = 5秒）
  const add = (
    type: NotificationType,
    message: string,
    duration: number = 5000 // 默认持续 5 秒后自动关闭
  ) => {
    // 生成唯一的通知 ID
    const id = uuidv4();
    // 创建通知对象并添加到通知列表
    notifications.value.push({
      id,
      type,
      message,
      duration,
    });

    // 在指定时间后自动移除通知
    // 这样用户不需要手动关闭，通知会自动消失
    setTimeout(() => {
      remove(id);
    }, duration);
  };

  // ===== 移除通知的方法 =====
  // 根据通知 ID 从列表中移除指定的通知
  // 参数: id - 要移除的通知 ID
  const remove = (id: string) => {
    // 查找通知在数组中的位置
    const index = notifications.value.findIndex((n) => n.id === id);
    // 如果找到了通知，则从数组中移除
    if (index !== -1) {
      notifications.value.splice(index, 1);
    }
  };

  // ===== 便捷方法：快速显示各类通知 =====
  // 显示成功通知：绿色提示框
  const success = (message: string, duration?: number) =>
    add("success", message, duration);

  // 显示错误通知：红色提示框
  const error = (message: string, duration?: number) =>
    add("error", message, duration);

  // 显示信息通知：蓝色提示框
  const info = (message: string, duration?: number) =>
    add("info", message, duration);

  // 显示警告通知：黄色提示框
  const warning = (message: string, duration?: number) =>
    add("warning", message, duration);

  // ===== 导出公共 API =====
  // 返回所有公共方法和状态
  return {
    notifications, // 通知列表（响应式数据）
    add, // 添加自定义通知的方法
    remove, // 移除通知的方法
    success, // 显示成功通知的快捷方法
    error, // 显示错误通知的快捷方法
    info, // 显示信息通知的快捷方法
    warning, // 显示警告通知的快捷方法
  };
};
