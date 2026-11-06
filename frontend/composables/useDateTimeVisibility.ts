export function useDateTimeVisibility() {
  const config = useRuntimeConfig();
  return {
    hideDateTime: computed(() => config.public.hideDateTimeUi === true),
  };
}
