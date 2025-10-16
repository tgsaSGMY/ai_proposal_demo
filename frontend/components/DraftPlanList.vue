<!-- /components/DraftPlanList.vue -->
<template>
  <div>
    <!-- Filter Controls -->
    <div class="mb-4 flex items-center gap-4">
      <input
        type="text"
        v-model="searchTerm"
        placeholder="搜索企划名称..."
        class="input-class w-full max-w-xs"
      />
      <select v-model="filterMode" class="select-class">
        <option value="">所有模式</option>
        <option value="synthetic">AI 生成</option>
        <option value="golden">手动标注</option>
        <option value="internal">生成企划书</option>
      </select>
    </div>

    <!-- Drafts Grid -->
    <div
      v-if="filteredDrafts.length > 0"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
    >
      <div
        v-for="draft in filteredDrafts"
        :key="draft.id"
        @click="$emit('select', draft)"
        class="bg-white shadow rounded-lg p-4 cursor-pointer hover:shadow-lg transition-shadow border-l-4"
        :class="getStatusBorderColor(draft.status)"
      >
        <div class="flex justify-between items-start">
          <h3 class="font-bold truncate pr-2">{{ draft.name }}</h3>
          <span class="text-xs font-mono text-gray-400">{{
            modeMap(draft.mode)
          }}</span>
        </div>
        <div class="mt-2 text-sm flex items-center gap-2">
          <span class="font-medium text-gray-600">状态:</span>
          <span
            :class="getStatusTextColor(draft.status)"
            class="font-semibold"
            >{{ getStatusText(draft.status) }}</span
          >
        </div>
        <div class="text-xs text-gray-400 mt-1">
          更新于: {{ new Date(draft.updated_at).toLocaleString() }}
        </div>
        <div
          v-if="
            draft.status === 'generating_idea' ||
            draft.status === 'generating_plan'
          "
          class="w-full bg-gray-200 rounded-full h-1.5 mt-3"
        >
          <div class="bg-blue-600 h-1.5 rounded-full animate-pulse"></div>
        </div>
      </div>
    </div>
    <div v-else class="text-center py-10 bg-white rounded-lg shadow">
      <p class="text-gray-500">没有找到符合条件的企划草稿。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({ drafts: Array });
defineEmits(["select"]);

const searchTerm = ref("");
const filterMode = ref("");

const filteredDrafts = computed(() => {
  return props.drafts.filter((draft) => {
    const nameMatch = draft.name
      .toLowerCase()
      .includes(searchTerm.value.toLowerCase());
    const modeMatch = !filterMode.value || draft.mode === filterMode.value;
    return nameMatch && modeMatch;
  });
});

function getStatusBorderColor(status) {
  const map = {
    completed: "border-green-500",
    generating_idea: "border-blue-500",
    generating_plan: "border-blue-500",
    pending: "border-gray-400",
    error: "border-red-500",
  };
  return map[status] || "border-gray-300";
}

function modeMap(status) {
  const map = {
    golden: "黃金範例",
    internal: "生成企劃",
    synthetic: "AI生成",
  };
  return map[status] || "border-gray-300";
}

function getStatusTextColor(status) {
  const map = {
    completed: "text-green-600",
    generating_idea: "text-blue-600",
    generating_plan: "text-blue-600",
    pending: "text-gray-600",
    error: "text-red-600",
  };
  return map[status] || "text-gray-500";
}

function getStatusText(status) {
  const map = {
    completed: "已完成",
    generating_idea: "生成想法中...",
    generating_plan: "生成计划中...",
    pending: "待处理",
    error: "失败",
  };
  return map[status] || status;
}
</script>

<style scoped>
/* 简单的输入框和选择框样式，可以放到全局 CSS 中 */
.input-class,
.select-class {
  @apply block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm;
}
</style>
