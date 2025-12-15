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
          <div
            class="h-11 w-11 rounded-2xl bg-rose-500 text-white flex items-center justify-center shadow-lg"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              class="h-6 w-6"
            >
              <path
                d="M12.672 5.266a1 1 0 00-1.344 0c-.749.681-2.35 2.263-3.356 4.383-1.012 2.13-1.415 4.512-.63 6.84a1 1 0 001.593.47l1.348-1.122a1 1 0 011.278 0l1.348 1.122a1 1 0 001.593-.47c.785-2.328.382-4.71-.63-6.84-1.007-2.12-2.608-3.702-3.356-4.383z"
              />
            </svg>
          </div>
          <div>
            <p class="text-lg font-semibold text-gray-900">TGSA企劃引擎</p>
            <p class="text-xs uppercase tracking-wide text-gray-400">
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
                @click.native="handleNavClick"
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
            </div>
          </template>

          <div v-else class="space-y-3">
            <NuxtLink
              to="/login"
              class="flex items-center gap-3 rounded-2xl border border-indigo-100 bg-white px-5 py-3 text-indigo-500 shadow-sm transition hover:bg-indigo-50"
              active-class="bg-indigo-500 text-white border-indigo-500"
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
          </div>
        </nav>

        <div v-if="isAuthenticated" class="mt-6 space-y-3">
          <button
            v-if="!isInternalView"
            class="w-full rounded-2xl bg-gray-900 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            @click="switchToInternalView"
          >
            進入內部人員版本
          </button>
          <button
            v-else
            class="w-full rounded-2xl border border-gray-200 px-4 py-3 text-sm font-semibold text-gray-700 transition hover:-translate-y-0.5 hover:border-gray-300"
            @click="switchToExternalView"
          >
            返回外部人員版本
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
import { ref, onMounted, onBeforeUnmount } from "vue";
import { supabase } from "~/utils/supabaseClient";

const router = useRouter();
const route = useRoute();
const showSidebar = ref(false);
const isAuthenticated = ref(false);
const isInternalView = ref(false);

let authSubscription = null;

function handleNavClick() {
  if (typeof window !== "undefined" && window.innerWidth < 768) {
    showSidebar.value = false;
  }
}

async function switchToInternalView() {
  isInternalView.value = true;
  await router.push("/_builder/model");
  handleNavClick();
}

async function switchToExternalView() {
  isInternalView.value = false;
  await router.push("/");
  handleNavClick();
}

async function checkAuth() {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    isAuthenticated.value = !!session?.user;
    if (!isAuthenticated.value) {
      isInternalView.value = false;
    }
  } catch (error) {
    console.error("Auth check error:", error);
    isAuthenticated.value = false;
  }
}

async function handleLogout() {
  try {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    isAuthenticated.value = false;
    isInternalView.value = false;
    localStorage.clear();
    await router.push("/login");
    handleNavClick();
  } catch (error) {
    console.error("Logout error:", error);
  }
}

onMounted(() => {
  checkAuth();
  fetchUserUsage();
  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange((event, session) => {
    isAuthenticated.value = !!session?.user;
    if (!isAuthenticated.value) {
      isInternalView.value = false;
    }
  });
  authSubscription = subscription;
});

onBeforeUnmount(() => {
  authSubscription?.unsubscribe();
});

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
</script>
