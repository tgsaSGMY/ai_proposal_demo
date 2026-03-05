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

      <div
        v-if="shouldShowSectionSelectors(node)"
        class="grid gap-4 md:grid-cols-2"
      >
        <label class="space-y-1 text-sm text-slate-600">
          資料章節
          <select
            :value="node.sectionId"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
            @change="handleSectionChange"
          >
            <option value="">無資料來源（純文字）</option>
            <option
              v-for="option in sectionOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="space-y-1 text-sm text-slate-600">
          資料欄位
          <div class="space-y-2">
            <template v-if="shouldShowSectionSelectors(node)">
              <div
                v-for="(levelOptions, levelIndex) in getDataPathLevels(node)"
                :key="`level-${levelIndex}`"
                class="flex items-center gap-2"
              >
                <select
                  :value="parseDataPath(node.dataPath)[levelIndex] || ''"
                  class="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  @change="handleDataPathLevelChange(levelIndex, $event)"
                >
                  <option value="">
                    {{ levelIndex === 0 ? "整個章節/物件" : "選擇子欄位..." }}
                  </option>
                  <option
                    v-for="option in levelOptions"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
                <button
                  v-if="
                    levelIndex === parseDataPath(node.dataPath).length - 1 &&
                    canNestDeeper(node)
                  "
                  type="button"
                  class="px-3 py-2 text-sm font-semibold text-rose-600 hover:text-rose-700 rounded-xl border border-rose-200 hover:bg-rose-50"
                  @click="handleAddDataPathLevel"
                  title="新增一層巢狀欄位"
                >
                  +
                </button>
              </div>
            </template>
            <select
              v-if="!shouldShowSectionSelectors(node)"
              :value="node.dataPath"
              class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
              @change="handleDataPathChange"
            >
              <option value="">無法選擇（需先選擇章節）</option>
            </select>
          </div>
        </label>
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

      <label
        v-if="node.type === 'paragraph' || node.type === 'customText'"
        class="flex items-center gap-2 text-sm text-slate-600 cursor-pointer"
      >
        <input
          type="checkbox"
          class="h-4 w-4 rounded border-slate-300"
          :checked="node.style?.bodyBold === true"
          @change="handleBoldToggle"
        />
        使用粗體
      </label>

      <!-- 表格配置 -->
      <div
        v-if="node.type === 'table'"
        class="space-y-3 rounded-xl bg-slate-50 p-3"
      >
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
                :placeholder="`列 ${colIndex + 1} 標題`"
                @input="handleColumnLabelChange(colIndex, $event)"
              />
              <span class="text-xs text-slate-500 whitespace-nowrap"
                >({{ column.key }})</span
              >
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
              </div>
            </div>
          </div>
        </div>

        <div>
          <p class="text-xs font-semibold text-slate-500">欄位內容</p>
          <div class="mt-2 grid gap-2 md:grid-cols-2">
            <label
              v-for="option in getNodeColumnCandidates(node)"
              :key="option.key"
              class="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm"
            >
              <input
                type="checkbox"
                :checked="
                  node.table?.columns?.some(
                    (column) => column.key === option.key,
                  )
                "
                class="h-4 w-4 rounded border-slate-300"
                @change="handleColumnToggle(option, $event)"
              />
              <span class="truncate"
                >{{ option.label }} ({{ option.key }})</span
              >
            </label>
          </div>
          <p
            v-if="!getNodeColumnCandidates(node).length"
            class="text-xs text-slate-400 mt-2"
          >
            無可用欄位，請確認章節或資料來源設定。
          </p>
        </div>

        <div
          v-if="node.table?.layout === 'fixed'"
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
      </div>

      <div
        v-if="node.type === 'customTable'"
        class="space-y-4 rounded-xl bg-slate-50 p-3"
      >
        <div class="grid gap-3 md:grid-cols-2">
          <label class="space-y-1 text-sm text-slate-600">
            列數 (1-20)
            <input
              :value="node.customTable?.rows ?? 1"
              type="number"
              min="1"
              max="20"
              class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
              @change="
                (event) =>
                  handleCustomTableDimensionChange(
                    'rows',
                    Number(
                      (event.target as HTMLInputElement | null)?.value || 1,
                    ),
                  )
              "
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
              @change="
                (event) =>
                  handleCustomTableDimensionChange(
                    'cols',
                    Number(
                      (event.target as HTMLInputElement | null)?.value || 1,
                    ),
                  )
              "
            />
          </label>
        </div>

        <div
          class="space-y-3 max-h-[28rem] overflow-y-auto overflow-x-auto pr-1"
        >
          <div
            v-for="rowIndex in node.customTable?.rows || 0"
            :key="`custom-row-${node.id}-${rowIndex}`"
            class="space-y-2"
          >
            <p class="text-xs font-semibold text-slate-500">
              第 {{ rowIndex }} 列
            </p>
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
                    <div
                      class="flex flex-wrap items-center justify-between gap-2"
                    >
                      <div
                        class="flex items-center gap-2 text-xs text-slate-500"
                      >
                        <span>片段 {{ contentIndex + 1 }}</span>
                        <select
                          v-model="content.type"
                          class="rounded-lg border border-slate-200 px-2 py-1 text-xs"
                          @change="
                            handleCustomTableCellContentTypeChange(
                              cell,
                              content,
                            )
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
                          title="上移片段"
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
                            moveCustomTableCellContent(
                              cell,
                              contentIndex,
                              'down',
                            )
                          "
                          title="下移片段"
                        >
                          ↓
                        </button>
                        <button
                          type="button"
                          class="rounded-lg border border-rose-200 px-2 py-1 text-xs text-rose-600 disabled:opacity-40"
                          :disabled="(cell.contents?.length || 0) === 1"
                          @click="
                            removeCustomTableCellContent(cell, content.id)
                          "
                          title="刪除此片段"
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
                      <p
                        v-if="
                          !getNodeColumnCandidates(node).length &&
                          node.sectionId
                        "
                        class="text-xs text-slate-400"
                      >
                        無可用欄位，請調整資料來源。
                      </p>
                      <p v-if="!node.sectionId" class="text-xs text-rose-500">
                        需先選擇資料章節才能綁定欄位。
                      </p>
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

      <!-- 清單配置 -->
      <div
        v-if="node.type === 'list' || node.type === 'subHeading'"
        class="space-y-3 rounded-xl bg-slate-50 p-3"
      >
        <label class="flex items-center gap-2 text-sm text-slate-600">
          <input
            :checked="node.list?.numbering"
            type="checkbox"
            class="h-4 w-4 rounded border-slate-300"
            @change="handleListNumberingChange"
          />
          使用編號
        </label>
        <label class="space-y-1 text-sm text-slate-600">
          清單樣式
          <select
            :value="node.list?.style"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
            @change="handleListStyleChange"
          >
            <option
              v-for="option in listStyleOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </label>

        <div
          v-if="node.type === 'list'"
          class="border-t border-slate-200 pt-3 mt-3"
        >
          <label class="flex items-center gap-2 text-sm text-slate-600 mb-2">
            <input
              :checked="node.list?.itemConfig?.useSubNodes"
              type="checkbox"
              class="h-4 w-4 rounded border-slate-300"
              @change="handleUseSubNodesChange"
            />
            使用子節點渲染對象（嵌套清單）
          </label>
          <p class="text-xs text-slate-500 mb-3">
            當清單項是對象時，使用子節點定義如何渲染每個字段
          </p>

          <div v-if="node.list?.itemConfig?.useSubNodes" class="space-y-2">
            <p class="text-xs text-slate-500">
              啟用後可在下方使用「+ 添加子節點」設定清單項內容
            </p>
          </div>
        </div>
      </div>

      <!-- 添加子節點按鈕（只有啟用嵌套清單時顯示） -->
      <div
        v-if="node.type === 'list' && node.list?.itemConfig?.useSubNodes"
        class="border-t border-slate-200 pt-3"
      >
        <button
          type="button"
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50"
          @click="$emit('add-child', node.id)"
        >
          + 添加子節點
        </button>
      </div>
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
import type {
  WordDocumentNode,
  WordDocumentNodeType,
  WordTableColumn,
  WordListStyle,
  WordCustomTableConfig,
  WordCustomTableCell,
  WordCustomTableCellContent,
  WordCustomTableCellContentType,
} from "~/types/wordExport";

