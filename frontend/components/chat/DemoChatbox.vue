<template>
  <div class="flex h-screen gap-4">
    <div class="flex-1 h-full relative">
      <div class="flex h-full min-h-0 flex-col rounded-[32px] bg-[#f7f8fc] shadow-2xl">
        <!-- Header -->
        <header class="flex flex-wrap items-center justify-between gap-4 rounded-3xl bg-white px-6 py-2 shadow-lg">
          <div class="flex items-center gap-4">
            <span class="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#ffb067] via-[#ff7a66] to-[#ff4b5c] text-base font-semibold text-white">
              AI
            </span>
            <div>
              <div class="flex items-center gap-2">
                <p class="text-lg font-semibold text-slate-900">補助引擎</p>
                <span class="hidden sm:inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-[0.6875rem] font-bold uppercase tracking-wide text-amber-600 border border-amber-100">
                  Demo
                </span>
              </div>
              <p class="flex items-center gap-2 text-xs text-slate-400">
                <span class="flex flex-1 h-2 w-2 rounded-full bg-green-500 shadow-lg shadow-green-500/50"></span>
                智慧推演進行中 · {{ activeGrantName }}
                <span v-if="activeTemplateName">/ {{ activeTemplateName }}</span>
              </p>
            </div>
          </div>
        </header>

        <!-- Chat area -->
        <div class="mt-6 flex-1 min-h-0">
          <div ref="chatContainer" class="h-full space-y-4 overflow-y-auto pr-3 scrollbar-thin scrollbar-thumb-rose-300 scrollbar-track-transparent">
            <div
              v-for="message in messages"
              :key="message.id"
              class="flex"
              :class="message.role === 'user' ? 'justify-end pl-12' : 'justify-start pr-12'"
            >
              <div class="flex max-w-3xl flex-1 px-2 gap-3" :class="message.role === 'user' ? 'flex-row-reverse' : 'flex-row'">
                <span v-if="message.role !== 'user'" class="mt-1 inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-[#fff1ea] text-sm font-semibold text-[#ff6b3d]">
                  AI
                </span>
                <div class="flex-1 space-y-3">
                  <template v-if="message.type === 'text'">
                    <article :class="[
                      'px-5 py-4 rounded-[28px] shadow-md',
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-[#ff9b6d] to-[#ff4b6b] text-white shadow-lg'
                        : 'border border-[#f0f2ff] bg-white text-slate-700',
                    ]">
                      <p class="text-sm leading-relaxed" v-html="formatMessageForDisplay(message.content)"></p>
                    </article>
                  </template>
                </div>
              </div>
            </div>

            <div v-if="isFetchingNextQuestion && !isGenerationComplete" class="flex items-center justify-center gap-2 pt-4 text-xs text-slate-400">
              <span class="h-2.5 w-2.5 animate-ping rounded-full bg-[#ffb4a8]"></span>
              AI 正在構思下一個提問...
            </div>
          </div>
        </div>

        <!-- Composer footer -->
        <footer class="mt-2 rounded-[32px] bg-white px-5 py-5 shadow-xl">
          <!-- 生成前確認模式：提示使用者到右側逐段確認，並顯示確認進度 -->
          <div
            v-if="reviewFieldIds"
            class="mb-3 flex items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600"
            role="status"
          >
            <span class="flex-shrink-0 font-semibold">確認模式</span>
            <p class="min-w-0 truncate">請在右側逐段檢查 AI 生成的內容</p>
            <div class="h-1.5 w-28 flex-shrink-0 overflow-hidden rounded-full bg-rose-200">
              <div
                class="h-full rounded-full bg-rose-500 transition-all duration-300"
                :style="{ width: `${reviewProgressPercent}%` }"
              ></div>
            </div>
            <span class="flex-shrink-0 tabular-nums">
              {{ reviewConfirmedCount }} / {{ reviewTotal }}
            </span>
            <button
              v-if="unconfirmedReviewCount > 0"
              type="button"
              class="ml-auto flex-shrink-0 font-semibold underline hover:text-rose-700"
              @click="chatSidebarRef?.openReview()"
            >
              開始檢查
            </button>
            <button
              type="button"
              class="flex-shrink-0 font-medium underline hover:text-rose-700"
              :class="unconfirmedReviewCount > 0 ? '' : 'ml-auto'"
              @click="reviewFieldIds = null"
            >
              先離開確認
            </button>
          </div>
          <!-- 常駐提示：引導使用者到右側「關鍵指令」卡片的「重新生成」/「編輯」調整欄位 -->
          <div v-else class="mb-3 flex items-start gap-2 rounded-xl bg-amber-50/50 px-3 py-2 text-xs text-amber-700/80" role="note">
            <span class="text-sm leading-none opacity-80">💡</span>
            <p class="flex-1 leading-relaxed">
              提醒：想調整某個欄位，可至右側「關鍵指令」，點擊該欄位的「展開」，即可進行重新生成或編輯。
            </p>
          </div>

          <!-- Soft-limit notices (no numbers shown) -->
          <div v-if="chatLimitReached" class="mb-3 rounded-xl bg-slate-100 px-4 py-3 text-center text-sm text-slate-600">
            體驗次數已達上限，<button class="font-semibold text-rose-600 hover:underline" @click="$emit('register')">免費註冊</button>以繼續使用。
          </div>
          <div v-else-if="generationLimitReached" class="mb-3 rounded-xl bg-slate-100 px-4 py-3 text-center text-sm text-slate-600">
            報告生成次數已達上限，<button class="font-semibold text-rose-600 hover:underline" @click="$emit('register')">免費註冊</button>以繼續使用。
          </div>
          <div v-else-if="downloadLimitReached" class="mb-3 rounded-xl bg-slate-100 px-4 py-3 text-center text-sm text-slate-600">
            下載次數已達上限，<button class="font-semibold text-rose-600 hover:underline" @click="$emit('register')">免費註冊</button>以繼續使用。
          </div>

          <div class="relative">
            <textarea
              ref="composerRef"
              v-model="draftMessage"
              class="mt-3 w-full min-h-16 resize-none rounded-[28px] border border-[#edf0ff] bg-[#f8f9ff] p-4 pr-14 text-sm text-slate-700 placeholder-slate-400 outline-none focus:border-[#ff4b5c] focus:bg-white focus:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 transition-all overflow-hidden"
              :placeholder="composerPlaceholder"
              :disabled="isReadOnly"
              @keydown.enter.prevent="handleEnter"
              @input="handleTextareaInput"
              @compositionstart="handleCompositionStart"
              @compositionupdate="handleCompositionUpdate"
              @compositionend="handleCompositionEnd"
            ></textarea>
            <button
              type="button"
              class="absolute right-6 bottom-5 flex h-10 w-10 items-center justify-center rounded-2xl border border-[#e4e7ff] bg-white text-[#ff6b6b] shadow hover:bg-[#fff6f6] disabled:cursor-not-allowed disabled:opacity-40"
              :disabled="true"
              title="註冊後可使用檔案匯入功能"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 12.79V7.5a4.5 4.5 0 00-9 0v9a3 3 0 006 0v-7.5" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 12v5.5a4.5 4.5 0 008.8 1.5" />
              </svg>
            </button>
          </div>
          <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
            <div class="flex flex-wrap gap-3">
              <button
                type="button"
                class="rounded-full bg-gradient-to-r from-[#ffd5c4] to-[#ffb8a8] px-5 py-2 text-sm font-semibold text-[#c44536] shadow-md shadow-[#ffb8a8]/30 hover:shadow-lg hover:from-[#ffc9b5] hover:to-[#ffaa99] disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="!canSendMessage"
                @click="() => handleSend(true)"
              >
                由AI自動幫忙填寫
              </button>
            </div>
            <div class="flex flex-wrap items-center gap-3">
              <span class="text-xs text-slate-400 font-semibold flex items-center gap-1.5 select-none mr-2">
                <span>✨</span>
                <span>免費體驗僅提供一次輸出機會</span>
              </span>
              <button
                type="button"
                class="rounded-full bg-gradient-to-r from-[#ff9b6d] to-[#ff4b6b] px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-[#ff4b6b]/30 disabled:cursor-not-allowed disabled:opacity-50 h-10 flex items-center justify-center"
                :disabled="!canRequestPlan || isStreaming"
                @click="requestGeneration()"
              >
                {{ isStreaming ? '推演中...' : '輸出完整推演' }}
                <span
                  v-if="!isStreaming && unconfirmedReviewCount > 0"
                  class="ml-1.5 rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-[#ff4b6b]"
                >
                  待確認 {{ unconfirmedReviewCount }}
                </span>
              </button>
              <button
                v-if="!isFetchingNextQuestion"
                type="button"
                class="rounded-full border border-[#dfe3ff] px-5 py-2 text-sm font-semibold text-[#6c719b] hover:bg-[#f4f5ff] disabled:cursor-not-allowed disabled:opacity-50 h-10 flex items-center justify-center"
                :disabled="!canSendMessage"
                @click="handleSend(false)"
              >
                回覆當前問題
              </button>
              <button
                v-if="isFetchingNextQuestion"
                type="button"
                class="rounded-full border border-red-400 bg-white px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 h-10 flex items-center justify-center"
                @click="handlePause"
                title="停止/取消目前的 AI 回覆"
              >
                停止/取消
              </button>
            </div>
          </div>
        </footer>
      </div>
    </div>

    <!-- Right sidebar: Q&A tracker + version history -->
    <div class="h-full w-full max-w-sm flex-shrink-0">
      <ChatSidebar
        ref="chatSidebarRef"
        :messages="messages"
        :versions="props.savedPlanVersions"
        :question-answers="questionAnswers"
        :question-answer-meta="questionAnswerMeta"
        :question-answer-provenance="questionAnswerProvenance"
        :guided-questions="props.allQuestions"
        :applicable-question-ids="applicableQuestionIds"
        :review-field-ids="reviewFieldIds"
        :confirming-field-ids="confirmingFieldIds"
        :can-request-plan="canRequestPlan && !isStreaming"
        :can-send-message="canSendMessage"
        :is-read-only="isReadOnly"
        @selectVersion="handleVersionSelect"
        @renameVersion="emit('renameVersion', $event)"
        @deleteVersion="handleVersionDelete"
        @editQuestion="handleEditQuestion"
        @regenerateQuestion="handleRegenerateQuestion"
        @clearReviewFilter="reviewFieldIds = null"
        @confirmAnswer="sendAnswerConfirmation([$event], true)"
        @unconfirmAnswer="sendAnswerConfirmation([$event], false)"
        @requestGeneration="requestGeneration({ missingAnswersAccepted: true })"
        @saveFieldEdit="handleSidebarFieldEdit"
      />
    </div>

    <!-- Edit field modal -->
    <EditFieldModal
      v-model:is-open="isEditFieldModalOpen"
      title="編輯欄位"
      :label="editFieldLabel"
      :initial-value="editFieldInitialValue"
      @confirm="handleEditConfirm"
      @cancel="chatSidebarRef?.reopenAnswerView()"
    />

    <!-- Recommend project name modal -->
    <RecommendNameModal
      v-model:is-open="isRecommendModalOpen"
      :original-name="props.projectTitle"
      :suggestions="recommendOptions"
      :loading="isFetchingRecommend"
      @confirm="handleRecommendConfirm"
    />

    <!-- 生成前檢查：AI 生成的答案是否已確認 -->
    <ExportReadinessModal
      v-model:is-open="isExportReadinessOpen"
      :readiness="exportReadiness"
      @proceed="handleExportReadinessProceed"
      @review="handleExportReadinessReview"
    />

    <!-- Generated plan candidate picker -->
    <PlanCandidateSelector
      :visible="isCandidateSelectorVisible"
      :candidate-plan="props.candidatePlan"
      :sections="props.sections"
      @confirm="handleCandidateConfirm"
      @close="isCandidateSelectorVisible = false"
    />

    <!-- Version detail modal -->
    <PlanVersionModal
      :visible="isVersionModalVisible"
      :version="selectedVersion"
      :plan-sections="props.sections"
      :loading="false"
      :timeline-loading="false"
      :is-internal="false"
      :generation-limit-reached="props.generationLimitReached"
      :download-limit-reached="props.downloadLimitReached"
      :grant-id="props.grantId"
      :template-id="props.templateId"
      :project-title="props.projectTitle"
      :project-created-at="props.projectCreatedAt"
      :project-section-versions="props.sectionVersions"
      @close="isVersionModalVisible = false"
      @export="handleVersionExport"
      @updateVersion="handleVersionUpdateRequest"
    />

  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import ChatSidebar from "~/components/chat/ChatSidebar.vue";
