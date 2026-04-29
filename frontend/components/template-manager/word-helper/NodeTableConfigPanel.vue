<!-- 用途：設定表格節點欄位勾選、列標題與表格轉置行為。 -->
<template>
  <div class="space-y-3 rounded-xl bg-slate-50 p-3">
    <label class="flex items-center gap-2 text-sm text-slate-600">
      <input
        :checked="node.table?.customHeaders"
        type="checkbox"
        class="h-4 w-4 rounded border-slate-300"
        @change="handleCustomHeadersChange"
      />
      啟用自定義列標題
    </label>
    <label class="flex items-center gap-2 text-sm text-slate-600">
      <input
        :checked="node.table?.transpose"
        type="checkbox"
        class="h-4 w-4 rounded border-slate-300"
        @change="handleTransposeChange"
      />
      倒置表格（列↔欄互換）
    </label>

    <div
      v-if="node.table?.customHeaders && node.table?.columns?.length"
      class="space-y-2 border-t border-slate-200 pt-3"
    >
      <p class="text-xs font-semibold text-slate-500">自定義列標題</p>
      <div class="space-y-2">
        <div
          v-for="(column, colIndex) in node.table.columns"
          :key="column.key"
          class="flex items-center gap-2"
        >
          <input
            :value="column.label"
            type="text"
            class="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm"
            :class="!isColumnValid(column.key) ? 'border-red-300 bg-red-50 text-red-700' : ''"
            :placeholder="`列 ${colIndex + 1} 標題`"
            @input="handleColumnLabelChange(colIndex, $event)"
          />
          <span class="text-xs whitespace-nowrap truncate max-w-[120px] inline-block align-middle" :class="!isColumnValid(column.key) ? 'text-red-500 font-semibold' : 'text-slate-500'"
            :title="column.key"
            >({{ column.key }})</span
          >
          <span v-if="!isColumnValid(column.key)" class="text-[10px] text-red-600 bg-red-100 px-1 rounded border border-red-200 whitespace-nowrap" title="此欄位已不存在於 Schema 中">⚠️ 失效</span>
          <div class="flex items-center gap-1">
            <button
              type="button"
              class="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-600 disabled:opacity-40"
              :disabled="colIndex === 0"
              @click="moveTableColumn(colIndex, 'up')"
              title="上移列"
            >
              ↑
            </button>
            <button
              type="button"
              class="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-600 disabled:opacity-40"
              :disabled="colIndex === node.table.columns.length - 1"
              @click="moveTableColumn(colIndex, 'down')"
              title="下移列"
            >
              ↓
            </button>
            <button
              type="button"
              class="rounded-lg border border-red-200 bg-red-50 px-2 py-1 text-xs text-red-600 hover:bg-red-100"
              @click="removeColumn(column.key)"
              title="刪除列"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="invalidColumns.length > 0 && !node.table?.customHeaders" class="mt-3 p-3 bg-red-50 border border-red-200 rounded-xl">
      <p class="text-xs font-bold text-red-600 mb-2 flex items-center gap-1">
        <span>⚠️</span> 發現失效欄位 (已從 Schema 中移除)
      </p>
      <div class="flex flex-wrap gap-2">
        <div v-for="col in invalidColumns" :key="col.key" class="flex items-center gap-1 bg-white border border-red-200 rounded px-2 py-1 text-xs text-red-600 shadow-sm">
          <span class="line-through truncate max-w-[150px] inline-block align-middle" :title="col.label || col.key">{{ col.label || col.key }}</span>
          <button type="button" class="ml-1 text-red-400 hover:text-red-700 font-bold" @click="removeColumn(col.key)" title="移除失效欄位">✕</button>
        </div>
      </div>
    </div>

    <div>
      <p class="text-xs font-semibold text-slate-500">欄位內容</p>
      <div class="mt-2 grid gap-2 md:grid-cols-2">
        <label
          v-for="option in getNodeColumnCandidates(node)"
          :key="option.key"
          class="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm min-w-0 overflow-hidden"
        >
          <input
            type="checkbox"
            :checked="
              node.table?.columns?.some((column) => column.key === option.key)
            "
            class="h-4 w-4 shrink-0 rounded border-slate-300"
            @change="handleColumnToggle(option, $event)"
          />
          <span class="truncate" :title="`${option.label} (${option.key})`">{{ option.label }} ({{ option.key }})</span>
        </label>
      </div>
      <p
        v-if="!getNodeColumnCandidates(node).length"
        class="text-xs text-slate-400 mt-2"
      >
        無可用欄位，請確認章節或資料來源設定。
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { createWordSchemaPathHelpers } from "~/composables/template-manager/useWordSchemaPath";
import type { WordDocumentNode, WordTableColumn } from "~/types/wordExport";

