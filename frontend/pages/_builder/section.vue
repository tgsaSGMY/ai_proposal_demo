<!-- 動態欄位配置中心 -->
<template>
  <ClientOnly>
    <div class="py-6 px-2 sm:px-4 md:py-10 md:px-8">
      <div
        class="w-full max-w-5xl mx-auto bg-white shadow-xl rounded-2xl p-4 sm:p-6 md:p-8"
      >
        <!-- Header -->
        <div
          class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4"
        >
          <div>
            <h1 class="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">
              動態欄位配置中心
            </h1>
            <p class="text-gray-500 text-sm sm:text-base">
              管理計畫書中「章節」與「欄位」的結構。內部人員可以在這裡新增 /
              調整 / 刪除章節與欄位，前端表單與 AI 提示會自動同步。
            </p>
          </div>

          <div class="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
            <button
              @click="openSectionRecommender"
              class="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 flex items-center justify-center gap-2 whitespace-nowrap"
              :disabled="!isTemplateSelected"
              :class="[
                !isTemplateSelected
                  ? 'cursor-not-allowed opacity-60'
                  : 'cursor-pointer',
              ]"
            >
              <span class="text-lg">🤖</span>
              AI 推薦
            </button>
            <button
              @click="openCreateSection"
              class="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 flex items-center justify-center gap-2 whitespace-nowrap"
              :disabled="!isTemplateSelected"
              :class="[
                !isTemplateSelected
                  ? 'cursor-not-allowed opacity-60'
                  : 'cursor-pointer',
              ]"
            >
              <span class="text-lg">＋</span>
              新增章節
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label
              class="block text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide"
            >
              選擇補助類別 (Grant)
            </label>
            <select
              v-model="selectedGrantId"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500"
            >
              <option value="" disabled>請先選擇補助類別</option>
              <option v-for="grant in grants" :key="grant.id" :value="grant.id">
                {{ grant.name }} ({{ grant.id }})
              </option>
            </select>
          </div>

          <div>
            <label
              class="block text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide"
            >
              選擇模板 (Template)
            </label>
            <select
              v-model="selectedTemplateId"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-500 disabled:bg-gray-100 disabled:text-gray-400"
              :disabled="!availableTemplates.length"
            >
              <option value="" disabled>
                {{
                  availableTemplates.length ? "請選擇模板" : "請先選擇補助類別"
                }}
              </option>
              <option
                v-for="template in availableTemplates"
                :key="template.id + template.name"
                :value="template.id"
              >
                {{ template.name }} ({{ template.id }})
              </option>
            </select>
          </div>
        </div>

        <div
          v-if="!isTemplateSelected"
          class="mb-6 rounded-xl bg-gray-50 border border-dashed border-gray-200 p-6 text-center text-gray-500"
        >
          請先選擇補助類別與模板，才能管理對應的章節與欄位。
        </div>

        <!-- Create Section Form (outside of loop) -->
        <div
          v-if="editingSection && !editingSection.id"
          class="mb-6 rounded-xl bg-gradient-to-br from-indigo-50 to-blue-50 border border-indigo-200 p-4 sm:p-6 space-y-4 shadow-sm"
        >
          <h3
            class="text-base font-bold text-indigo-900 flex items-center gap-2"
          >
            <span class="text-lg">✨</span>
            新增章節
          </h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label
                class="block text-xs font-semibold text-indigo-700 mb-2 uppercase tracking-wide"
              >
                章節 Key
              </label>
              <input
                v-model="editingSection.section_key"
                type="text"
                class="w-full px-3 py-2 rounded-lg border border-indigo-200 bg-white shadow-sm hover:border-indigo-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-sm placeholder-gray-400"
                placeholder="例如：二、研發動機"
              />
            </div>
            <div class="sm:col-span-2">
              <label
                class="block text-xs font-semibold text-indigo-700 mb-2 uppercase tracking-wide"
              >
                顯示標題
              </label>
              <input
                v-model="editingSection.title"
                type="text"
                class="w-full px-3 py-2 rounded-lg border border-indigo-200 bg-white shadow-sm hover:border-indigo-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-sm placeholder-gray-400"
                placeholder="例如：研發動機與背景"
              />
            </div>
          </div>
          <div class="flex flex-wrap gap-2 pt-2">
            <button
              @click="saveSection(editingSection)"
              class="px-4 py-2.5 text-sm font-semibold rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-md hover:shadow-lg hover:from-indigo-700 hover:to-indigo-600 transition-all active:scale-95"
            >
              ✓ 儲存章節
            </button>
            <button
              @click="cancelEditSection"
              class="px-4 py-2.5 text-sm font-medium rounded-lg border border-gray-300 text-gray-700 bg-white shadow-sm hover:bg-gray-50 hover:border-gray-400 transition-all"
            >
              取消
            </button>
          </div>
        </div>

        <!-- Section list (Draggable) -->
        <div v-if="sections.length" class="space-y-4">
          <div
            v-for="(section, index) in sections"
            :key="section.id"
            draggable="true"
            @dragstart="startDragSection(index, $event)"
            @dragover="dragOverSection(index, $event)"
            @drop="dropSection(index, $event)"
            @dragend="dragEndSection"
            :class="[
              'border rounded-xl p-4 sm:p-5 transition-shadow cursor-move',
              dragOverSectionIndex === index
                ? 'bg-indigo-100 border-indigo-300 shadow-md'
                : 'bg-gray-50 hover:shadow-md',
            ]"
          >
            <!-- Section header -->
            <div
              class="flex flex-col sm:flex-row justify-between gap-3 sm:gap-4 items-start sm:items-center mb-3"
            >
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <span
                    class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 text-xs font-semibold"
                  >
                    {{ section.order }}
                  </span>
                  <p class="font-semibold text-gray-800">
                    {{ section.section_key }}
                  </p>
                </div>
                <p class="text-sm text-gray-500">
                  顯示標題：{{ section.title }}
                </p>
              </div>

              <div class="flex flex-wrap gap-2">
                <button
                  @click="startEditSection(section)"
                  class="px-3 py-1.5 text-sm rounded-lg border border-indigo-200 text-indigo-700 bg-white hover:bg-indigo-50"
                >
                  編輯章節
                </button>
                <button
                  @click="confirmDeleteSection(section)"
                  class="px-3 py-1.5 text-sm rounded-lg border border-red-200 text-red-700 bg-white hover:bg-red-50"
                >
                  刪除章節
                </button>
              </div>
            </div>

            <!-- Section edit form (inline) -->
            <div
              v-if="editingSection && editingSection.id === section.id"
              class="mb-4 rounded-lg bg-gradient-to-br from-indigo-50 to-white border border-indigo-200 p-3 sm:p-4 space-y-3 shadow-sm"
            >
              <h3
                class="text-sm font-bold text-indigo-900 mb-2 flex items-center gap-2"
              >
                <span class="text-base">✎</span>
                編輯章節設定
              </h3>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label
                    class="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide"
                  >
                    章節 Key
                  </label>
                  <input
                    v-model="editingSection.section_key"
                    type="text"
                    class="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white shadow-sm hover:border-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-sm placeholder-gray-400"
                    placeholder="例如：二、研發動機"
                  />
                </div>
                <div class="sm:col-span-2">
                  <label
                    class="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide"
                  >
                    顯示標題
                  </label>
                  <input
                    v-model="editingSection.title"
                    type="text"
                    class="w-full px-3 py-2 rounded-lg border border-gray-300 bg-white shadow-sm hover:border-gray-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-sm placeholder-gray-400"
                    placeholder="例如：二、研發動機"
                  />
                </div>
              </div>
              <div
                class="flex flex-wrap gap-2 mt-3 pt-2 border-t border-indigo-100"
              >
                <button
                  @click="saveSection(editingSection)"
                  class="px-4 py-2 bg-gradient-to-r from-indigo-600 to-indigo-500 text-white rounded-lg text-sm font-semibold shadow-md hover:shadow-lg hover:from-indigo-700 hover:to-indigo-600 transition-all active:scale-95"
                >
                  ✓ 儲存章節
                </button>
                <button
                  @click="cancelEditSection"
                  class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-all"
                >
                  取消
                </button>
              </div>
            </div>

            <!-- Fields list -->
            <div class="mt-2">
              <div class="flex justify-between items-center mb-2">
                <h3 class="text-sm font-semibold text-gray-700">
                  欄位列表（{{ section.fields.length }}）
                </h3>
                <button
                  @click="openCreateField(section)"
                  class="px-3 py-1.5 text-xs rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
                >
                  ＋ 新增欄位
                </button>
              </div>

              <div v-if="section.fields.length" class="overflow-x-auto">
                <table class="min-w-full text-left text-xs sm:text-sm">
                  <thead>
                    <tr class="border-b text-gray-500 bg-white">
                      <th class="py-2 pr-4">欄位 Key</th>
                      <th class="py-2 pr-4">顯示標題</th>
                      <th class="py-2 pr-4 hidden sm:table-cell">說明</th>
                      <th class="py-2 pr-4 text-right">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(field, fieldIndex) in section.fields"
                      :key="field.id"
                      draggable="true"
                      @dragstart="
                        startDragField(section.id, fieldIndex, $event)
                      "
                      @dragover="dragOverField(section.id, fieldIndex, $event)"
                      @drop="dropField(section.id, fieldIndex, $event)"
                      @dragend="dragEndField"
                      :class="[
                        'border-b last:border-b-0 bg-white transition-colors cursor-move',
                        dragOverFieldSectionId === section.id &&
                        dragOverFieldIndex === fieldIndex
                          ? 'bg-indigo-50 border-indigo-300'
                          : 'border-gray-200',
                      ]"
                    >
                      <!-- Normal row -->
                      <template v-if="!isEditingField(field)">
                        <td class="py-2 pr-4 text-gray-800 whitespace-nowrap">
                          {{ field.field_key }}
                        </td>
                        <td class="py-2 pr-4 text-gray-800">
                          {{ field.title }}
                        </td>
                        <td
                          class="py-2 pr-4 text-gray-500 hidden sm:table-cell max-w-xs truncate"
                        >
                          {{ field.description }}
                        </td>
                        <td class="py-2 pr-0 text-right whitespace-nowrap">
                          <button
                            @click="startEditField(field)"
                            class="text-indigo-600 hover:text-indigo-800 mr-3"
                          >
                            編輯
                          </button>
                          <button
                            @click="confirmDeleteField(field)"
                            class="text-red-600 hover:text-red-800"
                          >
                            刪除
                          </button>
                        </td>
                      </template>

                      <!-- Editing row -->
                      <template v-else>
                        <td class="py-3 pr-4 align-top">
                          <input
                            v-model="editingField.field_key"
                            type="text"
                            class="w-full px-2 py-1.5 rounded-md border border-indigo-300 bg-white shadow-sm hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-xs placeholder-gray-400"
                          />
                        </td>
                        <td class="py-3 pr-4 align-top">
                          <input
                            v-model="editingField.title"
                            type="text"
                            class="w-full px-2 py-1.5 rounded-md border border-indigo-300 bg-white shadow-sm hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-xs placeholder-gray-400"
                          />
                        </td>
                        <td class="py-3 pr-4 align-top hidden sm:table-cell">
                          <textarea
                            v-model="editingField.description"
                            rows="2"
                            class="w-full px-2 py-1.5 rounded-md border border-indigo-300 bg-white shadow-sm hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-xs placeholder-gray-400 resize-none"
                          />
                        </td>
                        <td
                          class="py-3 pr-0 align-top text-right whitespace-nowrap space-x-2"
                        >
                          <button
                            @click="saveField(editingField)"
                            class="px-3 py-1 text-indigo-600 hover:text-white hover:bg-indigo-600 rounded-md text-xs font-semibold transition-all"
                          >
                            ✓ 儲存
                          </button>
                          <button
                            @click="cancelEditField"
                            class="px-3 py-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md text-xs transition-all"
                          >
                            ✕
                          </button>
                        </td>
                      </template>
                    </tr>
                  </tbody>
                </table>
              </div>

              <p v-else class="text-xs text-gray-400 italic">
                尚無欄位，請點擊「新增欄位」開始建立。
              </p>

              <!-- Create field form (shown regardless of field count) -->
              <div
                v-if="
                  editingField &&
                  editingField.section_id === section.id &&
                  !editingField.id
                "
                class="mt-3 border-t-2 border-indigo-200 bg-gradient-to-r from-indigo-50 via-blue-50 to-indigo-50 overflow-x-auto"
              >
                <table class="min-w-full text-left text-xs sm:text-sm">
                  <tbody>
                    <tr
                      class="bg-gradient-to-r from-indigo-50 to-blue-50 border-b border-indigo-200"
                    >
                      <td class="py-3 pr-4 align-top">
                        <input
                          v-model="editingField.field_key"
                          type="text"
                          class="w-full px-2 py-1.5 rounded-lg border-2 border-indigo-300 bg-white shadow-md hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-xs placeholder-gray-400 font-medium"
                          placeholder="例如：description"
                        />
                      </td>
                      <td class="py-3 pr-4 align-top">
                        <input
                          v-model="editingField.title"
                          type="text"
                          class="w-full px-2 py-1.5 rounded-lg border-2 border-indigo-300 bg-white shadow-md hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-xs placeholder-gray-400 font-medium"
                          placeholder="例如：項目說明"
                        />
                      </td>
                      <td class="py-3 pr-4 align-top hidden sm:table-cell">
                        <textarea
                          v-model="editingField.description"
                          rows="2"
                          class="w-full px-2 py-1.5 rounded-lg border-2 border-indigo-300 bg-white shadow-md hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all text-xs placeholder-gray-400 resize-none"
                          placeholder="欄位說明"
                        />
                      </td>
                      <td
                        class="py-3 pr-0 align-top text-right whitespace-nowrap space-x-1.5"
                      >
                        <button
                          @click="saveField(editingField)"
                          class="px-3 py-1.5 text-xs font-bold rounded-lg bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-md hover:shadow-lg hover:from-green-600 hover:to-emerald-600 transition-all active:scale-95"
                        >
                          ✓ 新增
                        </button>
                        <button
                          @click="cancelEditField"
                          class="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gray-300 text-gray-700 bg-white hover:bg-gray-100 transition-all"
                        >
                          ✕
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <div
          v-else-if="isTemplateSelected"
          class="text-center py-10 text-gray-500"
        >
          目前尚未建立任何章節，請先點擊右上角「新增章節」。
        </div>
      </div>

      <!-- Section Recommender Modal -->
      <SectionRecommenderModal
        :model-value="isRecommenderOpen"
        :current-sections="sections"
        @update:model-value="(val) => (isRecommenderOpen = val)"
        @close="isRecommenderOpen = false"
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
  title: "動態欄位配置中心 - TGSA 補助引擎",
  meta: [
    {
      name: "description",
      content:
        "管理計畫書的章節與欄位結構。內部人員可在此視覺化調整欄位，用於前端表單與 AI 提示。",
    },
    {
      name: "keywords",
      content: "動態欄位,章節配置,欄位管理,計畫書",
    },
  ],
});

