<template>
  <ClientOnly>
    <div class="usage-analytics-page">
      <section class="hero">
        <div>
          <p class="hero-eyebrow">AI Ops · Internal Only</p>
          <h1>內部成本儀表板</h1>
          <p class="hero-subtitle">
            透過維度與聚合快速定位成本熱區，判斷燃燒速度、超級用戶、昂貴行為與模型性價比。
          </p>
        </div>
        <div class="hero-meta">
          <p class="hero-range">{{ rangeSummary }}</p>
          <p class="hero-update">
            上次更新：
            <span>{{
              analytics?.lastUpdated
                ? formatDateTime(analytics.lastUpdated)
                : "尚未取得"
            }}</span>
          </p>
          <button class="btn btn-primary" @click="refresh" :disabled="loading">
            {{ loading ? "更新中..." : "重新整理" }}
          </button>
        </div>
      </section>

      <section class="glass-panel control-panel">
        <div class="panel-row">
          <div class="form-field full">
            <label>時間範圍</label>
            <div class="preset-buttons">
              <button
                v-for="preset in rangePresets"
                :key="preset.key"
                type="button"
                class="btn btn-chip"
                :class="{ active: filters.preset === preset.key }"
                @click="setPreset(preset.key)"
              >
                {{ preset.label }}
              </button>
            </div>
          </div>
        </div>
        <div class="panel-row">
          <div class="form-field">
            <label>開始日期</label>
            <input
              type="date"
              v-model="filters.startDate"
              @change="onCustomRange"
            />
          </div>
          <div class="form-field">
            <label>結束日期</label>
            <input
              type="date"
              v-model="filters.endDate"
              @change="onCustomRange"
            />
          </div>
          <div class="form-field">
            <label>使用者</label>
            <select v-model="filters.userId">
              <option value="">全部</option>
              <option
                v-for="user in filterOptions.users"
                :key="user.id"
                :value="user.id"
              >
                {{ user.email || user.id }}
              </option>
            </select>
          </div>
          <div class="form-field">
            <label>專案</label>
            <select v-model="filters.projectId">
              <option value="">全部</option>
              <option
                v-for="project in filterOptions.projects"
                :key="project.id"
                :value="project.id"
              >
                {{ project.id }}
              </option>
            </select>
          </div>
          <div class="form-field">
            <label>模型</label>
            <select v-model="filters.modelId">
              <option value="">全部</option>
              <option
                v-for="model in filterOptions.models"
                :key="model.id"
                :value="model.id"
              >
                {{ model.id }}
              </option>
            </select>
          </div>
          <div class="form-field">
            <label>功能 / Action</label>
            <select v-model="filters.action">
              <option value="">全部</option>
              <option
                v-for="actionOption in filterOptions.actions"
                :key="actionOption.id"
                :value="actionOption.id"
              >
                {{ actionOption.id }}
              </option>
            </select>
          </div>
        </div>
        <div class="panel-actions">
          <button
            class="btn btn-primary"
            @click="applyFilters"
            :disabled="loading"
          >
            套用篩選
          </button>
          <button
            class="btn btn-ghost"
            type="button"
            @click="resetFilters"
            :disabled="loading"
          >
            重置
          </button>
        </div>
        <p v-if="errorMessage" class="error-pill">{{ errorMessage }}</p>
      </section>

      <section v-if="analytics" class="grid grid-overview">
        <article class="kpi-card">
          <p class="kpi-label">總成本</p>
          <p class="kpi-value">{{ formatCurrency(overview.totalCostMTD) }}</p>
          <p class="kpi-hint">含所有時間區間内的呼叫</p>
        </article>
        <article class="kpi-card">
          <p class="kpi-label">區間 Token 消耗</p>
          <p class="kpi-value">
            {{ formatTokens(overview.totalInputTokens) }} /
            {{ formatTokens(overview.totalOutputTokens) }}
          </p>
          <p class="kpi-hint">Input / Output</p>
        </article>
        <article class="kpi-card">
          <p class="kpi-label">活躍專案 · 呼叫數</p>
          <p class="kpi-value">
            {{ overview.activeProjects }} / {{ overview.totalCalls }}
          </p>
          <p class="kpi-hint">範圍內至少一次呼叫</p>
        </article>
      </section>

      <section v-if="analytics" class="grid grid-major">
        <article class="glass-panel trend-card">
          <header>
            <div>
              <p class="section-eyebrow">Global Overview</p>
              <h2>30 天成本走勢</h2>
            </div>
            <div class="trend-meta">
              <p>最大單日：{{ formatCurrency(trendMaxCost) }}</p>
            </div>
          </header>
          <div v-if="!trendPoints.length" class="empty-state">
            暫無資料，請調整範圍或等待新呼叫。
          </div>
          <div v-else class="trend-body">
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
            <div class="trend-footer">
              <span>{{ trendRange.start }}</span>
              <span>{{ trendRange.end }}</span>
            </div>
            <button class="btn btn-expand" @click="showTrendModal = true">
              查看詳情 →
            </button>
          </div>
        </article>

        <article class="glass-panel" v-if="topUsers.length">
          <header>
            <p class="section-eyebrow">By User</p>
            <h2>用戶分析</h2>
          </header>
          <table>
            <thead>
              <tr>
                <th>用戶郵箱</th>
                <th>成本</th>
                <th>Tokens</th>
                <th>呼叫</th>
                <th>專案數</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in topUsers" :key="user.userId">
                <td>{{ user.email }}</td>
                <td>{{ formatCurrency(user.totalCost) }}</td>
                <td>
                  {{ formatTokens(user.inputTokens) }} /
                  {{ formatTokens(user.outputTokens) }}
                </td>
                <td>{{ user.callCount }}</td>
                <td>{{ user.projectCount }}</td>
              </tr>
            </tbody>
          </table>
          <button
            v-if="allUsers.length > 3"
            class="btn btn-secondary"
            @click="showUserDetailsModal = true"
          >
            查看詳情 →
          </button>
        </article>

        <article class="glass-panel" v-if="topProjects.length">
          <header>
            <p class="section-eyebrow">By Project</p>
            <h2>單一企劃成本</h2>
          </header>
          <table>
            <thead>
              <tr>
                <th>Project ID</th>
                <th>成本</th>
                <th>Tokens</th>
                <th>呼叫</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="project in topProjects" :key="project.projectId">
                <td>{{ project.projectId }}</td>
                <td>{{ formatCurrency(project.totalCost) }}</td>
                <td>
                  {{ formatTokens(project.inputTokens) }} /
                  {{ formatTokens(project.outputTokens) }}
                </td>
                <td>{{ project.callCount }}</td>
              </tr>
            </tbody>
          </table>
          <button
            class="btn btn-secondary"
            @click="showProjectDetailsModal = true"
          >
            查看詳情 →
          </button>
        </article>
      </section>

      <section v-if="analytics" class="grid grid-duo">
        <article class="glass-panel">
          <header>
            <p class="section-eyebrow">By Action</p>
            <h2>功能成本分佈</h2>
          </header>
          <div v-if="!analytics.byAction.length" class="empty-state">
            無行為記錄。
          </div>
          <div v-else class="action-list">
            <div
              v-for="actionRow in analytics.byAction"
              :key="actionRow.action"
              class="action-row"
            >
              <div>
                <p class="action-name">{{ actionRow.action }}</p>
                <p class="action-sub">{{ actionRow.callCount }} 次</p>
              </div>
              <div class="action-bar">
                <span class="action-value">{{
                  formatCurrency(actionRow.totalCost)
                }}</span>
                <div class="bar">
                  <span
                    class="fill"
                    :style="{ width: `${actionWidth(actionRow.totalCost)}%` }"
                  ></span>
                </div>
              </div>
            </div>
          </div>
        </article>

        <article class="glass-panel">
          <header>
            <p class="section-eyebrow">By Model</p>
            <h2>模型性價比</h2>
          </header>
          <table v-if="modelStats.length">
            <thead>
              <tr>
                <th>模型</th>
                <th>成本</th>
                <th>Tokens</th>
                <th>呼叫</th>
                <th>平均成本</th>
                <th>佔比</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="model in modelStats" :key="model.modelId">
                <td>{{ model.modelId }}</td>
                <td>{{ formatCurrency(model.totalCost) }}</td>
                <td>
                  {{ formatTokens(model.inputTokens) }} /
                  {{ formatTokens(model.outputTokens) }}
                </td>
                <td>{{ model.callCount }}</td>
                <td>{{ formatCurrency(model.avgCost) }}</td>
                <td>{{ model.share.toFixed(1) }}%</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state">尚無模型資料</div>
        </article>
      </section>

      <p v-if="!analytics && !loading" class="empty-state">
        尚未取得任何使用資料，請先套用篩選。
      </p>

      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <p>資料更新中...</p>
      </div>

      <TrendOverviewModal
        :isOpen="showTrendModal"
        :trend="analytics?.trend || []"
        @close="showTrendModal = false"
      />

      <UserDetailsModal
        :isOpen="showUserDetailsModal"
        :users="allUsers"
        @close="showUserDetailsModal = false"
      />

      <ProjectDetailsModal
        :isOpen="showProjectDetailsModal"
        :projects="allProjects"
        @close="showProjectDetailsModal = false"
      />
    </div>
  </ClientOnly>