// Schema 欄位結構（供欄位候選分析）。
interface SchemaField {
  title?: string;
  type?: string;
  properties?: Record<string, SchemaField>;
  items?: { properties?: Record<string, SchemaField> };
}

// 章節資料來源模型。
interface SectionRecord {
  id: string;
  name: string;
  json_schema?: { properties?: Record<string, SchemaField> } | null;
}

// 接收節點與章節資料。
const props = defineProps<{
  node: WordDocumentNode;
  sections: SectionRecord[];
}>();

// 對外派發節點更新事件。
const emit = defineEmits<{
  (
    e: "update",
    nodeId: string,
    updater: (node: WordDocumentNode) => void,
  ): void;
}>();

// 依章節與 dataPath 取得可用欄位候選。
const { getColumnCandidates } = createWordSchemaPathHelpers(
  () => props.sections,
);

// 取得目前節點可勾選的表格欄位。
function getNodeColumnCandidates(node: WordDocumentNode) {
  if (!node.sectionId) return [];
  return getColumnCandidates(node.sectionId, node.dataPath);
}

const validColumnKeys = computed(() => {
  return getNodeColumnCandidates(props.node).map(c => c.key);
});

function isColumnValid(key: string) {
  return validColumnKeys.value.includes(key);
}

const invalidColumns = computed(() => {
  if (!props.node.table?.columns) return [];
  return props.node.table.columns.filter(col => !isColumnValid(col.key));
});

// 確保節點具有 table 與 columns 結構。
function ensureTableConfig(node: WordDocumentNode) {
  if (!node.table) {
    node.table = { columns: [] };
  }
  if (!node.table.columns) {
    node.table.columns = [];
  }
  return node.table;
}

// 切換是否使用自訂欄位標題。
function handleCustomHeadersChange(event: Event) {
  const target = event.target as HTMLInputElement;
  emit("update", props.node.id, (node) => {
    ensureTableConfig(node).customHeaders = target.checked;
  });
}

// 切換是否轉置表格。
function handleTransposeChange(event: Event) {
  const target = event.target as HTMLInputElement;
  emit("update", props.node.id, (node) => {
    ensureTableConfig(node).transpose = target.checked;
  });
}

// 更新指定欄位顯示名稱。
function handleColumnLabelChange(colIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  emit("update", props.node.id, (node) => {
    if (node.table?.columns?.[colIndex]) {
      node.table.columns[colIndex].label = target.value;
    }
  });
}

// 調整欄位順序（上移/下移）。
function moveTableColumn(columnIndex: number, direction: "up" | "down") {
  emit("update", props.node.id, (node) => {
    if (!node.table?.columns) return;
    const columns = node.table.columns;
    const newIndex = direction === "up" ? columnIndex - 1 : columnIndex + 1;
    if (newIndex < 0 || newIndex >= columns.length) return;
    const current = columns[columnIndex];
    const target = columns[newIndex];
    if (!current || !target) return;
    columns[columnIndex] = target;
    columns[newIndex] = current;
  });
}

// 移除單個欄位（不論是自定義標題還是一般勾選）
function removeColumn(keyToRemove: string) {
  emit("update", props.node.id, (node) => {
    const table = ensureTableConfig(node);
    table.columns = table.columns.filter((col) => col.key !== keyToRemove);
  });
}

// 勾選/取消欄位，更新表格 columns 清單。
function handleColumnToggle(option: WordTableColumn, event: Event) {
  const target = event.target as HTMLInputElement;
  emit("update", props.node.id, (node) => {
    const table = ensureTableConfig(node);
    if (target.checked) {
      if (!table.columns.find((col) => col.key === option.key)) {
        table.columns.push({ ...option });
      }
    } else {
      table.columns = table.columns.filter((col) => col.key !== option.key);
    }
  });
}
</script>
