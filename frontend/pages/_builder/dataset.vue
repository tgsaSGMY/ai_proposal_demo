<template>
  <div class="p-4 md:p-8 h-full flex flex-col bg-gray-50">
    <!-- 頂部控制欄 -->
    <div
      class="flex-shrink-0 mb-6 flex justify-between items-center bg-white p-4 rounded-lg shadow"
    >
      <div>
        <h1 class="text-2xl font-bold text-gray-800">數據集生成工作室</h1>
        <div class="mt-2 flex items-center gap-4 text-sm">
          <label class="font-medium text-gray-700">模式:</label>
          <div class="flex gap-2">
            <button
              @click="setMode('synthetic')"
              :class="[
                'px-4 py-1.5 rounded-full font-semibold transition-all',
                mode === 'synthetic'
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'bg-gray-200 text-gray-600 hover:bg-gray-300',
              ]"
            >
              🤖 AI 生成 (Synthetic)
            </button>
            <button
              @click="setMode('golden')"
              :class="[
                'px-4 py-1.5 rounded-full font-semibold transition-all',
                mode === 'golden'
                  ? 'bg-green-500 text-white shadow-md'
                  : 'bg-gray-200 text-gray-600 hover:bg-gray-300',
              ]"
            >
              🏆 手動標註 (Golden)
            </button>
          </div>
        </div>
      </div>
      <button
        @click="handleSave"
        :disabled="isSaving || Object.keys(planContent).length === 0"
        class="bg-indigo-600 text-white font-bold py-3 px-6 rounded-lg shadow-md hover:bg-indigo-700 disabled:bg-indigo-300 flex items-center gap-2"
      >
        <svg
          v-if="isSaving"
          class="animate-spin h-5 w-5"
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
        {{ isSaving ? "保存中..." : "保存至數據集" }}
      </button>
    </div>

    <!-- 主工作區 -->
    <div class="flex-grow grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0">
      <PlanInputPanel
        :all-configs="allConfigs"
        v-model:userInput="userInput"
        :dynamic-inputs="dynamicInputs"
        @update:dynamic-inputs="(newVal) => (dynamicInputs = newVal)"
        :is-generating="isGenerating"
        :mode="mode"
        @selectionChange="onSelectionChange"
        @generatePlan="handleGeneratePlan"
        @generateUserInput="handleGenerateUserInput"
        :initial-grant-id="selectedGrantId"
        :initial-template-id="selectedTemplateId"
      />
      <PlanOutputPanel
        :plan-content="planContent"
        :sections="currentSections"
        :mode="mode"
        @update:content="onContentUpdate"
        @generateUserInput="handleGenerateUserInput"
        @autoFillComplete="handleAutoFill"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from "vue";
import PlanInputPanel from "~/components/PlanInputPanel.vue"; // 假設您的組件路徑
import PlanOutputPanel from "~/components/PlanOutputPanel.vue"; // 假設您的組件路徑
import { useLoading } from "~/composables/useLoading";
import { useNotifications } from "~/composables/useNotifications";
const { success, error: errorNotification } = useNotifications();
const { isLoading } = useLoading();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

// 狀態
const mode = ref("synthetic"); // 'synthetic' or 'golden'
const allConfigs = ref([]);
const userInput = ref("");
const planContent = ref({}); // { section_id: { content: "...", error: "..." } }

const selectedGrantId = ref("");
const selectedTemplateId = ref("");

const isGenerating = ref(false);
const isSaving = ref(false);
const dynamicInputs = ref([]); // [{ id, label, value }]

// --- Computed Properties ---
const availableTemplates = computed(() => {
  if (!selectedGrantId.value) return [];
  const grant = allConfigs.value.find((g) => g.id === selectedGrantId.value);
  return grant ? grant.templates : [];
});

const currentSections = computed(() => {
  if (!selectedTemplateId.value) return [];
  const template = availableTemplates.value.find(
    (t) => t.id === selectedTemplateId.value
  );
  return template ? template.sections : [];
});

const currentGrant = computed(() => {
  allConfigs.value.find((g) => g.id === selectedGrantId.value);
});
const currentTemplate = computed(() =>
  availableTemplates.value.find((t) => t.id === selectedTemplateId.value)
);

