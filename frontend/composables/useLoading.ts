export const useLoading = () => {
  // useState -》創建一個全局共享的 ref
  const isLoading = useState<boolean>("isLoading", () => false);
  const loadingMessage = useState<string>("loadingMessage", () => "");
  const showProgressHint = useState<boolean>("showProgressHint", () => false);

  const show = (message?: string, progressHint?: boolean) => {
    isLoading.value = true;
    loadingMessage.value = message || "";
    showProgressHint.value = progressHint || false;
  };

  const hide = () => {
    isLoading.value = false;
    loadingMessage.value = "";
    showProgressHint.value = false;
  };

  return {
    isLoading,
    loadingMessage,
    showProgressHint,
    show,
    hide,
  };
};
