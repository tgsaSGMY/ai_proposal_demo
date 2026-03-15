<template>
  <ClientOnly>
    <div class="flex items-center justify-center p-4 sm:p-6">
      <div class="w-full max-w-md">
        <!-- 卡片容器 -->
        <div class="bg-white rounded-2xl shadow-2xl overflow-hidden">
          <!-- 頂部區塊（漸層背景） -->
          <div
            class="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 sm:px-8 py-8 sm:py-10"
          >
            <h1 class="text-3xl sm:text-4xl font-bold text-white mb-2">
              歡迎回來
            </h1>
            <p class="text-indigo-100 text-sm sm:text-base">
              登入您的帳戶以訪問 AI 計畫書生成平台
            </p>
          </div>

          <!-- 表單區塊 -->
          <form
            @submit.prevent="handleLogin"
            class="px-6 sm:px-8 py-8 sm:py-10 space-y-6"
          >
            <!-- 電子郵件輸入 -->
            <div>
              <label
                for="email"
                class="block text-sm font-semibold text-gray-700 mb-2"
              >
                電子郵件
              </label>
              <input
                type="email"
                id="email"
                v-model="email"
                placeholder="your.email@example.com"
                autocomplete="email"
                required
                class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition duration-200 text-gray-900 placeholder-gray-400"
              />
            </div>

            <!-- 密碼輸入 -->
            <div>
              <label
                for="password"
                class="block text-sm font-semibold text-gray-700 mb-2"
              >
                密碼
              </label>
              <input
                type="password"
                id="password"
                v-model="password"
                placeholder="••••••••"
                autocomplete="current-password"
                required
                class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition duration-200 text-gray-900 placeholder-gray-400"
              />
              <div class="mt-2 text-right">
                <NuxtLink
                  to="/_builder/forgot-password"
                  class="text-sm text-indigo-600 hover:text-indigo-700 hover:underline transition"
                >
                  忘記密碼？
                </NuxtLink>
              </div>
            </div>

            <!-- 錯誤訊息 -->
            <Transition
              name="fade"
              enter-active-class="transition duration-200"
              leave-active-class="transition duration-200"
              enter-from-class="opacity-0 transform -translate-y-1"
              enter-to-class="opacity-100"
              leave-from-class="opacity-100"
              leave-to-class="opacity-0 transform -translate-y-1"
            >
              <div
                v-if="errorMessage"
                class="p-4 bg-red-50 border-l-4 border-red-500 rounded text-red-700 text-sm"
              >
                <div class="flex items-start gap-2">
                  <svg
                    class="w-5 h-5 flex-shrink-0 mt-0.5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clip-rule="evenodd"
                    />
                  </svg>
                  <span>{{ errorMessage }}</span>
                </div>
              </div>
            </Transition>

            <!-- 送出按鈕 -->
            <button
              type="submit"
              :disabled="isLoading"
              class="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold py-3 px-4 rounded-lg hover:shadow-lg hover:from-indigo-700 hover:to-purple-700 transition duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
            >
              <svg
                v-if="!isLoading"
                class="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v2a2 2 0 01-2 2H7a2 2 0 01-2-2v-2m14-4V7a2 2 0 00-2-2H7a2 2 0 00-2 2v2m14-4h-2.5A2.5 2.5 0 0016 5.5"
                />
              </svg>
              <svg
                v-else
                class="w-5 h-5 animate-spin"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                ></circle>
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              {{ isLoading ? "登入中..." : "登入" }}
            </button>
          </form>

          <div
            class="bg-gray-50 px-6 sm:px-8 py-6 text-center border-t border-gray-100"
          >
            <p class="text-gray-600 text-sm">
              尚未有內部帳號？
              <NuxtLink
                to="/_builder/signup"
                class="text-indigo-600 font-semibold hover:text-indigo-700 hover:underline transition"
              >
                前往註冊
              </NuxtLink>
            </p>
          </div>
        </div>
      </div>
    </div>
  </ClientOnly>
</template>

<script setup>
import { supabase } from "~/utils/supabaseClient";
import { authenticatedFetch } from "~/composables/useAppAuth";
// 引入 Supabase：處理登入驗證與錯誤回傳解析

definePageMeta({
  middleware: "redirect-if-authenticated",
});

useHead({
  title: "内部賬號登入 - TGSA 補助引擎",
});

// router 用於登入成功後導向
const router = useRouter();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

// 表單欄位與 UI 狀態說明
const email = ref(""); // 使用者輸入電子郵件
const password = ref(""); // 使用者輸入密碼
const errorMessage = ref(""); // 顯示錯誤訊息
const isLoading = ref(false); // 請求中狀態

/**
 * handleLogin - 處理使用者登入流程
 * 步驟：
 *  1) 檢查欄位是否填寫
 *  2) 呼叫 supabase.auth.signInWithPassword
 *  3) 根據回傳錯誤提供更友善的提示（如驗證未完成、帳號不存在等）
 */
const handleLogin = async () => {
  if (!email.value || !password.value) {
    errorMessage.value = "請輸入電子郵件和密碼";
    return;
  }

  isLoading.value = true;
  errorMessage.value = "";

  try {
    const { error } = await supabase.auth.signInWithPassword({
      email: email.value,
      password: password.value,
    });

    if (error) {
      // 根據錯誤類型提供更具體的提示
      if (error.message.includes("Invalid login credentials")) {
        errorMessage.value = "電子郵件或密碼不正確，請檢查後重試";
      } else if (error.message.includes("Email not confirmed")) {
        errorMessage.value = "帳戶尚未驗證，請檢查您的電子郵件並點擊驗證鏈接";
      } else if (error.message.includes("User not found")) {
        errorMessage.value = "此電子郵件帳戶不存在";
      } else {
        errorMessage.value = `登入失敗：${error.message}`;
      }
      console.error("Login error details:", error);
    } else {
      await authenticatedFetch(`${API_BASE_URL}/auth/me`);
      await router.push("/");
    }
  } catch (err) {
    errorMessage.value = "發生錯誤，請稍後重試";
    console.error("Login error:", err);
  } finally {
    isLoading.value = false;
  }
};
</script>
