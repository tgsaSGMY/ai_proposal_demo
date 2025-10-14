import { useLoading } from "~/composables/useLoading";

export default defineNuxtPlugin((nuxtApp) => {
  const { show, hide } = useLoading();

  // 監聽路由開始變更事件
  nuxtApp.hook("page:start", () => {
    show();
  });

  // 監聽路由結束變更事件
  nuxtApp.hook("page:finish", () => {
    hide();
  });

  // 監聽路由錯誤
  nuxtApp.hook("app:error", () => {
    hide();
  });
});
