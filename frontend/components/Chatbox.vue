<template>
  <div
    class="flex flex-col h-full w-full bg-slate-900 text-slate-200 p-6 shadow-2xl"
  >
    <div
      class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4"
    >
      <div>
        <p class="text-xs uppercase tracking-widest text-slate-400">第三階段</p>
        <p class="text-[11px] text-slate-500 mt-1">
          已回答 {{ answeredCount }} / {{ totalQuestions }} 題
        </p>
      </div>
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <span
            class="text-xs sm:text-sm font-semibold"
            :class="
              useModelType === 'internal' ? 'text-indigo-300' : 'text-slate-400'
            "
          >
            內部模型
          </span>
          <button
            @click="() => emit('toggleModel')"
            :class="[
              'relative inline-flex h-5 w-9 items-center rounded-full transition-colors',
              useModelType === 'external' ? 'bg-indigo-600' : 'bg-slate-500',
            ]"
          >
            <span
              :class="[
                'inline-block h-3 w-3 transform rounded-full bg-white transition-transform',
                useModelType === 'external' ? 'translate-x-5' : 'translate-x-1',
              ]"
            />
          </button>
          <span
            class="text-xs sm:text-sm font-semibold"
            :class="
              useModelType === 'external' ? 'text-indigo-300' : 'text-slate-400'
            "
          >
            外部模型
          </span>
        </div>
        <button
          type="button"
          class="px-3 py-1.5 rounded-full border border-slate-400 border-opacity-40 text-slate-200 text-xs sm:text-sm font-semibold bg-transparent disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-800 transition-all"
          @click="() => emit('backToStageOne')"
        >
          重新開始
        </button>
      </div>
      <div
        v-if="activeTemplateName"
        class="text-xs sm:text-sm text-indigo-200 bg-slate-800 bg-opacity-30 px-3 py-2 rounded-full whitespace-nowrap"
      >
        {{ activeGrantName }} · {{ activeTemplateName }}
      </div>
    </div>

    <div
      ref="chatContainer"
      class="flex-1 overflow-y-auto pr-2 sm:pr-3 flex flex-col gap-4 scrollbar-thin scrollbar-thumb-indigo-500 scrollbar-track-slate-800"
    >
      <div
        v-for="message in messages"
        :key="message.id"
        :class="[
          'max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg p-4 rounded-2xl',
          message.role === 'user'
            ? 'self-end bg-purple-900 border border-white border-opacity-10'
            : 'self-start bg-slate-800 bg-opacity-85 border border-slate-500 border-opacity-20',
        ]"
      >
        <template v-if="message.type === 'text'">
          <p class="leading-relaxed whitespace-pre-line">
            {{ message.content }}
          </p>
        </template>

        <template v-else-if="message.type === 'question'">
          <div class="space-y-2">
            <div>
              <p class="text-xs uppercase tracking-wide text-indigo-300">
                {{ message.label }}
              </p>
              <p class="leading-relaxed whitespace-pre-line font-semibold">
                {{ message.content }}
              </p>
            </div>
          </div>
        </template>

        <template v-else-if="message.type === 'answer'">
          <div class="space-y-2">
            <div
              class="flex items-center justify-between gap-2 text-[11px] uppercase tracking-widest"
            >
              <span class="text-slate-300">
                {{ message.source === "prefill" ? "已帶入答案" : "最新回答" }}
              </span>
              <button
                v-if="message.questionId"
                class="text-indigo-200 font-semibold border border-white border-opacity-20 rounded-full px-3 py-0.5 hover:bg-white hover:bg-opacity-10 transition-all"
                type="button"
                @click="() => editAnswer(message.questionId)"
              >
                修改
              </button>
            </div>
            <p class="leading-relaxed whitespace-pre-line">
              {{ message.content }}
            </p>
          </div>
        </template>

        <template
          v-else-if="message.type === 'references' && referenceSummaries.length"
        >
          <div
            class="bg-slate-800 bg-opacity-60 border border-slate-500 border-opacity-20 rounded-2xl p-4 flex flex-col gap-4"
          >
            <p class="text-sm font-semibold">已加入的參考資料</p>
            <ul class="space-y-2">
              <li
                v-for="(summary, idx) in referenceSummaries"
                :key="idx"
                class="flex gap-2 bg-slate-500 bg-opacity-10 rounded-xl p-2"
              >
                <span class="font-semibold text-indigo-300"
                  >#{{ idx + 1 }}</span
                >
                <p class="flex-1 text-sm text-slate-200">{{ summary }}</p>
              </li>
            </ul>
          </div>
        </template>

        <template v-else-if="message.type === 'candidates'">
          <div
            class="bg-slate-800 bg-opacity-60 border border-slate-500 border-opacity-20 rounded-2xl p-4 flex flex-col gap-3"
          >
            <p class="text-sm font-semibold">候選章節已就緒</p>
            <p class="text-xs text-slate-400">
              已為
              {{ message.sectionCount || sections.length }}
              個章節生成候選內容，請打開選擇器確認採用的版本。
            </p>
            <button
              type="button"
              class="self-start px-6 py-2.5 rounded-full font-semibold bg-gradient-to-r from-indigo-600 to-purple-700 text-white hover:from-indigo-500 hover:to-purple-600"
              @click="openCandidateSelector"
            >
              開啟候選選擇器
            </button>
          </div>
        </template>

        <template v-else-if="message.type === 'final'">
          <div
            class="bg-slate-800 bg-opacity-60 border border-slate-500 border-opacity-20 rounded-2xl p-4 flex flex-col gap-4"
          >
            <p class="text-sm font-semibold">最終輸出</p>
            <div class="space-y-4">
              <div
                v-for="section in message.sections"
                :key="section.id"
                class="bg-slate-800 bg-opacity-50 border border-slate-500 border-opacity-20 rounded-2xl p-3"
              >
                <div
                  v-if="section.html"
                  class="prose prose-invert max-w-none text-sm text-slate-100"
                  v-html="section.html"
                ></div>
                <p v-else class="text-sm text-slate-100 whitespace-pre-line">
                  {{ section.content }}
                </p>
              </div>
            </div>
            <button
              class="px-6 py-2.5 rounded-full font-semibold bg-transparent border border-slate-500 border-opacity-40 text-slate-200 hover:bg-slate-700 hover:bg-opacity-30 transition-all duration-200"
              @click="emit('requestExport')"
            >
              下載 Word 檔
            </button>
          </div>
        </template>
      </div>

      <div
        v-if="isGenerating"
        class="flex flex-col items-center justify-center mt-4"
      >
        <div class="flex gap-1">
          <span
            v-for="n in 3"
            :key="n"
            class="w-2 h-2 rounded-full bg-slate-300 animate-bounce"
            :style="{ animationDelay: `${(n - 1) * 0.15}s` }"
          ></span>
        </div>
        <p class="text-xs text-slate-400 mt-2">AI 正在生成候選內容...</p>
      </div>
    </div>

    <div class="mt-6 flex flex-col gap-3">
      <textarea
        v-model="draftMessage"
        class="w-full min-h-32 bg-slate-900 bg-opacity-80 border border-slate-500 border-opacity-20 rounded-2xl p-3.5 text-slate-100 placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed"
        :placeholder="composerPlaceholder"
        :disabled="allQuestionsAnswered || isGenerationComplete"
        @keydown.enter.prevent="handleEnter"
      ></textarea>
      <div class="flex gap-3 flex-wrap">
        <button
          class="px-6 py-2.5 rounded-full font-semibold bg-slate-600 bg-opacity-20 border border-transparent text-slate-100 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-opacity-30 transition-all duration-200"
          type="button"
          @click="handleSend"
          :disabled="!canSendMessage || isGenerationComplete"
          :title="
            isGenerationComplete
              ? '已生成計畫，無法傳送'
              : !canSendMessage
              ? '所有核心問題已完成，請生成候選計畫'
              : ''
          "
        >
          傳送
        </button>
        <button
          class="px-6 py-2.5 rounded-full font-semibold bg-gradient-to-r from-indigo-600 to-purple-700 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:from-indigo-500 hover:to-purple-600 transition-all duration-200"
          type="button"
          @click="requestGeneration"
          :disabled="!canRequestPlan || isGenerating || isGenerationComplete"
        >
          {{ isGenerating ? "等待回應..." : "生成計畫候選" }}
        </button>
      </div>
    </div>

    <PlanCandidateSelector
      :visible="isCandidateSelectorVisible"
      :candidate-plan="candidatePlan"
      :sections="sections"
      @confirm="handleCandidateConfirm"
      @close="isCandidateSelectorVisible = false"
    />
  </div>

  <AnswerEditModal
    :visible="isEditModalVisible"
    :question-label="editQuestionLabel"
    :question-prompt="editQuestionPrompt"
    v-model:draft="editAnswerDraft"
    @cancel="cancelEditAnswer"
    @save="saveEditedAnswer"
  />
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

.scrollbar-thumb-indigo-500::-webkit-scrollbar-thumb {
  background-color: rgb(99, 102, 241);
  border-radius: 3px;
}

.scrollbar-thumb-indigo-500::-webkit-scrollbar-thumb:hover {
  background-color: rgb(79, 70, 229);
}

.scrollbar-track-slate-800::-webkit-scrollbar-track {
  background-color: rgb(30, 41, 59);
  border-radius: 3px;
}

/* Firefox scrollbar */
.scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: rgb(99, 102, 241) rgb(30, 41, 59);
}
</style>
