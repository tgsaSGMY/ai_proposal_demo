<!-- 聊天框组件：显示聊天消息列表和输入框，支持发送消息 -->
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
              <p class="text-lg font-semibold text-slate-900">補助引擎</p>
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
              ref="composerRef"
              v-model="draftMessage"
              class="mt-3 w-full min-h-16 resize-none rounded-[28px] border border-[#edf0ff] bg-[#f8f9ff] p-4 pr-14 text-sm text-slate-700 placeholder-slate-400 outline-none focus:border-[#ff4b5c] focus:bg-white focus:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 transition-all overflow-hidden"
              :placeholder="composerPlaceholder"
              @keydown.enter.prevent="handleEnter"
              @input="handleTextareaInput"
              @compositionstart="handleCompositionStart"
              @compositionupdate="handleCompositionUpdate"
              @compositionend="handleCompositionEnd"
            ></textarea>
            <button
              type="button"
              class="absolute right-6 bottom-5 flex h-10 w-10 items-center justify-center rounded-2xl border border-[#e4e7ff] bg-white text-[#ff6b6b] shadow hover:bg-[#fff6f6]"
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
              <button
                type="button"
                class="rounded-full bg-gradient-to-r from-[#ff9b6d] to-[#ff4b6b] px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-[#ff4b6b]/30 disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="!canRequestPlan || isGenerating"
                @click="requestGeneration"
              >
                {{ isGenerating ? "推演中..." : "輸出完整推演" }}
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
        :question-answer-meta="questionAnswerMeta"
        @selectVersion="handleVersionSelect"
        @editQuestion="handleEditQuestion"
      />
    </div>

    <PlanVersionModal
      :visible="isVersionModalVisible"
      :version="selectedVersion"
      :plan-sections="sections"
      :loading="isGenerating"
      :timeline-loading="timelineLoading"
      @close="isVersionModalVisible = false"
      @export="handleVersionExport"
      @updateVersion="handleVersionUpdateRequest"
      @downloadTimeline="handleTimelineDownload"
    />
    <FieldFileImportModal
      v-model:is-open="isFileImportOpen"
      field-title="聊天輸入"
      field-description="上傳文件後可自動擷取內容填入訊息"
      :field-label="fileImportFieldLabel"
      :field-value="fileImportInitialValue"
      @confirm="handleFileImportConfirm"
    />

    <EditFieldModal
      v-model:is-open="isEditFieldModalOpen"
      title="編輯欄位"
      :label="editFieldLabel"
      :initial-value="editFieldInitialValue"
      @confirm="handleEditConfirm"
    />

    <RecommendNameModal
      v-model:is-open="isRecommendModalOpen"
      :original-name="props.projectTitle"
      :suggestions="recommendOptions"
      :loading="isFetchingRecommend"
      @confirm="handleRecommendConfirm"
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
import EditFieldModal from "~/components/editor/helper/EditFieldModal.vue";
import RecommendNameModal from "~/components/editor/helper/RecommendNameModal.vue";
import { useConfirm } from "~/composables/useConfirm";
import { useNotifications } from "~/composables/useNotifications";
import {
  buildDynamicSections,
  createEmptyDynamicValues,
} from "~/utils/dynamicSchema";
import { renderPlanToHtml } from "~/utils/exportToWord";
import { supabase } from "~/utils/supabaseClient";

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const props = defineProps({
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
  projectId: { type: String, default: "" },
  savedPlanVersions: { type: Array, default: () => [] },
  showSidebar: { type: Boolean, default: false },
  selectedModel: { type: String, default: "" },
});

const isGenerating = computed(() => props.isGenerating);
const showSidebar = computed(() => Boolean(props.showSidebar));

const { confirm } = useConfirm();
const { error: notifyError } = useNotifications();

const emit = defineEmits([
  "generatePlan",
  "updateProjectTitle",
  "finalizeCandidates",
  "requestExport",
  "backToStageOne",
  "messagesUpdated",
  "questionAnswersUpdated",
  "guidedQuestionsUpdated",
  "aiResponseComplete",
  "requestVersionUpdate",
]);

const messages = ref([]);
const lastSentUserIndex = ref(null);

