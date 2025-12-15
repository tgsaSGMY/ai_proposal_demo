<template>
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

      <section class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="project in projects"
          :key="project.id"
          class="relative flex h-full flex-col rounded-3xl border border-gray-100 bg-white p-5 shadow-sm"
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
              <span class="text-xl font-semibold text-gray-900">1,204 次</span>
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
            <p class="text-xs font-semibold uppercase tracking-wide text-white">
              需要專業協助？
            </p>
            <div class="mt-1 flex items-end gap-2">
              <span class="text-xl font-semibold text-white">真人專家邀請</span>
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
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import PlanLibraryEditModal from "~/components/PlanLibraryEditModal.vue";
import { useConfirm } from "~/composables/useConfirm";
import { useNotifications } from "~/composables/useNotifications";

interface ProjectCard {
  id: string;
  title: string;
  description: string;
  type: string;
  completeness: number;
  lastUpdate: string;
  accent: {
    tagBg: string;
    tagText: string;
    progress: string;
  };
}

const dateFormatter = new Intl.DateTimeFormat("zh-TW", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

const projects = ref<ProjectCard[]>([
  {
    id: "plan-1",
    title: "智慧零售數據樞紐平台",
    description:
      "建立跨品牌資料整合合作，運用 AI 預測客群與供應鏈管理貫穿門市運作。",
    type: "SBIR 審查中",
    completeness: 85,
    lastUpdate: "2024/09/05",
    accent: {
      tagBg: "bg-rose-50",
      tagText: "text-rose-500",
      progress: "bg-rose-500",
    },
  },
  {
    id: "plan-2",
    title: "高效碳排監測應用模組",
    description:
      "提升製造業 4.0 數據整合之即時判讀，結合區塊鏈技術確保 ESG 稽核。",
    type: "SBIR 執行中",
    completeness: 42,
    lastUpdate: "2024/05/18",
    accent: {
      tagBg: "bg-amber-50",
      tagText: "text-amber-600",
      progress: "bg-amber-500",
    },
  },
  {
    id: "plan-3",
    title: "城市共享空間協同平台",
    description:
      "規劃跨部門協力的場域資料整合平台，結合數據視覺化提升閒置空間利用率。",
    type: "SIT 執行編號",
    completeness: 63,
    lastUpdate: "2024/06/10",
    accent: {
      tagBg: "bg-purple-50",
      tagText: "text-purple-600",
      progress: "bg-purple-500",
    },
  },
  {
    id: "plan-4",
    title: "環保材料食品包裝設計",
    description: "導入可分解材質與無毒色料之包裝設計，提升產品保存與回收效率。",
    type: "CITD 品項驗收",
    completeness: 18,
    lastUpdate: "2024/04/22",
    accent: {
      tagBg: "bg-emerald-50",
      tagText: "text-emerald-600",
      progress: "bg-emerald-500",
    },
  },
]);

const menuOpenId = ref<string | null>(null);
const isEditModalOpen = ref(false);
const editingProject = ref<ProjectCard | null>(null);

const { confirm } = useConfirm();
const { success, info } = useNotifications();

const handleDocumentClick = () => {
  menuOpenId.value = null;
};

onMounted(() => {
  document.addEventListener("click", handleDocumentClick);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
});

function toggleMenu(id: string) {
  menuOpenId.value = menuOpenId.value === id ? null : id;
}

function openEdit(project: ProjectCard) {
  editingProject.value = { ...project } as ProjectCard;
  isEditModalOpen.value = true;
  menuOpenId.value = null;
}

function closeEditModal() {
  isEditModalOpen.value = false;
  editingProject.value = null;
}

function handleSave(payload: {
  id?: string;
  title: string;
  description: string;
}) {
  if (!payload.id) return;
  const index = projects.value.findIndex(
    (project) => project.id === payload.id
  );
  if (index === -1) return;
  // @ts-ignore
  projects.value[index] = {
    ...projects.value[index],
    title: payload.title,
    description: payload.description,
    lastUpdate: dateFormatter.format(new Date()),
  };
  success("計畫內容已更新");
  closeEditModal();
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
  projects.value = projects.value.filter((item) => item.id !== project.id);
  success("計畫已刪除");
}

function handleCreateProject() {
  info("建置中，敬請期待");
}
</script>
