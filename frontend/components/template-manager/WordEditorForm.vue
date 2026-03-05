<template>
  <div
    v-if="isVisible && template"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 py-6"
    @click.self="emit('close')"
  >
    <section
      class="w-full max-w-8xl max-h-full overflow-y-auto rounded-2xl bg-white p-6 space-y-6 shadow-2xl"
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

      <div class="grid gap-6 lg:grid-cols-[1fr,1fr]">
        <div class="space-y-6 overflow-y-auto max-h-[calc(100vh-12rem)]">
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

          <section class="rounded-2xl border border-slate-200 p-4 space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-base font-semibold text-slate-800">
                文件字體設定
              </h3>
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
                  文檔章節流程
                </h3>
                <p class="text-xs text-slate-500">
                  建立節點樹以控制標題、段落、表格、清單與條件顯示，匯出時會依序渲染。
                </p>
              </div>
              <div class="flex flex-col gap-2 sm:flex-row">
                <button
                  type="button"
                  class="rounded-lg border border-slate-300 px-3 py-1 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  @click="addNode()"
                >
                  新增章節
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
                class="flex items-center gap-2 overflow-x-auto rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm"
              >
                <button
                  v-for="chapter in groupedNodes"
                  :key="`tab-${chapter.id}`"
                  type="button"
                  class="shrink-0 rounded-xl px-3 py-1 font-semibold"
                  :class="[
                    selectedChapterId === chapter.id
                      ? 'bg-rose-500 text-white'
                      : 'text-slate-600 hover:text-rose-500',
                  ]"
                  @click="selectedChapterId = chapter.id"
                >
                  {{ chapter.title || "未命名章節" }}
                </button>
              </div>

              <details
                v-for="(chapter, chapterIndex) in filteredChapters"
                :key="chapter.id"
                class="rounded-2xl border border-slate-200 bg-white overflow-hidden"
                :open="chapterIndex === 0"
              >
                <summary
                  class="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50"
                >
                  <div class="flex items-center gap-3">
                    <span class="text-sm font-semibold text-slate-700">{{
                      chapter.title || "未命名章節"
                    }}</span>
                    <span class="text-xs text-slate-500"
                      >({{ chapter.contentNodes.length }} 個節點)</span
                    >
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      class="text-xs text-slate-600 hover:text-slate-700 rounded-lg border border-slate-200 px-2 py-1"
                      @click.stop="editChapterTitle(chapter.id)"
                      title="編輯章節標題"
                    >
                      編輯
                    </button>
                    <button
                      type="button"
                      class="text-xs rounded-lg border border-slate-200 px-2 py-1 text-slate-600 disabled:opacity-40"
                      :disabled="getChapterGlobalIndex(chapter.id) === 0"
                      @click.stop="moveChapter(chapter.id, 'up')"
                      title="上移章節"
                    >
                      ↑
                    </button>
                    <button
                      type="button"
                      class="text-xs rounded-lg border border-slate-200 px-2 py-1 text-slate-600 disabled:opacity-40"
                      :disabled="
                        getChapterGlobalIndex(chapter.id) ===
                        groupedNodes.length - 1
                      "
                      @click.stop="moveChapter(chapter.id, 'down')"
                      title="下移章節"
                    >
                      ↓
                    </button>
                    <button
                      type="button"
                      class="text-xs text-rose-600 hover:text-rose-700 rounded-lg border border-rose-200 px-2 py-1"
                      @click.stop="removeChapter(chapter.id)"
                      title="刪除章節"
                    >
                      刪除
                    </button>
                  </div>
                </summary>
                <div class="p-4 space-y-4 border-t border-slate-200">
                  <div
                    v-for="(node, nodeIndex) in chapter.contentNodes"
                    :key="node.id"
                    class="rounded-xl border border-slate-200 p-4 space-y-4 bg-white"
                  >
                    <div class="flex items-center justify-end gap-2 text-xs">
                      <button
                        type="button"
                        class="rounded-lg border border-slate-200 px-2 py-1 text-slate-600 disabled:opacity-40"
                        :disabled="nodeIndex === 0"
                        @click="moveNode(node.id, 'up')"
                      >
                        上移
                      </button>
                      <button
                        type="button"
                        class="rounded-lg border border-slate-200 px-2 py-1 text-slate-600 disabled:opacity-40"
                        :disabled="
                          nodeIndex === chapter.contentNodes.length - 1
                        "
                        @click="moveNode(node.id, 'down')"
                      >
                        下移
                      </button>
                    </div>

                    <RecursiveNodeEditor
                      :node="node"
                      :parent-node-id="chapter.id"
                      :parent-level="0"
                      :section-options="sectionOptions"
                      :sections="sections"
                      :level="0"
                      :node-type-options="NODE_TYPE_OPTIONS"
                      :list-style-options="LIST_STYLE_OPTIONS"
                      @update="handleRecursiveNodeUpdate"
                      @remove="handleRecursiveNodeRemove"
                      @add-child="handleRecursiveNodeAddChild"
                    />
                    <div class="flex justify-end pt-2">
                      <button
                        type="button"
                        class="rounded-lg border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                        @click="addNodeAfterNode(node.id, chapter.id)"
                      >
                        + 新增節點
                      </button>
                    </div>
                  </div>

                  <div
                    class="flex justify-end pt-2"
                    v-if="chapter.contentNodes.length === 0"
                  >
                    <button
                      type="button"
                      class="rounded-lg border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                      @click="addNodeToChapter(chapter.id)"
                    >
                      + 新增節點
                    </button>
                  </div>
                </div>
              </details>

              <div class="flex justify-center pt-2">
                <button
                  type="button"
                  class="text-xs text-rose-600 hover:text-rose-700 font-semibold"
                  @click="addChapterMarker"
                >
                  + 添加章節分組
                </button>
              </div>
            </div>
          </section>
        </div>

        <aside
          class="rounded-2xl border border-slate-200 bg-slate-50 p-4 flex flex-col lg:sticky lg:top-6 max-h-[calc(100vh-12rem)]"
        >
          <div class="flex items-center justify-between mb-3 flex-shrink-0">
            <h3 class="text-sm font-semibold text-slate-700">即時預覽</h3>
          </div>
          <p class="text-xs text-slate-500 mb-4 flex-shrink-0">
            預覽文檔的渲染效果，會即時反映您的更改。
          </p>
          <div
            class="rounded-xl border border-slate-200 bg-white overflow-auto flex-1 min-h-0"
            ref="previewContainerRef"
          >
            <iframe
              ref="previewIframeRef"
              :srcdoc="debouncedPreviewHtml"
              class="w-full h-full border-0"
              title="文檔預覽"
              @load="handleIframeLoad"
            />
          </div>
        </aside>
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
import { useWordDownload } from "~/composables/template-manager/useWordDownload";
import {
  createCustomTableNodeHelpers,
  resolveNodeScopedPath,
} from "~/composables/template-manager/useCustomTableNode";
import { useWordPreview } from "~/composables/template-manager/useWordPreview";
import { parseDataPath } from "~/composables/template-manager/useWordSchemaPath";
import {
  addChildNodeById,
  moveNodeById,
  removeNodeById,
  updateNodeById,
  walkWordNodes,
} from "~/composables/template-manager/useWordNodeTree";
import {
  createHeadingCounterState,
  formatHeadingPrefix,
  getListBulletLabel,
  resetHeadingCounters,
  shouldUseParagraphSubHeadingStyle,
  type HeadingCounterState,
} from "~/composables/template-manager/useWordNumbering";
import { buildPreviewSectionDataMap } from "~/composables/template-manager/useWordPreviewSampleData";
import { exportPlanUsingWordConfig } from "~/utils/exportToWord";
import RecursiveNodeEditor from "./RecursiveNodeEditor.vue";
import type {
  WordDocumentNode,
  WordDocumentNodeType,
  WordExportConfigEntry,
  WordExportTemplateConfig,
  WordTableColumn,
  WordCustomTableCell,
  WordCustomTableCellContent,
} from "~/types/wordExport";

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
    { label: "次標題", value: "subHeading" },
    { label: "段落文字", value: "paragraph" },
    { label: "表格", value: "table" },
    { label: "自訂表格", value: "customTable" },
    { label: "清單", value: "list" },
    { label: "自訂文字", value: "customText" },
  ];

