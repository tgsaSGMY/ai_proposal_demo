<template>
  <!-- 使用 Transition 讓顯示/隱藏有淡入淡出效果 -->
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
      class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900 bg-opacity-50"
    >
      <div class="flex flex-col items-center">
        <!-- Spinner 動畫 -->
        <div
          class="w-16 h-16 border-4 border-t-4 border-gray-200 border-t-indigo-500 rounded-full animate-spin"
        ></div>
        <!-- 可選的加載文字 -->
        <!-- <p class="mt-4 text-white text-lg font-semibold">Loading...</p> -->
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { useLoading } from "~/composables/useLoading";

const { isLoading } = useLoading();
</script>

<style scoped>
/* 我們也可以直接在 style 裡定義 spin 動畫，以防 Tailwind JIT 沒有生成它 */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
