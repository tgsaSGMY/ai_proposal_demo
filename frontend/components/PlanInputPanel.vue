<template>
  <div
    class="bg-white shadow-xl rounded-2xl p-4 sm:p-6 md:p-8 h-full flex flex-col"
  >
    <span class="text-sm sm:text-base font-semibold text-gray-800">
      一、摘要</span
    >
    <hr class="mb-4 sm:mb-6" />
    <!-- 第一层：主题 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mb-4 md:mb-6">
      <div>
        <label
          class="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2"
          >1. 選擇主題</label
        >
        <select
          v-model="selectedGrantId"
          @change="onGrantChange"
          class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition text-sm sm:text-base"
        >
          <option disabled value="">請選擇</option>
          <option v-for="grant in allConfigs" :key="grant.id" :value="grant.id">
            {{ grant.name }}
          </option>
        </select>
      </div>
      <div>
        <!-- 第二层：模板 -->
        <label
          class="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2"
          >2. 選擇模板</label
        >
        <select
          v-model="selectedTemplateId"
          :disabled="!selectedGrantId"
          class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition disabled:bg-gray-100 text-sm sm:text-base"
        >
          <option disabled value="">請選擇</option>
          <option
            v-for="template in availableTemplates"
            :key="template.id"
            :value="template.id"
          >
            {{ template.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- 第三层： 用户输入 + 辅助输入框 -->
    <div
      class="mb-4 sm:mb-6 space-y-4 sm:space-y-6 flex-grow flex flex-col min-h-0"
    >
      <!-- 主想法输入框 -->
      <div class="flex-shrink-0">
        <div
          class="flex flex-col sm:flex-row justify-between items-stretch sm:items-center mb-1 sm:mb-2 gap-2"
        >
          <label class="block text-xs sm:text-sm font-medium text-gray-700"
            >3. 描述你的項目名稱和摘要</label
          >
          <div
            class="flex items-center gap-2 self-start sm:self-auto flex-wrap"
          >
            <!-- <button
              v-if="mode === 'synthetic'"
              @click="$emit('generateUserInput')"
              class="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-lg hover:bg-gray-200 transition-colors"
              title="讓 AI 生成一個創新的項目想法"
            >
              ✨ 隨機生成想法
            </button>
            <button
              type="button"
              @click="triggerExcelUpload"
              :disabled="isImportingFromExcel"
              class="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded-lg hover:bg-indigo-200 transition-colors disabled:bg-indigo-50 disabled:text-indigo-300"
              title="從 Excel 匯入摘要與章節內容"
            >
              {{ isImportingFromExcel ? "匯入中..." : "📥 從 Excel 匯入" }}
            </button> -->
            <button
              type="button"
              @click="triggerWordUpload"
              :disabled="isLoading"
              class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-lg hover:bg-blue-200 transition-colors disabled:bg-blue-50 disabled:text-blue-300"
              title="從 Word 檔案匯入摘要與章節內容"
            >
              {{ isLoading ? "匯入中..." : "📄 從 Word 匯入" }}
            </button>
          </div>
        </div>
        <input
          ref="excelInputRef"
          type="file"
          class="hidden"
          accept=".xlsx,.xls"
          @change="handleExcelFileChange"
        />
        <input
          ref="wordInputRef"
          type="file"
          class="hidden"
          accept=".docx"
          @change="handleWordFileChange"
        />
        <textarea
          :value="modelValue"
          @input="$emit('update:modelValue', $event.target.value)"
          placeholder="例如：一個利用 AI 分析使用者評論，自動生成產品優化建議的 SaaS 平台..."
          rows="8"
          class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition resize-y p-2 text-sm sm:text-base"
        ></textarea>
      </div>

      <!-- 固定結構的輔助輸入區域 -->
      <div
        v-if="dynamicSections.length > 0"
        class="space-y-4 sm:space-y-6 border-t border-gray-200 pt-4 sm:pt-6 flex-grow overflow-y-auto pr-1 sm:pr-2"
      >
        <div
          class="p-3 sm:p-4 bg-indigo-50 border border-indigo-200 rounded-lg mb-4 sm:mb-6"
        >
          <p class="text-xs sm:text-sm text-indigo-700">
            <span class="font-semibold">專業提示：</span> 填寫以下細節能讓 AI
            生成更精準、更出色的內容！
          </p>
        </div>
        <ReferenceLinker
          :links="referenceLinks"
          :available-fields="referenceFieldOptions"
          @add="addReferenceLink"
          @remove="removeReferenceLink"
          @update="updateReferenceLink"
          @analyze="handleAnalyzeLink"
          @view-summary="viewLinkSummary"
          class="mt-6"
        />

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
              class="w-full flex items-center justify-between gap-3 px-3 sm:px-4 py-3 text-left transition hover:bg-indigo-50"
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
                <div class="flex flex-col gap-1">
                  <label class="text-xs sm:text-sm font-medium text-gray-600">
                    詳細內容
                  </label>
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
                    class="w-full rounded-lg border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition resize-y p-2 text-sm sm:text-base"
                  ></textarea>
                </div>
              </div>
            </transition>
          </div>
        </div>

        <div
          v-if="isSummaryModalVisible"
          @click.self="isSummaryModalVisible = false"
          class="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center"
        >
          <div
            class="bg-white rounded-lg shadow-xl w-full max-w-2xl p-4 sm:p-6"
          >
            <h3 class="text-base sm:text-lg font-bold mb-2 sm:mb-4">
              AI 分析重點
            </h3>
            <p class="text-gray-700 whitespace-pre-wrap text-sm sm:text-base">
              {{ currentSummary }}
            </p>
            <button
              @click="isSummaryModalVisible = false"
              class="mt-4 sm:mt-6 px-3 sm:px-4 py-2 bg-gray-200 rounded-md text-sm sm:text-base"
            >
              關閉
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 生成机会按钮 -->
    <button
      @click="emitGeneratePlan"
      v-if="mode !== 'golden'"
      :disabled="isGenerating || mode === 'golden' || !isReadyToGenerate"
      class="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-2.5 sm:py-3 rounded-lg shadow-md hover:bg-indigo-700 disabled:bg-indigo-300 disabled:cursor-not-allowed transition-all duration-300 text-sm sm:text-base"
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
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import {
  buildDynamicSections,
  createEmptyDynamicValues,
  mergeIntoEmptyValues,
  makeCompositeKey,
} from "~/utils/dynamicSchema";
import { useNotifications } from "~/composables/useNotifications";
import { useLoading } from "~/composables/useLoading";
import { useCurrentUser } from "~/composables/useCurrentUser";
import {
  applyExcelRows,
  buildExcelReplyTargetMap,
  extractExcelRows,
} from "~/utils/excelImport";
import {
  extractTextFromWord,
  callAutoFillApi,
  buildSectionSchema,
  processAutoFillResults,
} from "~/utils/wordImport";

const referenceLinks = ref([]);

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
});