const guidedQuestions = buildGuidedQuestionList();
const totalQuestions = guidedQuestions.length;
const questionAnswers = ref({});
const questionAnswerMeta = ref({});
const answeredCount = computed(() =>
  guidedQuestions.reduce((count, question) => {
    const answer = questionAnswers.value[question.id];
    return answer && answer.trim() ? count + 1 : count;
  }, 0),
);
const allQuestionsAnswered = computed(
  () => totalQuestions === 0 || answeredCount.value === totalQuestions,
);
const activeQuestionId = ref(null);

const chatContainer = ref(null);
const draftMessage = ref("");
const composerRef = ref(null);
const isFileImportOpen = ref(false);
const DEFAULT_FILE_IMPORT_LABEL = "聊天輸入";
const fileImportInitialValue = ref("");
const fileImportFieldLabel = ref(DEFAULT_FILE_IMPORT_LABEL);

// Edit-field modal state
const isEditFieldModalOpen = ref(false);
const editFieldLabel = ref("");
const editFieldInitialValue = ref("");
const editFieldQuestionId = ref(null);

// Recommend name modal state
const isRecommendModalOpen = ref(false);
const recommendOptions = ref([]);
const isFetchingRecommend = ref(false);
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
const timelineLoading = ref(false);
const textareaMinHeight = 64; // 4rem base height
const textareaMaxHeight = 184; // 約 11.5rem 上限

const activeGrantName = computed(() => props.grantName || "尚未選擇");
const activeTemplateName = computed(() => props.templateName || "");
// 轉義 HTML 字符防止 XSS 攻擊，將特殊字符轉換為 HTML Entity
function escapeHtml(unsafe) {
  return String(unsafe || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// 格式化聊天消息用於顯示：轉義 HTML、轉換粗體標記、保留換行符
function formatMessageForDisplay(raw) {
  const text = raw == null ? "" : String(raw);
  // Remove everything from 【回復結束】 onwards (hidden reply block)
  let cleaned = text.replace(/【回復結束】[\s\S]*/g, "");
  // escape HTML first
  let out = escapeHtml(cleaned);
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
    !isFetchingNextQuestion.value,
  );
});

const canRequestPlan = computed(() => {
  return Boolean(props.grantId && props.templateId);
});

const hasCandidatePlan = computed(
  () => Object.keys(props.candidatePlan || {}).length > 0,
);

const hasMissingAnswers = computed(() => !allQuestionsAnswered.value);

// 獲取當前 ISO 時間戳
function getCurrentTimestamp() {
  return new Date().toISOString();
}

// 從引導問題列表中查找指定 ID 的問題元數據
function getQuestionMeta(questionId) {
  if (!questionId) {
    return null;
  }
  return guidedQuestions.find((item) => item.id === questionId) || null;
}

function touchAnswerMeta(questionId, timestamp) {
  if (!questionId) {
    return;
  }
  const nextTimestamp = timestamp || getCurrentTimestamp();
  questionAnswerMeta.value = {
    ...questionAnswerMeta.value,
    [questionId]: {
      ...(questionAnswerMeta.value[questionId] || {}),
      updated_at: nextTimestamp,
    },
  };
}

// 構建用於 AI 對話的歷史消息負載，最多包含指定數量的最近消息，並格式化答案信息
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