// ===== 导入依赖库 =====
// 导入 Vue 核心库
import { ref, onMounted, computed, watch } from "vue";
import { authenticatedFetch } from "~/composables/useAppAuth";
// 导入自定义组合式函数
import { useNotifications } from "~/composables/useNotifications";
import { useConfirm } from "~/composables/useConfirm";
import { useLoading } from "~/composables/useLoading";
import { useInternalCheck } from "~/composables/useInternalCheck";
// 导入子组件
import SectionRecommenderModal from "~/components/data/section/SectionRecommenderModal.vue";

// ===== 初始化服务 =====
// 获取通知、确认、加载状态等服务
const { success, error: errorNotification } = useNotifications();
const { confirm } = useConfirm();
const { show: showLoading, hide: hideLoading } = useLoading();

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
const TEMPLATE_MANAGER_API = `${API_BASE_URL}/template-manager`;

// ===== 数据模型（前端端） =====
// 存储补助、选中的补助和模板、以及章节列表
const grants = ref([]);
const selectedGrantId = ref("");
const selectedTemplateId = ref("");
const sections = ref([]); // [{ id, schema_id, section_key, title, order, fields: [...] }]

// ===== 编辑状态 =====
// 当前正在编辑的章节和欄位，以及推荐模态框状态
const editingSection = ref(null);
const editingField = ref(null);
const isRecommenderOpen = ref(false);

