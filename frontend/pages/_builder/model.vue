<template>
  <div class="py-6 px-2 sm:px-4 md:py-10 md:px-8">
    <div
      class="w-full max-w-4xl mx-auto bg-white shadow-xl rounded-2xl p-4 sm:p-6 md:p-8"
    >
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <div>
          <h1 class="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">
            模型配置中心
          </h1>
          <p class="text-gray-500">
            為不同的計劃書章節分配最適合的 AI 模型。
          </p>
        </div>
        <button
          @click="refreshConfigurations"
          :disabled="isRefreshing"
          class="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-400 transition flex items-center gap-2 whitespace-nowrap"
        >
          <svg
            v-if="!isRefreshing"
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 1119.778 6.897 1 1 0 11-1.992-.316A5.002 5.002 0 005.099 5.99H7a1 1 0 110 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.901 14.1H13a1 1 0 110-2h3a1 1 0 011 1v2.101a1 1 0 11-2 0v-2.101a7.002 7.002 0 11-19.778-6.897 1 1 0 111.992.316A5.002 5.002 0 0014.901 5.9H13a1 1 0 110-2h3a1 1 0 011 1v2.101a1 1 0 11-2 0V5.99a7.002 7.002 0 01-12.893 5.067z"
              clip-rule="evenodd"
            />
          </svg>
          <svg
            v-else
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 animate-spin"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ isRefreshing ? "刷新中..." : "刷新配置" }}
        </button>
      </div>

      <!-- 選擇器 -->
      <div class="grid grid-cols-1 gap-4 sm:gap-6 mb-8 sm:mb-10 md:grid-cols-2">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >1. 選擇主題</label
          >
          <select
            v-model="selectedGrantId"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition"
          >
            <option disabled value="">請選擇</option>
            <option
              v-for="grant in allConfigs"
              :key="grant.id"
              :value="grant.id"
            >
              {{ grant.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >2. 選擇模板</label
          >
          <select
            v-model="selectedTemplateId"
            :disabled="!selectedGrantId"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition disabled:bg-gray-100"
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

      <!-- 章節列表 -->
      <div v-if="selectedTemplateId" class="space-y-3 sm:space-y-4">
        <h2
          class="text-lg sm:text-xl font-semibold text-gray-700 border-b pb-2 mb-3 sm:mb-4"
        >
          章節模型配置
        </h2>
        <div
          v-for="section in currentSections"
          :key="section.id"
          class="p-3 sm:p-4 border rounded-lg flex flex-col sm:flex-row justify-between items-start sm:items-center bg-gray-50 hover:shadow-md transition-shadow"
        >
          <p class="font-medium text-gray-800 mb-2 sm:mb-0">
            {{ section.name }}
          </p>
          <div
            class="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4 w-full sm:w-auto"
          >
            <div class="text-left sm:text-right">
              <span class="text-sm font-semibold text-indigo-700">{{
                getAppliedModelForSection(section.id)?.display_name || "未指定"
              }}</span>
              <p class="text-xs text-gray-500">
                <!-- {{
                  getAppliedRuleForSection(section.id)?.description ||
                  "使用全局默認"
                }} -->
                {{
                  getAppliedModelForSection(section.id)?.description || "未指定"
                }}
              </p>
            </div>
            <button
              @click="openModal(section)"
              class="bg-indigo-100 text-indigo-700 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-200"
            >
              配置
            </button>
          </div>
        </div>
      </div>
      <div
        v-else-if="selectedGrantId"
        class="text-center py-8 sm:py-12 text-gray-500"
      >
        請選擇一個模板以查看其章節。
      </div>
    </div>

    <!-- 模態框組件 -->
    <ModelSelectorCard
      v-if="isModalOpen && selectedSection"
      :section="selectedSection"
      :models="allModels"
      :template-id="selectedTemplateId"
      :grant-id="selectedGrantId"
      :current-rule="getAppliedRuleForSection(selectedSection.id)"
      @close="closeModal"
      @save="handleSaveRule"
      @settings-updated="handleSettingsUpdated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import ModelSelectorCard from "~/components/ModelSelectorCard.vue";
import { useNotifications } from "~/composables/useNotifications";

// SEO 配置
useHead({
  title: "模型配置中心 - AI 計畫書平台",
  meta: [
    {
      name: "description",
      content: "為計畫書不同章節配置最適合的 AI 模型。提供靈活的路由規則和模型選擇。",
    },
    {
      name: "keywords",
      content: "模型配置,AI 模型,路由規則,計畫書",
    },
    {
      property: "og:title",
      content: "模型配置中心 - AI 計畫書平台",
    },
    {
      property: "og:description",
      content: "為計畫書不同章節配置最適合的 AI 模型。提供靈活的路由規則和模型選擇。",
    },
  ],
});

const { success, error: errorNotification } = useNotifications();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const allConfigs = ref([]);
const allModels = ref([]);
const routingRules = ref([]);
const selectedGrantId = ref("");
const selectedTemplateId = ref("");
const selectedSection = ref(null);
const isModalOpen = ref(false);
const isRefreshing = ref(false);

// --- Computed Properties ---
const availableTemplates = computed(() => {
  if (!selectedGrantId.value) return [];
  const selectedGrant = allConfigs.value.find(
    (g) => g.id === selectedGrantId.value
  );
  return selectedGrant ? selectedGrant.templates : [];
});

const currentSections = computed(() => {
  if (!selectedTemplateId.value) return [];
  const template = availableTemplates.value.find(
    (t) => t.id === selectedTemplateId.value
  );
  return template ? template.sections : [];
});

// --- API Calls ---
async function fetchData() {
  try {
    const [configsRes, modelsRes, rulesRes] = await Promise.all([
      fetch(`${API_BASE_URL}/config`),
      fetch(`${API_BASE_URL}/models`),
      fetch(`${API_BASE_URL}/routing-rules`),
    ]);

    if (!configsRes.ok || !modelsRes.ok || !rulesRes.ok) {
      throw new Error("Failed to fetch initial data");
    }

    allConfigs.value = await configsRes.json();
    allModels.value = await modelsRes.json();
    routingRules.value = await rulesRes.json();
  } catch (error) {
    console.error("Data fetching error:", error);
    errorNotification("無法加載配置數據，請檢查後端服務。");
  }
}

onMounted(fetchData);

// --- Refresh Configuration ---
async function refreshConfigurations() {
  isRefreshing.value = true;
  try {
    const response = await fetch(`${API_BASE_URL}/config/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to refresh configurations");
    }

    // 重新加載所有數據
    await fetchData();
    success("配置已成功刷新！");
  } catch (error) {
    console.error("Failed to refresh configurations:", error);
    errorNotification(`刷新失敗: ${error.message}`);
  } finally {
    isRefreshing.value = false;
  }
}

// --- Logic & Methods ---
function getAppliedRuleForSection(sectionId) {
  // 規則已按優先級排序，第一個匹配的就是最高優先級的規則
  // 1. 查找完全匹配 section_id 的規則
  const specificRule = routingRules.value.find(
    (r) => r.section_id === sectionId
  );
  if (specificRule) return specificRule;

  // 2. 如果沒有，查找 grant_id 匹配且 section_id 為空的規則
  const grantRule = routingRules.value.find(
    (r) => r.grant_id === selectedGrantId.value && !r.section_id
  );
  if (grantRule) return grantRule;

  // 3. 如果再沒有，查找全局規則 (grant_id 和 section_id 都為空)
  const globalRule = routingRules.value.find(
    (r) => !r.grant_id && !r.section_id
  );
  return globalRule || null;
}

function getAppliedModelForSection(sectionId) {
  const rule = getAppliedRuleForSection(sectionId);
  if (!rule) return null;
  return allModels.value.find((m) => m.id === rule.model_id) || null;
}

function openModal(section) {
  selectedSection.value = section;
  isModalOpen.value = true;
}

function closeModal() {
  isModalOpen.value = false;
  selectedSection.value = null;
}

async function handleSaveRule(rulePayload) {
  try {
    const response = await fetch(`${API_BASE_URL}/routing-rules`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(rulePayload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to save rule");
    }

    // 更新 UI
    const rulesRes = await fetch(`${API_BASE_URL}/routing-rules`);
    routingRules.value = await rulesRes.json();

    closeModal();
    success("規則已成功儲存！");
  } catch (error) {
    console.error("Failed to save routing rule:", error);
    errorNotification(`儲存失敗: ${error.message}`);
  }
}

function handleSettingsUpdated(payload) {
  // 在本地數據中找到並更新對應的 section
  const grant = allConfigs.value.find((g) => g.id === selectedGrantId.value);
  if (grant) {
    const template = grant.templates.find(
      (t) => t.id === selectedTemplateId.value
    );
    if (template) {
      const section = template.sections.find((s) => s.id === payload.sectionId);
      if (section) {
        section.system_prompt = payload.system_prompt;
        section.custom_prompt_list = payload.custom_prompt_list;
      }
    }
  }
}

watch(availableTemplates, (newTemplates) => {
  if (newTemplates && newTemplates.length === 1 && !selectedTemplateId.value) {
    selectedTemplateId.value = newTemplates[0].id;
  }
});
</script>
