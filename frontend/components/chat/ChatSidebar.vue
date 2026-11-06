<!-- 聊天侧边栏组件：显示聊天關鍵指令和版本歷史 -->
<template>
  <div class="flex h-screen flex-col rounded-[32px] bg-white shadow-lg">
    <div class="flex flex-[0.7] flex-col overflow-hidden border-b border-slate-200">
      <div class="flex-shrink-0 px-5 py-4">
        <p class="text-base font-semibold text-slate-900">關鍵指令</p>
        <!-- 生成前確認：逐段確認 AI 生成的答案，全部確認後才能輸出完整推演 -->
        <div
          v-if="reviewFieldIds"
          class="mt-3 rounded-2xl border border-slate-200 bg-white p-3"
        >
          <div class="flex items-center justify-between gap-2">
            <p class="text-[0.9375rem] font-semibold text-slate-900">
              確認 AI 生成內容
            </p>
            <button
              type="button"
              class="flex-shrink-0 text-xs text-slate-500 underline hover:text-slate-700"
              @click="$emit('clearReviewFilter')"
            >
              離開
            </button>
          </div>
          <div class="mt-2 flex items-center justify-between text-sm">
            <span class="text-slate-700">
              已確認
              <span class="font-semibold text-slate-900"
                >{{ reviewConfirmedCount }} / {{ reviewTotal }}</span
              >
              段
            </span>
            <span class="text-xs text-slate-500">
              {{ reviewRemaining > 0 ? `還有 ${reviewRemaining} 段` : "全部完成" }}
            </span>
          </div>
          <div class="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-200">
            <div
              class="h-full rounded-full bg-emerald-600 transition-all duration-300"
              :style="{ width: `${reviewProgressPercent}%` }"
            ></div>
          </div>
          <div class="mt-3 flex gap-2">
            <button
              v-for="tab in reviewTabs"
              :key="tab.value"
              type="button"
              class="rounded-full border px-3 py-1 text-sm font-medium transition"
              :class="
                reviewTab === tab.value
                  ? 'border-slate-900 bg-slate-900 text-white'
                  : 'border-slate-300 bg-white text-slate-600 hover:border-slate-400'
              "
              @click="reviewTab = tab.value"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>
      </div>
      <div
        ref="answerListRef"
        class="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 pb-4 pr-3 scrollbar-thin scrollbar-thumb-rose-300 scrollbar-track-transparent"
      >
        <!-- Phase 3: once the backend has sent an applicable_questions list
             (ready/filled), render the answered applicable questions grouped
             by section in schema order; unanswered questions stay hidden
             until they get an answer. -->
        <template v-if="applicableQuestionIds !== null">
          <div
            v-for="section in groupedSections"
            :key="section.sectionName"
            class="space-y-2"
          >
            <p
              class="text-sm font-semibold uppercase tracking-[0.1em] text-slate-500"
            >
              {{ section.sectionName }}
            </p>
            <SidebarAnswerCard
              v-for="item in section.items"
              :key="item.id"
              :data-question-id="item.id"
              :title="item.questionTitle"
              :answer="item.answer"
              :is-ai-generated="item.isAiGenerated"
              :ai-badge-title="item.aiBadgeTitle"
              :review-state="reviewState(item.id)"
              @expand="openAnswerView({ questionId: item.id, questionLabel: item.fullLabel, answer: item.answer, isAiGenerated: item.isAiGenerated, aiBadgeTitle: item.aiBadgeTitle })"
              @open="openReview(item.id)"
            />
          </div>
          <div v-if="!groupedSections.length" class="py-6 text-center">
            <p class="text-sm text-slate-500">尚無已回答題目</p>
          </div>
        </template>

        <!-- Legacy fallback (QUESTION_CONTROL_ENABLED off, or before the
             first `ready` event): answered-only flat list, unchanged. -->
        <template v-else>
          <SidebarAnswerCard
            v-for="item in qaItems"
            :key="item.id"
            :data-question-id="item.id"
            :title="item.questionLabel"
            :answer="item.answer"
            :is-ai-generated="item.isAiGenerated"
            :ai-badge-title="item.aiBadgeTitle"
            :review-state="reviewState(item.id)"
            @expand="openAnswerView({ questionId: item.id, questionLabel: item.questionLabel, answer: item.answer, isAiGenerated: item.isAiGenerated, aiBadgeTitle: item.aiBadgeTitle })"
            @open="openReview(item.id)"
          />
          <div v-if="!qaItems.length" class="py-6 text-center">
            <p class="text-sm text-slate-500">尚無詢問記錄</p>
          </div>
        </template>
      </div>
      <div
        v-if="reviewFieldIds"
        class="flex-shrink-0 border-t border-slate-200 px-5 py-3"
        :class="reviewRemaining === 0 ? 'bg-emerald-50/60' : ''"
      >
        <button
          v-if="reviewRemaining > 0"
          type="button"
          class="w-full rounded-xl border-2 border-rose-300 bg-rose-50 py-2 text-sm font-semibold text-rose-600 transition hover:bg-rose-100"
          @click="openReview()"
        >
          開始逐段檢查（還有 {{ reviewRemaining }} 段）
        </button>
        <p v-else class="text-sm font-semibold text-emerald-700">
          ✓ {{ reviewTotal }} 段 AI 內容都已確認，可以輸出完整推演了。
        </p>
        <button
          type="button"
          class="mt-2 w-full rounded-xl px-5 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed"
          :class="
            reviewRemaining === 0 && canRequestPlan
              ? 'bg-gradient-to-r from-[#ff9b6d] to-[#ff4b6b] text-white shadow-lg shadow-[#ff4b6b]/30'
              : 'bg-slate-200 text-slate-400'
          "
          :disabled="reviewRemaining > 0 || !canRequestPlan"
          @click="$emit('requestGeneration')"
        >
          輸出完整推演（{{ reviewConfirmedCount }} / {{ reviewTotal }}）
        </button>
      </div>
    </div>

    <div class="flex-[0.3] overflow-hidden">
      <div class="px-5 py-4">
        <p class="text-base font-semibold text-slate-900">版本記錄</p>
      </div>
      <div
        class="max-h-[calc(100%-3.5rem)] space-y-2 overflow-y-auto px-5 pb-4 pr-3 scrollbar-thin scrollbar-thumb-rose-300 scrollbar-track-transparent"
      >
        <div
          v-for="version in versions"
          :key="version.id"
          role="button"
          tabindex="0"
          class="group w-full flex cursor-pointer items-start gap-2 rounded-2xl bg-slate-50 p-3 text-left transition hover:bg-slate-100 hover:shadow-md"
          @click="editingVersionId !== version.id && $emit('selectVersion', version)"
          @keydown.enter.self="$emit('selectVersion', version)"
        >
          <span
            class="mt-0.5 inline-flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-[#fff1ea] text-sm font-semibold text-[#ff6b3d]"
          >
            {{ version.number }}
          </span>
          <div class="min-w-0 flex-1">
            <input
              v-if="editingVersionId === version.id"
              ref="versionTitleInput"
              v-model="editingVersionTitle"
              type="text"
              maxlength="50"
              class="w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-sm font-semibold text-slate-800 focus:border-[#ff6b3d] focus:outline-none"
              @click.stop
              @keydown.enter.prevent="commitRenameVersion(version)"
              @keydown.esc.prevent="cancelRenameVersion"
              @blur="commitRenameVersion(version)"
            />
            <p v-else class="truncate text-sm font-semibold text-slate-800">
              {{ version.title }}
            </p>
            <p class="mt-1 text-xs text-slate-500" v-show="!hideDateTime">
              {{ version.timestamp }}
            </p>
          </div>
          <div
            v-if="!isReadOnly && editingVersionId !== version.id"
            class="flex flex-shrink-0 items-center gap-0.5 self-center"
          >
            <button
              type="button"
              class="rounded-lg p-1.5 text-slate-400 transition hover:bg-white hover:text-slate-700"
              title="重新命名"
              @click.stop="startRenameVersion(version)"
            >
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15.232 5.232l3.536 3.536M9 13l6.232-6.232a2.5 2.5 0 113.536 3.536L12.536 16.536 9 17l.464-3.536z"
                />
              </svg>
            </button>
            <button
              type="button"
              class="rounded-lg p-1.5 text-slate-400 transition hover:bg-white hover:text-rose-500"
              title="刪除版本"
              @click.stop="$emit('deleteVersion', version)"
            >
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </div>
        <div v-if="!versions.length" class="py-6 text-center">
          <p class="text-sm text-slate-500">尚無版本記錄</p>
        </div>
      </div>
    </div>

    <ViewAnswerModal
      v-model:is-open="isAnswerViewOpen"
      title="查看欄位"
      :label="answerViewItem?.questionLabel || ''"
      :answer="answerViewItem?.answer || ''"
      :is-ai-generated="answerViewItem?.isAiGenerated || false"
      :ai-badge-title="answerViewItem?.aiBadgeTitle || ''"
      :is-read-only="isReadOnly"
      @regenerate="handleAnswerViewRegenerate"
      @edit="handleAnswerViewEdit"
    />

    <ReviewAnswersModal
      v-model:is-open="isReviewOpen"
      v-model:current-id="reviewCurrentId"
      :items="reviewModalItems"
      :can-edit="canSendMessage"
      :is-read-only="isReadOnly"
      @confirm="$emit('confirmAnswer', $event)"
      @unconfirm="$emit('unconfirmAnswer', $event)"
      @regenerate="$emit('regenerateQuestion', $event)"
      @save-edit="$emit('saveFieldEdit', $event)"
    />
  </div>
