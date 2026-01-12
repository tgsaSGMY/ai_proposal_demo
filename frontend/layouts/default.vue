<template>
  <div class="min-h-screen bg-gray-50 font-sans flex flex-col md:flex-row">
    <header
      class="md:hidden bg-white text-gray-900 flex items-center justify-between px-4 py-3 border-b border-gray-200 sticky top-0 z-40"
    >
      <div class="font-semibold text-lg">
        TGSA企劃引擎
        <span class="text-xs text-gray-400 align-top">PRO ENTERPRISE</span>
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
        'w-full md:w-72 lg:w-80 flex-shrink-0 bg-white border-r border-gray-100 shadow-sm',
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
        <div class="font-semibold text-lg">
          TGSA企劃引擎
          <span class="text-xs text-gray-400 align-top">PRO ENTERPRISE</span>
        </div>
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

      <div class="flex h-full flex-col p-5 md:p-6">
        <div class="flex items-center gap-3 px-2">
          <div class="h-11 w-11 rounded-2xl overflow-hidden">
            <img
              src="/logo.png"
              alt="TGSA 企劃引擎"
              class="h-full w-full object-cover"
            />
          </div>

          <div>
            <p class="text-lg font-semibold text-gray-900">TGSA企劃引擎</p>
            <p
              v-if="isInternal"
              class="text-xs uppercase tracking-wide text-gray-400"
            >
              PRO ENTERPRISE (内部人員版本)
            </p>
            <p v-else class="text-xs uppercase tracking-wide text-gray-400">
              PRO ENTERPRISE
            </p>
          </div>
        </div>

        <nav class="mt-8 flex-1" aria-label="主選單">
          <template v-if="isAuthenticated">
            <div v-if="!isInternalView" class="space-y-3">
              <NuxtLink
                to="/"
                class="flex items-center justify-between rounded-2xl px-5 py-4 transition hover:-translate-y-0.5 hover:shadow-md"
                :class="
                  route.path === '/'
                    ? 'border border-rose-500 bg-rose-500 text-white shadow-lg shadow-rose-200'
                    : 'border border-gray-100 bg-white text-gray-500 shadow-sm hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600'
                "
                @click="handleNavClick"
              >
                <div class="flex items-center gap-3">
                  <span
                    class="flex h-10 w-10 items-center justify-center rounded-full border-2 border-rose-300 bg-white text-rose-500"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="2"
                      stroke="currentColor"
                      class="h-5 w-5"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M12 6v12m6-6H6"
                      />
                    </svg>
                  </span>
                  <span class="text-base font-semibold">新計畫案啓動</span>
                </div>
              </NuxtLink>

              <NuxtLink
                to="/plan-library"
                class="flex items-center justify-between rounded-2xl px-5 py-4 transition"
                :class="
                  route.path.startsWith('/plan-library')
                    ? 'border border-rose-500 bg-rose-500 text-white shadow-lg shadow-rose-200'
                    : 'border border-gray-100 bg-white text-gray-500 shadow-sm hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600'
                "
                @click.native="handleNavClick"
              >
                <div class="flex items-center gap-3">
                  <span
                    class="flex h-10 w-10 items-center justify-center rounded-full bg-gray-50 text-gray-400"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="1.5"
                      stroke="currentColor"
                      class="h-6 w-6"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M3 7h5l2 2h11v8a2 2 0 01-2 2H4a2 2 0 01-2-2V9a2 2 0 012-2z"
                      />
                    </svg>
                  </span>
                  <span class="text-base font-medium">我的計畫庫</span>
                </div>
              </NuxtLink>

              <NuxtLink
                to="/command-library"
                class="flex items-center justify-between rounded-2xl px-5 py-4 transition"
                :class="
                  route.path.startsWith('/command-library')
                    ? 'border border-rose-500 bg-rose-500 text-white shadow-lg shadow-rose-200'
                    : 'border border-gray-100 bg-white text-gray-500 shadow-sm hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600'
                "
                @click.native="handleNavClick"
              >
                <div class="flex items-center gap-3">
                  <span
                    class="flex h-10 w-10 items-center justify-center rounded-full bg-gray-50 text-gray-400"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="1.5"
                      stroke="currentColor"
                      class="h-6 w-6"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M7 5h10a2 2 0 012 2v12l-7-3-7 3V7a2 2 0 012-2z"
                      />
                    </svg>
                  </span>
                  <span class="text-base font-medium">我的指令庫</span>
                </div>
              </NuxtLink>
            </div>

            <div v-else class="space-y-2">
              <p class="text-xs uppercase tracking-wide text-gray-400 px-1">
                內部作業
              </p>
              <NuxtLink
                to="/_builder/model"
                class="flex items-center gap-3 rounded-xl px-4 py-3 text-gray-600 transition hover:bg-gray-900 hover:text-white"
                active-class="bg-gray-900 text-white shadow-md"
                @click.native="handleNavClick"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    d="M5 4a1 1 0 00-2 0v7.268a2 2 0 000 3.464V16a1 1 0 102 0v-1.268a2 2 0 000-3.464V4zM11 4a1 1 0 10-2 0v1.268a2 2 0 000 3.464V16a1 1 0 102 0V8.732a2 2 0 000-3.464V4zM16 3a1 1 0 011 1v7.268a2 2 0 010 3.464V16a1 1 0 11-2 0v-1.268a2 2 0 010-3.464V4a1 1 0 011-1z"
                  />
                </svg>
                <span>模型配置</span>
              </NuxtLink>

              <NuxtLink
                to="/_builder/dataset"
                class="flex items-center gap-3 rounded-xl px-4 py-3 text-gray-600 transition hover:bg-gray-900 hover:text-white"
                active-class="bg-gray-900 text-white shadow-md"
                @click.native="handleNavClick"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                  />
                </svg>
                <span>資料集更新</span>
              </NuxtLink>

              <NuxtLink
                to="/_builder/management"
                class="flex items-center gap-3 rounded-xl px-4 py-3 text-gray-600 transition hover:bg-gray-900 hover:text-white"
                active-class="bg-gray-900 text-white shadow-md"
                @click.native="handleNavClick"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                  />
                </svg>
                <span>數據庫更新</span>
              </NuxtLink>

              <NuxtLink
                to="/_builder/section"
                class="flex items-center gap-3 rounded-xl px-4 py-3 text-gray-600 transition hover:bg-gray-900 hover:text-white"
                active-class="bg-gray-900 text-white shadow-md"
                @click.native="handleNavClick"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    d="M5.5 13a3.5 3.5 0 01-.369-6.98 4 4 0 117.753-1.3A4.5 4.5 0 1113.5 13H11V9.413l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13H5.5z"
                  />
                </svg>
                <span>動態欄位配置</span>
              </NuxtLink>
            </div>
          </template>

          <div v-else class="space-y-3">
            <NuxtLink
              to="/login"
              class="flex items-center gap-3 rounded-2xl px-5 py-3 transition border border-gray-100 bg-white text-gray-500 shadow-sm hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600"
              active-class="border border-rose-500 bg-rose-500 text-rose-500 shadow-lg shadow-rose-200"
              @click.native="handleNavClick"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M3 3a1 1 0 011 1v12a1 1 0 11-2 0V4a1 1 0 011-1h12a1 1 0 110 2H4v12a1 1 0 11-2 0V4a1 1 0 011-1z"
                  clip-rule="evenodd"
                />
              </svg>
              <span class="font-medium">登入</span>
            </NuxtLink>
          </div>
        </nav>

        <div v-if="isAuthenticated" class="mt-6 space-y-3">
          <div
            v-if="userEmail"
            class="px-4 py-3 rounded-2xl bg-gray-100 border border-gray-200"
          >
            <p class="text-xs text-gray-500 uppercase tracking-wide">
              使用者帳號
            </p>
            <p class="text-sm font-semibold text-gray-900 mt-1 break-all">
              {{ userEmail }}
            </p>
          </div>

          <button
            v-if="!isInternalView && isInternal"
            class="w-full rounded-2xl bg-gray-900 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            @click="switchToInternalView"
          >
            進入調整參數界面
          </button>
          <button
            v-else-if="isInternalView && isInternal"
            class="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm font-semibold text-gray-700 transition hover:-translate-y-0.5 hover:border-gray-300"
            @click="switchToExternalView"
          >
            返回企劃填寫界面
          </button>

          <button
            class="w-full rounded-2xl border border-rose-100 bg-white px-4 py-3 text-sm font-semibold text-rose-600 shadow-sm transition hover:bg-rose-50"
            @click="handleLogout"
          >
            登出
          </button>
        </div>
      </div>
    </aside>

    <main class="flex-1 overflow-y-auto min-h-screen">
      <slot />
    </main>
  </div>