// ===== 拖拽状态 =====
// 用于管理章节和欄位的拖拽排序
const draggedSectionIndex = ref(null);
const dragOverSectionIndex = ref(null);
const draggedFieldIndex = ref(null);
const dragOverFieldSectionId = ref(null);
const dragOverFieldIndex = ref(null);

// ===== 计算属性：可用模板 =====
// 根据选中的补助类别，动态计算可用的模板列表
const availableTemplates = computed(() => {
  if (!selectedGrantId.value) return [];
  const targetGrant = grants.value.find(
    (grant) => grant.id === selectedGrantId.value,
  );
  return targetGrant?.templates || [];
});

// ===== 计算属性：是否选中模板 =====
// 检查用户是否同时选中了补助类别和模板
const isTemplateSelected = computed(() =>
  Boolean(selectedGrantId.value && selectedTemplateId.value),
);

// ===== 工具函数：克隆章节 =====
// 创建章节对象的浅拷贝，用于编辑操作
function cloneSection(section) {
  return {
    id: section.id,
    schema_id: section.schema_id,
    section_key: section.section_key,
    title: section.title,
    order: section.order,
    template_id: section.template_id || selectedTemplateId.value,
    template_grant_id: section.template_grant_id || selectedGrantId.value,
  };
}

// ===== 工具函数：克隆欄位 =====
// 创建欄位对象的浅拷贝，用于编辑操作
function cloneField(field) {
  return {
    id: field.id,
    section_id: field.section_id,
    field_key: field.field_key,
    title: field.title,
    description: field.description || "",
    order: field.order,
  };
}

