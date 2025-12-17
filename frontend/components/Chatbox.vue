<template>
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
              class="flex h-2 w-2 rounded-full bg-green-500 shadow-lg shadow-green-500/50"
            ></span>
            智慧推演進行中 · {{ activeGrantName }}
            <span v-if="activeTemplateName">/ {{ activeTemplateName }}</span>
          </p>
        </div>
      </div>
      <div class="flex flex-wrap gap-3">
        <button
          type="button"
          class="rounded-full border border-[#ff9380] px-5 py-2 text-sm font-semibold text-[#ff4b5c] transition hover:bg-[#fff2ef] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!hasCandidatePlan"
          @click="openCandidateSelector"
        >
          檢視推演結果
        </button>
        <button
          type="button"
          class="rounded-full bg-[#ff4b5c] px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-[#ff4b5c]/30 transition hover:-translate-y-0.5 hover:bg-[#ff2f45] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!canRequestPlan || isGenerating"
          @click="requestGeneration"
        >
          {{ isGenerating ? "推演中..." : "啟動精準推演" }}
        </button>
      </div>
    </header>

    <div class="mt-6 h-[50vh]">
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
            :class="message.role === 'user' ? 'flex-row-reverse' : 'flex-row'"
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
                  <p class="text-sm leading-relaxed whitespace-pre-line">
                    {{ message.content }}
                  </p>
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
                        message.source === "prefill" ? "已帶入答案" : "最新回答"
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
                  <p class="mt-2 text-sm text-slate-700 whitespace-pre-line">
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

              <template v-else-if="message.type === 'candidates'">
                <article
                  class="rounded-[28px] border border-[#ffd6c9] bg-[#fff5f1] px-5 py-5 shadow-md"
                >
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-sm font-semibold text-[#ff4b5c]">
                        候選章節已就緒
                      </p>
                      <p class="text-xs text-slate-500">
                        已為
                        {{ message.sectionCount || sections.length }}
                        個章節生成提案。
                      </p>
                    </div>
                    <button
                      type="button"
                      class="rounded-full bg-[#ff4b5c] px-4 py-2 text-xs font-semibold text-white shadow"
                      @click="openCandidateSelector"
                    >
                      查看詳情
                    </button>
                  </div>
                </article>
              </template>

              <template v-else-if="message.type === 'final'">
                <article
                  class="rounded-[32px] border-2 border-[#ffb4a8] bg-white px-6 py-5 shadow-xl"
                >
                  <header
                    class="flex flex-wrap items-center justify-between gap-3"
                  >
                    <div>
                      <p
                        class="text-xs font-semibold uppercase tracking-[0.4em] text-[#ff7a5b]"
                      >
                        計畫推演報告
                        <span class="ml-2 text-[11px] text-slate-400"
                          >Plan Deduction</span
                        >
                      </p>
                      <p class="mt-2 text-sm text-slate-600">
                        根據資料庫的情境與文件分析，以下為符合當前條件的推演結果摘要。
                      </p>
                    </div>
                    <span
                      class="rounded-full bg-[#fff1ea] px-3 py-1 text-xs font-semibold text-[#ff6b3d]"
                    >
                      專案熱度高
                    </span>
                  </header>
                  <div class="mt-4 space-y-4">
                    <div
                      v-for="section in message.sections"
                      :key="section.id"
                      class="rounded-2xl bg-[#fff7f3] px-4 py-3"
                    >
                      <p
                        class="text-xs font-semibold uppercase tracking-[0.3em] text-[#ff8a70]"
                      >
                        {{ section.name }}
                      </p>
                      <div
                        v-if="section.html"
                        class="mt-2 text-sm leading-relaxed text-slate-700 prose prose-sm prose-slate"
                        v-html="section.html"
                      ></div>
                      <p
                        v-else
                        class="mt-2 text-sm leading-relaxed text-slate-700 whitespace-pre-line"
                      >
                        {{ section.content }}
                      </p>
                    </div>
                  </div>
                  <div class="mt-5 flex flex-wrap gap-3">
                    <button
                      type="button"
                      class="rounded-full border border-[#ffb4a8] px-5 py-2 text-sm font-semibold text-[#ff4b5c] hover:bg-[#fff2ef]"
                      @click="emit('requestExport')"
                    >
                      下載報告 Word
                    </button>
                    <button
                      type="button"
                      class="rounded-full bg-[#ff4b5c] px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-[#ff4b5c]/20"
                      @click="emit('backToStageOne')"
                    >
                      重新啟動推演
                    </button>
                  </div>
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
      </div>
    </div>

    <footer class="mt-2 rounded-[32px] bg-white px-5 py-5 shadow-xl">
      <textarea
        v-model="draftMessage"
        class="mt-3 h-16 w-full resize-none rounded-[28px] border border-[#edf0ff] bg-[#f8f9ff] p-4 text-sm text-slate-700 placeholder-slate-400 outline-none focus:border-[#ff4b5c] focus:bg-white focus:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
        :placeholder="composerPlaceholder"
        :disabled="isGenerationComplete"
        @keydown.enter.prevent="handleEnter"
      ></textarea>
      <div class="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          class="rounded-full border border-[#dfe3ff] px-5 py-2 text-sm font-semibold text-[#6c719b] hover:bg-[#f4f5ff] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!canSendMessage || isGenerationComplete"
          @click="handleSend"
        >
          回覆當前問題
        </button>
        <button
          type="button"
          class="rounded-full bg-gradient-to-r from-[#ff9b6d] to-[#ff4b6b] px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-[#ff4b6b]/30 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!canRequestPlan || isGenerating"
          @click="requestGeneration"
        >
          {{ isGenerating ? "推演中..." : "輸出完整推演" }}
        </button>
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
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import PlanCandidateSelector from "~/components/PlanCandidateSelector.vue";
import AnswerEditModal from "~/components/AnswerEditModal.vue";
import { useConfirm } from "~/composables/useConfirm";
import {
  buildDynamicSections,
  createEmptyDynamicValues,
} from "~/utils/dynamicSchema";
import { renderPlanToHtml } from "~/utils/exportToWord";

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
  useModelType: { type: String, default: "external" },
  prefilledAnswers: { type: Object, default: () => ({}) },
});

