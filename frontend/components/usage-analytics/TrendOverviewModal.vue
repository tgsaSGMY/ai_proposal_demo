<!-- 30天成本走勢詳情 -->
<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4"
    @click="closeModal"
  >
    <div
      class="flex max-h-[95vh] w-full max-w-[calc(100%-1rem)] flex-col rounded-lg bg-white shadow-[0_10px_40px_rgba(0,0,0,0.2)] sm:max-h-[90vh] sm:max-w-[900px]"
      @click.stop
    >
      <div
        class="flex items-center justify-between border-b border-gray-200 p-6"
      >
        <h2 class="m-0 text-xl font-bold text-gray-800">30 天成本走勢詳情</h2>
        <button
          class="flex h-8 w-8 items-center justify-center rounded-md border-0 bg-transparent p-0 text-2xl text-gray-500 transition hover:bg-gray-100 hover:text-gray-800"
          @click="closeModal"
        >
          ✕
        </button>
      </div>

      <div class="flex flex-col gap-8 overflow-y-auto p-6">
        <div class="flex flex-col gap-4">
          <div
            class="flex flex-col gap-2 text-sm text-gray-700 sm:flex-row sm:gap-8"
          >
            <p class="m-0 font-medium">
              最大單日：{{ formatCurrency(trendMaxCost) }}
            </p>
            <p class="m-0 font-medium">
              日期範圍：{{ trendRange.start }} → {{ trendRange.end }}
            </p>
          </div>

          <div
            v-if="trendPoints.length"
            class="rounded-md border border-gray-200 bg-gray-50 p-4"
          >
            <svg viewBox="0 0 100 40" class="h-[200px] w-full">
              <defs>
                <linearGradient
                  id="trendGradient"
                  x1="0%"
                  y1="0%"
                  x2="0%"
                  y2="100%"
                >
                  <stop offset="0%" stop-color="#34d399" stop-opacity="0.8" />
                  <stop offset="100%" stop-color="#34d399" stop-opacity="0.1" />
                </linearGradient>
              </defs>
              <polyline
                :points="trendPoints"
                stroke="url(#trendGradient)"
                fill="none"
                stroke-width="1.8"
              />
            </svg>
          </div>
          <div
            v-else
            class="rounded-md border border-dashed border-gray-300 bg-gray-50 p-8 text-center text-gray-500"
          >
            暫無資料
          </div>
        </div>

        <div class="flex flex-col gap-4">
          <h3 class="m-0 text-base font-semibold text-gray-800">每日詳情</h3>
          <table
            v-if="trend.length"
            class="w-full overflow-hidden rounded-md border border-gray-200 text-xs sm:text-sm"
          >
            <thead>
              <tr>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold uppercase tracking-[0.05em] text-gray-700 sm:px-3"
                >
                  日期
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold uppercase tracking-[0.05em] text-gray-700 sm:px-3"
                >
                  成本
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold uppercase tracking-[0.05em] text-gray-700 sm:px-3"
                >
                  Input Tokens
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold uppercase tracking-[0.05em] text-gray-700 sm:px-3"
                >
                  Output Tokens
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="day in trend" :key="day.date">
                <td
                  class="border-b border-gray-200 px-2 py-2 text-gray-700 sm:px-3"
                >
                  {{ day.date }}
                </td>
                <td
                  class="border-b border-gray-200 px-2 py-2 font-semibold text-blue-500 sm:px-3"
                >
                  {{ formatCurrency(day.cost) }}
                </td>
                <td
                  class="border-b border-gray-200 px-2 py-2 text-gray-700 sm:px-3"
                >
                  {{ formatTokens(day.inputTokens) }}
                </td>
                <td
                  class="border-b border-gray-200 px-2 py-2 text-gray-700 sm:px-3"
                >
                  {{ formatTokens(day.outputTokens) }}
                </td>
              </tr>
            </tbody>
          </table>
          <div
            v-else
            class="rounded-md border border-dashed border-gray-300 bg-gray-50 p-8 text-center text-gray-500"
          >
            無資料
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  trend: {
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

// 取得趨勢資料中的最大單日成本，用於摘要顯示。
const trendMaxCost = computed(() => {
  if (!props.trend.length) return 0;
  return Math.max(...props.trend.map((p) => p.cost));
});

// 計算資料的起訖日期，若無資料則回傳占位符。
const trendRange = computed(() => {
  if (!props.trend.length) {
    return { start: "-", end: "-" };
  }
  return {
    start: props.trend[0].date,
    end: props.trend[props.trend.length - 1].date,
  };
});

// 將每日成本換算成折線圖座標字串，提供 SVG polyline 使用。
const trendPoints = computed(() => {
  const data = props.trend || [];
  if (data.length <= 1) return [];
  const maxCost = Math.max(...data.map((p) => p.cost), 0.001);
  return data
    .map((point, index) => {
      const x = (index / (data.length - 1)) * 100;
      const y = 38 - (point.cost / maxCost) * 34;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
});
</script>