import EditFieldModal from "~/components/chat/helper/EditFieldModal.vue";
import RecommendNameModal from "~/components/chat/helper/RecommendNameModal.vue";
import PlanCandidateSelector from "~/components/chat/helper/PlanCandidateSelector.vue";
import PlanVersionModal from "~/components/chat/helper/PlanVersionModal.vue";
import ExportReadinessModal from "~/components/chat/ExportReadinessModal.vue";
import { answerToEditText, editTextToAnswer } from "~/utils/answerParagraphs";
import { useConfirm } from "~/composables/useConfirm";
import { useNotifications } from "~/composables/useNotifications";
import { demoFetch } from "~/composables/useDemoSession";

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const props = defineProps({
  grantId: { type: String, default: "" },
  templateId: { type: String, default: "" },
  grantName: { type: String, default: "" },
  templateName: { type: String, default: "" },
  allQuestions: { type: Array, default: () => [] },
  sessionId: { type: String, default: "" },
  interactionCount: { type: Number, default: 0 },
  interactionLimit: { type: Number, default: 20 },
  chatLimitReached: { type: Boolean, default: false },
  generationLimitReached: { type: Boolean, default: false },
  downloadLimitReached: { type: Boolean, default: false },
  hasGeneratedDocx: { type: Boolean, default: false },
  conversationHistory: { type: Array, default: () => [] },
  storedAnswers: { type: Object, default: () => ({}) },
  storedAnswersMeta: { type: Object, default: () => ({}) },
  registerUrl: { type: String, default: "" },
  projectTitle: { type: String, default: "" },
  projectSummary: { type: String, default: "" },
  // 版本預覽需與 Word 下載選用同一份匯出設定
  projectCreatedAt: { type: String, default: "" },
  sections: { type: Array, default: () => [] },
  candidatePlan: { type: Object, default: () => ({}) },
  finalPlan: { type: Object, default: () => ({}) },
  savedPlanVersions: { type: Array, default: () => [] },
  sectionVersions: { type: Object, default: undefined },
});