</template>

<script setup lang="ts">
const { hideDateTime } = useDateTimeVisibility();
import { computed, nextTick, onMounted, ref, watch } from "vue";
import ViewAnswerModal from "~/components/chat/helper/ViewAnswerModal.vue";
import SidebarAnswerCard from "~/components/chat/helper/SidebarAnswerCard.vue";
import ReviewAnswersModal from "~/components/chat/helper/ReviewAnswersModal.vue";
import type { ReviewItem } from "~/components/chat/helper/ReviewAnswersModal.vue";

interface AnswerProvenance {
  source?: string;
  needs_review?: boolean;
  review_note?: string;
  confirmed?: boolean;
}

interface QAItem {
  id: string;
  questionLabel: string;
  answer: string;
  updatedAt?: string;
  isAiGenerated: boolean;
  aiBadgeTitle: string;
}

interface VersionRecord {
  id: string;
  number: number;
  title: string;
  timestamp: string;
}

interface GuidedQuestion {
  id: string;
  label: string;
  prompt?: string;
}

interface GroupedItem {
  id: string;
  fullLabel: string;
  questionTitle: string;
  answer: string;
  isAiGenerated: boolean;
  aiBadgeTitle: string;
}

interface GroupedSection {
  sectionName: string;
  items: GroupedItem[];
}

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
  versions: {
    type: Array as () => VersionRecord[],
    default: () => [],
  },
  questionAnswers: {
    type: Object as () => Record<string, string>,
    default: () => {},
  },
  questionAnswerMeta: {
    type: Object as () => Record<string, { updated_at?: string }>,
    default: () => ({}),
  },
  questionAnswerProvenance: {
    type: Object as () => Record<string, AnswerProvenance>,
    default: () => ({}),
  },
  // Full guided-question definitions (id/label), unfiltered — used to look up
  // section/title text for whichever ids are currently applicable.
  guidedQuestions: {
    type: Array as () => GuidedQuestion[],
    default: () => [],
  },
  // Backend-computed applicable question ids from the `ready`/`filled` WS
  // events (Phase 3). null means "not known yet" (QUESTION_CONTROL_ENABLED
  // off, or before the first `ready` event) — falls back to the legacy
  // answered-only qaItems view below.
  applicableQuestionIds: {
    type: Array as () => string[] | null,
    default: null,
  },
  reviewFieldIds: {
    type: Array as () => string[] | null,
    default: null,
  },
  // 已送出確認、等待後端回覆的欄位
  confirmingFieldIds: {
    type: Array as () => string[],
    default: () => [],
  },
  canRequestPlan: {
    type: Boolean,
    default: false,
  },
  // AI 回覆中不能重新生成／編輯
  canSendMessage: {
    type: Boolean,
    default: false,
  },
  isReadOnly: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits([
  "selectVersion",
  "renameVersion",
  "deleteVersion",
  "editQuestion",
  "regenerateQuestion",
  "clearReviewFilter",
  "confirmAnswer",
  "unconfirmAnswer",
  "requestGeneration",
  "saveFieldEdit",
]);

