<template>
  <div class="flex h-screen gap-4">
    <div class="flex-1 h-full">
      <div
        class="flex h-full min-h-0 flex-col rounded-[32px] bg-[#f7f8fc] shadow-2xl"
      >
        <header
          class="flex flex-wrap items-center justify-between gap-4 rounded-3xl bg-white px-6 py-2 shadow-lg"
        >
          <div class="flex items-center gap-4">
            <span
              class="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#ffb067] via-[#ff7a66] to-[#ff4b5c] text-base font-semibold text-white"
            >
              AI
            </span>
            <div>
              <p class="text-lg font-semibold text-slate-900">企劃引擎</p>
              <p class="flex items-center gap-2 text-xs text-slate-400">
                <span
                  class="flex flex-1 h-2 w-2 rounded-full bg-green-500 shadow-lg shadow-green-500/50"
                ></span>
                智慧推演進行中 · {{ activeGrantName }}
                <span v-if="activeTemplateName"
                  >/ {{ activeTemplateName }}</span
                >
              </p>
            </div>
          </div>
          <div class="flex flex-wrap gap-3">
            <!-- <button
              type="button"
              class="rounded-full bg-[#ff4b5c] px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-[#ff4b5c]/30 transition hover:-translate-y-0.5 hover:bg-[#ff2f45] disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="!canRequestPlan || isGenerating"
              @click="requestGeneration"
            >
              {{ isGenerating ? "推演中..." : "啟動精準推演" }}
            </button> -->
          </div>
        </header>

        <div class="mt-6 flex-1 min-h-0">
          <div
            ref="chatContainer"
            class="h-full space-y-4 overflow-y-auto pr-3 scrollbar-thin scrollbar-thumb-rose-300 scrollbar-track-transparent"
          >
            <div
              v-for="message in messages"
              :key="message.id"
              class="flex"
              :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="flex max-w-3xl flex-1 px-2 gap-3"
                :class="
                  message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                "
              >
                <span
                  v-if="message.role !== 'user'"
                  class="mt-1 inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-[#fff1ea] text-sm font-semibold text-[#ff6b3d]"
                >
                  AI
                </span>
                <div class="flex-1 space-y-3">
                  <template v-if="message.type === 'text'">
                    <article
                      :class="[
                        'px-5 py-4 rounded-[28px] shadow-md',
                        message.role === 'user'
                          ? 'bg-gradient-to-r from-[#ff9b6d] to-[#ff4b6b] text-white shadow-lg'
                          : 'border border-[#f0f2ff] bg-white text-slate-700',
                      ]"
                    >
                      <p
                        class="text-sm leading-relaxed"
                        v-html="formatMessageForDisplay(message.content)"
                      ></p>
                    </article>
                  </template>

                  <template v-else-if="message.type === 'question'">
                    <article
                      class="rounded-[28px] border border-[#ffe5da] bg-[#fff8f5] px-5 py-4 shadow-sm"
                    >
                      <p
                        class="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#ff7a5b]"
                      >
                        {{ message.label }}
                      </p>
                      <p
                        class="mt-2 text-sm font-semibold text-slate-800 whitespace-pre-line"
                      >
                        {{ message.content }}
                      </p>
                    </article>
                  </template>

                  <template v-else-if="message.type === 'answer'">
                    <article
                      class="rounded-[28px] border border-[#e1e7ff] bg-white px-5 py-4 shadow-sm"
                    >
                      <div
                        class="flex items-center justify-between text-[11px] uppercase tracking-[0.3em] text-slate-400"
                      >
                        <span>
                          {{
                            message.source === "prefill"
                              ? "已帶入答案"
                              : "我的回答"
                          }}
                        </span>
                        <button
                          v-if="message.questionId"
                          type="button"
                          class="rounded-full border border-[#d7dcf8] px-3 py-1 text-[11px] font-semibold text-[#7a80b6] hover:bg-[#f4f5ff]"
                          @click="() => editAnswer(message.questionId)"
                        >
                          修改
                        </button>
                      </div>
                      <p
                        class="mt-2 text-sm text-slate-700 whitespace-pre-line"
                      >
                        {{ message.content }}
                      </p>
                    </article>
                  </template>

                  <template
                    v-else-if="
                      message.type === 'references' && referenceSummaries.length
                    "
                  >
                    <article
                      class="rounded-[28px] border border-[#dde3ff] bg-white px-5 py-4 shadow-md"
                    >
                      <p class="text-sm font-semibold text-slate-800">
                        已加入的參考資料
                      </p>
                      <ul class="mt-3 space-y-2">
                        <li
                          v-for="(summary, idx) in referenceSummaries"
                          :key="idx"
                          class="rounded-2xl bg-[#f8f9ff] px-4 py-2 text-sm text-slate-600"
                        >
                          <span class="mr-2 font-semibold text-[#ff6b3d]"
                            >#{{ idx + 1 }}</span
                          >
                          {{ summary }}
                        </li>
                      </ul>
                    </article>
                  </template>
                </div>
              </div>
            </div>

            <div
              v-if="isGenerating"
              class="flex flex-col items-center justify-center pt-6"
            >
              <div class="flex gap-1">
                <span
                  v-for="n in 3"
                  :key="n"
                  class="h-2.5 w-2.5 animate-bounce rounded-full bg-[#ffb4a8]"
                  :style="{ animationDelay: `${(n - 1) * 0.15}s` }"
                ></span>
              </div>
              <p class="mt-2 text-xs text-slate-400">AI 正在推演整體架構...</p>
            </div>
            <div
              v-if="isFetchingNextQuestion && !isGenerationComplete"
              class="flex items-center justify-center gap-2 pt-4 text-xs text-slate-400"
            >
              <span
                class="h-2.5 w-2.5 animate-ping rounded-full bg-[#ffb4a8]"
              ></span>
              AI 正在構思下一個提問...
            </div>
          </div>
        </div>

        <footer class="mt-2 rounded-[32px] bg-white px-5 py-5 shadow-xl">
          <div class="relative">
            <textarea
              v-model="draftMessage"
              class="mt-3 h-16 w-full resize-none rounded-[28px] border border-[#edf0ff] bg-[#f8f9ff] p-4 pr-14 text-sm text-slate-700 placeholder-slate-400 outline-none focus:border-[#ff4b5c] focus:bg-white focus:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
              :placeholder="composerPlaceholder"
              @keydown.enter.prevent="handleEnter"
            ></textarea>
            <button
              type="button"
              class="absolute right-6 top-5 flex h-10 w-10 items-center justify-center rounded-2xl border border-[#e4e7ff] bg-white text-[#ff6b6b] shadow hover:bg-[#fff6f6]"
              @click="openAttachmentModal"
              title="匯入檔案輔助填寫"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1.8"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M21 12.79V7.5a4.5 4.5 0 00-9 0v9a3 3 0 006 0v-7.5"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M3 12v5.5a4.5 4.5 0 008.8 1.5"
                />
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
              <div class="flex items-center gap-2">
                <select
                  v-model="selectedModel"
                  class="rounded-full border border-[#dfe3ff] bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-[#f4f5ff] focus:border-[#ff4b5c] focus:outline-none"
                >
                  <option value="">預設模型</option>
                  <optgroup label="GPT 模型">
                    <option value="gpt-5.2">gpt-5.2</option>
                    <option value="gpt-5.1">gpt-5.1</option>
                    <option value="gpt-5-mini">
                      gpt-5-mini（目前内部人員）
                    </option>
                    <option value="gpt-5-nano">gpt-5-nano</option>
                    <option value="gpt-4.1-mini">gpt-4.1-mini</option>
                    <option value="gpt-4.1-nano">
                      gpt-4.1-nano(目前外部人員)
                    </option>
                  </optgroup>
                  <optgroup label="Gemini 模型">
                    <option value="gemini-3-pro-preview">
                      gemini-3-pro-preview
                    </option>
                    <option value="gemini-3-flash-preview">
                      gemini-3-flash-preview
                    </option>
                    <option value="gemini-2.5-pro">gemini-2.5-pro</option>
                    <option value="gemini-2.5-flash">gemini-2.5-flash</option>
                  </optgroup>
                </select>
              </div>
              <button
                type="button"
                class="rounded-full bg-gradient-to-r from-[#ff9b6d] to-[#ff4b6b] px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-[#ff4b6b]/30 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="!canRequestPlan || isGenerating"
                @click="requestGeneration"
              >
                {{ isGenerating ? "推演中..." : "輸出完整推演" }}
              </button>
            </div>
          </div>
        </footer>

        <PlanCandidateSelector
          :visible="isCandidateSelectorVisible"
          :candidate-plan="candidatePlan"
          :sections="sections"
          @confirm="handleCandidateConfirm"
          @close="isCandidateSelectorVisible = false"
        />
        <AnswerEditModal
          :visible="isEditModalVisible"
          :question-label="editQuestionLabel"
          :question-prompt="editQuestionPrompt"
          v-model:draft="editAnswerDraft"
          @cancel="cancelEditAnswer"
          @save="saveEditedAnswer"
        />
      </div>
    </div>
    <div v-if="showSidebar" class="h-full w-full max-w-xs flex-shrink-0">
      <ChatSidebar
        :messages="messages"
        :versions="props.savedPlanVersions"
        :question-answers="questionAnswers"
        @selectVersion="handleVersionSelect"
      />
    </div>

    <PlanVersionModal
      :visible="isVersionModalVisible"
      :version="selectedVersion"
      :plan-sections="sections"
      @close="isVersionModalVisible = false"
      @export="handleVersionExport"
    />
    <FieldFileImportModal
      v-model:is-open="isFileImportOpen"
      field-title="聊天輸入"
      field-description="上傳 PDF/TXT 後可自動擷取內容填入訊息"
      :sub-field-label="fileImportSubLabel"
      :sub-field-value="fileImportInitialValue"
      @confirm="handleFileImportConfirm"
    />
  </div>
