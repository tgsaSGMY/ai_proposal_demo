<!-- 用途：處理節點的資料來源章節與多層 dataPath 綁定。 -->
<template>
  <div class="grid gap-4 md:grid-cols-2">
    <label class="space-y-1 text-sm text-slate-600">
      資料章節
      <select
        :value="node.sectionId"
        class="w-full rounded-xl border px-3 py-2 text-sm"
        :class="isSectionOutdated ? 'border-red-300 text-red-600 bg-red-50 focus:border-red-500 focus:ring-red-200' : 'border-slate-200'"
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
        <option v-if="isSectionOutdated" :value="node.sectionId" class="text-red-500">
          ⚠️ 已刪除的章節 ({{ node.sectionId }})
        </option>
      </select>
      
      <div v-if="isSectionOutdated" class="mt-2 p-2 bg-red-50 border border-red-200 rounded-lg text-red-600 text-xs flex items-start gap-1.5">
        <span class="text-sm leading-none mt-0.5">⚠️</span>
        <span class="leading-relaxed">
          <strong>Outdated Section (已刪除的章節)</strong><br />
          The section bound to this node no longer exists. Historical data can still be exported if available, but rebinding is recommended for new projects.
        </span>
      </div>
    </label>
    <label class="space-y-1 text-sm text-slate-600">
      綁定欄位
      <div class="space-y-2">
        <div
          v-for="(levelOptions, levelIndex) in getDataPathLevels(node)"
          :key="`level-${levelIndex}`"
          class="flex items-center min-w-0"
        >
          <select
            :value="parseDataPath(node.dataPath)[levelIndex] || ''"
            class="flex-1 min-w-0 rounded-xl border border-slate-200 px-3 py-2 text-sm"
            :class="isBindingBroken ? 'border-red-300 text-red-600 focus:border-red-500 focus:ring-red-200' : ''"
            @change="handleDataPathLevelChange(levelIndex, $event)"
          >
            <option value="">
              {{ levelIndex === 0 ? "未選擇" : "請選擇..." }}
            </option>
            <option
              v-for="option in levelOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
        
        <div v-if="isBindingBroken" class="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-xs flex flex-col gap-2">
          <div class="flex items-start gap-1.5 font-medium">
            <span class="text-sm leading-none mt-0.5">⚠️</span>
            <span class="break-all">此欄位路徑在當前章節 Schema 中已失效或結構不符：<code class="font-mono bg-red-100 px-1 rounded">{{ node.dataPath }}</code></span>
          </div>
          
          <div class="ml-5 space-y-1.5 text-slate-700">
            <p class="font-bold text-red-700">💡 排解建議 (Troubleshooting):</p>
            <ul class="list-disc pl-4 space-y-1">
              <li>
                <strong>欄位名稱包含點 (<code>.</code>)：</strong> 若您的 Schema 欄位名稱包含點 (例如 <code>1.經濟效益</code>)，系統會誤判為巢狀路徑。請至「章節編輯器」將點改為底線 (例如 <code>1_經濟效益</code>)。
              </li>
              <li>
                <strong>巢狀陣列問題：</strong> 若您試圖綁定包含多個項目的「陣列」(Array)，請改用 Word 編輯器的 <strong>「清單 (List)」</strong> 或 <strong>「自訂表格 (Custom Table)」</strong> 節點來綁定。
              </li>
              <li>
                <strong>Schema 已更新：</strong> 若章節的結構被修改過，請點擊下方按鈕清除路徑並重新綁定。
              </li>
            </ul>
          </div>

          <div class="flex justify-end mt-1">
            <button 
              type="button" 
              class="px-3 py-1.5 bg-red-100 hover:bg-red-200 border border-red-300 text-red-700 rounded shadow-sm font-semibold transition-colors"
              @click="clearInvalidPath"
            >
              清除無效路徑
            </button>
          </div>
        </div>
      </div>
    </label>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
  buildDataPath,
  createWordSchemaPathHelpers,
  parseDataPath,
} from "~/composables/template-manager/useWordSchemaPath";
import type { WordDocumentNode } from "~/types/wordExport";

// Schema 欄位結構（僅供路徑候選分析）。
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

// 接收節點、章節選單與章節 schema。
const props = defineProps<{
  node: WordDocumentNode;
  sectionOptions: Array<{ label: string; value: string }>;
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

// 產生 dataPath 各層候選欄位。
const { getDataPathLevels, isValidDataPath } = createWordSchemaPathHelpers(() => props.sections);

// 判斷章節是否已被刪除 (Outdated)
const isSectionOutdated = computed(() => {
  if (!props.node.sectionId) return false;
  return !props.sections.some(s => s.id === props.node.sectionId);
});

// 判斷綁定路徑是否失效
const isBindingBroken = computed(() => {
  if (!props.node.sectionId) return false; // 沒綁定章節就不算失效
  if (isSectionOutdated.value) return false; // 如果章節已刪除，我們另外顯示章節失效警告，不顯示路徑失效
  if (!props.node.dataPath) return false; // 綁定整個章節也不算失效
  return !isValidDataPath(props.node.sectionId, props.node.dataPath);
});

// 切換資料章節時，重置 dataPath 以避免舊路徑殘留。
function handleSectionChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit("update", props.node.id, (node) => {
    node.sectionId = target.value;
    node.dataPath = "";
  });
}

// 更新指定層級的 dataPath，並截斷後續無效層級。
function handleDataPathLevelChange(levelIndex: number, event: Event) {
  const target = event.target as HTMLSelectElement;
  emit("update", props.node.id, (node) => {
    const segments = parseDataPath(node.dataPath);

    if (target.value === "") {
      segments.splice(levelIndex);
    } else {
      segments[levelIndex] = target.value;
      segments.splice(levelIndex + 1);
    }

    node.dataPath = buildDataPath(segments);
  });
}

// 清除失效的路徑，讓 UI 恢復到只有第一層下拉選單的乾淨狀態
function clearInvalidPath() {
  emit("update", props.node.id, (node) => {
    node.dataPath = ""; 
  });
}
</script>
