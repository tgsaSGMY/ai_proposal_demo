<template>
  <div class="min-h-screen bg-gray-50 px-4 py-6 md:px-10">
    <div class="mx-auto max-w-6xl space-y-6">
      <header class="space-y-3">
        <p
          class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-gray-400"
        >
          <NuxtLink to="/" class="hover:text-gray-600">首頁</NuxtLink>
          <span class="text-gray-300">></span>
          <span class="text-gray-600">我的指令庫</span>
        </p>
        <div
          class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
        >
          <div class="space-y-2">
            <h1 class="text-3xl font-semibold text-gray-900">
              模型參數與指令配置
            </h1>
            <p class="text-sm text-gray-500">
              定義您的其他DNA、公司實績與邏輯偏好，讓AI成爲最懂你的專業顧問
            </p>
          </div>
          <div
            class="grid w-full gap-3 rounded-3xl border border-gray-100 bg-white p-4 shadow-sm md:w-auto md:grid-cols-2"
          >
            <div>
              <p
                class="text-xs font-semibold uppercase tracking-wide text-gray-400"
              >
                已啟用
              </p>
              <p class="text-2xl font-semibold text-gray-900">
                {{ stats.active }}
              </p>
            </div>
            <div>
              <p
                class="text-xs font-semibold uppercase tracking-wide text-gray-400"
              >
                全部指令
              </p>
              <p class="text-2xl font-semibold text-gray-900">
                {{ stats.total }}
              </p>
            </div>
          </div>
        </div>
      </header>

      <section
        class="rounded-3xl border border-gray-100 bg-white p-4 shadow-sm"
      >
        <div class="flex flex-wrap gap-2">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            class="rounded-2xl px-4 py-2 text-sm font-semibold transition"
            :class="
              tab.value === activeTab
                ? 'bg-indigo-500 text-white shadow-md'
                : 'bg-gray-50 text-gray-500 hover:bg-gray-100'
            "
            @click="setTab(tab.value)"
          >
            {{ tab.label }} ({{ tab.count }})
          </button>
        </div>
      </section>

      <div
        class="flex flex-col gap-3 rounded-3xl border border-gray-100 bg-white p-4 shadow-sm md:flex-row md:items-center md:justify-between"
      >
        <div class="relative w-full md:max-w-md">
          <input
            v-model="searchTerm"
            type="text"
            class="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 pl-10 text-sm text-gray-700 outline-none focus:border-indigo-400 focus:bg-white"
            placeholder="搜尋指令標題..."
          />
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M21 21l-4.35-4.35m0 0A7.5 7.5 0 105.25 5.25a7.5 7.5 0 0011.4 11.4z"
            />
          </svg>
        </div>
        <button
          class="inline-flex items-center justify-center gap-2 rounded-2xl bg-rose-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-rose-200 transition hover:-translate-y-0.5 hover:bg-rose-600"
          @click="handleCreateCommand"
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
          新增指令
        </button>
      </div>

      <section class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="command in filteredCommands"
          :key="command.id"
          class="relative flex h-full flex-col rounded-3xl border border-gray-100 bg-white p-5 shadow-sm"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="space-y-2">
              <span
                class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold"
                :class="
                  command.isCompany
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'bg-sky-50 text-sky-600'
                "
              >
                {{ command.isCompany ? "企業 DNA" : "系統預設" }}
              </span>
              <h3 class="text-lg font-semibold text-gray-900">
                {{ command.title }}
              </h3>
              <p class="text-sm text-gray-500 min-h-[60px]">
                {{ command.description }}
              </p>
            </div>
            <div class="relative" @click.stop>
              <button
                class="rounded-full p-2 text-gray-400 transition hover:bg-gray-100 hover:text-gray-700"
                @click.stop="toggleMenu(command.id)"
                :aria-expanded="menuOpenId === command.id"
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
                  v-if="menuOpenId === command.id"
                  class="absolute right-0 mt-2 w-44 rounded-2xl border border-gray-100 bg-white py-2 text-sm shadow-xl"
                >
                  <button
                    class="flex w-full items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-50"
                    @click="openEdit(command)"
                  >
                    <span>編輯指令</span>
                  </button>
                  <button
                    class="flex w-full items-center gap-2 px-4 py-2 text-rose-600 hover:bg-rose-50"
                    @click="handleDelete(command)"
                  >
                    <span>刪除指令</span>
                  </button>
                </div>
              </Transition>
            </div>
          </div>

          <div
            class="mt-5 flex items-center justify-between border-t border-gray-100 pt-4"
          >
            <div class="text-xs text-gray-400">
              上次更新：
              <span class="font-semibold text-gray-600">{{
                command.lastUpdated
              }}</span>
            </div>
            <div
              class="flex items-center gap-2 text-xs font-semibold text-gray-500"
            >
              <span>{{ command.isOpen ? "啟用中" : "停用" }}</span>
              <button
                class="relative inline-flex h-6 w-11 items-center rounded-full transition"
                :class="command.isOpen ? 'bg-rose-500' : 'bg-gray-200'"
                @click="handleToggle(command.id)"
              >
                <span
                  class="inline-block h-5 w-5 transform rounded-full bg-white transition"
                  :class="command.isOpen ? 'translate-x-5' : 'translate-x-1'"
                ></span>
              </button>
            </div>
          </div>
        </article>

        <button
          class="flex h-full flex-col items-center justify-center rounded-3xl border-2 border-dashed border-gray-200 bg-white/80 px-6 py-8 text-center text-gray-400 transition hover:border-indigo-300 hover:text-indigo-500"
          @click="handleCreateCommand"
        >
          <span
            class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-indigo-50 text-indigo-500"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              class="h-7 w-7"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 6v12m6-6H6"
              />
            </svg>
          </span>
          <p class="text-base font-semibold text-gray-600">新增自訂指令</p>
          <p class="mt-1 text-sm text-gray-400">
            建立新的策略說明，馬上指向企業規範
          </p>
        </button>
      </section>
    </div>

    <CommandEditModal
      v-model:model-value="isEditModalOpen"
      :command="editingCommand"
      @save="handleSave"
      @close="closeEditModal"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import CommandEditModal from "~/components/CommandEditModal.vue";
