<!-- 用途：遞迴編輯 Word 節點樹，整合不同節點型別面板與子節點操作。 -->
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

// 章節資料來源（供資料欄位候選解析）。
interface SectionRecord {
  id: string;
  name: string;
  json_schema?: {
    properties?: Record<string, any>;
  } | null;
}

// 接收目前節點、父節點層級、章節與選項清單。
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

// 對外事件：更新節點、刪除節點、新增子節點。
const emit = defineEmits<{
  (
    e: "update",
    nodeId: string,
    updater: (node: WordDocumentNode) => void,
  ): void;
  (e: "remove", nodeId: string): void;
  (e: "add-child", nodeId: string): void;
}>();

// 路徑工具：取得當前節點可用欄位候選。
const { getColumnCandidates } = createWordSchemaPathHelpers(
  () => props.sections,
);

// 自訂表格工具：確保結構與舊欄位同步。
const { syncLegacyCustomTableCellFields, ensureCustomTableConfig } =
  createCustomTableNodeHelpers(generateNodeId);

// 節點最大層級限制，避免過深巢狀。
const MAX_LEVEL = 5;

// 依父層級推算下一層級，並限制上限。
function getNextLevel(baseLevel?: number) {
  const resolvedBase = baseLevel ?? props.parentLevel ?? 1;
  return Math.min(resolvedBase + 1, MAX_LEVEL);
}

// 確保當前節點 level 與父層關係一致。
function ensureNodeLevel() {
  const targetLevel = getNextLevel(props.parentLevel);
  if (props.node.level === targetLevel) {
    return;
  }
  updateNode((node) => {
    node.level = targetLevel;
  });
}

// 元件掛載時先校正一次層級。
onMounted(ensureNodeLevel);

// 當父層級變動時重新校正當前節點 level。
watch(
  () => props.parentLevel,
  () => {
    ensureNodeLevel();
  },
  { immediate: true },
);

// 派發目前節點更新事件的統一出口。
function updateNode(updater: (node: WordDocumentNode) => void) {
  emit("update", props.node.id, updater);
}

// 處理子面板回傳更新（需確認 nodeId 為當前節點）。
function handleChildPanelUpdate(
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
) {
  if (nodeId !== props.node.id) return;
  updateNode(updater);
}

// 處理資料綁定更新，並同步檢查 dataPath 相關設定。
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

// 處理表格設定更新，並同步檢查 dataPath 相關設定。
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

// 處理自訂表格設定更新，並同步檢查 dataPath 相關設定。
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

// 子面板請求新增子節點時向外轉發。
function handlePanelAddChild(nodeId: string) {
  emit("add-child", nodeId);
}

// 切換節點型別並初始化/清除對應設定。
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

// 更新節點標題。
function handleLabelChange(event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    node.label = target.value;
  });
}

// 更新自訂文字模板內容。
function handleTemplateChange(event: Event) {
  const target = event.target as HTMLTextAreaElement;
  updateNode((node) => {
    node.template = target.value;
  });
}

// 段落編號開關切換，關閉時清除編號樣式。
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

// 變更段落編號樣式。
function handleParagraphNumberStyleChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  updateNode((node) => {
    node.paragraphNumberStyle = target.value as WordListStyle;
  });
}

// 變更固定表格行數。
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

// 變更固定表格列數。
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

// 新增固定表格單元格設定。
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

// 移除指定固定表格單元格設定。
function handleRemoveTableCell(cellIndex: number) {
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells) {
      node.table.fixedLayout.cells.splice(cellIndex, 1);
    }
  });
}

// 更新單元格 row 值。
function handleCellRowChange(cellIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells?.[cellIndex]) {
      node.table.fixedLayout.cells[cellIndex].row = Number(target.value);
    }
  });
}

// 更新單元格 col 值。
function handleCellColChange(cellIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells?.[cellIndex]) {
      node.table.fixedLayout.cells[cellIndex].col = Number(target.value);
    }
  });
}

// 更新單元格固定標籤。
function handleCellLabelChange(cellIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells?.[cellIndex]) {
      node.table.fixedLayout.cells[cellIndex].label = target.value;
    }
  });
}

// 更新單元格資料路徑。
function handleCellDataPathChange(cellIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells?.[cellIndex]) {
      node.table.fixedLayout.cells[cellIndex].dataPath = target.value;
    }
  });
}

// 更新單元格是否為標題欄。
function handleCellIsHeaderChange(cellIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (node.table?.fixedLayout?.cells?.[cellIndex]) {
      node.table.fixedLayout.cells[cellIndex].isHeader = target.checked;
    }
  });
}

// 處理子節點更新（遞迴節點回傳）。
function handleChildUpdate(
  childNodeId: string,
  updater: (node: WordDocumentNode) => void,
) {
  updateNode((node) => {
    updateNodeById(node.children, childNodeId, updater);
  });
}

// 處理子節點刪除。
function handleChildRemove(childNodeId: string) {
  updateNode((node) => {
    removeNodeById(node.children, childNodeId);
  });
}

// 新增子節點：當前節點直接新增或轉交更深層子節點處理。
function handleAddChild(childNodeId: string) {
  // 若目標是當前節點，直接新增一個 paragraph 子節點。
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
    // 否則轉交到對應子節點內新增。
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

// 生成節點 ID（優先使用 crypto.randomUUID）。
function generateNodeId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `node_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

// 取得節點可用欄位候選。
function getNodeColumnCandidates(node: WordDocumentNode) {
  if (!node.sectionId) return [];
  return getColumnCandidates(node.sectionId, node.dataPath);
}

// 確保固定表格結構存在並回傳。
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

// 當資料路徑變更時，同步清理不再可用的欄位配置。
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
