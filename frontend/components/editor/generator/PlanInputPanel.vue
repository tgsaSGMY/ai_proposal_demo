<template>
  <div
    class="bg-white shadow-xl rounded-2xl p-4 sm:p-6 md:p-8 h-full flex flex-col"
  >
    <span class="text-sm sm:text-base font-semibold text-gray-800">
      一、摘要</span
    >
    <hr class="mb-4 sm:mb-6" />
    <!-- 第一層：主題與模板（唯讀展示） -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mb-4 md:mb-6">
      <div class="rounded-2xl border border-gray-200 bg-gray-50/60 p-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-gray-400">
          1. 選擇主題
        </p>
        <p class="mt-2 text-base font-semibold text-gray-900">
          {{ selectedGrantName }}
        </p>
      </div>
      <div class="rounded-2xl border border-gray-200 bg-gray-50/60 p-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-gray-400">
          2. 選擇模板
        </p>
        <p class="mt-2 text-base font-semibold text-gray-900">
          {{ selectedTemplateName }}
        </p>
      </div>
    </div>

    <!-- 第二層：項目資訊（唯讀展示） -->
    <div class="space-y-4 mb-6">
      <div class="rounded-2xl border border-gray-200 bg-white/80 p-4">
        <p class="text-xs font-semibold uppercase tracking-wide text-gray-400">
          3. 項目名稱
        </p>
        <p class="mt-2 text-lg font-semibold text-gray-900">
          {{ displayPlanName }}
        </p>
      </div>
      <div class="rounded-2xl border border-gray-200 bg-white/80 p-4">
        <div
          class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
        >
          <p
            class="text-xs font-semibold uppercase tracking-wide text-gray-400"
          >
            4. 項目摘要
          </p>
        </div>
        <p class="mt-3 text-sm text-gray-600 whitespace-pre-line">
          {{ displayPlanSummary }}
        </p>
      </div>
    </div>

    <!-- 第三層：動態欄位 -->
    <div
      class="mb-4 sm:mb-6 space-y-4 sm:space-y-6 flex-grow flex flex-col min-h-0"
    >
      <div
        v-if="dynamicSections.length > 0"
        class="space-y-4 sm:space-y-6 border-t border-gray-200 pt-4 sm:pt-6 flex-grow overflow-y-auto pr-1 sm:pr-2"
      >
        <div
          v-for="section in dynamicSections"
          :key="section.sectionId"
          class="space-y-3 sm:space-y-4"
        >
          <div class="flex items-center justify-between border-b pb-1 sm:pb-2">
            <h4 class="text-sm sm:text-md font-semibold text-gray-800">
              {{ section.sectionName }}
            </h4>
            <span
              class="text-xs text-gray-400"
              v-if="
                section.fields.some(
                  (field) => field.value && field.value.trim() !== ''
                )
              "
            >
              已填寫項目
            </span>
          </div>

          <div
            v-for="field in section.fields"
            :key="field.propertyKey"
            class="rounded-xl border border-gray-200 bg-white/80 shadow-sm"
          >
            <button
              type="button"
              class="w-full flex items-center justify-between gap-3 px-3 sm:px-4 py-3 text-left transition hover:bg-rose-50"
              @click="toggleField(section.sectionId, field.propertyKey)"
            >
              <div class="flex flex-col">
                <span class="text-sm sm:text-base font-semibold text-gray-800">
                  {{ field.title }}
                </span>
                <span class="text-xs text-gray-500">
                  {{ computeFieldStatus(field.value) }}
                </span>
              </div>
              <svg
                class="w-4 h-4 text-gray-500 transition-transform duration-200"
                :class="{
                  'rotate-90': isFieldExpanded(
                    section.sectionId,
                    field.propertyKey
                  ),
                }"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>

            <transition name="fade">
              <div
                v-if="isFieldExpanded(section.sectionId, field.propertyKey)"
                class="px-3 sm:px-4 pb-4 space-y-3 border-t border-gray-100"
              >
                <p
                  v-if="field.description"
                  class="text-xs sm:text-sm text-gray-600 whitespace-pre-line pt-3"
                >
                  {{ field.description }}
                </p>
                <div
                  class="flex flex-col gap-2 rounded-lg border border-transparent p-2 transition hover:border-rose-100"
                >
                  <div class="flex items-center justify-between gap-3">
                    <span class="text-xs sm:text-sm font-semibold text-gray-600"
                      >填寫內容</span
                    >
                    <div class="flex items-center gap-2">
                      <button
                        type="button"
                        class="text-[11px] sm:text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
                        @click.stop="
                          generateFieldWithAI(section.sectionId, field)
                        "
                        :disabled="isGeneratingField"
                      >
                        <svg
                          v-if="!isGeneratingField"
                          class="w-3.5 h-3.5"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          stroke-width="1.5"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M13 10V3L4 14h7v7l9-11h-7z"
                          />
                        </svg>
                        <svg
                          v-else
                          class="animate-spin w-3.5 h-3.5"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            class="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            stroke-width="4"
                          ></circle>
                          <path
                            class="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                          ></path>
                        </svg>
                        AI填寫
                      </button>
                      <button
                        type="button"
                        class="text-[11px] sm:text-xs font-semibold text-rose-600 hover:text-rose-700 flex items-center gap-1"
                        @click.stop="
                          openFileImportModal(section.sectionId, field)
                        "
                      >
                        <svg
                          class="w-3.5 h-3.5"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          stroke-width="1.5"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3"
                          />
                        </svg>
                        匯入檔案
                      </button>
                    </div>
                  </div>
                  <textarea
                    :value="field.value"
                    :placeholder="field.placeholder"
                    @input="
                      updateDynamicValue(
                        section.sectionId,
                        field.propertyKey,
                        $event.target.value
                      )
                    "
                    rows="4"
                    class="w-full rounded-lg border border-gray-300 shadow-sm focus:border-rose-400 focus:ring-2 focus:ring-rose-200 transition resize-y p-2 text-sm sm:text-base"
                  ></textarea>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </div>

    <!-- 生成机会按钮 -->
    <button
      @click="emitGeneratePlan"
      v-if="mode !== 'golden'"
      :disabled="isGenerating || mode === 'golden' || !isReadyToGenerate"
      class="w-full flex items-center justify-center gap-2 bg-rose-600 text-white font-semibold py-2.5 sm:py-3 rounded-lg shadow-md hover:bg-rose-700 disabled:bg-rose-400 disabled:cursor-not-allowed transition-all duration-300 text-sm sm:text-base"
    >
      <svg
        v-if="isGenerating"
        class="animate-spin h-5 w-5 text-white"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        ></circle>
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
        ></path>
      </svg>
      {{ isGenerating ? "正在生成..." : "生成完整計劃書" }}
    </button>
  </div>
  <FieldFileImportModal
    v-model:is-open="fileImportState.isOpen"
    :field-title="fileImportState.fieldTitle"
    :field-description="fileImportState.fieldDescription"
    :field-label="fileImportState.fieldLabel"
    :field-value="fileImportState.currentValue"
    @confirm="handleFileImportConfirm"
  />
