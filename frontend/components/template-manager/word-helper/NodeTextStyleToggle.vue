<template>
  <label class="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
    <input
      type="checkbox"
      class="h-4 w-4 rounded border-slate-300"
      :checked="node.style?.bodyBold === true"
      @change="handleBoldToggle"
    />
    使用粗體
  </label>
</template>

<script setup lang="ts">
import type { WordDocumentNode } from "~/types/wordExport";

const props = defineProps<{
  node: WordDocumentNode;
}>();

const emit = defineEmits<{
  (
    e: "update",
    nodeId: string,
    updater: (node: WordDocumentNode) => void,
  ): void;
}>();

function handleBoldToggle(event: Event) {
  const target = event.target as HTMLInputElement;
  emit("update", props.node.id, (node) => {
    if (!node.style) {
      node.style = {};
    }
    node.style.bodyBold = target.checked;
  });
}
</script>
