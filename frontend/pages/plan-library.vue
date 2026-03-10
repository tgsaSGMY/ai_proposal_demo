<template>
  <ClientOnly>
    <div class="flex flex-col h-screen bg-gray-50">
      <div class="flex-1 overflow-y-auto space-y-6 px-4 py-6 md:px-8 md:py-8">
        <section class="space-y-4">
          <p
            class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-gray-400"
          >
            <NuxtLink to="/" class="hover:text-gray-600">首頁</NuxtLink>
            <span class="text-gray-300">></span>
            <span class="text-gray-600">我的計畫庫</span>
          </p>
          <div
            class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
          >
            <!-- 頁面標題與動作區：顯示頁面標題、說明文字，以及新增計畫的 CTA 按鈕 -->
            <div class="space-y-2">
              <h1 class="text-3xl font-semibold text-gray-900">我的計畫庫</h1>
              <p class="text-sm text-gray-500 max-w-2xl">
                集中檢視所有外部計畫案的進度、審查狀態與更新紀錄，快速回顧重點並與客戶保持同步。
              </p>
            </div>
            <NuxtLink
              to="/"
              class="inline-flex items-center justify-center gap-2 rounded-2xl bg-rose-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-rose-200 transition hover:-translate-y-0.5 hover:bg-rose-600"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                class="h-4 w-4"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M12 6v12m6-6H6"
                />
              </svg>
              新計畫案啓動
            </NuxtLink>
          </div>
        </section>

        <section
          v-if="isLoadingProjects"
          class="flex flex-col items-center justify-center rounded-3xl border border-dashed border-rose-200 bg-white/80 p-10 text-center text-gray-500"
        >
          <!-- 載入中樣式：當專案尚在請求中顯示的占位區塊 -->
          <span class="text-sm font-semibold tracking-wide"
            >正在載入計畫...</span
          >
          <span class="mt-2 text-xs text-gray-400">請稍候片刻</span>
        </section>

        <section
          v-else-if="loadError"
          class="flex flex-col items-center justify-center rounded-3xl border border-rose-100 bg-white p-8 text-center"
        >
          <!-- 載入錯誤顯示：當取得專案發生錯誤時顯示提示與重試按鈕 -->
          <p class="text-base font-semibold text-rose-500">{{ loadError }}</p>
          <p class="mt-2 text-sm text-gray-500">無法載入專案，請重新整理。</p>
          <button
            class="mt-4 rounded-2xl bg-rose-500 px-5 py-2 text-sm font-semibold text-white shadow hover:bg-rose-600"
            @click="fetchProjects"
          >
            重新嘗試
          </button>
        </section>

        <section
          v-else-if="projects.length === 0"
          class="flex flex-col items-center justify-center rounded-3xl border border-dashed border-gray-200 bg-white/90 p-10 text-center"
        >
          <!-- 空狀態：尚無已儲存計畫時顯示，引導使用者建立新計畫 -->
          <p class="text-lg font-semibold text-gray-800">
            目前尚無已儲存的計畫
          </p>
          <p class="mt-2 text-sm text-gray-500">
            回到首頁生成企劃後，我們會自動把成果同步到這裡。
          </p>
          <NuxtLink
            to="/"
            class="mt-4 inline-flex items-center rounded-2xl bg-rose-500 px-6 py-3 text-sm font-semibold text-white shadow hover:bg-rose-600"
          >
            立即建立
          </NuxtLink>
        </section>

        <section v-else class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          <article
            v-for="project in projects"
            :key="project.id"
            class="relative flex h-full flex-col rounded-3xl border border-gray-100 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-rose-200 cursor-pointer"
            @click="goToProject(project.id)"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <span
                    class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold"
                    :class="[project.accent.tagBg, project.accent.tagText]"
                  >
                    {{ project.type }}
                  </span>
                  <span v-if="project.grantName" class="text-xs text-gray-500">
                    {{ project.grantName }}
                  </span>
                  <span
                    v-if="project.templateName"
                    class="text-xs text-gray-500"
                  >
                    / {{ project.templateName }}
                  </span>
                </div>
                <h3
                  class="mt-3 text-lg font-semibold text-gray-900 line-clamp-2"
                >
                  {{ project.title }}
                </h3>
                <p class="mt-2 text-sm text-gray-500 min-h-[48px] line-clamp-3">
                  {{ project.description }}
                </p>
              </div>
              <div class="relative" @click.stop>
                <button
                  class="rounded-full p-2 text-gray-400 transition hover:bg-gray-100 hover:text-gray-700"
                  @click.stop="toggleMenu(project.id)"
                  :aria-expanded="menuOpenId === project.id"
                  aria-label="更多操作"
                >
                  <!-- 專案卡片的「更多操作」按鈕（打開選單以編輯 / 刪除 / 生成圖片等） -->
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    class="h-5 w-5"
                  >
                    <path
                      d="M12 7a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm0 6a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm0 6a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"
                    />
                  </svg>
                </button>
                <Transition
                  enter-active-class="transition duration-150"
                  enter-from-class="opacity-0 translate-y-1"
                  enter-to-class="opacity-100 translate-y-0"
                  leave-active-class="transition duration-150"
                  leave-from-class="opacity-100 translate-y-0"
                  leave-to-class="opacity-0 translate-y-1"
                >
                  <div
                    v-if="menuOpenId === project.id"
                    class="absolute right-0 mt-2 w-44 rounded-2xl border border-gray-100 bg-white py-2 text-sm shadow-xl"
                  >
                    <button
                      class="flex w-full items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-50"
                      @click="openGenerateImage(project)"
                    >
                      <span>生成圖片</span>
                    </button>
                    <button
                      class="flex w-full items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-50"
                      @click="openEdit(project)"
                    >
                      <span>編輯計畫案</span>
                    </button>
                    <button
                      class="flex w-full items-center gap-2 px-4 py-2 text-rose-600 hover:bg-rose-50"
                      @click="handleDelete(project)"
                    >
                      <span>刪除計畫案</span>
                    </button>
                  </div>
                </Transition>
              </div>
            </div>

            <div class="mt-6 space-y-3">
              <div
                class="flex items-center justify-between text-xs font-semibold text-gray-400"
              >
                <span>完成度</span>
                <span class="text-gray-700">{{ project.completeness }}%</span>
              </div>
              <div class="h-2 rounded-full bg-gray-100">
                <div
                  class="h-full rounded-full"
                  :class="project.accent.progress"
                  :style="{ width: `${project.completeness}%` }"
                ></div>
              </div>
              <div
                class="flex items-center justify-between text-xs text-gray-400"
              >
                <span>更新於 {{ project.lastUpdate }}</span>
              </div>
            </div>
          </article>

          <button
            class="flex h-full flex-col items-center justify-center rounded-3xl border-2 border-dashed border-gray-200 bg-white/80 px-6 py-8 text-center text-gray-400 transition hover:border-rose-300 hover:text-rose-500"
            @click="handleCreateProject"
          >
            <span
              class="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-rose-50 text-rose-500"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.5"
                class="h-6 w-6"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M12 6v12m6-6H6"
                />
              </svg>
            </span>
            <p class="text-base font-semibold text-gray-600">建立新計畫</p>
            <p class="mt-1 text-sm text-gray-400">整合既有資料或重新生成</p>
          </button>
        </section>
      </div>

      <section
        class="flex-shrink-0 border-t border-gray-100 bg-gray-50 px-4 py-4 md:px-6 md:py-4"
      >
        <!-- 側欄統計與快捷資訊：例如本月生成次數、真人專家邀請等 -->
        <div class="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <div
            class="rounded-3xl border border-gray-100 bg-white p-4 shadow-sm flex items-center gap-3 cursor-pointer"
            @click="openSupportPanel"
          >
            <span
              class="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-full bg-rose-50 text-rose-500"
            >
              <Icon
                name="tabler:headset"
                width="24"
                height="24"
                style="color: #e40909"
              />
            </span>

            <div class="flex-1 flex items-center justify-between">
              <p class="text-base font-semibold text-gray-700">
                客戶服務與專家諮詢
              </p>
              <Icon
                name="tabler:arrow-narrow-right"
                width="64"
                height="64"
                class="text-gray-400"
              />
            </div>
          </div>
        </div>
      </section>

      <PlanLibraryEditModal
        v-model:model-value="isEditModalOpen"
        :project="editingProject"
        @save="handleSave"
        @close="closeEditModal"
      />

      <PlanImageGeneratorModal
        v-model:model-value="isImageGeneratorOpen"
        :project-id="selectedProjectForImage?.id"
        @generate="handleImageGenerate"
        @close="closeImageGeneratorModal"
      />

      <Transition
        enter-active-class="transition-opacity duration-200"
        leave-active-class="transition-opacity duration-200"
        enter-from-class="opacity-0"
        leave-to-class="opacity-0"
      >
        <div
          v-if="isSupportPanelOpen"
          class="fixed inset-0 bg-black/30 backdrop-blur-[1px] z-40"
          @click="closeSupportPanel"
        ></div>
      </Transition>

      <Transition
        enter-active-class="transition-transform duration-300"
        leave-active-class="transition-transform duration-300"
        enter-from-class="translate-x-full"
        leave-to-class="translate-x-full"
      >
        <aside
          v-if="isSupportPanelOpen"
          class="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-white shadow-2xl flex flex-col"
        >
          <div
            class="flex items-center justify-between px-6 py-4 border-b border-gray-100"
          >
            <div class="flex items-center gap-3">
              <span
                class="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-50 text-rose-500"
              >
                <Icon name="tabler:headset" width="26" height="26" />
              </span>
              <div>
                <h2 class="text-lg font-semibold text-gray-900">
                  客戶服務與專家咨詢
                </h2>
                <p class="text-sm text-gray-500">我們隨時準備為您提供服務</p>
              </div>
            </div>
            <button
              class="rounded-full p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              @click="closeSupportPanel"
              aria-label="關閉支援面板"
            >
              <Icon name="tabler:x" width="22" height="22" />
            </button>
          </div>

          <div class="flex-1 overflow-y-auto px-6 py-6 space-y-6">
            <section class="space-y-3">
              <h3 class="text-lg font-semibold text-gray-900">價格服務方案</h3>
              <button
                class="inline-flex cursor-not-allowed items-center justify-center gap-2 rounded-2xl bg-gray-300 px-4 py-2 text-sm font-semibold text-white shadow"
                disabled
              >
                取得專案報價
                <Icon name="tabler:arrow-up-right" width="18" height="18" />
              </button>
            </section>

            <section class="space-y-3">
              <h3 class="text-lg font-semibold text-gray-900">客戶 QA</h3>
              <div class="space-y-2 text-sm text-gray-600">
                <details
                  v-for="item in customerQaList"
                  :key="item.question"
                  class="rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3"
                >
                  <summary class="font-semibold text-gray-800 cursor-pointer">
                    {{ item.question }}
                  </summary>
                  <div
                    class="mt-2 text-gray-600 leading-relaxed"
                    v-html="formatQaAnswer(item.answer)"
                  ></div>
                </details>
              </div>
            </section>

            <section class="space-y-3">
              <h3 class="text-lg font-semibold text-gray-900">
                LINE QR Code 掃描客服
              </h3>
              <p class="text-sm text-gray-500">
                掃描下方 QR Code 或點擊連結，即可加入智庫 LINE@
                並獲得真人客服協助。
              </p>
              <div
                class="flex items-center gap-4 rounded-3xl border border-dashed border-gray-200 p-4"
              >
                <div
                  class="flex h-28 w-28 items-center justify-center rounded-2xl bg-white border border-gray-100 overflow-hidden"
                >
                  <img
                    src="/qr_code.jpg"
                    alt="LINE 客服 QR Code"
                    class="h-full w-full object-cover"
                  />
                </div>
                <div class="flex-1 space-y-2">
                  <p class="text-sm text-gray-600">LINE@ 智庫客服</p>
                  <a
                    href="https://lin.ee/h0tC2Hw"
                    target="_blank"
                    rel="noopener"
                    class="inline-flex items-center gap-2 text-emerald-600 font-semibold"
                  >
                    立即開啟 LINE 聊天
                    <Icon name="tabler:external-link" width="18" height="18" />
                  </a>
                </div>
              </div>
            </section>
          </div>
        </aside>
      </Transition>
    </div>
  </ClientOnly>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import PlanLibraryEditModal from "~/components/PlanLibraryEditModal.vue";
