import { v4 as uuidv4 } from "uuid";

// 定義通知的類型
export type NotificationType = "success" | "error" | "info" | "warning";

// 定義單個通知的接口
export interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  duration?: number; // 可選的持續時間（毫秒）
}

export const useNotifications = () => {
  // 使用 useState 創建一個全局共享的通知數組
  const notifications = useState<Notification[]>("notifications", () => []);

  // 添加通知的方法
  const add = (
    type: NotificationType,
    message: string,
    duration: number = 5000 // 默認持續 5 秒
  ) => {
    const id = uuidv4();
    notifications.value.push({
      id,
      type,
      message,
      duration,
    });

    // 設置計時器，在持續時間後自動移除此通知
    setTimeout(() => {
      remove(id);
    }, duration);
  };

  // 移除通知的方法
  const remove = (id: string) => {
    const index = notifications.value.findIndex((n) => n.id === id);
    if (index !== -1) {
      notifications.value.splice(index, 1);
    }
  };

  const success = (message: string, duration?: number) =>
    add("success", message, duration);
  const error = (message: string, duration?: number) =>
    add("error", message, duration);
  const info = (message: string, duration?: number) =>
    add("info", message, duration);
  const warning = (message: string, duration?: number) =>
    add("warning", message, duration);

  return {
    notifications,
    add,
    remove,
    success,
    error,
    info,
    warning,
  };
};
