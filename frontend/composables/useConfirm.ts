import { ref } from "vue";

// 定義 Modal 的選項接口
interface ConfirmOptions {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmColor?: "primary" | "danger"; // 用於按鈕顏色
}

// 狀態將由 composable 內部管理，不使用 useState 以免跨頁面污染
const isVisible = ref(false);
const options = ref<ConfirmOptions | null>(null);

// 用於解決 Promise 的函數
let resolvePromise: (value: boolean) => void;

export const useConfirm = () => {
  const confirm = (opts: ConfirmOptions): Promise<boolean> => {
    options.value = {
      confirmText: "確認",
      cancelText: "取消",
      confirmColor: "primary",
      ...opts,
    };
    isVisible.value = true;

    // 返回一個新的 Promise，並將 resolve 函數保存起來
    return new Promise((resolve) => {
      resolvePromise = resolve;
    });
  };

  const handleConfirm = () => {
    if (resolvePromise) {
      resolvePromise(true);
    }
    isVisible.value = false;
  };

  const handleCancel = () => {
    if (resolvePromise) {
      resolvePromise(false);
    }
    isVisible.value = false;
  };

  return {
    isVisible,
    options,
    confirm,
    handleConfirm,
    handleCancel,
  };
};
