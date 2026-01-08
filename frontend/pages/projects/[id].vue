<template>
  <ClientOnly>
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
            <div
              class="flex flex-wrap items-center gap-3 text-xs text-gray-400"
            >
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
          <div class="flex flex-wrap items-center gap-3">
            <div
              v-if="isInternal"
              class="inline-flex items-center gap-2 rounded-2xl border border-gray-200 px-4 py-2"
            >
              <span class="text-xs font-semibold text-gray-600">
                {{ useModelType === "internal" ? "內部模型" : "外部模型" }}
              </span>
              <button
                class="relative inline-flex h-6 w-11 items-center rounded-full transition"
                :class="
                  useModelType === 'internal' ? 'bg-rose-500' : 'bg-gray-300'
                "
                @click="toggleModel"
              >
                <span
                  class="inline-block h-5 w-5 transform rounded-full bg-white transition"
                  :class="
                    useModelType === 'internal'
                      ? 'translate-x-5'
                      : 'translate-x-1'
                  "
                ></span>
              </button>
            </div>
            <NuxtLink
              to="/"
              class="inline-flex items-center rounded-2xl border border-gray-200 px-5 py-2 text-sm font-semibold text-gray-600 transition hover:border-rose-200 hover:text-rose-500"
            >
              返回首頁
            </NuxtLink>
          </div>
        </header>

        <section
          v-if="isProjectLoading"
          class="flex min-h-[40vh] flex-col items-center justify-center rounded-3xl border border-dashed border-rose-200 bg-white/80 p-10 text-center text-gray-500"
        >
          <span class="text-sm font-semibold tracking-wide"
            >正在載入計畫...</span
          >
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
          :use-model-type="useModelType"
          @updateProjectRecord="handleGeneratorUpdate"
          @candidateConfirmed="onCandidateConfirm"
        />

        <section
          v-else-if="!isGeneratorMode && workspaceReady"
          class="min-h-[80vh] rounded-3xl p-0"
        >
          <Chatbox
            :key="projectRecord?.id"
            class="h-full"
            :sections="currentSections"
            :candidate-plan="candidatePlan"
            :final-plan="finalPlanContent"
            :is-generating="isLoading"
            :grant-id="selectedGrantId"
            :template-id="selectedTemplateId"
            :grant-name="grantName"
            :template-name="activeTemplateName"
            :project-title="projectRecord?.title"
            :project-summary="projectRecord?.description || ''"
            :project-id="projectRecord?.id || ''"
            :saved-plan-versions="savedPlanVersions"
            show-sidebar
            @generatePlan="handleChatPlanGeneration"
            @finalizeCandidates="onCandidateConfirm"
            @requestExport="handleExportWord"
            @backToStageOne="router.push('/')"
            @messagesUpdated="handleMessagesUpdated"
            @aiResponseComplete="persistConversationHistory"
            @updateProjectTitle="handleUpdateProjectTitle"
          />
        </section>
      </div>
    </div>
  </ClientOnly>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import Chatbox from "~/components/Chatbox.vue";
import GeneratorModeWorkspace from "~/components/GeneratorModeWorkspace.vue";
import { usePlanGenerator } from "~/composables/usePlanGenerator";
import { useNotifications } from "~/composables/useNotifications";
import { useLoading } from "~/composables/useLoading";
import { exportPlanToWord } from "~/utils/exportToWord";
import { useCurrentUser } from "~/composables/useCurrentUser";
import { mergeIntoEmptyValues } from "~/utils/dynamicSchema";
import { supabase } from "~/utils/supabaseClient";

const route = useRoute();

const projectRecord = ref<ProjectRecord | null>(null);

const projectTitle = computed(() => {
  return projectRecord.value?.title || "計畫工作區";
});