interface SectionRecord {
  id: string;
  name: string;
  json_schema?: {
    properties?: Record<string, any>;
  } | null;
}

interface SchemaField {
  title?: string;
  type?: string;
  properties?: Record<string, SchemaField>;
  items?: {
    properties?: Record<string, SchemaField>;
  };
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

function handleSectionChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  updateNode((node) => {
    node.sectionId = target.value;
    node.dataPath = "";
    handleNodeDataPathChange(node);
  });
}

function handleDataPathChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  updateNode((node) => {
    node.dataPath = target.value;
    handleNodeDataPathChange(node);
  });
}

function handleTemplateChange(event: Event) {
  const target = event.target as HTMLTextAreaElement;
  updateNode((node) => {
    node.template = target.value;
  });
}

function handleBoldToggle(event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (!node.style) {
      node.style = {};
    }
    node.style.bodyBold = target.checked;
  });
}

function handleTableLayoutChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  updateNode((node) => {
    if (!node.table) {
      node.table = { columns: [] };
    }
    if (!node.table.columns) {
      node.table.columns = [];
    }
    node.table.layout = target.value as "auto" | "grid" | "fixed";
    if (node.table.layout === "fixed" && !node.table.fixedLayout) {
      node.table.fixedLayout = {
        rows: 2,
        cols: 2,
        cells: [],
      };
    }
  });
}