const emit = defineEmits([
  "messagesUpdated",
  "questionAnswersUpdated",
  "aiResponseComplete",
  "generatePlan",
  "updateProjectTitle",
  "finalizeCandidates",
  "requestVersionUpdate",
  "renameVersion",
  "deleteVersion",
  "register",
  "downloadCompleted",
]);

const { confirm } = useConfirm();
const { success: notifySuccess, error: notifyError } = useNotifications();

// -- State --
const messages = ref([]);
const lastSentUserIndex = ref(null);
const questionAnswers = ref({});
const questionAnswerMeta = ref({});
const questionAnswerProvenance = ref({});
const applicableQuestionIds = ref(null);
const isExportReadinessOpen = ref(false);
const exportReadiness = ref(null);
const reviewFieldIds = ref(null);
// 已送出確認、等待後端回覆的欄位
const confirmingFieldIds = ref([]);
const chatContainer = ref(null);
const draftMessage = ref("");
const composerRef = ref(null);
const isEditFieldModalOpen = ref(false);
// 側邊欄元件實例：取消編輯時返回「展開」查看模態框
const chatSidebarRef = ref(null);
const editFieldLabel = ref("");
const editFieldInitialValue = ref("");
const editFieldQuestionId = ref(null);
const chatInitialized = ref(false);
const isStreaming = ref(false);
const isFetchingNextQuestion = ref(false);
const isGenerationComplete = ref(false);
const pausedFlag = ref(false);
const isRecommendModalOpen = ref(false);
const isFetchingRecommend = ref(false);
const recommendOptions = ref([]);
const isCandidateSelectorVisible = ref(false);
const lastCandidateSnapshot = ref("");
const isVersionModalVisible = ref(false);
const selectedVersion = ref(null);
const textareaMinHeight = 64;
const textareaMaxHeight = 184;

// -- Computed --
const isReadOnly = computed(() => props.chatLimitReached);

const totalQuestions = computed(() => props.allQuestions.length);
const answeredCount = computed(() =>
  props.allQuestions.reduce((count, q) => {
    const answer = questionAnswers.value[q.id];
    return answer && answer.trim() ? count + 1 : count;
  }, 0)
);
const allQuestionsAnswered = computed(() =>
  totalQuestions.value === 0 || answeredCount.value === totalQuestions.value
);

// 生成前確認：AI 生成且尚未確認的欄位（改成使用者自己的答案後就不必確認）
function needsConfirmation(fieldId) {
  const provenance = questionAnswerProvenance.value[fieldId];
  const answer = questionAnswers.value[fieldId];
  return Boolean(provenance && !provenance.confirmed && answer && String(answer).trim());
}
const unconfirmedReviewCount = computed(
  () => (reviewFieldIds.value || []).filter(needsConfirmation).length,
);
// 確認模式中 AI 新填寫的答案自動加入確認清單（與 export-readiness 相同：AI 生成或需確認）
watch(questionAnswerProvenance, (provenance) => {
  if (!reviewFieldIds.value) return;
  const known = new Set(reviewFieldIds.value);
  const added = Object.keys(provenance).filter(
    (fieldId) =>
      !known.has(fieldId) &&
      (provenance[fieldId]?.source === "ai_generated" || provenance[fieldId]?.needs_review) &&
      String(questionAnswers.value[fieldId] || "").trim(),
  );
  if (added.length) {
    reviewFieldIds.value = [...reviewFieldIds.value, ...added];
  }
});
// 確認模式進度（與側邊欄一致：只算仍有答案的欄位）
const reviewTotal = computed(
  () =>
    (reviewFieldIds.value || []).filter((fieldId) =>
      String(questionAnswers.value[fieldId] || "").trim(),
    ).length,
);
const reviewConfirmedCount = computed(() => reviewTotal.value - unconfirmedReviewCount.value);
const reviewProgressPercent = computed(() =>
  reviewTotal.value ? Math.round((reviewConfirmedCount.value / reviewTotal.value) * 100) : 100,
);