const LIST_STYLE_OPTIONS = [
  { label: "一、 二、 三、", value: "chineseNumber" },
  { label: "1. 2. 3.", value: "arabicNumber" },
  { label: "（1）、（2）、（3）", value: "parenNumbered" },
  { label: "• ◦ ▪", value: "bullet" },
];

const { ensureCustomTableConfig } =
  createCustomTableNodeHelpers(generateNodeId);

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

// 章節分組接口
interface ChapterGroup {
  id: string;
  title: string;
  nodes: WordDocumentNode[];
  contentNodes: WordDocumentNode[];
  isManual?: boolean; // 是否為手動添加的章節標記
}

// 章節分組邏輯
const groupedNodes = computed<ChapterGroup[]>(() => {
  if (!formState.value.nodes || formState.value.nodes.length === 0) {
    return [];
  }

  const groups: ChapterGroup[] = [];
  let currentChapter: ChapterGroup | null = null;

  const pushCurrentChapter = () => {
    if (currentChapter) {
      groups.push(currentChapter);
    }
  };

  for (const node of formState.value.nodes) {
    const isChapterMarker =
      node.type === "sectionTitle" || node.chapterMarker === true;

    if (isChapterMarker) {
      pushCurrentChapter();
      currentChapter = {
        id: node.id,
        title: node.chapterTitle ?? node.label ?? "未命名章節",
        nodes: [node],
        contentNodes: [],
        isManual: node.chapterMarker === true,
      };
      continue;
    }

    if (!currentChapter) {
      currentChapter = {
        id: `default-${groups.length}`,
        title: "未分組",
        nodes: [],
        contentNodes: [],
        isManual: false,
      };
    }

    currentChapter.nodes.push(node);
    currentChapter.contentNodes.push(node);
  }

  pushCurrentChapter();

  return groups;
});