</template>

<script setup>
import { computed, ref, watch } from "vue";
import {
  buildDynamicSections,
  createEmptyDynamicValues,
  mergeIntoEmptyValues,
  makeCompositeKey,
} from "~/utils/dynamicSchema";
import { useNotifications } from "~/composables/useNotifications";
import { useCurrentUser } from "~/composables/useCurrentUser";
import { useRuntimeConfig } from "#app";
import FieldFileImportModal from "~/components/editor/helper/FieldFileImportModal.vue";

const modelValue = defineModel();
const dynamicValuesModel = defineModel("dynamicValues", {
  type: Object,
  default: () => createEmptyDynamicValues(),
});

const props = defineProps({
  allConfigs: { type: Array, required: true },
  isGenerating: { type: Boolean, default: false },
  mode: { type: String, required: true },
  initialGrantId: { type: String, default: "" },
  initialTemplateId: { type: String, default: "" },
  projectTitle: { type: String, default: "" },
  projectSummary: { type: String, default: "" },
});

const emit = defineEmits([
  "update:modelValue",
  "selectionChange",
  "generatePlan",
  "generateUserInput",
]);

const { success: notifySuccess, error: notifyError } = useNotifications();
const { userId } = useCurrentUser();

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const isGeneratingField = ref(false);

