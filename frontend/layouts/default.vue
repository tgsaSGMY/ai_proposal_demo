<template>
  <div class="min-h-screen bg-gray-50 font-sans flex flex-col md:flex-row">
    <header
      class="md:hidden bg-white text-gray-900 flex items-center justify-between px-4 py-3 border-b border-gray-200 sticky top-0 z-40"
    >
      <div class="font-semibold text-lg">
        TGSA補助引擎
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
          TGSA補助引擎
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
              alt="TGSA 補助引擎"
              class="h-full w-full object-cover"
            />
          </div>

          <div>
            <p class="text-lg font-semibold text-gray-900">TGSA補助引擎</p>
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

              <NuxtLink
                to="/_builder/template-manager"
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
                    d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4z"
                  />
                </svg>
                <span>主題與模板管理</span>
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
// ===== 导入依赖库 =====
// 导入 Vue 核心库和相关函数
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
// 导入 Supabase 认证服务
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
// 用户是否已认证
const isAuthenticated = ref(false);
// 权限：是否为内部人员
const isInternal = ref(false);
// 用户的总消费成本
const userTotalCost = ref(0);

// ===== 视图切换状态 =====
// 计算属性或 Watcher 来决定显示哪种侧边栏
// 这样可以确保"侧边栏"永远跟"当前网址"是对应的
const isInternalView = ref(false);

// ===== 侦听器：路由变化 =====
// 监听路由变化，自动切换侧边栏状态
watch(
  () => route.path,
  (newPath) => {
    // 如果路径以 /_builder 开头，且用户有权限，则显示内部视图
    if (newPath.startsWith("/_builder") && isInternal.value) {
      isInternalView.value = true;
    } else {
      isInternalView.value = false;
    }
  },
  { immediate: true }
);

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

// ===== 事件处理函数 =====
// 处理侧边栏点击 (移动端关闭菜单)
function handleNavClick() {
  // 在移动设备上，点击菜单项后自动关闭侧边栏
  if (typeof window !== "undefined" && window.innerWidth < 768) {
    showSidebar.value = false;
  }
}

// ===== 视图切换功能 =====
// 切换到内部视图：跳转到内部管理员界面
// 管理员可以编辑方案模板、部分配置等
async function switchToInternalView() {
  // 跳转到内部管理员的模型编辑页面
  await router.push("/_builder/model");
  // 移动端上自动关闭侧边栏
  handleNavClick();
}

// 切换回外部视图：跳转到普通用户的首页
async function switchToExternalView() {
  // 跳转到外部用户的首页
  await router.push("/");
  // 移动端上自动关闭侧边栏
  handleNavClick();
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
    const response = await fetch(
      `${API_BASE_URL}/user-usage?user_id=${targetUserId}`
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
    // 调用 Supabase 的 signOut 方法进行登出
    const { error } = await supabase.auth.signOut();
    if (error) throw error;

    // 清除所有相关的用户状态信息
    isAuthenticated.value = false; // 标记为未认证
    isInternalView.value = false; // 切回外部视图
    currentUserId.value = null; // 清空用户 ID
    userTotalCost.value = null; // 清空用户成本
    localStorage.clear(); // 清空所有本地存储

    // 重定向到登录页面
    await router.push("/login");
    // 移动端上关闭侧边栏
    handleNavClick();
  } catch (error) {
    // 登出失败时打印错误信息
    console.error("Logout error:", error);
  }
}

// ===== 组件生命周期和初始化 =====
// 组件挂载时的初始化逻辑
// 在这里获取用户会话、检查权限、设置认证监听器
onMounted(async () => {
  // 刷新用户信息缓存
  refreshUser();

  // 第 1 步：获取初始的认证会话
  const {
    data: { session },
  } = await supabase.auth.getSession();
  // 使用会话信息更新本地状态
  await handleSessionUpdate(session);

  // 第 2 步：监听认证状态变化（包括用户切换标签页时的会话刷新）
  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange((event, session) => {
    // 当 Supabase 认证状态变化时，更新本地状态
    handleSessionUpdate(session);
  });
  // 保存订阅对象以便在组件卸载时取消订阅
  authSubscription = subscription;
});

// ===== 处理会话状态更新 =====
// 统一处理所有与 Supabase 会话相关的状态逻辑
// 参数: session - Supabase 会话对象（可能为 null）
async function handleSessionUpdate(session) {
  // 从会话中提取用户 ID（如果会话不存在则为 null）
  const sessionUserId = session?.user?.id ?? null;
  // 更新状态中的用户 ID
  currentUserId.value = sessionUserId;
  // 根据是否有用户 ID 来设置认证状态
  isAuthenticated.value = !!sessionUserId;
  // 更新用户邮箱（如果会话不存在则为空字符串）
  userEmail.value = session?.user?.email ?? "";

  // 如果用户未认证，清除所有相关权限和数据
  if (!isAuthenticated.value) {
    isInternal.value = false;
    userTotalCost.value = null;
    userEmail.value = "";
    return;
  }

  // 对于已认证的用户：获取成本/使用量信息
  fetchUserUsage(sessionUserId);

  // 检查用户是否具有内部权限（管理员权限）
  const { checkIsInternal } = useInternalCheck();
  isInternal.value = await checkIsInternal();

  // 强制检查一次路由状态，确保 isInternalView 标志准确
  // 如果路由是 /_builder 开头且用户有权限，则显示内部视图
  // 否则显示外部用户视图
  if (route.path.startsWith("/_builder") && isInternal.value) {
    isInternalView.value = true;
  } else {
    isInternalView.value = false;
  }
}

// ===== 组件卸载清理 =====
// 组件卸载前执行清理操作，防止内存泄漏
onBeforeUnmount(() => {
  // 取消 Supabase 认证状态变化的监听器订阅
  authSubscription?.unsubscribe();
});
</script>