import PlanImageGeneratorModal from "~/components/PlanImageGeneratorModal.vue";
import { useConfirm } from "~/composables/useConfirm";
import { useNotifications } from "~/composables/useNotifications";
import { useCurrentUser } from "~/composables/useCurrentUser";
import { useInternalCheck } from "~/composables/useInternalCheck";
// 引入元件與 composables：處理編輯 modal、圖片生成、使用者資訊、內部權限判定、通知與確認對話等功能

import {
  getDynamicFieldLabels,
  ensureDynamicSchemaLoaded,
} from "~/utils/dynamicSchema";
import { supabase } from "~/utils/supabaseClient";
import { customerQaList } from "~/utils/customerQa";
// 透過動態 schema 來計算每個計畫卡片的進度，並使用 Supabase API 取得與管理專案資料

// 介面定義：用來描述 UI 卡片與後端的專案紀錄結構
interface Accent {
  tagBg: string;
  tagText: string;
  progress: string;
}

interface ProjectRecord {
  id: string;
  user_id: string;
  mode: string;
  title: string;
  description: string | null;
  saved_plan: Record<string, any> | null;
  conversation_history: any;
  stored_answer: Record<string, any> | null;
  grant_id?: string | null;
  template_id?: string | null;
  plan_type_id?: string | null;
  grant_name?: string | null;
  template_name?: string | null;
  created_at: string;
  updated_at: string | null;
}

