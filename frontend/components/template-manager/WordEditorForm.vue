<!-- 調整文檔的模組，包含設定字體、建立章節分組與調整節點順序的功能。 -->
<template>
  <div
    v-if="isVisible && template"
    class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 py-6"
  >
    <section
      class="w-full max-w-8xl max-h-full overflow-y-auto overflow-x-hidden rounded-2xl bg-white p-6 space-y-6 shadow-2xl"
    >
      <header class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p
            class="text-xs font-semibold text-rose-400 uppercase tracking-[0.3em]"
          >
            Word Export Editor
          </p>
          <h2 class="text-2xl font-bold text-slate-900 truncate" :title="`${template.name} · ${template.id}`">
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
        <div class="space-y-6 overflow-y-auto max-h-[calc(100vh-12rem)] min-w-0">
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
                    <p class="font-semibold text-slate-800 flex items-center gap-2">
                      {{ formatDate(version.createdAt) }}
                      <span v-if="isVersionOutdated(version)" class="inline-flex items-center rounded-full bg-yellow-50 px-2 py-0.5 text-[10px] font-medium text-yellow-800 ring-1 ring-inset ring-yellow-600/20" title="此版本的章節結構與當前資料庫不同">
                        ⚠️ 結構已變更
                      </span>
                    </p>
                    <p class="text-xs text-slate-500 truncate">
                      {{ version.createdBy || "未記錄" }}
                    </p>
                  </div>
                  <div class="flex items-center gap-3">
                    <button
                      type="button"
                      class="text-xs font-semibold text-rose-600 hover:text-rose-700"
                      @click="applyVersion(version)"
                    >
                      套用
                    </button>
                    <button
                      v-if="versionHistory.length > 1 && version.id !== versionHistory[0].id"
                      type="button"
                      class="text-xs font-semibold text-red-500 hover:text-red-700"
                      title="刪除此版本"
                      @click="handleDeleteVersion(version.id)"
                    >
                      ✕
                    </button>
                  </div>
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
                  新增節點
                </button>
                <button
                  type="button"
                  class="rounded-lg border border-blue-300 px-3 py-1 text-sm font-semibold text-blue-600 hover:bg-blue-50 ml-2"
                  @click="syncMissingSections()"
                >
                  🔄 同步遺失的章節
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
                  class="shrink-0 rounded-xl px-3 py-1 font-semibold max-w-[10rem] truncate"
                  :class="[
                    selectedChapterId === chapter.id
                      ? 'bg-rose-500 text-white'
                      : 'text-slate-600 hover:text-rose-500',
                  ]"
                  :title="chapter.title || '未命名章節'"
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
                    <span class="text-sm font-semibold text-slate-700 truncate min-w-0" :title="chapter.title || '未命名章節'">{{
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
          class="rounded-2xl border border-slate-200 bg-slate-50 p-4 flex flex-col lg:sticky lg:top-6 max-h-[calc(100vh-12rem)] min-w-0"
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
import RecursiveNodeEditor from "./word-helper/RecursiveNodeEditor.vue";
import type {
  WordDocumentNode,
  WordDocumentNodeType,
  WordExportConfigEntry,
  WordExportTemplateConfig,
  WordTableColumn,
  WordCustomTableCell,
  WordCustomTableCellContent,
} from "~/types/wordExport";

// 模板基本資訊，包含歷史版本設定。
interface TemplateRecord {
  id: string;
  name: string;
  word_export_config?: WordExportConfigEntry[] | null;
}

// Schema 欄位結構（遞迴定義），供節點自動產生使用。
interface SchemaField {
  title?: string;
  type?: string;
  properties?: Record<string, SchemaField>;
  items?: {
    properties?: Record<string, SchemaField>;
  };
}

// 章節資料與其 JSON Schema 定義。
interface SectionRecord {
  id: string;
  name: string;
  json_schema?: {
    properties?: Record<string, SchemaField>;
  } | null;
}

// Word 文件的預設字體樣式。
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

// 接收彈窗顯示、模板資訊、章節資料與儲存中狀態。
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

// 對外事件：關閉編輯器、儲存新版本。
const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", payload: WordExportTemplateConfig): void;
  (e: "delete-version", versionId: string): void;
}>();

// 處理通知與錯誤提示
const { error: notifyError, success } = useNotifications();

// 可選字體清單。
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

// 可新增節點型別選項。
const NODE_TYPE_OPTIONS: Array<{ label: string; value: WordDocumentNodeType }> =
  [
    { label: "次標題", value: "subHeading" },
    { label: "段落文字", value: "paragraph" },
    { label: "表格", value: "table" },
    { label: "自訂表格", value: "customTable" },
    { label: "清單", value: "list" },
    { label: "自訂文字", value: "customText" },
  ];

// 清單編號樣式選項。
const LIST_STYLE_OPTIONS = [
  { label: "一、 二、 三、", value: "chineseNumber" },
  { label: "1. 2. 3.", value: "arabicNumber" },
  { label: "（1）、（2）、（3）", value: "parenNumbered" },
  { label: "• ◦ ▪", value: "bullet" },
];

// 取得自訂表格節點初始化輔助函式。
const { ensureCustomTableConfig } =
  createCustomTableNodeHelpers(generateNodeId);

// 編輯器主狀態（文件樣式、章節布局、節點樹）。
const formState = ref<WordExportTemplateConfig>({
  documentStyle: { ...DEFAULT_STYLE },
  sectionLayouts: [],
  nodes: [],
});

// 版本歷史依建立時間新到舊排序。
const versionHistory = computed<WordExportConfigEntry[]>(() => {
  const list = props.template?.word_export_config ?? [];
  return [...list].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );
});

