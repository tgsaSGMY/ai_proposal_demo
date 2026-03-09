<template>
  <ClientOnly>
    <div class="py-6 px-2 sm:px-4 md:py-10 md:px-8">
      <div
        class="w-full max-w-4xl mx-auto bg-white shadow-xl rounded-2xl p-4 sm:p-6 md:p-8"
      >
        <div
          class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4"
        >
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
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            {{ isRefreshing ? "刷新中..." : "刷新配置" }}
          </button>
        </div>

        <!-- 全局模型配置 -->
        <div
          v-if="selectedTemplateId"
          class="mb-8 sm:mb-10 p-4 sm:p-6 border-2 border-indigo-200 bg-indigo-50 rounded-lg"
        >
          <h2
            class="text-lg sm:text-xl font-semibold text-gray-700 mb-4 flex items-center gap-2"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-6 w-6 text-indigo-600"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM15.657 14.243a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM11 17a1 1 0 102 0v-1a1 1 0 10-2 0v1zM5.757 15.657a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM2 10a1 1 0 011-1h1a1 1 0 110 2H3a1 1 0 01-1-1zM5.757 4.343a1 1 0 00-1.414 1.414l.707.707a1 1 0 101.414-1.414l-.707-.707z"
              />
            </svg>
            全局模型配置
          </h2>
          <p class="text-sm text-gray-600 mb-4">
            設定所有章節的默認模型。特定章節的配置將覆蓋此設定。
          </p>

          <div class="grid grid-cols-1 gap-4 sm:gap-6 md:grid-cols-2 mb-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                全局外部模型
              </label>
              <select
                v-model="globalExternalModelId"
                class="w-full rounded-lg border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition"
              >
                <option value="">未指定（外部）</option>
                <option
                  v-for="model in allModels"
                  :key="model.id"
                  :value="model.id"
                >
                  {{ model.display_name }}
                </option>
              </select>
              <p class="text-xs text-gray-500 mt-1">
                當前：{{ getGlobalModel(true)?.display_name || "未指定" }}
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                全局內部模型
              </label>
              <select
                v-model="globalInternalModelId"
                class="w-full rounded-lg border border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition"
              >
                <option value="">未指定（內部）</option>
                <option
                  v-for="model in allModels"
                  :key="model.id"
                  :value="model.id"
                >
                  {{ model.display_name }}
                </option>
              </select>
              <p class="text-xs text-gray-500 mt-1">
                當前：{{ getGlobalModel(false)?.display_name || "未指定" }}
              </p>
            </div>
          </div>

          <button
            @click="saveGlobalModels"
            :disabled="isSavingGlobal"
            class="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-400 transition flex items-center justify-center gap-2"
          >
            <svg
              v-if="!isSavingGlobal"
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                d="M19.414 3.172a2 2 0 00-2.828 0l-12 12a2 2 0 102.828 2.828l12-12a2 2 0 000-2.828z"
              />
              <path
                fill-rule="evenodd"
                d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"
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
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            {{ isSavingGlobal ? "保存中..." : "保存全局配置" }}
          </button>
        </div>

        <!-- 選擇器 -->
        <div
          class="grid grid-cols-1 gap-4 sm:gap-6 mb-8 sm:mb-10 md:grid-cols-2"
        >
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
                <span class="text-sm font-semibold text-indigo-700"
                  >外部模型：{{
                    getAppliedModelForSection(section.id, true)?.display_name ||
                    "未指定 (外部)"
                  }}</span
                >
                <p class="text-xs text-gray-500">
                  内部模型：{{
                    getAppliedModelForSection(section.id, false)
                      ?.display_name || "未指定"
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
        :current-internal-rule="
          getAppliedRuleForSection(selectedSection.id, false)
        "
        :current-external-rule="
          getAppliedRuleForSection(selectedSection.id, true)
        "
        :routing-rules="routingRules"
        @close="closeModal"
        @save="handleSaveRule"
        @delete="handleDeleteRule"
        @settings-updated="handleSettingsUpdated"
      />
    </div>
  </ClientOnly>
</template>

<script setup>
// ===== 页面元数据 =====
// 设置中间件验证，确保用户已登陆
definePageMeta({
  middleware: "auth",
});

// ===== 导入依赖库 =====
// 导入 Vue 核心库
import { ref, onMounted, computed, watch } from "vue";
// 导入子组件和服务
import ModelSelectorCard from "~/components/ModelSelectorCard.vue";
import { useNotifications } from "~/composables/useNotifications";

// ===== SEO 配置 =====
// 设置页面标题和元数据，用于搜索引擎优化
useHead({
  title: "模型配置中心 - TGSA 補助引擎",
  meta: [
    {
      name: "description",
      content:
        "為計畫書不同章節配置最適合的 AI 模型。提供靈活的路由規則和模型選擇。",
    },
    {
      name: "keywords",
      content: "模型配置,AI 模型,路由規則,計畫書",
    },
    {
      property: "og:title",
      content: "模型配置中心 - TGSA 補助引擎",
    },
    {
      property: "og:description",
      content:
        "為計畫書不同章節配置最適合的 AI 模型。提供靈活的路由規則和模型選擇。",
    },
  ],
});

// ===== 初始化服务 =====
// 获取通知服务和配置信息
const { success, error: errorNotification } = useNotifications();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

// ===== 生命周期钩子 =====
// 页面挂载时检查用户是否为内部人员
onMounted(async () => {
  const { checkIsInternal } = useInternalCheck();

  // 執行檢查
  const isInternal = await checkIsInternal();

  if (!isInternal) {
    // 如果不是內部人員，重定向到外部版本頁面
    window.location.href = "/";
  }
});

// ===== 数据状态 =====
// 存储所有配置、模型、路由规则及用户选择
const allConfigs = ref([]);
const allModels = ref([]);
const routingRules = ref([]);
const selectedGrantId = ref("");
const selectedTemplateId = ref("");
const selectedSection = ref(null);
const isModalOpen = ref(false);
const isRefreshing = ref(false);
const isSavingGlobal = ref(false);
const globalExternalModelId = ref("");
const globalInternalModelId = ref("");
const savedGlobalExternalModelId = ref("");
const savedGlobalInternalModelId = ref("");

// ===== 计算属性：可用模板 =====
// 根据选中的补助类别，动态计算可用的模板列表
const availableTemplates = computed(() => {
  if (!selectedGrantId.value) return [];
  const selectedGrant = allConfigs.value.find(
    (g) => g.id === selectedGrantId.value,
  );
  return selectedGrant ? selectedGrant.templates : [];
});

// ===== 计算属性：当前章节列表 =====
// 根据选中的模板，动态计算对应的章节列表
const currentSections = computed(() => {
  if (!selectedTemplateId.value) return [];
  const template = availableTemplates.value.find(
    (t) => t.id === selectedTemplateId.value,
  );
  return template ? template.sections : [];
});

// ===== API 调用 =====
// 从后端获取初始数据：配置、模型和路由规则
async function fetchData() {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("請先登入");
    const [configsRes, modelsRes, rulesRes] = await Promise.all([
      fetch(`${API_BASE_URL}/config`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
      }),
      fetch(`${API_BASE_URL}/models`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
      }),
      fetch(`${API_BASE_URL}/routing-rules`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
      }),
    ]);

    if (!configsRes.ok || !modelsRes.ok || !rulesRes.ok) {
      throw new Error("Failed to fetch initial data");
    }

    allConfigs.value = await configsRes.json();
    allModels.value = await modelsRes.json();
    routingRules.value = await rulesRes.json();
    selectedGrantId.value = "marketing";
    selectedTemplateId.value = "siir";
  } catch (error) {
    console.error("Data fetching error:", error);
    errorNotification("無法加載配置數據，請檢查後端服務。");
  }

  // 初始化全局模型
  initializeGlobalModels();
}