const displayPlanName = computed(() => {
  const provided = (props.projectTitle || "").trim();
  return provided || "尚未提供項目名稱";
});

const displayPlanSummary = computed(() => {
  const provided = (props.projectSummary || "").trim();
  if (provided) {
    return provided;
  }
  const fallback = (modelValue.value || "").trim();
  return fallback || "尚未提供摘要";
});

// 內部狀態
const selectedGrantId = ref(props.initialGrantId);
const selectedTemplateId = ref(props.initialTemplateId);

const internalDynamicValues = ref(createEmptyDynamicValues());
const expandedFieldIds = ref(new Set());

const createFileImportState = () => ({
  isOpen: false,
  sectionId: "",
  propertyKey: "",
  fieldTitle: "",
  fieldDescription: "",
  fieldLabel: "",
  currentValue: "",
});

const fileImportState = ref(createFileImportState());

watch(
  dynamicValuesModel,
  (newVal) => {
    internalDynamicValues.value = mergeIntoEmptyValues(newVal);
  },
  { immediate: true, deep: true }
);

function resetDynamicValues() {
  internalDynamicValues.value = createEmptyDynamicValues();
  dynamicValuesModel.value = { ...internalDynamicValues.value };
  expandedFieldIds.value = new Set();
}

watch(
  () => props.initialGrantId,
  (newVal) => {
    if (selectedGrantId.value !== newVal) {
      selectedGrantId.value = newVal;
    }
  }
);

watch(
  () => props.initialTemplateId,
  (newVal) => {
    if (selectedTemplateId.value !== newVal) {
      selectedTemplateId.value = newVal;
    }
  }
);

// 計算屬性（模板和章節）
const selectedGrant = computed(() => {
  if (!selectedGrantId.value) {
    return null;
  }
  return props.allConfigs.find((g) => g.id === selectedGrantId.value) || null;
});

const availableTemplates = computed(() => {
  return selectedGrant.value?.templates || [];
});

const selectedTemplate = computed(() => {
  if (!selectedTemplateId.value) {
    return null;
  }
  return (
    availableTemplates.value.find(
      (tpl) => tpl.id === selectedTemplateId.value
    ) || null
  );
});

const selectedGrantName = computed(
  () => selectedGrant.value?.name || "尚未選擇"
);

const selectedTemplateName = computed(
  () => selectedTemplate.value?.name || "尚未選擇"
);

const dynamicSections = computed(() =>
  buildDynamicSections(internalDynamicValues.value)
);

const isReadyToGenerate = computed(() => {
  return (
    selectedTemplateId.value &&
    modelValue.value &&
    modelValue.value.trim() !== ""
  );
});

watch(
  [selectedGrantId, selectedTemplateId],
  ([newGrant, newTemplate], [oldGrant, oldTemplate]) => {
    const grantChanged = oldGrant !== undefined && oldGrant !== newGrant;
    const templateChanged =
      oldTemplate !== undefined && oldTemplate !== newTemplate;

    if (grantChanged || templateChanged) {
      if (
        grantChanged &&
        selectedTemplateId.value &&
        !availableTemplates.value.some(
          (tpl) => tpl.id === selectedTemplateId.value
        )
      ) {
        selectedTemplateId.value = "";
      }
      resetDynamicValues();
      emit("selectionChange", {
        grantId: selectedGrantId.value,
        templateId: selectedTemplateId.value,
      });
    }
  }
);

