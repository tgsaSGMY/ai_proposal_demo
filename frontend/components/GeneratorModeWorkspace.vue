<!-- 生成器帜控店组件：方案生成的主输入/输出面板 -->
<template>
  <section class="rounded-3xl border border-gray-100 bg-white/90 p-4">
    <div class="flex min-h-[70vh] flex-col gap-4 lg:flex-row">
      <div class="lg:w-1/2">
        <PlanInputPanel
          :all-configs="allConfigs"
          v-model:dynamic-values="dynamicFieldValues"
          :is-generating="isGeneratingPlan"
          :mode="projectRecord?.mode || 'generator'"
          :initial-grant-id="projectRecord?.grant_id || ''"
          :initial-template-id="projectRecord?.template_id || ''"
          :project-title="projectPlanName"
          :project-summary="projectPlanSummary"
          @selectionChange="handleGeneratorSelectionChange"
          @generatePlan="handleGeneratorPlanRequest"
          @generateUserInput="handleGeneratorUserInput"
        />
      </div>
      <div class="lg:w-1/2">
        <PlanOutputPanel
          :plan-content="finalPlanContent"
          :sections="currentSections"
          :mode="projectRecord?.mode || 'generator'"
          :grant-id="selectedGrantId"
          :template-id="selectedTemplateId"
          :saved-plan-versions="savedPlanVersions"
          :project-created-at="projectRecord?.created_at || null"
          @update:content="handleGeneratorContentUpdate"
          @autoFillComplete="handleGeneratorAutoFill"
          @generateUserInput="handleGeneratorUserInput"
        />
      </div>
    </div>
  </section>

  <PlanCandidateSelector
    :visible="showCandidateModal"
    :candidate-plan="candidatePlan"
    :sections="currentSections"
    @close="showCandidateModal = false"
    @confirm="onCandidateConfirm"
  />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import PlanInputPanel from "~/components/editor/generator/PlanInputPanel.vue";
import PlanOutputPanel from "~/components/editor/generator/PlanOutputPanel.vue";
import PlanCandidateSelector from "~/components/PlanCandidateSelector.vue";
import {
  buildDynamicSections,
  getCompositeKeyFromLabel,
  getDynamicFieldLabels,
  getDynamicFieldDefinitions,
  makeCompositeKey,
  mergeIntoEmptyValues,
} from "~/utils/dynamicSchema";
import { useNotifications } from "~/composables/useNotifications";
import { useLoading } from "~/composables/useLoading";
import { useCurrentUser } from "~/composables/useCurrentUser";

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

interface GeneratorConfig {
  allConfigs: any[];
  selectedGrantId: string;
  selectedTemplateId: string;
  dynamicFieldValues: Record<string, string>;
  finalPlanContent: Record<string, any>;
  currentSections: any[];
  projectRecord: ProjectRecord | null;
  currentGrant: any;
  currentTemplate: any;
  buildFinalUserInput: (summaries?: string[]) => string;
  useModelType?: string;
}

const props = defineProps<GeneratorConfig>();

const emit = defineEmits<{
  updateProjectRecord: [
    payload: {
      user_id: string;
      grant_id: string | null;
      template_id: string | null;
      stored_answer: Record<string, any> | null;
      // saved_plan: Record<string, any>;
    },
  ];
  candidateConfirmed: [
    payload: {
      selected: Record<string, any>;
      rejected: Record<string, any>;
      finalPrompt?: string;
    },
  ];
}>();

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const { success, error: notifyError } = useNotifications();
const { show: showLoading, hide: hideLoading } = useLoading();
const { userId: currentUserId, refreshUser } = useCurrentUser();

const showCandidateModal = ref(false);
const candidatePlan = ref<Record<string, any>>({});
const generatorAutosaveTimer = ref<ReturnType<typeof setTimeout> | null>(null);
const isGeneratingPlan = ref(false);
const lastFinalUserInput = ref("");
let isHydratingDynamicFieldState = false;

// Reactive copies for v-model
const dynamicFieldValues = ref(props.dynamicFieldValues);
const finalPlanContent = ref(props.finalPlanContent);

// Expose reactive properties for parent
const currentGrant = computed(() => props.currentGrant);
const currentTemplate = computed(() => props.currentTemplate);
const currentSections = computed(() => props.currentSections);
const allConfigs = computed(() => props.allConfigs);
const selectedGrantId = computed(() => props.selectedGrantId);
const selectedTemplateId = computed(() => props.selectedTemplateId);
const projectRecord = computed(() => props.projectRecord);

const projectPlanName = computed(() => {
  const fallback = props.projectRecord?.title;
  return typeof fallback === "string" ? fallback : "";
});

const projectPlanSummary = computed(() => {
  const fallback = props.projectRecord?.description;
  return typeof fallback === "string" ? fallback : "";
});

const savedPlanVersions = computed(() => {
  const savedPlan = props.projectRecord?.saved_plan;
  if (Array.isArray(savedPlan)) {
    return savedPlan;
  }
  return [];
});