</template>

<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import PlanCandidateSelector from "~/components/PlanCandidateSelector.vue";
import AnswerEditModal from "~/components/AnswerEditModal.vue";
import ChatSidebar from "~/components/ChatSidebar.vue";
import PlanVersionModal from "~/components/PlanVersionModal.vue";
import FieldFileImportModal from "~/components/editor/helper/FieldFileImportModal.vue";
import { useConfirm } from "~/composables/useConfirm";
import {
  buildDynamicSections,
  createEmptyDynamicValues,
} from "~/utils/dynamicSchema";
import { renderPlanToHtml } from "~/utils/exportToWord";
import { supabase } from "~/utils/supabaseClient";

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const props = defineProps({
  referenceSummaries: { type: Array, default: () => [] },
  sections: { type: Array, default: () => [] },
  candidatePlan: { type: Object, default: () => ({}) },
  finalPlan: { type: Object, default: () => ({}) },
  isGenerating: { type: Boolean, default: false },
  grantId: { type: String, default: "" },
  templateId: { type: String, default: "" },
  grantName: { type: String, default: "" },
  templateName: { type: String, default: "" },
  projectTitle: { type: String, default: "" },
  projectSummary: { type: String, default: "" },
  prefilledAnswers: { type: Object, default: () => ({}) },
  projectId: { type: String, default: "" },
  savedPlanVersions: { type: Array, default: () => [] },
  showSidebar: { type: Boolean, default: false },
});

