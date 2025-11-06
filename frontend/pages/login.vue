<template>
  <div class="flex items-center justify-center p-4 sm:p-6">
    <div class="w-full max-w-md">
      <!-- Card Container -->
      <div class="bg-white rounded-2xl shadow-2xl overflow-hidden">
        <!-- Header Section with Gradient -->
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

        <!-- Form Section -->
        <form
          @submit.prevent="handleLogin"
          class="px-6 sm:px-8 py-8 sm:py-10 space-y-6"
        >
          <!-- Email Input -->
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
              required
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition duration-200 text-gray-900 placeholder-gray-400"
            />
          </div>

          <!-- Password Input -->
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
              required
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition duration-200 text-gray-900 placeholder-gray-400"
            />
          </div>

          <!-- Error Message -->
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

          <!-- Submit Button -->
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

        <!-- Footer Section -->
        <div
          class="bg-gray-50 px-6 sm:px-8 py-6 text-center border-t border-gray-100"
        >
          <p class="text-gray-600 text-sm">
            沒有帳戶？
            <NuxtLink
              to="/"
              class="text-indigo-600 font-semibold hover:text-indigo-700 hover:underline transition"
            >
              返回首頁
            </NuxtLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { supabase } from "~/utils/supabaseClient";

const router = useRouter();

const email = ref("");
const password = ref("");
const errorMessage = ref("");
const isLoading = ref(false);

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
      errorMessage.value = "登入失敗，請檢查您的帳戶信息";
    } else {
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