// ===== 版本重新命名（行內編輯）=====
const editingVersionId = ref<string | null>(null);
const editingVersionTitle = ref("");
const versionTitleInput = ref<HTMLInputElement[]>([]);

async function startRenameVersion(version: VersionRecord) {
  editingVersionId.value = version.id;
  editingVersionTitle.value = version.title;
  await nextTick();
  const input = versionTitleInput.value[0];
  input?.focus();
  input?.select();
}

function cancelRenameVersion() {
  editingVersionId.value = null;
  editingVersionTitle.value = "";
}

function commitRenameVersion(version: VersionRecord) {
  // Enter 之後 blur 會再觸發一次，已結束編輯則忽略
  if (editingVersionId.value !== version.id) return;
  const title = editingVersionTitle.value.trim();
  cancelRenameVersion();
  if (title && title !== version.title) {
    emit("renameVersion", { version, title });
  }
}

// ===== 關鍵指令卡片「展開」：以模態框查看完整答案 =====
// 卡片只顯示固定高度的答案；重新生成／編輯按鈕只在模態框內出現
interface AnswerViewItem {
  questionId: string;
  questionLabel: string;
  answer: string;
  isAiGenerated: boolean;
  aiBadgeTitle: string;
}

const isAnswerViewOpen = ref(false);
const answerViewItem = ref<AnswerViewItem | null>(null);

