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
                <span class="hidden sm:inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-amber-600 border border-amber-100">
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
            <div v-for="message in messages" :key="message.id" class="flex" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
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
          <!-- Amber tip -->
          <div class="mb-3 flex items-start gap-2 rounded-xl bg-amber-50/50 px-3 py-2 text-xs text-amber-700/80" role="note">
            <span class="text-sm leading-none opacity-80">💡</span>
            <p class="flex-1 leading-relaxed">
              提醒：若對特定題目的回答未達預期，請輸入 【該題目標題】 並加上 【請重新回答】，系統將重新提供作答內容。
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
                class="rounded-full border border-[#dfe3ff] px-5 py-2 text-sm font-semibold text-[#6c719b] hover:bg-[#f4f5ff] disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="!canSendMessage"
                @click="handleSend(false)"
              >
                回覆當前問題
              </button>
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
              <button
                type="button"
                class="rounded-full bg-gradient-to-r from-[#ff9b6d] to-[#ff4b6b] px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-[#ff4b6b]/30 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="!canRequestPlan || isStreaming"
                @click="handleRequestGeneration"
              >
                {{ isStreaming ? '推演中...' : '輸出完整推演' }}
              </button>
              <button
                v-if="isFetchingNextQuestion"
                type="button"
                class="ml-2 rounded-full border border-red-400 bg-white px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-50"
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
    <div class="h-full w-full max-w-xs flex-shrink-0">
      <ChatSidebar
        :messages="messages"
        :versions="props.savedPlanVersions"
        :question-answers="questionAnswers"
        :question-answer-meta="questionAnswerMeta"
        @editQuestion="handleEditQuestion"
        @selectVersion="handleVersionSelect"
      />
    </div>

    <!-- Edit field modal -->
    <EditFieldModal
      v-model:is-open="isEditFieldModalOpen"
      title="編輯欄位"
      :label="editFieldLabel"
      :initial-value="editFieldInitialValue"
      @confirm="handleEditConfirm"
    />

    <!-- Recommend project name modal -->
    <RecommendNameModal
      v-model:is-open="isRecommendModalOpen"
      :original-name="props.projectTitle"
      :suggestions="recommendOptions"
      :loading="isFetchingRecommend"
      @confirm="handleRecommendConfirm"
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
import { exportPlanToWord } from "~/utils/exportToWord";
import { useConfirm } from "~/composables/useConfirm";
import { useNotifications } from "~/composables/useNotifications";

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
  registerUrl: { type: String, default: "" },
  projectTitle: { type: String, default: "" },
  projectSummary: { type: String, default: "" },
  sections: { type: Array, default: () => [] },
  candidatePlan: { type: Object, default: () => ({}) },
  finalPlan: { type: Object, default: () => ({}) },
  savedPlanVersions: { type: Array, default: () => [] },
  sectionVersions: { type: Object, default: () => ({}) },
});

const emit = defineEmits([
  "messagesUpdated",
  "questionAnswersUpdated",
  "aiResponseComplete",
  "generatePlan",
  "updateProjectTitle",
  "finalizeCandidates",
  "requestVersionUpdate",
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
const activeQuestionId = ref(null);
const chatContainer = ref(null);
const draftMessage = ref("");
const composerRef = ref(null);
const isEditFieldModalOpen = ref(false);
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
  lastSentUserIndex.value = messages.value.length - 1;
  scrollToBottom();

  if (activeQuestionId.value) {
    questionAnswers.value = { ...questionAnswers.value, [activeQuestionId.value]: messageContent };
    touchAnswerMeta(activeQuestionId.value);
    activeQuestionId.value = null;
  }

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

async function handleRequestGeneration() {
  if (!canRequestPlan.value) return;
  if (hasMissingAnswers.value) {
    const confirmed = await confirm({
      title: "尚有問題未回答",
      message: "仍有核心問題尚未完成，可能導致生成內容不完整，是否仍要繼續？",
      confirmText: "繼續生成",
      cancelText: "返回填寫",
      confirmColor: "danger",
    });
    if (!confirmed) return;
  }

  isFetchingRecommend.value = true;
  isRecommendModalOpen.value = true;
  recommendOptions.value = [];

  try {
    const resp = await fetch(`${API_BASE_URL}/recommend_project_names`, {
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
      const text = value?.reply ?? value;
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

function handleEditQuestion(payload) {
  try {
    const qId = payload?.questionId ?? null;
    const qLabel = payload?.questionLabel || "";
    const ans = payload?.answer || "";
    editFieldQuestionId.value = qId;
    editFieldLabel.value = qLabel;
    editFieldInitialValue.value = ans;
    isEditFieldModalOpen.value = true;
  } catch (e) {
    console.error("handleEditQuestion error", e);
  }
}

async function handleEditConfirm(value) {
  try {
    const qLabel = editFieldLabel.value || "";
    const updated = value || "";
    draftMessage.value = `幫我更改\n${qLabel}\n至\n${updated}`;
    isEditFieldModalOpen.value = false;
    await handleSend();
  } catch (e) {
    console.error("handleEditConfirm error", e);
  }
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
          // No-op
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
          Object.entries(filledFields).forEach(([fieldId, value]) => {
            if (value && String(value).trim()) {
              questionAnswers.value = { ...questionAnswers.value, [fieldId]: String(value).trim() };
              touchAnswerMeta(fieldId);
              lastSentUserIndex.value = null;
            }
          });
        } else if (msg.event === "done") {
          const lastMsg = messages.value[messages.value.length - 1];
          if (lastMsg && lastMsg.isStreaming) lastMsg.isStreaming = false;
          lastSentUserIndex.value = null;
          isFetchingNextQuestion.value = false;
          isStreaming.value = false;
          emit("aiResponseComplete");
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

function normalizeStoredAnswers(rawAnswers = {}) {
  if (!rawAnswers || typeof rawAnswers !== "object") return {};
  const normalized = {};
  Object.entries(rawAnswers).forEach(([key, value]) => {
    const text = String(value ?? "").trim();
    if (!key || !text) return;
    normalized[key] = text;
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
      applyStoredState(val, props.storedAnswers, {});
    }
  },
  { immediate: true }
);

watch(
  () => props.storedAnswers,
  (val) => {
    if (val && Object.keys(val).length && !Object.keys(questionAnswers.value).length) {
      applyStoredState(props.conversationHistory, val, {});
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