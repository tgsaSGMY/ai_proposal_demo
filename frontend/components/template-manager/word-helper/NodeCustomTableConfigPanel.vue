<template>
  <div class="space-y-4 rounded-xl bg-slate-50 p-3">
    <div class="grid gap-3 md:grid-cols-2">
      <label class="space-y-1 text-sm text-slate-600">
        列數 (1-20)
        <input
          :value="node.customTable?.rows ?? 1"
          type="number"
          min="1"
          max="20"
          class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
          @change="handleDimensionChange('rows', $event)"
        />
      </label>
      <label class="space-y-1 text-sm text-slate-600">
        欄數 (1-20)
        <input
          :value="node.customTable?.cols ?? 1"
          type="number"
          min="1"
          max="20"
          class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
          @change="handleDimensionChange('cols', $event)"
        />
      </label>
    </div>

    <div class="space-y-3 max-h-[28rem] overflow-y-auto overflow-x-auto pr-1">
      <div
        v-for="rowIndex in node.customTable?.rows || 0"
        :key="`custom-row-${node.id}-${rowIndex}`"
        class="space-y-2"
      >
        <p class="text-xs font-semibold text-slate-500">第 {{ rowIndex }} 列</p>
        <div
          class="grid gap-3"
          :style="{
            gridTemplateColumns:
              'repeat(' +
              (node.customTable?.cols || 1) +
              ', minmax(220px, 1fr))',
          }"
        >
          <div
            v-for="cell in getCustomTableRowCells(node, rowIndex - 1)"
            :key="cell.id"
            class="min-w-[220px] rounded-xl border border-slate-200 p-3 space-y-2 bg-white"
          >
            <p class="text-xs font-semibold text-slate-500">
              儲存格 {{ rowIndex }}-{{ cell.col + 1 }}
            </p>
            <div class="space-y-2">
              <div
                v-for="(content, contentIndex) in cell.contents"
                :key="content.id"
                class="rounded-lg border border-slate-200 p-2 space-y-2"
              >
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <div class="flex items-center gap-2 text-xs text-slate-500">
                    <span>片段 {{ contentIndex + 1 }}</span>
                    <select
                      v-model="content.type"
                      class="rounded-lg border border-slate-200 px-2 py-1 text-xs"
                      @change="
                        handleCustomTableCellContentTypeChange(cell, content)
                      "
                    >
                      <option value="text">自訂文字</option>
                      <option value="field">資料欄位</option>
                    </select>
                  </div>
                  <div class="flex items-center gap-1">
                    <button
                      type="button"
                      class="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-600 disabled:opacity-40"
                      :disabled="contentIndex === 0"
                      @click="
                        moveCustomTableCellContent(cell, contentIndex, 'up')
                      "
                    >
                      ↑
                    </button>
                    <button
                      type="button"
                      class="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-600 disabled:opacity-40"
                      :disabled="
                        contentIndex === (cell.contents?.length || 0) - 1
                      "
                      @click="
                        moveCustomTableCellContent(cell, contentIndex, 'down')
                      "
                    >
                      ↓
                    </button>
                    <button
                      type="button"
                      class="rounded-lg border border-rose-200 px-2 py-1 text-xs text-rose-600 disabled:opacity-40"
                      :disabled="(cell.contents?.length || 0) === 1"
                      @click="removeCustomTableCellContent(cell, content.id)"
                    >
                      刪除
                    </button>
                  </div>
                </div>
                <div v-if="content.type === 'text'" class="space-y-1">
                  <span class="text-xs text-slate-500">顯示文字</span>
                  <input
                    v-model="content.text"
                    type="text"
                    class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                    placeholder="輸入內容"
                    @input="syncLegacyCustomTableCellFields(cell)"
                  />
                </div>
                <div v-else class="space-y-1">
                  <span class="text-xs text-slate-500">資料欄位</span>
                  <select
                    v-model="content.dataPath"
                    class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                    @change="syncLegacyCustomTableCellFields(cell)"
                  >
                    <option value="">選擇欄位</option>
                    <option
                      v-for="option in getNodeColumnCandidates(node)"
                      :key="option.key"
                      :value="option.key"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="flex flex-wrap gap-2 pt-1">
                <button
                  type="button"
                  class="rounded-lg border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50"
                  @click="addCustomTableCellContent(cell, 'text')"
                >
                  + 新增文字片段
                </button>
                <button
                  type="button"
                  class="rounded-lg border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                  :disabled="!node.sectionId"
                  @click="addCustomTableCellContent(cell, 'field')"
                >
                  + 新增資料片段
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { createCustomTableNodeHelpers } from "~/composables/template-manager/useCustomTableNode";
import { createWordSchemaPathHelpers } from "~/composables/template-manager/useWordSchemaPath";
import type { WordDocumentNode } from "~/types/wordExport";

interface SchemaField {
  title?: string;
  type?: string;
  properties?: Record<string, SchemaField>;
  items?: { properties?: Record<string, SchemaField> };
}

interface SectionRecord {
  id: string;
  name: string;
  json_schema?: { properties?: Record<string, SchemaField> } | null;
}

const props = defineProps<{
  node: WordDocumentNode;
  sections: SectionRecord[];
}>();

const emit = defineEmits<{
  (
    e: "update",
    nodeId: string,
    updater: (node: WordDocumentNode) => void,
  ): void;
}>();

const { getColumnCandidates } = createWordSchemaPathHelpers(
  () => props.sections,
);

const {
  syncLegacyCustomTableCellFields,
  normalizeCustomTableCells,
  ensureCustomTableConfig,
  getCustomTableRowCells,
  addCustomTableCellContent,
  removeCustomTableCellContent,
  moveCustomTableCellContent,
  handleCustomTableCellContentTypeChange,
} = createCustomTableNodeHelpers(generateNodeId);

function generateNodeId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `node_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function getNodeColumnCandidates(node: WordDocumentNode) {
  if (!node.sectionId) return [];
  return getColumnCandidates(node.sectionId, node.dataPath);
}

function handleDimensionChange(dimension: "rows" | "cols", event: Event) {
  const raw = Number((event.target as HTMLInputElement | null)?.value || 1);
  const sanitized = Number.isFinite(raw) ? Math.floor(raw) : 1;
  emit("update", props.node.id, (node) => {
    const customTable = ensureCustomTableConfig(node);
    const clamped = Math.min(Math.max(sanitized, 1), 20);
    customTable[dimension] = clamped;
    normalizeCustomTableCells(customTable);
  });
}
</script>
