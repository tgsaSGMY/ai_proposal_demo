<!-- 用途：編輯單一 Schema 節點，支援型別切換、子欄位管理與遞迴結構呈現。 -->
<template>
  <div class="relative">
    <!-- 樹形連接線（縱線） -->
    <div
      v-if="level > 0"
      class="absolute left-0 top-0 w-px h-full pointer-events-none bg-slate-300"
    ></div>

    <!-- 節點容器 -->
    <div
      class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm"
      :style="{ marginLeft: `${level * 24}px` }"
    >
      <!-- 樹形分支（橫線） -->
      <div
        v-if="level > 0"
        class="absolute left-0 top-6 w-6 h-px bg-slate-300"
      ></div>

      <div class="flex flex-wrap items-center gap-2">
        <div v-if="!node.isArrayItem" class="grow min-w-[8rem]">
          <input
            v-model="node.key"
            :disabled="disabled"
            class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-xs text-slate-900 focus:border-rose-400 focus:ring-rose-200 disabled:bg-slate-50"
            placeholder="欄位名稱"
          />
          <div v-if="node.key && node.key.includes('.')" class="w-full mt-1.5 p-2 bg-red-50 border border-red-200 rounded-lg text-red-600 text-xs">
            <div class="flex items-start gap-1.5">
              <span class="text-sm leading-none mt-0.5">⚠️</span>
              <span class="leading-relaxed font-medium">
                請勿在欄位名稱中使用點號「 <code class="font-bold">.</code> 」
                <br/><span class="text-slate-500 font-normal">這會導致 Word 編輯器路徑解析失敗。請改用底線「 <code class="font-bold">_</code> 」(例如：<code>1_經濟效益</code>)。</span>
              </span>
            </div>
          </div>
        </div>
        <select
          :value="node.type"
          :disabled="disabled"
          class="rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-900 focus:border-rose-400 focus:ring-rose-200 disabled:bg-slate-50"
          @change="handleTypeChange"
        >
          <option v-for="option in typeOptions" :key="option" :value="option">
            {{ typeLabels[option] }}
          </option>
        </select>
        <button
          type="button"
          class="rounded-lg border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-500 hover:bg-slate-50 transition-transform"
          :disabled="disabled"
          @click="toggleDetails"
        >
          <span v-if="collapsed">></span>
          <span v-else>▼</span>
        </button>
      </div>

      <!-- 展開區域：欄位說明、必填、刪除 -->
      <transition name="collapse">
        <div v-if="!collapsed" class="mt-2 space-y-2">
          <textarea
            v-model="node.description"
            :disabled="disabled"
            class="w-full rounded-lg border border-slate-200 bg-slate-50 px-2 py-1.5 text-xs text-slate-900 focus:border-rose-400 focus:ring-rose-200 disabled:bg-slate-50"
            placeholder="欄位說明 (選填)"
            rows="2"
          ></textarea>
          <div class="flex flex-wrap items-center gap-2">
            <label
              v-if="showRequired && !node.isArrayItem"
              class="flex items-center gap-1 text-xs font-semibold text-slate-600"
            >
              <input
                v-model="node.required"
                :disabled="disabled"
                type="checkbox"
                class="rounded border-slate-300 text-rose-500 focus:ring-rose-200"
              />
              必填
            </label>
            <button
              v-if="!node.isArrayItem"
              type="button"
              class="rounded-lg border border-slate-200 px-2 py-1 text-xs font-semibold text-slate-500 hover:bg-slate-50"
              :disabled="disabled"
              @click="emit('remove')"
            >
              刪除
            </button>
          </div>
        </div>
      </transition>

      <!-- 子欄位 -->
      <div v-if="node.type === 'object'" class="mt-3 space-y-2">
        <p v-if="!node.children.length" class="text-xs text-slate-400 ml-1">
          無子欄位
        </p>
        <SchemaNodeEditor
          v-for="(child, idx) in node.children"
          :key="child.id"
          :node="child"
          :level="level + 1"
          :disabled="disabled"
          :show-required="true"
          :is-last="idx === node.children.length - 1"
          @remove="() => removeChild(child.id)"
        />
        <button
          type="button"
          class="rounded-lg border border-dashed border-slate-300 px-2 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"
          :disabled="disabled"
          @click="addChild"
        >
          + 新增子欄位
        </button>
      </div>

      <!-- 列表項目 -->
      <div v-else-if="node.type === 'array'" class="mt-3 space-y-2">
        <SchemaNodeEditor
          v-if="node.items"
          :node="node.items"
          :level="level + 1"
          :disabled="disabled"
          :show-required="false"
          :is-last="true"
        />
        <button
          v-else
          type="button"
          class="rounded-lg border border-dashed border-slate-300 px-2 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"
          :disabled="disabled"
          @click="initializeArrayItem"
        >
          建立列表項目
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.2s ease;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
  overflow: hidden;
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { PropType } from "vue";
import {
  createEmptyNode,
  type SchemaNode,
  type SchemaNodeType,
} from "./schema-tree";

