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
          :dynamic-inputs="dynamicInputsWithValues"
          :mode="editableDraft.mode"
          :initial-grant-id="editableDraft.grant_id"
          :initial-template-id="editableDraft.template_id"
          @update:modelValue="updateMainIdea"
          @update:dynamic-inputs="updateDynamicInputs"
          @selectionChange="onSelectionChangeInModal"
          @generatePlan="handleGeneratePlanInModal"
          @generateUserInput="handleGenerateUserInput"
        />
        <PlanOutputPanel
          :plan-content="planContent"
          :sections="currentSections"
          :mode="editableDraft.mode"
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
import PlanInputPanel from "~/components/PlanInputPanel.vue";
import PlanOutputPanel from "~/components/PlanOutputPanel.vue";
import PlanCandidateSelector from "~/components/PlanCandidateSelector.vue";

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

const {
  selectedGrantId,
  selectedTemplateId,
  fetchAllConfigs,
  planContent,
  currentGrant,
  currentTemplate,
  currentSections,
  allConfigs,
} = usePlanGenerator();

const isGeneratingPlan = ref(false);
const editableDraft = reactive(JSON.parse(JSON.stringify(props.draft)));

// --- State Initialization and Synchronization ---
onMounted(async () => {
  await fetchAllConfigs();
  // Force Composable state to match the draft's config
  selectedGrantId.value = props.draft.grant_id;
  selectedTemplateId.value = props.draft.template_id;
  planContent.value = props.draft.plan_content;
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

// This computed property merges the template structure (dynamicInputs) with actual values from the draft
const dynamicInputsWithValues = computed(() => {
  if (!currentSections.value || currentSections.value.length === 0) {
    return [];
  }

  const groupedInputs = [];
  currentSections.value.forEach((section) => {
    const sectionInputs = [];
    if (section.json_schema && section.json_schema.properties) {
      Object.entries(section.json_schema.properties).forEach(([key, prop]) => {
        sectionInputs.push({
          id: `${section.id}-${key}`,
          key: key,
          label: prop.description || key.replace("_", " "),
          value:
            editableDraft.user_input?.dynamic_fields?.[prop.description] || "",
        });
      });
    }

    // 无论是否有 inputs，都创建 group 以显示 custom_prompt_list
    groupedInputs.push({
      sectionId: section.id,
      sectionName: section.name,
      inputs: sectionInputs,
      custom_prompt_list: section.custom_prompt_list || [],
    });
  });

  return groupedInputs;
});

// --- Debounce for saving draft updates ---
let saveTimer = null;

const saveUpdatesToDb = async () => {
  try {
    // Build dynamic_fields from dynamicInputsWithValues
    const dynamic_fields = {};
    dynamicInputsWithValues.value
      .flatMap((g) => g.inputs)
      .forEach((input) => {
        dynamic_fields[input.key] = input.value;
      });
    editableDraft.user_input.dynamic_fields = dynamic_fields;

    const payload = {
      name: editableDraft.name,
      grant_id: editableDraft.grant_id,
      template_id: editableDraft.template_id,
      user_input: editableDraft.user_input,
      plan_content: planContent.value,
    };

    const res = await fetch(`${API_BASE_URL}/draft_plans/${props.draft.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
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

function updateDynamicInputs(newDynamicInputsGroups) {
  if (!editableDraft.user_input) editableDraft.user_input = {};
  if (!editableDraft.user_input.dynamic_fields)
    editableDraft.user_input.dynamic_fields = {};

  // Flatten and update the dynamic_fields object
  newDynamicInputsGroups
    .flatMap((g) => g.inputs)
    .forEach((input) => {
      editableDraft.user_input.dynamic_fields[input.key] = input.value;
    });
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
  showCandidateModal.value = false;
  saveUpdatesToDb();
  success("已選擇方案並填充到結果中！");
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
  const additionalDetails = dynamicInputsWithValues.value
    .flatMap((g) => g.inputs)
    .filter((input) => input.key && String(input.value).trim() !== "")
    .map((input) => `關於“${input.label}”的補充信息:\n${input.value}`)
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

async function handleGeneratePlanInModal(outerPayload) {
  isGeneratingPlan.value = true;
  showLoading();
  try {
    const finalUserInput = buildFinalUserInputForGeneration(
      outerPayload?.summaries
    );
    const sectionsToGenerate = currentSections.value.map((s) => ({
      section_id: s.id,
    }));

    const response = await fetch(`${API_BASE_URL}/generate_plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "dba4dabc-a24d-4e1a-aa2b-b239d06a8cf5",
        grant: selectedGrantId.value,
        template: selectedTemplateId.value,
        sections: sectionsToGenerate,
        user_input: finalUserInput,
        num_candidates: 2,
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
    const flattened = Object.fromEntries(
      Object.entries(planContent.value).map(([key, section]) => [
        key,
        section.content ?? section,
      ])
    );

    const payload = {
      mode: editableDraft.mode === "golden" ? "reverse" : "random",
      grant_name: currentGrant.value.name,
      template_name: currentTemplate.value.name,
      section_name: currentSections.value[0]?.name || "general",
      json_output: editableDraft.mode === "golden" ? flattened : null,
      user_id: "dba4dabc-a24d-4e1a-aa2b-b239d06a8cf5",
      // 傳遞動態字段的 schema
      dynamic_fields_schema:
        editableDraft.mode !== "golden"
          ? dynamicInputsWithValues.value
              .flatMap((group) => group.inputs)
              .map((f) => ({ label: f.label }))
          : null,
    };
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
      if (editableDraft.mode !== "golden") {
        dynamicInputsWithValues.value.forEach((group) => {
          group.inputs.forEach((input) => {
            if (data.dynamic_fields[input.label]) {
              input.value = data.dynamic_fields[input.label];
            }
          });
        });
      } else {
        // 对应 'reverse' 模式
        dynamicInputsWithValues.value.forEach((group) => {
          if (data.dynamic_fields[group.sectionId]) {
            const sectionData = data.dynamic_fields[group.sectionId];
            group.inputs.forEach((input) => {
              const [_, fieldKey] = input.id.split("-", 2);
              if (sectionData[fieldKey]) {
                input.value = sectionData[fieldKey];
              }
            });
          }
        });
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
