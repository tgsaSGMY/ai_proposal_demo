<template>
  <div class="min-h-screen bg-gray-100 font-sans flex flex-col md:flex-row">
    <!-- Mobile nav -->
    <header
      class="md:hidden bg-gray-800 text-white flex items-center justify-between px-4 sticky top-0 z-40"
    >
      <div class="font-semibold text-lg">
        AI 計畫書平台 <span class="text-xs text-gray-400 align-top">v0.1</span>
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

    <!-- 側邊欄 -->
    <aside
      :class="[
        showSidebar ? 'block' : 'hidden',
        'md:block md:flex',
        'w-full md:w-64 flex-shrink-0 bg-gray-800 text-white flex flex-col p-0 md:p-4',
        showSidebar
          ? 'fixed top-0 left-0 h-full z-50 overflow-y-auto md:static md:h-screen md:overflow-y-auto md:z-30'
          : '',
        !showSidebar
          ? 'md:sticky md:top-0 md:h-screen md:overflow-y-auto md:z-30'
          : '',
      ]"
      style="max-width: 100vw"
    >
      <!-- mobile sticky nav bar -->
      <div
        v-if="showSidebar"
        class="md:hidden sticky top-0 bg-gray-800 z-50 flex items-center justify-between px-4 py-3 border-b border-gray-700"
      >
        <div class="font-semibold text-lg">
          AI 計畫書平台
          <span class="text-xs text-gray-400 align-top">v0.1</span>
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
      <div class="text-center py-4 mb-6 hidden md:block">
        <h2 class="text-xl font-semibold">AI 計畫書平台</h2>
        <span class="text-xs text-gray-400">v0.1</span>
      </div>
      <nav class="flex-grow flex-1">
        <ul>
          <li>
            <NuxtLink
              v-if="isAuthenticated"
              to="/"
              class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700"
              active-class="bg-indigo-600 text-white"
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
                  d="M11.3 1.046A1 1 0 0112 2v1.999l4.763 4.763a1 1 0 01-1.414 1.414l-4.763-4.763V14a1 1 0 11-2 0V5.414L3.65 10.177a1 1 0 01-1.414-1.414L6.999 4V2a1 1 0 011.046-1.046.998.998 0 011.208.044l.046.046zM10 16a1 1 0 100 2 1 1 0 000-2z"
                  clip-rule="evenodd"
                />
              </svg>
              <span>計畫書生成</span>
            </NuxtLink>
          </li>
          <li v-if="isAuthenticated" class="mt-2">
            <NuxtLink
              to="/_builder/model"
              class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700"
              active-class="bg-indigo-600 text-white"
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
          </li>
          <li v-if="isAuthenticated" class="mt-2">
            <NuxtLink
              to="/_builder/dataset"
              class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700"
              active-class="bg-indigo-600 text-white"
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
          </li>
          <li v-if="isAuthenticated" class="mt-2">
            <NuxtLink
              to="/_builder/management"
              class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700"
              active-class="bg-indigo-600 text-white"
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
              <span>數據庫管理</span>
            </NuxtLink>
          </li>
          <li v-if="!isAuthenticated" class="mt-2">
            <NuxtLink
              to="/login"
              class="flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700 text-indigo-300 hover:text-white"
              active-class="bg-indigo-600 text-white"
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
              <span>登入</span>
            </NuxtLink>
          </li>
          <li v-if="isAuthenticated" class="mt-2">
            <button
              @click="handleLogout"
              class="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors duration-200 hover:bg-red-700 text-red-300 hover:text-white text-left"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M3 3a1 1 0 00-1 1v12a1 1 0 001 1h12a1 1 0 001-1V4a1 1 0 00-1-1H3zm11 4.414l-4.293 4.293a1 1 0 001.414 1.414L15.414 9l-4.293-4.293a1 1 0 00-1.414 1.414L13.586 7H6a1 1 0 000 2h7.586l-1.293 1.293a1 1 0 001.414 1.414l4.293-4.293V8z"
                  clip-rule="evenodd"
                />
              </svg>
              <span>登出</span>
            </button>
          </li>
        </ul>
      </nav>
      <!-- Cost 區塊移至側邊欄底部 -->
      <div class="mt-auto mb-4 px-4">
        <div
          class="bg-indigo-600/90 rounded-xl shadow-lg flex items-center gap-3 py-3 px-4 text-white"
        >
          <svg
            fill="#ffffff"
            viewBox="-5 0 19 19"
            xmlns="http://www.w3.org/2000/svg"
            class="cf-icon-svg h-6 w-6"
            stroke="#ffffff"
          >
            <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
            <g
              id="SVGRepo_tracerCarrier"
              stroke-linecap="round"
              stroke-linejoin="round"
            ></g>
            <g id="SVGRepo_iconCarrier">
              <path
                d="M8.699 11.907a3.005 3.005 0 0 1-1.503 2.578 4.903 4.903 0 0 1-1.651.663V16.3a1.03 1.03 0 1 1-2.059 0v-1.141l-.063-.011a5.199 5.199 0 0 1-1.064-.325 3.414 3.414 0 0 1-1.311-.962 1.029 1.029 0 1 1 1.556-1.347 1.39 1.39 0 0 0 .52.397l.002.001a3.367 3.367 0 0 0 .648.208h.002a4.964 4.964 0 0 0 .695.084 3.132 3.132 0 0 0 1.605-.445c.5-.325.564-.625.564-.851a1.005 1.005 0 0 0-.245-.65 2.06 2.06 0 0 0-.55-.44 2.705 2.705 0 0 0-.664-.24 3.107 3.107 0 0 0-.65-.066 6.046 6.046 0 0 1-1.008-.08 4.578 4.578 0 0 1-1.287-.415A3.708 3.708 0 0 1 1.02 9.04a3.115 3.115 0 0 1-.718-1.954 2.965 2.965 0 0 1 .321-1.333 3.407 3.407 0 0 1 1.253-1.335 4.872 4.872 0 0 1 1.611-.631V2.674a1.03 1.03 0 1 1 2.059 0v1.144l.063.014h.002a5.464 5.464 0 0 1 1.075.368 3.963 3.963 0 0 1 1.157.795A1.03 1.03 0 0 1 6.39 6.453a1.901 1.901 0 0 0-.549-.376 3.516 3.516 0 0 0-.669-.234l-.066-.014a3.183 3.183 0 0 0-.558-.093 3.062 3.062 0 0 0-1.572.422 1.102 1.102 0 0 0-.615.928 1.086 1.086 0 0 0 .256.654l.002.003a1.679 1.679 0 0 0 .537.43l.002.002a2.57 2.57 0 0 0 .703.225h.002a4.012 4.012 0 0 0 .668.053 5.165 5.165 0 0 1 1.087.112l.003.001a4.804 4.804 0 0 1 1.182.428l.004.002a4.115 4.115 0 0 1 1.138.906l.002.002a3.05 3.05 0 0 1 .753 2.003z"
              ></path>
            </g>
          </svg>
          <!-- <div class="flex flex-col">
            <span class="text-xs text-gray-200">花費（預計）</span>
            <span class="text-lg font-bold tracking-wide"
              >${{ userTotalCost }}</span
            >
          </div> -->
        </div>
      </div>
    </aside>

    <!-- 主内容區 -->
    <main
      class="flex-1 overflow-y-auto min-h-screen px-2 py-4 sm:px-4 md:px-8 lg:px-12 xl:px-16"
    >
      <slot />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { supabase } from "~/utils/supabaseClient";