function handleCustomHeadersChange(event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (!node.table) {
      node.table = { columns: [] };
    }
    if (!node.table.columns) {
      node.table.columns = [];
    }
    node.table.customHeaders = target.checked;
  });
}

function handleTransposeChange(event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (!node.table) {
      node.table = { columns: [] };
    }
    if (!node.table.columns) {
      node.table.columns = [];
    }
    node.table.transpose = target.checked;
  });
}

function handleColumnLabelChange(colIndex: number, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (node.table?.columns?.[colIndex]) {
      node.table.columns[colIndex].label = target.value;
    }
  });
}

function moveTableColumn(columnIndex: number, direction: "up" | "down") {
  updateNode((node) => {
    if (!node.table?.columns) return;

    const columns = node.table.columns;
    const newIndex = direction === "up" ? columnIndex - 1 : columnIndex + 1;

    if (newIndex < 0 || newIndex >= columns.length) return;

    const colAtIndex = columns[columnIndex];
    const colAtNewIndex = columns[newIndex];

    if (!colAtIndex || !colAtNewIndex) return;

    // 交換列的位置
    columns[columnIndex] = colAtNewIndex;
    columns[newIndex] = colAtIndex;
  });
}

function handleColumnToggle(option: WordTableColumn, event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (!node.table) {
      node.table = { columns: [] };
    }
    if (!node.table.columns) {
      node.table.columns = [];
    }
    if (target.checked) {
      if (!node.table.columns.find((col) => col.key === option.key)) {
        node.table.columns.push({ ...option });
      }
    } else {
      node.table.columns = node.table.columns.filter(
        (col) => col.key !== option.key,
      );
    }
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

function handleListNumberingChange(event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (!node.list) {
      node.list = {
        numbering: true,
        style: node.level ? getListStyleForLevel(node.level) : "chineseNumber",
      };
    }
    node.list!.numbering = target.checked;
  });
}

function handleListStyleChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  updateNode((node) => {
    if (!node.list) {
      node.list = {
        numbering: true,
        style: node.level ? getListStyleForLevel(node.level) : "chineseNumber",
      };
    }
    node.list.style = target.value as any;
  });
}

function handleUseSubNodesChange(event: Event) {
  const target = event.target as HTMLInputElement;
  updateNode((node) => {
    if (!node.list) {
      node.list = { numbering: true, style: "chineseNumber" };
    }
    if (!node.list.itemConfig) {
      node.list.itemConfig = { useSubNodes: false };
    }
    node.list.itemConfig.useSubNodes = target.checked;
    if (!target.checked && !node.children) {
      node.children = [];
    }
  });
}

function handleChildUpdate(
  childNodeId: string,
  updater: (node: WordDocumentNode) => void,
) {
  updateNode((node) => {
    if (node.children) {
      const childNode = node.children.find((c) => c.id === childNodeId);
      if (childNode) {
        updater(childNode);
      }
    }
  });
}

function handleChildRemove(childNodeId: string) {
  updateNode((node) => {
    if (node.children) {
      const index = node.children.findIndex((c) => c.id === childNodeId);
      if (index >= 0) {
        node.children.splice(index, 1);
      }
    }
  });
}

