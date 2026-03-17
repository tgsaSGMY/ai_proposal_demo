import { useLoading } from "~/composables/useLoading";

export default defineNuxtPlugin((nuxtApp) => {
  const { hide } = useLoading();

  // 監聽路由錯誤
  nuxtApp.hook("app:error", () => {
    hide();
  });
});