</template>

<script setup>
definePageMeta({
  middleware: "auth",
});

useHead({
  title: "成本分析儀表板 - TGSA 補助引擎",
  meta: [
    {
      name: "description",
      content:
        "追蹤 AI 模型成本與 Token 耗用，針對用戶、專案、功能與模型產生洞察。",
    },
  ],
});

import { ref, reactive, computed, onMounted } from "vue";
import { authenticatedFetch } from "~/composables/useAppAuth";
import { useNotifications } from "~/composables/useNotifications";
import { useInternalCheck } from "~/composables/useInternalCheck";
import TrendOverviewModal from "~/components/usage-analytics/TrendOverviewModal.vue";
import UserDetailsModal from "~/components/usage-analytics/UserDetailsModal.vue";
import ProjectDetailsModal from "~/components/usage-analytics/ProjectDetailsModal.vue";

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const analytics = ref(null);
const loading = ref(false);
const errorMessage = ref("");
const showTrendModal = ref(false);
const showUserDetailsModal = ref(false);
const showProjectDetailsModal = ref(false);
const { error: notifyError, success } = useNotifications();
const { checkIsInternal } = useInternalCheck();

const rangePresets = [
  { key: "7d", label: "近 7 天", days: 7 },
  { key: "30d", label: "近 30 天", days: 30 },
  { key: "90d", label: "近 90 天", days: 90 },
];