const selectedChapterId = ref<string>("");

const filteredChapters = computed(() => {
  return groupedNodes.value.filter(
    (group) => group.id === selectedChapterId.value,
  );
});

function getNodeGlobalIndex(nodeId: string): number {
  if (!formState.value.nodes) return -1;
  return formState.value.nodes.findIndex((n) => n.id === nodeId);
}

function getChapterGlobalIndex(chapterId: string): number {
  return groupedNodes.value.findIndex((group) => group.id === chapterId);
}

function moveChapter(chapterId: string, direction: "up" | "down") {
  const allNodes = ensureNodesRoot();
  const currentChapterIndex = getChapterGlobalIndex(chapterId);

  if (direction === "up" && currentChapterIndex <= 0) return;
  if (
    direction === "down" &&
    currentChapterIndex >= groupedNodes.value.length - 1
  )
    return;

  const targetChapterIndex =
    direction === "up" ? currentChapterIndex - 1 : currentChapterIndex + 1;
  const currentChapter = groupedNodes.value[currentChapterIndex];
  const targetChapter = groupedNodes.value[targetChapterIndex];

  if (!currentChapter || !targetChapter) return;

  // 找到章节在所有节点中的范围
  const currentStartIndex = allNodes.findIndex(
    (n) => n.id === currentChapter.nodes[0]?.id,
  );
  const currentEndIndex = currentStartIndex + currentChapter.nodes.length - 1;

  const targetStartIndex = allNodes.findIndex(
    (n) => n.id === targetChapter.nodes[0]?.id,
  );
  const targetEndIndex = targetStartIndex + targetChapter.nodes.length - 1;

  if (currentStartIndex === -1 || targetStartIndex === -1) return;

  // 提取当前章节和目标章节的所有节点
  const currentChapterNodes = allNodes.splice(
    currentStartIndex,
    currentChapter.nodes.length,
  );

  // 计算新的插入位置
  let insertIndex: number;
  if (direction === "up") {
    // 上移：insert before 目标章节
    insertIndex = allNodes.findIndex(
      (n) => n.id === targetChapter.nodes[0]?.id,
    );
  } else {
    // 下移：insert after 目标章节
    const newTargetEndIndex = allNodes.findIndex(
      (n) => n.id === targetChapter.nodes[targetChapter.nodes.length - 1]?.id,
    );
    insertIndex = newTargetEndIndex + 1;
  }

  allNodes.splice(insertIndex, 0, ...currentChapterNodes);
}

function addChapterMarker() {
  const newNode: WordDocumentNode = {
    id: generateNodeId(),
    type: "sectionTitle",
    label: "新章節",
    chapterMarker: true,
    chapterTitle: "新章節",
    level: 1,
  };
  ensureNodesRoot().push(newNode);
}

function addNodeAfterNode(nodeId: string, chapterId: string) {
  const nodes = ensureNodesRoot();
  const chapter = groupedNodes.value.find((group) => group.id === chapterId);
  const chapterNodes = chapter?.contentNodes ?? [];
  const referenceNode = chapterNodes[chapterNodes.length - 1];
  const newNode = createNode({
    type: "paragraph",
    label: "新節點內容",
    level: calculateNodeLevelFromDataPath(""),
    sectionId: referenceNode?.sectionId || props.sections[0]?.id,
    chapterMarker: false,
  });

  const insertAfterIndex = getNodeGlobalIndex(nodeId);
  if (insertAfterIndex === -1) {
    nodes.push(newNode);
    return;
  }

  nodes.splice(insertAfterIndex + 1, 0, newNode);
}

function addNodeToChapter(chapterId: string) {
  const nodes = ensureNodesRoot();
  const chapter = groupedNodes.value.find((group) => group.id === chapterId);
  const chapterNodes = chapter?.nodes ?? [];
  const referenceNode = chapterNodes[chapterNodes.length - 1];
  const newNode = createNode({
    type: "paragraph",
    label: "新節點內容",
    level: calculateNodeLevelFromDataPath(""),
    sectionId: referenceNode?.sectionId || props.sections[0]?.id,
    chapterMarker: false,
  });

  if (!chapter || chapterNodes.length === 0) {
    nodes.push(newNode);
    return;
  }

  const lastNode = chapterNodes[chapterNodes.length - 1];
  if (!lastNode) {
    nodes.push(newNode);
    return;
  }

  const lastIndex = getNodeGlobalIndex(lastNode.id);
  if (lastIndex === -1) {
    nodes.push(newNode);
    return;
  }

  nodes.splice(lastIndex + 1, 0, newNode);
}