// 判斷某個歷史版本是否已「過期」(章節結構與當前資料庫不符)
function isVersionOutdated(version: WordExportConfigEntry): boolean {
  if (!version.config?.nodes) return false;

  const dbSectionIds = new Set(props.sections.map((s) => s.id));
  const versionSectionIds = new Set<string>();

  const scanNodes = (nodes: WordDocumentNode[]) => {
    for (const node of nodes) {
      if (node.sectionId) versionSectionIds.add(node.sectionId);
      if (node.children && node.children.length > 0) scanNodes(node.children);
    }
  };
  scanNodes(version.config.nodes);

  // 1. 檢查是否有已刪除的章節 (Ghost nodes)
  for (const id of versionSectionIds) {
    if (!dbSectionIds.has(id)) return true;
  }

  // 2. 檢查是否有遺漏的新章節 (Missing nodes)
  for (const id of dbSectionIds) {
    if (!versionSectionIds.has(id)) return true;
  }

  return false;
}

// 章節分組模型：一個章節標記加上其內容節點。
interface ChapterGroup {
  id: string;
  title: string;
  nodes: WordDocumentNode[];
  contentNodes: WordDocumentNode[];
  isManual?: boolean; // 是否為手動添加的章節標記
}

// 將平面節點依章節標記切分為多個章節群組。
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

// 目前選取的章節 tab。
const selectedChapterId = ref<string>("");

// 依選取章節過濾，只顯示單一章節內容。
const filteredChapters = computed(() => {
  return groupedNodes.value.filter(
    (group) => group.id === selectedChapterId.value,
  );
});

// 取得節點在根節點陣列中的索引。
function getNodeGlobalIndex(nodeId: string): number {
  if (!formState.value.nodes) return -1;
  return formState.value.nodes.findIndex((n) => n.id === nodeId);
}

// 取得章節在分組清單中的索引。
function getChapterGlobalIndex(chapterId: string): number {
  return groupedNodes.value.findIndex((group) => group.id === chapterId);
}

// 移動整個章節（含章節內所有節點）的位置。
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

  // 找到章節在所有節點中的範圍。
  const currentStartIndex = allNodes.findIndex(
    (n) => n.id === currentChapter.nodes[0]?.id,
  );
  const currentEndIndex = currentStartIndex + currentChapter.nodes.length - 1;

  const targetStartIndex = allNodes.findIndex(
    (n) => n.id === targetChapter.nodes[0]?.id,
  );
  const targetEndIndex = targetStartIndex + targetChapter.nodes.length - 1;

  if (currentStartIndex === -1 || targetStartIndex === -1) return;

  // 提取目前章節的整段節點。
  const currentChapterNodes = allNodes.splice(
    currentStartIndex,
    currentChapter.nodes.length,
  );

  // 計算新的插入位置。
  let insertIndex: number;
  if (direction === "up") {
    // 上移：插入到目標章節前面。
    insertIndex = allNodes.findIndex(
      (n) => n.id === targetChapter.nodes[0]?.id,
    );
  } else {
    // 下移：插入到目標章節後面。
    const newTargetEndIndex = allNodes.findIndex(
      (n) => n.id === targetChapter.nodes[targetChapter.nodes.length - 1]?.id,
    );
    insertIndex = newTargetEndIndex + 1;
  }

  allNodes.splice(insertIndex, 0, ...currentChapterNodes);
}