const isGenerating = computed(() => props.isGenerating);
const showSidebar = computed(() => Boolean(props.showSidebar));

const { confirm } = useConfirm();

const emit = defineEmits([
  "generatePlan",
  "finalizeCandidates",
  "requestExport",
  "backToStageOne",
  "messagesUpdated",
  "questionAnswersUpdated",
  "guidedQuestionsUpdated",
  "aiResponseComplete",
]);

const messages = ref([]);

const guidedQuestions = buildGuidedQuestionList();
const totalQuestions = guidedQuestions.length;
const questionAnswers = ref({});
const answeredCount = computed(() =>
  guidedQuestions.reduce((count, question) => {
    const answer = questionAnswers.value[question.id];
    return answer && answer.trim() ? count + 1 : count;
  }, 0)
);
const allQuestionsAnswered = computed(
  () => totalQuestions === 0 || answeredCount.value === totalQuestions
);
const activeQuestionId = ref(null);

const chatContainer = ref(null);
const draftMessage = ref("");
const isFileImportOpen = ref(false);
const DEFAULT_FILE_IMPORT_LABEL = "聊天輸入";
const fileImportInitialValue = ref("");
const fileImportSubLabel = ref(DEFAULT_FILE_IMPORT_LABEL);
const lastCandidateSnapshot = ref("{}");
const lastFinalSnapshot = ref("{}");
const isCandidateSelectorVisible = ref(false);
const chatInitialized = ref(false);
const isEditModalVisible = ref(false);
const editQuestionId = ref(null);
const editQuestionLabel = ref("");
const editQuestionPrompt = ref("");
const editAnswerDraft = ref("");
const isGenerationComplete = ref(false);
const isFetchingNextQuestion = ref(false);
const projectRealtimeChannel = ref(null);
const isVersionModalVisible = ref(false);
const selectedVersion = ref(null);
const selectedModel = ref("");