const activeGrantName = computed(() => props.grantName || "尚未選擇");
const activeTemplateName = computed(() => props.templateName || "");

const canSendMessage = computed(() =>
  Boolean(
    !props.chatLimitReached &&
    props.grantId &&
    props.templateId &&
    !isGenerationComplete.value &&
    !isFetchingNextQuestion.value
  )
);

const canRequestPlan = computed(() =>
  Boolean(
    props.grantId &&
    props.templateId &&
    !props.generationLimitReached
  )
);

const hasMissingAnswers = computed(() => !allQuestionsAnswered.value);

const composerPlaceholder = computed(() => {
  if (props.chatLimitReached) {
    return "體驗次數已達上限，免費註冊即可繼續使用。";
  }
  if (props.generationLimitReached && !props.hasGeneratedDocx) {
    return "報告生成次數已達上限，免費註冊即可繼續使用。";
  }
  if (!props.grantId || !props.templateId) {
    return "請先完成第一階段的設定";
  }
  if (isFetchingNextQuestion.value) {
    return "AI 正在思考...";
  }
  if (allQuestionsAnswered.value) {
    return "所有核心問題已完成，請輸出完整推演";
  }
  return "請輸入你的想法或回答 AI 的問題";
});

// -- Helpers --
function getCurrentTimestamp() {
  return new Date().toISOString();
}

function touchAnswerMeta(questionId, timestamp) {
  if (!questionId) return;
  const nextTimestamp = timestamp || getCurrentTimestamp();
  questionAnswerMeta.value = {
    ...questionAnswerMeta.value,
    [questionId]: { ...(questionAnswerMeta.value[questionId] || {}), updated_at: nextTimestamp },
  };
}

function setAnswerProvenance(fieldId, source, reviewNote) {
  if (!fieldId) return;
  const next = { ...questionAnswerProvenance.value };
  if ((source && source !== "user_input") || reviewNote) {
    next[fieldId] = {
      source: source || "user_input",
      needs_review: Boolean(reviewNote),
      review_note: reviewNote || "",
    };
  } else {
    delete next[fieldId];
  }
  questionAnswerProvenance.value = next;
}

function escapeHtml(unsafe) {
  return String(unsafe || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatMessageForDisplay(raw) {
  const text = raw == null ? "" : String(raw);
  let cleaned = text.replace(/【回復結束】[\s\S]*/g, "");
  let out = escapeHtml(cleaned);
  out = out.replace(/\*\*([\s\S]+?)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/\r\n|\n/g, "<br/>");
  return out;
}

function buildConversationHistoryPayload(limit = 8) {
  const simpleHistory = [];
  const allowedTypes = new Set(["text"]);
  messages.value
    .filter((msg) => allowedTypes.has(msg.type))
    .slice(-limit)
    .forEach((msg) => {
      let content = msg.content || "";
      if (!content.trim()) return;
      simpleHistory.push({ role: msg.role === "user" ? "user" : "assistant", content });
    });
  return simpleHistory;
}

function scrollToBottom() {
  nextTick(() => {
    if (!chatContainer.value) return;
    chatContainer.value.scrollTo({ top: chatContainer.value.scrollHeight, behavior: "smooth" });
  });
}

function resolveTextarea(target) {
  if (target instanceof HTMLTextAreaElement) return target;
  if (target?.target instanceof HTMLTextAreaElement) return target.target;
  return composerRef.value;
}

function autoResizeTextarea(target, immediate = false) {
  const runResize = () => {
    const textarea = resolveTextarea(target);
    if (!textarea) return;
    textarea.style.height = "auto";
    const fullHeight = textarea.scrollHeight;
    const clampedHeight = Math.min(textareaMaxHeight, Math.max(fullHeight, textareaMinHeight));
    textarea.style.height = `${clampedHeight}px`;
    const isOverflowing = fullHeight > textareaMaxHeight;
    textarea.style.overflowY = isOverflowing ? "auto" : "hidden";
    if (isOverflowing) textarea.scrollTop = textarea.scrollHeight;
  };
  if (immediate) runResize();
  else nextTick(runResize);
}

function resetTextareaHeight() {
  const textarea = composerRef.value;
  if (!textarea) return;
  textarea.style.height = `${textareaMinHeight}px`;
  textarea.style.overflowY = "hidden";
}

function handleTextareaInput(event) { autoResizeTextarea(event, true); }
function handleCompositionStart(event) { autoResizeTextarea(event, true); }
function handleCompositionUpdate(event) { autoResizeTextarea(event, true); }
function handleCompositionEnd(event) { autoResizeTextarea(event, true); }

async function handleEnter(event) {
  if (event.shiftKey) {
    const textarea = event.target;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    draftMessage.value = draftMessage.value.substring(0, start) + "\n" + draftMessage.value.substring(end);
    nextTick(() => {
      textarea.setSelectionRange(start + 1, start + 1);
      autoResizeTextarea();
    });
    return;
  }
  if (!canSendMessage.value) {
    event.preventDefault();
    return;
  }
  event.preventDefault();
  await handleSend();
}

async function handleSend(useAIFill = false) {
  if (!props.grantId || !props.templateId) return;
  if (isReadOnly.value) return;
  const normalizedText = draftMessage.value.trim() || "無";
  const messageContent = useAIFill ? "請AI自動幫我填寫" : normalizedText;

  const userMsg = {
    id: `user-${Date.now()}`,
    role: "user",
    type: "text",
    content: messageContent,
    timestamp: getCurrentTimestamp(),
  };
  messages.value.push(userMsg);
  // remember index so we can remove it if the stream is cancelled
  lastSentUserIndex.value = messages.value.length - 1;
  scrollToBottom();

  if (window.chatWebSocket && window.chatWebSocket.readyState === WebSocket.OPEN) {
    const userPayload = {
      user_message: messageContent,
      current_answers: questionAnswers.value,
      current_answers_meta: questionAnswerMeta.value,
      project_title: props.grantName || "",
      project_summary: "",
    };
    isFetchingNextQuestion.value = true;
    window.chatWebSocket.send(JSON.stringify(userPayload));
  }

  draftMessage.value = "";
  nextTick(() => resetTextareaHeight());
}

function handlePause() {
  if (window.chatWebSocket && window.chatWebSocket.readyState === WebSocket.OPEN) {
    try {
      window.chatWebSocket.send(JSON.stringify({ action: "pause" }));
      pausedFlag.value = true;
    } catch (e) {
      console.error("Failed to send pause action", e);
    }
  }
}

// 請求生成完整計畫書：未回答提示 → AI 生成內容確認 → 推薦名稱
// 從側邊欄確認模式送出時，使用者在進入確認模式前已同意過未回答提示，不再重複詢問
async function requestGeneration(options) {
  if (!canRequestPlan.value) return;
  if (hasMissingAnswers.value && options?.missingAnswersAccepted !== true) {
    const confirmed = await confirm({
      title: "尚有問題未回答",
      message: "仍有核心問題尚未完成，可能導致生成內容不完整，是否仍要繼續？",
      confirmText: "繼續生成",
      cancelText: "返回填寫",
      confirmColor: "danger",
    });
    if (!confirmed) return;
  }

  // 有 AI 生成的答案就顯示確認清單（即使都已確認），由使用者選擇繼續生成或前往確認；
  // 但若是在確認模式中剛逐段確認完畢，就直接生成，不再重複顯示
  const readiness = await fetchExportReadiness();
  const justFinishedReview = Boolean(reviewFieldIds.value) && readiness?.unconfirmed === 0;
  if (readiness && (readiness.ai_generated || readiness.needs_review) && !justFinishedReview) {
    exportReadiness.value = readiness;
    isExportReadinessOpen.value = true;
    return;
  }
  if (!readiness && Object.keys(questionAnswerProvenance.value).some(needsConfirmation)) {
    notifyError("暫時無法檢查 AI 生成內容的確認狀態，請稍後再試");
    return;
  }

  reviewFieldIds.value = null;
  await openRecommendNames();
}

// 取得推薦項目名稱並打開選擇視窗
async function openRecommendNames() {
  isFetchingRecommend.value = true;
  isRecommendModalOpen.value = true;
  recommendOptions.value = [];

  try {
    const resp = await demoFetch(`${API_BASE_URL}/recommend_project_names`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        current_answers: questionAnswers.value,
        project_title: props.projectTitle || "",
        grant_name: props.grantName || "",
        template_name: props.templateName || "",
        grant_id: props.grantId || "",
        template_id: props.templateId || "",
      }),
    });
    const data = await resp.json().catch(() => null);
    recommendOptions.value = resp.ok && data?.names ? data.names : [];
  } catch (e) {
    console.error("Failed to fetch recommendations", e);
    recommendOptions.value = [];
  } finally {
    isFetchingRecommend.value = false;
  }
}

