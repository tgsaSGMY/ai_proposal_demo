<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="isVisible"
        class="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/60 px-4 py-6 backdrop-blur"
      >
        <div
          class="relative flex w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
        >
          <header
            class="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 px-6 py-5"
          >
            <div>
              <p
                class="text-xs font-semibold uppercase tracking-[0.35em] text-rose-400"
              >
                Section Editor
              </p>
              <h3 class="text-xl font-semibold text-slate-900">
                {{ template?.name || "尚未選擇模板" }}
              </h3>
              <p class="text-xs text-slate-500">
                Grant: {{ template?.grant_id || "—" }} · Template ID:
                {{ template?.id || "—" }}
              </p>
            </div>
            <button
              type="button"
              class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"
              @click="handleClose"
            >
              關閉
            </button>
          </header>

          <div class="grid gap-0 md:grid-cols-5">
            <section
              class="md:col-span-2 border-b border-slate-100 md:border-b-0 md:border-r"
            >
              <div
                class="flex items-center justify-between border-b border-slate-100 px-6 py-4"
              >
                <div>
                  <h4 class="text-sm font-semibold text-slate-900">章節列表</h4>
                  <p class="text-xs text-slate-500">
                    對應此模板的所有章節與順序
                  </p>
                </div>
                <button
                  type="button"
                  class="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800"
                  @click="() => startCreate()"
                >
                  新增章節
                </button>
              </div>

              <div class="max-h-[28rem] space-y-3 overflow-y-auto p-6">
                <div
                  v-if="loading"
                  class="flex items-center justify-center py-10 text-sm text-slate-500"
                >
                  載入章節中...
                </div>
                <div
                  v-else-if="!localSections.length"
                  class="rounded-xl border border-dashed border-slate-200 py-10 text-center text-xs text-slate-400"
                >
                  尚未建立章節，點擊「新增章節」建立第一個。
                </div>
                <ul v-else class="space-y-3" @dragover.prevent>
                  <li
                    v-for="section in localSections"
                    :key="section.id"
                    :class="[
                      'rounded-xl border px-3 py-3 text-sm shadow-sm transition',
                      section.id === formState.originalId
                        ? 'border-indigo-500 bg-indigo-50/70'
                        : 'border-slate-200 bg-white',
                      dragOverSectionId === section.id
                        ? 'ring-2 ring-indigo-300'
                        : '',
                      !saving && !loading
                        ? 'cursor-grab active:cursor-grabbing'
                        : 'cursor-default',
                    ]"
                    :draggable="!saving && !loading"
                    @dragstart="(event) => handleDragStart(section, event)"
                    @dragover="(event) => handleDragOver(section, event)"
                    @drop="(event) => handleDrop(section, event)"
                    @dragend="handleDragEnd"
                  >
                    <div class="flex items-start justify-between gap-3">
                      <div>
                        <div class="flex items-center gap-2">
                          <span class="text-xs font-semibold text-slate-500"
                            >#{{ section.order ?? "-" }}</span
                          >
                          <p class="font-semibold text-slate-900">
                            {{ section.name }}
                          </p>
                        </div>
                        <p class="text-xs text-slate-500">
                          ID: {{ section.id }}
                        </p>
                      </div>
                      <div class="flex gap-2">
                        <button
                          type="button"
                          class="rounded-md border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                          @click="selectSection(section)"
                        >
                          編輯
                        </button>
                        <button
                          type="button"
                          class="rounded-md border border-transparent px-2 py-1 text-xs font-semibold text-rose-600 hover:bg-rose-50"
                          :disabled="saving"
                          @click="emitDelete(section)"
                        >
                          刪除
                        </button>
                      </div>
                    </div>
                    <!-- <p class="mt-2 text-xs text-slate-500">
                      {{ jsonPreview(section.json_schema) }}
                    </p> -->
                  </li>
                </ul>
              </div>
            </section>

            <section class="md:col-span-3 space-y-4 px-6 py-6 overflow-y-auto">
              <div>
                <h4 class="text-sm font-semibold text-slate-900">
                  {{ isEditing ? "編輯章節" : "新增章節" }}
                </h4>
                <p class="text-xs text-slate-500">
                  可調整章節名稱、順序與 JSON
                  Schema；送出後資料會立即套用至計畫編輯器。
                </p>
              </div>

              <form
                class="space-y-4 max-h-96 overflow-y-auto"
                @submit.prevent="handleSave"
              >
                <div class="grid gap-4 sm:grid-cols-2">
                  <label class="text-xs font-semibold text-slate-600">
                    Section ID
                    <input
                      v-model="formState.id"
                      type="text"
                      class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:border-rose-400 focus:ring-rose-200"
                      placeholder="company_overview"
                      :disabled="saving || isEditing"
                    />
                  </label>
                  <label class="text-xs font-semibold text-slate-600">
                    順序 (Order)
                    <input
                      v-model.number="formState.order"
                      type="number"
                      class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:border-rose-400 focus:ring-rose-200"
                      min="0"
                      disabled
                    />
                  </label>
                </div>

                <label class="text-xs font-semibold text-slate-600">
                  顯示名稱
                  <input
                    v-model="formState.name"
                    type="text"
                    class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:border-rose-400 focus:ring-rose-200"
                    placeholder="壹、公司概況"
                    :disabled="saving"
                  />
                </label>

                <div>
                  <p class="text-xs font-semibold text-slate-600">章節結構</p>
                  <div
                    class="mt-2 rounded-2xl border border-slate-200 bg-slate-50/60 p-4"
                  >
                    <SchemaStructureEditor
                      v-model="formState.schemaTree"
                      v-model:title="formState.schemaTitle"
                      v-model:description="formState.schemaDescription"
                      :disabled="saving"
                    />
                  </div>
                </div>

                <p v-if="formError" class="text-xs font-semibold text-rose-600">
                  {{ formError }}
                </p>

                <div class="flex flex-wrap items-center justify-between gap-3">
                  <button
                    v-if="isEditing"
                    type="button"
                    class="text-xs font-semibold text-slate-500 hover:text-slate-700"
                    @click="() => startCreate(false)"
                  >
                    轉為新增其他章節
                  </button>
                  <div class="ml-auto flex gap-2">
                    <button
                      type="button"
                      class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                      @click="handleClose"
                    >
                      取消
                    </button>
                    <button
                      type="submit"
                      class="rounded-xl bg-rose-500 px-5 py-2 text-sm font-semibold text-white hover:bg-rose-600 disabled:opacity-60"
                      :disabled="saving"
                    >
                      {{ isEditing ? "更新章節" : "新增章節" }}
                    </button>
                  </div>
                </div>
              </form>
            </section>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { PropType } from "vue";