// ===== 工具函数：检查欄位是否在编辑 =====
// 判断指定的欄位是否正在被编辑
function isEditingField(field) {
  return (
    editingField.value &&
    editingField.value.id !== null &&
    editingField.value.id === field.id
  );
}

async function authedFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return authenticatedFetch(url, {
    ...options,
    headers,
  });
}

// ===== 获取章节列表 =====
// 从后端 API 获取选中模板的所有章节和欄位
async function fetchSections() {
  if (!isTemplateSelected.value) {
    sections.value = [];
    return;
  }
  try {
    showLoading("載入章節與欄位...");
    const response = await authedFetch(
      `${API_BASE_URL}/dynamic-sections?template_id=${encodeURIComponent(
        selectedTemplateId.value,
      )}&template_grant_id=${encodeURIComponent(selectedGrantId.value)}`,
    );
    if (!response.ok) throw new Error(await response.text());
    const data = await response.json();
    sections.value = (data || [])
      .map((section) => ({
        ...section,
        template_id: section.template_id || selectedTemplateId.value,
        template_grant_id: section.template_grant_id || selectedGrantId.value,
        fields: (section.fields || [])
          .slice()
          .sort((a, b) => (a.order || 0) - (b.order || 0)),
      }))
      .sort((a, b) => (a.order || 0) - (b.order || 0));
  } catch (e) {
    console.error(e);
    errorNotification("載入失敗：" + e.message);
  } finally {
    hideLoading();
  }
}

