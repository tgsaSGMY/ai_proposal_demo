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
      <div class="flex flex-col items-center">
        <div
          class="w-12 h-12 sm:w-16 sm:h-16 border-4 border-t-4 border-gray-200 border-t-indigo-500 rounded-full animate-spin"
        ></div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { useLoading } from "~/composables/useLoading";

const { isLoading } = useLoading();
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