useHead(() => ({
  title: `${projectTitle.value} - TGSA 企劃引擎`,
  meta: [
    {
      name: "description",
      content:
        "進行中的計畫工作區，支援互動模式和生成模式，與 AI 協作完成專業計畫書編輯。",
    },
    {
      name: "keywords",
      content: "計畫工作區, 計畫編輯, AI 協作, 企劃工具, 計畫生成",
    },
    {
      property: "og:title",
      content: `${projectTitle.value} - TGSA 企劃引擎`,
    },
    {
      property: "og:description",
      content: "進行中的計畫工作區，與 AI 協作完成專業計畫書編輯。",
    },
    { property: "og:type", content: "website" },
    { name: "robots", content: "noindex, follow" },
  ],
}));

const projectId = computed(() => route.params.id as string);

definePageMeta({
  middleware: "auth",
});

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
  created_at: string;
  updated_at: string | null;
}

const router = useRouter();

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

const isProjectLoading = ref(false);
const loadError = ref("");
const candidatePlan = ref<Record<string, any>>({});
const chatMessages = ref<any[]>([]);
const useModelType = ref("external");
const isInternal = ref(false);
const lastGenerationPrompt = ref("");
const isPersistingProject = ref(false);
const conversationSyncTimer = ref<ReturnType<typeof setTimeout> | null>(null);

onMounted(async () => {
  const { checkIsInternal } = useInternalCheck();

  // 執行檢查
  isInternal.value = await checkIsInternal();
});

const savedPlanVersions = computed(() => {
  if (!projectRecord.value?.saved_plan) {
    return [];
  }
  const savedPlan = projectRecord.value.saved_plan;
  // 如果 saved_plan 是数组，直接返回
  if (Array.isArray(savedPlan)) {
    return savedPlan.map((version, index) => ({
      id: `v${index + 1}`,
      number: index + 1,
      title: version.title || `版本 ${index + 1}`,
      timestamp: version.timestamp || new Date().toLocaleString("zh-TW"),
      data: version.data || version,
    }));
  }
  // 如果 saved_plan 是对象，转换为单个版本
  return [
    {
      id: "v1",
      number: 1,
      title: "初版推演結果",
      timestamp: projectRecord.value.updated_at
        ? new Date(projectRecord.value.updated_at).toLocaleString("zh-TW")
        : new Date().toLocaleString("zh-TW"),
      data: savedPlan,
    },
  ];
});
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