async function handleRecommendConfirm(selectedName) {
  if (!selectedName) return;

  emit("updateProjectTitle", selectedName);

  const joinedText = Object.entries(questionAnswers.value)
    .map(([key, value]) => {
      const text = value?.value ?? value?.reply ?? value;
      return `【${key}】\n${text}`;
    })
    .join("\n\n");

  const finalUserInput =
    "計畫名稱: " +
    selectedName +
    "\n\n計畫摘要: " +
    (props.projectSummary || "") +
    "\n\n" +
    joinedText;

  emit("generatePlan", {
    grantId: props.grantId,
    templateId: props.templateId,
    prompt: finalUserInput,
  });
}

function handleCandidateConfirm(payload) {
  emit("finalizeCandidates", payload);
  isCandidateSelectorVisible.value = false;
}

function handleVersionSelect(version) {
  selectedVersion.value = version;
  isVersionModalVisible.value = true;
}

async function handleVersionDelete(version) {
  const confirmed = await confirm({
    title: "刪除版本",
    message: `確定刪除「${version.title}」？此操作無法復原。`,
    confirmText: "刪除",
    cancelText: "取消",
    confirmColor: "danger",
  });
  if (!confirmed) return;
  if (selectedVersion.value?.id === version.id) {
    isVersionModalVisible.value = false;
    selectedVersion.value = null;
  }
  emit("deleteVersion", version);
}

async function handleVersionExport(version) {
  const versionData = version?.data;
  if (!versionData || Object.keys(versionData).length === 0) {
    notifyError("該版本沒有可匯出的內容");
    return;
  }

  // 1. 關閉當前的版本預覽模態窗，避免畫面堆疊遮擋
  isVersionModalVisible.value = false;

  // 2. 顯示溫馨提示，引導用戶進行註冊
  notifySuccess("體驗版不開放直接下載，註冊免費帳號即可立即匯出完整 Word 報告！");

  // 3. 發送 register 事件，直接彈出註冊模態窗
  emit("register");
}

function handleVersionUpdateRequest(version) {
  if (!version) return;
  emit("requestVersionUpdate", { version });
  isVersionModalVisible.value = false;
}

// 處理側邊欄編輯問題事件，打開編輯欄位模態框
function handleEditQuestion(payload) {
  try {
    const qId = payload?.questionId ?? null;
    const qLabel = payload?.questionLabel || "";
    const ans = payload?.answer || "";
    editFieldQuestionId.value = qId;
    editFieldLabel.value = qLabel;
    // 與「展開」模態框一致的分段；送出時會移除自動補的換段
    editFieldInitialValue.value = answerToEditText(ans);
    isEditFieldModalOpen.value = true;
  } catch (e) {
    console.error("handleEditQuestion error", e);
  }
}

