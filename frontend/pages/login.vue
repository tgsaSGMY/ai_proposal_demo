<template>
  <ClientOnly>
    <div class="flex items-center justify-center p-4 sm:p-6 min-h-[70vh]">
      <div class="w-full max-w-md">
        <div class="bg-white rounded-2xl shadow-2xl overflow-hidden">
          <div
            class="bg-gradient-to-r from-sky-600 to-cyan-600 px-6 sm:px-8 py-8 sm:py-10"
          >
            <h1 class="text-3xl sm:text-4xl font-bold text-white mb-2">
              外部帳號登入
            </h1>
            <p class="text-sky-100 text-sm sm:text-base">
              透過合作平台完成授權後，將自動返回本系統
            </p>
          </div>

          <div class="px-6 sm:px-8 py-8 sm:py-10 space-y-5">
            <p class="text-sm text-gray-600">
              點擊下方按鈕將前往外部平台登入，授權完成後自動返回。
            </p>
            <button
              type="button"
              @click="handleExternalLogin"
              class="w-full bg-gradient-to-r from-sky-600 to-cyan-600 text-white font-bold py-3 px-4 rounded-lg hover:shadow-lg hover:from-sky-700 hover:to-cyan-700 transition duration-300"
            >
              前往外部平台登入
            </button>
          </div>
        </div>
      </div>
    </div>
  </ClientOnly>
</template>

<script setup>
definePageMeta({
  middleware: "redirect-if-authenticated",
});

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const handleExternalLogin = () => {
  window.location.href = `${API_BASE_URL}/external-auth/redirect`;
};
</script>
