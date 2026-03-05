<template>
  <div
    class="recursive-node-editor space-y-3"
    :style="{ marginLeft: `${level * 12}px` }"
  >
    <!-- 當前節點的編輯器 -->
    <div
      class="rounded-lg border border-slate-200 p-3 bg-white space-y-3"
      :class="{ 'border-l-4 border-l-blue-400': level > 0 }"
    >
      <div class="flex flex-wrap items-center justify-between gap-3">
        <label class="flex-1 space-y-1 text-sm text-slate-600">
          <span class="text-xs font-semibold text-slate-500"> 節點類型 </span>
          <select
            :value="node.type"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
            @change="handleTypeChange"
          >
            <option
              v-for="option in nodeTypeOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </label>
        <div class="flex items-center gap-2 text-xs">
          <button
            type="button"
            class="rounded-lg border border-rose-200 px-2 py-1 text-rose-600 hover:bg-rose-50"
            @click="$emit('remove', node.id)"
          >
            刪除
          </button>
        </div>
      </div>

      <div
        v-if="shouldShowNodeLabel(node)"
        class="space-y-1 text-sm text-slate-600"
      >
        <span class="text-xs font-semibold text-slate-500">節點標題</span>
        <input
          :value="node.label"
          type="text"
          class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
          placeholder="例如：標題"
          @input="handleLabelChange"
        />
      </div>

      <div v-if="shouldShowSectionSelectors(node)">
        <NodeDataBindingPanel
          :node="node"
          :sections="sections"
          :section-options="sectionOptions"
          @update="handleDataBindingUpdate"
        />
      </div>

      <div
        v-if="shouldShowTemplateInput(node)"
        class="space-y-1 text-sm text-slate-600"
      >
        <span class="text-xs font-semibold text-slate-500">自訂文字</span>
        <textarea
          :value="node.template"
          rows="3"
          class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
          placeholder="輸入要顯示的內容"
          @input="handleTemplateChange"
        />
      </div>

      <NodeTextStyleToggle
        v-if="node.type === 'paragraph' || node.type === 'customText'"
        :node="node"
        @update="handleChildPanelUpdate"
      />

      <div
        v-if="node.type === 'paragraph'"
        class="flex flex-wrap items-center gap-2 text-sm text-slate-600"
      >
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            class="h-4 w-4 rounded border-slate-300"
            :checked="node.paragraphNumbering === true"
            @change="handleParagraphNumberingToggle"
          />
          使用編號
        </label>
        <select
          v-if="node.paragraphNumbering"
          :value="node.paragraphNumberStyle"
          class="rounded-xl border border-slate-200 px-3 py-1 text-xs"
          @change="handleParagraphNumberStyleChange"
        >
          <option
            v-for="option in listStyleOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </div>

      <!-- 表格配置 -->
      <NodeTableConfigPanel
        v-if="node.type === 'table'"
        :node="node"
        :sections="sections"
        @update="handleTableConfigUpdate"
      />

      <div
        v-if="node.type === 'table' && node.table?.layout === 'fixed'"
        class="space-y-3 border-t border-slate-200 pt-3"
      >
        <p class="text-xs font-semibold text-slate-500">固定布局配置</p>
        <div class="grid grid-cols-2 gap-2">
          <label class="space-y-1 text-sm text-slate-600">
            行數
            <input
              :value="node.table.fixedLayout?.rows || 2"
              type="number"
              min="1"
              class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
              @input="handleFixedLayoutRowsChange"
            />
          </label>
          <label class="space-y-1 text-sm text-slate-600">
            列數
            <input
              :value="node.table.fixedLayout?.cols || 2"
              type="number"
              min="1"
              class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
              @input="handleFixedLayoutColsChange"
            />
          </label>
        </div>

        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <p class="text-xs font-semibold text-slate-500">單元格配置</p>
            <button
              type="button"
              class="text-xs rounded-lg border border-slate-300 px-2 py-1 hover:bg-slate-50"
              @click="handleAddTableCell"
            >
              + 添加單元格
            </button>
          </div>
          <div
            v-for="(cell, cellIndex) in node.table.fixedLayout?.cells"
            :key="cellIndex"
            class="rounded-lg border border-slate-200 p-3 space-y-2 bg-white"
          >
            <div class="grid grid-cols-2 gap-2">
              <input
                :value="cell.row"
                type="number"
                min="0"
                placeholder="行"
                class="rounded-lg border border-slate-200 px-2 py-1 text-sm"
                @input="handleCellRowChange(cellIndex, $event)"
              />
              <input
                :value="cell.col"
                type="number"
                min="0"
                placeholder="列"
                class="rounded-lg border border-slate-200 px-2 py-1 text-sm"
                @input="handleCellColChange(cellIndex, $event)"
              />
            </div>
            <input
              :value="cell.label"
              type="text"
              placeholder="固定標籤（如：Strength 優勢）"
              class="w-full rounded-lg border border-slate-200 px-2 py-1 text-sm"
              @input="handleCellLabelChange(cellIndex, $event)"
            />
            <input
              :value="cell.dataPath"
              type="text"
              placeholder="數據路徑（如：strength.items）"
              class="w-full rounded-lg border border-slate-200 px-2 py-1 text-sm"
              @input="handleCellDataPathChange(cellIndex, $event)"
            />
            <div class="flex items-center justify-between">
              <label class="flex items-center gap-2 text-xs">
                <input
                  :checked="cell.isHeader"
                  type="checkbox"
                  class="h-3 w-3"
                  @change="handleCellIsHeaderChange(cellIndex, $event)"
                />
                標題單元格
              </label>
              <button
                type="button"
                class="text-xs text-rose-600 hover:text-rose-700"
                @click="handleRemoveTableCell(cellIndex)"
              >
                刪除
              </button>
            </div>
          </div>
          <p
            v-if="!node.table.fixedLayout?.cells?.length"
            class="text-xs text-slate-400 text-center py-2"
          >
            尚未配置任何單元格
          </p>
        </div>
      </div>

      <NodeCustomTableConfigPanel
        v-if="node.type === 'customTable'"
        :node="node"
        :sections="sections"
        @update="handleCustomTableConfigUpdate"
      />

      <!-- 清單配置 -->
      <NodeListConfigPanel
        v-if="node.type === 'list' || node.type === 'subHeading'"
        :node="node"
        :list-style-options="listStyleOptions"
        @update="handleChildPanelUpdate"
        @add-child="handlePanelAddChild"
      />
    </div>

    <!-- 遞歸渲染子節點 -->
    <div
      v-if="node.children?.length"
      class="space-y-3"
      :style="{ marginLeft: '12px' }"
    >
      <RecursiveNodeEditor
        v-for="childNode in node.children"
        :key="childNode.id"
        :node="childNode"
        :parent-node-id="node.id"
        :parent-level="
          node.level != null
            ? node.level
            : parentLevel != null
              ? parentLevel + 1
              : 1
        "
        :section-options="sectionOptions"
        :sections="sections"
        :level="level + 1"
        :node-type-options="nodeTypeOptions"
        :list-style-options="listStyleOptions"
        @update="handleChildUpdate"
        @remove="handleChildRemove"
        @add-child="handleAddChild"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from "vue";