// 處理編輯欄位確認，構建更新消息並自動發送給 AI
async function handleEditConfirm(value) {
  try {
    // 移除編輯框自動補的換段，其餘換行保留，避免顯示用分段寫回答案
    const updated = editTextToAnswer(value || "").trim();
    isEditFieldModalOpen.value = false;
    await sendFieldEdit(editFieldQuestionId.value || "", editFieldLabel.value || "", updated);
  } catch (e) {
    console.error("handleEditConfirm error", e);
  }
}

// 送出「幫我更改」訊息（編輯模態框與側邊欄確認模式的卡片內編輯共用）
async function sendFieldEdit(qId, qLabel, updated) {
  if (!updated) return;
  // Include the real field id so the model echoes it in field_updates instead of guessing one
  const target = qId ? `${qLabel}（${qId}）` : qLabel;
  // Keep whatever the user was typing; handleSend clears the draft
  const pendingDraft = draftMessage.value;
  draftMessage.value = `幫我更改\n${target}\n至\n${updated}`;
  await handleSend();
  draftMessage.value = pendingDraft;
}

// 側邊欄卡片內編輯（內容已移除自動換段）
async function handleSidebarFieldEdit(payload) {
  if (!canSendMessage.value) return;
  await sendFieldEdit(payload?.questionId || "", payload?.questionLabel || "", payload?.value || "");
}

// 處理側邊欄重新生成事件，確認後請 AI 只重寫該欄位
async function handleRegenerateQuestion(payload) {
  if (!canSendMessage.value) return;
  const qId = payload?.questionId || "";
  const qLabel = payload?.questionLabel || "";
  if (!qId) return;
  const confirmed = await confirm({
    title: "重新生成欄位",
    message: `將由 AI 重新撰寫「${qLabel}」，並覆蓋目前內容，是否繼續？`,
    confirmText: "重新生成",
    cancelText: "取消",
  });
  if (!confirmed || !canSendMessage.value) return;
  // Keep whatever the user was typing; handleSend clears the draft
  const pendingDraft = draftMessage.value;
  draftMessage.value = `請AI重新生成\n${qLabel}（${qId}）`;
  await handleSend();
  draftMessage.value = pendingDraft;
}

