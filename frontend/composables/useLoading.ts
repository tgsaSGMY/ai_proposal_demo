// ===== 加载状态组合式函数 =====
// 管理全局加载状态，提供跨组件的加载指示器
export const useLoading = () => {
  // ===== 全局加载状态变量 =====
  // 使用 useState 创建全局共享的加载状态
  // 这样所有组件都可以访问和修改相同的加载状态

  // 加载状态标志：true 表示正在加载，false 表示加载完成
  const isLoading = useState<boolean>("isLoading", () => false);

  // 加载时显示的消息文本（例如："保存中...","加载中..."）
  const loadingMessage = useState<string>("loadingMessage", () => "");

  // 是否显示进度条提示（对于长时间操作）
  const showProgressHint = useState<boolean>("showProgressHint", () => false);

  // 用於儲存逾時 ID，以便隨時清除
  const humorousTimeoutId = useState<any>("humorousTimeoutId", () => null);

  // ===== 显示加载动画的方法 =====
  // 启动加载状态，显示加载动画
  // 参数:
  //   - message: 加载时显示的消息（可选）
  //   - progressHint: 是否显示进度条提示（可选）
  const show = (message?: string, progressHint?: boolean) => {
    // 每次調用 show 前，先清除之前的 timer
    if (humorousTimeoutId.value) {
      clearTimeout(humorousTimeoutId.value);
      humorousTimeoutId.value = null;
    }

    // 设置加载状态为 true
    isLoading.value = true;
    // 设置加载消息（如果提供了消息，则显示；否则为空）
    loadingMessage.value = message ?? "";
    // 设置是否显示进度条提示
    showProgressHint.value = progressHint ?? false;

    // 建立一個 15 秒後的定時器，如果仍處於 isLoading 狀態，便切換到幽默訊息
    humorousTimeoutId.value = setTimeout(() => {
      if (isLoading.value) {
        loadingMessage.value = "稍等片刻，目前系統詠唱量較大，AI 正在瘋狂打字中... 🧙‍♂️💨";
      }
    }, 15000);
  };

  // ===== 隐藏加载动画的方法 =====
  // 隐藏加载动画，恢复正常状态
  const hide = () => {
    // 隱藏時清除定時器
    if (humorousTimeoutId.value) {
      clearTimeout(humorousTimeoutId.value);
      humorousTimeoutId.value = null;
    }

    // 设置加载状态为 false
    isLoading.value = false;
    // 清空加载消息
    loadingMessage.value = "";
    // 隐藏进度条提示
    showProgressHint.value = false;
  };

  // ===== 导出公共 API =====
  // 返回所有加载状态和控制方法
  return {
    isLoading, // 加载状态标志（响应式数据）
    loadingMessage, // 加载消息（响应式数据）
    showProgressHint, // 进度条提示标志（响应式数据）
    show, // 显示加载动画的方法
    hide, // 隐藏加载动画的方法
  };
};