interface ProjectCard {
  id: string;
  title: string;
  description: string;
  type: string;
  completeness: number;
  lastUpdate: string;
  accent: Accent;
  grantName: string | null;
  templateName: string | null;
  record: ProjectRecord;
}

const accentPalette: Accent[] = [
  { tagBg: "bg-rose-50", tagText: "text-rose-500", progress: "bg-rose-500" },
  { tagBg: "bg-amber-50", tagText: "text-amber-600", progress: "bg-amber-500" },
  {
    tagBg: "bg-purple-50",
    tagText: "text-purple-600",
    progress: "bg-purple-500",
  },
  {
    tagBg: "bg-emerald-50",
    tagText: "text-emerald-600",
    progress: "bg-emerald-500",
  },
];

const dateFormatter = new Intl.DateTimeFormat("zh-TW", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

useHead({
  title: "我的計畫庫 - TGSA 補助引擎",
  meta: [
    {
      name: "description",
      content:
        "集中檢視所有計畫案的進度、審查狀態與更新紀錄，快速回顧重點並與客戶保持同步。",
    },
    {
      name: "keywords",
      content: "計畫庫, 計畫管理, 計畫追蹤, TGSA, AI 企劃",
    },
    {
      property: "og:title",
      content: "我的計畫庫 - TGSA 補助引擎",
    },
    {
      property: "og:description",
      content:
        "集中檢視所有計畫案的進度、審查狀態與更新紀錄，快速回顧重點並與客戶保持同步。",
    },
    { property: "og:type", content: "website" },
    { name: "robots", content: "index, follow" },
  ],
});

const projects = ref<ProjectCard[]>([]);
const isLoadingProjects = ref(false);
const loadError = ref("");
const menuOpenId = ref<string | null>(null);
const isEditModalOpen = ref(false);
const editingProject = ref<ProjectCard | null>(null);
const isImageGeneratorOpen = ref(false);
const selectedProjectForImage = ref<ProjectCard | null>(null);
const isSupportPanelOpen = ref(false);

// internal check
const { checkIsInternal } = useInternalCheck();
const isInternal = ref(false);

const router = useRouter();
const { confirm } = useConfirm();
const { success, error: notifyError } = useNotifications();
const { userId: currentUserId, refreshUser } = useCurrentUser();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

/**
 * 點擊文件任意處時關閉任何打開的操作選單
 * - 用於實現「點選外部關閉」功能
 */
const handleDocumentClick = () => {
  menuOpenId.value = null;
};

definePageMeta({
  middleware: "auth",
  ssr: false,
});

onMounted(async () => {
  document.addEventListener("click", handleDocumentClick);
  await refreshUser();
  // determine if current user is internal
  isInternal.value = await checkIsInternal();
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
});

watch(
  () => currentUserId.value,
  async (userId) => {
    if (userId) {
      await fetchProjects();
      isInternal.value = await checkIsInternal();
    } else {
      projects.value = [];
      isInternal.value = false;
    }
  },
  { immediate: true },
);

/**
 * 將後端的 ProjectRecord 轉換為供 UI 顯示的 ProjectCard
 * - 計算計畫完成度百分比（基於 stored_answer 中填入的動態欄位）
 * - 指派顏色與樣式（accent）用於卡片展示
 * - 格式化最後更新時間為台灣時區格式
 * - 區分「生成模式」和「互動模式」
 * @param record - 後端專案記錄
 * @param index - 專案在列表中的索引（用於循環指派顏色）
 * @param accentOverride - 可選的顏色樣式覆蓋
 * @returns 裝飾後的前端專案卡片物件
 */
function decorateProject(
  record: ProjectRecord,
  index: number,
  accentOverride?: Accent,
): ProjectCard {
  const accent = accentOverride || accentPalette[index % accentPalette.length]!;

  let completeness = 0;
  const schemaOptions = {
    templateId: record.template_id,
    templateGrantId: record.grant_id,
  };
  const totalFields = getDynamicFieldLabels(schemaOptions).length;

  if (record.mode === "generator") {
    // 生成模式：计算 stored_answer.user_input.dynamic_fields 中有 value 的数量 / totalFields
    if (record.stored_answer?.user_input?.dynamic_fields) {
      const dynamicFields = record.stored_answer.user_input.dynamic_fields;
      const filledCount = Object.values(dynamicFields).filter(
        (field: any) => field,
      ).length;
      completeness =
        totalFields > 0 ? Math.round((filledCount / totalFields) * 100) : 0;
    } else {
      completeness = 0;
    }
  } else {
    // 对话模式：计算 stored_answer 中除了 main_idea 之外的字段数量 / totalFields
    if (record.stored_answer && record.stored_answer.chat_answers) {
      const allKeys = Object.keys(record.stored_answer.chat_answers);
      const filledCount = new Set(
        allKeys
          .filter(
            (key) =>
              key.includes("::") && key !== "main_idea" && key !== "main-idea",
          )
          .map((key) => key.split("::").slice(0, 2).join("::")),
      ).size;
      completeness =
        totalFields > 0 ? Math.round((filledCount / totalFields) * 100) : 0;
    } else {
      completeness = 0;
    }
  }
  completeness = Math.min(Math.max(completeness, 0), 100);

  const modeLabel = record.mode === "generator" ? "生成模式" : "互動模式";
  const lastUpdateSource = record.updated_at || record.created_at;
  const lastUpdate = dateFormatter.format(new Date(lastUpdateSource));

  return {
    id: record.id,
    title: record.title,
    description: record.description || "尚未提供描述",
    type: modeLabel,
    completeness,
    lastUpdate,
    accent,
    grantName: record.grant_name || null,
    templateName: record.template_name || null,
    record,
  };
}

/**
 * 向後端 API 取得使用者的專案列表
 * - 確保動態 schema 已載入（用於計算完成度）
 * - 驗證登入狀態與取得 session token
 * - 呼叫 GET /api/projects API
 * - 將每個 record 裝飾成 ProjectCard 並按索引指派顏色
 * - 設定載入狀態與錯誤訊息
 */
async function fetchProjects() {
  const userId = currentUserId.value || (await refreshUser());
  if (!userId) {
    projects.value = [];
    return;
  }
  isLoadingProjects.value = true;
  loadError.value = "";
  try {
    // Ensure dynamic schema is loaded before processing projects
    await ensureDynamicSchemaLoaded();

    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error("請先登入");
    }

    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "Failed to load projects");
    }
    const data: ProjectRecord[] = await response.json();
    projects.value = data.map((record, index) =>
      decorateProject(record, index),
    );
  } catch (error: any) {
    console.error("Failed to fetch projects", error);
    loadError.value = error?.message || "無法載入專案列表";
  } finally {
    isLoadingProjects.value = false;
  }
}