const grantName = computed(() => {
  const targetGrant = allConfigs.value.find(
    (grant) => grant.id === selectedGrantId.value
  );
  return targetGrant?.name || "";
});
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
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error("請先登入");
    }

    const response = await fetch(
      `${API_BASE_URL}/projects/${projectId.value}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
      }
    );
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "Failed to load project");
    }
    const data: ProjectRecord = await response.json();
    projectRecord.value = data;

    // 从 saved_plan 中提取最新版本的内容用于显示
    if (data.saved_plan) {
      const savedPlanArray = Array.isArray(data.saved_plan)
        ? data.saved_plan
        : [data.saved_plan];
      const latestVersion = savedPlanArray[savedPlanArray.length - 1];
      finalPlanContent.value = latestVersion?.data || {};
    } else {
      finalPlanContent.value = {};
    }

    chatMessages.value = Array.isArray(data.conversation_history)
      ? data.conversation_history
      : [];
    if (chatMessages.value.length) {
      handleMessagesUpdated(chatMessages.value);
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

async function handleExportWord(payload?: { version?: any }) {
  let contentToExport = finalPlanContent.value;

  // 如果是从版本弹窗传来的导出请求
  if (payload?.version) {
    const versionData = payload.version.data;
    if (!versionData || Object.keys(versionData).length === 0) {
      notifyError("該版本沒有可匯出的內容");
      return;
    }
    contentToExport = versionData;
  } else {
    // 原有逻辑：导出当前显示的最新版本
    const hasPlan = Object.keys(contentToExport || {}).length > 0;
    if (!hasPlan) {
      notifyError("尚未有可匯出的內容");
      return;
    }
  }

  try {
    await exportPlanToWord(
      currentSections.value,
      contentToExport,
      selectedGrantId.value,
      selectedTemplateId.value,
      projectRecord.value?.title
    );
  } catch (error) {
    console.error("Failed to export plan", error);
    notifyError("匯出失敗，請稍後再試");
  }
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
  // saved_plan: Record<string, any>;
}) {
  if (!projectRecord.value) return;
  try {
    await updateProject({
      stored_answer: payload.stored_answer,
      // saved_plan: payload.saved_plan,
      grant_id: payload.grant_id,
      template_id: payload.template_id,
    });
  } catch (error) {
    console.warn("Failed to persist generator state", error);
  }
}

async function handleUpdateProjectTitle(newTitle: string) {
  if (!projectRecord.value) return;
  try {
    await updateProject({ title: newTitle });
    success("已更新專案名稱");
  } catch (err) {
    console.error("Failed to update project title", err);
    notifyError("更新專案名稱失敗，請稍後再試");
  }
}

async function updateProject(payload: Record<string, any>) {
  if (!projectRecord.value) return null;
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error("請先登入");
    }

    const response = await fetch(
      `${API_BASE_URL}/projects/${projectRecord.value.id}`,
      {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      }
    );
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "更新計畫失敗");
    }
    const updated: ProjectRecord = await response.json();
    projectRecord.value = updated;
    finalPlanContent.value = updated.saved_plan || finalPlanContent.value;
    hydrateInputStateFromStoredAnswer(updated);
    return updated;
  } catch (error: any) {
    console.error("Failed to update project", error);
    throw error;
  }
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
  storedAnswer?: Record<string, any> | null;
}) {
  if (!projectRecord.value || isPersistingProject.value) {
    return;
  }
  const userId = await getUserIdOrNotify();
  if (!userId) return;

  isPersistingProject.value = true;
  try {
    const payload: Record<string, any> = {
      saved_plan: serializeForStorage(options.savedPlan),
      conversation_history: serializeForStorage(chatMessages.value),
    };
    if (options.storedAnswer !== undefined) {
      payload.stored_answer = serializeForStorage(options.storedAnswer);
    }
    await updateProject({
      ...payload,
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
  finalPrompt,
}: {
  selected: Record<string, any>;
  rejected: Record<string, any>;
  finalPrompt?: string;
}) {
  if (finalPrompt) {
    lastGenerationPrompt.value = finalPrompt;
  }
  // 构建当前版本的内容
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

  // 创建新版本对象
  const currentSavedPlan = projectRecord.value?.saved_plan || [];
  const versionArray = Array.isArray(currentSavedPlan)
    ? currentSavedPlan
    : [currentSavedPlan];
  const versionNumber = versionArray.length + 1;

  const newVersion = {
    number: versionNumber,
    title: `版本 ${versionNumber}`,
    timestamp: new Date().toLocaleString("zh-TW"),
    data: newPlanContent,
  };

  // 追加新版本到数组
  const updatedSavedPlan = [...versionArray, newVersion];

  // 更新前端显示内容为最新版本
  finalPlanContent.value = newPlanContent;
  success("已選擇方案並填充到結果中！");

  // 保存到数据库
  await persistProjectRecord({
    savedPlan: updatedSavedPlan,
    storedAnswer: projectRecord.value?.stored_answer || null,
  });

  // Save conversation history when version is confirmed
  await persistConversationHistory();

  savePreferenceData(selected, rejected, lastGenerationPrompt.value);
}

async function handleChatPlanGeneration(payload: {
  prompt: string;
  selectedModel?: string;
}) {
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
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      hideLoading();
      notifyError("請先登入");
      return;
    }
    console.log(projectRecord.value?.id);

    const response = await fetch(`${API_BASE_URL}/generate_plan`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        grant: selectedGrantId.value,
        template: selectedTemplateId.value,
        user_input: payload.prompt,
        num_candidates: 2,
        is_external: useModelType.value === "external",
        sections: sectionsToGenerate,
        selected_model: payload.selectedModel,
        project_id: projectRecord.value?.id || null,
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
            source_type: "external_direct",
            grant_id: selectedGrantId.value,
            template_id: selectedTemplateId.value,
            section_id: section.id,
            prompt: finalPrompt,
            final_answer: chosen.content,
            rejected_answer: rejected?.content ? rejected.content : null,
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
  // Removed auto-save on keystroke - now saving only when AI responds or versions are confirmed
}
</script>
