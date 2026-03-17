<!-- 主要是一个内部使用的成本分析仪表板页面，提供了对 AI 模型使用情况和成本的深入洞察。用户可以通过不同的维度（如用户、项目、模型、功能）来分析成本分布和趋势。 -->
<template>
  <ClientOnly>
    <div class="min-h-screen bg-gray-50 p-4 text-gray-800">
      <section
        class="mb-6 flex items-end justify-between gap-8 max-[900px]:flex-col max-[900px]:items-start"
      >
        <div>
          <p class="text-xs uppercase tracking-[0.1em] text-gray-500">
            AI Ops · Internal Only
          </p>
          <h1 class="mb-1 text-3xl font-bold">內部成本儀表板</h1>
          <p class="max-w-[48ch] text-sm text-gray-500">
            透過維度與聚合快速定位成本熱區，判斷燃燒速度、超級用戶、昂貴行為與模型性價比。
          </p>
        </div>
        <div class="text-right text-sm max-[900px]:text-left">
          <p class="font-semibold text-gray-700">{{ rangeSummary }}</p>
          <p class="mb-2">
            上次更新：
            <span class="font-semibold text-gray-700">{{
              analytics?.lastUpdated
                ? formatDateTime(analytics.lastUpdated)
                : "尚未取得"
            }}</span>
          </p>
          <button
            class="rounded-lg bg-blue-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
            @click="refresh"
            :disabled="loading"
          >
            {{ loading ? "更新中..." : "重新整理" }}
          </button>
        </div>
      </section>

      <section
        class="overflow-x-auto rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
      >
        <div
          class="mb-4 grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(150px,1fr))]"
        >
          <div>
            <label class="mb-1 block text-[0.85rem] font-medium text-gray-700"
              >時間範圍</label
            >
            <div class="flex flex-wrap gap-2">
              <button
                v-for="preset in rangePresets"
                :key="preset.key"
                type="button"
                class="rounded-lg border px-3 py-1.5 text-sm font-semibold transition"
                :class="
                  filters.preset === preset.key
                    ? 'border-blue-500 bg-blue-50 text-blue-800'
                    : 'border-gray-200 bg-gray-100 text-gray-700 hover:bg-gray-200'
                "
                @click="setPreset(preset.key)"
              >
                {{ preset.label }}
              </button>
            </div>
          </div>
        </div>
        <div
          class="mb-4 grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(150px,1fr))]"
        >
          <div>
            <label class="mb-1 block text-[0.85rem] font-medium text-gray-700"
              >開始日期</label
            >
            <input
              type="date"
              v-model="filters.startDate"
              @change="onCustomRange"
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800"
            />
          </div>
          <div>
            <label class="mb-1 block text-[0.85rem] font-medium text-gray-700"
              >結束日期</label
            >
            <input
              type="date"
              v-model="filters.endDate"
              @change="onCustomRange"
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800"
            />
          </div>
          <div>
            <label class="mb-1 block text-[0.85rem] font-medium text-gray-700"
              >使用者</label
            >
            <select
              v-model="filters.userId"
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800"
            >
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
          <div>
            <label class="mb-1 block text-[0.85rem] font-medium text-gray-700"
              >專案</label
            >
            <select
              v-model="filters.projectId"
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800"
            >
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
          <div>
            <label class="mb-1 block text-[0.85rem] font-medium text-gray-700"
              >模型</label
            >
            <select
              v-model="filters.modelId"
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800"
            >
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
          <div>
            <label class="mb-1 block text-[0.85rem] font-medium text-gray-700"
              >功能 / Action</label
            >
            <select
              v-model="filters.action"
              class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800"
            >
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
        <div class="flex gap-4 max-[900px]:flex-col">
          <button
            class="rounded-lg bg-blue-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
            @click="applyFilters"
            :disabled="loading"
          >
            套用篩選
          </button>
          <button
            class="rounded-lg bg-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:bg-gray-300 disabled:cursor-not-allowed disabled:opacity-50"
            type="button"
            @click="resetFilters"
            :disabled="loading"
          >
            重置
          </button>
        </div>
        <p
          v-if="errorMessage"
          class="mt-2 rounded-md bg-red-100 px-3 py-1.5 text-xs text-red-800"
        >
          {{ errorMessage }}
        </p>
      </section>

      <section
        v-if="analytics"
        class="mb-6 grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]"
      >
        <article
          class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
        >
          <p class="text-[0.8rem] font-medium text-gray-500">總成本</p>
          <p class="my-1 text-2xl font-bold text-gray-800">
            {{ formatCurrency(overview.totalCostMTD) }}
          </p>
          <p class="text-xs text-gray-400">含所有時間區間内的呼叫</p>
        </article>
        <article
          class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
        >
          <p class="text-[0.8rem] font-medium text-gray-500">區間 Token 消耗</p>
          <p class="my-1 text-2xl font-bold text-gray-800">
            {{ formatTokens(overview.totalInputTokens) }} /
            {{ formatTokens(overview.totalOutputTokens) }}
          </p>
          <p class="text-xs text-gray-400">Input / Output</p>
        </article>
        <article
          class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
        >
          <p class="text-[0.8rem] font-medium text-gray-500">
            活躍專案 · 呼叫數
          </p>
          <p class="my-1 text-2xl font-bold text-gray-800">
            {{ overview.activeProjects }} / {{ overview.totalCalls }}
          </p>
          <p class="text-xs text-gray-400">範圍內至少一次呼叫</p>
        </article>
      </section>

      <section
        v-if="analytics"
        class="mb-6 grid gap-5 [grid-template-columns:repeat(auto-fit,minmax(280px,1fr))]"
      >
        <article
          class="overflow-x-auto rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
        >
          <header class="mb-6">
            <div>
              <p
                class="text-[0.7rem] font-semibold uppercase tracking-[0.05em] text-gray-500"
              >
                Global Overview
              </p>
              <h2 class="my-1 text-xl font-bold text-gray-800">
                30 天成本走勢
              </h2>
            </div>
            <div class="text-sm text-gray-600">
              <p>最大單日：{{ formatCurrency(trendMaxCost) }}</p>
            </div>
          </header>
          <div
            v-if="!trendPoints.length"
            class="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-gray-500"
          >
            暫無資料，請調整範圍或等待新呼叫。
          </div>
          <div v-else class="mt-3">
            <svg viewBox="0 0 100 40" class="h-[150px] w-full stroke-blue-500">
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
            <div class="mb-3 mt-2 flex justify-between text-xs text-gray-500">
              <span>{{ trendRange.start }}</span>
              <span>{{ trendRange.end }}</span>
            </div>
            <button
              class="rounded-md border border-gray-300 bg-gray-100 px-4 py-2 text-sm font-semibold text-blue-500 transition hover:border-blue-500 hover:bg-blue-50"
              @click="showTrendModal = true"
            >
              查看詳情 →
            </button>
          </div>
        </article>

        <article
          class="overflow-x-auto rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
          v-if="topUsers.length"
        >
          <header class="mb-6">
            <p
              class="text-[0.7rem] font-semibold uppercase tracking-[0.05em] text-gray-500"
            >
              By User
            </p>
            <h2 class="my-1 text-xl font-bold text-gray-800">用戶分析</h2>
          </header>
          <table class="mt-3 w-full border-collapse text-sm">
            <thead>
              <tr>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  用戶郵箱
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  成本
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  Tokens
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  呼叫
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  專案數
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in topUsers" :key="user.userId">
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ user.email }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ formatCurrency(user.totalCost) }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ formatTokens(user.inputTokens) }} /
                  {{ formatTokens(user.outputTokens) }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ user.callCount }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ user.projectCount }}
                </td>
              </tr>
            </tbody>
          </table>
          <button
            v-if="allUsers.length > 3"
            class="mt-4 w-full rounded-md border border-gray-300 bg-gray-100 px-4 py-2 text-sm font-semibold text-blue-500 transition hover:border-blue-500 hover:bg-blue-50"
            @click="showUserDetailsModal = true"
          >
            查看詳情 →
          </button>
        </article>

        <article
          class="overflow-x-auto rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
          v-if="topProjects.length"
        >
          <header class="mb-6">
            <p
              class="text-[0.7rem] font-semibold uppercase tracking-[0.05em] text-gray-500"
            >
              By Project
            </p>
            <h2 class="my-1 text-xl font-bold text-gray-800">單一計畫成本</h2>
          </header>
          <table class="mt-3 w-full border-collapse text-sm">
            <thead>
              <tr>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  Project ID
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  成本
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  Tokens
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  呼叫
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="project in topProjects" :key="project.projectId">
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ project.projectId }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ formatCurrency(project.totalCost) }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ formatTokens(project.inputTokens) }} /
                  {{ formatTokens(project.outputTokens) }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ project.callCount }}
                </td>
              </tr>
            </tbody>
          </table>
          <button
            class="mt-4 w-full rounded-md border border-gray-300 bg-gray-100 px-4 py-2 text-sm font-semibold text-blue-500 transition hover:border-blue-500 hover:bg-blue-50"
            @click="showProjectDetailsModal = true"
          >
            查看詳情 →
          </button>
        </article>
      </section>

      <section
        v-if="analytics"
        class="mb-6 grid gap-5 [grid-template-columns:repeat(auto-fit,minmax(320px,1fr))]"
      >
        <article
          class="overflow-x-auto rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
        >
          <header class="mb-6">
            <p
              class="text-[0.7rem] font-semibold uppercase tracking-[0.05em] text-gray-500"
            >
              By Action
            </p>
            <h2 class="my-1 text-xl font-bold text-gray-800">功能成本分佈</h2>
          </header>
          <div
            v-if="!analytics.byAction.length"
            class="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-gray-500"
          >
            無行為記錄。
          </div>
          <div v-else class="mt-3 flex flex-col gap-3">
            <div
              v-for="actionRow in analytics.byAction"
              :key="actionRow.action"
              class="flex items-center justify-between gap-4"
            >
              <div>
                <p class="text-sm font-semibold text-gray-800">
                  {{ actionRow.action }}
                </p>
                <p class="text-xs text-gray-500">
                  {{ actionRow.callCount }} 次
                </p>
              </div>
              <div class="flex-1">
                <span
                  class="block text-right text-[0.8rem] font-medium text-gray-700"
                  >{{ formatCurrency(actionRow.totalCost) }}</span
                >
                <div
                  class="mt-1 h-1.5 w-full overflow-hidden rounded bg-gray-200"
                >
                  <span
                    class="block h-full rounded bg-gradient-to-r from-blue-500 to-cyan-500"
                    :style="{ width: `${actionWidth(actionRow.totalCost)}%` }"
                  ></span>
                </div>
              </div>
            </div>
          </div>
        </article>

        <article
          class="overflow-x-auto rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
        >
          <header class="mb-6">
            <p
              class="text-[0.7rem] font-semibold uppercase tracking-[0.05em] text-gray-500"
            >
              By Model
            </p>
            <h2 class="my-1 text-xl font-bold text-gray-800">模型性價比</h2>
          </header>
          <table
            v-if="modelStats.length"
            class="mt-3 w-full border-collapse text-sm"
          >
            <thead>
              <tr>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  模型
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  成本
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  Tokens
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  呼叫
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  平均成本
                </th>
                <th
                  class="border-b border-gray-200 bg-gray-50 px-2 py-2 text-left text-[0.8rem] font-semibold text-gray-700"
                >
                  佔比
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="model in modelStats" :key="model.modelId">
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ model.modelId }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ formatCurrency(model.totalCost) }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ formatTokens(model.inputTokens) }} /
                  {{ formatTokens(model.outputTokens) }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ model.callCount }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ formatCurrency(model.avgCost) }}
                </td>
                <td class="border-b border-gray-200 px-2 py-2 text-gray-700">
                  {{ model.share.toFixed(1) }}%
                </td>
              </tr>
            </tbody>
          </table>
          <div
            v-else
            class="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-gray-500"
          >
            尚無模型資料
          </div>
        </article>
      </section>

      <p
        v-if="!analytics && !loading"
        class="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-gray-500"
      >
        尚未取得任何使用資料，請先套用篩選。
      </p>

      <div
        v-if="loading"
        class="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-white/75 backdrop-blur-sm"
      >
        <div
          class="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"
        ></div>
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