function editChapterTitle(chapterId: string) {
  const chapter = groupedNodes.value.find((group) => group.id === chapterId);
  const currentTitle = chapter?.title ?? "";
  const nextTitle = prompt("請輸入章節標題：", currentTitle);
  if (nextTitle === null) return;
  const trimmed = nextTitle.trim();
  if (!trimmed) return;
  updateNode(chapterId, (node) => {
    node.chapterTitle = trimmed;
    node.label = trimmed;
  });
}

function removeChapter(chapterId: string) {
  const chapter = groupedNodes.value.find((group) => group.id === chapterId);
  if (!chapter) return;

  if (!confirm("確定要刪除這個章節嗎？章節下的所有節點也會被刪除。")) {
    return;
  }

  const nodes = ensureNodesRoot();
  const idsToRemove = new Set(chapter.nodes.map((node) => node.id));

  formState.value.nodes = nodes.filter((node) => !idsToRemove.has(node.id));
}

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

watch(
  groupedNodes,
  (groups) => {
    if (!groups.length) {
      selectedChapterId.value = "";
      return;
    }
    if (
      !selectedChapterId.value ||
      !groups.some((group) => group.id === selectedChapterId.value)
    ) {
      const fallback = groups[0];
      if (fallback) {
        selectedChapterId.value = fallback.id;
      }
    }
  },
  { immediate: true },
);

function initializeNodeDefaults(nodes?: WordDocumentNode[]) {
  if (!nodes) return;
  nodes.forEach((node) => {
    if (!node) return;
    if (node.type === "customTable") {
      ensureCustomTableConfig(node);
    }
    if (node.children?.length) {
      initializeNodeDefaults(node.children);
    }
  });
}

function hydrateForm(base?: WordExportTemplateConfig) {
  try {
    const documentStyle = {
      ...DEFAULT_STYLE,
      ...(base?.documentStyle || {}),
    };

    // 使用 JSON 序列化确保数据可用，避免 Vue 响应式代理问题
    const layouts = base?.sectionLayouts
      ? JSON.parse(JSON.stringify(base.sectionLayouts))
      : [];

    const nodes =
      base?.nodes && base.nodes.length > 0
        ? JSON.parse(JSON.stringify(base.nodes))
        : generateDefaultNodes();

    initializeNodeDefaults(nodes);

    formState.value = {
      documentStyle,
      sectionLayouts: layouts,
      nodes,
    };
  } catch (error) {
    console.error("Error hydrating form:", error);
    // 使用默认值
    formState.value = {
      documentStyle: { ...DEFAULT_STYLE },
      sectionLayouts: [],
      nodes: generateDefaultNodes(),
    };
  }
}

