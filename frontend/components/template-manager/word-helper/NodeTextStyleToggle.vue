<!-- 用途：提供節點文字粗體開關，更新 node.style.bodyBold。 -->
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

// 接收目前節點。
const props = defineProps<{
  node: WordDocumentNode;
}>();

// 對外派發節點更新事件。
const emit = defineEmits<{
  (
    e: "update",
    nodeId: string,
    updater: (node: WordDocumentNode) => void,
  ): void;
}>();

// 切換粗體設定，必要時補上 style 物件。
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
