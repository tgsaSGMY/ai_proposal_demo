<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="isOpenModel"
        class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/60 px-4 py-6 backdrop-blur-sm"
        @click.self="handleClose"
      >
        <div
          class="flex max-h-[85vh] w-full max-w-xl flex-col overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-2xl"
        >
          <header class="border-b border-slate-100 px-6 py-5">
            <p
              class="text-xs font-semibold uppercase tracking-widest text-[#ff7a5b]"
            >
              生成前確認
            </p>
            <h2 class="mt-1 text-xl font-bold text-slate-900">
              部分答案由 AI 生成
            </h2>
            <p class="mt-2 text-sm text-slate-500">
              共 {{ readiness?.total_applicable ?? 0 }} 題，其中
              {{ readiness?.user_filled ?? 0 }} 題由您填寫、
              {{ readiness?.ai_generated ?? 0 }} 題由 AI 生成<span
                v-if="(readiness?.needs_review ?? 0) > 0"
                >，<span class="font-semibold text-rose-600"
                  >{{ readiness?.needs_review }} 題建議確認</span
                ></span
              >。
            </p>
            <p class="mt-1 text-sm font-semibold text-rose-600">
              建議先確認所有 AI 生成內容再輸出完整推演（已確認
              {{ confirmedCount }} / {{ fieldCount }}）
            </p>
          </header>

          <div class="flex-1 space-y-2 overflow-y-auto px-6 py-4">
            <div
              v-for="field in sortedFields"
              :key="field.id"
              class="rounded-2xl border-2 p-3"
              :class="
                field.needs_review
                  ? 'border-rose-200 bg-rose-50'
                  : 'border-slate-100 bg-slate-50'
              "
            >
              <div class="flex items-center gap-2">
                <p class="min-w-0 flex-1 text-sm font-semibold text-slate-800">
                  {{ field.label }}
                </p>
                <span
                  v-if="field.confirmed"
                  class="flex-shrink-0 rounded bg-emerald-100 px-1.5 py-0.5 text-[0.625rem] font-medium leading-none text-emerald-700"
                >
                  ✓ 已確認
                </span>
                <span
                  v-else-if="field.needs_review"
                  class="flex-shrink-0 rounded bg-rose-100 px-1.5 py-0.5 text-[0.625rem] font-medium leading-none text-rose-600"
                >
                  待確認
                </span>
                <span
                  v-if="field.source === 'ai_generated'"
                  class="flex-shrink-0 rounded bg-slate-200 px-1.5 py-0.5 text-[0.625rem] font-medium leading-none text-slate-500"
                >
                  AI
                </span>
              </div>
              <p v-if="field.review_note" class="mt-1 text-xs text-slate-500">
                {{ field.review_note }}
              </p>
            </div>
          </div>

          <footer
            class="flex flex-col gap-3 border-t border-slate-100 px-6 py-5 sm:flex-row sm:justify-end"
          >
            <button
              type="button"
              class="rounded-xl border border-slate-300 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
              @click="handleClose"
            >
              取消
            </button>
            <button
              type="button"
              class="rounded-xl border border-slate-300 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
              @click="emitProceed"
            >
              繼續生成
            </button>
            <button
              type="button"
              class="rounded-xl bg-gradient-to-r from-rose-500 to-amber-500 px-6 py-2 text-sm font-semibold text-white shadow-lg"
              @click="emitReview"
            >
              前往確認
            </button>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface ReadinessField {
  id: string;
  label: string;
  source: string;
  needs_review: boolean;
  review_note?: string | null;
  confirmed?: boolean;
}

interface ExportReadiness {
  total_applicable: number;
  user_filled: number;
  ai_generated: number;
  needs_review: number;
  unconfirmed?: number;
  fields: ReadinessField[];
}

const props = defineProps({
  readiness: {
    type: Object as () => ExportReadiness | null,
    default: null,
  },
});

const emit = defineEmits<{
  (e: "proceed"): void;
  (e: "review", fieldIds: string[]): void;
}>();
const isOpenModel = defineModel("isOpen", { type: Boolean, default: false });

// 待確認的排最前面，其中需特別確認（needs_review）的再優先
const sortedFields = computed(() => {
  const fields = props.readiness?.fields || [];
  const rank = (f: ReadinessField) => (f.confirmed ? 2 : f.needs_review ? 0 : 1);
  return [...fields].sort((a, b) => rank(a) - rank(b));
});

const fieldCount = computed(() => props.readiness?.fields?.length ?? 0);
const confirmedCount = computed(
  () => (props.readiness?.fields || []).filter((f) => f.confirmed).length,
);

// 略過這次確認直接生成；答案維持未確認，下次生成仍會提示
function emitProceed() {
  isOpenModel.value = false;
  emit("proceed");
}

function emitReview() {
  isOpenModel.value = false;
  emit(
    "review",
    (props.readiness?.fields || []).map((f) => f.id),
  );
}

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