const isGenerating = computed(() => props.isGenerating);

const useModelType = computed(() => props.useModelType);
const { confirm } = useConfirm();

const emit = defineEmits([
  "generatePlan",
  "finalizeCandidates",
  "requestExport",
  "toggleModel",
  "backToStageOne",
  "messagesUpdated",
]);

const messages = ref([
  {
    id: "intro",
    role: "assistant",
    type: "text",
    content: "歡迎使用對話式計畫書生成器，請依序輸入想法並提交給 AI。",
  },
]);

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
const nextQuestionIndex = ref(0);
const questionFlowCompleted = ref(false);

const chatContainer = ref(null);
const draftMessage = ref("");
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

const activeGrantName = computed(() => props.grantName || "尚未選擇");
const activeTemplateName = computed(() => props.templateName || "");
const currentQuestion = computed(
  () =>
    guidedQuestions.find((item) => item.id === activeQuestionId.value) || null
);

const composerPlaceholder = computed(() => {
  if (!props.grantId || !props.templateId) {
    return "請先完成第一階段的設定";
  }
  if (currentQuestion.value) {
    return `回答：${currentQuestion.value.prompt}`;
  }
  if (!allQuestionsAnswered.value) {
    return "請等待下一個問題...";
  }
  return "所有核心問題已完成，請生成候選計畫";
});

const canSendMessage = computed(() => {
  // Only allow sending if we're still answering questions
  return Boolean(
    props.grantId &&
      props.templateId &&
      (currentQuestion.value || !allQuestionsAnswered.value)
  );
});

const canRequestPlan = computed(() => {
  return Boolean(props.grantId && props.templateId);
});

const hasCandidatePlan = computed(
  () => Object.keys(props.candidatePlan || {}).length > 0
);

const hasMissingAnswers = computed(() => !allQuestionsAnswered.value);

function questionMessageExists(questionId) {
  if (!questionId) {
    return false;
  }
  return messages.value.some(
    (msg) => msg.type === "question" && msg.questionId === questionId
  );
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

  const payload = {
    id:
      index >= 0
        ? messages.value[index].id
        : `answer-${questionId}-${Date.now()}`,
    role: "user",
    type: "answer",
    questionId,
    content: text,
    source,
  };

  if (index >= 0) {
    messages.value[index] = { ...messages.value[index], ...payload };
  } else {
    messages.value.push(payload);
  }
  if (shouldScroll) {
    scrollToBottom();
  }
}

watch(
  () => props.referenceSummaries,
  () => {
    scrollToBottom();
  },
  { deep: true }
);