// 新增一個章節標記節點，作為章節分組起點。
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

// 在指定節點後方插入新節點。
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

// 在章節尾端新增節點。
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

// 編輯章節標題，並同步更新 label。
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

// 刪除整個章節（含章節內所有節點）。
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

// 轉換章節資料為下拉選單格式。
const sectionOptions = computed(() =>
  props.sections.map((section) => ({
    label: section.name,
    value: section.id,
  })),
);

// 彈窗開啟時載入最新版本設定。
watch(
  () => [props.isVisible, props.template, props.sections],
  ([visible]) => {
    if (visible) {
      hydrateForm(versionHistory.value[0]?.config);
    }
  },
  { immediate: true },
);

// 章節變動時維持 selectedChapterId 的有效性。
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

// 遞迴初始化節點預設值，確保 customTable 結構完整。
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

// 將版本資料灌入編輯表單，並在失敗時回退到預設配置。
function hydrateForm(base?: WordExportTemplateConfig) {
  try {
    const documentStyle = {
      ...DEFAULT_STYLE,
      ...(base?.documentStyle || {}),
    };

    // 使用 JSON 序列化確保資料可用，避免 Vue 響應式代理影響。
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
    // 回退至預設值，避免編輯器失效。
    formState.value = {
      documentStyle: { ...DEFAULT_STYLE },
      sectionLayouts: [],
      nodes: generateDefaultNodes(),
    };
  }
}

// 套用歷史版本配置。
function applyVersion(version: WordExportConfigEntry) {
  hydrateForm(version.config);
}

