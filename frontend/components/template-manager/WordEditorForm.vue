<template>
  <div
    v-if="isVisible && template"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 py-6"
    @click.self="emit('close')"
  >
    <section
      class="w-full max-w-6xl max-h-full overflow-y-auto rounded-2xl bg-white p-6 space-y-6 shadow-2xl"
    >
      <header class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p
            class="text-xs font-semibold text-rose-400 uppercase tracking-[0.3em]"
          >
            Word Export Editor
          </p>
          <h2 class="text-2xl font-bold text-slate-900">
            {{ template.name }} · {{ template.id }}
          </h2>
          <p class="text-sm text-slate-500">
            設定 Word
            樣式、段落字體與表格欄位，儲存後會產生新版本供專案匯出時比對使用。
          </p>
        </div>
        <button
          type="button"
          class="text-2xl font-bold text-slate-400 hover:text-slate-600"
          @click="emit('close')"
        >
          ×
        </button>
      </header>

      <div class="grid gap-6 lg:grid-cols-[280px,1fr]">
        <aside
          class="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4"
        >
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold text-slate-700">版本歷史</h3>
            <span class="text-xs text-slate-500"
              >{{ versionHistory.length }} 筆</span
            >
          </div>
          <p class="text-xs text-slate-500">
            系統會依專案建立時間，找出當時最近的版本。若尚未建立版本，匯出時將落回預設版型。
          </p>
          <ul class="space-y-2 text-sm">
            <li
              v-for="version in versionHistory"
              :key="version.id"
              class="rounded-xl border border-slate-200 bg-white p-3"
            >
              <div class="flex items-center justify-between gap-2">
                <div>
                  <p class="font-semibold text-slate-800">
                    {{ formatDate(version.createdAt) }}
                  </p>
                  <p class="text-xs text-slate-500 truncate">
                    {{ version.createdBy || "未記錄" }}
                  </p>
                </div>
                <button
                  type="button"
                  class="text-xs font-semibold text-rose-600 hover:text-rose-700"
                  @click="applyVersion(version)"
                >
                  套用
                </button>
              </div>
            </li>
            <li v-if="!versionHistory.length" class="text-xs text-slate-400">
              尚未建立任何版本。
            </li>
          </ul>
        </aside>

        <div class="space-y-6">
          <section class="rounded-2xl border border-slate-200 p-4 space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-base font-semibold text-slate-800">
                文件字體設定
              </h3>
              <button
                type="button"
                class="text-xs text-rose-500 underline-offset-2 hover:underline"
                @click="resetDocumentStyle"
              >
                還原預設
              </button>
            </div>
            <div class="grid gap-4 md:grid-cols-3">
              <label class="space-y-1 text-sm text-slate-600">
                標題字體
                <select
                  v-model="formState.documentStyle.headingFont"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                >
                  <option
                    v-for="font in FONT_OPTIONS"
                    :key="font"
                    :value="font"
                  >
                    {{ font }}
                  </option>
                </select>
              </label>
              <label class="space-y-1 text-sm text-slate-600">
                標題大小 (pt)
                <input
                  v-model.number="formState.documentStyle.headingSizePt"
                  type="number"
                  min="8"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                />
              </label>
              <label class="flex items-center gap-2 text-sm text-slate-600">
                <input
                  v-model="formState.documentStyle.headingBold"
                  type="checkbox"
                  class="h-4 w-4 rounded border-slate-300"
                />
                標題加粗
              </label>
              <label class="space-y-1 text-sm text-slate-600">
                小標字體
                <select
                  v-model="formState.documentStyle.subHeadingFont"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                >
                  <option
                    v-for="font in FONT_OPTIONS"
                    :key="font"
                    :value="font"
                  >
                    {{ font }}
                  </option>
                </select>
              </label>
              <label class="space-y-1 text-sm text-slate-600">
                小標大小 (pt)
                <input
                  v-model.number="formState.documentStyle.subHeadingSizePt"
                  type="number"
                  min="8"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                />
              </label>
              <label class="flex items-center gap-2 text-sm text-slate-600">
                <input
                  v-model="formState.documentStyle.subHeadingBold"
                  type="checkbox"
                  class="h-4 w-4 rounded border-slate-300"
                />
                小標加粗
              </label>
              <label class="space-y-1 text-sm text-slate-600">
                內文字體
                <select
                  v-model="formState.documentStyle.bodyFont"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                >
                  <option
                    v-for="font in FONT_OPTIONS"
                    :key="font"
                    :value="font"
                  >
                    {{ font }}
                  </option>
                </select>
              </label>
              <label class="space-y-1 text-sm text-slate-600">
                內文大小 (pt)
                <input
                  v-model.number="formState.documentStyle.bodySizePt"
                  type="number"
                  min="8"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                />
              </label>
              <label class="flex items-center gap-2 text-sm text-slate-600">
                <input
                  v-model="formState.documentStyle.bodyBold"
                  type="checkbox"
                  class="h-4 w-4 rounded border-slate-300"
                />
                內文加粗
              </label>
            </div>
          </section>

          <section class="rounded-2xl border border-slate-200 p-4 space-y-4">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 class="text-base font-semibold text-slate-800">
                  文檔節點流程
                </h3>
                <p class="text-xs text-slate-500">
                  建立節點樹以控制標題、段落、表格、清單與條件顯示，匯出時會依序渲染。
                </p>
              </div>
              <div class="flex flex-col gap-2 sm:flex-row">
                <button
                  type="button"
                  class="rounded-lg border border-slate-300 px-3 py-1 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                  @click="formState.nodes = generateDefaultNodes()"
                  title="重置為自動生成的默認節點"
                >
                  使用默認節點
                </button>
                <button
                  type="button"
                  class="rounded-lg border border-slate-300 px-3 py-1 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="addNode()"
                >
                  新增節點
                </button>
              </div>
            </div>

            <div
              v-if="!(formState.nodes && formState.nodes.length)"
              class="rounded-xl border border-dashed border-slate-300 bg-slate-50/60 p-6 text-center text-sm text-slate-500"
            >
              尚未建立節點，點擊「新增節點」開始設定自訂輸出流程。
            </div>

            <div v-else class="space-y-4">
              <div
                v-for="(node, index) in formState.nodes"
                :key="node.id"
                class="rounded-2xl border border-slate-200 p-4 space-y-4"
              >
                <div class="flex flex-wrap items-center justify-between gap-3">
                  <label class="flex-1 space-y-1 text-sm text-slate-600">
                    <span class="text-xs font-semibold text-slate-500">
                      節點類型
                    </span>
                    <select
                      v-model="node.type"
                      class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                      @change="handleNodeTypeChange(node.id)"
                    >
                      <option
                        v-for="option in NODE_TYPE_OPTIONS"
                        :key="option.value"
                        :value="option.value"
                      >
                        {{ option.label }}
                      </option>
                    </select>
                  </label>
                  <label class="space-y-1 text-sm text-slate-600">
                    <span class="text-xs font-semibold text-slate-500">
                      標題層級
                    </span>
                    <input
                      v-model.number="node.level"
                      type="number"
                      min="1"
                      max="5"
                      class="w-24 rounded-xl border border-slate-200 px-3 py-2 text-sm"
                    />
                  </label>
                  <div class="flex items-center gap-2 text-xs">
                    <button
                      type="button"
                      class="rounded-lg border border-slate-200 px-2 py-1 text-slate-600 disabled:opacity-40"
                      :disabled="index === 0"
                      @click="moveNode(node.id, 'up')"
                    >
                      上移
                    </button>
                    <button
                      type="button"
                      class="rounded-lg border border-slate-200 px-2 py-1 text-slate-600 disabled:opacity-40"
                      :disabled="index === (formState.nodes?.length || 0) - 1"
                      @click="moveNode(node.id, 'down')"
                    >
                      下移
                    </button>
                    <button
                      type="button"
                      class="rounded-lg border border-rose-200 px-2 py-1 text-rose-600"
                      @click="removeNode(node.id)"
                    >
                      刪除
                    </button>
                  </div>
                </div>

                <div
                  v-if="shouldShowNodeLabel(node)"
                  class="space-y-1 text-sm text-slate-600"
                >
                  <span class="text-xs font-semibold text-slate-500"
                    >節點標題</span
                  >
                  <input
                    v-model="node.label"
                    type="text"
                    class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                    placeholder="例如：壹、申請業者簡介"
                  />
                </div>

                <div
                  v-if="shouldShowSectionSelectors(node)"
                  class="grid gap-4 md:grid-cols-2"
                >
                  <label class="space-y-1 text-sm text-slate-600">
                    資料章節
                    <select
                      v-model="node.sectionId"
                      class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                      @change="handleNodeSectionChange(node.id)"
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
                      <!-- Cascading dropdowns for nested data path selection -->
                      <template v-if="shouldShowSectionSelectors(node)">
                        <div
                          v-for="(
                            levelOptions, levelIndex
                          ) in getDataPathLevels(node)"
                          :key="`level-${levelIndex}`"
                          class="flex items-center gap-2"
                        >
                          <select
                            :value="
                              parseDataPath(node.dataPath)[levelIndex] || ''
                            "
                            class="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm"
                            @change="
                              (event) =>
                                handleDataPathLevelChange(
                                  node.id,
                                  levelIndex,
                                  (event.target as HTMLSelectElement).value,
                                )
                            "
                          >
                            <option value="">
                              {{
                                levelIndex === 0
                                  ? "整個章節/物件"
                                  : "選擇子欄位..."
                              }}
                            </option>
                            <option
                              v-for="option in levelOptions"
                              :key="option.value"
                              :value="option.value"
                            >
                              {{ option.label }}
                            </option>
                          </select>
                          <!-- Add button to drill deeper if possible -->
                          <button
                            v-if="
                              levelIndex ===
                                parseDataPath(node.dataPath).length - 1 &&
                              canNestDeeper(node)
                            "
                            type="button"
                            class="px-3 py-2 text-sm font-semibold text-rose-600 hover:text-rose-700 rounded-xl border border-rose-200 hover:bg-rose-50"
                            @click="handleAddDataPathLevel(node.id)"
                            title="新增一層巢狀欄位"
                          >
                            +
                          </button>
                        </div>
                      </template>
                      <!-- Simple option when section not selected -->
                      <select
                        v-if="!shouldShowSectionSelectors(node)"
                        v-model="node.dataPath"
                        class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                        @change="handleNodeDataPathChange(node.id)"
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
                  <span class="text-xs font-semibold text-slate-500"
                    >自訂文字</span
                  >
                  <textarea
                    v-model="node.template"
                    rows="3"
                    class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                    placeholder="輸入要顯示的內容"
                  ></textarea>
                </div>

                <div
                  v-if="node.type === 'table'"
                  class="space-y-3 rounded-xl bg-slate-50 p-3"
                >
                  <label class="space-y-1 text-sm text-slate-600">
                    表格標題
                    <input
                      v-model="ensureTableConfig(node).title"
                      type="text"
                      class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                      placeholder="可選：例如 實施方式表"
                    />
                  </label>
                  <label class="space-y-1 text-sm text-slate-600">
                    分組欄位（可選）
                    <input
                      v-model="ensureTableConfig(node).groupBy"
                      type="text"
                      class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                      placeholder="輸入欄位 key，以該欄位值拆表"
                    />
                  </label>
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
                          @change="
                            (event) =>
                              onNodeColumnToggle(node.id, option, event)
                          "
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
                </div>

                <div
                  v-if="node.type === 'list' || node.type === 'subHeading'"
                  class="space-y-3 rounded-xl bg-slate-50 p-3"
                >
                  <label class="flex items-center gap-2 text-sm text-slate-600">
                    <input
                      v-model="ensureListConfig(node).numbering"
                      type="checkbox"
                      class="h-4 w-4 rounded border-slate-300"
                    />
                    使用編號
                  </label>
                  <label class="space-y-1 text-sm text-slate-600">
                    清單樣式
                    <select
                      v-model="ensureListConfig(node).style"
                      class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                    >
                      <option
                        v-for="option in LIST_STYLE_OPTIONS"
                        :key="option.value"
                        :value="option.value"
                      >
                        {{ option.label }}
                      </option>
                    </select>
                  </label>
                </div>

                <details
                  class="rounded-xl border border-slate-200 p-3 text-sm text-slate-600"
                >
                  <summary
                    class="cursor-pointer list-none font-semibold text-slate-700"
                  >
                    樣式設定（可選）
                  </summary>
                  <div class="mt-3 space-y-3">
                    <label class="space-y-1 text-sm">
                      對齊方式
                      <select
                        v-model="ensureNodeStyle(node).alignment"
                        class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                      >
                        <option value="">跟隨預設</option>
                        <option value="left">靠左</option>
                        <option value="center">置中</option>
                        <option value="right">靠右</option>
                      </select>
                    </label>
                  </div>
                </details>
              </div>
            </div>
          </section>
        </div>
      </div>

      <div class="flex flex-col gap-3 pt-2 sm:flex-row sm:justify-end">
        <button
          type="button"
          class="w-full sm:w-auto rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
          @click="emit('close')"
        >
          取消
        </button>
        <button
          type="button"
          class="w-full sm:w-auto rounded-xl border border-blue-300 px-4 py-2 text-sm font-semibold text-blue-600 hover:bg-blue-50"
          @click="handlePreviewExport"
        >
          預覽導出
        </button>
        <button
          type="button"
          class="w-full sm:w-auto rounded-xl border border-green-300 px-4 py-2 text-sm font-semibold text-green-600 hover:bg-green-50"
          @click="handleDownloadWord"
        >
          下載 Word
        </button>
        <button
          type="button"
          class="w-full sm:w-auto rounded-xl bg-rose-500 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-600 disabled:opacity-50"
          :disabled="saving"
          @click="handleSave"
        >
          {{ saving ? "儲存中..." : "儲存為新版本" }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { PropType } from "vue";
import { useNotifications } from "~/composables/useNotifications";
import type {
  WordDocumentNode,
  WordDocumentNodeType,
  WordExportConfigEntry,
  WordExportTemplateConfig,
  WordTableColumn,
  WordListStyle,
} from "~/types/wordExport";
import {
  Document,
  Packer,
  Paragraph,
  Table,
  TableCell,
  TableRow,
  TextRun,
  AlignmentType,
  UnderlineType,
  convertInchesToTwip,
} from "docx";

interface TemplateRecord {
  id: string;
  name: string;
  word_export_config?: WordExportConfigEntry[] | null;
}

interface SchemaField {
  title?: string;
  type?: string;
  properties?: Record<string, SchemaField>;
  items?: {
    properties?: Record<string, SchemaField>;
  };
}

interface SectionRecord {
  id: string;
  name: string;
  json_schema?: {
    properties?: Record<string, SchemaField>;
  } | null;
}

const DEFAULT_STYLE = {
  headingFont: "Times New Roman",
  headingSizePt: 18,
  headingBold: true,
  subHeadingFont: "Times New Roman",
  subHeadingSizePt: 14,
  subHeadingBold: true,
  bodyFont: "Times New Roman",
  bodySizePt: 12,
  bodyBold: false,
};

const props = defineProps({
  isVisible: { type: Boolean, default: false },
  template: {
    type: Object as PropType<TemplateRecord | null>,
    default: null,
  },
  sections: {
    type: Array as PropType<SectionRecord[]>,
    default: () => [],
  },
  saving: { type: Boolean, default: false },
});

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", payload: WordExportTemplateConfig): void;
}>();

