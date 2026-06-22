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
              <h2 class="text-2xl font-bold text-slate-900">
                體驗已達上限
              </h2>
              <p class="text-sm text-slate-500">
                體驗次數已達上限，免費註冊即可繼續使用。
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
            <!-- Project title (editable before migration) -->
            <div>
              <label for="demo-project-title" class="block text-sm font-medium text-slate-700 mb-1">
                計畫書名稱
              </label>
              <input
                id="demo-project-title"
                v-model="editableTitle"
                type="text"
                class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:border-rose-400 focus:outline-none focus:ring-1 focus:ring-rose-400"
                placeholder="為您的計畫書命名"
                @change="handleTitleChange"
              />
              <p class="mt-1 text-xs text-slate-400">註冊後將以此名稱帶入完整平台</p>
            </div>

            <!-- Benefits -->
            <div>
              <p class="text-sm font-semibold text-slate-800 mb-3">註冊免費帳號，即刻解鎖：</p>
              <ul class="space-y-2.5">
                <li class="flex items-start gap-3 text-sm text-slate-600">
                  <span class="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-green-100 text-green-600 text-xs font-bold flex-shrink-0">✓</span>
                  <span>完整 AI 對話與計畫書生成</span>
                </li>
                <li class="flex items-start gap-3 text-sm text-slate-600">
                  <span class="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-green-100 text-green-600 text-xs font-bold flex-shrink-0">✓</span>
                  <span>Word 完整報告匯出</span>
                </li>
                <li class="flex items-start gap-3 text-sm text-slate-600">
                  <span class="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-green-100 text-green-600 text-xs font-bold flex-shrink-0">✓</span>
                  <span>多版本管理與歷程追蹤</span>
                </li>
              </ul>
            </div>

            <!-- Note -->
            <div class="rounded-xl bg-amber-50 border border-amber-100 px-4 py-3">
              <p class="text-xs text-amber-700 leading-relaxed">
                💡 您目前的對話內容已自動儲存，註冊後可立即返回原進度，繼續完成計畫書。
              </p>
            </div>
          </div>

          <!-- Footer -->
          <footer class="flex items-center justify-center border-t border-slate-100 bg-white px-6 py-6">
            <a
              :href="registerHref"
              target="_blank"
              class="rounded-2xl bg-gradient-to-r from-rose-500 to-amber-500 px-10 py-4 text-base font-semibold text-white shadow-lg text-center hover:shadow-xl transition"
            >
              立即免費註冊 →
            </a>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  interactionCount: { type: Number, default: 0 },
  interactionLimit: { type: Number, default: 15 },
  registerUrl: { type: String, default: "" },
  sessionId: { type: String, default: "" },
  projectTitle: { type: String, default: "" },
});

const emit = defineEmits(["close", "updateTitle"]);
const isOpenModel = defineModel("isOpen", { type: Boolean, default: false });

const editableTitle = ref(props.projectTitle || "計畫草稿");

watch(() => props.projectTitle, (val) => {
  if (val) editableTitle.value = val;
});

function handleTitleChange() {
  emit("updateTitle", editableTitle.value);
}

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