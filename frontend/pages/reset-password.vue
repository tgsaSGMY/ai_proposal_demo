<template>
  <ClientOnly>
    <div class="flex items-center justify-center p-4 sm:p-6 min-h-screen">
      <div class="w-full max-w-md">
        <!-- Card Container -->
        <div class="bg-white rounded-2xl shadow-2xl overflow-hidden">
          <!-- Header Section with Gradient -->
          <div
            class="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 sm:px-8 py-8 sm:py-10"
          >
            <h1 class="text-3xl sm:text-4xl font-bold text-white mb-2">
              設定新密碼
            </h1>
            <p class="text-indigo-100 text-sm sm:text-base">請輸入您的新密碼</p>
          </div>

          <!-- Form Section -->
          <form
            v-if="sessionValid"
            @submit.prevent="handleResetPassword"
            class="px-6 sm:px-8 py-8 sm:py-10 space-y-6"
          >
            <!-- New Password Input -->
            <div>
              <label
                for="password"
                class="block text-sm font-semibold text-gray-700 mb-2"
              >
                新密碼
              </label>
              <div class="relative">
                <input
                  :type="showPassword ? 'text' : 'password'"
                  id="password"
                  v-model="password"
                  placeholder="••••••••"
                  autocomplete="new-password"
                  required
                  minlength="6"
                  class="w-full px-4 py-3 pr-12 border-2 border-gray-200 rounded-lg focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition duration-200 text-gray-900 placeholder-gray-400"
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition"
                  :aria-label="showPassword ? '隱藏密碼' : '顯示密碼'"
                >
                  <svg
                    v-if="showPassword"
                    class="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-4.803m5.596-3.856a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0M15 12a3 3 0 11-6 0 3 3 0 016 0zm6 0c0 1.657-.672 3.157-1.757 4.243A6 6 0 0121 12a6 6 0 00-9-5.657"
                    />
                  </svg>
                  <svg
                    v-else
                    class="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    />
                  </svg>
                </button>
              </div>
              <p class="text-xs text-gray-500 mt-2">密碼至少需要 6 個字符</p>
            </div>

            <!-- Confirm Password Input -->
            <div>
              <label
                for="confirmPassword"
                class="block text-sm font-semibold text-gray-700 mb-2"
              >
                確認密碼
              </label>
              <div class="relative">
                <input
                  :type="showConfirmPassword ? 'text' : 'password'"
                  id="confirmPassword"
                  v-model="confirmPassword"
                  placeholder="••••••••"
                  autocomplete="new-password"
                  required
                  minlength="6"
                  class="w-full px-4 py-3 pr-12 border-2 border-gray-200 rounded-lg focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200 transition duration-200 text-gray-900 placeholder-gray-400"
                />
                <button
                  type="button"
                  @click="showConfirmPassword = !showConfirmPassword"
                  class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition"
                  :aria-label="showConfirmPassword ? '隱藏密碼' : '顯示密碼'"
                >
                  <svg
                    v-if="showConfirmPassword"
                    class="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-4.803m5.596-3.856a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0M15 12a3 3 0 11-6 0 3 3 0 016 0zm6 0c0 1.657-.672 3.157-1.757 4.243A6 6 0 0121 12a6 6 0 00-9-5.657"
                    />
                  </svg>
                  <svg
                    v-else
                    class="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    />
                  </svg>
                </button>
              </div>
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

            <!-- Success Message -->
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
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
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
              {{ isLoading ? "設定中..." : "設定新密碼" }}
            </button>
          </form>

          <!-- Session Error Message -->
          <div
            v-if="!sessionValid && errorMessage"
            class="px-6 sm:px-8 py-8 sm:py-10"
          >
            <div
              class="p-4 bg-red-50 border-l-4 border-red-500 rounded text-red-700 text-sm mb-6"
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
            <NuxtLink
              to="/forgot-password"
              class="inline-block bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold py-2 px-4 rounded-lg hover:shadow-lg hover:from-indigo-700 hover:to-purple-700 transition"
            >
              返回重申請重設密碼
            </NuxtLink>
          </div>

          <!-- Footer Section -->
          <div
            class="bg-gray-50 px-6 sm:px-8 py-6 text-center border-t border-gray-100"
          >
            <p class="text-gray-600 text-sm">
              密碼設定成功？
              <NuxtLink
                to="/login"
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

const router = useRouter();
const route = useRoute();

const password = ref("");
const confirmPassword = ref("");
const errorMessage = ref("");
const successMessage = ref("");
const isLoading = ref(false);
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const sessionValid = ref(false);

// 頁面挂載時驗證會話和令牌
onMounted(async () => {
  try {
    // 檢查 URL 中是否有令牌（來自郵件鏈接）
    const hash = window.location.hash;
    console.log("URL hash:", hash);

    // 如果 URL 中沒有令牌，檢查是否有現有會話
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session && !hash) {
      errorMessage.value =
        "無效的重設密碼鏈接，請重新申請。請檢查您的電子郵件並點擊鏈接。";
      console.error("No session and no token in URL");
      return;
    }

    // 如果有令牌，Supabase 應該自動創建會話
    if (hash) {
      // 等待 Supabase 處理令牌
      setTimeout(() => {
        sessionValid.value = true;
      }, 500);
    } else if (session) {
      sessionValid.value = true;
    }
  } catch (err) {
    console.error("Error checking session:", err);
    errorMessage.value = "驗證會話時發生錯誤";
  }
});

// 驗證密碼匹配
const validatePasswords = () => {
  if (password.value.length < 6) {
    errorMessage.value = "密碼至少需要 6 個字符";
    return false;
  }

  if (password.value !== confirmPassword.value) {
    errorMessage.value = "兩次輸入的密碼不一致，請重新檢查";
    return false;
  }

  return true;
};

const handleResetPassword = async () => {
  errorMessage.value = "";
  successMessage.value = "";

  if (!validatePasswords()) {
    return;
  }

  isLoading.value = true;

  try {
    const { error } = await supabase.auth.updateUser({
      password: password.value,
    });

    if (error) {
      console.error("Password reset error:", error);
      if (error.message.includes("Invalid token")) {
        errorMessage.value = "重設鏈接已過期，請重新申請重設密碼";
      } else if (error.message.includes("same password")) {
        errorMessage.value = "新密碼不能與舊密碼相同";
      } else if (error.message.includes("session")) {
        errorMessage.value = "會話已過期，請重新申請重設密碼";
      } else {
        errorMessage.value = `設定失敗：${error.message}`;
      }
    } else {
      successMessage.value = "密碼已成功重設，將重新導向";
      password.value = "";
      confirmPassword.value = "";
      setTimeout(() => {
        router.push("/");
      }, 1000);
    }
  } catch (err) {
    errorMessage.value = "發生錯誤，請稍後重試";
    console.error("Reset password error:", err);
  } finally {
    isLoading.value = false;
  }
};
</script>