function handleAddChild(childNodeId: string) {
  // 如果是在當前節點下添加子節點
  if (childNodeId === props.node.id) {
    updateNode((node) => {
      if (!node.children) {
        node.children = [];
      }
      const newChildNode: WordDocumentNode = {
        id: generateNodeId(),
        type: "paragraph",
        sectionId: node.sectionId,
        level: getNextLevel(node.level),
      };
      node.children.push(newChildNode);
    });
  } else {
    // 轉發給子節點處理
    if (props.node.children) {
      const targetChild = props.node.children.find((c) => c.id === childNodeId);
      if (targetChild) {
        handleChildUpdate(childNodeId, (node) => {
          if (!node.children) {
            node.children = [];
          }
          const newChildNode: WordDocumentNode = {
            id: generateNodeId(),
            type: "paragraph",
            sectionId: node.sectionId,
            level: getNextLevel(node.level),
          };
          node.children.push(newChildNode);
        });
      }
    }
  }
}

function generateNodeId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `node_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function shouldShowNodeLabel(node: WordDocumentNode) {
  return !["paragraph", "table", "customTable", "list", "customText"].includes(
    node.type,
  );
}

function shouldShowSectionSelectors(node: WordDocumentNode) {
  return !["sectionTitle", "subHeading", "customText"].includes(node.type);
}

function shouldShowTemplateInput(node: WordDocumentNode) {
  return node.type === "customText";
}

function parseDataPath(dataPath?: string): string[] {
  if (!dataPath) return [];
  return dataPath.split(".").filter((p) => p.length > 0);
}

function getDataPathOptions(sectionId: string) {
  const schema = getSectionSchema(sectionId);
  if (!schema) return [];
  return Object.entries(schema).map(([key, meta]) => ({
    value: key,
    label: meta?.title || key,
  }));
}

function getNestedPathOptions(
  sectionId: string,
  currentPath: string,
): { value: string; label: string }[] {
  const target = getPropertySchema(sectionId, currentPath);
  if (!target) return [];
  return Object.entries(target).map(([key, meta]) => ({
    value: key,
    label: meta?.title || key,
  }));
}

function getSectionSchema(
  sectionId: string,
): Record<string, SchemaField> | null {
  const section = props.sections.find((item) => item.id === sectionId);
  return section?.json_schema?.properties || null;
}

function getPropertySchema(
  sectionId: string,
  path?: string,
): Record<string, SchemaField> | null {
  const base = getSectionSchema(sectionId);
  if (!base) return null;
  if (!path) return base;

  const pathParts = path.split(".");
  let current: any = base;

  for (const part of pathParts) {
    if (!current[part]) return null;

    const schema = current[part];
    if (schema.type === "object" && schema.properties) {
      current = schema.properties;
    } else if (schema.type === "array" && schema.items?.properties) {
      current = schema.items.properties;
    } else {
      return null;
    }
  }

  return current;
}

function getDataPathLevels(
  node: WordDocumentNode,
): Array<{ value: string; label: string }[]> {
  if (!node.sectionId) return [];

  const currentSegments = parseDataPath(node.dataPath);
  const levels: Array<{ value: string; label: string }[]> = [];

  levels.push(getDataPathOptions(node.sectionId));

  for (let i = 0; i < currentSegments.length; i++) {
    const pathSoFar = currentSegments.slice(0, i + 1).join(".");
    const nextLevel = getNestedPathOptions(node.sectionId, pathSoFar);
    if (nextLevel.length === 0) break;
    levels.push(nextLevel);
  }

  return levels;
}

function canNestDeeper(node: WordDocumentNode): boolean {
  if (!node.sectionId) return false;
  const currentSegments = parseDataPath(node.dataPath);
  const pathSoFar = node.dataPath || "";
  const nextOptions = getNestedPathOptions(node.sectionId, pathSoFar);
  return nextOptions.length > 0;
}

function handleDataPathLevelChange(levelIndex: number, event: Event) {
  const target = event.target as HTMLSelectElement;
  updateNode((node) => {
    const segments = parseDataPath(node.dataPath);

    if (target.value === "") {
      segments.splice(levelIndex);
    } else {
      segments[levelIndex] = target.value;
      segments.splice(levelIndex + 1);
    }

    node.dataPath = segments.join(".");
    handleNodeDataPathChange(node);
  });
}

function handleAddDataPathLevel() {
  // 這個函數只是觸發重新渲染，實際的添加由 UI 自動處理
}

function getNodeColumnCandidates(node: WordDocumentNode) {
  if (!node.sectionId) return [];
  return getColumnCandidates(node.sectionId, node.dataPath);
}

function getColumnCandidates(sectionId: string, dataPath?: string) {
  const target = getPropertySchema(sectionId, dataPath);
  if (!target) return [];

  const candidates: Array<{ key: string; label: string }> = [];

  const flattenProperties = (
    props: Record<string, SchemaField>,
    prefix = "",
  ) => {
    for (const [key, meta] of Object.entries(props)) {
      const fullKey = prefix ? `${prefix}.${key}` : key;
      const label = meta?.title || key;

      if (meta?.type !== "object" && meta?.type !== "array") {
        candidates.push({
          key: fullKey,
          label: prefix ? `${prefix} > ${label}` : label,
        });
      }

      if (meta?.type === "object" && meta?.properties) {
        flattenProperties(meta.properties, fullKey);
      }
    }
  };

  flattenProperties(target);
  return candidates;
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

function resolveNodeScopedPath(
  node: WordDocumentNode,
  relativePath?: string,
): string | undefined {
  if (!relativePath || !relativePath.trim()) {
    return node.dataPath;
  }
  if (!node.dataPath || !node.dataPath.trim()) {
    return relativePath;
  }
  const trimmedRelative = relativePath.trim();
  const basePrefix = `${node.dataPath}.`;
  if (trimmedRelative.startsWith(basePrefix)) {
    return trimmedRelative;
  }
  return `${node.dataPath}.${trimmedRelative}`;
}

function normalizeCustomTableCells(config: WordCustomTableConfig) {
  const rows = Math.min(Math.max(Math.floor(config.rows || 1), 1), 20);
  const cols = Math.min(Math.max(Math.floor(config.cols || 1), 1), 20);
  const expectedCellCount = rows * cols;
  const existingCells = Array.isArray(config.cells) ? config.cells : [];
  let needsRebuild =
    !Array.isArray(config.cells) || existingCells.length !== expectedCellCount;

  const seenKeys = new Set<string>();
  if (!needsRebuild) {
    for (const cell of existingCells) {
      const rowValid =
        typeof cell.row === "number" && cell.row >= 0 && cell.row < rows;
      const colValid =
        typeof cell.col === "number" && cell.col >= 0 && cell.col < cols;
      if (!rowValid || !colValid) {
        needsRebuild = true;
        break;
      }
      const key = `${cell.row}-${cell.col}`;
      if (seenKeys.has(key)) {
        needsRebuild = true;
        break;
      }
      seenKeys.add(key);
    }
  }

  const finalizeCell = (cell: WordCustomTableCell) => {
    if (!cell.id) {
      cell.id = generateNodeId();
    }
    ensureCustomTableCellContents(cell);
    return cell;
  };

  if (!needsRebuild) {
    existingCells.forEach(finalizeCell);
    config.rows = rows;
    config.cols = cols;
    return;
  }

  const existing = new Map<string, WordCustomTableCell>();
  for (const cell of existingCells) {
    if (
      typeof cell.row !== "number" ||
      typeof cell.col !== "number" ||
      cell.row < 0 ||
      cell.col < 0
    ) {
      continue;
    }
    const key = `${cell.row}-${cell.col}`;
    if (!existing.has(key)) {
      existing.set(key, cell);
    }
  }

  const cells: WordCustomTableCell[] = [];
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const key = `${row}-${col}`;
      const cell = existing.get(key) ?? {
        id: generateNodeId(),
        row,
        col,
        type: "text",
        text: "",
        dataPath: "",
      };
      cell.row = row;
      cell.col = col;
      cells.push(finalizeCell(cell));
    }
  }

  config.rows = rows;
  config.cols = cols;
  config.cells = cells;
}

function ensureCustomTableConfig(node: WordDocumentNode) {
  if (!node.customTable) {
    node.customTable = {
      rows: 2,
      cols: 2,
      cells: [],
    };
  }
  normalizeCustomTableCells(node.customTable);
  return node.customTable;
}

function getCustomTableRowCells(node: WordDocumentNode, rowIndex: number) {
  if (!node.customTable?.cells) {
    return [];
  }
  return node.customTable.cells
    .filter((cell) => cell.row === rowIndex)
    .sort((a, b) => a.col - b.col);
}

function syncLegacyCustomTableCellFields(cell: WordCustomTableCell) {
  const primary = cell.contents?.[0];
  if (!primary) {
    cell.type = "text";
    cell.text = "";
    cell.dataPath = "";
    return;
  }

  cell.type = primary.type;
  if (primary.type === "text") {
    cell.text = primary.text ?? "";
    cell.dataPath = "";
  } else {
    cell.dataPath = primary.dataPath ?? "";
    cell.text = "";
  }
}

function ensureCustomTableCellContents(cell: WordCustomTableCell) {
  const buildContent = (
    base?: Partial<WordCustomTableCellContent> & {
      type?: WordCustomTableCellContentType;
    },
  ): WordCustomTableCellContent => {
    const resolvedType = base?.type ?? "text";
    return {
      id: base?.id || generateNodeId(),
      type: resolvedType,
      text: resolvedType === "text" ? (base?.text ?? "") : undefined,
      dataPath: resolvedType === "field" ? (base?.dataPath ?? "") : undefined,
    };
  };

  if (!Array.isArray(cell.contents) || cell.contents.length === 0) {
    const fallbackType = cell.type ?? "text";
    cell.contents = [
      buildContent({
        type: fallbackType,
        text: cell.text,
        dataPath: cell.dataPath,
      }),
    ];
  } else {
    cell.contents = cell.contents.map((content) =>
      buildContent({
        id: content.id,
        type: content.type,
        text: content.text,
        dataPath: content.dataPath,
      }),
    );
  }

  syncLegacyCustomTableCellFields(cell);
  return cell.contents;
}

function handleCustomTableDimensionChange(
  dimension: "rows" | "cols",
  rawValue: number,
) {
  const sanitized = Number.isFinite(rawValue) ? Math.floor(rawValue) : 1;
  updateNode((node) => {
    const customTable = ensureCustomTableConfig(node);
    const clamped = Math.min(Math.max(sanitized, 1), 20);
    customTable[dimension] = clamped;
    normalizeCustomTableCells(customTable);
  });
}

function addCustomTableCellContent(
  cell: WordCustomTableCell,
  type: WordCustomTableCellContentType,
) {
  if (!cell.contents) {
    cell.contents = [];
  }
  cell.contents.push({
    id: generateNodeId(),
    type,
    text: type === "text" ? "" : undefined,
    dataPath: type === "field" ? "" : undefined,
  });
  ensureCustomTableCellContents(cell);
}

function removeCustomTableCellContent(
  cell: WordCustomTableCell,
  contentId: string,
) {
  if (!cell.contents || cell.contents.length === 0) {
    cell.contents = [
      {
        id: generateNodeId(),
        type: "text",
        text: "",
      },
    ];
  }
  if (cell.contents.length === 1) {
    const first = cell.contents[0];
    if (first) {
      first.type = "text";
      first.text = "";
      first.dataPath = "";
    }
    syncLegacyCustomTableCellFields(cell);
    return;
  }
  cell.contents = cell.contents.filter((content) => content.id !== contentId);
  if (!cell.contents.length) {
    cell.contents = [
      {
        id: generateNodeId(),
        type: "text",
        text: "",
      },
    ];
  }
  ensureCustomTableCellContents(cell);
}

function moveCustomTableCellContent(
  cell: WordCustomTableCell,
  contentIndex: number,
  direction: "up" | "down",
) {
  if (!cell.contents || cell.contents.length < 2) return;
  const newIndex = direction === "up" ? contentIndex - 1 : contentIndex + 1;
  if (newIndex < 0 || newIndex >= cell.contents.length) return;
  const current = cell.contents[contentIndex];
  const target = cell.contents[newIndex];
  if (!current || !target) return;
  cell.contents[contentIndex] = target;
  cell.contents[newIndex] = current;
  ensureCustomTableCellContents(cell);
}

function handleCustomTableCellContentTypeChange(
  cell: WordCustomTableCell,
  content: WordCustomTableCellContent,
) {
  if (content.type === "text") {
    content.text = content.text ?? "";
    content.dataPath = "";
  } else {
    content.dataPath = content.dataPath ?? "";
    content.text = "";
  }
  ensureCustomTableCellContents(cell);
}

function getListStyleForLevel(level: number): WordListStyle {
  switch (level) {
    case 2:
      return "chineseNumber";
    case 3:
      return "arabicNumber";
    case 4:
      return "parenNumbered";
    default:
      return "bullet";
  }
}
</script>