// 儀表板核心資料與 UI 狀態
const analytics = ref(null);
const loading = ref(false);
const errorMessage = ref("");
const showTrendModal = ref(false);
const showUserDetailsModal = ref(false);
const showProjectDetailsModal = ref(false);
const { error: notifyError, success } = useNotifications();
const { checkIsInternal } = useInternalCheck();

// 預設時間區間快捷選項
const rangePresets = [
  { key: "7d", label: "近 7 天", days: 7 },
  { key: "30d", label: "近 30 天", days: 30 },
  { key: "90d", label: "近 90 天", days: 90 },
];

// 查詢條件（會組成 API 參數）
const filters = reactive({
  preset: "30d",
  startDate: formatDate(shiftDays(new Date(), -29)),
  endDate: formatDate(new Date()),
  userId: "",
  projectId: "",
  modelId: "",
  action: "",
});

// 下拉選單可選項（由後端回傳）
const filterOptions = reactive({
  users: [],
  projects: [],
  models: [],
  actions: [],
});

// 儀表板總覽指標；若尚未載入則回傳預設值避免模板判斷複雜化
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

// 首屏只顯示前 3 名，用於摘要卡片
const topUsers = computed(() => {
  const allUsers = analytics.value?.byUser?.rows || [];
  return allUsers.slice(0, 3);
});