const filters = reactive({
  preset: "30d",
  startDate: formatDate(shiftDays(new Date(), -29)),
  endDate: formatDate(new Date()),
  userId: "",
  projectId: "",
  modelId: "",
  action: "",
});

const filterOptions = reactive({
  users: [],
  projects: [],
  models: [],
  actions: [],
});

const overview = computed(
  () =>
    analytics.value?.globalOverview || {
      totalCostMTD: 0,
      rangeCost: 0,
      totalInputTokens: 0,
      totalOutputTokens: 0,
      activeProjects: 0,
      totalCalls: 0,
    },
);

const topUsers = computed(() => {
  const allUsers = analytics.value?.byUser?.rows || [];
  return allUsers.slice(0, 3);
});

const allUsers = computed(() => analytics.value?.byUser?.rows || []);

const topProjects = computed(() => {
  const allProjects = analytics.value?.byProject?.rows || [];
  return allProjects.slice(0, 3);
});

const allProjects = computed(() => analytics.value?.byProject?.rows || []);

const totalCostInRange = computed(() => overview.value.rangeCost || 0);

const modelStats = computed(() => {
  const models = analytics.value?.byModel || [];
  const total =
    totalCostInRange.value ||
    models.reduce((acc, row) => acc + (row.totalCost || 0), 0);
  if (!models.length || total === 0) {
    return [];
  }
  return models.map((row) => ({
    ...row,
    share: row.totalCost ? (row.totalCost / total) * 100 : 0,
  }));
});

