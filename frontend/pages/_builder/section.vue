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
            <div class="text-sm text-gray-500 flex items-center gap-2">
              <span class="font-semibold text-gray-700">使用中的 Schema：</span>
              <span
                class="px-2 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold"
              >
                {{ currentSchemaId }}
              </span>
            </div>
            <button
              @click="openCreateSection"
              class="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 flex items-center justify-center gap-2 whitespace-nowrap"
            >
              <span class="text-lg">＋</span>
              新增章節
            </button>
          </div>
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
                            @click="startEditField(section, field)"
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

                <!-- Create field form (inline after table) -->
                <div
                  v-if="
                    editingField &&
                    editingField.section_id === section.id &&
                    !editingField.id
                  "
                  class="border-t-2 border-indigo-200 bg-gradient-to-r from-indigo-50 via-blue-50 to-indigo-50 overflow-x-auto"
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

              <p v-else class="text-xs text-gray-400 italic">
                尚無欄位，請點擊「新增欄位」開始建立。
              </p>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-10 text-gray-500">
          目前尚未建立任何章節，請先點擊右上角「新增章節」。
        </div>
      </div>
    </div>
  </ClientOnly>
</template>

<script setup>
definePageMeta({
  middleware: "auth",
});

// SEO
useHead({
  title: "動態欄位配置中心 - AI 計畫書平台",
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

import { ref, onMounted } from "vue";
import { supabase } from "~/utils/supabaseClient";
import { useNotifications } from "~/composables/useNotifications";
import { useConfirm } from "~/composables/useConfirm";
import { useLoading } from "~/composables/useLoading";

const { success, error: errorNotification } = useNotifications();
const { confirm } = useConfirm();
const { show: showLoading, hide: hideLoading } = useLoading();

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

// Data models (frontend-side)
const currentSchemaId = ref("default");
const sections = ref([]); // [{ id, schema_id, section_key, title, order, fields: [...] }]

const editingSection = ref(null);
const editingField = ref(null);

// Drag-and-drop state
const draggedSectionIndex = ref(null);
const dragOverSectionIndex = ref(null);
const draggedFieldIndex = ref(null);
const dragOverFieldSectionId = ref(null);
const dragOverFieldIndex = ref(null);

function cloneSection(section) {
  return {
    id: section.id,
    schema_id: section.schema_id,
    section_key: section.section_key,
    title: section.title,
    order: section.order,
  };
}

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

function isEditingField(field) {
  return (
    editingField.value &&
    editingField.id !== null &&
    editingField.value.id === field.id
  );
}

// --- API helpers ---
async function getAuthToken() {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) throw new Error("請先登入");
  return session.access_token;
}

async function fetchSections() {
  try {
    showLoading("載入章節與欄位...");
    const token = await getAuthToken();
    const response = await fetch(
      `${API_BASE_URL}/dynamic-sections?schema_id=${encodeURIComponent(
        currentSchemaId.value
      )}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    if (!response.ok) throw new Error(await response.text());
    const data = await response.json();
    sections.value = data;
  } catch (e) {
    console.error(e);
    errorNotification("載入失敗：" + e.message);
  } finally {
    hideLoading();
  }
}

// --- Section CRUD ---
function openCreateSection() {
  const maxOrder = sections.value.reduce(
    (max, s) => (s.order > max ? s.order : max),
    0
  );
  editingSection.value = {
    id: null,
    schema_id: currentSchemaId.value,
    section_key: "",
    title: "",
    order: maxOrder + 1,
  };
}

function startEditSection(section) {
  editingSection.value = cloneSection(section);
}

function cancelEditSection() {
  editingSection.value = null;
}

async function saveSection(localSection) {
  try {
    if (!localSection.section_key || !localSection.title) {
      throw new Error("章節 key 與標題不可為空");
    }

    const token = await getAuthToken();
    const isCreate = !localSection.id;
    const url = isCreate
      ? `${API_BASE_URL}/dynamic-sections/sections`
      : `${API_BASE_URL}/dynamic-sections/sections/${localSection.id}`;

    const method = isCreate ? "POST" : "PUT";

    const response = await fetch(url, {
      method,
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        schema_id: currentSchemaId.value,
        section_key: localSection.section_key,
        title: localSection.title,
        order: localSection.order || 1,
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
    const token = await getAuthToken();
    const response = await fetch(
      `${API_BASE_URL}/dynamic-sections/sections/${section.id}`,
      {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
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

// --- Field CRUD ---
function openCreateField(section) {
  const maxOrder = section.fields.reduce(
    (max, f) => (f.order > max ? f.order : max),
    0
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

function startEditField(section, field) {
  editingField.value = cloneField(field);
}

function cancelEditField() {
  editingField.value = null;
}

async function saveField(localField) {
  try {
    if (!localField.field_key || !localField.title) {
      throw new Error("欄位 key 與標題不可為空");
    }

    const token = await getAuthToken();
    const isCreate = !localField.id;
    const url = isCreate
      ? `${API_BASE_URL}/dynamic-sections/fields`
      : `${API_BASE_URL}/dynamic-sections/fields/${localField.id}`;
    const method = isCreate ? "POST" : "PUT";

    const response = await fetch(url, {
      method,
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
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
    const token = await getAuthToken();
    const response = await fetch(
      `${API_BASE_URL}/dynamic-sections/fields/${field.id}`,
      {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
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

// --- Drag-and-drop for sections ---
function startDragSection(index, event) {
  draggedSectionIndex.value = index;
  event.dataTransfer.effectAllowed = "move";
}

function dragOverSection(index, event) {
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  dragOverSectionIndex.value = index;
}

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

  // Recalculate order for all affected sections
  const sectionIdsToUpdate = sections.value.map((s, idx) => ({
    id: s.id,
    oldOrder: s.order,
    newOrder: idx + 1,
  }));

  draggedSectionIndex.value = null;

  // Update API for all sections that changed order
  try {
    const token = await getAuthToken();
    for (const section of sections.value) {
      section.order = sections.value.indexOf(section) + 1;
      const response = await fetch(
        `${API_BASE_URL}/dynamic-sections/sections/${section.id}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            schema_id: section.schema_id,
            section_key: section.section_key,
            title: section.title,
            order: section.order,
          }),
        }
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

function dragEndSection() {
  draggedSectionIndex.value = null;
  dragOverSectionIndex.value = null;
}

// --- Drag-and-drop for fields ---
function startDragField(sectionId, fieldIndex, event) {
  draggedFieldIndex.value = fieldIndex;
  dragOverFieldSectionId.value = sectionId;
  event.dataTransfer.effectAllowed = "move";
}

function dragOverField(sectionId, fieldIndex, event) {
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  dragOverFieldSectionId.value = sectionId;
  dragOverFieldIndex.value = fieldIndex;
}

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
    const token = await getAuthToken();
    for (let i = 0; i < section.fields.length; i++) {
      section.fields[i].order = i + 1;
      const response = await fetch(
        `${API_BASE_URL}/dynamic-sections/fields/${section.fields[i].id}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            section_id: section.fields[i].section_id,
            field_key: section.fields[i].field_key,
            title: section.fields[i].title,
            description: section.fields[i].description || "",
            order: section.fields[i].order,
          }),
        }
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

function dragEndField() {
  draggedFieldIndex.value = null;
  dragOverFieldSectionId.value = null;
  dragOverFieldIndex.value = null;
}

// --- Lifecycle ---
onMounted(async () => {
  // 僅允許內部人員存取
  const { checkIsInternal } = useInternalCheck();
  const isInternal = await checkIsInternal();
  if (!isInternal) {
    window.location.href = "/";
    return;
  }

  await fetchSections();
});
</script>
