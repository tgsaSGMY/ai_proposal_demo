<template>
  <div class="py-10 px-4">
    <div class="w-full max-w-4xl mx-auto bg-white shadow-xl rounded-2xl p-8">
      <h1 class="text-3xl font-bold text-gray-800 text-center mb-2">
        模型配置中心
      </h1>
      <p class="text-center text-gray-500 mb-8">
        為不同的計畫書章節分配最適合的 AI 模型。
      </p>

      <!-- 選擇器 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >1. 選擇主題 (Grant)</label
          >
          <select
            v-model="selectedGrantId"
            @change="selectedTemplateId = ''"
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
      <div v-if="selectedTemplateId" class="space-y-4">
        <h2 class="text-xl font-semibold text-gray-700 border-b pb-2 mb-4">
          章節模型配置
        </h2>
        <div
          v-for="section in currentSections"
          :key="section.id"
          class="p-4 border rounded-lg flex justify-between items-center bg-gray-50 hover:shadow-md transition-shadow"
        >
          <p class="font-medium text-gray-800">{{ section.name }}</p>
          <div class="flex items-center gap-4">
            <div class="text-right">
              <span class="text-sm font-semibold text-indigo-700">{{
                getAppliedModelForSection(section.id)?.display_name || "未指定"
              }}</span>
              <p class="text-xs text-gray-500">
                {{
                  getAppliedRuleForSection(section.id)?.description ||
                  "使用全局默認"
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
      <div v-else-if="selectedGrantId" class="text-center py-12 text-gray-500">
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
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import ModelSelectorCard from "~/components/ModelSelectorCard.vue";
import { useNotifications } from "~/composables/useNotifications";
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
      fetch(`${API_BASE_URL}/routing_rules`),
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

    // 成功後，重新獲取最新的路由規則以更新 UI
    const rulesRes = await fetch(`${API_BASE_URL}/routing-rules`);
    routingRules.value = await rulesRes.json();

    closeModal();
    success("規則已成功儲存！");
  } catch (error) {
    console.error("Failed to save routing rule:", error);
    errorNotification(`儲存失敗: ${error.message}`);
  }
}
</script>
