<template>
  <div class="min-h-screen bg-gray-50 font-sans flex flex-col md:flex-row">
    <header
      class="md:hidden bg-white text-gray-900 flex items-center justify-between px-4 py-3 border-b border-gray-200 sticky top-0 z-40"
    >
      <div class="flex flex-col">
        <img src="/AI補助引擎_Logo_留邊.png" alt="AI 補助引擎" class="h-8 w-auto pointer-events-none select-none" />
        <p v-if="sessionExpiryText" class="text-[10px] text-gray-400 leading-tight mt-0.5">
          {{ sessionExpiryText }}
        </p>
      </div>
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
          </div>

        </div>

        <!-- Center: Demo Mode Info Bubble -->
        <div v-if="!isSidebarCollapsed" class="mt-6 px-4 py-3.5 rounded-2xl bg-amber-50/70 border border-amber-100">
          <p class="text-xs text-amber-600 uppercase tracking-wide font-bold flex items-center gap-1.5 select-none">
            <span>✨</span>
            <span>【體驗版】AI 補助引擎 </span>
          </p>
          <p class="text-xs text-amber-700 mt-2 leading-relaxed">
            系統已為您開放<strong class="font-bold text-amber-800">限定額度</strong>免費對話與智慧推演功能。歡迎立即體驗，見證 AI 協助您快速建構與產出高效計畫書的實質成效。🚀
          </p>
          <p class="text-xs text-amber-600 mt-3 leading-relaxed border-t border-amber-200/50 pt-2.5">
            <strong class="font-bold flex items-center gap-1 select-none text-amber-700">💡 重要提醒</strong>
            本功能目前為免登入的臨時體驗模式。提醒您，下方的倒數計時結束後,<strong class="font-bold text-amber-700">系統將自動清除當前頁面的所有對話與企劃內容。</strong>建議您立即註冊免費帳號，即可永久儲存您的精彩企劃，隨時隨地繼續編輯。
          </p>
        </div>

        <div class="flex-1" />

        <div v-if="!isSidebarCollapsed" class="mt-6 space-y-3">
          <!-- Bottom Expiry Countdown (Soft & Inviting) -->
          <div v-if="sessionExpiryText" class="px-4 py-2.5 rounded-2xl bg-slate-50 border border-slate-100 text-center">
            <p class="text-[11px] text-slate-500 flex items-center justify-center gap-1.5 leading-none">
              <span>⏳</span>
              <span>本期試用剩餘時間：</span>
              <span class="font-semibold text-slate-700 font-mono text-xs">{{ sessionExpiryText }}</span>
            </p>
          </div>

          <a
            :href="registerUrl"
            target="_blank"
            class="flex items-center justify-center gap-2 w-full rounded-full bg-gradient-to-r from-rose-500 to-amber-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg hover:shadow-xl transition hover:-translate-y-0.5"
          >
            <span>註冊免費帳號</span>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </a>
        </div>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto min-h-screen">
      <slot />
    </main>

  </div>
</template>
<script setup>
import { ref, onMounted, watch, computed } from "vue";
import { useSessionExpiry } from "~/composables/useSessionExpiry";

const showSidebar = ref(false);
const isSidebarCollapsed = ref(false);
const SIDEBAR_COLLAPSED_KEY = "tgsa.sidebarCollapsed";

const runtimeConfig = useRuntimeConfig();
const registerUrl = computed(
  () =>
    runtimeConfig.public.platformHomeUrl ||
    "https://aiproposal.tgsa.com.tw/api/external-auth/redirect"
);

const expiresAt = ref(null);
const { timeString: sessionExpiryText } = useSessionExpiry(expiresAt);

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

  // Fetch session expiry via the shared memoised bootstrap so the layout does
  // NOT mint a second demo session in parallel with the page (see useDemoSession).
  {
    const { ensureDemoSession } = useDemoSession();
    ensureDemoSession()
      .then((data) => {
        if (data && data.expires_at) {
          expiresAt.value = data.expires_at;
        }
      })
      .catch((err) => {
        console.warn("Failed to fetch session expiry", err);
      });
  }
});
</script>