const emit = defineEmits([
  "update:modelValue",
  "selectionChange",
  "generatePlan",
  "generateUserInput",
]);

const { success: notifySuccess, error: notifyError } = useNotifications();
const { isLoading } = useLoading();
const { userId: currentUserId, refreshUser } = useCurrentUser();

onMounted(() => {
  refreshUser();
});

async function getUserIdOrNotify() {
  const userId = currentUserId.value || (await refreshUser());
  if (!userId) {
    notifyError("無法取得使用者資訊，請重新登入後再試。");
  }
  return userId;
}

const excelInputRef = ref(null);
const wordInputRef = ref(null);
const isImportingFromExcel = ref(false);

// 內部狀態
const selectedGrantId = ref(props.initialGrantId);
const selectedTemplateId = ref(props.initialTemplateId);
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const internalDynamicValues = ref(createEmptyDynamicValues());
const expandedFieldIds = ref(new Set());

watch(
  dynamicValuesModel,
  (newVal) => {
    internalDynamicValues.value = mergeIntoEmptyValues(newVal, {
      templateId: selectedTemplateId.value,
      templateGrantId: selectedGrantId.value,
    });
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
const availableTemplates = computed(() => {
  if (!selectedGrantId.value) return [];
  const grant = props.allConfigs.find((g) => g.id === selectedGrantId.value);
  return grant ? grant.templates : [];
});

const dynamicSections = computed(() =>
  buildDynamicSections(internalDynamicValues.value, {
    templateId: selectedTemplateId.value,
    templateGrantId: selectedGrantId.value,
  })
);

const referenceFieldOptions = computed(() => {
  const sections = dynamicSections.value || [];
  return sections.flatMap((section) =>
    section.fields
      .filter((field) => !field.value || field.value.trim() === "")
      .map((field) => ({
        section_id: section.sectionId,
        property_key: field.propertyKey,
        label: `${section.sectionName} · ${field.title}`,
      }))
  );
});

const analysisTargets = computed(() =>
  referenceFieldOptions.value.map(({ section_id, property_key }) => ({
    section_id,
    property_key,
  }))
);

const excelReplyTargetMap = computed(() =>
  buildExcelReplyTargetMap(dynamicSections.value)
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
      resetDynamicValues();
      emit("selectionChange", {
        grantId: selectedGrantId.value,
        templateId: selectedTemplateId.value,
      });
    }
  }
);

