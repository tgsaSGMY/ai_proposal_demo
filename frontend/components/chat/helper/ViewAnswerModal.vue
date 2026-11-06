<!-- 答案檢視組件：查看完整答案（點擊關鍵指令卡片的「展開」會打開此模態框） -->
<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="isOpenModel"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 py-6 overflow-y-auto"
        @click.self="handleClose"
      >
        <div
          class="w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden flex flex-col my-8"
        >
          <header
            class="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5 bg-white"
          >
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <p
                  class="text-xs font-semibold tracking-widest text-slate-500 uppercase"
                >
                  {{ title || "查看欄位" }}
                </p>
                <span
                  v-if="isAiGenerated"
                  class="rounded bg-slate-200 px-2 py-1 text-xs font-medium leading-none text-slate-600"
                  :title="aiBadgeTitle"
                >
                  AI
                </span>
              </div>
              <h2 class="text-2xl font-bold text-slate-900">{{ label }}</h2>
            </div>
            <button
              type="button"
              class="text-slate-500 hover:text-slate-700"
              @click="handleClose"
            >
              <span class="sr-only">關閉</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </header>

          <div class="flex-1 overflow-y-auto px-6 py-6">
            <!-- 僅顯示用：長段落依句號分段，不改動已儲存的答案（Word 輸出不受影響） -->
            <div
              class="max-h-[60vh] space-y-3 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-4 text-base leading-relaxed text-slate-800"
            >
              <template v-if="paragraphs.length">
                <p v-for="(para, index) in paragraphs" :key="index">
                  <span
                    v-for="(segment, segIndex) in splitPlaceholders(para)"
                    :key="segIndex"
                    :class="segment.hit ? 'rounded bg-amber-100 px-0.5 font-medium text-amber-800' : ''"
                    >{{ segment.text }}</span
                  >
                </p>
              </template>
              <p v-else>（待回答）</p>
            </div>
          </div>

          <footer
            class="flex flex-col gap-3 border-t border-slate-100 bg-white px-6 py-5 sm:flex-row sm:items-center sm:justify-between"
          >
            <div></div>
            <div class="flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                class="rounded-xl border border-slate-300 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                @click="handleClose"
              >
                關閉
              </button>
              <template v-if="!isReadOnly">
                <button
                  type="button"
                  class="rounded-xl border border-slate-300 px-5 py-2 text-sm font-semibold text-slate-600 hover:border-[#ff6b3d] hover:text-[#ff6b3d]"
                  @click="emitAndClose('regenerate')"
                >
                  重新生成
                </button>
                <button
                  type="button"
                  class="rounded-xl bg-gradient-to-r from-rose-500 to-amber-500 px-6 py-2 text-sm font-semibold text-white shadow-lg"
                  @click="emitAndClose('edit')"
                >
                  編輯
                </button>
              </template>
            </div>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { splitAnswerParagraphs } from "~/utils/answerParagraphs";
import { splitPlaceholders } from "~/utils/placeholderHighlight";

const props = defineProps({
  title: { type: String, default: "" },
  label: { type: String, default: "" },
  answer: { type: String, default: "" },
  isAiGenerated: { type: Boolean, default: false },
  aiBadgeTitle: { type: String, default: "" },
  isReadOnly: { type: Boolean, default: false },
});

// 顯示用分段（只影響排版；props.answer 原文不變，Word 輸出不受影響）
const paragraphs = computed(() => splitAnswerParagraphs(props.answer));

const emit = defineEmits<{
  (e: "regenerate"): void;
  (e: "edit"): void;
}>();
const isOpenModel = defineModel("isOpen", { type: Boolean, default: false });

// 先關閉本模態框，再交給外層處理（重新生成確認框／編輯模態框）
function emitAndClose(action: "regenerate" | "edit") {
  handleClose();
  if (action === "regenerate") {
    emit("regenerate");
  } else {
    emit("edit");
  }
}

// 關閉模態框
function handleClose() {
  isOpenModel.value = false;
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