const showSidebar = ref(false);
const isAuthenticated = ref(false);

function handleNavClick() {
  if (window.innerWidth < 768) {
    showSidebar.value = false;
  }
}

// 檢查認證狀態
async function checkAuth() {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    isAuthenticated.value = !!session?.user;
  } catch (error) {
    console.error("Auth check error:", error);
    isAuthenticated.value = false;
  }
}

// 登出功能
async function handleLogout() {
  try {
    await supabase.auth.signOut();
    isAuthenticated.value = false;
    await useRouter().push("/login");
  } catch (error) {
    console.error("Logout error:", error);
  }
}

onMounted(() => {
  checkAuth();

  // 監聽認證狀態變化
  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange((event, session) => {
    isAuthenticated.value = !!session?.user;
  });
});

// 用戶總 cost 狀態
const userTotalCost = ref(0);
const userId = "dba4dabc-a24d-4e1a-aa2b-b239d06a8cf5";
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
async function fetchUserUsage() {
  try {
    const response = await fetch(
      `${API_BASE_URL}/user-usage?user_id=${userId}`
    );
    if (!response.ok) throw new Error("Failed to fetch usage");
    const data = await response.json();
    userTotalCost.value = Number(data.usage).toFixed(2);
  } catch (e) {
    userTotalCost.value = null;
  }
}
onMounted(fetchUserUsage);
</script>
