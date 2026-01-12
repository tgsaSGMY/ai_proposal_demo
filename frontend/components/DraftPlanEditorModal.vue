<!-- /components/DraftPlanEditorModal.vue -->
<template>
  <div
    class="fixed inset-0 bg-black bg-opacity-50 z-40 flex justify-center items-center p-2 sm:p-0"
    @click.self="close"
  >
    <div
      class="bg-gray-50 w-full h-[96vh] sm:w-[95vw] sm:h-[95vh] rounded-lg shadow-xl flex flex-col p-2 sm:p-4"
    >
      <header
        class="flex-shrink-0 flex flex-col sm:flex-row justify-between items-start sm:items-center mb-2 sm:mb-4 pb-2 sm:pb-4 border-b"
      >
        <h2
          class="text-lg sm:text-xl font-bold text-gray-800 break-words max-w-xs sm:max-w-none"
        >
          {{ editableDraft.name }}
        </h2>
        <div class="mt-2 sm:mt-0 flex flex-row gap-2">
          <button
            @click="handleSaveToDataset"
            class="btn-primary text-sm sm:text-base px-3 sm:px-4 py-1.5 sm:py-2"
          >
            保存至最終數據集
          </button>
          <button
            @click="close"
            class="btn-secondary ml-2 text-sm sm:text-base px-3 sm:px-4 py-1.5 sm:py-2"
          >
            關閉
          </button>
        </div>
      </header>

      <div
        class="flex-grow grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-6 min-h-0 overflow-y-scroll"
      >
        <PlanInputPanel
          :all-configs="allConfigs"
          v-model="mainIdea"
          :is-generating="isGeneratingPlan"
          v-model:dynamic-values="dynamicFieldValues"
          :mode="editableDraft.mode"
          :initial-grant-id="editableDraft.grant_id"
          :initial-template-id="editableDraft.template_id"
          @update:modelValue="updateMainIdea"
          @selectionChange="onSelectionChangeInModal"
          @generatePlan="handleGeneratePlanInModal"
          @generateUserInput="handleGenerateUserInput"
        />
        <PlanOutputPanel
          :plan-content="planContent"
          :sections="currentSections"
          :mode="editableDraft.mode"
          :grant-id="editableDraft.grant_id"
          :template-id="editableDraft.template_id"
          @update:content="onContentUpdateInModal"
          @autoFillComplete="handleAutoFillInModal"
          @generateUserInput="handleGenerateUserInput"
        />
      </div>
    </div>
  </div>
  <PlanCandidateSelector
    :visible="showCandidateModal"
    :candidate-plan="candidatePlan"
    :sections="currentSections"
    @close="showCandidateModal = false"
    @confirm="onCandidateConfirm"
  />
</template>

<script setup>
import { ref, reactive, watch, onUnmounted, computed, onMounted } from "vue";
import { usePlanGenerator } from "~/composables/usePlanGenerator";
import { useNotifications } from "~/composables/useNotifications";
import { useLoading } from "~/composables/useLoading";
import {
  buildDynamicSections,
  mergeIntoEmptyValues,
  getCompositeKeyFromLabel,
  getDynamicFieldLabels,
  getDynamicFieldDefinitions,
  makeCompositeKey,
} from "~/utils/dynamicSchema";
import { supabase } from "~/utils/supabaseClient";
import PlanInputPanel from "~/components/PlanInputPanel.vue";
import PlanOutputPanel from "~/components/PlanOutputPanel.vue";
import PlanCandidateSelector from "~/components/PlanCandidateSelector.vue";
import { useCurrentUser } from "~/composables/useCurrentUser";

const props = defineProps({
  draft: {
    type: Object,
    required: true,
  },
  allConfigs: {
    type: Array,
    required: true,
  },
});
const emit = defineEmits(["close", "save-to-dataset"]);

const { isLoading, show: showLoading, hide: hideLoading } = useLoading();
const { success, error: errorNotification } = useNotifications();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
const { userId: currentUserId, refreshUser } = useCurrentUser();

const {
  selectedGrantId,
  selectedTemplateId,
  fetchAllConfigs,
  planContent,
  currentGrant,
  currentTemplate,
  currentSections,
  allConfigs,
  dynamicFieldValues,
} = usePlanGenerator();

const isGeneratingPlan = ref(false);
const editableDraft = reactive(JSON.parse(JSON.stringify(props.draft)));
let isHydratingDynamicFields = true;

// --- State Initialization and Synchronization ---
onMounted(async () => {
  await refreshUser();
  await fetchAllConfigs();
  // Force Composable state to match the draft's config
  selectedGrantId.value = props.draft.grant_id;
  selectedTemplateId.value = props.draft.template_id;
  planContent.value = props.draft.plan_content;
  dynamicFieldValues.value = mergeIntoEmptyValues(
    props.draft.user_input?.dynamic_fields
  );
  if (!editableDraft.user_input) {
    editableDraft.user_input = { main_idea: "", dynamic_fields: {} };
  }
  editableDraft.user_input.dynamic_fields = {
    ...dynamicFieldValues.value,
  };
});

