<template>
  <div v-if="isOpen" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>企劃成本詳情</h2>
        <button class="btn-close" @click="closeModal">✕</button>
      </div>

      <div class="modal-body">
        <table v-if="projects.length">
          <thead>
            <tr>
              <th>Project ID</th>
              <th>用戶郵箱</th>
              <th>成本</th>
              <th>Tokens</th>
              <th>呼叫</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="project in projects" :key="project.projectId">
              <td>{{ project.projectId }}</td>
              <td>{{ project.email }}</td>
              <td class="cost">{{ formatCurrency(project.totalCost) }}</td>
              <td>
                {{ formatTokens(project.inputTokens) }} /
                {{ formatTokens(project.outputTokens) }}
              </td>
              <td>{{ project.callCount }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-state">無企劃資料</div>
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
  max-width: 800px;
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

  table {
    font-size: 0.75rem;
  }

  th,
  td {
    padding: 0.5rem;
  }
}
</style>
