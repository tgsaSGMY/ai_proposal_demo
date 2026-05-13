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
        <!--
          側邊欄頂端：品牌 logo + 收合切換按鈕
          - 展開模式：logo 與切換按鈕並排（logo 左，按鈕右）
          - 收合模式：logo 置中，下方顯示切換按鈕（icon-only rail）
          切換按鈕僅在 md+ 顯示，移動端使用既有的 showSidebar 開關。
        -->
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
              v-if="isInternal && !isSidebarCollapsed"
              class="mt-2 text-[11px] uppercase tracking-wide text-gray-400"
            >
              内部人員版本
            </p>
          </div>

        </div>

        <div class="flex-1" />

        <div v-if="isAuthenticated" class="mt-6 space-y-3">
          <!-- 使用者帳號卡：收合模式下隱藏（icon-only rail 上沒有意義） -->
          <div
            v-if="userEmail && !isSidebarCollapsed"
            class="px-4 py-3 rounded-2xl bg-gray-100 border border-gray-200"
          >
            <p class="text-xs text-gray-500 uppercase tracking-wide">
              使用者帳號
            </p>
            <p class="text-sm font-semibold text-gray-900 mt-1 break-all">
              {{ userEmail }}
            </p>
          </div>

          <!-- 登出：收合時顯示登出 icon -->
          <button
            class="rounded-2xl border border-rose-100 bg-white text-sm font-semibold text-rose-600 shadow-sm transition hover:bg-rose-50"
            :class="
              isSidebarCollapsed
                ? 'flex h-10 w-full items-center justify-center'
                : 'w-full px-4 py-3'
            "
            title="返回 TGSA 平台首頁"
            @click="handleLogout"
          >
            <Icon
              v-if="isSidebarCollapsed"
              name="tabler:logout"
              class="h-5 w-5"
            />
            <span v-else>返回 TGSA 平台首頁</span>
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
// ===== 导入依赖库 =====
// 导入 Vue 核心库和相关函数
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
import {
  appLogout,
  authenticatedFetch,
  getAppSession,
} from "~/composables/useAppAuth";
import { supabase } from "~/utils/supabaseClient";
// 导入自定义组合式函数
import { useCurrentUser } from "~/composables/useCurrentUser";

// ===== 路由和初始化 =====
// 获取 Vue Router 实例
const router = useRouter();
const route = useRoute();

// ===== UI 状态管理 =====
// 移动设备上侧边栏的显示/隐藏状态
const showSidebar = ref(false);
// 桌面端：侧边栏是否处于收合（icon-only）状态。仅在 md+ 生效，移动端无影响。
// 状态会持久化到 localStorage（key: tgsa.sidebarCollapsed），重新整理後仍保留。
const isSidebarCollapsed = ref(false);
const SIDEBAR_COLLAPSED_KEY = "tgsa.sidebarCollapsed";

function toggleSidebarCollapsed() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
}

// 用户是否已认证
const isAuthenticated = ref(false);
// 权限：是否为内部人员
const isInternal = ref(false);
// 用户的总消费成本
const userTotalCost = ref(0);

// ===== 侧边栏收合状态持久化 =====
// 任何收合/展开操作都会同步写入 localStorage，使下次进入时保持上次的偏好。
watch(isSidebarCollapsed, (collapsed) => {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? "1" : "0");
  } catch (err) {
    console.warn("Failed to persist sidebar collapse state", err);
  }
});

// ===== 用户信息管理 =====
// 获取当前用户 ID 和刷新函数
const { userId: currentUserId, refreshUser } = useCurrentUser();
// 当前用户的电子邮件地址
const userEmail = ref("");
// 认证变化的订阅对象
let authSubscription = null;

// ===== API 配置 =====
// 获取运行时配置
const config = useRuntimeConfig();
// API 基础 URL
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
const TGSA_PLATFORM_HOME_URL =
  config.public.platformHomeUrl || "https://portal.tgsaapp.com/";

// ===== 事件处理函数 =====
// 处理侧边栏点击 (移动端关闭菜单)
function handleNavClick() {
  // 在移动设备上，点击菜单项后自动关闭侧边栏
  if (typeof window !== "undefined" && window.innerWidth < 768) {
    showSidebar.value = false;
  }
}

