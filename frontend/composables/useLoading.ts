export const useLoading = () => {
  // 使用 useState 來創建一個全局共享的 ref
  const isLoading = useState<boolean>("isLoading", () => false);

  const show = () => {
    isLoading.value = true;
  };

  const hide = () => {
    isLoading.value = false;
  };

  return {
    isLoading,
    show,
    hide,
  };
};
