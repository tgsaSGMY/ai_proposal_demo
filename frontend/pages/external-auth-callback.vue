<template>
  <ClientOnly>
    <div class="min-h-[60vh] flex items-center justify-center p-6">
      <div
        class="w-full max-w-md rounded-xl border border-gray-200 bg-white p-6 shadow"
      >
        <h1 class="text-xl font-semibold text-gray-900">外部登入處理中</h1>
        <p class="mt-3 text-sm text-gray-600">{{ message }}</p>
      </div>
    </div>
  </ClientOnly>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: "redirect-if-authenticated",
});

const router = useRouter();
const message = ref("正在完成登入，請稍候...");
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

onMounted(async () => {
  try {
    const meResponse = await fetch(`${API_BASE_URL}/auth/me`, {
      credentials: "include",
    });

    if (!meResponse.ok) {
      message.value = "外部登入失敗：登入狀態未建立。";
      return;
    }

    message.value = "登入成功，正在跳轉...";
    await router.replace("/");
  } catch (error) {
    console.error("Failed to finalize external login", error);
    message.value = "外部登入處理失敗，請稍後重試。";
  }
});
</script>