// 詳細 modal 使用完整清單
const allUsers = computed(() => analytics.value?.byUser?.rows || []);

// 首屏只顯示前 3 個專案
const topProjects = computed(() => {
  const allProjects = analytics.value?.byProject?.rows || [];
  return allProjects.slice(0, 3);
});

// 專案詳細 modal 使用完整清單
const allProjects = computed(() => analytics.value?.byProject?.rows || []);

// 計算模型成本佔比，作為模型性價比表格欄位
const modelStats = computed(() => {
  const models = analytics.value?.byModel || [];
  const total =
    overview.value.rangeCost ||
    models.reduce((acc, row) => acc + (row.totalCost || 0), 0);
  if (!models.length || total === 0) {
    return [];
  }
  return models.map((row) => ({
    ...row,
    share: row.totalCost ? (row.totalCost / total) * 100 : 0,
  }));
});

// 將趨勢資料轉為 SVG polyline 座標
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

// 供摘要顯示「區間最大單日成本」
const trendMaxCost = computed(() => {
  const trend = analytics.value?.trend || [];
  if (!trend.length) return 0;
  return Math.max(...trend.map((p) => p.cost));
});

// 供圖表底部顯示趨勢實際日期範圍
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

// 右上角顯示目前套用日期區間
const rangeSummary = computed(
  () => `${filters.startDate} → ${filters.endDate}`,
);

