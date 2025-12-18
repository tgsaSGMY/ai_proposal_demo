<template>
  <div class="min-h-screen bg-gray-50 px-4 py-6 md:px-8">
    <div class="mx-auto max-w-6xl space-y-6">
      <header class="flex flex-wrap items-center justify-between gap-4">
        <div class="space-y-2">
          <p
            class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-gray-400"
          >
            <NuxtLink to="/plan-library" class="hover:text-gray-600"
              >我的計畫庫</NuxtLink
            >
            <span class="text-gray-300">></span>
            <span class="text-gray-600">{{
              projectRecord?.title || "計畫工作區"
            }}</span>
          </p>
          <h1 class="text-3xl font-semibold text-gray-900">
            {{ projectRecord?.title || "計畫工作區" }}
          </h1>
          <p class="text-sm text-gray-500">
            {{ projectRecord?.description || "尚未提供計畫摘要" }}
          </p>
          <div class="flex flex-wrap items-center gap-3 text-xs text-gray-400">
            <span
              class="inline-flex items-center rounded-full bg-rose-50 px-3 py-1 font-semibold text-rose-500"
            >
              {{ modeLabel }}
            </span>
            <span v-if="lastUpdatedDisplay"
              >最後更新：{{ lastUpdatedDisplay }}</span
            >
          </div>
        </div>
        <NuxtLink
          to="/"
          class="inline-flex items-center rounded-2xl border border-gray-200 px-5 py-2 text-sm font-semibold text-gray-600 transition hover:border-rose-200 hover:text-rose-500"
        >
          返回首頁
        </NuxtLink>
      </header>

      <section
        v-if="isProjectLoading"
        class="flex min-h-[40vh] flex-col items-center justify-center rounded-3xl border border-dashed border-rose-200 bg-white/80 p-10 text-center text-gray-500"
      >
        <span class="text-sm font-semibold tracking-wide">正在載入計畫...</span>
        <span class="mt-2 text-xs text-gray-400">請稍候片刻</span>
      </section>

      <section
        v-else-if="loadError"
        class="flex min-h-[40vh] flex-col items-center justify-center rounded-3xl border border-rose-100 bg-white p-8 text-center"
      >
        <p class="text-base font-semibold text-rose-500">{{ loadError }}</p>
        <p class="mt-2 text-sm text-gray-500">
          無法載入專案，請重新整理或返回計畫庫。
        </p>
        <div class="mt-4 flex gap-3">
          <button
            class="rounded-2xl bg-rose-500 px-5 py-2 text-sm font-semibold text-white shadow hover:bg-rose-600"
            @click="fetchProject"
          >
            重新嘗試
          </button>
          <NuxtLink
            to="/plan-library"
            class="rounded-2xl border border-gray-200 px-5 py-2 text-sm font-semibold text-gray-600 hover:border-rose-200 hover:text-rose-500"
          >
            返回計畫庫
          </NuxtLink>
        </div>
      </section>

      <section
        v-else-if="!workspaceReady"
        class="flex min-h-[40vh] flex-col items-center justify-center rounded-3xl border border-dashed border-gray-200 bg-white/90 p-10 text-center"
      >
        <p class="text-lg font-semibold text-gray-800">尚未完成配置載入</p>
        <p class="mt-2 text-sm text-gray-500">
          正在同步模板設定，完成後即可繼續對話式編輯。
        </p>
      </section>

      <GeneratorModeWorkspace
        v-if="isGeneratorMode"
        :all-configs="allConfigs"
        :selected-grant-id="selectedGrantId"
        :selected-template-id="selectedTemplateId"
        :user-input="userInput"
        :dynamic-field-values="dynamicFieldValues"
        :final-plan-content="finalPlanContent"
        :current-sections="currentSections"
        :project-record="projectRecord"
        :current-grant="currentGrant"
        :current-template="currentTemplate"
        :build-final-user-input="buildFinalUserInput"
        @updateProjectRecord="handleGeneratorUpdate"
        @candidateConfirmed="handleGeneratorCandidateConfirm"
      />

      <section
        v-else-if="!isGeneratorMode && workspaceReady"
        class="flex min-h-[80vh] gap-4 rounded-3xl p-0"
      >
        <div class="w-4/5">
          <Chatbox
            :key="projectRecord?.id"
            class="h-full"
            :sections="currentSections"
            :reference-summaries="referenceSummaries"
            :candidate-plan="candidatePlan"
            :final-plan="finalPlanContent"
            :is-generating="isLoading"
            :grant-id="selectedGrantId"
            :template-id="selectedTemplateId"
            :grant-name="grantLabel"
            :template-name="activeTemplateName"
            :use-model-type="useModelType"
            :prefilled-answers="prefilledChatAnswers"
            @generatePlan="handleChatPlanGeneration"
            @finalizeCandidates="onCandidateConfirm"
            @requestExport="handleExportWord"
            @toggleModel="toggleModel"
            @backToStageOne="router.push('/')"
            @messagesUpdated="handleMessagesUpdated"
            @questionAnswersUpdated="handleQuestionAnswersUpdated"
            @guidedQuestionsUpdated="handleGuidedQuestionsUpdated"
          />
        </div>
        <div class="w-1/5">
          <ChatSidebar
            :messages="chatMessages"
            :versions="versionHistory"
            :question-answers="chatQuestionAnswers"
            :guided-questions="chatGuidedQuestions"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import Chatbox from "~/components/Chatbox.vue";