// 取得生成前檢查（AI 生成／需確認的答案統計），失敗時回傳 null
async function fetchExportReadiness() {
  try {
    const response = await demoFetch(`${API_BASE_URL}/demo/export-readiness`, {
      method: "GET",
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.warn("Failed to fetch export readiness, generating anyway", error);
    return null;
  }
}

// 使用者選擇略過確認、直接生成（答案維持未確認）
function handleExportReadinessProceed() {
  reviewFieldIds.value = null;
  openRecommendNames();
}

async function handleExportReadinessReview(fieldIds) {
  const wasReviewing = Boolean(reviewFieldIds.value);
  reviewFieldIds.value = fieldIds;
  // 剛進入確認模式時側邊欄會自動打開確認視窗；已在確認模式中則需手動打開
  if (wasReviewing) {
    await nextTick();
    chatSidebarRef.value?.openReview();
  }
}

// 生成前確認：透過聊天連線送出（後端在同一個連線存檔，避免被下一輪對話的存檔覆蓋）
function sendAnswerConfirmation(fieldIds, confirmed) {
  const ws = window.chatWebSocket;
  if (!fieldIds.length || !ws || ws.readyState !== WebSocket.OPEN) {
    notifyError("連線中斷，請重新整理後再確認");
    return;
  }
  try {
    ws.send(
      JSON.stringify({
        action: "confirm_answers",
        field_ids: fieldIds,
        confirmed,
      }),
    );
    confirmingFieldIds.value = [...new Set([...confirmingFieldIds.value, ...fieldIds])];
  } catch (e) {
    console.error("Failed to send confirm_answers", e);
    notifyError("確認失敗，請稍後再試");
  }
}

// 後端存檔成功後才更新畫面上的確認狀態
function applyAnswerConfirmation(fieldIds, confirmed) {
  const next = { ...questionAnswerProvenance.value };
  fieldIds.forEach((fieldId) => {
    if (next[fieldId]) {
      next[fieldId] = { ...next[fieldId], confirmed };
    }
  });
  questionAnswerProvenance.value = next;
  confirmingFieldIds.value = confirmingFieldIds.value.filter(
    (fieldId) => !fieldIds.includes(fieldId),
  );
}

// -- WebSocket --
async function streamAIGuidanceMessage(question) {
  if (!question || !question.id) return;
  if (!props.grantId || !props.templateId) return;
  if (typeof window === "undefined") return;

  const rawApiBase = config.public.apiBaseUrl || "";
  let wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
  let wsHost = window.location.host;
  let wsPathPrefix = "";

  if (rawApiBase.startsWith("http://") || rawApiBase.startsWith("https://")) {
    try {
      const parsedBase = new URL(rawApiBase);
      wsProtocol = parsedBase.protocol === "https:" ? "wss" : "ws";
      wsHost = parsedBase.host;
      wsPathPrefix = parsedBase.pathname.replace(/\/+$/, "");
    } catch (err) {
      console.warn("Failed to parse apiBaseUrl, using window location instead", err);
    }
  } else if (rawApiBase) {
    wsPathPrefix = (rawApiBase.startsWith("/") ? rawApiBase : `/${rawApiBase}`).replace(/\/+$/, "");
  }

  const wsPath = `${wsPathPrefix}/api/ws/chat_guidance`.replace(/\/{2,}/g, "/").replace(/^\/?/, "/");
  const sessionQuery = props.sessionId ? `?session_id=${encodeURIComponent(props.sessionId)}` : "";
  const wsUrl = `${wsProtocol}://${wsHost}${wsPath}${sessionQuery}`;

  if (question.id === "init") {
    if (window.chatWebSocket && window.chatWebSocket.readyState !== WebSocket.CLOSED && window.chatWebSocket.readyState !== WebSocket.CLOSING) {
      window.chatWebSocket.close();
    }

    window.chatWebSocket = new WebSocket(wsUrl);

    window.chatWebSocket.onopen = () => {
      const payload = {
        grant_id: props.grantId,
        template_id: props.templateId,
        grant_name: props.grantName || "",
        template_name: props.templateName || "",
        project_id: "",
        project_title: props.grantName || "",
        project_summary: "",
        all_questions: props.allQuestions,
        current_answers: questionAnswers.value,
        current_answers_meta: questionAnswerMeta.value,
        history: buildConversationHistoryPayload(),
      };
      window.chatWebSocket.send(JSON.stringify(payload));
    };

    window.chatWebSocket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.event === "ready") {
          if (Array.isArray(msg.applicable_questions)) {
            applicableQuestionIds.value = msg.applicable_questions;
          }
        } else if (msg.event === "chunk_start") {
          const aiMsg = {
            id: `ai-stream-${Date.now()}`,
            role: "assistant",
            type: "text",
            content: "",
            isStreaming: true,
            timestamp: getCurrentTimestamp(),
          };
          messages.value.push(aiMsg);
          if (lastSentUserIndex.value === null) {
            for (let i = messages.value.length - 1; i >= 0; i -= 1) {
              if (messages.value[i].role === "user") {
                lastSentUserIndex.value = i;
                break;
              }
            }
          }
          isStreaming.value = true;
          scrollToBottom();
        } else if (msg.event === "chunk") {
          const lastMsg = messages.value[messages.value.length - 1];
          if (lastMsg && lastMsg.role === "assistant" && lastMsg.isStreaming) {
            lastMsg.content += msg.data || "";
            if (lastMsg.content.includes("【回復結束】")) {
              lastMsg.isStreaming = false;
              lastSentUserIndex.value = null;
              isFetchingNextQuestion.value = false;
              isStreaming.value = false;
              emit("aiResponseComplete");
            }
            scrollToBottom();
          }
        } else if (msg.event === "filled") {
          const filledFields = msg.data || {};
          const filledSources = msg.sources || {};
          const filledReview = msg.needs_review || {};
          Object.entries(filledFields).forEach(([fieldId, value]) => {
            if (value && String(value).trim()) {
              questionAnswers.value = { ...questionAnswers.value, [fieldId]: String(value).trim() };
              touchAnswerMeta(fieldId);
              setAnswerProvenance(fieldId, filledSources[fieldId], filledReview[fieldId]);
              lastSentUserIndex.value = null;
            }
          });
          if (Array.isArray(msg.applicable_questions)) {
            applicableQuestionIds.value = msg.applicable_questions;
          }
        } else if (msg.event === "cleared") {
          // 條件改變後恢復作答的題目：移除系統自動填入的「本項免填」
          const clearedIds = Array.isArray(msg.data) ? msg.data : [];
          if (clearedIds.length) {
            const nextAnswers = { ...questionAnswers.value };
            const nextMeta = { ...questionAnswerMeta.value };
            const nextProvenance = { ...questionAnswerProvenance.value };
            clearedIds.forEach((fieldId) => {
              delete nextAnswers[fieldId];
              delete nextMeta[fieldId];
              delete nextProvenance[fieldId];
            });
            questionAnswers.value = nextAnswers;
            questionAnswerMeta.value = nextMeta;
            questionAnswerProvenance.value = nextProvenance;
          }
          if (Array.isArray(msg.applicable_questions)) {
            applicableQuestionIds.value = msg.applicable_questions;
          }
        } else if (msg.event === "done") {
          const lastMsg = messages.value[messages.value.length - 1];
          if (lastMsg && lastMsg.isStreaming) lastMsg.isStreaming = false;
          lastSentUserIndex.value = null;
          isFetchingNextQuestion.value = false;
          isStreaming.value = false;
          emit("aiResponseComplete");
        } else if (msg.event === "answers_confirmed") {
          applyAnswerConfirmation(
            Array.isArray(msg.field_ids) ? msg.field_ids : [],
            Boolean(msg.confirmed),
          );
        } else if (msg.event === "cancelled") {
          try {
            for (let i = messages.value.length - 1; i >= 0; i -= 1) {
              const m = messages.value[i];
              if (m.role === "assistant" && m.isStreaming) {
                messages.value.splice(i, 1);
                break;
              }
            }
            if (lastSentUserIndex.value !== null) {
              const idx = lastSentUserIndex.value;
              if (messages.value[idx] && messages.value[idx].role === "user") {
                messages.value.splice(idx, 1);
              }
            } else if (msg.restore_user_message) {
              for (let i = messages.value.length - 1; i >= 0; i -= 1) {
                const m = messages.value[i];
                if (m.role === "user" && m.content === msg.restore_user_message) {
                  messages.value.splice(i, 1);
                  break;
                }
              }
            }
            if (msg.restore_user_message) draftMessage.value = msg.restore_user_message;
            lastSentUserIndex.value = null;
          } catch (e) {
            console.error("Error handling cancelled event", e);
          }
          isFetchingNextQuestion.value = false;
          isStreaming.value = false;
        } else if (msg.event === "error") {
          const lastMsg = messages.value[messages.value.length - 1];
          if (lastMsg && lastMsg.isStreaming) {
            lastMsg.isStreaming = false;
            lastMsg.content = msg.message || lastMsg.content || "抱歉，無法取得 AI 回應。";
          } else if (msg.message) {
            notifyError(msg.message);
          }
          isFetchingNextQuestion.value = false;
          isStreaming.value = false;
          confirmingFieldIds.value = [];
        } else if (msg.event === "limit_reached") {
          isFetchingNextQuestion.value = false;
          isStreaming.value = false;
          emit("register");
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    window.chatWebSocket.onerror = (error) => {
      console.error("WebSocket error:", error);
      isFetchingNextQuestion.value = false;
      isStreaming.value = false;
    };

    window.chatWebSocket.onclose = () => {
      isFetchingNextQuestion.value = false;
      isStreaming.value = false;
      confirmingFieldIds.value = [];
    };
  }
  return;
}

// -- Watchers --
watch(
  messages,
  (newMessages) => {
    emit("messagesUpdated", newMessages);
  },
  { deep: true }
);

watch(
  questionAnswers,
  (newAnswers) => {
    emit("questionAnswersUpdated", newAnswers);
  },
  { deep: true }
);

watch(
  () => props.candidatePlan,
  (val) => {
    const snapshot = JSON.stringify(val || {});
    if (!snapshot || snapshot === "{}" || snapshot === lastCandidateSnapshot.value) {
      return;
    }
    lastCandidateSnapshot.value = snapshot;
    isCandidateSelectorVisible.value = true;
    scrollToBottom();
  },
  { deep: true }
);

// -- Hydration from props --
function normalizeStoredMessages(entries = []) {
  if (!Array.isArray(entries)) return [];
  return entries
    .map((entry, index) => {
      if (!entry) return null;
      const role = entry.role === "user" ? "user" : "assistant";
      const content = String(entry.content || "").trim();
      if (!content) return null;
      const timestampCandidate =
        entry.timestamp || entry.created_at || entry.createdAt || entry.time || entry.updated_at;
      const normalizedTimestamp = timestampCandidate ? String(timestampCandidate) : getCurrentTimestamp();
      return {
        id: entry.id || `history-${index}-${Date.now()}`,
        role,
        type: entry.type || "text",
        content,
        timestamp: normalizedTimestamp,
      };
    })
    .filter(Boolean);
}

// 答案可能是純文字（舊資料）或 {value, source, ...}（記錄來源的新格式）
function normalizeStoredAnswers(rawAnswers = {}) {
  if (!rawAnswers || typeof rawAnswers !== "object") return {};
  const normalized = {};
  Object.entries(rawAnswers).forEach(([key, value]) => {
    const raw = value && typeof value === "object" ? (value.value ?? value.reply) : value;
    const text = String(raw ?? "").trim();
    if (!key || !text) return;
    normalized[key] = text;
  });
  return normalized;
}

function normalizeStoredProvenance(rawAnswers = {}) {
  if (!rawAnswers || typeof rawAnswers !== "object") return {};
  const normalized = {};
  Object.entries(rawAnswers).forEach(([key, value]) => {
    if (!key || !value || typeof value !== "object") return;
    const source = String(value.source || "").trim();
    const needsReview = Boolean(value.needs_review ?? value.needsReview);
    if ((!source || source === "user_input") && !needsReview) return;
    normalized[key] = {
      source: source || "user_input",
      needs_review: needsReview,
      review_note: String(value.review_note ?? value.reviewNote ?? "").trim(),
      confirmed: Boolean(value.confirmed),
    };
  });
  return normalized;
}

function normalizeStoredAnswerMeta(rawMeta = {}) {
  if (!rawMeta || typeof rawMeta !== "object") return {};
  const normalized = {};
  Object.entries(rawMeta).forEach(([key, value]) => {
    if (!key) return;
    let timestamp = "";
    if (typeof value === "string") {
      timestamp = value.trim();
    } else if (value && typeof value === "object") {
      timestamp = String(value.updated_at || value.updatedAt || "").trim();
    }
    if (!timestamp) return;
    normalized[key] = { updated_at: timestamp };
  });
  return normalized;
}

function applyStoredState(history = [], answers = {}, meta = {}) {
  const historyEntries = normalizeStoredMessages(history);
  if (historyEntries.length && !messages.value.length) {
    messages.value = historyEntries;
    scrollToBottom();
  }
  const storedAnswers = normalizeStoredAnswers(answers);
  if (Object.keys(storedAnswers).length) {
    questionAnswers.value = { ...questionAnswers.value, ...storedAnswers };
    const storedProvenance = normalizeStoredProvenance(answers);
    const nextProvenance = { ...questionAnswerProvenance.value };
    Object.keys(storedAnswers).forEach((key) => {
      if (storedProvenance[key]) {
        nextProvenance[key] = storedProvenance[key];
      } else {
        delete nextProvenance[key];
      }
    });
    if (JSON.stringify(nextProvenance) !== JSON.stringify(questionAnswerProvenance.value)) {
      questionAnswerProvenance.value = nextProvenance;
    }
  }
  const storedMeta = normalizeStoredAnswerMeta(meta);
  if (Object.keys(storedMeta).length) {
    questionAnswerMeta.value = { ...questionAnswerMeta.value, ...storedMeta };
  }
  Object.keys(storedAnswers).forEach((key) => {
    if (!questionAnswerMeta.value[key]) {
      touchAnswerMeta(key, getCurrentTimestamp());
    }
  });
}

watch(
  () => props.conversationHistory,
  (val) => {
    if (val && val.length && !messages.value.length) {
      applyStoredState(val, props.storedAnswers, props.storedAnswersMeta);
    }
  },
  { immediate: true }
);

watch(
  () => props.storedAnswers,
  (val) => {
    if (val && Object.keys(val).length && !Object.keys(questionAnswers.value).length) {
      applyStoredState(props.conversationHistory, val, props.storedAnswersMeta);
    }
  },
  { immediate: true }
);

// -- Lifecycle --
onMounted(() => {
  chatInitialized.value = true;
  scrollToBottom();
  autoResizeTextarea();
  if (props.grantId && props.templateId) {
    const dummyQuestion = { id: "init", label: "初始化", prompt: "初始化" };
    void streamAIGuidanceMessage(dummyQuestion);
  }
});

onBeforeUnmount(() => {
  if (window.chatWebSocket && window.chatWebSocket.readyState !== WebSocket.CLOSED) {
    window.chatWebSocket.close();
  }
});
</script>

<style scoped>
.scrollbar-thin::-webkit-scrollbar { width: 6px; }
.scrollbar-thumb-rose-300::-webkit-scrollbar-thumb { background-color: #ffb4a8; border-radius: 3px; }
.scrollbar-thumb-rose-300::-webkit-scrollbar-thumb:hover { background-color: #ff998e; }
.scrollbar-track-transparent::-webkit-scrollbar-track { background-color: transparent; border-radius: 3px; }
.scrollbar-thin { scrollbar-width: thin; scrollbar-color: #ffb4a8 transparent; }
</style>