// 產生節點唯一 ID（優先使用 crypto.randomUUID）。
function generateNodeId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `node_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

// 刪除指定歷史版本
function handleDeleteVersion(versionId: string) {
  if (window.confirm("確定要刪除此歷史版本嗎？這將無法復原，且可能影響依賴此版本的舊計畫匯出格式。")) {
    emit("delete-version", versionId);
  }
}

/**
 * 依章節 schema 產生預設節點樹（含章節標題、次標題、段落、清單、表格）。
 */
function generateDefaultNodes(): WordDocumentNode[] {
  const nodes: WordDocumentNode[] = [];

  for (const section of props.sections) {
    // 新增章節標題節點（level 1）。
    nodes.push({
      id: generateNodeId(),
      label: section.name,
      type: "sectionTitle",
      sectionId: section.id,
      level: 1,
    });

    // 遞迴解析 schema properties，層級從 level 2 開始。
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

// 同步與重整 (Smart Sync & Reorder)
// 將現有節點分塊、依據資料庫章節順序重新排序、插入遺失的章節，並將已刪除的章節移至最下方
function syncMissingSections() {
  const currentNodes = formState.value.nodes || [];
  if (currentNodes.length === 0) {
    formState.value.nodes = generateDefaultNodes();
    success("已產生預設節點結構！");
    return;
  }

  // 1. 將現有節點切分成 Chapter Blocks
  const blocks: WordDocumentNode[][] = [];
  let currentBlock: WordDocumentNode[] = [];
  for (const node of currentNodes) {
    const isChapterMarker = node.type === "sectionTitle" || node.chapterMarker === true;
    if (isChapterMarker && currentBlock.length > 0) {
      blocks.push(currentBlock);
      currentBlock = [];
    }
    currentBlock.push(node);
  }
  if (currentBlock.length > 0) blocks.push(currentBlock);

  // 2. 分析每個 Block 的主要 sectionId
  const blockMap = new Map<string, WordDocumentNode[][]>();
  const unmappedBlocks: WordDocumentNode[][] = [];

  for (const block of blocks) {
    let primarySectionId: string | null = null;
    
    // 遞迴掃描找出第一個有效的 sectionId
    const scanForSectionId = (nodes: WordDocumentNode[]): string | null => {
      for (const node of nodes) {
        if (node.sectionId) return node.sectionId;
        if (node.children && node.children.length > 0) {
          const childId = scanForSectionId(node.children);
          if (childId) return childId;
        }
      }
      return null;
    };
    
    primarySectionId = scanForSectionId(block);

    if (primarySectionId) {
      if (!blockMap.has(primarySectionId)) blockMap.set(primarySectionId, []);
      blockMap.get(primarySectionId)!.push(block);
    } else {
      unmappedBlocks.push(block);
    }
  }

  // 3. 依據資料庫的章節順序，重新組裝節點樹
  const newFlatNodes: WordDocumentNode[] = [];
  let syncedCount = 0;

  for (const section of props.sections) {
    if (blockMap.has(section.id)) {
      // 保留並插入現有區塊
      const sectionBlocks = blockMap.get(section.id)!;
      for (const b of sectionBlocks) {
        newFlatNodes.push(...b);
      }
      blockMap.delete(section.id);
    } else {
      // 遺失的章節：動態產生並安插在正確位置
      const newNodes: WordDocumentNode[] = [];
      newNodes.push({
        id: generateNodeId(),
        label: section.name,
        type: "sectionTitle",
        sectionId: section.id,
        level: 1,
      });

      const schemaProps = section.json_schema?.properties;
      if (schemaProps) {
        const childNodes = generateNodesFromSchema(section.id, schemaProps, "", 2);
        newNodes.push(...childNodes);
      }
      newFlatNodes.push(...newNodes);
      syncedCount++;
    }
  }

  // 4. 將無綁定的純手動區塊加在活耀章節後方
  for (const b of unmappedBlocks) {
    newFlatNodes.push(...b);
  }

  // 5. 將已刪除(Orphan/Ghost)的章節區塊移至最下方
  for (const [secId, orphanBlocks] of blockMap.entries()) {
    for (const b of orphanBlocks) {
      newFlatNodes.push(...b);
    }
  }

  formState.value.nodes = newFlatNodes;
  success(`同步完成！已依照最新結構排序，並補齊 ${syncedCount} 個遺失章節。`);
}

/**
 * 由 schema properties 遞迴生成節點。
 * 每個屬性會先建立次標題，再依型別建立內容節點。
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

    // 為每個屬性新增次標題並帶入對應 level。
    nodes.push({
      id: generateNodeId(),
      label,
      type: "subHeading",
      sectionId,
      level,
      list: { numbering: false },
    });

    if (field.type === "array") {
      if (field.items?.properties) {
        // 陣列物件 -> 表格：自動展平巢狀欄位到葉節點。
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

            // 僅加入葉節點（非 object、非 array）。
            if (itemField?.type !== "object" && itemField?.type !== "array") {
              columns.push({
                key: fullKey,
                label: fullLabel,
              });
            }

            // 若欄位仍是物件則繼續展平。
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
        // 陣列字串/簡單值 -> 清單，樣式依設定顯示。
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
      // 物件 -> 遞迴處理巢狀屬性，level 遞增。
      const nestedNodes = generateNodesFromSchema(
        sectionId,
        field.properties,
        path,
        level + 1,
      );
      nodes.push(...nestedNodes);
    } else {
      // 其他簡單值 -> 段落節點。
      nodes.push({
        id: generateNodeId(),
        label: `${label} 内容`,
        type: "paragraph",
        sectionId,
        dataPath: path,
        level: level + 1,
        paragraphNumbering: false,
      });
    }
  }

  return nodes;
}

// 確保根節點陣列存在後回傳。
function ensureNodesRoot(): WordDocumentNode[] {
  if (!formState.value.nodes) {
    formState.value.nodes = [];
  }
  return formState.value.nodes;
}

// 建立新節點的預設工廠函式。
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

// 新增節點；若指定 parentId 則新增為子節點。
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

// 以 id 更新節點內容。
function updateNode(
  nodeId: string,
  updater: (node: WordDocumentNode) => void,
): void {
  updateNodeById(formState.value.nodes, nodeId, updater);
}

// 移動節點上下順序。
function moveNode(nodeId: string, direction: "up" | "down") {
  moveNodeById(formState.value.nodes, nodeId, direction);
}

// 依 dataPath 深度推算節點層級，並限制最大層級。
function calculateNodeLevelFromDataPath(dataPath: string | undefined): number {
  if (!dataPath) return 2;
  const segments = parseDataPath(dataPath);
  // level = 2 + depth of dataPath (starting from level 2 as subheading)
  // e.g., "section" -> level 3, "section.subsection" -> level 4
  return Math.min(2 + segments.length, 5);
}

// 將自訂表格欄位值格式化為可顯示文字。
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

// 依 cell content 設定取得自訂表格儲存格內容。
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

// 兼容新舊資料格式，組合自訂表格儲存格最終顯示字串。
function getCustomTableCellDisplayValue(
  node: WordDocumentNode,
  cell: WordCustomTableCell | undefined,
  sectionData: Record<string, any> | null,
): string {
  if (!cell) return "";

  // 讀取 contents 時不改動原資料，並兼容舊欄位格式。
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

// 遞迴節點編輯器：刪除指定節點。
function handleRecursiveNodeRemove(nodeId: string) {
  removeNodeById(formState.value.nodes, nodeId);
}

// 遞迴節點編輯器：在指定父節點下新增子節點。
function handleRecursiveNodeAddChild(nodeId: string) {
  addChildNodeById(formState.value.nodes, nodeId, (parent) => ({
    id: generateNodeId(),
    type: "paragraph",
    sectionId: parent.sectionId,
    level: (parent.level || 1) + 1,
  }));
}

// 深拷貝並清理資料，確保可序列化後再保存。
function sanitizeForClone(
  data: WordExportTemplateConfig,
): WordExportTemplateConfig {
  // 建立乾淨副本，只保留可序列化欄位。
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

// 保存前先驗證節點配置，再派發 save 事件。
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

    // 使用 sanitize 函式確保資料可被序列化。
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

// 格式化版本建立時間。
function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-TW");
}

/**
 * 以範例資料渲染單一節點為預覽 HTML。
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
    const showNumbering = node.list?.numbering === true; // 必須明確啟用才會編號

    // 即使未啟用編號，遇到新的次標題邊界時仍需重置更深層的計數器。
    // 否則同層級的下一組子節點會繼承上一組的編號（例如 [1,2] → [3,4] 而非 [1,2] → [1,2]）。
    const nodeLevel = node.level || 2;
    Object.keys(headingCounters).forEach((key) => {
      const keyNum = Number(key);
      if (keyNum > nodeLevel) {
        delete headingCounters[keyNum];
      }
    });

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

    // 當清單項為物件且啟用子節點時，逐項渲染避免資料被扁平化。
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
              // 子節點可能是從 section 起的完整路徑，需轉成 list item 相對路徑。
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
                // 子節點若是完整路徑，轉為 list item 相對路徑再渲染。
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

  // 遞迴渲染子節點（list 型別已在清單區塊中處理，不重複渲染）。
  if (node.children?.length && node.type !== "list") {
    for (const childNode of node.children) {
      html += renderNodePreview(childNode, sectionDataMap, headingCounters);
    }
  }

  html += `</div>`;

  return html;
}

/**
 * 依 dot path 從物件中取值，支援陣列聚合。
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
 * 生成整份文件的 HTML 預覽內容。
 */
function generatePreviewHtml(): string {
  const sectionDataMap = buildPreviewSectionDataMap(
    props.sections,
    formState.value.nodes,
  );

  const headingCounters = createHeadingCounterState();

  // 依節點順序組裝完整預覽 HTML。
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
  // 當樣式或節點變更時，自動重新生成預覽。
  source: () => [formState.value.documentStyle, formState.value.nodes],
  generatePreviewHtml,
  notifyError,
});

/**
 * 依目前配置生成 docx Blob（不自動下載）。
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

// 綁定下載流程：由 composable 接管錯誤提示與檔名。
const { handleDownloadWord } = useWordDownload({
  generateDocxDocument,
  getFileName: () => `${props.template?.name || "文檔"}_預覽.docx`,
  notifyError,
});
</script>