// Watchers to keep local state in sync
watch(
  () => props.dynamicFieldValues,
  (newVal) => {
    if (recordsAreEqual(newVal, dynamicFieldValues.value)) {
      return;
    }
    isHydratingDynamicFieldState = true;
    dynamicFieldValues.value = { ...(newVal || {}) };
  },
  { deep: true },
);

watch(
  () => props.finalPlanContent,
  (newVal) => {
    finalPlanContent.value = { ...newVal };
  },
  { deep: true },
);

// 比较两个记录对象是否完全相等
function recordsAreEqual(
  next?: Record<string, string> | null,
  prev?: Record<string, string> | null,
) {
  if (next === prev) {
    return true;
  }
  const a = next || {};
  const b = prev || {};
  const aKeys = Object.keys(a);
  const bKeys = Object.keys(b);
  if (aKeys.length !== bKeys.length) {
    return false;
  }
  for (const key of aKeys) {
    if (a[key] !== b[key]) {
      return false;
    }
  }
  return true;
}

watch(
  dynamicFieldValues,
  () => {
    if (isHydratingDynamicFieldState) {
      isHydratingDynamicFieldState = false;
      return;
    }
    scheduleGeneratorAutosave();
  },
  { deep: true },
);

onBeforeUnmount(() => {
  if (generatorAutosaveTimer.value) {
    clearTimeout(generatorAutosaveTimer.value);
    generatorAutosaveTimer.value = null;
    void persistGeneratorState();
  }
});

async function getUserIdOrNotify() {
  const userId = currentUserId.value || (await refreshUser());
  if (!userId) {
    notifyError("無法取得使用者資訊，請重新登入後再試。");
  }
  return userId;
}

// 调度生成器自动保存，使用防抖延迟执行
function scheduleGeneratorAutosave() {
  if (!projectRecord.value) {
    return;
  }
  if (generatorAutosaveTimer.value) {
    clearTimeout(generatorAutosaveTimer.value);
  }
  generatorAutosaveTimer.value = setTimeout(() => {
    void persistGeneratorState();
  }, 2000);
}

// 持久化生成器状态到后端
async function persistGeneratorState() {
  if (!projectRecord.value) {
    return;
  }
  try {
    const nextStoredAnswer = {
      user_input: {
        dynamic_fields: { ...dynamicFieldValues.value },
      },
    };
    emit("updateProjectRecord", {
      user_id: projectRecord.value.user_id,
      grant_id: selectedGrantId.value || null,
      template_id: selectedTemplateId.value || null,
      stored_answer: serializeForStorage(nextStoredAnswer),
      // saved_plan: serializeForStorage(finalPlanContent.value) || {},
    });
  } catch (error) {
    console.warn("Failed to auto-save generator project", error);
  }
}

// 序列化数据以便存储，处理undefined和null
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

// 处理生成器选择变更，调度自动保存
function handleGeneratorSelectionChange(selection: {
  grantId: string;
  templateId: string;
}) {
  scheduleGeneratorAutosave();
}

// 处理自动填充，更新方案内容
function handleGeneratorAutoFill(
  filledContent: Record<string, { content?: string; error?: string }>,
) {
  if (!finalPlanContent.value) {
    finalPlanContent.value = {};
  }
  Object.assign(finalPlanContent.value, filledContent);
  scheduleGeneratorAutosave();
}

// 处理方案内容更新
function handleGeneratorContentUpdate({
  sectionId,
  content,
}: {
  sectionId: string;
  content: string;
}) {
  if (!finalPlanContent.value) {
    finalPlanContent.value = {};
  }
  finalPlanContent.value[sectionId] = { content };
  scheduleGeneratorAutosave();
}

// 处理计划生成请求，调用后端API生成方案
async function handleGeneratorPlanRequest(outerPayload?: {
  summaries?: string[];
}) {
  if (!selectedGrantId.value || !selectedTemplateId.value) {
    notifyError("請先選擇主題與模板");
    return;
  }
  isGeneratingPlan.value = true;
  showLoading("正在生成計畫書...", true);
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      hideLoading();
      notifyError("請先登入");
      return;
    }

    const userInput = props.buildFinalUserInput(outerPayload?.summaries || []);
    const finalUserInput =
      "計劃名稱: " +
      projectPlanName.value +
      "\n\n計劃摘要: " +
      projectPlanSummary.value +
      "\n\n" +
      userInput;

    // 保存最後使用的生成輸入，以便父層在確認候選時取得
    lastFinalUserInput.value = finalUserInput;

    finalPlanContent.value = {};
    const response = await fetch(`${API_BASE_URL}/generate_plan`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        grant: selectedGrantId.value,
        template: selectedTemplateId.value,
        user_input: finalUserInput,
        num_candidates: 2,
        is_external: props.useModelType !== "internal",
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
        }),
      );
    }
    candidatePlan.value = processedCandidates;
    showCandidateModal.value = true;
    success("計畫書已生成!");
  } catch (error: any) {
    console.error("生成計畫書時發生錯誤:", error);
    notifyError(`生成失敗: ${error.message}`);
  } finally {
    isGeneratingPlan.value = false;
    hideLoading();
  }
}

