<template>
  <!-- 通知容器，固定在屏幕右上角 -->
  <div class="fixed top-4 right-4 z-50 w-full max-w-sm space-y-3">
    <!-- 使用 TransitionGroup 讓列表的增刪有動畫效果 -->
    <TransitionGroup name="list" tag="div">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="notificationClasses(notification.type)"
        class="w-full rounded-lg shadow-lg p-4 flex items-start"
      >
        <!-- Icon -->
        <div class="flex-shrink-0">
          <component
            :is="notificationIcon(notification.type)"
            class="h-6 w-6"
          />
        </div>
        <!-- Message -->
        <div class="ml-3 w-0 flex-1">
          <p class="text-sm font-medium">
            {{ notification.message }}
          </p>
        </div>
        <!-- Close Button -->
        <div class="ml-4 flex-shrink-0 flex">
          <button
            @click="remove(notification.id)"
            class="inline-flex rounded-md text-current opacity-70 hover:opacity-100 focus:outline-none"
          >
            <span class="sr-only">Close</span>
            <svg
              class="h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clip-rule="evenodd"
              />
            </svg>
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useNotifications } from "~/composables/useNotifications";
import {
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
} from "@heroicons/vue/24/outline";

const { notifications, remove } = useNotifications();

// 根據通知類型返回對應的 Tailwind CSS 樣式
const notificationClasses = (type) => {
  const baseClasses = "bg-white text-gray-900 border";
  const typeClasses = {
    success: "bg-green-50 border-green-400 text-green-800",
    error: "bg-red-50 border-red-400 text-red-800",
    info: "bg-blue-50 border-blue-400 text-blue-800",
    warning: "bg-yellow-50 border-yellow-400 text-yellow-800",
  };
  return typeClasses[type] || baseClasses;
};

// 根據通知類型返回對應的圖標組件
const notificationIcon = (type) => {
  const icons = {
    success: CheckCircleIcon,
    error: XCircleIcon,
    info: InformationCircleIcon,
    warning: ExclamationTriangleIcon,
  };
  return icons[type] || InformationCircleIcon;
};
</script>

<style>
.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
