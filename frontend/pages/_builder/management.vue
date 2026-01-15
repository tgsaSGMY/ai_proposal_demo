<template>
  <ClientOnly>
    <div class="p-4 md:p-8">
      <div class="flex justify-between items-center mb-4 sm:mb-6">
        <h1 class="text-xl sm:text-2xl font-bold">
          數據庫管理
          <p class="text-sm sm:text-md text-gray-400 mb-2 sm:mb-0">
            當某類企劃書生成效果不好時，能夠將外部資料轉爲生成資料，讓AI學習提升效果。也能夠檢查並移除生成資料，確保數據庫品質。
          </p>
        </h1>
        <button
          @click="handleRefreshDatasets"
          :disabled="isRefreshing"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 h-9 flex items-center gap-2"
        >
          <span v-if="!isRefreshing">刷新數據庫</span>
          <span v-else>刷新中...</span>
        </button>
      </div>
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

      <!-- Data Table -->
      <div
        v-if="datasets.length > 0"
        class="bg-white shadow-lg rounded-lg overflow-x-scroll"
      >
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
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
            <tr v-for="item in paginatedDatasets" :key="item.id">
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
                      nameMaps.templates.get(item.template_id) ||
                      item.template_id
                    }}
                  </span>
                </div>
              </td>

              <td
                class="px-6 py-4 text-sm text-gray-600 max-w-72 2xl:max-w-96 truncate"
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
                  :class="
                    item.source_type === 'golden_samples'
                      ? 'text-gray-400 cursor-not-allowed'
                      : 'text-red-600 hover:text-red-900'
                  "
                  :disabled="item.source_type === 'golden_samples'"
                  :title="
                    item.source_type === 'golden_samples'
                      ? '黃金樣本不可刪除'
                      : '刪除'
                  "
                >
                  刪除
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination Controls -->
        <div class="flex justify-center items-center gap-2 mt-6 mb-4 px-6 py-4">
          <button
            v-if="currentPage > 1"
            @click="previousPage"
            class="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            上一頁
          </button>

          <button
            v-for="page in totalPages"
            :key="page"
            @click="goToPage(page)"
            :class="[
              'px-3 py-1 rounded',
              currentPage === page
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300',
            ]"
          >
            {{ page }}
          </button>

          <button
            v-if="currentPage < totalPages"
            @click="nextPage"
            class="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            下一頁
          </button>
        </div>

        <!-- Page Info -->
        <div class="text-center text-sm text-gray-600 mb-4 px-6 pb-4">
          第 {{ currentPage }} / {{ totalPages }} 頁 | 共
          {{ datasets.length }} 條數據
        </div>
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
  </ClientOnly>
</template>

<script setup>
// ===== 页面元数据 =====
// 设置中间件验证，确保用户已登陆
definePageMeta({
  middleware: "auth",
});

// ===== SEO 配置 =====
// 设置页面标题和元数据，用于搜索引擎优化
useHead({
  title: "數據庫管理 - AI 計畫書平台",
  meta: [
    {
      name: "description",
      content:
        "管理和編輯計畫書數據集。支持按主題、模板、章節過濾，批量操作數據。",
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

// ===== 导入依赖库 =====
// 导入 Vue 核心库
import { ref, onMounted, reactive, watch, computed } from "vue";
// 导入子组件和工具函数
import DatasetEditModal from "~/components/DatasetEditModal.vue";
import { getSourceTypeClass, getSourceTypeName } from "~/utils/textMapping";
import { usePlanGenerator } from "~/composables/usePlanGenerator";

// ===== 数据分页和过滤状态 =====
// 数据集列表、当前页码、每页条数等
const datasets = ref([]);
const allDatasets = ref([]);
const currentPage = ref(1);
const itemsPerPage = 50;

// ===== 导入通知和确认服务 =====
import { useLoading } from "~/composables/useLoading";
import { useNotifications } from "~/composables/useNotifications";
const { show: showLoading, hide: hideLoading } = useLoading();
const { success, error: errorNotification } = useNotifications();
import { useConfirm } from "~/composables/useConfirm";
const { confirm } = useConfirm();
const isSaving = ref(false);
const isRefreshing = ref(false);
const error = ref(null);
const { allConfigs } = usePlanGenerator();

// ===== 模态框和编辑状态 =====
// 编辑数据集的模态框状态
const isModalVisible = ref(false);
const currentDataset = ref(null);

// ===== 过滤器状态 =====
// 用于过滤数据的条件：补助类别、模板、章节、数据来源
const filters = reactive({
  grantId: "",
  templateId: "",
  sectionId: "",
  sourceType: "",
});

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

// ===== 计算属性：依赖下拉菜单 =====
// 根据选中的补助类别，动态计算可用的模板列表
const availableTemplates = computed(() => {
  if (!filters.grantId) return [];
  const grant = allConfigs.value.find((g) => g.id === filters.grantId);
  return grant ? grant.templates : [];
});

// ===== 计算属性：可用章节列表 =====
// 根据选中的模板，动态计算可用的章节列表
const availableSections = computed(() => {
  if (!filters.templateId) return [];
  const template = availableTemplates.value.find(
    (t) => t.id === filters.templateId
  );
  return template ? template.sections : [];
});

// ===== 计算属性：总页数 =====
// 计算基于过滤后的数据集和每页条数的总页数
const totalPages = computed(() => {
  return Math.ceil(datasets.value.length / itemsPerPage);
});

// ===== 计算属性：过滤后的数据集 =====
// 根据用户选择的过滤条件，返回过滤后的数据集
const filteredDatasets = computed(() => {
  return allDatasets.value.filter((item) => {
    const grantMatch = !filters.grantId || item.grant_id === filters.grantId;
    const templateMatch =
      !filters.templateId || item.template_id === filters.templateId;
    const sectionMatch =
      !filters.sectionId || item.section_id === filters.sectionId;
    const sourceMatch =
      !filters.sourceType || item.source_type === filters.sourceType;
    return grantMatch && templateMatch && sectionMatch && sourceMatch;
  });
});

// ===== 侦听器：过滤数据变化 =====
// 当过滤后的数据集变化时，重置页码并更新显示列表
watch(
  filteredDatasets,
  (newVal) => {
    datasets.value = newVal;
    currentPage.value = 1;
  },
  { deep: true }
);

// ===== 计算属性：分页后的数据集 =====
// 根据当前页码，返回该页应显示的数据
const paginatedDatasets = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  return datasets.value.slice(start, end);
});

// ===== 计算属性：名称映射 =====
// 构建一个映射表，将 ID 转换为人类可读的名称（补助、模板、章节等）
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

// ===== 刷新数据库 =====
// 调用后端 API 刷新数据集，获取最新的数据
async function handleRefreshDatasets() {
  isRefreshing.value = true;
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("請先登入");
    const response = await fetch(`${API_BASE_URL}/refresh-datasets`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });
    if (!response.ok) throw new Error("Network response was not ok.");

    const result = await response.json();
    allDatasets.value = result.datasets;
    datasets.value = allDatasets.value;
    success("數據庫刷新成功！");
  } catch (e) {
    errorNotification(`刷新失敗: ${e.message}`);
  } finally {
    isRefreshing.value = false;
  }
}