</template>
<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
import { supabase } from "~/utils/supabaseClient";
import { useCurrentUser } from "~/composables/useCurrentUser";

const router = useRouter();
const route = useRoute();

// UI 狀態
const showSidebar = ref(false);
const isAuthenticated = ref(false);
const isInternal = ref(false); // 權限：是否為內部人員
const userTotalCost = ref(0);

// 計算屬性或 Watcher 來決定顯示哪種側邊欄
// 這樣可以確保"側邊欄"永遠跟"當前網址"是對應的
const isInternalView = ref(false);

// 監聽路由變化，自動切換側邊欄狀態
watch(
  () => route.path,
  (newPath) => {
    // 如果路徑以 /_builder 開頭，且使用者有權限，則顯示內部視圖
    if (newPath.startsWith("/_builder") && isInternal.value) {
      isInternalView.value = true;
    } else {
      isInternalView.value = false;
    }
  },
  { immediate: true }
);

const { userId: currentUserId, refreshUser } = useCurrentUser();
const userEmail = ref("");
let authSubscription = null;

// 配置
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

// 處理側邊欄點擊 (移動端關閉菜單)
function handleNavClick() {
  if (typeof window !== "undefined" && window.innerWidth < 768) {
    showSidebar.value = false;
  }
}

// 切換視圖功能：只負責跳轉路由，剩下的交給上面的 watch 處理
async function switchToInternalView() {
  await router.push("/_builder/model");
  handleNavClick();
}