// ===== 用户成本/使用量管理 =====
// 获取指定用户的成本和使用量信息
// 参数: targetUserId - 要查询的用户 ID
async function fetchUserUsage(targetUserId) {
  // 如果没有提供用户 ID，则将使用量设为 null
  if (!targetUserId) {
    userTotalCost.value = null;
    return;
  }

  try {
    // 调用 API 获取用户成本信息
    const response = await authenticatedFetch(
      `${API_BASE_URL}/user-usage?user_id=${targetUserId}`,
    );
    // 如果响应失败，抛出错误
    if (!response.ok) throw new Error("Failed to fetch usage");
    const data = await response.json();
    // 将成本保存到状态，格式化为 2 位小数
    userTotalCost.value = Number(data.usage).toFixed(2);
  } catch (e) {
    // 如果出错，将使用量设为 null
    userTotalCost.value = null;
  }
}

// ===== 用户登出功能 =====
// 处理用户登出：清除认证状态，清理本地存储，重定向到登录页面
async function handleLogout() {
  try {
    await appLogout({ redirectTo: TGSA_PLATFORM_HOME_URL });
  } catch (error) {
    // 登出失败时打印错误信息
    console.error("Logout error:", error);
  }
}

// ===== 组件生命周期和初始化 =====
// 组件挂载时的初始化逻辑
// 在这里获取用户会话、检查权限、设置认证监听器
onMounted(async () => {
  // 从 localStorage 读取 sidebar 收合状态（仅在 client 端执行，避免 SSR 不一致）
  if (typeof window !== "undefined") {
    try {
      const stored = window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
      if (stored === "1") {
        isSidebarCollapsed.value = true;
      }
    } catch (err) {
      // localStorage 在隐私模式下可能抛错，忽略即可
      console.warn("Failed to read sidebar collapse state", err);
    }
  }

  // 刷新用户信息缓存
  refreshUser();

  // 第 1 步：获取初始的认证会话
  const appSession = await getAppSession();
  // 使用会话信息更新本地状态
  await handleSessionUpdate(appSession);

  // 第 2 步：监听认证状态变化（包括用户切换标签页时的会话刷新）
  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange(() => {
    void (async () => {
      const latest = await getAppSession();
      await handleSessionUpdate(latest);
    })();
  });
  // 保存订阅对象以便在组件卸载时取消订阅
  authSubscription = subscription;
});

// ===== 处理会话状态更新 =====
// 统一处理所有与 Supabase 会话相关的状态逻辑
// 参数: session - Supabase 会话对象（可能为 null）
async function handleSessionUpdate(appSession) {
  // 和 middleware 保持一致：有 session 且有 user 才算已登入。
  isAuthenticated.value = appSession?.isAuthenticated === true;
  // 先放入 session email；稍後會用 /auth/me（users table）覆寫成 canonical email。
  userEmail.value = "";

  // 如果用户未认证，清除所有相关权限和数据
  if (!isAuthenticated.value) {
    isInternal.value = false;
    userTotalCost.value = null;
    userEmail.value = "";
    return;
  }

  let canonicalUserId = null;
  try {
    // 统一从后端 /auth/me 获取 canonical user（来源为 users table）。
    const meResponse = await authenticatedFetch(`${API_BASE_URL}/auth/me`);

    if (meResponse.ok) {
      const me = await meResponse.json();
      canonicalUserId = me?.id ?? null;
      currentUserId.value = canonicalUserId;
      userEmail.value = me?.email ?? userEmail.value;
      isInternal.value = me?.role === "internal";
    } else {
      // /auth/me 暫時失敗時，回退到既有流程。
      canonicalUserId = await refreshUser();
      currentUserId.value = canonicalUserId;
      const { checkIsInternal } = useInternalCheck();
      isInternal.value = await checkIsInternal();
    }
  } catch (error) {
    console.error("Failed to load canonical user profile", error);
    canonicalUserId = await refreshUser();
    currentUserId.value = canonicalUserId;
    const { checkIsInternal } = useInternalCheck();
    isInternal.value = await checkIsInternal();
  }

  // 对于已认证的用户：获取成本/使用量信息
  if (canonicalUserId) {
    fetchUserUsage(canonicalUserId);
  }

}

// ===== 组件卸载清理 =====
// 组件卸载前执行清理操作，防止内存泄漏
onBeforeUnmount(() => {
  // 取消 Supabase 认证状态变化的监听器订阅
  authSubscription?.unsubscribe();
});
</script>