import ChatSidebar from "~/components/ChatSidebar.vue";
import GeneratorModeWorkspace from "~/components/GeneratorModeWorkspace.vue";
import { usePlanGenerator } from "~/composables/usePlanGenerator";
import { useNotifications } from "~/composables/useNotifications";
import { useLoading } from "~/composables/useLoading";
import { exportPlanToWord } from "~/utils/exportToWord";
import { useCurrentUser } from "~/composables/useCurrentUser";
import { mergeIntoEmptyValues } from "~/utils/dynamicSchema";

definePageMeta({
  middleware: "auth",
});

interface ProjectMetadata {
  planType?: Record<string, any> | null;
  backgroundEntries?: string[];
  prefilledChatAnswers?: Record<string, string>;
  [key: string]: any;
}

interface ProjectRecord {
  id: string;
  user_id: string;
  mode: string;
  title: string;
  description: string | null;
  saved_plan: Record<string, any> | null;
  conversation_history: any;
  stored_answer: Record<string, any> | null;
  grant_id?: string | null;
  template_id?: string | null;
  plan_type_id?: string | null;
  plan_metadata?: ProjectMetadata | null;
  created_at: string;
  updated_at: string | null;
}

const router = useRouter();
const route = useRoute();
const projectId = computed(() => route.params.id as string);

const { success, info, error: notifyError } = useNotifications();
const { isLoading, show: showLoading, hide: hideLoading } = useLoading();
const { userId: currentUserId, refreshUser } = useCurrentUser();

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const {
  allConfigs,
  selectedGrantId,
  selectedTemplateId,
  currentSections,
  planContent: finalPlanContent,
  dynamicFieldValues,
  userInput,
  currentGrant,
  currentTemplate,
  buildFinalUserInput,
  fetchAllConfigs,
} = usePlanGenerator();

const projectRecord = ref<ProjectRecord | null>(null);
const isProjectLoading = ref(false);
const loadError = ref("");
const planMetadata = ref<ProjectMetadata | null>(null);
const candidatePlan = ref<Record<string, any>>({});
const chatMessages = ref<any[]>([]);
const chatQuestionAnswers = ref<Record<string, string>>({});
const chatGuidedQuestions = ref<any[]>([]);
const versionHistory = ref<any[]>([]);
const useModelType = ref("external");
const lastGenerationPrompt = ref("");
const isPersistingProject = ref(false);
const conversationSyncTimer = ref<ReturnType<typeof setTimeout> | null>(null);