watch(
  messages,
  (newMessages) => {
    emit("messagesUpdated", newMessages);
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
    buildFinalMessage();
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
  askNextQuestion();
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

function appendQuestionMessage(question) {
  if (!question || !question.id || questionMessageExists(question.id)) {
    return;
  }
  messages.value.push({
    id: `question-${question.id}-${Date.now()}`,
    role: "assistant",
    type: "question",
    label: question.label,
    content: question.prompt,
    questionId: question.id,
  });
}

function finalizeQuestionFlowMessage() {
  if (questionFlowCompleted.value) {
    return;
  }
  messages.value.push({
    id: `qa-complete-${Date.now()}`,
    role: "assistant",
    type: "text",
    content: "已完成所有核心問題，隨時可以生成候選計畫。",
  });
  questionFlowCompleted.value = true;
  scrollToBottom();
}

function handleEnter(event) {
  if (event.shiftKey) {
    return;
  }
  if (!canSendMessage.value) {
    event.preventDefault();
    return;
  }
  event.preventDefault();
  handleSend();
}

function handleSend() {
  if (!props.grantId || !props.templateId) {
    return;
  }
  const normalizedText = draftMessage.value.trim();
  const messageContent = normalizedText || "無";
  const currentId = activeQuestionId.value;
  const questionMeta = guidedQuestions.find((item) => item.id === currentId);

  if (currentId && questionMeta) {
    const isEditing =
      questionAnswers.value[currentId] &&
      questionAnswers.value[currentId].trim();
    upsertAnswerMessage(currentId, messageContent, "user");
    questionAnswers.value = {
      ...questionAnswers.value,
      [currentId]: messageContent,
    };
    activeQuestionId.value = null;
    if (!isEditing) {
      askNextQuestion();
    }
  } else {
    const payload = {
      id: `user-${Date.now()}`,
      role: "user",
      type: "text",
      content: messageContent,
    };
    messages.value.push(payload);
  }

  draftMessage.value = "";
  scrollToBottom();
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
  const promptParts = [];

  if (guidedQuestions.length) {
    const qaText = guidedQuestions
      .map((question, idx) => {
        const answer = questionAnswers.value[question.id] || "尚未提供";
        return `${idx + 1}. ${question.label}\n${answer}`;
      })
      .join("\n\n");
    promptParts.push(`${qaText}`);
  }

  emit("generatePlan", {
    grantId: props.grantId,
    templateId: props.templateId,
    prompt: promptParts.join("\n\n"),
  });
}

function openCandidateSelector() {
  if (!props.candidatePlan || !Object.keys(props.candidatePlan).length) {
    return;
  }
  isCandidateSelectorVisible.value = true;
}

function handleCandidateConfirm(payload) {
  emit("finalizeCandidates", payload);
}

function buildCandidateMessage() {
  isCandidateSelectorVisible.value = true;
  isGenerationComplete.value = true;
  messages.value.push({
    id: `candidates-${Date.now()}`,
    role: "assistant",
    type: "candidates",
    sectionCount: props.sections.length,
  });
  scrollToBottom();
}

function askNextQuestion() {
  while (nextQuestionIndex.value < guidedQuestions.length) {
    const question = guidedQuestions[nextQuestionIndex.value];
    appendQuestionMessage(question);
    const existingAnswer = questionAnswers.value[question.id];
    nextQuestionIndex.value += 1;

    if (existingAnswer && existingAnswer.trim()) {
      upsertAnswerMessage(question.id, existingAnswer, "prefill");
      continue;
    }

    activeQuestionId.value = question.id;
    scrollToBottom();
    return;
  }

  activeQuestionId.value = null;
  finalizeQuestionFlowMessage();
}

function buildFinalMessage() {
  const sections = props.sections
    .map((section) => {
      const content = props.finalPlan[section.id]?.content;
      if (!content) {
        return null;
      }
      return {
        id: section.id,
        name: section.name,
        content,
        html: generateHtmlForFinalSection(section, content),
      };
    })
    .filter(Boolean);

  if (!sections.length) {
    return;
  }

  messages.value.push({
    id: `final-${Date.now()}`,
    role: "assistant",
    type: "final",
    sections,
  });
  scrollToBottom();
}

function generateHtmlForFinalSection(section, content) {
  try {
    return renderPlanToHtml(
      [
        {
          id: section.id,
          name: section.name || section.title || section.id,
          json_schema: section.json_schema,
        },
      ],
      {
        [section.id]: {
          content,
        },
      }
    );
  } catch (error) {
    console.error("無法渲染最終章節", section?.id, error);
    return "";
  }
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

onMounted(() => {
  chatInitialized.value = true;
  scrollToBottom();
  askNextQuestion();
});

function buildGuidedQuestionList() {
  const base = [
    {
      id: "main-idea",
      label: "核心構想",
      prompt: "請先描述計畫的主要想法、產品或服務摘要。",
    },
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