const { error: notifyError } = useNotifications();

const FONT_OPTIONS = [
  "Times New Roman",
  "Arial",
  "Calibri",
  "Courier New",
  "Georgia",
  "Verdana",
  "宋體",
  "微軟雅黑",
  "黑體",
];

const NODE_TYPE_OPTIONS: Array<{ label: string; value: WordDocumentNodeType }> =
  [
    { label: "章節標題", value: "sectionTitle" },
    { label: "次標題", value: "subHeading" },
    { label: "段落文字", value: "paragraph" },
    { label: "表格", value: "table" },
    { label: "清單", value: "list" },
    { label: "自訂文字", value: "customText" },
  ];

const LIST_STYLE_OPTIONS = [
  { label: "一、 二、 三、", value: "chineseNumber" },
  { label: "1. 2. 3.", value: "arabicNumber" },
  { label: "（1）、（2）、（3）", value: "parenNumbered" },
  { label: "• ◦ ▪", value: "bullet" },
];

type HeadingCounterState = Record<number, number>;

function createHeadingCounterState(): HeadingCounterState {
  return {};
}

function resetHeadingCounters(state: HeadingCounterState) {
  Object.keys(state).forEach((key) => delete state[Number(key)]);
}

function formatChineseNumeral(value: number): string {
  if (value <= 0) return "";
  const digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"];
  if (value <= 10) {
    return value === 10 ? "十" : digits[value] || "";
  }
  if (value < 20) {
    return `十${digits[value - 10]}`;
  }
  if (value < 100) {
    const tens = Math.floor(value / 10);
    const units = value % 10;
    let result = `${digits[tens]}十`;
    if (units !== 0) {
      result += digits[units];
    }
    return result;
  }
  // Fallback for large numbers - simple decimal representation
  return String(value);
}