import type { PropType } from "vue";
import {
  createCustomTableNodeHelpers,
  resolveNodeScopedPath,
} from "~/composables/template-manager/useCustomTableNode";
import {
  addChildNodeById,
  removeNodeById,
  updateNodeById,
} from "~/composables/template-manager/useWordNodeTree";
import { createWordSchemaPathHelpers } from "~/composables/template-manager/useWordSchemaPath";
import {
  shouldShowNodeLabel,
  shouldShowSectionSelectors,
  shouldShowTemplateInput,
} from "~/composables/template-manager/useWordNodeVisibility";
import NodeCustomTableConfigPanel from "~/components/template-manager/word-helper/NodeCustomTableConfigPanel.vue";
import NodeDataBindingPanel from "~/components/template-manager/word-helper/NodeDataBindingPanel.vue";
import NodeListConfigPanel from "~/components/template-manager/word-helper/NodeListConfigPanel.vue";
import NodeTableConfigPanel from "~/components/template-manager/word-helper/NodeTableConfigPanel.vue";
import NodeTextStyleToggle from "~/components/template-manager/word-helper/NodeTextStyleToggle.vue";
import type {
  WordDocumentNode,
  WordDocumentNodeType,
  WordListStyle,
} from "~/types/wordExport";

interface SectionRecord {
  id: string;
  name: string;
  json_schema?: {
    properties?: Record<string, any>;
  } | null;
}

