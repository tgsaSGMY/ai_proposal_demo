<!-- 全局确认对话框组件：显示带两个按钮的确认弹窗，支持primary和danger两种样式 -->
<template>
  <Transition
    enter-active-class="transition-opacity duration-300 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-200 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="isVisible && options"
      class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900 bg-opacity-60 p-2 sm:p-4"
      @click.self="handleCancel"
    >
      <Transition
        enter-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          class="w-full max-w-xs sm:max-w-md bg-white rounded-xl shadow-2xl overflow-hidden"
        >
          <div class="p-4 sm:p-6">
            <div class="flex flex-col sm:flex-row items-start">
              <!-- Icon -->
              <div
                class="mx-auto sm:mx-0 flex-shrink-0 flex items-center justify-center h-10 w-10 sm:h-12 sm:w-12 rounded-full"
                :class="iconBgColor"
              >
                <ExclamationTriangleIcon
                  v-if="options.confirmColor === 'danger'"
                  class="h-5 w-5 sm:h-6 sm:w-6"
                  :class="iconColor"
                />
                <QuestionMarkCircleIcon
                  v-else
                  class="h-5 w-5 sm:h-6 sm:w-6"
                  :class="iconColor"
                />
              </div>
              <div class="mt-3 sm:mt-0 sm:ml-4 text-left flex-1">
                <h3
                  class="text-base sm:text-lg leading-6 font-bold text-gray-900"
                >
                  {{ options.title }}
                </h3>
                <div class="mt-1 sm:mt-2">
                  <p
                    class="text-xs sm:text-sm text-gray-500 whitespace-pre-wrap"
                  >
                    {{ options.message }}
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div
            class="bg-gray-50 px-4 sm:px-6 py-3 sm:py-4 flex flex-col-reverse sm:flex-row-reverse gap-2 sm:gap-3"
          >
            <button
              @click="handleConfirm"
              type="button"
              class="inline-flex justify-center rounded-md border border-transparent shadow-sm px-3 sm:px-4 py-2 text-sm sm:text-base font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2"
              :class="confirmButtonClass"
            >
              {{ options.confirmText }}
            </button>
            <button
              @click="handleCancel"
              type="button"
              class="inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-3 sm:px-4 py-2 bg-white text-sm sm:text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {{ options.cancelText }}
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from "vue";
import { useConfirm } from "~/composables/useConfirm";
import {
  ExclamationTriangleIcon,
  QuestionMarkCircleIcon,
} from "@heroicons/vue/24/outline";

const { isVisible, options, handleConfirm, handleCancel } = useConfirm();

// 根据确认按钮类型返回对应的样式类（primary为蓝色，danger为红色）
const confirmButtonClass = computed(() => {
  if (!options.value) return "";
  return (
    {
      primary: "bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500",
      danger: "bg-red-600 hover:bg-red-700 focus:ring-red-500",
    }[options.value.confirmColor] ||
    "bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500"
  );
});

// 根据确认颜色返回图标背景色
const iconBgColor = computed(() => {
  if (!options.value) return "";
  return (
    {
      primary: "bg-indigo-100",
      danger: "bg-red-100",
    }[options.value.confirmColor] || "bg-indigo-100"
  );
});

// 根据确认颜色返回图标颜色
const iconColor = computed(() => {
  if (!options.value) return "";
  return (
    {
      primary: "text-indigo-600",
      danger: "text-red-600",
    }[options.value.confirmColor] || "text-indigo-600"
  );
});
</script>
