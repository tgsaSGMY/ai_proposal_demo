<template>
  <div v-if="isOpen" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>30 天成本走勢詳情</h2>
        <button class="btn-close" @click="closeModal">✕</button>
      </div>

      <div class="modal-body">
        <div class="trend-section">
          <div class="trend-meta">
            <p>最大單日：{{ formatCurrency(trendMaxCost) }}</p>
            <p>日期範圍：{{ trendRange.start }} → {{ trendRange.end }}</p>
          </div>

          <div v-if="trendPoints.length" class="trend-chart">
            <svg viewBox="0 0 100 40">
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
          <div v-else class="empty-state">暫無資料</div>
        </div>

        <div class="table-section">
          <h3>每日詳情</h3>
          <table v-if="trend.length">
            <thead>
              <tr>
                <th>日期</th>
                <th>成本</th>
                <th>Input Tokens</th>
                <th>Output Tokens</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="day in trend" :key="day.date">
                <td>{{ day.date }}</td>
                <td class="cost">{{ formatCurrency(day.cost) }}</td>
                <td>{{ formatTokens(day.inputTokens) }}</td>
                <td>{{ formatTokens(day.outputTokens) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state">無資料</div>
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

function closeModal() {
  emit("close");
}

function formatCurrency(value) {
  const number = Number(value || 0);
  if (number >= 1) {
    return `$${number.toFixed(2)}`;
  }
  if (number === 0) return "$0";
  return `$${number.toExponential(2)}`;
}

function formatTokens(value) {
  const numeric = Number(value || 0);
  if (numeric >= 1_000_000) return `${(numeric / 1_000_000).toFixed(1)}M`;
  if (numeric >= 1_000) return `${(numeric / 1_000).toFixed(1)}K`;
  return numeric.toLocaleString();
}

const trendMaxCost = computed(() => {
  if (!props.trend.length) return 0;
  return Math.max(...props.trend.map((p) => p.cost));
});

const trendRange = computed(() => {
  if (!props.trend.length) {
    return { start: "-", end: "-" };
  }
  return {
    start: props.trend[0].date,
    end: props.trend[props.trend.length - 1].date,
  };
});

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

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 0.5rem;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  font-size: 1.25rem;
  font-weight: bold;
  margin: 0;
  color: #1f2937;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.modal-body {
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.trend-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.trend-meta {
  display: flex;
  gap: 2rem;
  font-size: 0.875rem;
  color: #374151;
}

.trend-meta p {
  margin: 0;
  font-weight: 500;
}

.trend-chart {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  padding: 1rem;
}

.trend-chart svg {
  width: 100%;
  height: 200px;
}

.table-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.table-section h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  overflow: hidden;
}

th,
td {
  text-align: left;
  padding: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

th {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  color: #374151;
}

td.cost {
  font-weight: 600;
  color: #3b82f6;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
  border: 1px dashed #d1d5db;
  border-radius: 0.375rem;
  background: #f9fafb;
}

@media (max-width: 640px) {
  .modal-content {
    max-height: 95vh;
    max-width: calc(100% - 1rem);
  }

  .trend-meta {
    flex-direction: column;
    gap: 0.5rem;
  }

  table {
    font-size: 0.75rem;
  }

  th,
  td {
    padding: 0.5rem;
  }
}
</style>
