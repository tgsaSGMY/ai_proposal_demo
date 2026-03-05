<template>
  <div class="space-y-3 rounded-xl bg-slate-50 p-3">
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

    <div
      v-if="node.type === 'list' && node.list?.itemConfig?.useSubNodes"
      class="border-t border-slate-200 pt-3"
    >
      <button
        type="button"
        class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50"
        @click="emit('add-child', node.id)"
      >
        + 添加子節點
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WordDocumentNode, WordListStyle } from "~/types/wordExport";

const props = defineProps<{
  node: WordDocumentNode;
  listStyleOptions: Array<{ label: string; value: string }>;
}>();

const emit = defineEmits<{
  (
    e: "update",
    nodeId: string,
    updater: (node: WordDocumentNode) => void,
  ): void;
  (e: "add-child", nodeId: string): void;
}>();

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

function handleListNumberingChange(event: Event) {
  const target = event.target as HTMLInputElement;
  emit("update", props.node.id, (node) => {
    if (!node.list) {
      node.list = {
        numbering: true,
        style: node.level ? getListStyleForLevel(node.level) : "chineseNumber",
      };
    }
    node.list.numbering = target.checked;
  });
}

function handleListStyleChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit("update", props.node.id, (node) => {
    if (!node.list) {
      node.list = {
        numbering: true,
        style: node.level ? getListStyleForLevel(node.level) : "chineseNumber",
      };
    }
    node.list.style = target.value as WordListStyle;
  });
}

function handleUseSubNodesChange(event: Event) {
  const target = event.target as HTMLInputElement;
  emit("update", props.node.id, (node) => {
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
</script>
