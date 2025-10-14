<template>
  <div class="p-4 md:p-8 h-full flex flex-col bg-gray-50">
    <div class="flex-shrink-0 mb-6 bg-white p-4 rounded-lg shadow text-center">
      <h1 class="text-2xl font-bold text-gray-800">AI 計畫書生成器</h1>
      <p class="text-sm text-gray-500 mt-1">專為高效產出專業計劃書而設計</p>
    </div>

    <!-- 主工作區：左右佈局 -->
    <div class="flex-grow grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0">
      <!-- 左側：輸入面板 -->
      <PlanInputPanel
        :all-configs="allConfigs"
        v-model:userInput="userInput"
        :dynamic-inputs="dynamicInputs"
        @update:dynamic-inputs="(newVal) => (dynamicInputs = newVal)"
        :is-generating="isLoading"
        :mode="'generator'"
        @selectionChange="onSelectionChange"
        @generatePlan="handleGeneratePlan"
      />

      <!-- 右側：輸出面板 -->
      <!-- 使用 v-if 確保在生成前不顯示空的輸出面板 -->
      <div v-if="Object.keys(planContent).length > 0 || isLoading">
        <PlanOutputPanel
          :plan-content="planContent"
          :sections="currentSections"
          :mode="'generator'"
          :is-loading="isLoading"
        />
      </div>
      <!-- 初始狀態下的提示信息 -->
      <div
        v-else
        class="bg-white shadow-xl rounded-2xl p-8 h-full flex flex-col items-center justify-center text-center"
      >
        <svg
          class="h-16 w-16 text-indigo-200"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.5"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-700">準備開始創作</h3>
        <p class="mt-1 text-sm text-gray-500">
          請在左側面板填寫您的專案想法，點擊生成後，結果將會顯示於此。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watchEffect } from "vue";
import PlanInputPanel from "~/components/PlanInputPanel.vue";
import PlanOutputPanel from "~/components/PlanOutputPanel.vue";
import { useLoading } from "~/composables/useLoading";
import { useNotifications } from "~/composables/useNotifications";

// --- 全局狀態 ---
const { isLoading, show: showLoading, hide: hideLoading } = useLoading();
const { success, error: errorNotification } = useNotifications();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

// --- 本地狀態 ---
const allConfigs = ref([]);
const userInput = ref("");
const planContent = ref({}); // { section_id: { content: "...", error: "..." } }
const selectedGrantId = ref("");
const selectedTemplateId = ref("");
const dynamicInputs = ref([]);

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

// --- Lifecycle & Data Fetching ---
onMounted(async () => {
  try {
    console.log(API_BASE_URL);
    const response = await fetch(`${API_BASE_URL}/config`);

    if (!response.ok) throw new Error("Network response was not ok");
    allConfigs.value = await response.json();
  } catch (error) {
    console.error("Failed to load config:", error);
    errorNotification("無法加載應用配置，請檢查後端服務是否運行。");
  }
});

// 使用 watchEffect 自動處理動態輸入框的生成
watchEffect(() => {
  const sections = currentSections.value;
  if (!sections || sections.length === 0) {
    dynamicInputs.value = [];
    return;
  }
  const groupedInputs = [];
  sections.forEach((section) => {
    const sectionInputs = [];
    if (section.json_schema && section.json_schema.properties) {
      Object.entries(section.json_schema.properties).forEach(([key, prop]) => {
        sectionInputs.push({
          id: `${section.id}-${key}`,
          label: prop.description || key.replace("_", " "),
          value: "",
        });
      });
    }
    if (sectionInputs.length > 0) {
      groupedInputs.push({
        sectionId: section.id,
        sectionName: section.name,
        inputs: sectionInputs,
        custom_prompt_list: section.custom_prompt_list || [],
        system_prompt: section.system_prompt || "",
      });
    }
  });
  dynamicInputs.value = groupedInputs;
});

// --- Event Handlers ---
function onSelectionChange(selection) {
  selectedGrantId.value = selection.grantId;
  selectedTemplateId.value = selection.templateId;
  planContent.value = {}; // 重置輸出
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
  if (!selectedTemplateId.value || !userInput.value.trim()) {
    errorNotification("請選擇主題、模板，並描述您的核心想法。");
    return;
  }
  showLoading();
  planContent.value = {};
  const finalUserInput = buildFinalUserInput();

  try {
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
      }),
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

    try {
      console.log("開始將生成結果異步保存到數據集...");

      // 準備要保存的數據條目
      const entriesToSave = currentSections.value
        .map((section) => {
          const sectionResult = rawData[section.id];

          // 確保該章節成功生成且有內容
          if (sectionResult && sectionResult.content && !sectionResult.error) {
            return {
              source_type: "external_direct",
              grant_id: selectedGrantId.value,
              template_id: selectedTemplateId.value,
              section_id: section.id,
              prompt: finalUserInput,
              final_answer: sectionResult.raw_json_content,
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
        })
          .then((saveResponse) => {
            if (saveResponse.status === 202) {
              console.log("數據集保存請求已成功提交到後台。");
            } else {
              // 即使保存失敗，也只在控制台記錄錯誤，不打擾用戶
              saveResponse
                .json()
                .then((err) => console.error("後台保存數據集失敗:", err));
            }
          })
          .catch((saveError) => {
            console.error("發送保存數據集請求時出錯:", saveError);
          });
      }
    } catch (saveError) {
      // 捕獲準備數據時的錯誤，同樣只在控制台記錄
      console.error("準備保存數據集時出錯:", saveError);
    }

    success("計劃書草稿已生成！");
  } catch (error) {
    console.error("生成計劃書時發生錯誤:", error);
    errorNotification(`生成失敗: ${error.message}`);
  } finally {
    hideLoading();
  }
}
</script>
