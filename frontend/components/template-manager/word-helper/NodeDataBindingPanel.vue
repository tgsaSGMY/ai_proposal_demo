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
  sectionOptions: Array<{ label: string; value: string }>;
  sections: SectionRecord[];
}>();

const emit = defineEmits<{
  (
    e: "update",
    nodeId: string,
    updater: (node: WordDocumentNode) => void,
  ): void;
}>();

const { getDataPathLevels } = createWordSchemaPathHelpers(() => props.sections);

function handleSectionChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit("update", props.node.id, (node) => {
    node.sectionId = target.value;
    node.dataPath = "";
  });
}

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
