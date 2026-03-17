<!-- 用戶分析點擊詳情 -->
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
        <h2 class="m-0 text-xl font-bold text-gray-800">用戶分析詳情</h2>
        <button
          class="flex h-8 w-8 items-center justify-center rounded-md border-0 bg-transparent p-0 text-2xl text-gray-500 transition hover:bg-gray-100 hover:text-gray-800"
          @click="closeModal"
        >
          ✕
        </button>
      </div>

      <div class="overflow-y-auto p-6">
        <table
          v-if="users.length"
          class="w-full overflow-hidden rounded-md border border-gray-200 text-xs sm:text-sm"
        >
          <thead>
            <tr>
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
              <th
                class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold uppercase tracking-[0.05em] text-gray-700 sm:px-3"
              >
                專案數
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.userId">
              <td
                class="border-b border-gray-200 px-2 py-2 text-gray-700 sm:px-3"
              >
                {{ user.email }}
              </td>
              <td
                class="border-b border-gray-200 px-2 py-2 font-semibold text-blue-500 sm:px-3"
              >
                {{ formatCurrency(user.totalCost) }}
              </td>
              <td
                class="border-b border-gray-200 px-2 py-2 text-gray-700 sm:px-3"
              >
                {{ formatTokens(user.inputTokens) }} /
                {{ formatTokens(user.outputTokens) }}
              </td>
              <td
                class="border-b border-gray-200 px-2 py-2 text-gray-700 sm:px-3"
              >
                {{ user.callCount }}
              </td>
              <td
                class="border-b border-gray-200 px-2 py-2 text-gray-700 sm:px-3"
              >
                {{ user.projectCount }}
              </td>
            </tr>
          </tbody>
        </table>
        <div
          v-else
          class="rounded-md border border-dashed border-gray-300 bg-gray-50 p-8 text-center text-gray-500"
        >
          無用戶資料
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
  users: {
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