const trendPoints = computed(() => {
  const trend = analytics.value?.trend || [];
  if (trend.length <= 1) return [];
  const maxCost = Math.max(...trend.map((p) => p.cost), 0.001);
  return trend
    .map((point, index) => {
      const x = (index / (trend.length - 1)) * 100;
      const y = 38 - (point.cost / maxCost) * 34;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
});

const trendMaxCost = computed(() => {
  const trend = analytics.value?.trend || [];
  if (!trend.length) return 0;
  return Math.max(...trend.map((p) => p.cost));
});

const trendRange = computed(() => {
  const trend = analytics.value?.trend || [];
  if (!trend.length) {
    return { start: filters.startDate, end: filters.endDate };
  }
  return {
    start: trend[0].date,
    end: trend[trend.length - 1].date,
  };
});

const rangeSummary = computed(
  () => `${filters.startDate} → ${filters.endDate}`,
);

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

function formatDate(dateInput) {
  const d = new Date(dateInput);
  return d.toISOString().slice(0, 10);
}

function formatDateTime(isoString) {
  const d = new Date(isoString);
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`;
}

function shiftDays(base, offset) {
  const clone = new Date(base);
  clone.setDate(clone.getDate() + offset);
  return clone;
}

function actionWidth(cost) {
  const rows = analytics.value?.byAction || [];
  if (!rows.length) return 0;
  const max = Math.max(...rows.map((row) => row.totalCost || 0), 0.0001);
  return Math.min(100, (cost / max) * 100);
}

function onCustomRange() {
  filters.preset = "custom";
}

function setPreset(key) {
  const preset = rangePresets.find((item) => item.key === key);
  if (!preset) return;
  filters.preset = key;
  filters.endDate = formatDate(new Date());
  filters.startDate = formatDate(shiftDays(new Date(), -(preset.days - 1)));
}

function resetFilters() {
  filters.preset = "30d";
  filters.startDate = formatDate(shiftDays(new Date(), -29));
  filters.endDate = formatDate(new Date());
  filters.userId = "";
  filters.projectId = "";
  filters.modelId = "";
  filters.action = "";
  applyFilters();
}

function validateRange() {
  if (!filters.startDate || !filters.endDate) {
    return false;
  }
  return new Date(filters.startDate) <= new Date(filters.endDate);
}

async function fetchAnalytics(showToast = false) {
  loading.value = true;
  errorMessage.value = "";
  try {
    const params = new URLSearchParams();
    params.append("start_date", filters.startDate);
    params.append("end_date", filters.endDate);
    if (filters.userId) params.append("user_id", filters.userId);
    if (filters.projectId) params.append("project_id", filters.projectId);
    if (filters.modelId) params.append("model_id", filters.modelId);
    if (filters.action) params.append("action", filters.action);

    const response = await authenticatedFetch(
      `${API_BASE_URL}/usage-log/analytics?${params.toString()}`,
    );

    if (!response.ok) {
      const detail = await response.json().catch(() => ({ detail: "" }));
      throw new Error(detail.detail || "無法取得儀表板資料");
    }

    const data = await response.json();
    analytics.value = data;
    filterOptions.users = data.availableFilters?.users || [];
    filterOptions.projects = data.availableFilters?.projects || [];
    filterOptions.models = data.availableFilters?.models || [];
    filterOptions.actions = data.availableFilters?.actions || [];
    if (showToast) {
      success("儀表板已更新");
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    errorMessage.value = message;
    notifyError(message);
  } finally {
    loading.value = false;
  }
}

async function applyFilters() {
  if (!validateRange()) {
    const msg = "請確認開始日期早於結束日期";
    errorMessage.value = msg;
    notifyError(msg);
    return;
  }
  await fetchAnalytics(false);
}

const refresh = () => fetchAnalytics(true);

onMounted(async () => {
  const isInternal = await checkIsInternal();
  if (!isInternal) {
    window.location.href = "/";
    return;
  }
  await fetchAnalytics();
});
</script>

<style scoped>
.usage-analytics-page {
  min-height: 100vh;
  padding: 1rem;
  background: #f9fafb;
  color: #1f2937;
}

.hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.hero-eyebrow {
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6b7280;
  font-size: 0.75rem;
}

.hero h1 {
  font-size: 1.875rem;
  margin-bottom: 0.25rem;
  font-weight: bold;
}

.hero-subtitle {
  color: #6b7280;
  max-width: 48ch;
  font-size: 0.875rem;
}

.hero-meta {
  text-align: right;
  font-size: 0.875rem;
}

.hero-meta p {
  margin-bottom: 0.5rem;
}

.hero-meta span {
  font-weight: 600;
  color: #374151;
}

.hero-range {
  font-weight: 600;
  color: #374151;
}

.btn {
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
  font-weight: 600;
  font-size: 0.875rem;
  transition: all 0.2s ease;
  border: none;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:not(:disabled):hover {
  background: #2563eb;
}

.btn-ghost {
  background: #e5e7eb;
  color: #374151;
}

.btn-ghost:not(:disabled):hover {
  background: #d1d5db;
}

.btn-chip {
  background: #f3f4f6;
  color: #374151;
  padding: 0.35rem 0.75rem;
  border: 1px solid #e5e7eb;
}

.btn-chip.active {
  border-color: #3b82f6;
  background: #eff6ff;
  color: #1e40af;
}

.glass-panel {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

.panel-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-field label {
  display: block;
  font-size: 0.85rem;
  color: #374151;
  margin-bottom: 0.35rem;
  font-weight: 500;
}

.form-field input,
.form-field select {
  width: 100%;
  border-radius: 0.375rem;
  border: 1px solid #d1d5db;
  padding: 0.5rem 0.75rem;
  background: white;
  color: #1f2937;
  font-size: 0.875rem;
}

.preset-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.panel-actions {
  display: flex;
  gap: 1rem;
}

.error-pill {
  margin-top: 0.5rem;
  padding: 0.35rem 0.75rem;
  border-radius: 0.375rem;
  background: #fee2e2;
  color: #991b1b;
  font-size: 0.8rem;
}

.grid-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.kpi-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.kpi-label {
  font-size: 0.8rem;
  color: #6b7280;
  font-weight: 500;
}

.kpi-value {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0.35rem 0;
  color: #1f2937;
}

.kpi-hint {
  font-size: 0.75rem;
  color: #9ca3af;
}

.grid-major {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.section-eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6b7280;
  font-size: 0.7rem;
  font-weight: 600;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.75rem;
  font-size: 0.875rem;
  overflow-x: auto;
}

th,
td {
  text-align: left;
  padding: 0.5rem 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

th {
  font-size: 0.8rem;
  color: #374151;
  font-weight: 600;
  background: #f9fafb;
}

td {
  color: #374151;
}

.glass-panel {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

.grid-duo {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.action-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
}

.action-name {
  font-weight: 600;
  color: #1f2937;
  font-size: 0.875rem;
}

.action-sub {
  font-size: 0.75rem;
  color: #6b7280;
}

.action-bar {
  flex: 1;
}

.action-value {
  display: block;
  text-align: right;
  font-size: 0.8rem;
  color: #374151;
  font-weight: 500;
}

.bar {
  width: 100%;
  height: 0.4rem;
  border-radius: 0.25rem;
  background: #e5e7eb;
  overflow: hidden;
  margin-top: 0.25rem;
}

.bar .fill {
  display: block;
  height: 100%;
  border-radius: 0.25rem;
  background: linear-gradient(90deg, #3b82f6, #06b6d4);
}

.trend-card svg {
  width: 100%;
  height: 150px;
  stroke: #3b82f6;
}

.trend-footer {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.5rem;
  margin-bottom: 0.75rem;
}

.btn-expand {
  background: #f3f4f6;
  color: #3b82f6;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-expand:hover {
  background: #eff6ff;
  border-color: #3b82f6;
}

.btn-secondary {
  margin-top: 1rem;
  background: #f3f4f6;
  color: #3b82f6;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;
}

.btn-secondary:hover {
  background: #eff6ff;
  border-color: #3b82f6;
}

.trend-body {
  margin-top: 0.75rem;
}

.empty-state {
  text-align: center;
  color: #6b7280;
  padding: 1.5rem;
  border: 1px dashed #d1d5db;
  border-radius: 0.5rem;
  background: #f9fafb;
}

.loading-overlay {
  position: fixed;
  inset: 0;
  backdrop-filter: blur(2px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: rgba(255, 255, 255, 0.75);
  z-index: 50;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

header {
  margin-bottom: 1.5rem;
}

header p.section-eyebrow {
  margin: 0;
}

header h2 {
  margin: 0.25rem 0;
  font-size: 1.25rem;
  font-weight: bold;
  color: #1f2937;
}

@media (max-width: 900px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-meta {
    text-align: left;
  }

  .panel-actions {
    flex-direction: column;
  }
}
</style>