// ===== 初始化全局模型 =====
// 从路由规则中加载全局模型设置
function initializeGlobalModels() {
  const externalGlobalRule = routingRules.value.find(
    (r) => !r.grant_id && !r.section_id && r.is_external === true,
  );
  const internalGlobalRule = routingRules.value.find(
    (r) => !r.grant_id && !r.section_id && r.is_external === false,
  );

  globalExternalModelId.value = externalGlobalRule?.model_id || "";
  globalInternalModelId.value = internalGlobalRule?.model_id || "";
  savedGlobalExternalModelId.value = externalGlobalRule?.model_id || "";
  savedGlobalInternalModelId.value = internalGlobalRule?.model_id || "";
}

onMounted(fetchData);

// ===== 刷新配置 =====
// 调用 API 刷新所有配置数据，获取最新的模板和模型列表
async function refreshConfigurations() {
  isRefreshing.value = true;
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("請先登入");
    const response = await fetch(`${API_BASE_URL}/config/refresh`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
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

// ===== 计算属性：默认模型 ID =====
// 通过优先级系统查找默认应用的模型 ID
const defaultModelId = computed(() => {
  // 通過優先級系統查找默認應用的模型 ID
  const globalRule = routingRules.value.find(
    (r) => !r.grant_id && !r.section_id,
  );
  return globalRule ? globalRule.model_id : null;
});

// ===== 获取章节的应用规则 =====
// 根据 section ID 和模型类型（内部/外部），获取应用的路由规则
// 优先级：完全匹配 > 全局规则
function getAppliedRuleForSection(sectionId, isExternal) {
  // 先按 isExternal 過濾，再按 priority 排序
  // 1. 查找完全匹配 section_id 和 is_external 的規則
  const specificRule = routingRules.value.find(
    (r) =>
      r.section_id === sectionId &&
      r.is_external === isExternal &&
      r.template_id === selectedTemplateId.value &&
      r.grant_id === selectedGrantId.value,
  );
  if (specificRule) return specificRule;

  // 3. 如果再沒有，查找全局規則 (grant_id 和 section_id 都為空) 且 is_external 匹配
  const globalRule = routingRules.value.find(
    (r) => !r.grant_id && !r.section_id && r.is_external === isExternal,
  );

  return globalRule || null;
}

// ===== 获取章节的应用模型 =====
// 根据规则查找对应的模型对象
function getAppliedModelForSection(sectionId, isExternal) {
  const rule = getAppliedRuleForSection(sectionId, isExternal);
  if (!rule) return null;
  return allModels.value.find((m) => m.id === rule.model_id) || null;
}

// ===== 打开模态框 =====
// 打开指定章节的模型配置模态框
function openModal(section) {
  selectedSection.value = section;
  isModalOpen.value = true;
}

// ===== 关闭模态框 =====
// 关闭模型配置模态框
function closeModal() {
  isModalOpen.value = false;
  selectedSection.value = null;
}

// ===== 保存路由规则 =====
// 调用 API 保存新的路由规则配置
async function handleSaveRule(rulePayload) {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("請先登入");
    const response = await fetch(`${API_BASE_URL}/routing-rules`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(rulePayload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to save rule");
    }

    // 更新 UI
    const rulesRes = await fetch(`${API_BASE_URL}/routing-rules`, {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });
    routingRules.value = await rulesRes.json();
    success("規則已成功儲存！");
    closeModal();
  } catch (error) {
    console.error("Failed to save routing rule:", error);
    errorNotification(`儲存失敗: ${error.message}`);
  }
}

// ===== 删除路由规则 =====
// 调用 API 删除指定的路由规则
async function handleDeleteRule(ruleId) {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("請先登入");
    const response = await fetch(`${API_BASE_URL}/routing-rules/${ruleId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to delete rule");
    }

    // 更新 UI
    const rulesRes = await fetch(`${API_BASE_URL}/routing-rules`, {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });
    routingRules.value = await rulesRes.json();

    closeModal();
    success("已移除自訂配置，將使用默認模型！");
  } catch (error) {
    console.error("Failed to delete routing rule:", error);
    errorNotification(`刪除失敗: ${error.message}`);
  }
}

// ===== 设置更新处理 =====
// 处理章节设置的更新（系统提示、自定义提示等）
function handleSettingsUpdated(payload) {
  // 在本地數據中找到並更新對應的 section
  const grant = allConfigs.value.find((g) => g.id === selectedGrantId.value);
  if (grant) {
    const template = grant.templates.find(
      (t) => t.id === selectedTemplateId.value,
    );
    if (template) {
      const section = template.sections.find((s) => s.id === payload.sectionId);
      if (section) {
        section.system_prompt = payload.system_prompt;
        section.custom_prompt_list = payload.custom_prompt_list;
        if (typeof payload.search_external === "boolean") {
          section.search_external = payload.search_external;
        }
      }
    }
  }
}

// ===== 获取全局模型 =====
// 根据类型（内部/外部）获取应用的全局模型对象（已保存的值）
function getGlobalModel(isExternal) {
  const modelId = isExternal
    ? savedGlobalExternalModelId.value
    : savedGlobalInternalModelId.value;
  if (!modelId) return null;
  return allModels.value.find((m) => m.id === modelId) || null;
}

// ===== 保存全局模型配置 =====
// 调用 API 保存全局模型配置
async function saveGlobalModels() {
  isSavingGlobal.value = true;
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("請先登入");

    // 删除现有的全局规则
    const existingGlobalRules = routingRules.value.filter(
      (r) => !r.grant_id && !r.section_id,
    );

    for (const rule of existingGlobalRules) {
      const deleteRes = await fetch(
        `${API_BASE_URL}/routing-rules/${rule.id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            "Content-Type": "application/json",
          },
        },
      );
      if (!deleteRes.ok) {
        throw new Error("Failed to delete existing global rules");
      }
    }

    // 保存新的全局规则
    const rulesToCreate = [];

    if (globalExternalModelId.value) {
      rulesToCreate.push({
        model_id: globalExternalModelId.value,
        is_external: true,
        priority: 10,
      });
    }

    if (globalInternalModelId.value) {
      rulesToCreate.push({
        model_id: globalInternalModelId.value,
        is_external: false,
        priority: 10,
      });
    }

    for (const rule of rulesToCreate) {
      const saveRes = await fetch(`${API_BASE_URL}/routing-rules`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(rule),
      });

      if (!saveRes.ok) {
        const errorData = await saveRes.json();
        throw new Error(errorData.detail || "Failed to save global rule");
      }
    }

    // 重新加载路由规则
    const rulesRes = await fetch(`${API_BASE_URL}/routing-rules`, {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });
    routingRules.value = await rulesRes.json();

    // 更新已保存的全局模型值
    savedGlobalExternalModelId.value = globalExternalModelId.value;
    savedGlobalInternalModelId.value = globalInternalModelId.value;

    success("全局配置已成功儲存！");
  } catch (error) {
    console.error("Failed to save global models:", error);
    errorNotification(`儲存失敗: ${error.message}`);
  } finally {
    isSavingGlobal.value = false;
  }
}

// ===== 侦听器：模板列表变化 =====
// 当可用模板列表变化时，自动选择第一个模板
watch(availableTemplates, (newTemplates) => {
  if (newTemplates) {
    selectedTemplateId.value = newTemplates[0].id;
  }
});
</script>