function applyVersion(version: WordExportConfigEntry) {
  hydrateForm(version.config);
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

        const flattenTableColumns = (
          props: Record<string, SchemaField>,
          prefix = "",
        ) => {
          for (const [itemKey, itemField] of Object.entries(props)) {
            const fullKey = prefix ? `${prefix}.${itemKey}` : itemKey;
            const fullLabel = prefix
              ? `${prefix} > ${itemField.title || itemKey}`
              : itemField.title || itemKey;

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
            style: "chineseNumber",
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

function createNode(
  overrides: Partial<WordDocumentNode> = {},
): WordDocumentNode {
  return {
    id: generateNodeId(),
    label: overrides.label ?? "新節點",
    type: overrides.type ?? "paragraph",
    sectionId: overrides.sectionId ?? props.sections[0]?.id,
    level: overrides.level ?? 1,
    children: overrides.children ?? [],
    ...overrides,
  };
}

function addNode(parentId?: string) {
  const newNode = createNode();
  if (!parentId) {
    ensureNodesRoot().push(newNode);
    return;
  }
  updateNodeById(ensureNodesRoot(), parentId, (parent) => {
    if (!parent.children) {
      parent.children = [];
    }
    parent.children.push(newNode);
  });
}

function updateNode(
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
): void {
  updateNodeById(formState.value.nodes, nodeId, updater);
}

function moveNode(nodeId: string, direction: "up" | "down") {
  moveNodeById(formState.value.nodes, nodeId, direction);
}

function calculateNodeLevelFromDataPath(dataPath: string | undefined): number {
  if (!dataPath) return 2;
  const segments = parseDataPath(dataPath);
  // level = 2 + depth of dataPath (starting from level 2 as subheading)
  // e.g., "section" -> level 3, "section.subsection" -> level 4
  return Math.min(2 + segments.length, 5);
}

function formatCustomTableFieldValue(value: any): string {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) {
    return value
      .map((item) =>
        typeof item === "object" ? JSON.stringify(item) : String(item ?? ""),
      )
      .filter((text) => text.length > 0)
      .join(", ");
  }
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch (error) {
      console.warn("Failed to stringify value", error);
      return String(value);
    }
  }
  return String(value);
}

function getCustomTableCellContentValue(
  node: WordDocumentNode,
  sectionData: Record<string, any> | null,
  content: WordCustomTableCellContent,
): string {
  if (!content) return "";
  if (content.type === "text") {
    return content.text ?? "";
  }
  if (!sectionData || !content.dataPath) return "";
  const scopedPath = resolveNodeScopedPath(node, content.dataPath);
  if (!scopedPath) return "";
  const value = getValueByPath(sectionData, scopedPath);
  return formatCustomTableFieldValue(value);
}

function getCustomTableCellDisplayValue(
  node: WordDocumentNode,
  cell: WordCustomTableCell | undefined,
  sectionData: Record<string, any> | null,
): string {
  if (!cell) return "";

  // Read contents without mutating - use existing contents or fallback to legacy fields
  let contents: WordCustomTableCellContent[];
  if (Array.isArray(cell.contents) && cell.contents.length > 0) {
    contents = cell.contents;
  } else {
    contents = [
      {
        id: "",
        type: cell.type ?? "text",
        text: cell.text,
        dataPath: cell.dataPath,
      } as WordCustomTableCellContent,
    ];
  }

  return contents
    .map((content) =>
      getCustomTableCellContentValue(node, sectionData, content),
    )
    .join("");
}

/**
 * 處理遞歸節點編輯器的事件
 */
function handleRecursiveNodeUpdate(
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
) {
  try {
    updateNodeById(formState.value.nodes, nodeId, updater);
  } catch (error) {
    console.error("Error updating node:", error);
    throw error;
  }
}

function handleRecursiveNodeRemove(nodeId: string) {
  removeNodeById(formState.value.nodes, nodeId);
}

function handleRecursiveNodeAddChild(nodeId: string) {
  addChildNodeById(formState.value.nodes, nodeId, (parent) => ({
    id: generateNodeId(),
    type: "paragraph",
    sectionId: parent.sectionId,
    level: (parent.level || 1) + 1,
  }));
}

function sanitizeForClone(
  data: WordExportTemplateConfig,
): WordExportTemplateConfig {
  // 创建一个清洁的副本，只包含可序列化的数据
  return {
    documentStyle: {
      headingFont: data.documentStyle?.headingFont,
      headingSizePt: data.documentStyle?.headingSizePt,
      headingBold: data.documentStyle?.headingBold,
      subHeadingFont: data.documentStyle?.subHeadingFont,
      subHeadingSizePt: data.documentStyle?.subHeadingSizePt,
      subHeadingBold: data.documentStyle?.subHeadingBold,
      bodyFont: data.documentStyle?.bodyFont,
      bodySizePt: data.documentStyle?.bodySizePt,
      bodyBold: data.documentStyle?.bodyBold,
    },
    sectionLayouts: data.sectionLayouts
      ? JSON.parse(JSON.stringify(data.sectionLayouts))
      : [],
    nodes: data.nodes ? JSON.parse(JSON.stringify(data.nodes)) : [],
  };
}

function handleSave() {
  try {
    let invalidNodes = false;
    walkWordNodes(formState.value.nodes, (node) => {
      if (!node) {
        console.warn("Found null/undefined node in node tree");
        return false;
      }
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

    // 使用 sanitize 函数確保數據可被序列化
    const cleanData = sanitizeForClone(formState.value);
    if (!cleanData || !cleanData.documentStyle) {
      throw new Error("保存數據不完整");
    }

    emit("save", cleanData);
  } catch (error) {
    console.error("Error in handleSave:", error);
    notifyError(
      error instanceof Error ? error.message : "保存失敗，請稍後重試",
    );
  }
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-TW");
}

/**
 * Render a node with dummy data for preview
 */
function renderNodePreview(
  node: WordDocumentNode,
  sectionDataMap: Record<string, Record<string, any>>,
  headingCounters: HeadingCounterState,
): string {
  const indent = 0;

  let html = `<div style="margin-left: ${indent}px; margin-bottom: 12px;">`;

  if (node.type === "sectionTitle") {
    resetHeadingCounters(headingCounters);
    const fontSize = (formState.value.documentStyle.headingSizePt || 18) / 2;
    html += `<h2 style="font-size: ${fontSize}pt; font-weight: bold; margin: 12px 0;">
      ${node.label || "章節標題"}
    </h2>`;
  } else if (node.type === "subHeading") {
    const fontSize = (formState.value.documentStyle.subHeadingSizePt || 14) / 2;
    const showNumbering = node.list?.numbering !== false; // 預設 true
    const prefix = showNumbering
      ? formatHeadingPrefix(node.level, headingCounters, node.list?.style)
      : "";

    html += `<h3 style="font-size: ${fontSize}pt; font-weight: bold; margin: 8px 0;">
      ${prefix}${node.label || "次標題"}
    </h3>`;
  } else if (node.type === "paragraph") {
    const docStyle = formState.value.documentStyle;
    const sectionData = node.sectionId
      ? (sectionDataMap[node.sectionId] ?? null)
      : null;
    const value = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : `${node.label || "段落內容"} (無資料)`;
    const formattedValue =
      value === undefined || value === null ? "" : String(value);
    const numberingEnabled = node.paragraphNumbering === true;
    const numberingStyle = node.paragraphNumberStyle || "arabicNumber";
    const useSubHeadingTypography = shouldUseParagraphSubHeadingStyle(node);
    const baseFontSizePt = useSubHeadingTypography
      ? docStyle.subHeadingSizePt || 14
      : docStyle.bodySizePt || 12;
    const fontSize = baseFontSizePt / 2;
    const weightValue = useSubHeadingTypography
      ? docStyle.subHeadingBold !== false
      : (node.style?.bodyBold ?? docStyle.bodyBold ?? false);
    const fontWeight = weightValue ? "bold" : "normal";
    const fontFamily = useSubHeadingTypography
      ? docStyle.subHeadingFont || "Times New Roman"
      : docStyle.bodyFont || "Times New Roman";
    const fontFamilyCss = fontFamily.includes(" ")
      ? `'${fontFamily}'`
      : fontFamily;
    const prefix = numberingEnabled
      ? formatHeadingPrefix(node.level ?? 3, headingCounters, numberingStyle)
      : "";
    const labelText = node.label ? `${node.label}: ` : "";
    html += `<p style="font-size: ${fontSize}pt; margin: 6px 0; font-weight: ${fontWeight}; font-family: ${fontFamilyCss};">
      ${prefix}${labelText}${formattedValue}
    </p>`;
  } else if (node.type === "table") {
    const sectionData = node.sectionId ? sectionDataMap[node.sectionId] : null;
    const tableData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const rows = Array.isArray(tableData) ? tableData : [];
    const columns = node.table?.columns || [];
    const transpose = node.table?.transpose === true;

    html += `<table style="width: 100%; border-collapse: collapse; margin: 8px 0;">`;

    if (!transpose) {
      html += `<thead>
        <tr style="background-color: #f0f0f0;">`;
      for (const col of columns) {
        html += `<th style="border: 1px solid #ccc; padding: 6px;">${col.label}</th>`;
      }
      html += `</tr></thead>`;
    }

    html += `<tbody>`;
    if (transpose) {
      for (const col of columns) {
        html += `<tr><td style="border: 1px solid #ccc; padding: 6px; font-weight: bold;">${col.label}</td>`;
        for (const row of rows) {
          const cellValue =
            typeof row === "object" ? getValueByPath(row, col.key) : row;
          html += `<td style="border: 1px solid #ccc; padding: 6px;">${cellValue}</td>`;
        }
        html += `</tr>`;
      }
    } else {
      for (const row of rows) {
        html += `<tr>`;
        for (const col of columns) {
          const cellValue =
            typeof row === "object" ? getValueByPath(row, col.key) : row;
          html += `<td style="border: 1px solid #ccc; padding: 6px;">${cellValue}</td>`;
        }
        html += `</tr>`;
      }
    }
    html += `</tbody></table>`;
  } else if (node.type === "customTable") {
    const customTable = node.customTable;
    const rows = Math.max(0, customTable?.rows ?? 0);
    const cols = Math.max(0, customTable?.cols ?? 0);
    const bodyFontSize = (formState.value.documentStyle.bodySizePt || 12) / 2;
    const sectionData: Record<string, any> | null = node.sectionId
      ? (sectionDataMap[node.sectionId] ?? null)
      : null;

    if (!rows || !cols || !customTable?.cells?.length) {
      html += `<p style="font-size: ${bodyFontSize}pt; color: #94a3b8; margin: 6px 0;">自訂表格尚未設定內容</p>`;
    } else {
      const cellMap = new Map<string, WordCustomTableCell>();
      for (const cell of customTable.cells) {
        if (!cell) continue;
        cellMap.set(`${cell.row}-${cell.col}`, cell);
      }

      const renderCellValue = (cell?: WordCustomTableCell | null): string =>
        getCustomTableCellDisplayValue(node, cell || undefined, sectionData);

      html += `<table style="width: 100%; border-collapse: collapse; margin: 8px 0;">`;
      for (let rowIndex = 0; rowIndex < rows; rowIndex++) {
        html += "<tr>";
        for (let colIndex = 0; colIndex < cols; colIndex++) {
          const cellKey = `${rowIndex}-${colIndex}`;
          const cell = cellMap.get(cellKey);
          const displayValue = renderCellValue(cell);
          html += `<td style="border: 1px solid #cbd5f5; padding: 6px; font-size: ${bodyFontSize}pt; vertical-align: top;">${
            displayValue || "&nbsp;"
          }</td>`;
        }
        html += "</tr>";
      }
      html += `</table>`;
    }
  } else if (node.type === "list") {
    const sectionData = node.sectionId ? sectionDataMap[node.sectionId] : null;
    const listData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const items = Array.isArray(listData) ? listData : [listData];

    const isNumbered = node.list?.numbering !== false;
    const listTag = isNumbered ? "ol" : "ul";
    const getBulletText = (index: number) =>
      isNumbered ? getListBulletLabel(node.list?.style, index) : "";

    html += `<${listTag} style="margin: 6px 0; padding-left: 0; list-style: none;">`;

    // 清單內為對象且使用子節點時：依「每個 list item」逐項渲染，每項用 itemDataMap 渲染所有 children（含段落與內層清單），避免把多項用逗號合併或把內層清單壓平
    if (
      node.list?.itemConfig?.useSubNodes &&
      items.length > 0 &&
      typeof items[0] === "object" &&
      items[0] !== null &&
      !Array.isArray(items[0]) &&
      node.children?.length
    ) {
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const itemDataMap: Record<string, Record<string, any>> = {};
        const currentSectionId = node.sectionId;
        if (currentSectionId && typeof item === "object" && item !== null) {
          itemDataMap[currentSectionId] = item as Record<string, any>;
        }
        const mergedSectionDataMap: Record<string, Record<string, any>> = {
          ...sectionDataMap,
          ...itemDataMap,
        };

        const firstChild = node.children[0];
        let firstChildDisplayHtml = "";

        if (firstChild) {
          let adjustedFirstChild = { ...firstChild };
          if (node.dataPath && firstChild.dataPath) {
            const parentPathPrefix = node.dataPath + ".";
            if (firstChild.dataPath.startsWith(parentPathPrefix)) {
              adjustedFirstChild = {
                ...firstChild,
                dataPath: firstChild.dataPath.substring(
                  parentPathPrefix.length,
                ),
              };
            } else if (firstChild.dataPath.includes(parentPathPrefix)) {
              // 子節點可能是從 section 起的完整路徑（如 執行步驟及方法.細分方法.細分名稱），當前 item 已是 list 項，取「細分方法.」之後的相對路徑
              const after =
                firstChild.dataPath.indexOf(parentPathPrefix) +
                parentPathPrefix.length;
              adjustedFirstChild = {
                ...firstChild,
                dataPath: firstChild.dataPath.substring(after),
              };
            }
          }

          if (adjustedFirstChild.type === "paragraph") {
            const childSectionData = adjustedFirstChild.sectionId
              ? mergedSectionDataMap[adjustedFirstChild.sectionId]
              : null;
            const value = childSectionData
              ? getValueByPath(childSectionData, adjustedFirstChild.dataPath)
              : adjustedFirstChild.label || "段落內容";
            const textContent = value == null ? "" : String(value);
            const childBold =
              adjustedFirstChild.style?.bodyBold ??
              formState.value.documentStyle.bodyBold ??
              false;
            const fontWeight = childBold ? "bold" : "normal";
            firstChildDisplayHtml = `<span style="font-weight: ${fontWeight};">${textContent}</span>`;
          }
        }

        const bullet = getBulletText(i);
        const displayFirstChild = firstChildDisplayHtml || "";
        html += `<li style="margin: 4px 0;">${bullet} ${displayFirstChild}`;

        if (node.children.length > 1) {
          html += `<ul style="margin: 6px 0; padding-left: 1.25em; list-style: none;">`;
          for (
            let childIndex = 1;
            childIndex < node.children.length;
            childIndex++
          ) {
            const childNode = node.children[childIndex];
            if (!childNode) continue;
            let adjustedChildNode = { ...childNode };
            if (node.dataPath && childNode.dataPath) {
              const parentPathPrefix = node.dataPath + ".";
              if (childNode.dataPath.startsWith(parentPathPrefix)) {
                adjustedChildNode = {
                  ...childNode,
                  dataPath: childNode.dataPath.substring(
                    parentPathPrefix.length,
                  ),
                };
              } else if (childNode.dataPath.includes(parentPathPrefix)) {
                // 子節點為完整路徑（如 執行步驟及方法.細分方法.說明）時，取 list 項相對路徑
                const after =
                  childNode.dataPath.indexOf(parentPathPrefix) +
                  parentPathPrefix.length;
                adjustedChildNode = {
                  ...childNode,
                  dataPath: childNode.dataPath.substring(after),
                };
              }
            }

            if (adjustedChildNode.type === "paragraph") {
              const childSectionData = adjustedChildNode.sectionId
                ? mergedSectionDataMap[adjustedChildNode.sectionId]
                : null;
              const value = childSectionData
                ? getValueByPath(childSectionData, adjustedChildNode.dataPath)
                : adjustedChildNode.label || "段落內容";
              const nestedDisplay =
                value === undefined || value === null ? "" : String(value);
              const childBold =
                adjustedChildNode.style?.bodyBold ??
                formState.value.documentStyle.bodyBold ??
                false;
              const fontWeight = childBold ? "bold" : "normal";
              html += `<li style="margin: 0px 0;"><span style="font-weight: ${fontWeight};">${nestedDisplay}</span></li>`;
            } else {
              const childHtml = renderNodePreview(
                adjustedChildNode,
                mergedSectionDataMap,
                headingCounters,
              );
              const innerContent = childHtml.replace(
                /^<div[^>]*>|<\/div>$/g,
                "",
              );
              html += `<li>${innerContent}</li>`;
            }
          }
          html += `</ul>`;
        }

        html += `</li>`;
      }
    } else {
      items.forEach((item, index) => {
        const displayValue =
          typeof item === "object" && item !== null
            ? JSON.stringify(item)
            : String(item ?? "");
        const bullet = getBulletText(index);
        html += `<li style="margin: 4px 0;">${bullet} ${displayValue}</li>`;
      });
    }

    html += `</${listTag}>`;
  } else if (node.type === "customText") {
    const boldSetting =
      node.style?.bodyBold ?? formState.value.documentStyle.bodyBold ?? false;
    const fontWeight = boldSetting ? "bold" : "normal";
    html += `<div style="margin: 6px 0; font-weight: ${fontWeight};">
      ${node.template || "自訂文字"}
    </div>`;
  }

  // 遞歸渲染子節點（適用於所有節點類型，但清單類型的子節點已經在清單項處理中處理過了）
  if (node.children?.length && node.type !== "list") {
    for (const childNode of node.children) {
      html += renderNodePreview(childNode, sectionDataMap, headingCounters);
    }
  }

  html += `</div>`;

  return html;
}

/**
 * Get value from object by dot-notation path
 */
function getValueByPath(obj: Record<string, any>, path?: string): any {
  if (!path || obj == null) return obj;
  const parts = path.split(".").filter((segment) => segment.length > 0);

  const traverse = (current: any, remaining: string[]): any => {
    if (!remaining.length) {
      return current;
    }

    if (Array.isArray(current)) {
      const aggregated: any[] = [];
      current.forEach((item) => {
        const value = traverse(item, remaining);
        if (Array.isArray(value)) {
          aggregated.push(...value);
        } else if (value !== undefined && value !== null) {
          aggregated.push(value);
        }
      });
      return aggregated.length ? aggregated : null;
    }

    if (!current || typeof current !== "object") {
      return null;
    }

    const [segment, ...rest] = remaining;
    if (segment === undefined || !(segment in current)) {
      return null;
    }
    return traverse(current[segment], rest);
  };

  return traverse(obj, parts);
}

/**
 * Generate HTML preview of the document
 */
function generatePreviewHtml(): string {
  const sectionDataMap = buildPreviewSectionDataMap(
    props.sections,
    formState.value.nodes,
  );

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
          font-size: ${(formState.value.documentStyle.bodySizePt || 12) / 2}pt;
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
          font-size: ${(formState.value.documentStyle.headingSizePt || 18) / 2}pt;
          font-weight: ${formState.value.documentStyle.headingBold ? "bold" : "normal"};
          margin-top: 20px;
          margin-bottom: 12px;
        }
        h3 {
          font-family: ${formState.value.documentStyle.subHeadingFont || "Times New Roman"};
          font-size: ${(formState.value.documentStyle.subHeadingSizePt || 14) / 2}pt;
          font-weight: ${formState.value.documentStyle.subHeadingBold ? "bold" : "normal"};
          margin-top: 14px;
          margin-bottom: 8px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin: 12px 0;
          font-size: ${(formState.value.documentStyle.bodySizePt || 12) / 2}pt;
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
        ul, ol {
          margin: 8px 0;
          padding-left: 0;
          list-style-position: inside;
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

const {
  debouncedPreviewHtml,
  previewIframeRef,
  previewContainerRef,
  handleIframeLoad,
  handlePreviewExport,
} = useWordPreview({
  source: () => [formState.value.documentStyle, formState.value.nodes],
  generatePreviewHtml,
  notifyError,
});

/**
 * Generate docx document from current form state
 */
async function generateDocxDocument(): Promise<Blob> {
  const sectionDataMap = buildPreviewSectionDataMap(
    props.sections,
    formState.value.nodes,
  );

  const planContent = Object.fromEntries(
    props.sections.map((section) => [
      section.id,
      { content: sectionDataMap[section.id] ?? {} },
    ]),
  );

  return await exportPlanUsingWordConfig(
    formState.value,
    props.sections,
    planContent,
    props.template?.name || "文檔",
    { autoDownload: false },
  );
}

const { handleDownloadWord } = useWordDownload({
  generateDocxDocument,
  getFileName: () => `${props.template?.name || "文檔"}_預覽.docx`,
  notifyError,
});
</script>