// ===== 章节 CRUD 操作 =====
// 打开创建新章节的界面
function openCreateSection() {
  if (!isTemplateSelected.value) {
    errorNotification("請先選擇補助類別與模板");
    return;
  }
  const maxOrder = sections.value.reduce(
    (max, s) => (s.order > max ? s.order : max),
    0,
  );
  editingSection.value = {
    id: null,
    schema_id: "default",
    section_key: "",
    title: "",
    order: maxOrder + 1,
    template_id: selectedTemplateId.value,
    template_grant_id: selectedGrantId.value,
  };
}

// ===== 打开章节推荐模态框 =====
// 显示 AI 推荐章节的模态框
function openSectionRecommender() {
  if (!isTemplateSelected.value) {
    errorNotification("請先選擇補助類別與模板");
    return;
  }
  isRecommenderOpen.value = true;
}

// ===== 开始编辑章节 =====
// 打开指定章节的编辑界面
function startEditSection(section) {
  editingSection.value = cloneSection(section);
}

// ===== 取消章节编辑 =====
// 关闭章节编辑界面，不保存任何更改
function cancelEditSection() {
  editingSection.value = null;
}

// ===== 保存章节 =====
// 调用 API 保存新建或编辑的章节
async function saveSection(localSection) {
  try {
    if (!localSection.section_key || !localSection.title) {
      throw new Error("章節 key 與標題不可為空");
    }

    const isCreate = !localSection.id;
    const url = isCreate
      ? `${API_BASE_URL}/dynamic-sections/sections`
      : `${API_BASE_URL}/dynamic-sections/sections/${localSection.id}`;

    const method = isCreate ? "POST" : "PUT";

    const response = await authedFetch(url, {
      method,
      body: JSON.stringify({
        schema_id: localSection.schema_id,
        section_key: localSection.section_key,
        title: localSection.title,
        order: localSection.order || 1,
        template_id: localSection.template_id || selectedTemplateId.value,
        template_grant_id:
          localSection.template_grant_id || selectedGrantId.value,
      }),
    });

    if (!response.ok) throw new Error(await response.text());
    const saved = await response.json();

    if (isCreate) {
      sections.value.push(saved);
    } else {
      const idx = sections.value.findIndex((s) => s.id === saved.id);
      if (idx !== -1) {
        sections.value[idx] = saved;
      }
    }

    // 依照排序值重新排序，讓畫面更直觀
    sections.value.sort((a, b) => (a.order || 0) - (b.order || 0));

    editingSection.value = null;
    success("章節已儲存");
  } catch (e) {
    console.error(e);
    errorNotification("儲存章節失敗：" + e.message);
  }
}