// 將成本格式化為易讀金額
function formatCurrency(value) {
  const number = Number(value || 0);
  if (number >= 1) {
    return `$${number.toFixed(2)}`;
  }
  if (number === 0) return "$0";
  return `$${number.toExponential(2)}`;
}

// 將 token 數量轉成 K/M 顯示
function formatTokens(value) {
  const numeric = Number(value || 0);
  if (numeric >= 1_000_000) return `${(numeric / 1_000_000).toFixed(1)}M`;
  if (numeric >= 1_000) return `${(numeric / 1_000).toFixed(1)}K`;
  return numeric.toLocaleString();
}

// 日期格式統一為 yyyy-mm-dd，對齊 input[type=date]
function formatDate(dateInput) {
  const d = new Date(dateInput);
  return d.toISOString().slice(0, 10);
}

// 儀表板顯示使用的完整日期時間格式
function formatDateTime(isoString) {
  const d = new Date(isoString);
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`;
}

// 日期平移工具：根據 offset 取得相對日期
function shiftDays(base, offset) {
  const clone = new Date(base);
  clone.setDate(clone.getDate() + offset);
  return clone;
}

// Action 長條圖寬度比例（以當前查詢內最大成本為 100%）
function actionWidth(cost) {
  const rows = analytics.value?.byAction || [];
  if (!rows.length) return 0;
  const max = Math.max(...rows.map((row) => row.totalCost || 0), 0.0001);
  return Math.min(100, (cost / max) * 100);
}

// 手動調整日期時，切換為自訂區間模式
function onCustomRange() {
  filters.preset = "custom";
}

// 點選快捷範圍後同步更新起訖日期
function setPreset(key) {
  const preset = rangePresets.find((item) => item.key === key);
  if (!preset) return;
  filters.preset = key;
  filters.endDate = formatDate(new Date());
  filters.startDate = formatDate(shiftDays(new Date(), -(preset.days - 1)));
}

// 重置所有篩選，並立即重新查詢
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

// 防呆：確保開始日不晚於結束日
function validateRange() {
  if (!filters.startDate || !filters.endDate) {
    return false;
  }
  return new Date(filters.startDate) <= new Date(filters.endDate);
}

// 主查詢函式：依 filters 取得分析資料並更新選單來源
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

// 先驗證日期再查詢，避免送出無效請求
async function applyFilters() {
  if (!validateRange()) {
    const msg = "請確認開始日期早於結束日期";
    errorMessage.value = msg;
    notifyError(msg);
    return;
  }
  await fetchAnalytics(false);
}

// 手動刷新時顯示成功提示
const refresh = () => fetchAnalytics(true);

// 僅允許內部帳號進入；初次掛載即載入資料
onMounted(async () => {
  const isInternal = await checkIsInternal();
  if (!isInternal) {
    window.location.href = "/";
    return;
  }
  await fetchAnalytics();
});
</script>