import SchemaStructureEditor from "./SchemaStructureEditor.vue";
import type { SchemaNode } from "./schema-tree";
import {
  buildSchemaFromEditorState,
  createEmptySchemaState,
  parseSchemaToEditorState,
  validateSchemaNodes,
} from "./schema-tree";

interface TemplateSummary {
  id: string;
  grant_id: string;
  name: string;
  [key: string]: any;
}

interface SectionRecord {
  id: string;
  name: string;
  order?: number | null;
  json_schema?: Record<string, any> | null;
  template_id: string;
  grant_id: string;
  [key: string]: any;
}

interface SectionFormState {
  id: string;
  name: string;
  order: number | null;
  schemaTree: SchemaNode[];
  schemaTitle: string;
  schemaDescription: string;
  originalId: string | null;
}

interface SectionMutationPayload {
  id: string;
  name: string;
  order: number;
  json_schema: Record<string, any> | null;
  originalId?: string | null;
}

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false,
  },
  template: {
    type: Object as PropType<TemplateSummary | null>,
    default: null,
  },
  sections: {
    type: Array as PropType<SectionRecord[]>,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  saving: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits<{
  (e: "close"): void;
  (e: "create", payload: SectionMutationPayload): void;
  (e: "update", payload: SectionMutationPayload): void;
  (e: "delete", section: SectionRecord): void;
  (e: "reorder", sections: SectionRecord[]): void;
}>();

const localSections = ref<SectionRecord[]>([]);
const formError = ref("");
const formState = ref<SectionFormState>(getEmptyForm());
const shouldAutoSelectFirst = ref(false);

const isEditing = computed(() => Boolean(formState.value.originalId));
const draggedSectionId = ref<string | null>(null);
const dragOverSectionId = ref<string | null>(null);

watch(
  () => props.sections,
  (sections) => {
    const sorted = [...(sections || [])]
      .sort((a, b) => {
        const orderA = a.order ?? 0;
        const orderB = b.order ?? 0;
        if (orderA !== orderB) {
          return orderA - orderB;
        }
        return a.name.localeCompare(b.name);
      })
      .map((section) => ({ ...section }));
    localSections.value = sorted;
    resetDragState();

    if (props.isVisible && shouldAutoSelectFirst.value) {
      initializeFormForCurrentSections();
    }
  },
  { immediate: true, deep: true },
);

watch(
  () => props.isVisible,
  (visible) => {
    if (visible) {
      shouldAutoSelectFirst.value = true;
      initializeFormForCurrentSections();
    } else {
      shouldAutoSelectFirst.value = false;
      resetForm();
      resetDragState();
    }
  },
);

function getEmptyForm(): SectionFormState {
  const schemaState = createEmptySchemaState();
  return {
    id: "",
    name: "",
    order: 0,
    schemaTree: schemaState.nodes,
    schemaTitle: schemaState.title,
    schemaDescription: schemaState.description,
    originalId: null,
  };
}

function initializeFormForCurrentSections(): void {
  if (!shouldAutoSelectFirst.value) {
    return;
  }

  const firstSection = localSections.value[0];
  if (firstSection) {
    selectSection(firstSection);
  } else {
    startCreate(true);
  }
}

function startCreate(preserveAutoSelect = false): void {
  formError.value = "";
  if (!preserveAutoSelect) {
    shouldAutoSelectFirst.value = false;
  }
  const lastSection = localSections.value.length
    ? localSections.value[localSections.value.length - 1]
    : null;
  const baseOrder =
    typeof lastSection?.order === "number"
      ? lastSection.order
      : localSections.value.length;
  const suggestedOrder = baseOrder + 1;
  const schemaState = createEmptySchemaState();
  formState.value = {
    id: "",
    name: "",
    order: suggestedOrder,
    schemaTree: schemaState.nodes,
    schemaTitle: "",
    schemaDescription: "",
    originalId: null,
  };
}

function selectSection(section: SectionRecord): void {
  formError.value = "";
  shouldAutoSelectFirst.value = false;
  const schemaState = parseSchemaToEditorState(section.json_schema ?? null);
  formState.value = {
    id: section.id,
    name: section.name,
    order: section.order ?? 0,
    schemaTree: schemaState.nodes,
    schemaTitle: schemaState.title || section.name,
    schemaDescription: schemaState.description || "",
    originalId: section.id,
  };
}

function handleSave(): void {
  formError.value = "";
  const id = formState.value.id.trim();
  const name = formState.value.name.trim();
  if (!id || !name) {
    formError.value = "請填寫 Section ID 與顯示名稱";
    return;
  }

  const orderValue = Number(formState.value.order ?? 0);
  if (!Number.isFinite(orderValue)) {
    formError.value = "順序必須為數字";
    return;
  }

  const schemaError = validateSchemaNodes(formState.value.schemaTree);
  if (schemaError) {
    formError.value = schemaError;
    return;
  }

  const schemaPayload = buildSchemaFromEditorState(formState.value.schemaTree, {
    id,
    title: formState.value.schemaTitle || name,
    description: formState.value.schemaDescription,
  });

  const payload: SectionMutationPayload = {
    id,
    name,
    order: orderValue,
    json_schema: schemaPayload,
    originalId: formState.value.originalId,
  };

  if (isEditing.value) {
    emit("update", payload);
  } else {
    emit("create", payload);
  }
}

function emitDelete(section: SectionRecord): void {
  if (props.saving) {
    return;
  }
  const confirmed = window.confirm(`確定要刪除章節「${section.name}」嗎？`);
  if (!confirmed) {
    return;
  }
  emit("delete", section);
}

function jsonPreview(schema?: Record<string, any> | null): string {
  if (!schema) {
    return "尚未定義 JSON Schema";
  }
  const text = JSON.stringify(schema);
  return text.length > 120 ? `${text.slice(0, 120)}...` : text;
}

function handleClose(): void {
  shouldAutoSelectFirst.value = false;
  resetForm();
  emit("close");
}

function resetForm(): void {
  formError.value = "";
  formState.value = getEmptyForm();
}

function resetDragState(): void {
  draggedSectionId.value = null;
  dragOverSectionId.value = null;
}

function handleDragStart(section: SectionRecord, event: DragEvent): void {
  if (props.saving || props.loading) {
    event.preventDefault();
    return;
  }
  draggedSectionId.value = section.id;
  event.dataTransfer?.setData("text/plain", section.id);
}

function handleDragOver(section: SectionRecord, event: DragEvent): void {
  if (!draggedSectionId.value || props.saving || props.loading) {
    return;
  }
  event.preventDefault();
  if (dragOverSectionId.value !== section.id) {
    dragOverSectionId.value = section.id;
  }
}

function handleDragEnd(): void {
  resetDragState();
}

function handleDrop(section: SectionRecord, event: DragEvent): void {
  if (!draggedSectionId.value || props.saving || props.loading) {
    return;
  }
  event.preventDefault();

  const sourceId = draggedSectionId.value;
  resetDragState();
  if (sourceId === section.id) {
    return;
  }

  const previousOrderMap = new Map(
    localSections.value.map((item, index) => [
      item.id,
      typeof item.order === "number" ? item.order : index + 1,
    ]),
  );

  const orderedList = localSections.value.map((item) => ({ ...item }));
  const fromIndex = orderedList.findIndex((item) => item.id === sourceId);
  const toIndex = orderedList.findIndex((item) => item.id === section.id);
  if (fromIndex === -1 || toIndex === -1) {
    return;
  }

  const [movedSection] = orderedList.splice(fromIndex, 1);
  if (!movedSection) {
    return;
  }
  orderedList.splice(toIndex, 0, movedSection);

  const updatedList = orderedList.map((item, idx) => ({
    ...item,
    order: idx + 1,
  }));

  localSections.value = updatedList;

  const changedSections = updatedList.filter(
    (item) => previousOrderMap.get(item.id) !== item.order,
  );

  if (changedSections.length) {
    emit(
      "reorder",
      changedSections.map((item) => ({ ...item })),
    );
  }
}

defineOptions({ name: "SectionEditorModal" });
</script>