const onGrantChange = () => {
  const isIncluded = availableTemplates.value.some(
    (t) => t.id === selectedTemplateId.value
  );

  if (!isIncluded) {
    selectedTemplateId.value = "";
  }
};

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

  const completedSummaries = referenceLinks.value
    .filter((link) => link.status === "completed" && link.summary)
    .map((link) => link.summary);

  emit("generatePlan", { summaries: completedSummaries });
};

function triggerExcelUpload() {
  if (isImportingFromExcel.value) {
    return;
  }
  const input = excelInputRef.value;
  if (input) {
    input.value = "";
    input.click();
  }
}

function triggerWordUpload() {
  const input = wordInputRef.value;
  if (input) {
    input.value = "";
    input.click();
  }
}

async function handleWordFileChange(event) {
  const input = event?.target;
  const file = input?.files?.[0];
  if (input) {
    input.value = "";
  }
  if (!file) {
    return;
  }

  const { show: showLoading, hide: hideLoading } = useLoading();
  showLoading("正在從 Word 檔案中提取內容...");

  try {
    // 檢查是否選擇了模板
    if (!selectedTemplateId.value) {
      notifyError("請先選擇模板，以便我們知道要填充哪些欄位");
      return;
    }

    // 提取 Word 檔案中的文本
    const extractedText = await extractTextFromWord(file);

    const userId = await getUserIdOrNotify();
    if (!userId) {
      return;
    }

    // 準備傳送給後端的資料
    const payload = {
      document_text: extractedText,
      sections: dynamicSections.value.map((s) => ({
        section_id: s.sectionId,
        section_name: s.sectionName,
        json_schema: buildSectionSchema(s),
      })),
      user_id: userId,
    };

    const filledContent = await callAutoFillApi(payload, API_BASE_URL);
    modelValue.value =
      filledContent?.main_idea?.content?.project_name_and_summary || "";

    // 處理結果：填入動態欄位
    processAutoFillResults(
      filledContent,
      dynamicSections.value,
      updateDynamicValue,
      ensureFieldExpanded
    );

    notifySuccess("Word 檔案匯入完成！");
  } catch (error) {
    console.error("Failed to import Word document", error);
    const message = error?.message || "匯入過程發生未知錯誤";
    notifyError(`匯入失敗：${message}`);
  } finally {
    hideLoading();
  }
}

async function handleExcelFileChange(event) {
  const input = event?.target;
  const file = input?.files?.[0];
  if (input) {
    input.value = "";
  }
  if (!file) {
    return;
  }

  isImportingFromExcel.value = true;
  try {
    const buffer = await file.arrayBuffer();
    const rows = extractExcelRows(buffer);
    const result = applyExcelRows({
      rows,
      dynamicSections: dynamicSections.value,
      replyTargetMap: excelReplyTargetMap.value,
      onFill: (sectionId, propertyKey, value) => {
        updateDynamicValue(sectionId, propertyKey, value);
        ensureFieldExpanded(sectionId, propertyKey);
      },
    });

    if (result.summaryText) {
      modelValue.value = result.summaryText;
    }

    const messageParts = [];
    if (result.summaryText) {
      messageParts.push("已更新摘要內容");
    }
    if (result.appliedCount > 0) {
      messageParts.push(`填入 ${result.appliedCount} 個欄位`);
    }
    if (result.skippedCount > 0) {
      messageParts.push(`略過 ${result.skippedCount} 筆未匹配欄位`);
    }

    if (messageParts.length > 0) {
      notifySuccess(`Excel 匯入完成：${messageParts.join("、")}`);
    } else {
      notifyError("Excel 檔案未包含可匯入的資料");
    }
  } catch (error) {
    console.error("Failed to import Excel data", error);
    const message = error?.message || "匯入過程發生未知錯誤";
    notifyError(`匯入失敗：${message}`);
  } finally {
    isImportingFromExcel.value = false;
  }
}