// ===== 重置过滤器 =====
// 清除所有过滤条件，显示全部数据
function resetFilters() {
  filters.grantId = "";
  filters.templateId = "";
  filters.sectionId = "";
  filters.sourceType = "";
  currentPage.value = 1;
}

// ===== 分页函数 =====
// 跳转到指定的页码
function goToPage(page) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

// ===== 下一页 =====
// 转到下一页（如果不是最后一页）
function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

// ===== 上一页 =====
// 转到上一页（如果不是第一页）
function previousPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

// ===== 侦听器：过滤器变化 =====
// 当过滤器变化时，重置相关的依赖过滤器和页码
watch(
  () => filters.grantId,
  () => {
    filters.templateId = "";
    filters.sectionId = "";
  }
);
watch(
  () => filters.templateId,
  () => {
    filters.sectionId = "";
  }
);

// ===== 初始化数据集 =====
// 从生命周期预加载的数据集中初始化页面数据
async function initializeDatasets() {
  // 从 /datasets-lifecycle 接口获取预加载的数据集
  showLoading("加載數據庫...");
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) throw new Error("請先登入");
  const response = await fetch(`${API_BASE_URL}/datasets-lifecycle`, {
    headers: {
      Authorization: `Bearer ${session.access_token}`,
    },
  });
  if (!response.ok) throw new Error("Failed to fetch preloaded datasets");
  const data = await response.json();
  allDatasets.value = data;
  hideLoading();
}
onMounted(async () => {
  // ===== 页面挂载时初始化 =====
  // 使用 lifecycle 预加载的数据集初始化页面
  await initializeDatasets();
  datasets.value = allDatasets.value;
});

// ===== 内部用户检查 =====
// 检查当前用户是否为内部人员，否则重定向到首页
onMounted(async () => {
  const { checkIsInternal } = useInternalCheck();

  // 執行檢查
  const isInternal = await checkIsInternal();

  if (!isInternal) {
    // 如果不是內部人員，重定向到外部版本頁面
    window.location.href = "/";
  }
});

// ===== 打开编辑模态框 =====
// 打开指定数据集的编辑模态框
function openEditModal(dataset) {
  currentDataset.value = dataset;
  isModalVisible.value = true;
}

// ===== 关闭编辑模态框 =====
// 关闭编辑模态框并清空当前数据集
function closeEditModal() {
  isModalVisible.value = false;
  currentDataset.value = null;
}

// ===== 保存数据集编辑 =====
// 调用 API 保存编辑后的数据集内容
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

    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("請先登入");

    const response = await fetch(`${API_BASE_URL}/datasets/${updatedData.id}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(entry),
    });
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "保存失敗");
    }
    success("保存成功！");
    closeEditModal();
    handleRefreshDatasets();
  } catch (e) {
    errorNotification(`保存失敗: ${e.message}`);
  } finally {
    isSaving.value = false;
  }
}

// ===== 删除数据集 =====
// 显示确认对话框，验证用户确认后删除数据集
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
  // Prevent deleting golden samples as an extra safety guard
  const target = allDatasets.value.find((d) => d.id === id);
  if (target && target.source_type === "golden_samples") {
    errorNotification("黃金樣本不可刪除。如需更新資料請使用編輯功能。");
    return;
  }

  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("請先登入");
    const response = await fetch(`${API_BASE_URL}/datasets/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "刪除失敗");
    }
    success("刪除成功！");
    handleRefreshDatasets();
  } catch (e) {
    errorNotification(`刪除失敗: ${e.message}`);
  }
}
</script>
