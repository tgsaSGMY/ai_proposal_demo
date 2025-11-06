<template>
  <div class="p-3 sm:p-4 md:p-8 h-full flex flex-col bg-gray-50">
    <div
      class="flex-shrink-0 mb-4 sm:mb-6 bg-white p-3 sm:p-4 rounded-lg shadow"
    >
      <div class="text-center mb-4">
        <h1 class="text-xl sm:text-2xl font-bold text-gray-800">
          AI 計畫書生成器
        </h1>
        <p class="text-xs sm:text-sm text-gray-500 mt-1">
          專為高效產出專業計劃書而設計
        </p>
      </div>

      <!-- 模型類型選擇 Toggle -->
      <div class="flex justify-center items-center gap-3">
        <span
          class="text-xs sm:text-sm font-medium"
          :class="
            useModelType === 'internal' ? 'text-indigo-600' : 'text-gray-600'
          "
        >
          內部模型
        </span>
        <button
          @click="
            useModelType = useModelType === 'internal' ? 'external' : 'internal'
          "
          :class="[
            'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
            useModelType === 'external' ? 'bg-indigo-600' : 'bg-gray-300',
          ]"
        >
          <span
            :class="[
              'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
              useModelType === 'external' ? 'translate-x-6' : 'translate-x-1',
            ]"
          />
        </button>
        <span
          class="text-xs sm:text-sm font-medium"
          :class="
            useModelType === 'external' ? 'text-indigo-600' : 'text-gray-600'
          "
        >
          外部模型
        </span>
      </div>
    </div>

    <!-- 主工作區：左右佈局 -->
    <div
      class="flex-grow grid grid-cols-1 gap-4 sm:gap-6 min-h-0 md:grid-cols-2"
    >
      <!-- 左側：輸入面板 -->
      <PlanInputPanel
        :all-configs="allConfigs"
        v-model="userInput"
        v-model:dynamic-values="dynamicFieldValues"
        :initial-template-id="selectedTemplateId"
        :is-generating="isLoading"
        :mode="'generator'"
        @selectionChange="onSelectionChange"
        @generatePlan="handleGeneratePlan"
      />

      <!-- 右側：輸出面板 -->
      <div v-if="Object.keys(planContent).length > 0 || isLoading">
        <PlanOutputPanel
          :plan-content="planContent"
          :sections="currentSections"
          :mode="'generator'"
          :is-loading="isLoading"
          :grant-id="selectedGrantId"
          :template-id="selectedTemplateId"
        />
      </div>
      <!-- 初始狀態下的提示信息 -->
      <div
        v-else
        class="bg-white shadow-xl rounded-2xl p-4 sm:p-8 h-full flex flex-col items-center justify-center text-center"
      >
        <svg
          class="h-12 w-12 sm:h-16 sm:w-16 text-indigo-200"
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
        <h3 class="mt-3 sm:mt-4 text-base sm:text-lg font-medium text-gray-700">
          準備開始創作
        </h3>
        <p class="mt-1 text-xs sm:text-sm text-gray-500">
          請在左側面板填寫您的專案想法，點擊生成後，結果將會顯示於此。
        </p>
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
import { usePlanGenerator } from "~/composables/usePlanGenerator"; // 引入 Composable
import PlanInputPanel from "~/components/PlanInputPanel.vue";
import PlanOutputPanel from "~/components/PlanOutputPanel.vue";
import PlanCandidateSelector from "~/components/PlanCandidateSelector.vue";
import { useLoading } from "~/composables/useLoading";
import { useNotifications } from "~/composables/useNotifications";

// SEO 配置
useHead({
  title: "AI 計畫書生成器 - 專業提案一鍵生成",
  meta: [
    {
      name: "description",
      content:
        "使用 AI 技術快速生成專業計畫書。支持多種主題和模板，提高提案效率。",
    },
    {
      name: "keywords",
      content: "計畫書,AI 生成,提案,企劃書,自動化",
    },
    {
      property: "og:title",
      content: "AI 計畫書生成器 - 專業提案一鍵生成",
    },
    {
      property: "og:description",
      content:
        "使用 AI 技術快速生成專業計畫書。支持多種主題和模板，提高提案效率。",
    },
    {
      property: "og:type",
      content: "website",
    },
  ],
});

const { isLoading, show: showLoading, hide: hideLoading } = useLoading();
const { success, error: errorNotification } = useNotifications();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

// 模型類型選擇狀態
const useModelType = ref("external");

// --- 使用 Composable ---
const {
  selectedGrantId,
  selectedTemplateId,
  userInput,
  dynamicFieldValues,
  planContent,
  currentSections,
  allConfigs,
  buildFinalUserInput,
  onSelectionChange,
} = usePlanGenerator();

const showCandidateModal = ref(false);
const candidatePlan = ref({});

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
  success("已選擇方案並填充到結果中！");
  savePreferenceData(selected, rejected);
}

async function savePreferenceData(selectedData, rejectedData) {
  try {
    const finalUserInput = buildFinalUserInput();
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
            prompt: finalUserInput,
            final_answer: chosen.content,
            rejected_answer: rejected?.content || null,
          };
        }
        return null;
      })
      .filter(Boolean);

    if (entriesToSave.length > 0) {
      // 使用 fetch 發送到 /api/datasets，不阻塞用戶 UI
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
  } catch (e) {
    console.error("準備保存偏好數據時出錯:", e);
  }
}

// --- 页面独有的方法 ---
async function handleGeneratePlan(outerPayload) {
  if (!selectedTemplateId.value || !userInput.value.trim()) {
    errorNotification("請選擇主題、模板，並描述您的核心想法。");
    return;
  }
  showLoading("正在生成計劃書...", true);
  planContent.value = {};
  candidatePlan.value = {};

  const finalUserInput = buildFinalUserInput(outerPayload?.summaries);

  try {
    const sectionsToGenerate = currentSections.value.map((s) => ({
      section_id: s.id,
    }));
    console.log("生成計劃書請求負載:", {
      user_id: "dba4dabc-a24d-4e1a-aa2b-b239d06a8cf5",
      grant: selectedGrantId.value,
      template: selectedTemplateId.value,
      sections: sectionsToGenerate,
      user_input: finalUserInput,
      num_candidates: 2,
      is_external: useModelType.value === "external",
    });

    const response = await fetch(`${API_BASE_URL}/generate_plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "dba4dabc-a24d-4e1a-aa2b-b239d06a8cf5",
        grant: selectedGrantId.value,
        template: selectedTemplateId.value,
        user_input: finalUserInput,
        num_candidates: 2,
        is_external: useModelType.value === "external",
      }),
    });

    if (!response.ok) {
      const errorDetail = await response.text();
      throw new Error(`伺服器錯誤 (${response.status}): ${errorDetail}`);
    }

    const rawData = await response.json();

    const processedCandidates = {};
    for (const sectionId in rawData) {
      const candidates = rawData[sectionId]; // candidates 现在是一个数组
      processedCandidates[sectionId] = candidates.map((candidate) => ({
        content: candidate.raw_json_content,
        error: candidate.error || null,
      }));
    }

    candidatePlan.value = processedCandidates;
    showCandidateModal.value = true; // 显示选择模态框
    success("計劃書草稿已生成！");
  } catch (error) {
    console.error("生成計劃書時發生錯誤:", error);
    errorNotification(`生成失敗: ${error.message}`);
  } finally {
    hideLoading();
  }
}
</script>