const referenceSummaries = computed(
  () => planMetadata.value?.backgroundEntries || []
);
const prefilledChatAnswers = computed(
  () => planMetadata.value?.prefilledChatAnswers || {}
);
const isGeneratorMode = computed(
  () => projectRecord.value?.mode === "generator"
);
const workspaceReady = computed(() =>
  Boolean(
    projectRecord.value &&
      selectedGrantId.value &&
      selectedTemplateId.value &&
      currentSections.value.length
  )
);
const lastUpdatedDisplay = computed(() => {
  if (!projectRecord.value) return "";
  const source =
    projectRecord.value.updated_at || projectRecord.value.created_at;
  return new Date(source).toLocaleString("zh-TW");
});
const modeLabel = computed(() =>
  projectRecord.value?.mode === "generator" ? "計畫生成模式" : "互動模式"
);
const grantLabel = computed(
  () => planMetadata.value?.planType?.title || "自訂計畫"
);
const activeTemplateName = computed(() => {
  const targetGrant = allConfigs.value.find(
    (grant) => grant.id === selectedGrantId.value
  );
  const template = targetGrant?.templates.find(
    (tpl) => tpl.id === selectedTemplateId.value
  );
  return template?.name || "";
});

onMounted(async () => {
  await refreshUser();
  if (!allConfigs.value.length) {
    try {
      await fetchAllConfigs();
    } catch (error) {
      console.error("Failed to preload plan configurations", error);
    }
  }
  await fetchProject();
});

onBeforeUnmount(() => {
  if (conversationSyncTimer.value) {
    clearTimeout(conversationSyncTimer.value);
    conversationSyncTimer.value = null;
    persistConversationHistory();
  }
});

watch(
  () => projectRecord.value?.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      // reset version history when loading a different project
      versionHistory.value = [];
    }
  }
);

async function getUserIdOrNotify() {
  const userId = currentUserId.value || (await refreshUser());
  if (!userId) {
    notifyError("無法取得使用者資訊，請重新登入後再試。");
  }
  return userId;
}

function hydrateInputStateFromStoredAnswer(record: ProjectRecord | null) {
  if (!record?.stored_answer || typeof record.stored_answer !== "object") {
    return;
  }
  const userInputPayload = (record.stored_answer as any).user_input;
  if (!userInputPayload || typeof userInputPayload !== "object") {
    return;
  }
  if (Object.prototype.hasOwnProperty.call(userInputPayload, "main_idea")) {
    userInput.value = userInputPayload.main_idea || "";
  }
  if (
    userInputPayload.dynamic_fields &&
    typeof userInputPayload.dynamic_fields === "object"
  ) {
    dynamicFieldValues.value = mergeIntoEmptyValues(
      userInputPayload.dynamic_fields as Record<string, string>
    );
  }
}

