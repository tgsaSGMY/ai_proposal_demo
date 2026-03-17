<!-- 計劃成本詳情 (單一計劃成本點擊查看詳情) -->
<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4"
    @click="closeModal"
  >
    <div
      class="flex max-h-[95vh] w-full max-w-[calc(100%-1rem)] flex-col rounded-lg bg-white shadow-[0_10px_40px_rgba(0,0,0,0.2)] sm:max-h-[90vh] sm:max-w-[800px]"
      @click.stop
    >
      <div
        class="flex items-center justify-between border-b border-gray-200 p-6"
      >
        <h2 class="m-0 text-xl font-bold text-gray-800">計畫成本詳情</h2>
        <button
          class="flex h-8 w-8 items-center justify-center rounded-md border-0 bg-transparent p-0 text-2xl text-gray-500 transition hover:bg-gray-100 hover:text-gray-800"
          @click="closeModal"
        >
          ✕
        </button>
      </div>

      <div class="overflow-y-auto p-6">
        <table
          v-if="projects.length"
          class="w-full overflow-hidden rounded-md border border-gray-200 text-xs sm:text-sm"
        >
          <thead>
            <tr>
              <th
                class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold uppercase tracking-[0.05em] text-gray-700 sm:px-3"
              >
                Project ID
              </th>
              <th
                class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold uppercase tracking-[0.05em] text-gray-700 sm:px-3"
              >
                用戶郵箱
              </th>
              <th
                class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold uppercase tracking-[0.05em] text-gray-700 sm:px-3"
              >
                成本
              </th>
              <th
                class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold uppercase tracking-[0.05em] text-gray-700 sm:px-3"
              >
                Tokens
              </th>
              <th
                class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold uppercase tracking-[0.05em] text-gray-700 sm:px-3"
              >
                呼叫
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="project in projects" :key="project.projectId">
              <td
                class="border-b border-gray-200 px-2 py-2 text-gray-700 sm:px-3"
              >
                {{ project.projectId }}
              </td>
              <td
                class="border-b border-gray-200 px-2 py-2 text-gray-700 sm:px-3"
              >
                {{ project.email }}
              </td>
              <td
                class="border-b border-gray-200 px-2 py-2 font-semibold text-blue-500 sm:px-3"
              >
                {{ formatCurrency(project.totalCost) }}
              </td>
              <td
                class="border-b border-gray-200 px-2 py-2 text-gray-700 sm:px-3"
              >
                {{ formatTokens(project.inputTokens) }} /
                {{ formatTokens(project.outputTokens) }}
              </td>
              <td
                class="border-b border-gray-200 px-2 py-2 text-gray-700 sm:px-3"
              >
                {{ project.callCount }}
              </td>
            </tr>
          </tbody>
        </table>
        <div
          v-else
          class="rounded-md border border-dashed border-gray-300 bg-gray-50 p-8 text-center text-gray-500"
        >
          無計畫資料
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  projects: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["close"]);

// 關閉彈窗並通知父層更新顯示狀態。
function closeModal() {
  emit("close");
}

// 將成本轉為可讀格式：一般值保留兩位小數，極小值使用科學記號。
function formatCurrency(value) {
  const number = Number(value || 0);
  if (number >= 1) {
    return `$${number.toFixed(2)}`;
  }
  if (number === 0) return "$0";
  return `$${number.toExponential(2)}`;
}

// 將 token 數量縮寫為 K/M，避免表格欄位過長影響閱讀。
function formatTokens(value) {
  const numeric = Number(value || 0);
  if (numeric >= 1_000_000) return `${(numeric / 1_000_000).toFixed(1)}M`;
  if (numeric >= 1_000) return `${(numeric / 1_000).toFixed(1)}K`;
  return numeric.toLocaleString();
}
</script>