// --- Lifecycle & Data Fetching ---
onMounted(async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/config`);
    if (!response.ok) throw new Error("Network response was not ok");
    allConfigs.value = await response.json();
  } catch (error) {
    console.error("Failed to load config:", error);
    errorNotification("無法加載應用配置。");
  }
});

watch(
  currentSections,
  (newSections) => {
    const groupedInputs = []; // 改用一個新的分組數組
    if (newSections && newSections.length > 0) {
      newSections.forEach((section) => {
        const sectionInputs = []; // 存放當前 section 的所有 input
        const prompts = section.custom_prompt_list || [];
        if (section.json_schema && section.json_schema.properties) {
          Object.entries(section.json_schema.properties).forEach(
            ([key, prop]) => {
              // 在分組模式下，我們不再需要跨 section 去重，因為問題是屬於特定 section 的
              sectionInputs.push({
                id: `${section.id}-${key}`,
                label: prop.description || key.replace("_", " "),
                value: "", // 初始值為空
              });
            }
          );
        }

        // 如果這個 section 有任何 input，就創建一個分組對象
        if (sectionInputs.length > 0) {
          groupedInputs.push({
            sectionId: section.id,
            sectionName: section.name,
            inputs: sectionInputs,
            custom_prompt_list: prompts,
            system_prompt: section.system_prompt || "",
          });
        }
      });
    }
    dynamicInputs.value = groupedInputs;
  },
  { deep: true }
);

// --- Event Handlers ---
function onSelectionChange(selection) {
  selectedGrantId.value = selection.grantId;
  selectedTemplateId.value = selection.templateId; // 保持对用户手动选择的支持
  planContent.value = {}; // 重置輸出
}

function setMode(newMode) {
  mode.value = newMode;
  // 重置狀態以避免混淆
  userInput.value = "";
  planContent.value = {};
}

function onContentUpdate({ sectionId, content }) {
  if (!planContent.value[sectionId]) {
    planContent.value[sectionId] = {};
  }
  planContent.value[sectionId].content = content;
}

async function handleGenerateUserInput() {
  if (!currentGrant.value || !currentTemplate.value) {
    errorNotification("請先選擇主題和模板！");
    return;
  }
  isLoading.value = true;

  isGenerating.value = true;

  try {
    const flattened = Object.fromEntries(
      Object.entries(planContent.value).map(([key, section]) => [
        key,
        section.content ?? section,
      ])
    );

    const payload = {
      mode: mode.value === "golden" ? "reverse" : "random",
      grant_name: currentGrant.value.name,
      template_name: currentTemplate.value.name,
      section_name: currentSections.value[0]?.name || "general",
      json_output: mode.value === "golden" ? flattened : null,
      // 傳遞動態字段的 schema
      dynamic_fields_schema:
        mode.value !== "golden"
          ? dynamicInputs.value
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
      userInput.value = data.main_idea;
    }
    if (data.dynamic_fields && mode.value !== "golden") {
      // 更新 dynamicInputs 的 value
      // `${section.id}-${key}`
      dynamicInputs.value
        .flatMap((group) => group.inputs)
        .forEach((input) => {
          if (data.dynamic_fields[input.label]) {
            input.value = data.dynamic_fields[input.label];
          }
        });
    }

    if (data.dynamic_fields && mode.value === "golden") {
      dynamicInputs.value
        .flatMap((group) => group.inputs)
        .forEach((input) => {
          // 拆開 id，例如 "company_overview-company_profile_paragraph"
          const [sectionId, fieldKey] = input.id.split("-", 2);

          // 檢查巢狀結構是否存在
          const sectionData = data.dynamic_fields[sectionId];
          if (sectionData && fieldKey in sectionData) {
            input.value = sectionData[fieldKey];
          }
        });
    }
  } catch (error) {
    console.error("Error generating user input:", error);
    errorNotification(`生成失敗: ${error.message}`);
  } finally {
    isLoading.value = false;
    isGenerating.value = false;
  }
}

function buildFinalUserInput() {
  let finalInput = `核心想法: ${userInput.value}\n\n`;
  const additionalDetails = dynamicInputs.value
    .flatMap((group) => group.inputs)
    .filter((input) => input.value && input.value.trim() !== "")
    .map((input) => `關於“${input.label}”的補充信息:\n${input.value}`)
    .join("\n\n");

  if (additionalDetails) {
    finalInput += `--- 詳細補充信息 ---\n${additionalDetails}`;
  }
  return finalInput;
}

async function handleGeneratePlan() {
  const fullUserInput = buildFinalUserInput();

  if (!selectedTemplateId.value || !fullUserInput.trim()) {
    errorNotification("請選擇完整的主題、模板，並輸入您的核心項目描述。");
    return;
  }

  isGenerating.value = true;
  planContent.value = {}; // 清空舊的生成結果

  try {
    // 準備請求體
    const sectionsToGenerate = currentSections.value.map((s) => ({
      section_id: s.id,
    }));

    const payload = {
      user_id: "dba4dabc-a24d-4e1a-aa2b-b239d06a8cf5",
      grant: selectedGrantId.value,
      template: selectedTemplateId.value,
      sections: sectionsToGenerate,
      user_input: fullUserInput,
    };

    const response = await fetch(`${API_BASE_URL}/generate_plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorDetail = await response.text();
      throw new Error(`伺服器錯誤 (${response.status}): ${errorDetail}`);
    }

    const rawData = await response.json();
    console.log(rawData);

    const processedContent = {};
    for (const sectionId in rawData) {
      const sectionResult = rawData[sectionId];
      if (sectionResult.content && !sectionResult.error) {
        processedContent[sectionId] = {
          content: sectionResult.raw_json_content,
        };
      } else {
        processedContent[sectionId] = { error: sectionResult.error };
      }
    }
    planContent.value = processedContent;
  } catch (error) {
    console.error("生成計劃書時發生錯誤:", error);
    errorNotification(`生成失敗: ${error.message}`);
    // 可以選擇在特定 section 顯示錯誤信息
    const firstSectionId = currentSections.value[0]?.id;
    if (firstSectionId) {
      planContent.value[firstSectionId] = {
        error: `生成失敗: ${error.message}`,
      };
    }
  } finally {
    isGenerating.value = false;
  }
}
async function handleSave() {
  if (Object.keys(planContent.value).length === 0) {
    errorNotification("沒有可保存的數據。");
    return;
  }
  isSaving.value = true;
  try {
    const entries = currentSections.value
      .map((section) => {
        const content = planContent.value[section.id]?.content;
        // 確保 content 是有效的對象
        if (typeof content !== "object" || content === null) {
          console.warn(
            `Skipping section ${section.id} due to invalid content.`
          );
          return null;
        }
        return {
          source_type:
            mode.value === "golden" ? "golden_samples" : "synthetic_data",
          grant_id: selectedGrantId.value,
          template_id: selectedTemplateId.value,
          section_id: section.id,
          prompt: userInput.value,
          final_answer: content,
        };
      })
      .filter(Boolean);

    if (entries.length === 0) {
      errorNotification(
        "沒有有效的數據可以保存，請確保所有章節都有正確的 JSON 內容。"
      );
      isSaving.value = false;
      return;
    }

    const response = await fetch(`${API_BASE_URL}/datasets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entries }),
    });

    if (response.status !== 202) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to save dataset.");
    }

    success("數據集已成功提交保存！");
    // 可選：清空表單
    userInput.value = "";
    planContent.value = {};
  } catch (error) {
    console.error("Save error:", error);
    errorNotification(`保存失敗: ${error.message}`);
  } finally {
    isSaving.value = false;
  }
}

watch(availableTemplates, (newTemplates) => {
  // 检查新模板列表是否只有一个选项，并且当前没有模板被选中
  if (newTemplates && newTemplates.length === 1 && !selectedTemplateId.value) {
    // 自动选中这唯一的一个模板
    selectedTemplateId.value = newTemplates[0].id;
    console.log(`自动选中了唯一的模板: ${newTemplates[0].name}`);
  }
});

function handleAutoFill(filledContent) {
  // 這裡我們不直接賦值，而是合併，以防萬一 API 沒有返回所有 section
  const newPlanContent = { ...planContent.value };

  for (const sectionId in filledContent) {
    if (Object.hasOwnProperty.call(filledContent, sectionId)) {
      newPlanContent[sectionId] = filledContent[sectionId];
    }
  }

  planContent.value = newPlanContent;
}
</script>
