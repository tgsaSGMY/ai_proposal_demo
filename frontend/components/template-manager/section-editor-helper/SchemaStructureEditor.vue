<!-- 用途：管理整體章節 Schema 結構，負責根欄位增刪與雙向同步編輯狀態。 -->
<template>
  <div class="space-y-4">
    <div class="grid gap-4">
      <label class="text-xs font-semibold text-slate-600">
        章節描述
        <input
          v-model="localDescription"
          :disabled="disabled"
          class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:border-rose-400 focus:ring-rose-200 disabled:bg-slate-50"
          placeholder="補充說明 (選填)"
        />
      </label>
    </div>

    <div class="flex items-center justify-between">
      <div>
        <h5 class="text-sm font-semibold text-slate-900">章節結構</h5>
        <p class="text-xs text-slate-500">以階層方式定義欄位、型別與必填規則</p>
      </div>
      <button
        type="button"
        class="rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
        :disabled="disabled"
        @click="addRootField"
      >
        + 新增欄位
      </button>
    </div>

    <p
      v-if="!tree.length"
      class="rounded-xl border border-dashed border-slate-200 px-4 py-6 text-center text-xs text-slate-400"
    >
      尚未設定章節結構，點擊「新增欄位」開始建立。
    </p>

    <div v-else class="space-y-3">
      <SchemaNodeEditor
        v-for="node in tree"
        :key="node.id"
        :node="node"
        :level="0"
        :disabled="disabled"
        :show-required="true"
        @remove="() => removeNode(node.id)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import type { PropType } from "vue";
import SchemaNodeEditor from "./SchemaNodeEditor.vue";
import { cloneNodes, createEmptyNode, type SchemaNode } from "./schema-tree";

// 元件名稱，方便 DevTools 與錯誤追蹤辨識。
defineOptions({ name: "SchemaStructureEditor" });

// 接收 schema 節點、章節描述與可編輯狀態。
const props = defineProps({
  modelValue: {
    type: Array as PropType<SchemaNode[]>,
    default: () => [],
  },
  description: {
    type: String,
    default: "",
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

// 對外同步事件：節點樹與描述欄位。
const emit = defineEmits<{
  (e: "update:modelValue", value: SchemaNode[]): void;
  (e: "update:description", value: string): void;
}>();

// 本地可編輯副本，避免直接改動 props。
const tree = ref<SchemaNode[]>(cloneNodes(props.modelValue));
const localDescription = ref(props.description);
let syncing = false;

// 當父層 modelValue 變動時，重新同步本地樹狀資料。
watch(
  () => props.modelValue,
  (value) => {
    syncing = true;
    tree.value = cloneNodes(value || []);
    nextTick(() => {
      syncing = false;
    });
  },
  { deep: true },
);

// 當父層描述更新時，同步到本地輸入框。
watch(
  () => props.description,
  (value) => {
    const nextValue = value ?? "";
    if (localDescription.value !== nextValue) {
      localDescription.value = nextValue;
    }
  },
);

// 監聽本地樹狀變更並回傳深拷貝，避免引用共享。
watch(
  tree,
  (value) => {
    if (syncing) {
      return;
    }
    emit("update:modelValue", cloneNodes(value));
  },
  { deep: true },
);

// 本地描述變動即時向外同步。
watch(localDescription, (value) => emit("update:description", value));

// 新增根層欄位節點。
function addRootField(): void {
  if (props.disabled) {
    return;
  }
  tree.value.push(
    createEmptyNode("string", {
      key: `欄位_${tree.value.length + 1}`,
    }),
  );
}

// 遞迴移除指定節點（支援 object children 與 array items）。
function removeNode(
  targetId: string,
  nodes: SchemaNode[] = tree.value,
): boolean {
  const index = nodes.findIndex((item) => item.id === targetId);
  if (index !== -1) {
    nodes.splice(index, 1);
    return true;
  }

  for (const node of nodes) {
    if (node.type === "object" && node.children.length) {
      const removed = removeNode(targetId, node.children);
      if (removed) {
        return true;
      }
    }
    if (node.type === "array" && node.items) {
      if (node.items.id === targetId) {
        node.items = null;
        return true;
      }
      if (node.items.type === "object") {
        const removedFromItems = removeNode(targetId, node.items.children);
        if (removedFromItems) {
          return true;
        }
      }
    }
  }

  return false;
}
</script>