// ===== 确认删除章节 =====
// 显示确认对话框，验证用户确认后删除章节及其所有欄位
async function confirmDeleteSection(section) {
  const isConfirmed = await confirm({
    title: "確認刪除章節",
    message: `您確定要刪除「${section.section_key}」嗎？\n此動作會連同底下所有欄位一併刪除，且無法復原。`,
    confirmText: "確認刪除",
    cancelText: "取消",
    confirmColor: "danger",
  });

  if (!isConfirmed) return;

  try {
    const response = await authedFetch(
      `${API_BASE_URL}/dynamic-sections/sections/${section.id}`,
      {
        method: "DELETE",
      },
    );
    if (!response.ok) throw new Error(await response.text());

    sections.value = sections.value.filter((s) => s.id !== section.id);
    if (editingSection.value && editingSection.value.id === section.id) {
      editingSection.value = null;
    }
    success("章節已刪除");
  } catch (e) {
    console.error(e);
    errorNotification("刪除章節失敗：" + e.message);
  }
}

// ===== 欄位 CRUD 操作 =====
// 打开创建新欄位的界面
function openCreateField(section) {
  const maxOrder = section.fields.reduce(
    (max, f) => (f.order > max ? f.order : max),
    0,
  );
  editingField.value = {
    id: null,
    section_id: section.id,
    field_key: "",
    title: "",
    description: "",
    order: maxOrder + 1,
  };
}

// ===== 开始编辑欄位 =====
// 打开指定欄位的编辑界面
function startEditField(field) {
  editingField.value = cloneField(field);
}

// ===== 取消欄位编辑 =====
// 关闭欄位编辑界面，不保存任何更改
function cancelEditField() {
  editingField.value = null;
}

// ===== 保存欄位 =====
// 调用 API 保存新建或编辑的欄位
async function saveField(localField) {
  try {
    if (!localField.field_key || !localField.title) {
      throw new Error("欄位 key 與標題不可為空");
    }

    const isCreate = !localField.id;
    const url = isCreate
      ? `${API_BASE_URL}/dynamic-sections/fields`
      : `${API_BASE_URL}/dynamic-sections/fields/${localField.id}`;
    const method = isCreate ? "POST" : "PUT";

    const response = await authedFetch(url, {
      method,
      body: JSON.stringify({
        section_id: localField.section_id,
        field_key: localField.field_key,
        title: localField.title,
        description: localField.description || "",
        order: localField.order || 1,
      }),
    });

    if (!response.ok) throw new Error(await response.text());
    const saved = await response.json();

    const section = sections.value.find((s) => s.id === saved.section_id);
    if (!section) {
      await fetchSections();
    } else if (isCreate) {
      section.fields.push(saved);
    } else {
      const idx = section.fields.findIndex((f) => f.id === saved.id);
      if (idx !== -1) section.fields[idx] = saved;
    }

    if (section) {
      section.fields.sort((a, b) => (a.order || 0) - (b.order || 0));
    }

    editingField.value = null;
    success("欄位已儲存");
  } catch (e) {
    console.error(e);
    errorNotification("儲存欄位失敗：" + e.message);
  }
}