function updateDynamicValue(sectionId, propertyKey, value) {
  const key = makeCompositeKey(sectionId, propertyKey);
  internalDynamicValues.value = {
    ...internalDynamicValues.value,
    [key]: value,
  };
  dynamicValuesModel.value = { ...internalDynamicValues.value };
}

function fieldPanelKey(sectionId, propertyKey) {
  return `${sectionId}::${propertyKey}`;
}

function toggleField(sectionId, propertyKey) {
  const id = fieldPanelKey(sectionId, propertyKey);
  const next = new Set(expandedFieldIds.value);
  if (next.has(id)) {
    next.delete(id);
  } else {
    next.add(id);
  }
  expandedFieldIds.value = next;
}

function isFieldExpanded(sectionId, propertyKey) {
  return expandedFieldIds.value.has(fieldPanelKey(sectionId, propertyKey));
}

function computeFieldStatus(value) {
  if (value && value.trim() !== "") {
    return "已填寫";
  }
  return "可選填";
}

const emitGeneratePlan = () => {
  if (!isReadyToGenerate.value) return;
  emit("generatePlan", { summaries: [] });
};

function ensureFieldExpanded(sectionId, propertyKey) {
  const id = fieldPanelKey(sectionId, propertyKey);
  if (expandedFieldIds.value.has(id)) {
    return;
  }
  const next = new Set(expandedFieldIds.value);
  next.add(id);
  expandedFieldIds.value = next;
}

function openFileImportModal(sectionId, field) {
  fileImportState.value = {
    isOpen: true,
    sectionId,
    propertyKey: field.propertyKey,
    fieldTitle: field.title,
    fieldDescription: field.description || "",
    fieldLabel: field.title,
    currentValue: field.value || "",
  };
}

function handleFileImportConfirm(newValue) {
  const state = fileImportState.value;
  if (!state.sectionId || !state.propertyKey) {
    fileImportState.value = createFileImportState();
    return;
  }
  updateDynamicValue(state.sectionId, state.propertyKey, newValue);
  ensureFieldExpanded(state.sectionId, state.propertyKey);
  notifySuccess("欄位內容已透過檔案匯入更新。");
  fileImportState.value = createFileImportState();
}

watch(
  () => fileImportState.value.isOpen,
  (isOpen, wasOpen) => {
    if (!isOpen && wasOpen) {
      fileImportState.value = createFileImportState();
    }
  }
);

async function generateFieldWithAI(sectionId, field) {
  if (isGeneratingField.value) return;

  isGeneratingField.value = true;
  try {
    // 收集已填寫的其他欄位
    const filledFields = {};
    const sections = buildDynamicSections(internalDynamicValues.value);
    sections.forEach((section) => {
      section.fields.forEach((f) => {
        if (f.value && f.value.trim() !== "") {
          filledFields[`${section.sectionName} · ${f.title}`] = f.value;
        }
      });
    });

    // 调用后端 API
    const response = await fetch(`${API_BASE_URL}/generate_field_content`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        field_title: field.title,
        field_description: field.description || "",
        subfield_label: field.title,
        current_value: field.value || "",
        filled_fields: filledFields,
        plan_name: props.projectTitle || "",
        plan_summary: props.projectSummary || "",
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`服務器錯誤 (${response.status}): ${errorText}`);
    }

    const result = await response.json();
    const generatedContent = result.generated_content
      ? "(AI 填寫) " + result.generated_content
      : "";

    if (generatedContent.trim()) {
      // 更新欄位內容
      updateDynamicValue(sectionId, field.propertyKey, generatedContent);
      ensureFieldExpanded(sectionId, field.propertyKey);
      notifySuccess("AI 已為欄位填寫內容，請檢查並編輯。");
    } else {
      notifyError("AI 無法為此欄位生成內容。");
    }
  } catch (error) {
    console.error("AI 填寫失敗:", error);
    notifyError(`AI 填寫失敗: ${error.message}`);
  } finally {
    isGeneratingField.value = false;
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