const props = defineProps({
  node: {
    type: Object as PropType<WordDocumentNode>,
    required: true,
  },
  parentNodeId: {
    type: String,
    required: true,
  },
  parentLevel: {
    type: Number,
    default: 1,
  },
  sectionOptions: {
    type: Array as PropType<Array<{ label: string; value: string }>>,
    required: true,
  },
  sections: {
    type: Array as PropType<SectionRecord[]>,
    required: true,
  },
  level: {
    type: Number,
    default: 0,
  },
  nodeTypeOptions: {
    type: Array as PropType<
      Array<{ label: string; value: WordDocumentNodeType }>
    >,
    required: true,
  },
  listStyleOptions: {
    type: Array as PropType<Array<{ label: string; value: string }>>,
    required: true,
  },
});

const emit = defineEmits<{
  (
    e: "update",
    nodeId: string,
    updater: (node: WordDocumentNode) => void,
  ): void;
  (e: "remove", nodeId: string): void;
  (e: "add-child", nodeId: string): void;
}>();

const { getColumnCandidates } = createWordSchemaPathHelpers(
  () => props.sections,
);

const { syncLegacyCustomTableCellFields, ensureCustomTableConfig } =
  createCustomTableNodeHelpers(generateNodeId);

const MAX_LEVEL = 5;

function getNextLevel(baseLevel?: number) {
  const resolvedBase = baseLevel ?? props.parentLevel ?? 1;
  return Math.min(resolvedBase + 1, MAX_LEVEL);
}

function ensureNodeLevel() {
  const targetLevel = getNextLevel(props.parentLevel);
  if (props.node.level === targetLevel) {
    return;
  }
  updateNode((node) => {
    node.level = targetLevel;
  });
}

onMounted(ensureNodeLevel);

watch(
  () => props.parentLevel,
  () => {
    ensureNodeLevel();
  },
  { immediate: true },
);

function updateNode(updater: (node: WordDocumentNode) => void) {
  emit("update", props.node.id, updater);
}

function handleChildPanelUpdate(
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
) {
  if (nodeId !== props.node.id) return;
  updateNode(updater);
}

function handleDataBindingUpdate(
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
) {
  if (nodeId !== props.node.id) return;
  updateNode((node) => {
    updater(node);
    handleNodeDataPathChange(node);
  });
}

function handleTableConfigUpdate(
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
) {
  if (nodeId !== props.node.id) return;
  updateNode((node) => {
    updater(node);
    handleNodeDataPathChange(node);
  });
}

function handleCustomTableConfigUpdate(
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
) {
  if (nodeId !== props.node.id) return;
  updateNode((node) => {
    updater(node);
    handleNodeDataPathChange(node);
  });
}

function handlePanelAddChild(nodeId: string) {
  emit("add-child", nodeId);
}

function handleTypeChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  updateNode((node) => {
    node.type = target.value as WordDocumentNodeType;
    if (node.type !== "table") {
      delete node.table;
    }
    if (node.type !== "list") {
      delete node.list;
    }
    if (node.type !== "customTable") {
      delete node.customTable;
    } else {
      ensureCustomTableConfig(node);
    }
    if (!shouldShowSectionSelectors(node)) {
      node.sectionId = "";
      node.dataPath = "";
    }
  });
}

function handleLabelChange(event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    node.label = target.value;
  });
}

function handleTemplateChange(event: Event) {
  const target = event.target as HTMLTextAreaElement;
  updateNode((node) => {
    node.template = target.value;
  });
}

function handleParagraphNumberingToggle(event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    node.paragraphNumbering = target.checked;
    if (target.checked) {
      node.paragraphNumberStyle = node.paragraphNumberStyle || "arabicNumber";
    } else {
      delete node.paragraphNumberStyle;
    }
  });
}

function handleParagraphNumberStyleChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  updateNode((node) => {
    node.paragraphNumberStyle = target.value as WordListStyle;
  });
}

