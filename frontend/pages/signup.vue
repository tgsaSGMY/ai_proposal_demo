<template>
  <div class="flex items-center justify-center px-4 sm:p-6">
    <div class="w-full max-w-md">
      <!-- Card Container -->
      <div class="bg-white rounded-2xl shadow-2xl overflow-hidden">
        <!-- Header Section with Gradient -->
        <div
          class="bg-gradient-to-r from-purple-600 to-violet-600 px-6 sm:px-8 py-4 sm:py-7"
        >
          <h1 class="text-3xl sm:text-4xl font-bold text-white mb-2">
            建立帳戶
          </h1>
          <p class="text-purple-100 text-sm sm:text-base">
            加入 AI 計畫書生成平台
          </p>
        </div>

        <!-- Form Section -->
        <form
          @submit.prevent="handleSignUp"
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
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200 transition duration-200 text-gray-900 placeholder-gray-400"
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
            <div class="relative">
              <input
                :type="showPassword ? 'text' : 'password'"
                id="password"
                v-model="password"
                placeholder="請輸入至少 6 個字符"
                required
                class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200 transition duration-200 text-gray-900 placeholder-gray-400"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                <svg
                  v-if="!showPassword"
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
                <svg
                  v-else
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
              </button>
            </div>
          </div>

          <!-- Password Requirements -->
          <div class="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <p class="text-xs font-semibold text-purple-900 mb-2">密碼要求：</p>
            <ul class="text-xs text-purple-700 space-y-1">
              <li
                :class="
                  password.length >= 8
                    ? 'text-purple-600 font-semibold'
                    : 'text-purple-600'
                "
              >
                <span v-if="password.length >= 8">✓</span>
                <span v-else>○</span>
                至少 8 個字符
              </li>
              <li
                :class="
                  hasUppercase
                    ? 'text-purple-600 font-semibold'
                    : 'text-purple-600'
                "
              >
                <span v-if="hasUppercase">✓</span>
                <span v-else>○</span>
                至少 1 個大寫字母 (A-Z)
              </li>
              <li
                :class="
                  hasLowercase
                    ? 'text-purple-600 font-semibold'
                    : 'text-purple-600'
                "
              >
                <span v-if="hasLowercase">✓</span>
                <span v-else>○</span>
                至少 1 個小寫字母 (a-z)
              </li>
              <li
                :class="
                  hasNumber
                    ? 'text-purple-600 font-semibold'
                    : 'text-purple-600'
                "
              >
                <span v-if="hasNumber">✓</span>
                <span v-else>○</span>
                至少 1 個數字 (0-9)
              </li>
              <li
                :class="
                  hasSpecialChar
                    ? 'text-purple-600 font-semibold'
                    : 'text-purple-600'
                "
              >
                <span v-if="hasSpecialChar">✓</span>
                <span v-else>○</span>
                至少 1 個特殊字符 (!@#$%^&*)
              </li>
            </ul>
          </div>

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
            :disabled="loading || !isPasswordValid"
            class="w-full bg-gradient-to-r from-purple-600 to-violet-600 text-white font-bold py-3 px-4 rounded-lg hover:shadow-lg hover:from-purple-700 hover:to-violet-700 transition duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
          >
            <svg
              v-if="!loading"
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
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
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            {{ loading ? "註冊中..." : "建立帳戶" }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { supabase } from "~/utils/supabaseClient";

definePageMeta({
  middleware: "redirect-if-authenticated",
});

const router = useRouter();

const email = ref("");
const password = ref("");
const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const showPassword = ref(false);

// 密碼驗證計算屬性
const hasUppercase = computed(() => /[A-Z]/.test(password.value));
const hasLowercase = computed(() => /[a-z]/.test(password.value));
const hasNumber = computed(() => /[0-9]/.test(password.value));
const hasSpecialChar = computed(() =>
  /[!@#$%^&*()_\-+=\[\]{};':"\\|,.<>\/?]/.test(password.value)
);

const isPasswordValid = computed(() => {
  return (
    password.value.length >= 8 &&
    hasUppercase.value &&
    hasLowercase.value &&
    hasNumber.value &&
    hasSpecialChar.value
  );
});

const handleSignUp = async () => {
  if (!email.value || !password.value) {
    errorMessage.value = "請輸入電子郵件和密碼";
    return;
  }

  if (!isPasswordValid.value) {
    errorMessage.value =
      "密碼不符合要求。請確保包含大小寫字母、數字和特殊字符，且至少 8 個字符。";
    return;
  }

  loading.value = true;
  errorMessage.value = "";
  successMessage.value = "";

  try {
    // 步驟 1: 使用 RPC 檢查 Email 是否在白名單中（回傳 boolean）
    const { data: isWhitelisted, error: whitelistError } = await supabase.rpc(
      "is_whitelisted",
      { email: email.value }
    );
    // 如果呼叫失敗或回傳 false（未被授權）
    if (whitelistError || !isWhitelisted) {
      errorMessage.value = "此電子郵件未被授權註冊。";
      loading.value = false;
      return;
    }

    // 步驟 3: 如果 Email 在白名單中且未被註冊，才執行真正的註冊
    const { data, error: signUpError } = await supabase.auth.signUp({
      email: email.value,
      password: password.value,
    });

    if (signUpError) {
      errorMessage.value = signUpError.message || "註冊失敗，請稍後重試";
    } else {
      successMessage.value = "註冊成功！您現在可以去郵箱點擊確認鏈接。";
      // 清空表單
      email.value = "";
      password.value = "";
    }
  } catch (err) {
    errorMessage.value = "發生未知錯誤，請稍後重試。";
    console.error("Signup error:", err);
  } finally {
    loading.value = false;
  }
};
</script>
