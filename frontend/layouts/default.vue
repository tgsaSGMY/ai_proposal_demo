<template>
  <div class="min-h-screen bg-gray-50 font-sans flex flex-col md:flex-row">
    <header
      class="md:hidden bg-white text-gray-900 flex items-center justify-between px-4 py-3 border-b border-gray-200 sticky top-0 z-40"
    >
      <img src="/AI補助引擎_Logo_留邊.png" alt="AI 補助引擎" class="h-8 w-auto pointer-events-none select-none" />
      <button @click="showSidebar = !showSidebar" class="focus:outline-none">
        <svg
          v-if="!showSidebar"
          xmlns="http://www.w3.org/2000/svg"
          class="h-7 w-7"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          class="h-7 w-7"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </header>

    <aside
      :class="[
        showSidebar ? 'block' : 'hidden',
        'md:block',
        'w-full flex-shrink-0 bg-white border-r border-gray-100 shadow-sm transition-[width] duration-200',
        isSidebarCollapsed ? 'md:w-20' : 'md:w-72 lg:w-80',
        showSidebar
          ? 'fixed top-0 left-0 h-full z-50 overflow-y-auto md:static md:h-screen'
          : 'md:sticky md:top-0 md:h-screen md:overflow-y-auto md:z-30',
      ]"
      style="max-width: 100vw"
    >
      <div
        v-if="showSidebar"
        class="md:hidden sticky top-0 bg-white z-50 flex items-center justify-between px-4 py-3 border-b border-gray-200"
      >
        <img src="/AI補助引擎_Logo_留邊.png" alt="AI 補助引擎" class="h-8 w-auto pointer-events-none select-none" />
        <button @click="showSidebar = false" class="focus:outline-none">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-7 w-7"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <div
        class="flex h-full flex-col p-5"
        :class="isSidebarCollapsed ? 'md:p-3' : 'md:p-6'"
      >
        <div
          class="flex items-center px-2"
          :class="isSidebarCollapsed ? 'md:flex-col md:gap-2 md:px-0' : 'gap-2 justify-between'"
        >
          <div
            class="flex flex-col min-w-0"
            :class="isSidebarCollapsed ? 'md:items-center md:w-full' : 'items-start'"
          >
            <img
              :src="
                isSidebarCollapsed
                  ? '/AI補助引擎.png'
                  : '/AI補助引擎_Logo_留邊.png'
              "
              alt="AI 補助引擎"
              class="pointer-events-none select-none max-w-full"
              :class="isSidebarCollapsed ? 'h-7 w-auto' : 'h-14 w-auto'"
            />
            <p
              v-if="!isSidebarCollapsed"
              class="mt-2 text-[11px] uppercase tracking-wide text-amber-500 font-semibold"
            >
              {Demo} 試用版
            </p>
          </div>

        </div>

        <div class="flex-1" />

        <div v-if="!isSidebarCollapsed" class="mt-6 space-y-3">
          <div class="px-4 py-3 rounded-2xl bg-amber-50 border border-amber-100">
            <p class="text-xs text-amber-600 uppercase tracking-wide font-semibold">
              Demo Mode
            </p>
            <p class="text-xs text-amber-700 mt-1 leading-relaxed">
              這是 AI 補助引擎的試用體驗版。<br />
              註冊免費帳號即可解鎖完整功能。
            </p>
          </div>
        </div>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto min-h-screen">
      <slot />
    </main>

  </div>
</template>
<script setup>
import { ref, onMounted, watch } from "vue";

const showSidebar = ref(false);
const isSidebarCollapsed = ref(false);
const SIDEBAR_COLLAPSED_KEY = "tgsa.sidebarCollapsed";

watch(isSidebarCollapsed, (collapsed) => {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? "1" : "0");
  } catch (err) {
    console.warn("Failed to persist sidebar collapse state", err);
  }
});

onMounted(() => {
  if (typeof window !== "undefined") {
    try {
      const stored = window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
      if (stored === "1") {
        isSidebarCollapsed.value = true;
      }
    } catch (err) {
      console.warn("Failed to read sidebar collapse state", err);
    }
  }
});
</script>