// 处理用户输入生成，反推用户输入内容
async function handleGeneratorUserInput() {
  if (!currentGrant.value || !currentTemplate.value) {
    notifyError("請先選擇主題和模板！");
    return;
  }
  isGeneratingPlan.value = true;

  try {
    const userId = await getUserIdOrNotify();
    if (!userId) {
      return;
    }

    const schemaOptions = {
      templateId: selectedTemplateId.value,
      templateGrantId: selectedGrantId.value,
    };

    const currentDynamicFields: Record<string, string> = {};
    const labelByCompositeKey = new Map(
      getDynamicFieldDefinitions(schemaOptions).map((definition) => [
        definition.compositeKey,
        definition.label,
      ]),
    );
    const sections = buildDynamicSections(dynamicFieldValues.value, {
      templateId: selectedTemplateId.value,
      templateGrantId: selectedGrantId.value,
    });
    sections.forEach((section) => {
      section.fields.forEach((field) => {
        if (field.value && field.value.trim() !== "") {
          const label =
            labelByCompositeKey.get(field.compositeKey) || field.title;
          currentDynamicFields[label] = field.value;
        }
      });
    });

    const payload: Record<string, any> = {
      mode: projectRecord.value?.mode === "golden" ? "reverse" : "random",
      grant_name: currentGrant.value.name,
      template_name: currentTemplate.value.name,
      section_name: currentSections.value[0]?.name || "general",
      user_id: userId,
      dynamic_fields_schema: getDynamicFieldLabels(schemaOptions).map(
        (label) => ({
          label,
        }),
      ),
    };

    if (projectRecord.value?.mode === "golden" && finalPlanContent.value) {
      payload.plan_content = finalPlanContent.value;
    }

    const response = await fetch(`${API_BASE_URL}/generate_synthetic_input`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (data.dynamic_fields) {
      const nextValues = { ...dynamicFieldValues.value };
      let hasUpdates = false;

      const attemptLabelMap = (fieldMap: Record<string, any>) => {
        let updated = false;
        Object.entries(fieldMap).forEach(([label, fieldValue]) => {
          const compositeKey = getCompositeKeyFromLabel(label, schemaOptions);
          if (compositeKey && compositeKey in nextValues) {
            const normalized =
              typeof fieldValue === "string"
                ? fieldValue
                : fieldValue != null
                  ? JSON.stringify(fieldValue)
                  : "";
            nextValues[compositeKey] = normalized;
            updated = true;
          }
        });
        return updated;
      };

      const attemptNestedMap = (fieldMap: Record<string, any>) => {
        let updated = false;
        Object.entries(fieldMap).forEach(([sectionId, sectionValue]) => {
          if (!sectionValue || typeof sectionValue !== "object") return;
          Object.entries(sectionValue).forEach(
            ([propertyKey, propertyValue]) => {
              const compositeKey = makeCompositeKey(sectionId, propertyKey);
              if (!(compositeKey in nextValues)) {
                return;
              }
              const normalized =
                typeof propertyValue === "string"
                  ? propertyValue
                  : propertyValue != null
                    ? JSON.stringify(propertyValue)
                    : "";
              nextValues[compositeKey] = normalized;
              updated = true;
            },
          );
        });
        return updated;
      };

      hasUpdates = attemptLabelMap(data.dynamic_fields);

      if (!hasUpdates) {
        hasUpdates = attemptNestedMap(data.dynamic_fields);
      }

      if (hasUpdates) {
        isHydratingDynamicFieldState = true;
        dynamicFieldValues.value = mergeIntoEmptyValues(
          nextValues,
          schemaOptions,
        );
      }
    }
    scheduleGeneratorAutosave();
  } catch (error: any) {
    console.error("Error generating user input:", error);
    notifyError(`生成失敗: ${error.message}`);
  } finally {
    isGeneratingPlan.value = false;
  }
}

// 处理候选方案确认，将选中方案填充到结果中
function onCandidateConfirm({
  selected,
  rejected,
}: {
  selected: Record<string, any>;
  rejected: Record<string, any>;
}) {
  showCandidateModal.value = false;
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

  // Extract the last generation prompt from the last proposal
  let lastPrompt = "";
  if (newPlanContent && Object.keys(newPlanContent).length > 0) {
    // Try to get prompt from first section's content
    const firstSection = Object.values(newPlanContent)[0];
    if (firstSection && typeof (firstSection as any).content === "string") {
      lastPrompt = (firstSection as any).content.substring(0, 100);
    }
  }

  emit("candidateConfirmed", {
    selected: selected,
    rejected: rejected,
    finalPrompt: lastFinalUserInput.value,
  });
  scheduleGeneratorAutosave();
}
</script>
