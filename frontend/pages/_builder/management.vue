<template>
  <div class="p-4 md:p-8">
    <h1 class="text-xl sm:text-2xl font-bold mb-4 sm:mb-6">數據庫管理</h1>
    <!-- Filter Section -->
    <div class="mb-6 p-4 bg-white rounded-lg shadow-md">
      <div
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 items-end"
      >
        <!-- Grant Filter -->
        <div>
          <label class="block text-sm font-medium text-gray-700">主題</label>
          <select
            v-model="filters.grantId"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="">全部</option>
            <option
              v-for="grant in allConfigs"
              :key="grant.id"
              :value="grant.id"
            >
              {{ grant.name }}
            </option>
          </select>
        </div>

        <!-- Template Filter -->
        <div>
          <label class="block text-sm font-medium text-gray-700">模板</label>
          <select
            v-model="filters.templateId"
            :disabled="!filters.grantId"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm disabled:bg-gray-50"
          >
            <option value="">全部</option>
            <option
              v-for="template in availableTemplates"
              :key="template.id"
              :value="template.id"
            >
              {{ template.name }}
            </option>
          </select>
        </div>

        <!-- Section Filter -->
        <div>
          <label class="block text-sm font-medium text-gray-700">章節</label>
          <select
            v-model="filters.sectionId"
            :disabled="!filters.templateId"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm disabled:bg-gray-50"
          >
            <option value="">全部</option>
            <option
              v-for="section in availableSections"
              :key="section.id"
              :value="section.id"
            >
              {{ section.name }}
            </option>
          </select>
        </div>

        <!-- Source Type Filter -->
        <div>
          <label class="block text-sm font-medium text-gray-700">來源</label>
          <select
            v-model="filters.sourceType"
            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="">全部</option>
            <option value="golden_samples">黃金樣本</option>
            <option value="synthetic_data">生成資料</option>
            <option value="external_direct">外部資料</option>
          </select>
        </div>

        <!-- Reset Button -->
        <button
          @click="resetFilters"
          class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 h-9"
        >
          重置篩選
        </button>
      </div>
    </div>

    <!-- Loading and Error States -->
    <div v-if="isLoading" class="text-center py-10">
      <p>正在加載數據...</p>
    </div>
    <div v-else-if="error" class="bg-red-100 text-red-700 p-4 rounded-lg">
      <p>加載失敗: {{ error }}</p>
    </div>

    <!-- Data Table -->
    <div
      v-else-if="datasets.length > 0"
      class="bg-white shadow-lg rounded-lg overflow-hidden"
    >
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              ID
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              來源
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              關聯章節
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              輸入指令
            </th>
            <th
              scope="col"
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              操作
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="item in datasets" :key="item.id">
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ item.id }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span
                :class="getSourceTypeClass(item.source_type)"
                class="px-4 py-2 inline-flex text-xs leading-5 font-semibold rounded-full"
              >
                {{ getSourceTypeName(item.source_type) }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
              <div class="flex flex-col">
                <span class="font-semibold text-gray-900">{{
                  nameMaps.sections.get(item.section_id) || item.section_id
                }}</span>
                <span class="text-xs text-gray-500 mt-1">
                  {{ nameMaps.grants.get(item.grant_id) || item.grant_id }} >
                  {{
                    nameMaps.templates.get(item.template_id) || item.template_id
                  }}
                </span>
              </div>
            </td>

            <td
              class="px-6 py-4 text-sm text-gray-600 max-w-sm truncate"
              :title="item.prompt"
            >
              {{ item.prompt }}
            </td>

            <td
              class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2"
            >
              <button
                @click="openEditModal(item)"
                class="text-indigo-600 hover:text-indigo-900"
              >
                編輯
              </button>
              <button
                @click="handleDelete(item.id)"
                class="text-red-600 hover:text-red-900"
              >
                刪除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-10 bg-white rounded-lg shadow">
      <p class="text-gray-500">數據庫中沒有任何數據。</p>
    </div>

    <!-- Edit Modal -->
    <DatasetEditModal
      :show="isModalVisible"
      :dataset="currentDataset"
      :is-saving="isSaving"
      :all-configs="allConfigs"
      @close="closeEditModal"
      @save="handleSave"
    />
  </div>
</template>

<script setup>
// SEO 配置
useHead({
  title: "數據庫管理 - AI 計畫書平台",
  meta: [
    {
      name: "description",
      content: "管理和編輯計畫書數據集。支持按主題、模板、章節過濾，批量操作數據。",
    },
    {
      name: "keywords",
      content: "數據庫,數據管理,編輯,過濾,計畫書",
    },
    {
      property: "og:title",
      content: "數據庫管理 - AI 計畫書平台",
    },
    {
      property: "og:description",
      content: "管理和編輯計畫書數據集。支持按主題、模板、章節過濾。",
    },
  ],
});

import { ref, onMounted, reactive, watch, computed } from "vue";
import DatasetEditModal from "~/components/DatasetEditModal.vue";
import { getSourceTypeClass, getSourceTypeName } from "~/utils/textMapping";

const datasets = ref([]);
import { useLoading } from "~/composables/useLoading";
import { useNotifications } from "~/composables/useNotifications";
const { isLoading } = useLoading();
const { success, error: errorNotification } = useNotifications();
import { useConfirm } from "~/composables/useConfirm";
const { confirm } = useConfirm();
const isSaving = ref(false);
const error = ref(null);
const { allConfigs } = usePlanGenerator();

const isModalVisible = ref(false);
const currentDataset = ref(null);
const filters = reactive({
  grantId: "",
  templateId: "",
  sectionId: "",
  sourceType: "",
});

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

// --- Computed properties for dependent dropdowns ---
const availableTemplates = computed(() => {
  if (!filters.grantId) return [];
  const grant = allConfigs.value.find((g) => g.id === filters.grantId);
  return grant ? grant.templates : [];
});

const availableSections = computed(() => {
  if (!filters.templateId) return [];
  const template = availableTemplates.value.find(
    (t) => t.id === filters.templateId
  );
  return template ? template.sections : [];
});

const nameMaps = computed(() => {
  const maps = {
    grants: new Map(),
    templates: new Map(),
    sections: new Map(),
  };

  if (allConfigs.value.length === 0) {
    return maps;
  }

  allConfigs.value.forEach((grant) => {
    maps.grants.set(grant.id, grant.name);
    if (grant.templates) {
      grant.templates.forEach((template) => {
        maps.templates.set(template.id, template.name);
        if (template.sections) {
          template.sections.forEach((section) => {
            maps.sections.set(section.id, section.name);
          });
        }
      });
    }
  });

  return maps;
});

// --- 創建一個輔助函數來查找名稱 ---
function getSectionDisplayName(item) {
  const grantName = nameMaps.value.grants.get(item.grant_id) || item.grant_id;
  const templateName =
    nameMaps.value.templates.get(item.template_id) || item.template_id;
  const sectionName =
    nameMaps.value.sections.get(item.section_id) || item.section_id;

  // 返回一個結構化的字符串，或者你可以返回一個對象在模板中分別渲染
  return `${grantName} > ${templateName} > ${sectionName}`;
}

// --- Fetch datasets with filters ---
async function fetchDatasets() {
  isLoading.value = true;
  error.value = null;

  const params = new URLSearchParams();
  if (filters.grantId) params.append("grant_id", filters.grantId);
  if (filters.templateId) params.append("template_id", filters.templateId);
  if (filters.sectionId) params.append("section_id", filters.sectionId);
  if (filters.sourceType) params.append("source_type", filters.sourceType);

  const queryString = params.toString();
  const fetchURL = `${API_BASE_URL}/datasets${
    queryString ? "?" + queryString : ""
  }`;

  try {
    const response = await fetch(fetchURL);
    if (!response.ok) throw new Error("Network response was not ok.");
    datasets.value = await response.json();
  } catch (e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}

// --- Reset filters ---
function resetFilters() {
  filters.grantId = "";
  filters.templateId = "";
  filters.sectionId = "";
  filters.sourceType = "";
}

// --- Watchers to react to filter changes ---
watch(
  () => filters.grantId,
  (newVal) => {
    if (!newVal) {
      filters.templateId = "";
    }
  }
);
watch(
  () => filters.templateId,
  (newVal) => {
    if (!newVal) {
      filters.sectionId = "";
    }
  }
);

// Watch all filters and re-fetch when any of them change
watch(filters, fetchDatasets, { deep: true });

onMounted(() => {
  fetchDatasets(); // Load initial table data
});

function openEditModal(dataset) {
  currentDataset.value = dataset;
  isModalVisible.value = true;
}

function closeEditModal() {
  isModalVisible.value = false;
  currentDataset.value = null;
}

async function handleSave(updatedData) {
  isSaving.value = true;
  try {
    const entry = {
      source_type: updatedData.source_type,
      grant_id: currentDataset.value.grant_id,
      template_id: currentDataset.value.template_id,
      section_id: currentDataset.value.section_id,
      prompt: updatedData.prompt,
      final_answer: updatedData.final_answer,
    };

    const response = await fetch(`${API_BASE_URL}/datasets/${updatedData.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry),
    });
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "保存失敗");
    }
    success("保存成功！");
    closeEditModal();
    await fetchDatasets();
  } catch (e) {
    errorNotification(`保存失敗: ${e.message}`);
  } finally {
    isSaving.value = false;
  }
}

async function handleDelete(id) {
  const isConfirmed = await confirm({
    title: "確認刪除",
    message: `您確定要刪除數據點 #${id} 嗎？\n此操作無法復原。`,
    confirmText: "確認刪除",
    cancelText: "取消",
    confirmColor: "danger", // 設置按鈕顏色為危險/紅色
  });

  if (!isConfirmed) {
    return; // 如果用戶點擊取消，則直接返回
  }

  try {
    const response = await fetch(`${API_BASE_URL}/datasets/${id}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "刪除失敗");
    }
    success("刪除成功！");
    await fetchDatasets();
  } catch (e) {
    errorNotification(`刪除失敗: ${e.message}`);
  }
}
</script>