function formatHeadingPrefix(
  level: number | undefined,
  state: HeadingCounterState,
): string {
  if (!level) return "";
  state[level] = (state[level] ?? 0) + 1;
  Object.keys(state).forEach((key) => {
    const currentLevel = Number(key);
    if (currentLevel > level) {
      delete state[currentLevel];
    }
  });

  const count = state[level];
  switch (level) {
    case 2:
      return `${formatChineseNumeral(count)}、`;
    case 3:
      return `${count}. `;
    case 4:
      return `（${count}）`;
    default:
      return "";
  }
}

function getListBulletLabel(style: WordListStyle | undefined, index: number): string {
  switch (style) {
    case "chineseNumber":
    case "chineseComma":
      return `${formatChineseNumeral(index + 1)}、`;
    case "arabicNumber":
    case "numberedDot":
      return `${index + 1}.`;
    case "parenNumbered":
      return `（${index + 1}）`;
    default:
      return "•";
  }
}

const formState = ref<WordExportTemplateConfig>({
  documentStyle: { ...DEFAULT_STYLE },
  sectionLayouts: [],
  nodes: [],
});

const versionHistory = computed<WordExportConfigEntry[]>(() => {
  const list = props.template?.word_export_config ?? [];
  return [...list].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );
});

const sectionOptions = computed(() =>
  props.sections.map((section) => ({
    label: section.name,
    value: section.id,
  })),
);