function handleFixedLayoutRowsChange(event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (!node.table) {
      node.table = { columns: [] };
    }
    if (!node.table.fixedLayout) {
      node.table.fixedLayout = { rows: 2, cols: 2, cells: [] };
    }
    node.table.fixedLayout.rows = Number(target.value);
  });
}

function handleFixedLayoutColsChange(event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (!node.table) {
      node.table = { columns: [] };
    }
    if (!node.table.fixedLayout) {
      node.table.fixedLayout = { rows: 2, cols: 2, cells: [] };
    }
    node.table.fixedLayout.cols = Number(target.value);
  });
}

function handleAddTableCell() {
  updateNode((node) => {
    const fixedLayout = ensureTableFixedLayout(node);
    fixedLayout.cells.push({
      row: 0,
      col: 0,
      isHeader: false,
    });
  });
}

function handleRemoveTableCell(cellIndex: number) {
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells) {
      node.table.fixedLayout.cells.splice(cellIndex, 1);
    }
  });
}

function handleCellRowChange(cellIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells?.[cellIndex]) {
      node.table.fixedLayout.cells[cellIndex].row = Number(target.value);
    }
  });
}

function handleCellColChange(cellIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells?.[cellIndex]) {
      node.table.fixedLayout.cells[cellIndex].col = Number(target.value);
    }
  });
}

function handleCellLabelChange(cellIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells?.[cellIndex]) {
      node.table.fixedLayout.cells[cellIndex].label = target.value;
    }
  });
}

function handleCellDataPathChange(cellIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells?.[cellIndex]) {
      node.table.fixedLayout.cells[cellIndex].dataPath = target.value;
    }
  });
}

function handleCellIsHeaderChange(cellIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells?.[cellIndex]) {
      node.table.fixedLayout.cells[cellIndex].isHeader = target.checked;
    }
  });
}

function handleChildUpdate(
  childNodeId: string,
  updater: (node: WordDocumentNode) => void,
) {
  updateNode((node) => {
    updateNodeById(node.children, childNodeId, updater);
  });
}

function handleChildRemove(childNodeId: string) {
  updateNode((node) => {
    removeNodeById(node.children, childNodeId);
  });
}

function handleAddChild(childNodeId: string) {
  // 如果是在當前節點下添加子節點
  if (childNodeId === props.node.id) {
    updateNode((node) => {
      addChildNodeById([node], node.id, (parent) => ({
        id: generateNodeId(),
        type: "paragraph",
        sectionId: parent.sectionId,
        level: getNextLevel(parent.level),
      }));
    });
  } else {
    // 轉發給子節點處理
    handleChildUpdate(childNodeId, (node) => {
      addChildNodeById([node], node.id, (parent) => ({
        id: generateNodeId(),
        type: "paragraph",
        sectionId: parent.sectionId,
        level: getNextLevel(parent.level),
      }));
    });
  }
}

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

function ensureTableFixedLayout(node: WordDocumentNode) {
  if (!node.table) {
    node.table = { columns: [] };
  }
  if (!node.table.fixedLayout) {
    node.table.fixedLayout = {
      rows: 2,
      cols: 2,
      cells: [],
    };
  }
  return node.table.fixedLayout;
}

function handleNodeDataPathChange(node: WordDocumentNode) {
  if (node.type === "table" && node.table?.columns?.length) {
    const allow = new Set(getNodeColumnCandidates(node).map((opt) => opt.key));
    node.table.columns = node.table.columns.filter((col) => allow.has(col.key));
  }

  if (node.type === "customTable" && node.customTable?.cells?.length) {
    const allow = new Set(getNodeColumnCandidates(node).map((opt) => opt.key));
    node.customTable.cells.forEach((cell) => {
      let changed = false;
      cell.contents?.forEach((content) => {
        if (content.type !== "field" || !content.dataPath) return;
        if (!allow.has(content.dataPath)) {
          const scopedPath = resolveNodeScopedPath(node, content.dataPath);
          const stillAllowed = scopedPath ? allow.has(scopedPath) : false;
          if (!stillAllowed) {
            content.dataPath = "";
            changed = true;
          }
        }
      });
      if (changed) {
        syncLegacyCustomTableCellFields(cell);
      }
    });
  }
}
</script>