// 通過 WebSocket 建立連接並流式接收 AI 的引導消息和問題回答
// 初始化階段會建立 WebSocket 連接，之後通過此連接發送用戶消息和接收 AI 回應
// 支持流式接收、自動填充答案、暫停/取消操作等功能
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
        current_answers_meta: questionAnswerMeta.value,
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
            timestamp: getCurrentTimestamp(),
          };
          messages.value.push(aiMsg);
          // ensure we have a recorded last user index (in case it wasn't set)
          if (lastSentUserIndex.value === null) {
            for (let i = messages.value.length - 1; i >= 0; i -= 1) {
              if (messages.value[i].role === "user") {
                lastSentUserIndex.value = i;
                break;
              }
            }
          }
          scrollToBottom();
        } else if (msg.event === "chunk") {
          // 追加到最后一个 AI 消息
          const lastMsg = messages.value[messages.value.length - 1];
          if (lastMsg && lastMsg.role === "assistant" && lastMsg.isStreaming) {
            lastMsg.content += msg.data;

            // Check if response end marker is reached
            if (lastMsg.content.includes("【回復結束】")) {
              // Stop streaming and mark as done
              lastMsg.isStreaming = false;
              lastSentUserIndex.value = null;
              isFetchingNextQuestion.value = false;
              emit("aiResponseComplete");
            }
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
              touchAnswerMeta(fieldId);
              // clear last sent user index when done
              lastSentUserIndex.value = null;
            }
          });
        } else if (msg.event === "done") {
          const lastMsg = messages.value[messages.value.length - 1];
          if (lastMsg && lastMsg.isStreaming) {
            lastMsg.isStreaming = false;
          }
          lastSentUserIndex.value = null;
          isFetchingNextQuestion.value = false;
          // Emit event to trigger save after AI response completes
          emit("aiResponseComplete");
        } else if (msg.event === "cancelled") {
          // Remove streaming AI message and restore user message into draft
          try {
            // remove last streaming assistant message
            for (let i = messages.value.length - 1; i >= 0; i -= 1) {
              const m = messages.value[i];
              if (m.role === "assistant" && m.isStreaming) {
                messages.value.splice(i, 1);
                break;
              }
            }
            // remove the user's message that triggered this stream if we tracked it
            if (lastSentUserIndex.value !== null) {
              const idx = lastSentUserIndex.value;
              if (messages.value[idx] && messages.value[idx].role === "user") {
                messages.value.splice(idx, 1);
              }
            } else if (msg.restore_user_message) {
              // fallback: remove the last user message that matches the restored content
              for (let i = messages.value.length - 1; i >= 0; i -= 1) {
                const m = messages.value[i];
                if (
                  m.role === "user" &&
                  m.content === msg.restore_user_message
                ) {
                  messages.value.splice(i, 1);
                  break;
                }
              }
            }

            // restore user's message into draft
            if (msg.restore_user_message) {
              draftMessage.value = msg.restore_user_message;
            }
            // clear tracker
            lastSentUserIndex.value = null;
          } catch (e) {
            console.error("Error handling cancelled event", e);
          }
          isFetchingNextQuestion.value = false;
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

// 更新或插入答案消息，如果無內容則刪除該消息，支持自動滾動到底部
function upsertAnswerMessage(
  questionId,
  content,
  source = "user",
  shouldScroll = true,
) {
  if (!questionId) {
    return;
  }
  const text = (content || "").trim();
  const index = messages.value.findIndex(
    (msg) => msg.type === "answer" && msg.questionId === questionId,
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
      (msg) => msg.type !== "candidates" && msg.type !== "final",
    );
    emit("messagesUpdated", filteredMessages);
  },
  { deep: true },
);

watch(
  questionAnswers,
  (newAnswers) => {
    emit("questionAnswersUpdated", newAnswers);
  },
  { deep: true },
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
  { deep: true },
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
  { deep: true },
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
  { immediate: true },
);

// 從傳遞映射中提取預填充值，首先查找直接對應的字段，其次查找 ::reply 格式的字段
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

// 打開編輯答案模態框，初始化編輯狀態和表單資料
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

// 取消編輯答案，重置編輯狀態和表單資料
function cancelEditAnswer() {
  isEditModalVisible.value = false;
  editQuestionId.value = null;
  editQuestionLabel.value = "";
  editQuestionPrompt.value = "";
  editAnswerDraft.value = "";
}

// 保存編輯的答案，更新問題答案狀態，同步答案消息到聊天記錄
function saveEditedAnswer() {
  if (!editQuestionId.value) {
    return;
  }
  const normalized = (editAnswerDraft.value || "").trim();
  questionAnswers.value = {
    ...questionAnswers.value,
    [editQuestionId.value]: normalized,
  };
  touchAnswerMeta(editQuestionId.value);
  upsertAnswerMessage(editQuestionId.value, normalized, "user", false);
  cancelEditAnswer();
}