watch(
  () => [props.isVisible, props.template, props.sections],
  ([visible]) => {
    if (visible) {
      hydrateForm(versionHistory.value[0]?.config);
    }
  },
  { immediate: true },
);

function hydrateForm(base?: WordExportTemplateConfig) {
  const documentStyle = {
    ...DEFAULT_STYLE,
    ...(base?.documentStyle || {}),
  };

  const layouts = deepClone(base?.sectionLayouts || []);
  // 如果没有现成的节点，则生成默认节点
  const nodes =
    base?.nodes && base.nodes.length > 0
      ? deepClone(base.nodes)
      : generateDefaultNodes();

  formState.value = {
    documentStyle,
    sectionLayouts: layouts,
    nodes,
  };
}

function resetDocumentStyle() {
  formState.value.documentStyle = { ...DEFAULT_STYLE };
}

function applyVersion(version: WordExportConfigEntry) {
  hydrateForm(version.config);
}

/**
 * Get all top-level data path options for a section
 */
function getDataPathOptions(sectionId: string) {
  const schema = getSectionSchema(sectionId);
  if (!schema) return [];
  return Object.entries(schema).map(([key, meta]) => ({
    value: key,
    label: meta?.title || key,
  }));
}

/**
 * Get nested property options at a specific level
 * Supports cascading dropdown - returns children of the current path
 */
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

function getColumnCandidates(sectionId: string, dataPath?: string) {
  const target = getPropertySchema(sectionId, dataPath);
  if (!target) return [];
  
  const candidates: Array<{ key: string; label: string }> = [];
  
  const flattenProperties = (props: Record<string, SchemaField>, prefix = "") => {
    for (const [key, meta] of Object.entries(props)) {
      const fullKey = prefix ? `${prefix}.${key}` : key;
      const label = meta?.title || key;
      
      // 只添加叶子节点（非对象、非数组类型的字段）
      if (meta?.type !== "object" && meta?.type !== "array") {
        candidates.push({
          key: fullKey,
          label: prefix ? `${prefix} > ${label}` : label,
        });
      }
      
      // 如果是物件，递迴展平
      if (meta?.type === "object" && meta?.properties) {
        flattenProperties(meta.properties, fullKey);
      }
    }
  };
  
  flattenProperties(target);
  return candidates;
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

  // Support nested paths with dot notation: "升級轉型動機.升級前後效益比較表"
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
      // Leaf node, cannot drill deeper
      return null;
    }
  }

  return current;
}