import { useConfirm } from "~/composables/useConfirm";
import { useNotifications } from "~/composables/useNotifications";

interface CommandItem {
  id: string;
  title: string;
  description: string;
  lastUpdated: string;
  isOpen: boolean;
  isCompany: boolean;
}

type CommandTab = "all" | "system" | "company";

const commands = ref<CommandItem[]>([
  {
    id: "cmd-1",
    title: "公司基本資料與資訊庫",
    description:
      "整合成立時間、AIOT 解決方案、認證與過往里程碑，作為 AI 回答專案背景的必備素材。",
    lastUpdated: "2 天前",
    isOpen: true,
    isCompany: true,
  },
  {
    id: "cmd-2",
    title: "公司商業策略與機會",
    description:
      "聚焦 B2B 訂閱制策略，強調客戶留存率與系統整合能力，指引 AI 優先回應商務策略。",
    lastUpdated: "1 週前",
    isOpen: true,
    isCompany: true,
  },
  {
    id: "cmd-3",
    title: "企業 ESG 規範",
    description:
      "所有提案需符合 SDGs 指標 12，優先說明供應鏈及材料策略，並強調 ESG 治理。",
    lastUpdated: "3 天前",
    isOpen: false,
    isCompany: false,
  },
  {
    id: "cmd-4",
    title: "專用名詞庫",
    description:
      "統一定義內部用語與產品名稱，避免生成時出現舊稱呼或錯誤拼法，維護品牌一致性。",
    lastUpdated: "2 天前",
    isOpen: true,
    isCompany: false,
  },
  {
    id: "cmd-5",
    title: "工程師提問模組",
    description:
      "蒐集技術 PM 常見問題，規範提問格式與必要欄位，確保 AI 可快速回覆技術細節。",
    lastUpdated: "1 天前",
    isOpen: false,
    isCompany: true,
  },
]);

const activeTab = ref<CommandTab>("all");
const searchTerm = ref("");
const menuOpenId = ref<string | null>(null);
const isEditModalOpen = ref(false);
const editingCommand = ref<CommandItem | null>(null);
const { confirm } = useConfirm();
const { success, info } = useNotifications();

const tabCounts = computed(() => ({
  all: commands.value.length,
  system: commands.value.filter((item) => !item.isCompany).length,
  company: commands.value.filter((item) => item.isCompany).length,
}));

const tabs = computed(() => [
  { label: "所有指令", value: "all" as CommandTab, count: tabCounts.value.all },
  {
    label: "系統規則邏輯",
    value: "system" as CommandTab,
    count: tabCounts.value.system,
  },
  {
    label: "企業專屬 DNA",
    value: "company" as CommandTab,
    count: tabCounts.value.company,
  },
]);

const stats = computed(() => ({
  active: commands.value.filter((item) => item.isOpen).length,
  total: commands.value.length,
}));

const filteredCommands = computed(() => {
  return commands.value.filter((command) => {
    const matchesTab =
      activeTab.value === "all" ||
      (activeTab.value === "system" && !command.isCompany) ||
      (activeTab.value === "company" && command.isCompany);
    const keyword = searchTerm.value.trim().toLowerCase();
    const matchesKeyword =
      !keyword || command.title.toLowerCase().includes(keyword);
    return matchesTab && matchesKeyword;
  });
});

function setTab(value: CommandTab) {
  activeTab.value = value;
}

function toggleMenu(id: string) {
  menuOpenId.value = menuOpenId.value === id ? null : id;
}

function openEdit(command: CommandItem) {
  editingCommand.value = { ...command };
  isEditModalOpen.value = true;
  menuOpenId.value = null;
}

function closeEditModal() {
  isEditModalOpen.value = false;
  editingCommand.value = null;
}

function handleSave(payload: {
  id?: string;
  title: string;
  description: string;
  isCompany: boolean;
}) {
  if (!payload.id) return;
  const index = commands.value.findIndex(
    (command) => command.id === payload.id
  );
  if (index === -1) return;
  // @ts-ignore
  commands.value[index] = {
    ...commands.value[index],
    id: payload.id!, // Ensure id is non-undefined
    title: payload.title,
    description: payload.description,
    isCompany: payload.isCompany,
    lastUpdated: "剛剛",
  };
  success("指令內容已更新");
  closeEditModal();
}

async function handleDelete(command: CommandItem) {
  menuOpenId.value = null;
  const confirmed = await confirm({
    title: "刪除指令",
    message: `確定要刪除「${command.title}」嗎？此操作無法復原。`,
    confirmText: "刪除",
    confirmColor: "danger",
  });
  if (!confirmed) return;
  commands.value = commands.value.filter((item) => item.id !== command.id);
  success("指令已刪除");
}

function handleCreateCommand() {
  info("建置中，敬請期待");
}

function handleToggle(commandId: string) {
  const target = commands.value.find((item) => item.id === commandId);
  if (!target) return;
  target.isOpen = !target.isOpen;
  info(target.isOpen ? "已啟用此指令" : "已停用此指令");
}

const handleDocumentClick = () => {
  menuOpenId.value = null;
};

onMounted(() => {
  document.addEventListener("click", handleDocumentClick);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
});
</script>