// Main idea is a computed property for easier v-model binding
const mainIdea = computed({
  get: () => editableDraft.user_input?.main_idea || "",
  set: (value) => {
    if (!editableDraft.user_input) {
      editableDraft.user_input = { main_idea: "", dynamic_fields: {} };
    }
    editableDraft.user_input.main_idea = value;
    debounceSave();
  },
});

// --- Debounce for saving draft updates ---
let saveTimer = null;

watch(
  dynamicFieldValues,
  (newVal) => {
    if (!editableDraft.user_input) {
      editableDraft.user_input = { main_idea: "", dynamic_fields: {} };
    }
    editableDraft.user_input.dynamic_fields = { ...newVal };
    if (isHydratingDynamicFields) {
      isHydratingDynamicFields = false;
      return;
    }
    debounceSave();
  },
  { deep: true }
);

const saveUpdatesToDb = async () => {
  try {
    if (!editableDraft.user_input) {
      editableDraft.user_input = { main_idea: "", dynamic_fields: {} };
    }
    editableDraft.user_input.dynamic_fields = {
      ...dynamicFieldValues.value,
    };

    const payload = {
      name: editableDraft.name,
      grant_id: editableDraft.grant_id,
      template_id: editableDraft.template_id,
      user_input: editableDraft.user_input,
      plan_content: planContent.value,
    };

    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("請先登入");

    const res = await fetch(`${API_BASE_URL}/draft_plans/${props.draft.id}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      console.error(`Failed to auto-save draft ${props.draft.id}`);
    }
  } catch (err) {
    console.error("Auto-save failed:", err);
  }
};

const debounceSave = () => {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(saveUpdatesToDb, 1500);
};

onUnmounted(() => {
  if (saveTimer) clearTimeout(saveTimer);
});

// --- Event Handlers ---
async function close() {
  showLoading();
  await saveUpdatesToDb();
  emit("close");
  hideLoading();
}
function handleSaveToDataset() {
  const finalInputs = buildFinalUserInputForGeneration();
  editableDraft.plan_content = planContent.value;
  emit("save-to-dataset", editableDraft, finalInputs);
}

function updateMainIdea(value) {
  if (!editableDraft.user_input) editableDraft.user_input = {};
  editableDraft.user_input.main_idea = value;
  debounceSave();
}

function onSelectionChangeInModal(selection) {
  selectedGrantId.value = selection.grantId;
  selectedTemplateId.value = selection.templateId;
  editableDraft.grant_id = selection.grantId;
  editableDraft.template_id = selection.templateId;
  debounceSave();
}

function onCandidateConfirm({ selected, rejected }) {
  const newPlanContent = {};
  for (const [sectionId, candidate] of Object.entries(selected)) {
    if (candidate && candidate.content) {
      newPlanContent[sectionId] = { content: candidate.content };
    } else {
      newPlanContent[sectionId] = { error: candidate?.error || "No content" };
    }
  }
  planContent.value = newPlanContent;
  saveRejectedAnswersToDb(rejected);
  showCandidateModal.value = false;
  debounceSave();
  success("已選擇方案並填充到結果中！");
}

async function saveRejectedAnswersToDb(rejected) {
  try {
    const rejectedAnswerData = {};
    for (const [sectionId, candidate] of Object.entries(rejected)) {
      if (candidate && candidate.content) {
        rejectedAnswerData[sectionId] = candidate.content;
      }
    }

    if (Object.keys(rejectedAnswerData).length === 0) {
      return; // 没有 rejected answers，不需要保存
    }

    const payload = {
      rejected_answer: rejectedAnswerData,
    };

    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("請先登入");

    const res = await fetch(`${API_BASE_URL}/draft_plans/${props.draft.id}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      console.error(
        `Failed to save rejected answers for draft ${props.draft.id}`
      );
    }
  } catch (err) {
    console.error("Save rejected answers failed:", err);
  }
}

function handleAutoFillInModal(filledContent) {
  if (!planContent.value) planContent.value = {};
  Object.assign(planContent.value, filledContent);
  debounceSave();
}

function onContentUpdateInModal({ sectionId, content }) {
  if (!planContent.value) planContent.value = {};
  planContent.value[sectionId] = { content };
  debounceSave();
}