// 獲取最後一個 AI 助手消息的內容，用作檔案匯入提示標籤，預設值為預設標籤
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

// 打開檔案匯入模態框，初始化欄位標籤和初始值
function openAttachmentModal() {
  fileImportInitialValue.value = draftMessage.value || "";
  fileImportFieldLabel.value = getLastAssistantMessageLabel();
  isFileImportOpen.value = true;
}

// 處理檔案匯入確認，更新草稿消息並關閉模態框
function handleFileImportConfirm(value) {
  draftMessage.value = value;
  isFileImportOpen.value = false;
}

function resolveTextarea(target) {
  if (target instanceof HTMLTextAreaElement) {
    return target;
  }
  if (target?.target instanceof HTMLTextAreaElement) {
    return target.target;
  }
  return composerRef.value;
}

// 自动调整 textarea 高度，根据内容自动扩容
function autoResizeTextarea(target, immediate = false) {
  const runResize = () => {
    const textarea = resolveTextarea(target);
    if (!textarea) {
      return;
    }

    textarea.style.height = "auto";
    const fullHeight = textarea.scrollHeight;
    const clampedHeight = Math.min(
      textareaMaxHeight,
      Math.max(fullHeight, textareaMinHeight),
    );
    textarea.style.height = `${clampedHeight}px`;
    const isOverflowing = fullHeight > textareaMaxHeight;
    textarea.style.overflowY = isOverflowing ? "auto" : "hidden";
    if (isOverflowing) {
      textarea.scrollTop = textarea.scrollHeight;
    }
  };

  if (immediate) {
    runResize();
  } else {
    nextTick(runResize);
  }
}

function resetTextareaHeight() {
  const textarea = composerRef.value;
  if (!textarea) {
    return;
  }
  textarea.style.height = `${textareaMinHeight}px`;
  textarea.style.overflowY = "hidden";
}

function handleTextareaInput(event) {
  autoResizeTextarea(event, true);
}

function handleCompositionStart(event) {
  autoResizeTextarea(event, true);
}

function handleCompositionUpdate(event) {
  autoResizeTextarea(event, true);
}

function handleCompositionEnd(event) {
  autoResizeTextarea(event, true);
}

// 處理 Enter 鍵按下事件，支持 Shift+Enter 換行，否則發送消息
async function handleEnter(event) {
  if (event.shiftKey) {
    // Shift+Enter: 插入換行符，文字自動換行
    const textarea = event.target;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    draftMessage.value =
      draftMessage.value.substring(0, start) +
      "\n" +
      draftMessage.value.substring(end);

    // 執行 input 事件以觸發自動調整高度
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
  // 發送後重置高度
  await handleSend();
}

// 發送用戶消息到 AI，添加到聊天記錄，同步到 WebSocket 連接，支持 AI 自動填寫模式
async function handleSend(useAIFill = false) {
  if (!props.grantId || !props.templateId) {
    return;
  }
  const normalizedText = draftMessage.value.trim() || "無";
  const messageContent = useAIFill ? "請AI自動幫我填寫" : normalizedText;

  // 添加用户消息到聊天记录
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

  // 如果有当前的活动问题，更新答案
  if (activeQuestionId.value) {
    questionAnswers.value = {
      ...questionAnswers.value,
      [activeQuestionId.value]: messageContent,
    };
    touchAnswerMeta(activeQuestionId.value);
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
      current_answers_meta: questionAnswerMeta.value,
      project_title: props.projectTitle || "",
      project_summary: props.projectSummary || "",
    };
    isFetchingNextQuestion.value = true;
    window.chatWebSocket.send(JSON.stringify(userPayload));
  }

  draftMessage.value = "";
  nextTick(() => {
    resetTextareaHeight();
  });
}

// 暫停 AI 回應，通過 WebSocket 發送暫停命令
function handlePause() {
  if (
    window.chatWebSocket &&
    window.chatWebSocket.readyState === WebSocket.OPEN
  ) {
    try {
      window.chatWebSocket.send(JSON.stringify({ action: "pause" }));
    } catch (e) {
      console.error("Failed to send pause action", e);
    }
  }
}

