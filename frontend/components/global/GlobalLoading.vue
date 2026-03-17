<!-- 全局加载动画组件：显示旋转加载指示器和加载消息 -->
<template>
  <Transition
    enter-active-class="transition-opacity duration-200 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-200 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="isLoading"
      class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900 bg-opacity-60 p-2 sm:p-0"
    >
      <div class="flex flex-col items-center gap-4 sm:gap-6">
        <div
          class="w-12 h-12 sm:w-16 sm:h-16 border-4 border-t-4 border-gray-200 border-t-indigo-500 rounded-full animate-spin"
        ></div>
        <div v-if="loadingMessage" class="text-center">
          <p class="text-white text-sm sm:text-base font-medium">
            {{ loadingMessage }}
          </p>
          <p
            v-if="showProgressHint"
            class="text-gray-300 text-xs sm:text-sm mt-2"
          >
            💡 此操作可能需要 2-3 分鐘，請耐心等待...
          </p>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
// 使用全局加载状态组合式函数
import { useLoading } from "~/composables/useLoading";

const { isLoading, loadingMessage, showProgressHint } = useLoading();
</script>

<style scoped>
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