function generateNodeId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `node_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

/**
 * 生成默认文档节点结构（参考 exportPlanToWordDefault 的逻辑）
 * 为每个 section 生成：
 * 1. 章节标题 (sectionTitle) - level 1
 * 2. 递归处理 schema properties - level 2+
 *    - 对象 → 次标题 (subHeading) + 递归
 *    - 数组of字符串 → 清单 (list) - 根据深度自动选择样式
 *    - 数组of对象 → 表格 (table) - 根据深度自动选择样式
 *    - 简单值 → 段落 (paragraph)
 */
function generateDefaultNodes(): WordDocumentNode[] {
  const nodes: WordDocumentNode[] = [];

  for (const section of props.sections) {
    // 添加章节标题节点（level 1）
    nodes.push({
      id: generateNodeId(),
      label: section.name,
      type: "sectionTitle",
      sectionId: section.id,
      level: 1,
    });

    // 递归处理 schema properties（从 level 2 开始）
    const schemaProps = section.json_schema?.properties;
    if (schemaProps) {
      const childNodes = generateNodesFromSchema(
        section.id,
        schemaProps,
        "",
        2,
      );
      nodes.push(...childNodes);
    }
  }

  return nodes;
}

/**
 * 根据 level 选择列表样式
 * Level 2: 一、二、三、 (chineseNumber)
 * Level 3: 1、2、3、 (arabicNumber)
 * Level 4: （1）、（2）、（3） (parenNumbered)
 * Level 5+: • (bullet)
 */
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

/**
 * 从 schema properties 递归生成节点
 * 为每个属性创建副标题，然后根据类型创建内容节点
 */
function generateNodesFromSchema(
  sectionId: string,
  properties: Record<string, SchemaField>,
  parentPath: string,
  level: number = 2,
): WordDocumentNode[] {
  const nodes: WordDocumentNode[] = [];

  for (const [key, field] of Object.entries(properties)) {
    const path = parentPath ? `${parentPath}.${key}` : key;
    const label = field.title || key;

    // 为每个属性添加副标题，设置正确的 level
    nodes.push({
      id: generateNodeId(),
      label,
      type: "subHeading",
      sectionId,
      level,
    });

    if (field.type === "array") {
      if (field.items?.properties) {
        // 数组of对象 → 表格，自动展平嵌套对象字段到叶子节点
        const columns: WordTableColumn[] = [];
        
        const flattenTableColumns = (props: Record<string, SchemaField>, prefix = "") => {
          for (const [itemKey, itemField] of Object.entries(props)) {
            const fullKey = prefix ? `${prefix}.${itemKey}` : itemKey;
            const fullLabel = prefix ? `${prefix} > ${itemField.title || itemKey}` : (itemField.title || itemKey);
            
            // 只添加叶子节点（非对象、非数组类型的字段）
            if (itemField?.type !== "object" && itemField?.type !== "array") {
              columns.push({
                key: fullKey,
                label: fullLabel,
              });
            }
            
            // 如果嵌套字段是物件，继续展平
            if (itemField?.type === "object" && itemField?.properties) {
              flattenTableColumns(itemField.properties, fullKey);
            }
          }
        };
        
        flattenTableColumns(field.items.properties);

        nodes.push({
          id: generateNodeId(),
          label: `${label} 表格`,
          type: "table",
          sectionId,
          dataPath: path,
          level: level + 1,
          table: {
            columns,
          },
        });
      } else {
        // 数组of字符串/简单值 → 清单，根据 level 自动选择样式
        nodes.push({
          id: generateNodeId(),
          label: `${label} 清单`,
          type: "list",
          sectionId,
          dataPath: path,
          level: level + 1,
          list: {
            numbering: true,
            style: getListStyleForLevel(level + 1),
          },
        });
      }
    } else if (field.type === "object" && field.properties) {
      // 对象 → 递归处理嵌套属性，递增 level
      const nestedNodes = generateNodesFromSchema(
        sectionId,
        field.properties,
        path,
        level + 1,
      );
      nodes.push(...nestedNodes);
    } else {
      // 简单值 → 段落
      nodes.push({
        id: generateNodeId(),
        label: `${label} 内容`,
        type: "paragraph",
        sectionId,
        dataPath: path,
        level: level + 1,
      });
    }
  }

  return nodes;
}

function ensureNodesRoot(): WordDocumentNode[] {
  if (!formState.value.nodes) {
    formState.value.nodes = [];
  }
  return formState.value.nodes;
}

function createNode(): WordDocumentNode {
  return {
    id: generateNodeId(),
    label: "新節點",
    type: "sectionTitle",
    sectionId: props.sections[0]?.id,
    level: 1,
    children: [],
  };
}

function addNode(parentId?: string) {
  const newNode = createNode();
  if (!parentId) {
    ensureNodesRoot().push(newNode);
    return;
  }
  updateNode(parentId, (parent) => {
    if (!parent.children) {
      parent.children = [];
    }
    parent.children.push(newNode);
  });
}

function findNodeReference(
  nodeId: string,
  nodes: WordDocumentNode[] | undefined = formState.value.nodes,
): { node: WordDocumentNode; siblings: WordDocumentNode[] } | null {
  if (!nodes) return null;
  for (const node of nodes) {
    if (node.id === nodeId) {
      return { node, siblings: nodes };
    }
    if (node.children?.length) {
      const found = findNodeReference(nodeId, node.children);
      if (found) {
        return found;
      }
    }
  }
  return null;
}

function updateNode(
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
): void {
  const reference = findNodeReference(nodeId);
  if (!reference) return;
  updater(reference.node);
}

function removeNode(nodeId: string) {
  const reference = findNodeReference(nodeId);
  if (!reference) return;
  const index = reference.siblings.indexOf(reference.node);
  if (index >= 0) {
    reference.siblings.splice(index, 1);
  }
}

function moveNode(nodeId: string, direction: "up" | "down") {
  const reference = findNodeReference(nodeId);
  if (!reference) return;
  const index = reference.siblings.indexOf(reference.node);
  const targetIndex = direction === "up" ? index - 1 : index + 1;
  if (targetIndex < 0 || targetIndex >= reference.siblings.length) return;
  const temp = reference.siblings[targetIndex]!;
  reference.siblings[targetIndex] = reference.node;
  reference.siblings[index] = temp;
}

function handleNodeSectionChange(nodeId: string) {
  updateNode(nodeId, (node) => {
    node.dataPath = "";
    handleNodeDataPathChange(nodeId);
  });
}

function handleNodeTypeChange(nodeId: string) {
  updateNode(nodeId, (node) => {
    if (node.type !== "table") {
      delete node.table;
    }
    if (node.type !== "list") {
      delete node.list;
    }
    if (!shouldShowSectionSelectors(node)) {
      node.sectionId = "";
      node.dataPath = "";
    }
  });
}

function handleNodeDataPathChange(nodeId: string) {
  updateNode(nodeId, (node) => {
    if (node.type === "table" && node.table?.columns?.length) {
      const allow = new Set(
        getNodeColumnCandidates(node).map((option) => option.key),
      );
      node.table.columns = node.table.columns.filter((column) =>
        allow.has(column.key),
      );
    }
  });
}

/**
 * Parse dataPath into path segments
 * Example: "升級轉型動機.升級前後效益比較表" → ["升級轉型動機", "升級前後效益比較表"]
 */
function parseDataPath(dataPath?: string): string[] {
  if (!dataPath) return [];
  return dataPath.split(".").filter((p) => p.length > 0);
}

/**
 * Build dataPath from path segments
 * Example: ["升級轉型動機", "升級前後效益比較表"] → "升級轉型動機.升級前後效益比較表"
 */
function buildDataPath(segments: string[]): string {
  return segments.join(".");
}

/**
 * Get cascading dropdown levels for a node's dataPath
 * Returns array of available options at each nesting level
 */
function getDataPathLevels(
  node: WordDocumentNode,
): Array<{ value: string; label: string }[]> {
  if (!node.sectionId) return [];

  const currentSegments = parseDataPath(node.dataPath);
  const levels: Array<{ value: string; label: string }[]> = [];

  // Level 0: Top-level properties
  levels.push(getDataPathOptions(node.sectionId));

  // Levels 1+: Nested properties based on selected path so far
  for (let i = 0; i < currentSegments.length; i++) {
    const pathSoFar = buildDataPath(currentSegments.slice(0, i + 1));
    const nextLevel = getNestedPathOptions(node.sectionId, pathSoFar);
    if (nextLevel.length === 0) break; // No more nesting possible
    levels.push(nextLevel);
  }

  return levels;
}

/**
 * Check if there are more nesting levels available from current path
 */
function canNestDeeper(node: WordDocumentNode): boolean {
  if (!node.sectionId) return false;
  const currentSegments = parseDataPath(node.dataPath);
  const pathSoFar = node.dataPath || "";
  const nextOptions = getNestedPathOptions(node.sectionId, pathSoFar);
  return nextOptions.length > 0;
}

/**
 * Handle cascading dropdown level change
 */
function handleDataPathLevelChange(
  nodeId: string,
  levelIndex: number,
  value: string,
): void {
  updateNode(nodeId, (node) => {
    const segments = parseDataPath(node.dataPath);

    if (value === "") {
      // Clear this level and all deeper levels
      segments.splice(levelIndex);
    } else {
      // Set this level and clear all deeper levels
      segments[levelIndex] = value;
      segments.splice(levelIndex + 1);
    }

    node.dataPath = buildDataPath(segments);
    handleNodeDataPathChange(nodeId);
  });
}

/**
 * Handle adding another nesting level
 */
function handleAddDataPathLevel(nodeId: string): void {
  // Just render another dropdown - the user will select from it
  // The cascading dropdown UI will automatically show the next level
  // when the current path becomes non-empty
}

function getNodeDataPathOptions(node: WordDocumentNode) {
  if (!node.sectionId) return [];
  return getDataPathOptions(node.sectionId);
}

function getNodeColumnCandidates(node: WordDocumentNode) {
  if (!node.sectionId) return [];
  return getColumnCandidates(node.sectionId, node.dataPath);
}

function ensureTableConfig(node: WordDocumentNode) {
  if (!node.table) {
    node.table = { columns: [] };
  }
  if (!node.table.columns) {
    node.table.columns = [];
  }
  return node.table;
}

function ensureListConfig(node: WordDocumentNode) {
  if (!node.list) {
    node.list = {
      numbering: true,
      style: node.level ? getListStyleForLevel(node.level) : "chineseNumber",
    };
  }
  if (!node.list.style) {
    node.list.style = node.level
      ? getListStyleForLevel(node.level)
      : "chineseNumber";
  }
  return node.list;
}

function ensureNodeStyle(node: WordDocumentNode) {
  if (!node.style) {
    node.style = {};
  }
  return node.style;
}

function toggleNodeColumnForNode(
  nodeId: string,
  option: WordTableColumn,
  checked?: boolean,
) {
  updateNode(nodeId, (node) => {
    const table = ensureTableConfig(node);
    if (checked) {
      if (!table.columns.find((column) => column.key === option.key)) {
        table.columns.push({ ...option });
      }
    } else {
      table.columns = table.columns.filter(
        (column) => column.key !== option.key,
      );
    }
  });
}

function onNodeColumnToggle(
  nodeId: string,
  option: WordTableColumn,
  event: Event,
) {
  const target = event.target as HTMLInputElement | undefined;
  toggleNodeColumnForNode(nodeId, option, target?.checked);
}

function shouldShowTemplateInput(node: WordDocumentNode) {
  return node.type === "customText";
}

function shouldShowNodeLabel(node: WordDocumentNode) {
  return !["paragraph", "table", "list", "customText"].includes(node.type);
}

function shouldShowSectionSelectors(node: WordDocumentNode) {
  return !["sectionTitle", "subHeading", "customText"].includes(node.type);
}

function walkNodes(
  nodes: WordDocumentNode[] | undefined,
  callback: (node: WordDocumentNode) => boolean | void,
): boolean {
  if (!nodes) return false;
  for (const node of nodes) {
    const shouldStop = callback(node);
    if (shouldStop) {
      return true;
    }
    if (node.children?.length && walkNodes(node.children, callback)) {
      return true;
    }
  }
  return false;
}

function deepClone<T>(value: T): T {
  return typeof structuredClone === "function"
    ? structuredClone(value)
    : JSON.parse(JSON.stringify(value));
}

function handleSave() {
  let invalidNodes = false;
  walkNodes(formState.value.nodes, (node) => {
    if (
      node.type === "table" &&
      (!node.table?.columns || !node.table.columns.length)
    ) {
      invalidNodes = true;
      return true;
    }
    return false;
  });

  if (invalidNodes) {
    notifyError("有節點的表格尚未選擇欄位");
    return;
  }

  emit("save", deepClone(formState.value));
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-TW");
}

/**
 * Generate dummy data for a section based on its schema
 */
function generateDummyData(section: SectionRecord): Record<string, any> {
  const schema = section.json_schema?.properties;
  if (!schema) return {};

  const dummy: Record<string, any> = {};

  const generateValueFromSchema = (
    field: SchemaField,
    fieldKey: string,
  ): any => {
    if (field.type === "array") {
      const items = [];
      if (field.items?.properties) {
        // Array of objects
        for (let i = 0; i < 2; i++) {
          const item: Record<string, any> = {};
          for (const [key, itemField] of Object.entries(
            field.items.properties,
          )) {
            item[key] = generateValueFromSchema(itemField, key);
          }
          items.push(item);
        }
      } else {
        // Array of simple values
        items.push(`範例${fieldKey}數據1`, `範例${fieldKey}數據2`);
      }
      return items;
    } else if (field.type === "object" && field.properties) {
      const obj: Record<string, any> = {};
      for (const [key, subField] of Object.entries(field.properties)) {
        obj[key] = generateValueFromSchema(subField, key);
      }
      return obj;
    } else if (
      field.type === "number" ||
      fieldKey.includes("金額") ||
      fieldKey.includes("數量")
    ) {
      return Math.floor(Math.random() * 10000) + 1000;
    } else {
      return `${field.title || fieldKey}的示例內容`;
    }
  };

  for (const [key, field] of Object.entries(schema)) {
    dummy[key] = generateValueFromSchema(field, key);
  }

  return dummy;
}

/**
 * Render a node with dummy data for preview
 */
function renderNodePreview(
  node: WordDocumentNode,
  sectionDataMap: Record<string, Record<string, any>>,
  headingCounters: HeadingCounterState,
): string {
  const indent = (node.level || 1) * 20;

  let html = `<div style="margin-left: ${indent}px; margin-bottom: 12px;">`;

  if (node.type === "sectionTitle") {
    resetHeadingCounters(headingCounters);
    const fontSize = formState.value.documentStyle.headingSizePt || 18;
    html += `<h2 style="font-size: ${fontSize}pt; font-weight: bold; margin: 12px 0;">
      ${node.label || "章節標題"}
    </h2>`;
  } else if (node.type === "subHeading") {
    const fontSize = formState.value.documentStyle.subHeadingSizePt || 14;
    const prefix = formatHeadingPrefix(node.level, headingCounters);
    html += `<h3 style="font-size: ${fontSize}pt; font-weight: bold; margin: 8px 0;">
      ${prefix}${node.label || "次標題"}
    </h3>`;
  } else if (node.type === "paragraph") {
    const fontSize = formState.value.documentStyle.bodySizePt || 12;
    const sectionData = node.sectionId
      ? sectionDataMap[node.sectionId]
      : null;
    const value = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : `${node.label || "段落內容"} (無資料)`;
    html += `<p style="font-size: ${fontSize}pt; margin: 6px 0;">
      ${node.label}: ${value}
    </p>`;
  } else if (node.type === "table") {
    const sectionData = node.sectionId
      ? sectionDataMap[node.sectionId]
      : null;
    const tableData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const rows = Array.isArray(tableData) ? tableData : [];
    const columns = node.table?.columns || [];

    html += `<table style="width: 100%; border-collapse: collapse; margin: 8px 0;">
      <thead>
        <tr style="background-color: #f0f0f0;">`;
    for (const col of columns) {
      html += `<th style="border: 1px solid #ccc; padding: 6px;">${col.label}</th>`;
    }
    html += `</tr></thead><tbody>`;
    for (const row of rows) {
      html += `<tr>`;
      for (const col of columns) {
        const cellValue = typeof row === "object" ? getValueByPath(row, col.key) : row;
        html += `<td style="border: 1px solid #ccc; padding: 6px;">${cellValue}</td>`;
      }
      html += `</tr>`;
    }
    html += `</tbody></table>`;
  } else if (node.type === "list") {
    const sectionData = node.sectionId
      ? sectionDataMap[node.sectionId]
      : null;
    const listData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const items = Array.isArray(listData) ? listData : [listData];

    html += `<ul style="margin: 6px 0; padding-left: 20px;">`;
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      const bullet = node.list?.numbering
        ? getListBulletLabel(node.list?.style, i)
        : "•";
      html += `<li>${bullet} ${item}</li>`;
    }
    html += `</ul>`;
  } else if (node.type === "customText") {
    html += `<div style="margin: 6px 0;">
      ${node.template || "自訂文字"}
    </div>`;
  }

  html += `</div>`;

  return html;
}

/**
 * Get value from object by dot-notation path
 */
function getValueByPath(
  obj: Record<string, any>,
  path?: string,
): any {
  if (!path || !obj) return obj;
  const parts = path.split(".");
  let current = obj;
  for (const part of parts) {
    if (current && typeof current === "object") {
      current = current[part];
    } else {
      return null;
    }
  }
  return current;
}

/**
 * Generate HTML preview of the document
 */
function generatePreviewHtml(): string {
  // Generate dummy data for all sections
  const sectionDataMap: Record<string, Record<string, any>> = {};
  for (const section of props.sections) {
    sectionDataMap[section.id] = generateDummyData(section);
  }

  const headingCounters = createHeadingCounterState();

  // Render all nodes
  let html = `
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
      <meta charset="UTF-8">
      <title>Word 導出預覽</title>
      <style>
        body {
          font-family: ${formState.value.documentStyle.bodyFont || "Times New Roman"};
          font-size: ${formState.value.documentStyle.bodySizePt || 12}pt;
          margin: 40px;
          line-height: 1.6;
          color: #333;
        }
        .preview-container {
          max-width: 900px;
          margin: 0 auto;
          background: white;
          padding: 40px;
          border: 1px solid #eee;
        }
        h2 {
          font-family: ${formState.value.documentStyle.headingFont || "Times New Roman"};
          font-size: ${formState.value.documentStyle.headingSizePt || 18}pt;
          font-weight: ${formState.value.documentStyle.headingBold ? "bold" : "normal"};
          margin-top: 20px;
          margin-bottom: 12px;
        }
        h3 {
          font-family: ${formState.value.documentStyle.subHeadingFont || "Times New Roman"};
          font-size: ${formState.value.documentStyle.subHeadingSizePt || 14}pt;
          font-weight: ${formState.value.documentStyle.subHeadingBold ? "bold" : "normal"};
          margin-top: 14px;
          margin-bottom: 8px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin: 12px 0;
          font-size: ${formState.value.documentStyle.bodySizePt || 12}pt;
        }
        th, td {
          border: 1px solid #999;
          padding: 8px;
          text-align: left;
        }
        th {
          background-color: #e8e8e8;
          font-weight: bold;
        }
        ul {
          margin: 8px 0;
          padding-left: 24px;
        }
        li {
          margin: 4px 0;
        }
        p {
          margin: 6px 0;
        }
      </style>
    </head>
    <body>
      <div class="preview-container">
  `;

  if (!formState.value.nodes || formState.value.nodes.length === 0) {
    html += "<p style='color: #999;'>尚未設定任何節點。</p>";
  } else {
    for (const node of formState.value.nodes) {
      html += renderNodePreview(node, sectionDataMap, headingCounters);
    }
  }

  html += `
      </div>
    </body>
    </html>
  `;

  return html;
}

async function handlePreviewExport() {
  try {
    const previewHtml = generatePreviewHtml();

    // Open preview in a new window
    const previewWindow = window.open("", "_blank");
    if (previewWindow) {
      previewWindow.document.write(previewHtml);
      previewWindow.document.close();
    } else {
      notifyError("無法開啟預覽視窗，請檢查瀏覽器設定");
    }
  } catch (err) {
    notifyError(
      `預覽生成失敗: ${err instanceof Error ? err.message : "未知錯誤"}`,
    );
  }
}

/**
 * Build docx Paragraph elements from node
 */
function buildParagraphsFromNode(
  node: WordDocumentNode,
  sectionDataMap: Record<string, Record<string, any>>,
  headingCounters: HeadingCounterState,
): Array<Paragraph | Table> {
  const elements: Array<Paragraph | Table> = [];

  if (node.type === "sectionTitle") {
    resetHeadingCounters(headingCounters);
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: node.label || "章節標題",
            bold: formState.value.documentStyle.headingBold ?? true,
            size: (formState.value.documentStyle.headingSizePt ?? 18) * 2,
            font: formState.value.documentStyle.headingFont || "Times New Roman",
          }),
        ],
        spacing: { before: 200, after: 120 },
      }),
    );
  } else if (node.type === "subHeading") {
    const prefix = formatHeadingPrefix(node.level, headingCounters);
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: `${prefix}${node.label || "次標題"}`,
            bold: formState.value.documentStyle.subHeadingBold ?? true,
            size: (formState.value.documentStyle.subHeadingSizePt ?? 14) * 2,
            font: formState.value.documentStyle.subHeadingFont || "Times New Roman",
          }),
        ],
        spacing: { before: 120, after: 80 },
      }),
    );
  } else if (node.type === "paragraph") {
    const sectionData = node.sectionId
      ? sectionDataMap[node.sectionId]
      : null;
    const value = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : `${node.label || "段落內容"} (無資料)`;
    const text = `${node.label}: ${value}`;

    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text,
            size: (formState.value.documentStyle.bodySizePt ?? 12) * 2,
            font: formState.value.documentStyle.bodyFont || "Times New Roman",
            bold: formState.value.documentStyle.bodyBold ?? false,
          }),
        ],
        spacing: { after: 60 },
        alignment: node.style?.alignment
          ? getAlignmentType(node.style.alignment)
          : AlignmentType.LEFT,
      }),
    );
  } else if (node.type === "table") {
    const sectionData = node.sectionId
      ? sectionDataMap[node.sectionId]
      : null;
    const tableData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const rows = Array.isArray(tableData) ? tableData : [];
    const columns = node.table?.columns || [];

    if (columns.length > 0) {
      // Build table header
      const headerCells = columns.map(
        (col) =>
          new TableCell({
            children: [
              new Paragraph({
                children: [
                  new TextRun({
                    text: col.label,
                    bold: true,
                    size: (formState.value.documentStyle.bodySizePt ?? 12) * 2,
                  }),
                ],
              }),
            ],
          }),
      );

      // Build table rows
      const dataCells = rows.map(
        (row) =>
          new TableRow({
            children: columns.map(
              (col) =>
                new TableCell({
                  children: [
                    new Paragraph({
                      children: [
                        new TextRun({
                          text: String(
                            typeof row === "object" ? (getValueByPath(row, col.key) ?? "") : row,
                          ),
                          size: (formState.value.documentStyle.bodySizePt ??
                            12) * 2,
                        }),
                      ],
                    }),
                  ],
                }),
            ),
          }),
      );

      elements.push(
        new Table({
          rows: [new TableRow({ children: headerCells }), ...dataCells],
          width: { size: 100, type: "pct" },
        }),
      );
    }
  } else if (node.type === "list") {
    const sectionData = node.sectionId
      ? sectionDataMap[node.sectionId]
      : null;
    const listData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const items = Array.isArray(listData) ? listData : [listData];

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      const bullet = node.list?.numbering
        ? getListBulletLabel(node.list?.style, i)
        : "•";

      elements.push(
        new Paragraph({
          children: [
            new TextRun({
              text: `${bullet} ${item}`,
              size: (formState.value.documentStyle.bodySizePt ?? 12) * 2,
              font: formState.value.documentStyle.bodyFont || "Times New Roman",
            }),
          ],
          spacing: { after: 40 },
          indent: { left: 720 },
        }),
      );
    }
  } else if (node.type === "customText") {
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: node.template || "自訂文字",
            size: (formState.value.documentStyle.bodySizePt ?? 12) * 2,
            font: formState.value.documentStyle.bodyFont || "Times New Roman",
          }),
        ],
        spacing: { after: 60 },
      }),
    );
  }

  return elements;
}

/**
 * Convert alignment string to docx AlignmentType
 */
function getAlignmentType(
  alignment?: string,
): typeof AlignmentType[keyof typeof AlignmentType] {
  switch (alignment) {
    case "center":
      return AlignmentType.CENTER;
    case "right":
      return AlignmentType.RIGHT;
    case "left":
    default:
      return AlignmentType.LEFT;
  }
}

/**
 * Generate docx document from current form state
 */
async function generateDocxDocument(): Promise<Blob> {
  // Generate dummy data for all sections
  const sectionDataMap: Record<string, Record<string, any>> = {};
  for (const section of props.sections) {
    sectionDataMap[section.id] = generateDummyData(section);
  }

  // Build document body
  const documentElements: Array<Paragraph | Table> = [];
  const headingCounters = createHeadingCounterState();

  if (formState.value.nodes && formState.value.nodes.length > 0) {
    for (const node of formState.value.nodes) {
      const elements = buildParagraphsFromNode(
        node,
        sectionDataMap,
        headingCounters,
      );
      documentElements.push(...elements);
    }
  } else {
    documentElements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "尚未設定任何節點。",
            size: 12 * 2,
            color: "999999",
          }),
        ],
      }),
    );
  }

  const doc = new Document({
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: convertInchesToTwip(1),
              right: convertInchesToTwip(1),
              bottom: convertInchesToTwip(1),
              left: convertInchesToTwip(1),
            },
          },
        },
        children: documentElements,
      },
    ],
  });

  return await Packer.toBlob(doc);
}

/**
 * Download document as Word file
 */
async function handleDownloadWord() {
  try {
    const blob = await generateDocxDocument();

    // Create download link
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${props.template?.name || "文檔"}_預覽.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    notifyError(
      `下載失敗: ${err instanceof Error ? err.message : "未知錯誤"}`,
    );
  }
}
</script>