async function fetchProject() {
  if (!projectId.value) return;
  isProjectLoading.value = true;
  loadError.value = "";
  try {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId.value}`);
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "Failed to load project");
    }
    const data: ProjectRecord = await response.json();
    projectRecord.value = data;
    planMetadata.value = data.plan_metadata || null;
    finalPlanContent.value = data.saved_plan || {};
    chatMessages.value = Array.isArray(data.conversation_history)
      ? data.conversation_history
      : [];
    if (chatMessages.value.length) {
      handleMessagesUpdated(chatMessages.value);
    } else {
      versionHistory.value = [];
    }
    selectedGrantId.value = data.grant_id || "";
    selectedTemplateId.value = data.template_id || "";
    useModelType.value = "external";
    if (data.mode === "generator") {
      await initializeGeneratorStateFromProject(data);
    }
    hydrateInputStateFromStoredAnswer(data);
  } catch (error: any) {
    console.error("Failed to load project", error);
    loadError.value = error?.message || "無法載入專案";
  } finally {
    isProjectLoading.value = false;
  }
}

function toggleModel() {
  useModelType.value =
    useModelType.value === "internal" ? "external" : "internal";
}

async function handleExportWord() {
  const hasPlan = Object.keys(finalPlanContent.value || {}).length > 0;
  if (!hasPlan) {
    notifyError("尚未有可匯出的內容");
    return;
  }
  try {
    await exportPlanToWord(
      currentSections.value,
      finalPlanContent.value,
      selectedGrantId.value,
      selectedTemplateId.value
    );
  } catch (error) {
    console.error("Failed to export plan", error);
    notifyError("匯出失敗，請稍後再試");
  }
}

function scheduleConversationSync() {
  if (conversationSyncTimer.value) {
    clearTimeout(conversationSyncTimer.value);
  }
  conversationSyncTimer.value = setTimeout(() => {
    persistConversationHistory();
  }, 2000);
}

async function persistConversationHistory() {
  if (!projectRecord.value) return;
  try {
    await updateProject({
      conversation_history: serializeForStorage(chatMessages.value),
    });
  } catch (error) {
    console.warn("Failed to sync conversation history", error);
  }
}

async function initializeGeneratorStateFromProject(record: ProjectRecord) {
  if (record.mode !== "generator") {
    return;
  }
  if (!allConfigs.value.length) {
    try {
      await fetchAllConfigs();
    } catch (error) {
      console.error("無法載入計畫模板設定", error);
    }
  }
}

async function handleGeneratorUpdate(payload: {
  user_id: string;
  grant_id: string | null;
  template_id: string | null;
  stored_answer: Record<string, any> | null;
  saved_plan: Record<string, any>;
}) {
  if (!projectRecord.value) return;
  try {
    await updateProject({
      stored_answer: payload.stored_answer,
      saved_plan: payload.saved_plan,
      grant_id: payload.grant_id,
      template_id: payload.template_id,
    });
  } catch (error) {
    console.warn("Failed to persist generator state", error);
  }
}

async function handleGeneratorCandidateConfirm(payload: {
  selectedData: Record<string, any>;
  rejectedData: Record<string, any>;
  finalPrompt: string;
}) {
  lastGenerationPrompt.value = payload.finalPrompt;
  await persistProjectRecord({
    savedPlan: payload.selectedData,
    storedAnswer: payload.selectedData,
  });
  savePreferenceData(
    payload.selectedData,
    payload.rejectedData,
    payload.finalPrompt
  );
}

async function updateProject(payload: Record<string, any>) {
  if (!projectRecord.value) return null;
  const response = await fetch(
    `${API_BASE_URL}/projects/${projectRecord.value.id}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "更新計畫失敗");
  }
  const updated: ProjectRecord = await response.json();
  projectRecord.value = updated;
  planMetadata.value = updated.plan_metadata || planMetadata.value;
  finalPlanContent.value = updated.saved_plan || finalPlanContent.value;
  hydrateInputStateFromStoredAnswer(updated);
  return updated;
}

function serializeForStorage<T>(value: T): T | null {
  if (value === undefined || value === null) {
    return null;
  }
  try {
    return JSON.parse(JSON.stringify(value)) as T;
  } catch (error) {
    console.warn("Failed to serialize project payload", error);
    return null;
  }
}

async function persistProjectRecord(options: {
  savedPlan: Record<string, any>;
  storedAnswer: Record<string, any>;
}) {
  if (!projectRecord.value || isPersistingProject.value) {
    return;
  }
  const userId = await getUserIdOrNotify();
  if (!userId) return;

  isPersistingProject.value = true;
  try {
    await updateProject({
      saved_plan: serializeForStorage(options.savedPlan),
      stored_answer: serializeForStorage(options.storedAnswer),
      conversation_history: serializeForStorage(chatMessages.value),
    });
    info("計畫已同步到我的計畫庫");
  } catch (error: any) {
    console.error("Failed to persist project", error);
    notifyError(error?.message || "儲存計畫失敗，請稍後再試");
  } finally {
    isPersistingProject.value = false;
  }
}