// 元件名稱，方便 DevTools 與錯誤追蹤辨識。
defineOptions({ name: "SchemaNodeEditor" });

// 接收節點資料、階層深度與互動狀態。
const props = defineProps({
  node: {
    type: Object as PropType<SchemaNode>,
    required: true,
  },
  level: {
    type: Number,
    default: 0,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  showRequired: {
    type: Boolean,
    default: true,
  },
  isLast: {
    type: Boolean,
    default: false,
  },
});

// 對外事件：移除當前節點。
const emit = defineEmits<{ (e: "remove"): void }>();

// 控制節點詳情區是否收合。
const collapsed = ref(true);

// 可選的欄位型別。
const typeOptions: SchemaNodeType[] = [
  "string",
  "number",
  "integer",
  "boolean",
  "object",
  "array",
];

// 欄位型別對應顯示名稱。
const typeLabels: Record<SchemaNodeType, string> = {
  string: "文字欄位",
  number: "數字",
  integer: "整數",
  boolean: "是非題",
  object: "複合欄位",
  array: "清單",
};

// 以 computed 包裝 props.node，便於模板中統一存取。
const node = computed(() => props.node);

// 切換詳情區展開/收合狀態。
function toggleDetails(): void {
  collapsed.value = !collapsed.value;
}

// 變更節點型別，並同步調整 object/array 所需結構。
function handleTypeChange(event: Event): void {
  if (props.disabled) {
    return;
  }
  const value = (event.target as HTMLSelectElement).value as SchemaNodeType;
  if (node.value.type === value) {
    return;
  }
  node.value.type = value;
  if (value === "object") {
    node.value.children = node.value.children ?? [];
    node.value.items = null;
  } else if (value === "array") {
    node.value.children = [];
    node.value.items =
      node.value.items ??
      createEmptyNode("string", {
        key: node.value.key ? `${node.value.key} 項目` : "列表項目",
        title: node.value.key ? `${node.value.key} 項目` : "列表項目",
        isArrayItem: true,
      });
  } else {
    node.value.children = [];
    node.value.items = null;
  }
}

// 為 object 節點新增子欄位。
function addChild(): void {
  if (props.disabled || node.value.type !== "object") {
    return;
  }
  node.value.children.push(
    createEmptyNode("string", {
      key: node.value.children.length
        ? `欄位_${node.value.children.length + 1}`
        : "欄位_1",
    }),
  );
}

// 移除 object 節點的指定子欄位。
function removeChild(childId: string): void {
  if (props.disabled || node.value.type !== "object") {
    return;
  }
  const idx = node.value.children.findIndex((child) => child.id === childId);
  if (idx >= 0) {
    node.value.children.splice(idx, 1);
  }
}

// 初始化 array 節點的 items 定義。
function initializeArrayItem(): void {
  if (props.disabled || node.value.type !== "array") {
    return;
  }
  node.value.items = createEmptyNode("string", {
    key: node.value.key ? `${node.value.key} 項目` : "列表項目",
    title: node.value.key ? `${node.value.key} 項目` : "列表項目",
    isArrayItem: true,
  });
}
</script>