// ===== 确认删除欄位 =====
// 显示确认对话框，验证用户确认后删除欄位
async function confirmDeleteField(field) {
  const isConfirmed = await confirm({
    title: "確認刪除欄位",
    message: `您確定要刪除欄位「${field.field_key}」嗎？此操作無法復原。`,
    confirmText: "確認刪除",
    cancelText: "取消",
    confirmColor: "danger",
  });

  if (!isConfirmed) return;

  try {
    const response = await authedFetch(
      `${API_BASE_URL}/dynamic-sections/fields/${field.id}`,
      {
        method: "DELETE",
      },
    );
    if (!response.ok) throw new Error(await response.text());

    const section = sections.value.find((s) => s.id === field.section_id);
    if (section) {
      section.fields = section.fields.filter((f) => f.id !== field.id);
    }

    if (editingField.value && editingField.value.id === field.id) {
      editingField.value = null;
    }

    success("欄位已刪除");
  } catch (e) {
    console.error(e);
    errorNotification("刪除欄位失敗：" + e.message);
  }
}

// ===== 拖拽排序：章节 =====
// 处理章节拖拽的开始事件
function startDragSection(index, event) {
  draggedSectionIndex.value = index;
  event.dataTransfer.effectAllowed = "move";
}

// ===== 拖拽排序：章节悬停 =====
// 处理拖拽章节时的悬停事件
function dragOverSection(index, event) {
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  dragOverSectionIndex.value = index;
}

// ===== 拖拽排序：章节放置 =====
// 处理章节拖拽放置事件，更新章节顺序并调用 API 保存
async function dropSection(targetIndex, event) {
  event.preventDefault();
  dragOverSectionIndex.value = null;

  if (draggedSectionIndex.value === null) return;

  const sourceIndex = draggedSectionIndex.value;
  if (sourceIndex === targetIndex) {
    draggedSectionIndex.value = null;
    return;
  }

  // Swap sections in array
  const [draggedSection] = sections.value.splice(sourceIndex, 1);
  sections.value.splice(targetIndex, 0, draggedSection);

  draggedSectionIndex.value = null;

  // Update API for all sections that changed order
  try {
    for (const section of sections.value) {
      section.order = sections.value.indexOf(section) + 1;
      const response = await authedFetch(
        `${API_BASE_URL}/dynamic-sections/sections/${section.id}`,
        {
          method: "PUT",
          body: JSON.stringify({
            schema_id: section.schema_id,
            section_key: section.section_key,
            title: section.title,
            order: section.order,
            template_id: section.template_id || selectedTemplateId.value,
            template_grant_id:
              section.template_grant_id || selectedGrantId.value,
          }),
        },
      );
      if (!response.ok) throw new Error(await response.text());
    }
    success("章節順序已更新");
  } catch (e) {
    console.error(e);
    errorNotification("更新順序失敗：" + e.message);
    // Reload to get correct state
    await fetchSections();
  }
}

// ===== 拖拽排序：章节结束 =====
// 处理章节拖拽结束事件，清理拖拽状态
function dragEndSection() {
  draggedSectionIndex.value = null;
  dragOverSectionIndex.value = null;
}

// ===== 拖拽排序：欄位 =====
// 处理欄位拖拽的开始事件
function startDragField(sectionId, fieldIndex, event) {
  draggedFieldIndex.value = fieldIndex;
  dragOverFieldSectionId.value = sectionId;
  event.dataTransfer.effectAllowed = "move";
}

// ===== 拖拽排序：欄位悬停 =====
// 处理拖拽欄位时的悬停事件
function dragOverField(sectionId, fieldIndex, event) {
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  dragOverFieldSectionId.value = sectionId;
  dragOverFieldIndex.value = fieldIndex;
}