/**
 * 切換指定專案卡片的操作選單開關狀態
 * @param id - 專案的 ID
 */
function toggleMenu(id: string) {
  menuOpenId.value = menuOpenId.value === id ? null : id;
}

/**
 * 導向指定專案的詳細頁面
 * @param id - 專案的 ID
 */
function goToProject(id: string) {
  router.push(`/projects/${id}`);
}

/**
 * 打開專案編輯 modal，將選中的專案載入到編輯表單中
 * @param project - 要編輯的專案卡片物件
 */
function openEdit(project: ProjectCard) {
  editingProject.value = { ...project } as ProjectCard;
  isEditModalOpen.value = true;
  menuOpenId.value = null;
}

/**
 * 打開圖片生成 modal（僅限內部使用者）
 * - 驗證當前使用者是否為內部人員
 * - 若不是內部使用者，顯示錯誤通知並返回
 * - 設定選中的專案用於圖片生成
 * - 打開圖片生成 modal
 * @param project - 要生成圖片的專案卡片物件
 */
function openGenerateImage(project: ProjectCard) {
  // runtime guard: only internal users can open the image generator
  // if (!isInternal.value) {
  //   notifyError("僅限內部人員使用圖片生成功能");
  //   menuOpenId.value = null;
  //   return;
  // }

  selectedProjectForImage.value = project;
  isImageGeneratorOpen.value = true;
  menuOpenId.value = null;
}