// 請求生成完整計畫書，如果有未回答問題則提示確認，後續調用推薦名稱 API
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

  // Fetch recommendations and show modal instead of directly generating
  isFetchingRecommend.value = true;
  isRecommendModalOpen.value = true;
  recommendOptions.value = [];

  try {
    const resp = await fetch(`${API_BASE_URL}/recommend_project_names`, {
      method: "POST",
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
    if (resp.ok && data?.names) {
      recommendOptions.value = data.names;
    } else {
      // fallback: empty list, UI will show original name option
      recommendOptions.value = [];
    }
  } catch (e) {
    console.error("Failed to fetch recommendations", e);
    recommendOptions.value = [];
  } finally {
    isFetchingRecommend.value = false;
  }
}

// 確認推薦的項目名稱，更新父組件的項目標題，然後生成完整計畫書
async function handleRecommendConfirm(selectedName) {
  if (!selectedName) return;

  // Emit update for parent to change project title
  emit("updateProjectTitle", selectedName);

  // Now proceed to generate the full plan with the selected name
  const joinedText = Object.entries(questionAnswers.value)
    .map(([key, value]) => {
      const text = value.reply ?? value;
      return `【${key}】\n${text}`;
    })
    .join("\n\n");

  const projectPlanName = selectedName || props.projectTitle || "";
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
    selectedModel: props.selectedModel || undefined,
  });
}

// 確認候選計畫選擇，發送最終確定事件
function handleCandidateConfirm(payload) {
  emit("finalizeCandidates", payload);
}

// 構建候選消息，顯示候選計畫選擇器
function buildCandidateMessage() {
  isCandidateSelectorVisible.value = true;
  scrollToBottom();
}

// 選擇計畫版本，打開版本詳情模態框
function handleVersionSelect(version) {
  selectedVersion.value = version;
  isVersionModalVisible.value = true;
}

// 處理側邊欄編輯問題事件，打開編輯欄位模態框，初始化編輯狀態
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

// 處理編輯欄位確認，構建更新消息並自動發送給 AI
async function handleEditConfirm(value) {
  try {
    const qLabel = editFieldLabel.value || "";
    const updated = value || "";
    // Construct the message in required format and send immediately
    draftMessage.value = `幫我更改\n${qLabel}\n至\n${updated}`;
    isEditFieldModalOpen.value = false;
    await handleSend();
  } catch (e) {
    console.error("handleEditConfirm error", e);
  }
}

// 導出計畫版本，發送導出請求事件
async function handleVersionExport(version) {
  emit("requestExport", { version });
}

// 下載計畫時間軸 PDF，通過 API 獲取 PDF 文件並下載
async function handleTimelineDownload(version) {
  if (!props.projectId) {
    notifyError("找不到專案資料，請重新整理後再嘗試");
    return;
  }
  if (!version) {
    notifyError("請先選擇要下載的版本");
    return;
  }

  timelineLoading.value = true;
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error("請先登入後再下載時間軸");
    }

    const params = new URLSearchParams();
    if (version.id) {
      params.set("version_id", version.id);
    } else if (version.number) {
      params.set("version_number", String(version.number));
    }

    const query = params.toString() ? `?${params.toString()}` : "";
    const response = await fetch(
      `${API_BASE_URL}/projects/${props.projectId}/timeline/pdf${query}`,
      {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      },
    );

    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(detail || "下載時間軸失敗");
    }

    const blob = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = downloadUrl;
    anchor.download = buildTimelineFilename(version);
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error("Failed to download timeline", error);
    notifyError(error?.message || "下載時間軸失敗，請稍後再試");
  } finally {
    timelineLoading.value = false;
  }
}

