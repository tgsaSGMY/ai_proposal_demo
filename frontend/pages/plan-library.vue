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
          <span class="text-sm font-semibold tracking-wide"
            >正在載入計畫...</span
          >
          <span class="mt-2 text-xs text-gray-400">請稍候片刻</span>
        </section>

        <section
          v-else-if="loadError"
          class="flex flex-col items-center justify-center rounded-3xl border border-rose-100 bg-white p-8 text-center"
        >
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
                <span
                  class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold"
                  :class="[project.accent.tagBg, project.accent.tagText]"
                >
                  {{ project.type }}
                </span>
                <h3 class="mt-3 text-lg font-semibold text-gray-900">
                  {{ project.title }}
                </h3>
                <p class="mt-2 text-sm text-gray-500 min-h-[48px]">
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
                      v-if="isInternal"
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
        <div class="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <div
            class="rounded-3xl border border-gray-100 bg-white p-4 shadow-sm flex items-start gap-3"
          >
            <span
              class="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-full bg-rose-50 text-rose-500"
            >
              <Icon
                name="tabler:circle"
                width="24"
                height="24"
                style="color: #e40909"
              />
            </span>

            <div class="flex-1">
              <p
                class="text-xs font-semibold uppercase tracking-wide text-gray-400"
              >
                本月 AI 生成次數
              </p>
              <div class="mt-1 flex items-end gap-2">
                <span class="text-xl font-semibold text-gray-900"
                  >暫不計算</span
                >
              </div>
            </div>
          </div>
          <div
            class="rounded-3xl border border-gray-100 bg-red-500 text-white p-4 shadow-sm flex items-start gap-3"
          >
            <span
              class="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-full bg-white/20 text-white"
            >
              <Icon
                name="mdi:people-add"
                width="24"
                height="24"
                style="color: #fff"
              />
            </span>
            <div class="flex-1">
              <p
                class="text-xs font-semibold uppercase tracking-wide text-white"
              >
                需要專業協助？
              </p>
              <div class="mt-1 flex items-end gap-2">
                <span class="text-xl font-semibold text-white"
                  >真人專家邀請</span
                >
              </div>
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
        v-if="isInternal"
        v-model:model-value="isImageGeneratorOpen"
        :project-id="selectedProjectForImage?.id"
        @generate="handleImageGenerate"
        @close="closeImageGeneratorModal"
      />
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
import { supabase } from "~/utils/supabaseClient";

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
  plan_metadata?: Record<string, any> | null;
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

const projects = ref<ProjectCard[]>([]);
const isLoadingProjects = ref(false);
const loadError = ref("");
const menuOpenId = ref<string | null>(null);
const isEditModalOpen = ref(false);
const editingProject = ref<ProjectCard | null>(null);
const isImageGeneratorOpen = ref(false);
const selectedProjectForImage = ref<ProjectCard | null>(null);

// internal check
const { checkIsInternal } = useInternalCheck();
const isInternal = ref(false);

const router = useRouter();
const { confirm } = useConfirm();
const { success, error: notifyError } = useNotifications();
const { userId: currentUserId, refreshUser } = useCurrentUser();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const handleDocumentClick = () => {
  menuOpenId.value = null;
};

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
  { immediate: true }
);

function decorateProject(
  record: ProjectRecord,
  index: number,
  accentOverride?: Accent
): ProjectCard {
  const accent = accentOverride || accentPalette[index % accentPalette.length]!;

  let completeness = 0;

  if (record.mode === "generator") {
    // 生成模式：计算 stored_answer.user_input.dynamic_fields 中有 value 的数量 / 24
    if (record.stored_answer?.user_input?.dynamic_fields) {
      const dynamicFields = record.stored_answer.user_input.dynamic_fields;
      const filledCount = Object.values(dynamicFields).filter(
        (field: any) => field
      ).length;
      completeness = Math.round((filledCount / 16) * 100);
    } else {
      completeness = 0;
    }
  } else {
    // 对话模式：计算 stored_answer 中除了 main_idea 之外的字段数量 / 24
    if (record.stored_answer && record.stored_answer.chat_answers) {
      const allKeys = Object.keys(record.stored_answer.chat_answers);
      const filledCount = new Set(
        allKeys
          .filter(
            (key) =>
              key.includes("::") && key !== "main_idea" && key !== "main-idea"
          )
          .map((key) => key.split("::").slice(0, 2).join("::"))
      ).size;
      completeness = Math.round((filledCount / 16) * 100);
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
    record,
  };
}

async function fetchProjects() {
  const userId = currentUserId.value || (await refreshUser());
  if (!userId) {
    projects.value = [];
    return;
  }
  isLoadingProjects.value = true;
  loadError.value = "";
  try {
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
      decorateProject(record, index)
    );
  } catch (error: any) {
    console.error("Failed to fetch projects", error);
    loadError.value = error?.message || "無法載入專案列表";
  } finally {
    isLoadingProjects.value = false;
  }
}

function toggleMenu(id: string) {
  menuOpenId.value = menuOpenId.value === id ? null : id;
}

function goToProject(id: string) {
  router.push(`/projects/${id}`);
}

function openEdit(project: ProjectCard) {
  editingProject.value = { ...project } as ProjectCard;
  isEditModalOpen.value = true;
  menuOpenId.value = null;
}

function openGenerateImage(project: ProjectCard) {
  // runtime guard: only internal users can open the image generator
  if (!isInternal.value) {
    notifyError("僅限內部人員使用圖片生成功能");
    menuOpenId.value = null;
    return;
  }

  selectedProjectForImage.value = project;
  isImageGeneratorOpen.value = true;
  menuOpenId.value = null;
}

function closeEditModal() {
  isEditModalOpen.value = false;
  editingProject.value = null;
}

function closeImageGeneratorModal() {
  isImageGeneratorOpen.value = false;
  selectedProjectForImage.value = null;
}

async function handleImageGenerate(prompt: string) {
  if (!selectedProjectForImage.value) return;

  try {
    const project = selectedProjectForImage.value;
    console.log(
      `Generating image for project "${project.title}" with prompt: "${prompt}"`
    );

    success(`圖片生成請求已提交：${prompt}`);
  } catch (error: any) {
    console.error("Failed to generate image", error);
    notifyError(error?.message || "圖片生成失敗，請稍後再試");
  }
}

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
      (project) => project.id === payload.id
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
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
    });
    if (!response.ok && response.status !== 204) {
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

function handleCreateProject() {
  router.push("/");
}
</script>
