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
              設定新密碼
            </h1>
            <p class="text-indigo-100 text-sm sm:text-base">請輸入您的新密碼</p>
          </div>

          <!-- 表單區塊 -->
          <form
            v-if="sessionValid"
            @submit.prevent="handleResetPassword"
            class="px-6 sm:px-8 py-8 sm:py-10 space-y-6"
          >
            <!-- 新密碼輸入 -->
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
                  placeholder="請輸入至少 8 個字符"
                  autocomplete="new-password"
                  required
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
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z"
                      clip-rule="evenodd"
                    />
                    <path
                      d="M15.171 13.576l1.414 1.414a1 1 0 00.707-.293l-3.546-3.546a4 4 0 00-5.478-5.478L8.829 6.424a6 6 0 018.484 8.484z"
                    />
                  </svg>
                  <svg
                    v-else
                    class="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                    <path
                      fill-rule="evenodd"
                      d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            </div>

            <!-- 密碼要求說明 -->
            <div class="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
              <p class="text-xs font-semibold text-indigo-900 mb-2">
                密碼要求：
              </p>
              <ul class="text-xs text-indigo-700 space-y-1">
                <li
                  :class="
                    password.length >= 8
                      ? 'text-indigo-600 font-semibold'
                      : 'text-indigo-600'
                  "
                >
                  <span v-if="password.length >= 8">✓</span>
                  <span v-else>○</span>
                  至少 8 個字符
                </li>
                <li
                  :class="
                    hasUppercase
                      ? 'text-indigo-600 font-semibold'
                      : 'text-indigo-600'
                  "
                >
                  <span v-if="hasUppercase">✓</span>
                  <span v-else>○</span>
                  至少 1 個大寫字母 (A-Z)
                </li>
                <li
                  :class="
                    hasLowercase
                      ? 'text-indigo-600 font-semibold'
                      : 'text-indigo-600'
                  "
                >
                  <span v-if="hasLowercase">✓</span>
                  <span v-else>○</span>
                  至少 1 個小寫字母 (a-z)
                </li>
                <li
                  :class="
                    hasNumber
                      ? 'text-indigo-600 font-semibold'
                      : 'text-indigo-600'
                  "
                >
                  <span v-if="hasNumber">✓</span>
                  <span v-else>○</span>
                  至少 1 個數字 (0-9)
                </li>
                <li
                  :class="
                    hasSpecialChar
                      ? 'text-indigo-600 font-semibold'
                      : 'text-indigo-600'
                  "
                >
                  <span v-if="hasSpecialChar">✓</span>
                  <span v-else>○</span>
                  至少 1 個特殊字符 (!@#$%^&*)
                </li>
              </ul>
            </div>
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
                  placeholder="請再次輸入密碼"
                  autocomplete="new-password"
                  required
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
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fill-rule="evenodd"
                      d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z"
                      clip-rule="evenodd"
                    />
                    <path
                      d="M15.171 13.576l1.414 1.414a1 1 0 00.707-.293l-3.546-3.546a4 4 0 00-5.478-5.478L8.829 6.424a6 6 0 018.484 8.484z"
                    />
                  </svg>
                  <svg
                    v-else
                    class="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                    <path
                      fill-rule="evenodd"
                      d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                      clip-rule="evenodd"
                    />
                  </svg>
                </button>
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
              :disabled="isLoading || !isPasswordValid"
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

          <!-- 會話相關錯誤訊息 -->
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
              to="/_builder/forgot-password"
              class="inline-block bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold py-2 px-4 rounded-lg hover:shadow-lg hover:from-indigo-700 hover:to-purple-700 transition"
            >
              返回重申請重設密碼
            </NuxtLink>
          </div>

          <!-- 頁腳區塊 -->
          <div
            class="bg-gray-50 px-6 sm:px-8 py-6 text-center border-t border-gray-100"
          >
            <p class="text-gray-600 text-sm">
              密碼設定成功？
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
// 引入 Supabase：處理驗證與使用者操作（例如更新密碼與會話檢查）

useHead({
  title: "重設密碼 - TGSA 補助引擎",
});

// router 用於頁面導向；route 用於取得當前路由資訊（例如重設 token 在 URL hash）
const router = useRouter();
const route = useRoute();

// 表單欄位與 UI 狀態說明
const password = ref(""); // 使用者輸入的新密碼
const confirmPassword = ref(""); // 確認密碼欄位
const errorMessage = ref(""); // 顯示錯誤訊息
const successMessage = ref(""); // 顯示成功訊息
const isLoading = ref(false); // 請求進行中
const showPassword = ref(false); // 新密碼顯示切換
const showConfirmPassword = ref(false); // 確認密碼顯示切換
const sessionValid = ref(false); // 是否有有效的重設會話/token，控制是否顯示表單

// 以下為密碼驗證計算屬性（用於 UI 即時顯示各項要求是否滿足）
const hasUppercase = computed(() => /[A-Z]/.test(password.value));
const hasLowercase = computed(() => /[a-z]/.test(password.value));
const hasNumber = computed(() => /[0-9]/.test(password.value));
const hasSpecialChar = computed(() =>
  /[!@#$%^&*()_\-+=\[\]{};':"\\|,.<>\/?]/.test(password.value),
);

/* isPasswordValid：綜合檢查密碼是否符合所有條件（長度、字元組合、與確認密碼相符） */
const isPasswordValid = computed(() => {
  return (
    password.value.length >= 8 &&
    hasUppercase.value &&
    hasLowercase.value &&
    hasNumber.value &&
    hasSpecialChar.value &&
    password.value === confirmPassword.value &&
    confirmPassword.value.length > 0
  );
});

// 頁面掛載時：檢查 URL hash（可能含重設 token）或現有會話，以決定是否顯示重設表單
onMounted(async () => {
  try {
    // 檢查 URL 中是否有令牌（來自郵件鏈接）
    const hash = window.location.hash;

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

/**
 * handleResetPassword - 處理重設密碼流程
 * 步驟：
 *  1) 驗證欄位與密碼強度
 *  2) 呼叫 Supabase API 更新使用者密碼
 *  3) 根據錯誤訊息給予使用者具體提示（例如 token 過期 / 與舊密碼相同）
 *  4) 成功後導向回首頁
 */
const handleResetPassword = async () => {
  errorMessage.value = "";
  successMessage.value = "";

  if (!isPasswordValid.value) {
    errorMessage.value =
      "密碼不符合要求。請確保包含大小寫字母、數字和特殊字符，且至少 8 個字符。";
    return;
  }

  if (password.value !== confirmPassword.value) {
    errorMessage.value = "兩次輸入的密碼不一致，請重新檢查";
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
        router.push("/_builder/login");
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
