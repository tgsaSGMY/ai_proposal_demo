// ===== 导入依赖库 =====
// 导入 Vue 的 ref 函数用于创建响应式数据
import { ref } from "vue";

// ===== 确认对话框选项接口 =====
/**
 * 定义确认对话框（Modal）的配置选项
 */
interface ConfirmOptions {
  title: string; // 对话框标题
  message: string; // 对话框消息内容
  confirmText?: string; // 确认按钮的文字（默认："确认"）
  cancelText?: string; // 取消按钮的文字（默认："取消"）
  confirmColor?: "primary" | "danger"; // 确认按钮的颜色（蓝色或红色）
}

// ===== 全局确认对话框状态 =====
// 注意：这些状态不使用 useState，而是普通的 ref
// 原因：避免跨页面污染（在多个页面间共享状态可能导致数据混乱）
// 每个页面都有自己的确认对话框实例

// 对话框是否显示
const isVisible = ref(false);
// 当前对话框的配置选项
const options = ref<ConfirmOptions | null>(null);

// ===== 全局 Promise 解决函数 =====
// 这个函数会被保存起来，用于在用户点击确认/取消时改变 Promise 的状态
let resolvePromise: (value: boolean) => void;

// ===== 确认对话框组合式函数 =====
/**
 * 管理确认对话框的显示和交互
 *
 * 使用 Promise 模式，使得调用方可以用 await 的方式来等待用户的确认/取消操作
 *
 * 示例：
 *   const { confirm } = useConfirm();
 *   const result = await confirm({
 *     title: '删除确认',
 *     message: '确定要删除吗？',
 *     confirmText: '删除',
 *     confirmColor: 'danger'
 *   });
 *   if (result) {
 *     // 用户点击了确认
 *   } else {
 *     // 用户点击了取消
 *   }
 */
export const useConfirm = () => {
  // ===== 显示确认对话框 =====
  /**
   * 显示确认对话框并返回一个 Promise
   * Promise 会在用户点击确认或取消时改变状态
   *
   * 参数: opts - 对话框配置选项
   *
   * 返回值：
   *   - 用户点击确认：Promise 结果为 true
   *   - 用户点击取消：Promise 结果为 false
   */
  const confirm = (opts: ConfirmOptions): Promise<boolean> => {
    // ===== 设置对话框配置 =====
    // 合并用户传入的选项和默认值
    // 优先使用用户传入的值，如果没有则使用默认值
    options.value = {
      confirmText: "确认", // 默认确认按钮文字
      cancelText: "取消", // 默认取消按钮文字
      confirmColor: "primary", // 默认按钮颜色为蓝色（primary）
      ...opts, // 用户的自定义选项会覆盖上面的默认值
    };
    // 显示对话框
    isVisible.value = true;

    // ===== 返回一个新的 Promise =====
    // 这个 Promise 会在用户点击确认或取消时改变状态
    // 我们将 resolve 函数保存到全局变量，
    // 以便在 handleConfirm 或 handleCancel 中调用
    return new Promise((resolve) => {
      resolvePromise = resolve;
    });
  };

  // ===== 处理用户点击"确认"按钮 =====
  /**
   * 当用户点击对话框的确认按钮时调用
   * 会让等待中的 Promise 以 true 结果完成
   * 并关闭对话框
   */
  const handleConfirm = () => {
    // 调用保存的 Promise resolve 函数，传入 true（表示用户确认了）
    if (resolvePromise) {
      resolvePromise(true);
    }
    // 隐藏对话框
    isVisible.value = false;
  };

  // ===== 处理用户点击"取消"按钮 =====
  /**
   * 当用户点击对话框的取消按钮或按下 ESC 键时调用
   * 会让等待中的 Promise 以 false 结果完成
   * 并关闭对话框
   */
  const handleCancel = () => {
    // 调用保存的 Promise resolve 函数，传入 false（表示用户取消了）
    if (resolvePromise) {
      resolvePromise(false);
    }
    // 隐藏对话框
    isVisible.value = false;
  };

  // ===== 导出公共 API =====
  // 返回对话框状态和交互方法
  return {
    isVisible, // 对话框是否显示（响应式数据）
    options, // 对话框配置选项（响应式数据）
    confirm, // 显示确认对话框的方法
    handleConfirm, // 处理确认按钮点击的方法
    handleCancel, // 处理取消按钮点击的方法
  };
};