function openAnswerView(item: AnswerViewItem) {
  answerViewItem.value = item;
  editFromAnswerView.value = false;
  isAnswerViewOpen.value = true;
}

function handleAnswerViewRegenerate() {
  const item = answerViewItem.value;
  if (!item) return;
  emit("regenerateQuestion", {
    questionId: item.questionId,
    questionLabel: item.questionLabel,
  });
}

// 記錄編輯是否由模態框發起，取消編輯時才返回模態框
const editFromAnswerView = ref(false);

function handleAnswerViewEdit() {
  const item = answerViewItem.value;
  if (!item) return;
  editFromAnswerView.value = true;
  emit("editQuestion", {
    questionId: item.questionId,
    questionLabel: item.questionLabel,
    answer: item.answer,
  });
}

// 外層在使用者取消編輯時呼叫：重新打開同一欄位的查看模態框
function reopenAnswerView() {
  if (!editFromAnswerView.value || !answerViewItem.value) return;
  editFromAnswerView.value = false;
  isAnswerViewOpen.value = true;
}

defineExpose({ reopenAnswerView, openReview: () => openReview() });

// ===== 生成前確認模式（reviewFieldIds 有值時）=====
const reviewFilterSet = computed(() =>
  props.reviewFieldIds ? new Set(props.reviewFieldIds) : null,
);

type ReviewTab = "ai" | "all";
const reviewTab = ref<ReviewTab>("ai");
// 每次進入確認模式都先顯示 AI 生成的欄位（確認模式中新增欄位時不重設）
watch(
  () => props.reviewFieldIds,
  (ids, oldIds) => {
    if (ids && !oldIds) reviewTab.value = "ai";
  },
);

// 仍有答案的確認欄位（答案被清空的不列入）
const reviewItemIds = computed(() =>
  (props.reviewFieldIds || []).filter((id) =>
    String((props.questionAnswers || {})[id] || "").trim(),
  ),
);

const reviewTabs = computed(() => [
  { value: "ai" as ReviewTab, label: `AI 生成（${reviewItemIds.value.length}）` },
  { value: "all" as ReviewTab, label: "全部欄位" },
]);

function passesReviewFilter(questionId: string) {
  return (
    !reviewFilterSet.value ||
    reviewTab.value === "all" ||
    reviewFilterSet.value.has(questionId)
  );
}

// pending：AI 生成、待確認；confirmed：已確認，或已改成使用者自己的答案；null：不在確認清單
function reviewState(questionId: string): "pending" | "confirmed" | null {
  if (!reviewFilterSet.value?.has(questionId)) return null;
  const provenance = (props.questionAnswerProvenance || {})[questionId];
  return provenance && !provenance.confirmed ? "pending" : "confirmed";
}

// ===== 確認視窗：逐段檢查完整內容，確認／重新生成／編輯 =====
const isReviewOpen = ref(false);
const reviewCurrentId = ref<string | null>(null);

