<!-- 生成前確認視窗：左側段落清單、右側完整內容；動作列固定在底部，只有內文捲動。
     確認或編輯儲存後自動跳到下一段待確認，全部確認後自動關閉。 -->
<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="isOpenModel && current"
        class="fixed inset-0 z-[45] flex items-center justify-center bg-slate-900/60 p-6 backdrop-blur-sm"
        @click.self="close"
      >
        <div
          class="flex h-[85vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
        >
          <header class="flex flex-shrink-0 items-center gap-4 border-b border-slate-100 px-6 py-4">
            <div class="min-w-0 flex-1">
              <p class="text-xs font-semibold tracking-widest text-[#ff7a5b]">
                生成前確認 · 第 {{ currentIndex + 1 }} / {{ items.length }} 段
              </p>
              <div class="mt-1 flex items-center gap-2">
                <h2 class="truncate text-xl font-bold text-slate-900">{{ current.title }}</h2>
                <span
                  v-if="current.isAiGenerated"
                  class="flex-shrink-0 rounded bg-slate-200 px-2 py-1 text-xs font-medium leading-none text-slate-600"
                >
                  AI
                </span>
                <span
                  class="flex-shrink-0 rounded px-2 py-1 text-xs font-semibold leading-none"
                  :class="
                    current.state === 'confirmed'
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-amber-100 text-amber-700'
                  "
                >
                  {{ current.state === "confirmed" ? "✓ 已確認" : "待確認" }}
                </span>
              </div>
              <p v-if="current.section" class="mt-0.5 text-xs text-slate-400">
                {{ current.section }}
              </p>
            </div>
            <div class="w-44 flex-shrink-0">
              <div class="flex justify-between text-xs text-slate-500">
                <span>已確認</span>
                <span class="font-semibold text-slate-800">{{ confirmedCount }} / {{ items.length }}</span>
              </div>
              <div class="mt-1 h-2 overflow-hidden rounded-full bg-slate-200">
                <div
                  class="h-full rounded-full bg-emerald-600 transition-all duration-300"
                  :style="{ width: `${progressPercent}%` }"
                ></div>
              </div>
            </div>
            <button
              type="button"
              class="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
              title="關閉"
              @click="close"
            >
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </header>

          <div class="flex min-h-0 flex-1">
            <!-- 段落清單 -->
            <nav class="review-scroll w-60 flex-shrink-0 space-y-1 overflow-y-auto border-r border-slate-100 p-3">
              <button
                v-for="item in items"
                :key="item.id"
                type="button"
                class="flex w-full items-start gap-2 rounded-xl px-3 py-2 text-left text-sm transition"
                :class="item.id === currentId ? 'bg-rose-50 ring-1 ring-rose-300' : 'hover:bg-slate-50'"
                @click="goTo(item.id)"
              >
                <span
                  class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-[0.65rem] font-bold text-white"
                  :class="item.state === 'confirmed' ? 'bg-emerald-500' : 'bg-amber-400'"
                >
                  {{ item.state === "confirmed" ? "✓" : "!" }}
                </span>
                <span class="min-w-0">
                  <span v-if="item.section" class="block truncate text-[0.7rem] text-slate-400">
                    {{ item.section }}
                  </span>
                  <span
                    class="block leading-snug"
                    :class="item.id === currentId ? 'font-semibold text-slate-900' : 'text-slate-600'"
                  >
                    {{ item.title }}
                  </span>
                </span>
              </button>
            </nav>

            <!-- 完整內容 -->
            <div class="flex min-w-0 flex-1 flex-col">
              <p
                v-if="placeholderCount && !isEditing"
                class="mx-6 mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-800"
              >
                ⚠ 有 {{ placeholderCount }} 處「待決定」資料（已標示），AI 無法查證，請編輯補上可查證的資料。
              </p>
              <div class="review-scroll min-h-0 flex-1 overflow-y-auto px-6 py-4">
                <textarea
                  v-if="isEditing"
                  ref="editBox"
                  v-model="editText"
                  class="h-full min-h-[18rem] w-full resize-none rounded-xl border border-[#ff6b3d] bg-white p-4 text-[0.95rem] leading-8 text-slate-800 outline-none"
                ></textarea>
                <div v-else class="space-y-3 text-[0.95rem] leading-8 text-slate-700">
                  <p v-for="(para, index) in paragraphs" :key="index">
                    <span
                      v-for="(segment, segIndex) in splitPlaceholders(para)"
                      :key="segIndex"
                      :class="segment.hit ? 'rounded bg-amber-100 px-0.5 font-medium text-amber-800' : ''"
                      >{{ segment.text }}</span
                    >
                  </p>
                </div>
              </div>

              <footer class="flex flex-shrink-0 items-center gap-2 border-t border-slate-100 bg-white px-6 py-4">
                <template v-if="isEditing">
                  <p class="text-xs text-slate-500">儲存後會視為您自己的答案，不需再確認。</p>
                  <div class="ml-auto flex gap-2">
                    <button
                      type="button"
                      class="rounded-xl border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                      @click="isEditing = false"
                    >
                      取消
                    </button>
                    <button
                      type="button"
                      class="rounded-xl bg-gradient-to-r from-rose-500 to-amber-500 px-6 py-2.5 text-sm font-semibold text-white shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
                      :disabled="!canEdit || !editText.trim()"
                      @click="saveEdit"
                    >
                      儲存並下一段
                    </button>
                  </div>
                </template>

                <template v-else>
                  <button
                    type="button"
                    class="rounded-xl border border-slate-300 px-3 py-2.5 text-sm text-slate-600 hover:bg-slate-50"
                    title="上一段"
                    @click="step(-1)"
                  >
                    ‹
                  </button>
                  <button
                    type="button"
                    class="rounded-xl border border-slate-300 px-3 py-2.5 text-sm text-slate-600 hover:bg-slate-50"
                    title="下一段"
                    @click="step(1)"
                  >
                    ›
                  </button>
                  <button
                    type="button"
                    class="ml-2 inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-700 transition hover:border-[#ff6b3d] hover:text-[#ff6b3d] disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="!canEdit || isReadOnly"
                    @click="regenerate"
                  >
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    重新生成
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-700 transition hover:border-[#ff6b3d] hover:text-[#ff6b3d] disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="!canEdit || isReadOnly"
                    @click="startEdit"
                  >
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536M9 13l6.232-6.232a2.5 2.5 0 113.536 3.536L12.536 16.536 9 17l.464-3.536z" />
                    </svg>
                    編輯
                  </button>
                  <span v-if="!canEdit" class="text-xs text-slate-400">AI 回覆中，請稍候…</span>

                  <button
                    v-if="current.state === 'confirmed' && current.canUnconfirm"
                    type="button"
                    class="ml-auto text-sm text-slate-500 underline hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="current.busy || isReadOnly"
                    @click="$emit('unconfirm', current.id)"
                  >
                    {{ current.busy ? "處理中..." : "取消確認" }}
                  </button>
                  <button
                    v-else-if="current.state === 'pending'"
                    type="button"
                    class="ml-auto inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="current.busy || isReadOnly"
                    @click="confirmCurrent"
                  >
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                    </svg>
                    {{ current.busy ? "確認中..." : "內容正確，確認並下一段" }}
                  </button>
                  <button
                    v-if="allConfirmed"
                    type="button"
                    :class="current.canUnconfirm ? 'ml-3' : 'ml-auto'"
                    class="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white shadow transition hover:bg-emerald-700"
                    @click="close"
                  >
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                    </svg>
                    內容全部正確，下一步
                  </button>
                </template>
              </footer>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import type { PropType } from "vue";
import { answerToEditText, editTextToAnswer, splitAnswerParagraphs } from "~/utils/answerParagraphs";
import { countPlaceholders, splitPlaceholders } from "~/utils/placeholderHighlight";

export interface ReviewItem {
  id: string;
  section: string;
  title: string;
  // 完整欄位名稱（送出「幫我更改」／重新生成時使用）
  fullLabel: string;
  answer: string;
  isAiGenerated: boolean;
  state: "pending" | "confirmed";
  // 已改成使用者自己的答案時為 false（不顯示「取消確認」）
  canUnconfirm: boolean;
  // 已送出確認、等待後端回覆
  busy: boolean;
}

const props = defineProps({
  items: { type: Array as PropType<ReviewItem[]>, default: () => [] },
  canEdit: { type: Boolean, default: false },
  isReadOnly: { type: Boolean, default: false },
});

const emit = defineEmits<{
  (e: "confirm", id: string): void;
  (e: "unconfirm", id: string): void;
  (e: "regenerate", payload: { questionId: string; questionLabel: string }): void;
  (e: "saveEdit", payload: { questionId: string; questionLabel: string; value: string }): void;
}>();

const isOpenModel = defineModel("isOpen", { type: Boolean, default: false });
const currentId = defineModel<string | null>("currentId", { default: null });

const currentIndex = computed(() => props.items.findIndex((item) => item.id === currentId.value));
const current = computed(() => props.items[currentIndex.value] ?? null);
const paragraphs = computed(() => splitAnswerParagraphs(current.value?.answer || ""));
const placeholderCount = computed(() => countPlaceholders(current.value?.answer || ""));

const confirmedCount = computed(
  () => props.items.filter((item) => item.state === "confirmed").length,
);
const allConfirmed = computed(
  () => props.items.length > 0 && confirmedCount.value === props.items.length,
);
const progressPercent = computed(() =>
  props.items.length ? Math.round((confirmedCount.value / props.items.length) * 100) : 100,
);

// 從目前這段之後找下一段待確認（到底後從頭找）；目前這段與送出中的略過
function nextPendingId() {
  const items = props.items;
  const start = currentIndex.value + 1;
  const ordered = [...items.slice(start), ...items.slice(0, start)];
  return (
    ordered.find(
      (item) => item.id !== currentId.value && item.state === "pending" && !item.busy,
    )?.id ?? null
  );
}

// 確認／儲存後前往下一段；沒有待確認的就關閉視窗
function advance() {
  const nextId = nextPendingId();
  if (nextId) {
    currentId.value = nextId;
  } else {
    close();
  }
}

function goTo(id: string) {
  isEditing.value = false;
  currentId.value = id;
}

function step(offset: number) {
  const count = props.items.length;
  if (!count) return;
  goTo(props.items[(currentIndex.value + offset + count) % count].id);
}

function confirmCurrent() {
  if (!current.value) return;
  emit("confirm", current.value.id);
  advance();
}

function regenerate() {
  if (!current.value) return;
  emit("regenerate", { questionId: current.value.id, questionLabel: current.value.fullLabel });
}

// ===== 編輯：沿用聊天「幫我更改」流程 =====
const isEditing = ref(false);
const editText = ref("");
const editBox = ref<HTMLTextAreaElement | null>(null);

async function startEdit() {
  if (!current.value) return;
  // 與編輯模態框一致的分段；送出時會移除自動補的換段
  editText.value = answerToEditText(current.value.answer);
  isEditing.value = true;
  await nextTick();
  editBox.value?.focus();
}

function saveEdit() {
  if (!current.value) return;
  const value = editTextToAnswer(editText.value).trim();
  if (!value) return;
  isEditing.value = false;
  emit("saveEdit", {
    questionId: current.value.id,
    questionLabel: current.value.fullLabel,
    value,
  });
  advance();
}

function close() {
  isEditing.value = false;
  isOpenModel.value = false;
}

// 目前這段從清單消失（例如答案被清空）時，改到第一段
watch(
  () => props.items.map((item) => item.id).join("|"),
  () => {
    if (isOpenModel.value && !current.value && props.items.length) {
      currentId.value = props.items[0].id;
    }
  },
);
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

.review-scroll {
  scrollbar-width: thin;
  scrollbar-color: #ffb4a8 transparent;
}
</style>
