<template>
  <ClientOnly>
    <div class="flex items-center justify-center p-4 sm:p-6 min-h-screen">
      <div class="w-full max-w-md">
        <!-- 卡片容器 -->
        <div class="bg-white rounded-2xl shadow-2xl overflow-hidden">
          <!-- 頂部區塊（漸層背景） -->
          <div
            class="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 sm:px-8 py-8 sm:py-10"
          >
            <h1 class="text-3xl sm:text-4xl font-bold text-white mb-2">
              重設密碼
            </h1>
            <p class="text-indigo-100 text-sm sm:text-base">
              輸入您的電子郵件，我們將發送重設密碼的鏈接
            </p>
          </div>

          <!-- 表單區塊 -->
          <form
            @submit.prevent="handleForgotPassword"
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

            <!-- 成功訊息 -->
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
                v-if="successMessage"
                class="p-4 bg-green-50 border-l-4 border-green-500 rounded text-green-700 text-sm"
              >
                <div class="flex items-start gap-2">
                  <svg
                    class="w-5 h-5 flex-shrink-0 mt-0.5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clip-rule="evenodd"
                    />
                  </svg>
                  <span>{{ successMessage }}</span>
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
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
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
              {{ isLoading ? "發送中..." : "發送重設鏈接" }}
            </button>
          </form>

          <!-- 頁腳區塊 -->
          <div
            class="bg-gray-50 px-6 sm:px-8 py-6 text-center border-t border-gray-100"
          >
            <p class="text-gray-600 text-sm">
              記起密碼了？
              <NuxtLink
                to="/_builder/login"
                class="text-indigo-600 font-semibold hover:text-indigo-700 hover:underline transition"
              >
                返回登入
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
// 引入 Supabase：用於發送重設郵件以及處理與驗證相關的操作

definePageMeta({
  middleware: "redirect-if-authenticated",
});

// 表單欄位與 UI 狀態
const email = ref(""); // 使用者輸入的電子郵件
const errorMessage = ref(""); // 錯誤訊息顯示
const successMessage = ref(""); // 成功訊息顯示
const isLoading = ref(false); // 請求中狀態

/**
 * handleForgotPassword - 處理發送重設密碼郵件
 * 步驟：
 *  1) 驗證是否輸入郵件
 *  2) 呼叫 supabase.auth.resetPasswordForEmail 發送重設鏈接
 *  3) 根據錯誤類型顯示友善提示
 */
const handleForgotPassword = async () => {
  if (!email.value) {
    errorMessage.value = "請輸入電子郵件";
    return;
  }

  isLoading.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    const { error } = await supabase.auth.resetPasswordForEmail(email.value, {
      redirectTo: `${window.location.origin}/_builder/reset-password`,
    });

    if (error) {
      console.error("Password reset error:", error);
      if (error.message.includes("User not found")) {
        errorMessage.value = "此電子郵件帳戶不存在";
      } else {
        errorMessage.value = `發送失敗：${error.message}`;
      }
    } else {
      successMessage.value = "重設密碼鏈接已發送到您的電子郵件，請檢查收件箱";
      email.value = "";
    }
  } catch (err) {
    errorMessage.value = "發生錯誤，請稍後重試";
    console.error("Forgot password error:", err);
  } finally {
    isLoading.value = false;
  }
};
</script>