const activeGrantName = computed(() => props.grantName || "尚未選擇");
const activeTemplateName = computed(() => props.templateName || "");
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
  // escape HTML first
  let out = escapeHtml(text);
  // convert **bold** to <strong> — support multiline inside ** **
  out = out.replace(/\*\*([\s\S]+?)\*\*/g, "<strong>$1</strong>");
  // preserve line breaks
  out = out.replace(/\r\n|\n/g, "<br/>");
  return out;
}

const composerPlaceholder = computed(() => {
  if (!props.grantId || !props.templateId) {
    return "請先完成第一階段的設定";
  }
  if (isFetchingNextQuestion.value) {
    return "AI 正在思考...";
  }
  if (allQuestionsAnswered.value) {
    return "所有核心問題已完成，請生成候選計畫";
  }
  return "請輸入你的想法或回答 AI 的問題";
});

const canSendMessage = computed(() => {
  // 项目已选择、不是生成完成状态、且AI没有正在思考下一个问题
  return Boolean(
    props.grantId &&
      props.templateId &&
      !isGenerationComplete.value &&
      !isFetchingNextQuestion.value
  );
});

const canRequestPlan = computed(() => {
  return Boolean(props.grantId && props.templateId);
});

const hasCandidatePlan = computed(
  () => Object.keys(props.candidatePlan || {}).length > 0
);

const hasMissingAnswers = computed(() => !allQuestionsAnswered.value);

function getQuestionMeta(questionId) {
  if (!questionId) {
    return null;
  }
  return guidedQuestions.find((item) => item.id === questionId) || null;
}

function buildConversationHistoryPayload(limit = 8) {
  const simpleHistory = [];
  const allowedTypes = new Set(["text", "question", "answer"]);
  messages.value
    .filter((msg) => allowedTypes.has(msg.type))
    .slice(-limit)
    .forEach((msg) => {
      let content = msg.content || "";
      if (msg.type === "answer" && msg.questionId) {
        const meta = getQuestionMeta(msg.questionId);
        const label = meta?.label || msg.questionId;
        content = `${label}：${msg.content}`;
      }
      if (!content.trim()) {
        return;
      }
      simpleHistory.push({
        role: msg.role === "user" ? "user" : "assistant",
        content,
      });
    });

  return simpleHistory;
}