// 確認清單（依題目順序，不受分頁篩選影響）
const reviewModalItems = computed<ReviewItem[]>(() => {
  const ids = new Set(reviewItemIds.value);
  const questionById = new Map(
    (props.guidedQuestions || []).map((q) => [q.id, q] as const),
  );
  const orderedIds = [
    ...(props.guidedQuestions || []).map((q) => q.id).filter((id) => ids.has(id)),
    ...reviewItemIds.value.filter((id) => !questionById.has(id)),
  ];
  return orderedIds.map((id) => {
    const fullLabel = questionById.get(id)?.label || id;
    const separatorIndex = fullLabel.indexOf("｜");
    const state = reviewState(id) === "pending" ? "pending" : "confirmed";
    return {
      id,
      section: separatorIndex >= 0 ? fullLabel.slice(0, separatorIndex) : "",
      title: separatorIndex >= 0 ? fullLabel.slice(separatorIndex + 1) : fullLabel,
      fullLabel,
      answer: String((props.questionAnswers || {})[id] || ""),
      isAiGenerated: aiBadgeState(id).isAiGenerated,
      state,
      canUnconfirm: confirmControlState(id) === "confirmed",
      busy: isConfirming(id),
    };
  });
});

// 打開確認視窗：指定欄位，或第一段待確認
function openReview(questionId?: string) {
  const items = reviewModalItems.value;
  if (!items.length) return;
  reviewCurrentId.value =
    questionId ||
    items.find((item) => item.state === "pending")?.id ||
    items[0].id;
  isReviewOpen.value = true;
}

// 進入確認模式時直接打開視窗；離開時關閉。確認模式中清單新增欄位時不自動打開
watch(
  () => props.reviewFieldIds,
  async (ids, oldIds) => {
    if (!ids) {
      isReviewOpen.value = false;
      return;
    }
    if (oldIds) return;
    await nextTick();
    openReview();
  },
);

// 已改成使用者自己的答案時不必確認，也就不顯示「取消確認」
function confirmControlState(questionId: string) {
  const state = reviewState(questionId);
  const provenance = (props.questionAnswerProvenance || {})[questionId];
  return state === "confirmed" && !provenance ? null : state;
}

function isConfirming(questionId: string) {
  return props.confirmingFieldIds.includes(questionId);
}

const reviewTotal = computed(() => reviewItemIds.value.length);
const reviewConfirmedCount = computed(
  () =>
    reviewItemIds.value.filter((id) => reviewState(id) === "confirmed").length,
);
const reviewRemaining = computed(
  () => reviewTotal.value - reviewConfirmedCount.value,
);
const reviewProgressPercent = computed(() =>
  reviewTotal.value
    ? Math.round((reviewConfirmedCount.value / reviewTotal.value) * 100)
    : 100,
);

function aiBadgeState(questionId: string) {
  const provenance = (props.questionAnswerProvenance || {})[questionId];
  const isAiGenerated = provenance?.source === "ai_generated";
  const aiBadgeTitle = provenance?.needs_review
    ? provenance.review_note || "AI 生成，請確認"
    : "由 AI 生成";
  return { isAiGenerated, aiBadgeTitle };
}

// 計算屬性：將問題答案轉換為顯示格式，支持按中文數字排序和提取 Label
const qaItems = computed(() => {
  const items: QAItem[] = [];
  const answers = props.questionAnswers || {};
  const metaMap = props.questionAnswerMeta || {};

  // 中文数字顺序映射
  const chineseNumberOrder: Record<string, number> = {
    一: 1,
    二: 2,
    三: 3,
    四: 4,
    五: 5,
    六: 6,
    七: 7,
    八: 8,
    九: 9,
    十: 10,
  };

  // 先提取所有key-value对，计算label
  const tempItems: Array<{
    key: string;
    label: string;
    answer: string;
    updatedAt?: string;
  }> = [];

  Object.entries(answers).forEach(([key, value]) => {
    const answer = String(value || "").trim();
    if (answer && passesReviewFilter(key)) {
      // 提取label：保留第一個"::"之前的所有文字（通常為章節名稱）
      let label = key;
      const firstDoubleColonIndex = key.indexOf("::");
      if (firstDoubleColonIndex !== -1) {
        label = key.substring(0, firstDoubleColonIndex);
      }

      const meta = metaMap[key] || {};
      const updatedAt = meta.updated_at || "";
      tempItems.push({ key, label, answer, updatedAt });
    }
  });

  tempItems.sort((a, b) => {
    const aTime = a.updatedAt ? Date.parse(a.updatedAt) || 0 : 0;
    const bTime = b.updatedAt ? Date.parse(b.updatedAt) || 0 : 0;
    if (aTime !== bTime) {
      return bTime - aTime;
    }
    const aFirstChar = a.label.charAt(0);
    const bFirstChar = b.label.charAt(0);
    const aOrder = chineseNumberOrder[aFirstChar] ?? 999;
    const bOrder = chineseNumberOrder[bFirstChar] ?? 999;
    if (aOrder !== bOrder) {
      return aOrder - bOrder;
    }
    return a.label.localeCompare(b.label, "zh-Hant");
  });

  // 排序后再push到items
  tempItems.forEach(({ key, label, answer, updatedAt }) => {
    items.push({
      id: key,
      questionLabel: label,
      answer: answer,
      updatedAt,
      ...aiBadgeState(key),
    });
  });

  return items;
});