// 構建時間軸下載檔案名稱，將計畫名稱和版本資訊組合為安全的檔案名
function buildTimelineFilename(version) {
  const safeTitle = (version?.title || props.projectTitle || "timeline")
    .replace(/[\\/:*?"<>|]/g, "_")
    .trim()
    .replace(/_{2,}/g, "_");
  const versionTag =
    version?.id || (version?.number ? `v${version.number}` : "");
  const suffix = versionTag ? `-${versionTag}` : "";
  return `${safeTitle || "timeline"}${suffix}-timeline.pdf`;
}

// 處理計畫版本更新請求，發送請求事件並關閉版本模態框
function handleVersionUpdateRequest(version) {
  if (!version) {
    return;
  }
  emit("requestVersionUpdate", {
    version,
    selectedModel: props.selectedModel || undefined,
  });
  isVersionModalVisible.value = false;
}

// 滾動聊天容器到底部，使用平滑滾動動畫
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

// 規範化從數據庫加載的聊天消息，驗證角色、內容、時間戳等字段
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
      const timestampCandidate =
        entry.timestamp ||
        entry.created_at ||
        entry.createdAt ||
        entry.time ||
        entry.updated_at ||
        entry.createdAt;
      const normalizedTimestamp = timestampCandidate
        ? String(timestampCandidate)
        : getCurrentTimestamp();
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

// 規範化從數據庫加載的問題答案，驗證鍵名和值，過濾空值
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

function normalizeStoredAnswerMeta(rawMeta = {}) {
  if (!rawMeta || typeof rawMeta !== "object") {
    return {};
  }
  const normalized = {};
  Object.entries(rawMeta).forEach(([key, value]) => {
    if (!key) {
      return;
    }
    let timestamp = "";
    if (typeof value === "string") {
      timestamp = value.trim();
    } else if (value && typeof value === "object") {
      timestamp = String(value.updated_at || value.updatedAt || "").trim();
    }
    if (!timestamp) {
      return;
    }
    normalized[key] = { updated_at: timestamp };
  });
  return normalized;
}

// 應用項目狀態到本地組件狀態，包括聊天歷史和問題答案
function applyProjectState(record = {}) {
  if (!record || typeof record !== "object") {
    return;
  }
  const historyEntries = normalizeStoredMessages(record.conversation_history);
  if (historyEntries.length && !messages.value.length) {
    messages.value = historyEntries;
    scrollToBottom();
  }
  const storedAnswers = normalizeStoredAnswers(
    record.stored_answer?.chat_answers || record.stored_answer?.chatAnswers,
  );
  if (Object.keys(storedAnswers).length) {
    questionAnswers.value = {
      ...questionAnswers.value,
      ...storedAnswers,
    };
  }
  const storedMeta = normalizeStoredAnswerMeta(
    record.stored_answer?.chat_answers_meta ||
      record.stored_answer?.chatAnswersMeta ||
      {},
  );
  if (Object.keys(storedMeta).length) {
    questionAnswerMeta.value = {
      ...questionAnswerMeta.value,
      ...storedMeta,
    };
  }
  Object.keys(storedAnswers).forEach((key) => {
    if (!questionAnswerMeta.value[key]) {
      touchAnswerMeta(
        key,
        record.updated_at || record.updatedAt || getCurrentTimestamp(),
      );
    }
  });
}

// 從 Supabase 數據庫加載項目的聊天歷史和問題答案
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

// 設置 Supabase 實時訂閱，監聽項目資料變更並同步到本地狀態
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
      },
    )
    .subscribe();
}

// 清除 Supabase 實時訂閱，清理資源
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

// 組件掛載時初始化 WebSocket 連接和項目狀態，發送引導問題列表事件
onMounted(() => {
  chatInitialized.value = true;
  emit("guidedQuestionsUpdated", guidedQuestions);
  scrollToBottom();
  autoResizeTextarea();

  // 初始化 WebSocket 连接（虚拟问题用于建立连接）
  if (props.grantId && props.templateId) {
    const dummyQuestion = { id: "init", label: "初始化", prompt: "初始化" };
    void streamAIGuidanceMessage(dummyQuestion);
  }
});

// 組件卸載時清除實時訂閱和資源
onBeforeUnmount(() => {
  void teardownRealtimeSubscription();
});

// 構建引導問題列表，從動態 Schema 提取所有字段信息，支持階層式問題組織
function buildGuidedQuestionList() {
  const base = [];

  const sections = buildDynamicSections(
    createEmptyDynamicValues({
      templateId: props.templateId,
      templateGrantId: props.grantId,
    }),
    {
      templateId: props.templateId,
      templateGrantId: props.grantId,
    },
  );
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