async function streamAIGuidanceMessage(question) {
  if (!question || !question.id) {
    return;
  }
  if (!props.grantId || !props.templateId) {
    return;
  }

  const config = useRuntimeConfig();
  const wsProtocol = config.public.apiBaseUrl.startsWith("https")
    ? "wss"
    : "ws";

  // Get access token for WebSocket authentication
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const token = session?.access_token || "";
  const wsUrl = `${wsProtocol}://${
    config.public.apiBaseUrl.split("://")[1]
  }/api/ws/chat_guidance${token ? `?token=${encodeURIComponent(token)}` : ""}`;

  // 如果是初始化阶段，只建立连接，不创建 AI 消息
  if (question.id === "init") {
    // 关闭旧连接（如果存在）
    if (
      window.chatWebSocket &&
      window.chatWebSocket.readyState !== WebSocket.CLOSED &&
      window.chatWebSocket.readyState !== WebSocket.CLOSING
    ) {
      window.chatWebSocket.close();
    }

    window.chatWebSocket = new WebSocket(wsUrl);

    window.chatWebSocket.onopen = () => {
      const payload = {
        grant_id: props.grantId,
        template_id: props.templateId,
        grant_name: props.grantName || "",
        template_name: props.templateName || "",
        project_id: props.projectId || "",
        project_title: props.projectTitle || "",
        project_summary: props.projectSummary || "",
        all_questions: guidedQuestions,
        current_answers: questionAnswers.value,
        history: buildConversationHistoryPayload(),
      };
      window.chatWebSocket.send(JSON.stringify(payload));
    };

    window.chatWebSocket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        if (msg.event === "ready") {
        } else if (msg.event === "chunk_start") {
          // 创建新的 AI 消息来接收块数据
          const aiMsg = {
            id: `ai-stream-${Date.now()}`,
            role: "assistant",
            type: "text",
            content: "",
            isStreaming: true,
          };
          messages.value.push(aiMsg);
          scrollToBottom();
        } else if (msg.event === "chunk") {
          // 追加到最后一个 AI 消息
          const lastMsg = messages.value[messages.value.length - 1];
          if (lastMsg && lastMsg.role === "assistant" && lastMsg.isStreaming) {
            lastMsg.content += msg.data;
            scrollToBottom();
          }
        } else if (msg.event === "filled") {
          const filledFields = msg.data || {};
          Object.entries(filledFields).forEach(([fieldId, value]) => {
            if (value && String(value).trim()) {
              questionAnswers.value = {
                ...questionAnswers.value,
                [fieldId]: String(value).trim(),
              };
            }
          });
        } else if (msg.event === "done") {
          const lastMsg = messages.value[messages.value.length - 1];
          if (lastMsg && lastMsg.isStreaming) {
            lastMsg.isStreaming = false;
          }
          isFetchingNextQuestion.value = false;
          // Emit event to trigger save after AI response completes
          emit("aiResponseComplete");
        } else if (msg.event === "error") {
          const lastMsg = messages.value[messages.value.length - 1];
          if (lastMsg && lastMsg.isStreaming) {
            lastMsg.isStreaming = false;
            lastMsg.content = lastMsg.content || "抱歉，無法取得 AI 回應。";
          }
          isFetchingNextQuestion.value = false;
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    window.chatWebSocket.onerror = (error) => {
      console.error("❌ WebSocket error:", error);
      console.error("WebSocket readyState:", window.chatWebSocket?.readyState);
      isFetchingNextQuestion.value = false;
    };
  }
  return;
}

function upsertAnswerMessage(
  questionId,
  content,
  source = "user",
  shouldScroll = true
) {
  if (!questionId) {
    return;
  }
  const text = (content || "").trim();
  const index = messages.value.findIndex(
    (msg) => msg.type === "answer" && msg.questionId === questionId
  );
  if (!text) {
    if (index >= 0) {
      messages.value.splice(index, 1);
    }
    return;
  }
  if (shouldScroll) {
    scrollToBottom();
  }
}

watch(
  messages,
  (newMessages) => {
    // 過濾掉 candidates 和 final 類型的消息，不存入 conversation_history
    const filteredMessages = newMessages.filter(
      (msg) => msg.type !== "candidates" && msg.type !== "final"
    );
    emit("messagesUpdated", filteredMessages);
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
    if (
      !snapshot ||
      snapshot === "{}" ||
      snapshot === lastCandidateSnapshot.value
    ) {
      return;
    }
    lastCandidateSnapshot.value = snapshot;
    buildCandidateMessage();
  },
  { deep: true }
);

watch(
  () => props.finalPlan,
  (val) => {
    const snapshot = JSON.stringify(val || {});
    if (
      !snapshot ||
      snapshot === "{}" ||
      snapshot === lastFinalSnapshot.value
    ) {
      return;
    }
    lastFinalSnapshot.value = snapshot;
  },
  { deep: true }
);

watch(
  () => props.prefilledAnswers,
  (next) => {
    applyPrefilledAnswers(next || {});
  },
  { deep: true, immediate: true }
);

watch(
  () => props.projectId,
  (nextId, prevId) => {
    if (typeof window === "undefined" || nextId === prevId) {
      return;
    }
    if (nextId) {
      void loadProjectState(nextId);
      void setupRealtimeSubscription(nextId);
    } else {
      void teardownRealtimeSubscription();
    }
  },
  { immediate: true }
);

function applyPrefilledAnswers(prefillMap) {
  if (!prefillMap || typeof prefillMap !== "object") {
    return;
  }
  const nextAnswers = { ...questionAnswers.value };
  let hasUpdates = false;
  guidedQuestions.forEach((question) => {
    const existing = nextAnswers[question.id];
    if (existing && existing.trim()) {
      return;
    }
    const candidate = extractPrefillValue(prefillMap, question.id);
    if (candidate) {
      nextAnswers[question.id] = candidate;
      hasUpdates = true;
    }
  });
  if (!hasUpdates) {
    return;
  }
  questionAnswers.value = nextAnswers;
  if (!chatInitialized.value) {
    return;
  }
  if (activeQuestionId.value && nextAnswers[activeQuestionId.value]) {
    upsertAnswerMessage(
      activeQuestionId.value,
      nextAnswers[activeQuestionId.value],
      "prefill"
    );
    activeQuestionId.value = null;
  }
}

function extractPrefillValue(prefillMap, questionId) {
  if (!questionId) {
    return "";
  }
  const direct = prefillMap[questionId];
  if (direct && String(direct).trim()) {
    return String(direct).trim();
  }
  const replyKey = `${questionId}::reply`;
  const fallback = prefillMap[replyKey];
  if (fallback && String(fallback).trim()) {
    return String(fallback).trim();
  }
  return "";
}

function editAnswer(questionId) {
  if (!questionId) {
    return;
  }
  const question = guidedQuestions.find((item) => item.id === questionId);
  if (!question) {
    return;
  }
  editQuestionId.value = question.id;
  editQuestionLabel.value = question.label;
  editQuestionPrompt.value = question.prompt;
  editAnswerDraft.value = questionAnswers.value[question.id] || "";
  isEditModalVisible.value = true;
}

function cancelEditAnswer() {
  isEditModalVisible.value = false;
  editQuestionId.value = null;
  editQuestionLabel.value = "";
  editQuestionPrompt.value = "";
  editAnswerDraft.value = "";
}

function saveEditedAnswer() {
  if (!editQuestionId.value) {
    return;
  }
  const normalized = (editAnswerDraft.value || "").trim();
  questionAnswers.value = {
    ...questionAnswers.value,
    [editQuestionId.value]: normalized,
  };
  upsertAnswerMessage(editQuestionId.value, normalized, "user", false);
  cancelEditAnswer();
}

function getLastAssistantMessageLabel() {
  for (let idx = messages.value.length - 1; idx >= 0; idx -= 1) {
    const message = messages.value[idx];
    if (
      message.role === "assistant" &&
      (message.type === "text" || message.type === "answer") &&
      message.content &&
      message.content.trim()
    ) {
      return message.content.trim();
    }
  }
  return DEFAULT_FILE_IMPORT_LABEL;
}

function openAttachmentModal() {
  fileImportInitialValue.value = draftMessage.value || "";
  fileImportSubLabel.value = getLastAssistantMessageLabel();
  isFileImportOpen.value = true;
}

function handleFileImportConfirm(value) {
  draftMessage.value = value;
  isFileImportOpen.value = false;
}

async function handleEnter(event) {
  if (event.shiftKey) {
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
  if (!props.grantId || !props.templateId) {
    return;
  }
  const normalizedText = draftMessage.value.trim();
  const messageContent = useAIFill
    ? "請AI自動幫我填寫"
    : normalizedText || "無";

  // 添加用户消息到聊天记录
  const userMsg = {
    id: `user-${Date.now()}`,
    role: "user",
    type: "text",
    content: messageContent,
  };
  messages.value.push(userMsg);
  scrollToBottom();

  // 如果有当前的活动问题，更新答案
  if (activeQuestionId.value) {
    questionAnswers.value = {
      ...questionAnswers.value,
      [activeQuestionId.value]: messageContent,
    };
    activeQuestionId.value = null;
  }

  // 发送用户消息到 WebSocket
  if (
    window.chatWebSocket &&
    window.chatWebSocket.readyState === WebSocket.OPEN
  ) {
    const userPayload = {
      user_message: messageContent,
      current_answers: questionAnswers.value,
      project_title: props.projectTitle || "",
      project_summary: props.projectSummary || "",
    };
    isFetchingNextQuestion.value = true;
    window.chatWebSocket.send(JSON.stringify(userPayload));
  }

  draftMessage.value = "";
}

async function requestGeneration() {
  if (!canRequestPlan.value) {
    return;
  }
  if (hasMissingAnswers.value) {
    const confirmed = await confirm({
      title: "尚有問題未回答",
      message: "仍有核心問題尚未完成，可能導致生成內容不完整，是否仍要繼續？",
      confirmText: "繼續生成",
      cancelText: "返回填寫",
      confirmColor: "danger",
    });
    if (!confirmed) {
      return;
    }
  }
  const joinedText = Object.entries(questionAnswers.value)
    .map(([key, value]) => {
      const text = value.reply ?? value;
      return `【${key}】\n${text}`;
    })
    .join("\n\n");

  // Compose final input including project title and summary (same format as GeneratorModeWorkspace)
  const projectPlanName = props.projectTitle || "";
  const projectPlanSummary = props.projectSummary || "";
  const userInput = joinedText;
  const finalUserInput =
    "計劃名稱: " +
    projectPlanName +
    "\n\n計劃摘要: " +
    projectPlanSummary +
    "\n\n" +
    userInput;

  emit("generatePlan", {
    grantId: props.grantId,
    templateId: props.templateId,
    prompt: finalUserInput,
    selectedModel: selectedModel.value || undefined,
  });
}

function handleCandidateConfirm(payload) {
  emit("finalizeCandidates", payload);
}

function buildCandidateMessage() {
  isCandidateSelectorVisible.value = true;
  scrollToBottom();
}

function handleVersionSelect(version) {
  selectedVersion.value = version;
  isVersionModalVisible.value = true;
}

async function handleVersionExport(version) {
  emit("requestExport", { version });
}

function scrollToBottom() {
  nextTick(() => {
    if (!chatContainer.value) {
      return;
    }
    chatContainer.value.scrollTo({
      top: chatContainer.value.scrollHeight,
      behavior: "smooth",
    });
  });
}

function normalizeStoredMessages(entries = []) {
  if (!Array.isArray(entries)) {
    return [];
  }
  return entries
    .map((entry, index) => {
      if (!entry) {
        return null;
      }
      const role = entry.role === "user" ? "user" : "assistant";
      const content = String(entry.content || "").trim();
      if (!content) {
        return null;
      }
      return {
        id: entry.id || `history-${index}-${Date.now()}`,
        role,
        type: entry.type || "text",
        content,
      };
    })
    .filter(Boolean);
}

function normalizeStoredAnswers(rawAnswers = {}) {
  if (!rawAnswers || typeof rawAnswers !== "object") {
    return {};
  }
  const normalized = {};
  Object.entries(rawAnswers).forEach(([key, value]) => {
    const text = String(value ?? "").trim();
    if (!key || !text) {
      return;
    }
    normalized[key] = text;
  });
  return normalized;
}

function applyProjectState(record = {}) {
  if (!record || typeof record !== "object") {
    return;
  }
  const historyEntries = normalizeStoredMessages(record.conversation_history);
  if (historyEntries.length) {
    messages.value = historyEntries;
    scrollToBottom();
  }
  const storedAnswers = normalizeStoredAnswers(
    record.stored_answer?.chat_answers || record.stored_answer?.chatAnswers
  );
  if (Object.keys(storedAnswers).length) {
    questionAnswers.value = {
      ...questionAnswers.value,
      ...storedAnswers,
    };
  }
}

async function loadProjectState(projectId) {
  if (!projectId || typeof window === "undefined") {
    return;
  }
  try {
    const { data, error } = await supabase
      .from("projects")
      .select("conversation_history, stored_answer")
      .eq("id", projectId)
      .maybeSingle();
    if (error) {
      console.error("Failed to load project chat state", error.message);
      return;
    }
    if (data) {
      applyProjectState(data);
    }
  } catch (err) {
    console.error("Unexpected error while loading project state", err);
  }
}

async function setupRealtimeSubscription(projectId) {
  if (!projectId || typeof window === "undefined") {
    return;
  }
  await teardownRealtimeSubscription();

  projectRealtimeChannel.value = supabase
    .channel(`project-${projectId}`)
    .on(
      "postgres_changes",
      {
        event: "*",
        schema: "public",
        table: "projects",
      },
      (payload) => {
        if (payload.new?.id !== projectId) return;
        applyProjectState(payload.new || {});
      }
    )
    .subscribe();
}

async function teardownRealtimeSubscription() {
  if (!projectRealtimeChannel.value) {
    return;
  }
  try {
    await projectRealtimeChannel.value.unsubscribe();
    await supabase.removeChannel(projectRealtimeChannel.value);
  } catch (err) {
    console.warn("Failed to cleanup realtime subscription", err);
  } finally {
    projectRealtimeChannel.value = null;
  }
}

onMounted(() => {
  chatInitialized.value = true;
  emit("guidedQuestionsUpdated", guidedQuestions);
  scrollToBottom();

  // 初始化 WebSocket 连接（虚拟问题用于建立连接）
  if (props.grantId && props.templateId) {
    const dummyQuestion = { id: "init", label: "初始化", prompt: "初始化" };
    void streamAIGuidanceMessage(dummyQuestion);
  }
});

onBeforeUnmount(() => {
  void teardownRealtimeSubscription();
});

function buildGuidedQuestionList() {
  const base = [
    // {
    //   id: "项目形容"",
    //   label: "核心構想",
    //   prompt: "請先描述計畫的主要想法、產品或服務摘要。",
    // },
  ];

  const sections = buildDynamicSections(createEmptyDynamicValues());
  sections.forEach((section) => {
    section.fields.forEach((field) => {
      const id = `${section.sectionId}::${field.propertyKey}`;
      const description = field.description?.trim()
        ? `\n${field.description.trim()}`
        : "";
      base.push({
        id,
        label: `${section.sectionName}｜${field.title}`,
        prompt: `${field.title}${description}`.trim(),
      });
    });
  });

  return base;
}
</script>
<style scoped>
/* Custom scrollbar styling */
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thumb-indigo-500::-webkit-scrollbar-thumb,
.scrollbar-thumb-rose-300::-webkit-scrollbar-thumb {
  background-color: #ffb4a8;
  border-radius: 3px;
}

.scrollbar-thumb-indigo-500::-webkit-scrollbar-thumb:hover,
.scrollbar-thumb-rose-300::-webkit-scrollbar-thumb:hover {
  background-color: #ff998e;
}

.scrollbar-track-slate-800::-webkit-scrollbar-track,
.scrollbar-track-transparent::-webkit-scrollbar-track {
  background-color: transparent;
  border-radius: 3px;
}

/* Firefox scrollbar */
.scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: #ffb4a8 transparent;
}
</style>