// Phase 3: answered applicable questions grouped by section — natural schema
// order (guidedQuestions is already section.order/field.order from the
// backend). Unanswered questions are left out until they get an answer.
const groupedSections = computed<GroupedSection[]>(() => {
  const ids = props.applicableQuestionIds;
  if (!ids) {
    return [];
  }
  const applicableSet = new Set(ids);
  const answers = props.questionAnswers || {};
  const sectionByName = new Map<string, GroupedSection>();
  const sections: GroupedSection[] = [];

  (props.guidedQuestions || []).forEach((q) => {
    if (!applicableSet.has(q.id) || !passesReviewFilter(q.id)) {
      return;
    }
    const rawAnswer = answers[q.id];
    const answer = rawAnswer ? String(rawAnswer).trim() : "";
    if (!answer) {
      return;
    }
    const separatorIndex = q.label.indexOf("｜");
    const sectionName =
      separatorIndex >= 0 ? q.label.slice(0, separatorIndex) : q.label;
    const questionTitle =
      separatorIndex >= 0 ? q.label.slice(separatorIndex + 1) : q.label;

    let section = sectionByName.get(sectionName);
    if (!section) {
      section = { sectionName, items: [] };
      sectionByName.set(sectionName, section);
      sections.push(section);
    }

    section.items.push({
      id: q.id,
      fullLabel: q.label,
      questionTitle,
      answer,
      ...aiBadgeState(q.id),
    });
  });

  return sections;
});

const answerListRef = ref<HTMLElement | null>(null);

const answeredIds = computed(() =>
  Object.entries(props.questionAnswers || {})
    .filter(([, value]) => String(value || "").trim())
    .map(([key]) => key),
);

function scrollAnswerList(card: HTMLElement | null, smooth: boolean) {
  const container = answerListRef.value;
  if (!container) return;
  const top = card
    ? card.getBoundingClientRect().top -
      container.getBoundingClientRect().top +
      container.scrollTop -
      8
    : container.scrollHeight;
  container.scrollTo({ top, behavior: smooth ? "smooth" : "auto" });
}

let initialScrollDone = false;

function scrollToBottomOnFirstRender() {
  if (!groupedSections.value.length) {
    if (!answeredIds.value.length) initialScrollDone = false;
    return;
  }
  if (initialScrollDone) return;
  initialScrollDone = true;
  scrollAnswerList(null, false);
}

onMounted(scrollToBottomOnFirstRender);
watch(() => groupedSections.value.length, scrollToBottomOnFirstRender, {
  flush: "post",
});

watch(
  answeredIds,
  async (ids, oldIds) => {
    if (!oldIds?.length) return;
    const oldSet = new Set(oldIds);
    const added = new Set(ids.filter((id) => !oldSet.has(id)));
    if (!added.size) return;
    await nextTick();
    const container = answerListRef.value;
    if (!container) return;
    const cards = Array.from(
      container.querySelectorAll<HTMLElement>("[data-question-id]"),
    ).filter((card) => added.has(card.dataset.questionId || ""));
    scrollAnswerList(cards[cards.length - 1] || null, true);
  },
);
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thumb-rose-300::-webkit-scrollbar-thumb {
  background-color: #ffb4a8;
  border-radius: 3px;
}

.scrollbar-thumb-rose-300::-webkit-scrollbar-thumb:hover {
  background-color: #ff998e;
}

.scrollbar-track-transparent::-webkit-scrollbar-track {
  background-color: transparent;
  border-radius: 3px;
}

.scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: #ffb4a8 transparent;
}
</style>