const isSummaryModalVisible = ref(false);
const currentSummary = ref("");

function addReferenceLink() {
  referenceLinks.value.push({ url: "", status: "pending", summary: "" });
}

function ensureFieldExpanded(sectionId, propertyKey) {
  const id = fieldPanelKey(sectionId, propertyKey);
  if (expandedFieldIds.value.has(id)) {
    return;
  }
  const next = new Set(expandedFieldIds.value);
  next.add(id);
  expandedFieldIds.value = next;
}

function applyAutoFillEntries(autoFillItems = []) {
  if (!Array.isArray(autoFillItems) || autoFillItems.length === 0) {
    return [];
  }

  const applied = [];

  autoFillItems.forEach((item) => {
    const compositeKey = (item.composite_key || item.compositeKey || "").trim();
    if (!compositeKey) {
      return;
    }

    const [sectionId, propertyKey] = compositeKey.split("::");
    if (!sectionId || !propertyKey) {
      return;
    }

    const content = (item.content || "").trim();
    if (!content) {
      return;
    }

    const currentValue = internalDynamicValues.value[compositeKey] || "";
    if (currentValue.trim()) {
      return;
    }

    updateDynamicValue(sectionId, propertyKey, content);
    ensureFieldExpanded(sectionId, propertyKey);

    applied.push({
      compositeKey,
      label: item.label || "",
      content,
    });
  });

  return applied;
}

function removeReferenceLink(index) {
  referenceLinks.value.splice(index, 1);
}

function updateReferenceLink({ index, field, value }) {
  if (referenceLinks.value[index]) {
    referenceLinks.value[index][field] = value;
    if (field === "url") {
      referenceLinks.value[index].status = "pending";
      referenceLinks.value[index].summary = "";
    }
  }
}

function viewLinkSummary(index) {
  if (referenceLinks.value[index]) {
    currentSummary.value = referenceLinks.value[index].summary;
    isSummaryModalVisible.value = true;
  }
}

async function handleAnalyzeLink(index) {
  const link = referenceLinks.value[index];
  if (!link || !link.url) return;

  link.status = "loading";
  try {
    const selectedFieldLabels =
      Array.isArray(link.selectedFields) && link.selectedFields.length > 0
        ? link.selectedFields
        : null;

    const targetFields = selectedFieldLabels
      ? referenceFieldOptions.value.filter((field) =>
          selectedFieldLabels.includes(field.label)
        )
      : referenceFieldOptions.value;

    const contextTargets = targetFields.length
      ? targetFields.map(({ section_id, property_key }) => ({
          section_id,
          property_key,
        }))
      : analysisTargets.value;

    const response = await fetch(`${API_BASE_URL}/scrape_and_analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: link.url,
        context_targets: contextTargets,
        max_items: selectedFieldLabels ? targetFields.length || 1 : 4,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "分析失敗");
    }

    const result = await response.json();
    const summaryText =
      typeof result.summary === "string" ? result.summary.trim() : "";
    const autoFillItems = Array.isArray(result.auto_fill)
      ? result.auto_fill
      : [];
    const appliedEntries = applyAutoFillEntries(autoFillItems);

    const summaryLines = [];
    if (summaryText) {
      summaryLines.push(summaryText);
    }

    if (appliedEntries.length > 0) {
      if (summaryLines.length > 0) {
        summaryLines.push("");
      }
      summaryLines.push("自動填寫欄位：");
      appliedEntries.forEach((entry) => {
        const label = entry.label || entry.compositeKey;
        summaryLines.push(`- ${label}: ${entry.content}`);
      });
    }

    const finalSummary = summaryLines.join("\n").trim();
    link.summary = finalSummary || "此連結未產生可用的摘要。";
    link.status = "completed";
    if (selectedFieldLabels) {
      link.selectedFields = [];
    }
  } catch (error) {
    console.error(`Error analyzing URL ${link.url}:`, error);
    link.status = "error";
    link.summary = `分析失敗: ${error.message}`;
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