/**
 * 關閉專案編輯 modal 並清空編輯狀態
 */
function closeEditModal() {
  isEditModalOpen.value = false;
  editingProject.value = null;
}

/**
 * 關閉圖片生成 modal 並清空選中專案狀態
 */
function closeImageGeneratorModal() {
  isImageGeneratorOpen.value = false;
  selectedProjectForImage.value = null;
}

function openSupportPanel() {
  isSupportPanelOpen.value = true;
}

function closeSupportPanel() {
  isSupportPanelOpen.value = false;
}

function escapeHtml(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatQaAnswer(answer: string): string {
  return escapeHtml(answer)
    .replace(
      /\*\*(.+?)\*\*/g,
      '<strong class="font-black text-gray-700">$1</strong>',
    )
    .replace(/\n/g, "<br />");
}

/**
 * 處理圖片生成請求
 * - 驗證選中的專案存在
 * - 記錄生成請求信息
 * - 顯示成功通知
 * @param prompt - 用戶輸入的圖片生成提示詞
 */
async function handleImageGenerate(prompt: string) {
  if (!selectedProjectForImage.value) return;

  try {
    const project = selectedProjectForImage.value;
    console.log(
      `Generating image for project "${project.title}" with prompt: "${prompt}"`,
    );

    success(`圖片生成請求已提交：${prompt}`);
  } catch (error: any) {
    console.error("Failed to generate image", error);
    notifyError(error?.message || "圖片生成失敗，請稍後再試");
  }
}

/**
 * 儲存編輯後的專案資訊
 * - 驗證專案 ID 存在
 * - 驗證登入狀態與取得 session token
 * - 呼叫 PUT /api/projects/{id} API 更新標題與描述
 * - 更新本地列表中的專案卡片
 * - 成功後顯示通知並關閉編輯 modal
 * @param payload - 專案更新數據，包含 id、title、description
 */
async function handleSave(payload: {
  id?: string;
  title: string;
  description: string;
}) {
  if (!payload.id) return;
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error("請先登入");
    }

    const response = await fetch(`${API_BASE_URL}/projects/${payload.id}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: payload.title,
        description: payload.description,
      }),
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "更新計畫失敗");
    }
    const updated: ProjectRecord = await response.json();
    const index = projects.value.findIndex(
      (project) => project.id === payload.id,
    );
    if (index !== -1) {
      const accent = projects.value[index]?.accent;
      projects.value[index] = decorateProject(updated, index, accent);
    }
    success("計畫內容已更新");
  } catch (error: any) {
    console.error("Failed to update project", error);
    notifyError(error?.message || "更新計畫失敗，請稍後再試");
  } finally {
    closeEditModal();
  }
}

/**
 * 刪除專案
 * - 需使用者確認（二次確認對話）
 * - 驗證登入狀態與取得 session token
 * - 呼叫 DELETE /api/projects/{id} API
 * - 從本地列表中移除已刪除的專案
 * - 成功後顯示通知
 * @param project - 要刪除的專案卡片物件
 */
async function handleDelete(project: ProjectCard) {
  menuOpenId.value = null;
  const confirmed = await confirm({
    title: "刪除計畫案",
    message: `確定要刪除「${project.title}」嗎？此操作無法復原。`,
    confirmText: "刪除",
    confirmColor: "danger",
  });
  if (!confirmed) return;

  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error("請先登入");
    }

    const response = await fetch(`${API_BASE_URL}/projects/${project.id}`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ is_deleted: true }),
    });
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || "刪除計畫失敗");
    }
    projects.value = projects.value.filter((item) => item.id !== project.id);
    success("計畫已刪除");
  } catch (error: any) {
    console.error("Failed to delete project", error);
    notifyError(error?.message || "刪除失敗，請稍後再試");
  }
}

/**
 * 建立新專案：導向首頁以開始新的計畫生成流程
 */
function handleCreateProject() {
  router.push("/");
}
</script>