async function onCandidateConfirm({
  selected,
  rejected,
}: {
  selected: Record<string, any>;
  rejected: Record<string, any>;
}) {
  const newPlanContent: Record<string, { content?: string; error?: string }> =
    {};
  Object.entries(selected).forEach(([sectionId, candidate]) => {
    if (candidate && (candidate as any).content) {
      newPlanContent[sectionId] = { content: (candidate as any).content };
    } else {
      newPlanContent[sectionId] = {
        error: (candidate as any)?.error || "No content",
      };
    }
  });
  finalPlanContent.value = newPlanContent;
  success("已選擇方案並填充到結果中！");
  await persistProjectRecord({
    savedPlan: newPlanContent,
    storedAnswer: selected,
  });
  savePreferenceData(selected, rejected, lastGenerationPrompt.value);
}

async function handleChatPlanGeneration(payload: { prompt: string }) {
  if (!payload?.prompt || !selectedTemplateId.value || !selectedGrantId.value) {
    notifyError("請先完成基本設定，並輸入至少一則對話訊息。");
    return;
  }
  showLoading("正在生成計畫書...", true);
  finalPlanContent.value = {};
  candidatePlan.value = {};
  lastGenerationPrompt.value = payload.prompt;

  try {
    const sectionsToGenerate = currentSections.value.map((section) => ({
      section_id: section.id,
    }));
    const userId = await getUserIdOrNotify();
    if (!userId) {
      hideLoading();
      return;
    }

    const response = await fetch(`${API_BASE_URL}/generate_plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        grant: selectedGrantId.value,
        template: selectedTemplateId.value,
        user_input: payload.prompt,
        num_candidates: 2,
        is_external: useModelType.value === "external",
        sections: sectionsToGenerate,
      }),
    });

    if (!response.ok) {
      const errorDetail = await response.text();
      throw new Error(`伺服器錯誤 (${response.status}): ${errorDetail}`);
    }

    const rawData = await response.json();
    const processedCandidates: Record<string, any> = {};
    for (const sectionId in rawData) {
      processedCandidates[sectionId] = rawData[sectionId].map(
        (candidate: any) => ({
          content: candidate.raw_json_content,
          error: candidate.error || null,
        })
      );
    }
    candidatePlan.value = processedCandidates;
    success("計畫書草稿已生成！");
  } catch (error: any) {
    console.error("生成計畫書時發生錯誤:", error);
    notifyError(`生成失敗: ${error.message}`);
  } finally {
    hideLoading();
  }
}

async function savePreferenceData(
  selectedData: Record<string, any>,
  rejectedData: Record<string, any>,
  finalPrompt = ""
) {
  try {
    const entriesToSave = currentSections.value
      .map((section) => {
        const chosen = selectedData[section.id];
        const rejected = rejectedData[section.id];
        if (chosen && chosen.content) {
          return {
            section_id: section.id,
            section_name: section.name,
            chosen_content: chosen.content,
            rejected_content: rejected?.content || "",
            final_prompt: finalPrompt,
          };
        }
        return null;
      })
      .filter(Boolean);

    if (entriesToSave.length > 0) {
      fetch(`${API_BASE_URL}/datasets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entries: entriesToSave }),
      }).then((response) => {
        if (response.status !== 202) {
          console.error("後台保存偏好數據失敗。");
        }
      });
    }
  } catch (error) {
    console.error("準備保存偏好數據時出錯:", error);
  }
}

function handleMessagesUpdated(messages: any[]) {
  chatMessages.value = messages;

  const hasFinalMessage = messages.some((msg) => msg.type === "final");
  if (hasFinalMessage && versionHistory.value.length === 0) {
    versionHistory.value.push({
      id: `v1`,
      number: 1,
      title: "初版推演結果",
      timestamp: new Date().toLocaleString("zh-TW"),
    });
  }
  scheduleConversationSync();
}

function handleQuestionAnswersUpdated(payload: Record<string, string>) {
  chatQuestionAnswers.value = { ...(payload || {}) };
}

function handleGuidedQuestionsUpdated(payload: any[]) {
  chatGuidedQuestions.value = Array.isArray(payload) ? payload : [];
}
</script>
