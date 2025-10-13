import { useLoading } from "~/composables/useLoading";

export default defineNuxtRouteMiddleware((to, from) => {
  const { show, hide } = useLoading();

  // 在導航開始前顯示 loading
  if (to.path !== from.path) {
    show();
  }

  if (to.meta.pageTransition && typeof to.meta.pageTransition === "object") {
    to.meta.pageTransition.onAfterLeave = () => {
      hide();
    };
  }
});
