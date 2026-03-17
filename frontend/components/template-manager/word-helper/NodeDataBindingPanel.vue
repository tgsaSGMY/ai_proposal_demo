<!-- 用途：處理節點的資料來源章節與多層 dataPath 綁定。 -->
<template>
  <div class="grid gap-4 md:grid-cols-2">
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
        <div
          v-for="(levelOptions, levelIndex) in getDataPathLevels(node)"
          :key="`level-${levelIndex}`"
          class="flex items-center"
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
        </div>
      </div>
    </label>
  </div>
</template>

<script setup lang="ts">
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
const { getDataPathLevels } = createWordSchemaPathHelpers(() => props.sections);

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
</script>