async function switchToExternalView() {
  await router.push("/");
  handleNavClick();
}

// 獲取用量
async function fetchUserUsage(targetUserId) {
  if (!targetUserId) {
    userTotalCost.value = null;
    return;
  }
  try {
    const response = await fetch(
      `${API_BASE_URL}/user-usage?user_id=${targetUserId}`
    );
    if (!response.ok) throw new Error("Failed to fetch usage");
    const data = await response.json();
    userTotalCost.value = Number(data.usage).toFixed(2);
  } catch (e) {
    userTotalCost.value = null;
  }
}

// 登出
async function handleLogout() {
  try {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;

    // 狀態重置
    isAuthenticated.value = false;
    isInternalView.value = false;
    currentUserId.value = null;
    userTotalCost.value = null;
    localStorage.clear();

    await router.push("/login");
    handleNavClick();
  } catch (error) {
    console.error("Logout error:", error);
  }
}

// 初始化與監聽
onMounted(async () => {
  refreshUser();

  // 1. 獲取初始 Session
  const {
    data: { session },
  } = await supabase.auth.getSession();
  await handleSessionUpdate(session);

  // 2. 監聽 Auth 變化 (包含切換 Tab 時的 Session Refresh)
  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange((event, session) => {
    handleSessionUpdate(session);
  });
  authSubscription = subscription;
});

// 統一處理 Session 邏輯
async function handleSessionUpdate(session) {
  const sessionUserId = session?.user?.id ?? null;
  currentUserId.value = sessionUserId;
  isAuthenticated.value = !!sessionUserId;
  userEmail.value = session?.user?.email ?? "";

  if (!isAuthenticated.value) {
    isInternal.value = false;
    userTotalCost.value = null;
    userEmail.value = "";
    return;
  }

  // 獲取用量
  fetchUserUsage(sessionUserId);

  // 檢查內部權限
  const { checkIsInternal } = useInternalCheck();
  isInternal.value = await checkIsInternal();

  // 強制檢查一次路由狀態，確保 isInternalView 正確
  if (route.path.startsWith("/_builder") && isInternal.value) {
    isInternalView.value = true;
  } else {
    isInternalView.value = false;
  }
}

onBeforeUnmount(() => {
  authSubscription?.unsubscribe();
});
</script>