function buildFinalUserInputForGeneration(summaries = []) {
  let finalInput = `核心想法: ${editableDraft.user_input?.main_idea || ""}\n\n`;
  const sections = buildDynamicSections(dynamicFieldValues.value);

  const additionalDetails = sections
    .map((section) => {
      const filledFields = section.fields
        .map((field) => {
          const fieldValue = field.value?.trim();
          if (!fieldValue) {
            return null;
          }
          const description = field.description
            ? `說明: ${field.description}\n`
            : "";
          return `【${field.title}】\n${description}${fieldValue}`;
        })
        .filter((item) => Boolean(item));

      if (!filledFields.length) {
        return null;
      }

      return `◆ ${section.sectionName}\n${filledFields.join("\n\n")}`;
    })
    .filter((item) => Boolean(item))
    .join("\n\n");

  if (additionalDetails) {
    finalInput += `--- 詳細補充信息 ---\n${additionalDetails}`;
  }

  if (summaries && summaries.length > 0) {
    const summariesText = summaries.join("\n\n---\n\n");
    finalInput += `\n\n--- 額外參考資料重點 ---\n${summariesText}`;
  }

  return finalInput;
}

const showCandidateModal = ref(false);
const candidatePlan = ref({});

async function getUserIdOrNotify() {
  const userId = currentUserId.value || (await refreshUser());
  if (!userId) {
    errorNotification("無法取得使用者資訊，請重新登入後再試。");
  }
  return userId;
}

async function handleGeneratePlanInModal(outerPayload) {
  isGeneratingPlan.value = true;
  showLoading("正在生成計劃書...", true);
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      hideLoading();
      errorNotification("請先登入");
      return;
    }

    const finalUserInput = buildFinalUserInputForGeneration(
      outerPayload?.summaries
    );
    const sectionsToGenerate = currentSections.value.map((s) => ({
      section_id: s.id,
    }));

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
        is_external: false,
      }),
    });
    if (!response.ok) {
      const errorDetail = await response.text();
      throw new Error(`伺服器錯誤 (${response.status}): ${errorDetail}`);
    }

    const rawData = await response.json();

    const processedCandidates = {};
    for (const sectionId in rawData) {
      const candidates = rawData[sectionId];
      processedCandidates[sectionId] = candidates.map((candidate) => ({
        content: candidate.raw_json_content,
        error: candidate.error || null,
      }));
    }

    candidatePlan.value = processedCandidates;
    showCandidateModal.value = true; // 显示选择模态框
    success("計劃書已生成!");
    debounceSave();
  } catch (e) {
    errorNotification(`生成失敗: ${e.message}`);
  } finally {
    isGeneratingPlan.value = false;
    hideLoading();
  }
}

async function handleGenerateUserInput() {
  if (!currentGrant.value || !currentTemplate.value) {
    errorNotification("請先選擇主題和模板！");
    return;
  }
  isLoading.value = true;

  isGeneratingPlan.value = true;

  try {
    const userId = await getUserIdOrNotify();
    if (!userId) {
      return;
    }
    // 構建動態字段當前值（用於 reverse 模式）
    const currentDynamicFields = {};
    const labelByCompositeKey = new Map(
      getDynamicFieldDefinitions().map((definition) => [
        definition.compositeKey,
        definition.label,
      ])
    );
    const sections = buildDynamicSections(dynamicFieldValues.value);
    sections.forEach((section) => {
      section.fields.forEach((field) => {
        if (field.value && field.value.trim() !== "") {
          const label =
            labelByCompositeKey.get(field.compositeKey) || field.title;
          currentDynamicFields[label] = field.value;
        }
      });
    });

    const payload = {
      mode: editableDraft.mode === "golden" ? "reverse" : "random",
      grant_name: currentGrant.value.name,
      template_name: currentTemplate.value.name,
      section_name: currentSections.value[0]?.name || "general",
      user_id: userId,
      dynamic_fields_schema: getDynamicFieldLabels().map((label) => ({
        label,
      })),
    };

    // 在 reverse 模式下，傳送 planContent 讓後端反推
    if (editableDraft.mode === "golden" && planContent.value) {
      payload.plan_content = planContent.value;
    }
    const response = await fetch(`${API_BASE_URL}/generate_synthetic_input`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    // 處理返回的結構化數據
    if (data.main_idea) {
      mainIdea.value = data.main_idea;
    }
    if (data.dynamic_fields) {
      const nextValues = { ...dynamicFieldValues.value };
      let hasUpdates = false;

      const attemptLabelMap = (fieldMap) => {
        let updated = false;
        Object.entries(fieldMap).forEach(([label, fieldValue]) => {
          const compositeKey = getCompositeKeyFromLabel(label);
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

      const attemptNestedMap = (fieldMap) => {
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
            }
          );
        });
        return updated;
      };

      hasUpdates = attemptLabelMap(data.dynamic_fields);

      if (!hasUpdates) {
        hasUpdates = attemptNestedMap(data.dynamic_fields);
      }

      if (hasUpdates) {
        isHydratingDynamicFields = true;
        dynamicFieldValues.value = mergeIntoEmptyValues(nextValues);
        debounceSave();
      }
    }
  } catch (error) {
    console.error("Error generating user input:", error);
    errorNotification(`生成失敗: ${error.message}`);
  } finally {
    isLoading.value = false;
    isGeneratingPlan.value = false;
  }
}
</script>