// ===== 拖拽排序：欄位放置 =====
// 处理欄位拖拽放置事件，更新欄位顺序并调用 API 保存
async function dropField(targetSectionId, targetFieldIndex, event) {
  event.preventDefault();
  dragOverFieldSectionId.value = null;
  dragOverFieldIndex.value = null;

  if (draggedFieldIndex.value === null) return;

  const section = sections.value.find((s) => s.id === targetSectionId);
  if (!section) return;

  const sourceFieldIndex = draggedFieldIndex.value;
  if (sourceFieldIndex === targetFieldIndex) {
    draggedFieldIndex.value = null;
    return;
  }

  // Swap fields in array
  const [draggedField] = section.fields.splice(sourceFieldIndex, 1);
  section.fields.splice(targetFieldIndex, 0, draggedField);

  draggedFieldIndex.value = null;

  // Recalculate order for all fields in this section
  try {
    for (let i = 0; i < section.fields.length; i++) {
      section.fields[i].order = i + 1;
      const response = await authedFetch(
        `${API_BASE_URL}/dynamic-sections/fields/${section.fields[i].id}`,
        {
          method: "PUT",
          body: JSON.stringify({
            section_id: section.fields[i].section_id,
            field_key: section.fields[i].field_key,
            title: section.fields[i].title,
            description: section.fields[i].description || "",
            order: section.fields[i].order,
          }),
        },
      );
      if (!response.ok) throw new Error(await response.text());
    }
    success("欄位順序已更新");
  } catch (e) {
    console.error(e);
    errorNotification("更新欄位順序失敗：" + e.message);
    // Reload to get correct state
    await fetchSections();
  }
}

// ===== 拖拽排序：欄位结束 =====
// 处理欄位拖拽结束事件，清理拖拽状态
function dragEndField() {
  draggedFieldIndex.value = null;
  dragOverFieldSectionId.value = null;
  dragOverFieldIndex.value = null;
}

// ===== 生命周期 =====
// 页面挂载时，检查用户权限并加载补助模板列表
onMounted(async () => {
  // 僅允許內部人員存取
  const { checkIsInternal } = useInternalCheck();
  const isInternal = await checkIsInternal();
  if (!isInternal) {
    window.location.href = "/";
    return;
  }

  await fetchGrantTemplates();
});

// ===== 获取补助和模板列表 =====
// 从后端 API 获取所有可用的补助类别和对应的模板
async function fetchGrantTemplates() {
  try {
    showLoading("載入補助模板...");
    const [grantsResp, templatesResp] = await Promise.all([
      authedFetch(`${TEMPLATE_MANAGER_API}/grants`),
      authedFetch(`${TEMPLATE_MANAGER_API}/templates`),
    ]);

    if (!grantsResp.ok) {
      throw new Error(await grantsResp.text());
    }
    if (!templatesResp.ok) {
      throw new Error(await templatesResp.text());
    }

    const grantList = await grantsResp.json();
    const templateList = await templatesResp.json();

    const grantMap = new Map();
    grantList.forEach((grant) => {
      grantMap.set(grant.id, {
        ...grant,
        templates: [],
      });
    });

    templateList.forEach((template) => {
      if (!grantMap.has(template.grant_id)) {
        grantMap.set(template.grant_id, {
          id: template.grant_id,
          name: template.grant_id,
          templates: [],
        });
      }
      grantMap.get(template.grant_id).templates.push(template);
    });

    grants.value = Array.from(grantMap.values());
    if (!selectedGrantId.value && grants.value.length) {
      selectedGrantId.value = grants.value[0].id;
    }
  } catch (e) {
    console.error(e);
    errorNotification("載入補助列表失敗：" + e.message);
  } finally {
    hideLoading();
  }
}

// ===== 侦听器：补助类别变化 =====
// 当补助类别变化时，重置模板选择和章节列表
watch(selectedGrantId, (newGrantId) => {
  const templates = availableTemplates.value;
  if (!newGrantId || !templates.length) {
    selectedTemplateId.value = "";
    sections.value = [];
    return;
  }
  if (!templates.find((tpl) => tpl.id === selectedTemplateId.value)) {
    selectedTemplateId.value = templates[0]?.id || "";
  }
});

// ===== 侦听器：模板变化 =====
// 当模板选择变化时，清空编辑状态并获取该模板的章节列表
watch(selectedTemplateId, async (newTemplateId) => {
  sections.value = [];
  editingSection.value = null;
  editingField.value = null;
  if (!newTemplateId) {
    return;
  }
  await fetchSections();
});
</script>
