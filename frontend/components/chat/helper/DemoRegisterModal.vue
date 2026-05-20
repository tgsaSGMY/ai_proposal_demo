<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="isOpenModel"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 py-6 overflow-y-auto"
        @click.self="handleClose"
      >
        <div class="w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden flex flex-col my-8">
          <!-- Header -->
          <header class="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5 bg-gradient-to-r from-rose-50 to-amber-50">
            <div class="space-y-1">
              <p class="text-xs font-semibold tracking-widest text-slate-500 uppercase">
                Demo Limit Reached
              </p>
              <h2 class="text-2xl font-bold text-slate-900">
                體驗已達上限
              </h2>
              <p class="text-sm text-slate-500">
                Demo limit reached, sign up for FREE to continue the session.
              </p>
            </div>
            <button type="button" class="text-slate-500 hover:text-slate-700 transition" @click="handleClose">
              <span class="sr-only">關閉</span>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </header>

          <!-- Body -->
          <div class="flex-1 overflow-y-auto px-6 py-6 space-y-5">
            <!-- Stats -->
            <div class="flex items-center gap-4 rounded-2xl bg-slate-50 px-5 py-4 border border-slate-100">
              <div class="flex-1">
                <p class="text-xs text-slate-500 uppercase tracking-wide">已使用互動次數</p>
                <p class="text-lg font-bold text-slate-900 mt-0.5">
                  {{ interactionCount }} <span class="text-sm font-normal text-slate-400">/ {{ interactionLimit }}</span>
                </p>
              </div>
              <div class="h-10 w-px bg-slate-200"></div>
              <div class="flex-1">
                <p class="text-xs text-slate-500 uppercase tracking-wide">計畫書完成度</p>
                <p class="text-lg font-bold text-slate-900 mt-0.5">
                  {{ completionPercent }}%
                </p>
              </div>
            </div>

            <!-- Benefits -->
            <div>
              <p class="text-sm font-semibold text-slate-800 mb-3">註冊免費帳號，即刻解鎖：</p>
              <ul class="space-y-2.5">
                <li class="flex items-start gap-3 text-sm text-slate-600">
                  <span class="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-green-100 text-green-600 text-xs font-bold flex-shrink-0">✓</span>
                  <span>無限制 AI 對話與計畫書優化</span>
                </li>
                <li class="flex items-start gap-3 text-sm text-slate-600">
                  <span class="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-green-100 text-green-600 text-xs font-bold flex-shrink-0">✓</span>
                  <span>Word / PDF 完整報告匯出</span>
                </li>
                <li class="flex items-start gap-3 text-sm text-slate-600">
                  <span class="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-green-100 text-green-600 text-xs font-bold flex-shrink-0">✓</span>
                  <span>多版本管理與歷程追蹤</span>
                </li>
                <li class="flex items-start gap-3 text-sm text-slate-600">
                  <span class="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-green-100 text-green-600 text-xs font-bold flex-shrink-0">✓</span>
                  <span>團隊協作與檔案上傳輔助填寫</span>
                </li>
              </ul>
            </div>

            <!-- Note -->
            <div class="rounded-xl bg-amber-50 border border-amber-100 px-4 py-3">
              <p class="text-xs text-amber-700 leading-relaxed">
                💡 您目前的對話內容已自動儲存。註冊後即可無縫接軌，繼續完成這份計畫書。
              </p>
            </div>
          </div>

          <!-- Footer -->
          <footer class="flex flex-col gap-3 border-t border-slate-100 bg-white px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
            <div></div>
            <div class="flex flex-col gap-3 sm:flex-row w-full sm:w-auto">
              <button
                type="button"
                class="rounded-xl border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition"
                @click="handleClose"
              >
                再看看
              </button>
              <a
                :href="registerHref"
                target="_blank"
                class="rounded-xl bg-gradient-to-r from-rose-500 to-amber-500 px-6 py-2.5 text-sm font-semibold text-white shadow-lg text-center hover:shadow-xl transition"
              >
                立即免費註冊 →
              </a>
            </div>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  interactionCount: { type: Number, default: 0 },
  interactionLimit: { type: Number, default: 15 },
  registerUrl: { type: String, default: "" },
  sessionId: { type: String, default: "" },
});

const emit = defineEmits(["close"]);
const isOpenModel = defineModel("isOpen", { type: Boolean, default: false });

const completionPercent = computed(() => {
  if (!props.interactionLimit) return 0;
  return Math.min(100, Math.round((props.interactionCount / props.interactionLimit) * 100));
});

const registerHref = computed(() => {
  if (!props.registerUrl) return "#";
  const url = new URL(props.registerUrl);
  if (props.sessionId) {
    url.searchParams.set("ref", props.sessionId);
  }
  return url.toString();
});

function handleClose() {
  isOpenModel.value = false;
  emit("close");
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>