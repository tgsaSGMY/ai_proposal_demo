<template>
  <div class="min-h-screen bg-gray-50 px-4 py-6 md:px-10">
    <div class="mx-auto max-w-6xl space-y-6">
      <header class="space-y-3">
        <!-- 頁首區：顯示導覽路徑與頁面統計（已啟用 / 全部指令） -->
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

      <!-- 標籤篩選區：切換查看所有 / 系統 / 企業指令 -->
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

      <!-- 搜尋與新增區：可搜尋指令或建立新指令 -->
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
      <p
        v-if="isLoadingCommands"
        class="text-xs font-semibold uppercase tracking-wide text-gray-400"
      >
        正在同步 Supabase 指令...
      </p>

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
              <p class="text-sm text-gray-500 h-[60px] overflow-hidden">
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
                <!-- 卡片更多操作按鈕：打開選單以編輯或刪除該指令 -->
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
            <!-- 指令啟用切換區：可直接在卡片上啟用或停用對應指令 -->
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
import { supabase } from "~/utils/supabaseClient";
// 引入：modal、確認與通知工具、以及 Supabase 用於指令的 CRUD 操作

definePageMeta({
  middleware: "auth",
  ssr: false,
});

// 本頁需驗證（登入）後才可存取與編輯指令
if (process.client) {
  useHead({
    title: "我的指令庫 - TGSA 補助引擎",
    meta: [
      // SEO 與分享資訊：說明該頁面的用途與關鍵字，改善搜尋結果顯示
      {
        name: "description",
        content:
          "定義您的企業 DNA、公司實績與邏輯偏好，讓 AI 成為最懂你的專業顧問。管理系統規則和企業專屬指令。",
      },
      {
        name: "keywords",
        content: "指令庫, 模型參數, AI 配置, 企業 DNA, 提示詞管理",
      },
      {
        property: "og:title",
        content: "我的指令庫 - 模型參數與配置管理 - TGSA 補助引擎",
      },
      {
        property: "og:description",
        content:
          "定義您的企業 DNA、公司實績與邏輯偏好，讓 AI 成為最懂你的專業顧問。",
      },
      { property: "og:type", content: "website" },
      { name: "robots", content: "index, follow" },
    ],
  });
}

// 介面定義：描述指令在前端使用的形態
interface CommandItem {
  id: string;
  title: string;
  description: string;
  lastUpdated: string;
  isOpen: boolean;
  isCompany: boolean;
  userId: string;
}

interface SupabaseCommandRow {
  id: string;
  title: string;
  description: string;
  user_id: string;
  last_updated: string | null;
  is_open: boolean;
  is_company: boolean;
}

type CommandTab = "all" | "system" | "company";

// 預設指令：若使用者尚未建立任何指令，系統會 seed 一組預設項目供快速開始
const DEFAULT_COMMANDS = [
  { title: "公司基本資料與資訊庫", isCompany: true },
  { title: "公司商業策略與機會", isCompany: true },
  { title: "企業 ESG 規範", isCompany: false },
  { title: "專用名詞庫", isCompany: false },
  { title: "工程師提問模組", isCompany: true },
] as const;

// 資料與 UI 狀態變數
const commands = ref<CommandItem[]>([]); // 指令列表
const activeTab = ref<CommandTab>("all"); // 目前分頁（all, system, company）
const searchTerm = ref(""); // 搜尋關鍵字
const menuOpenId = ref<string | null>(null); // 打開的卡片操作選單 id
const isEditModalOpen = ref(false); // 編輯 modal 顯示狀態
const editingCommand = ref<{
  id?: string;
  title: string;
  description: string;
  isCompany: boolean;
} | null>(null); // 正在編輯的指令
const { confirm } = useConfirm();
const {
  success,
  info,
  error: notifyError,
  warning: notifyWarning,
} = useNotifications();
const userId = ref<string | null>(null); // 當前使用者 id
const isLoadingCommands = ref(false); // 載入狀態
let hasSeededDefaults = false; // 是否已經 seed 過預設指令

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

/**
 * 切換指令分頁篩選
 * @param value - 分頁類型 ('all' - 所有指令, 'system' - 系統規則, 'company' - 企業專屬)
 */
function setTab(value: CommandTab) {
  activeTab.value = value;
}

/**
 * 切換指定指令卡片的操作選單開關狀態
 * @param id - 指令的 ID
 */
function toggleMenu(id: string) {
  menuOpenId.value = menuOpenId.value === id ? null : id;
}

/**
 * 打開指令編輯 modal，將選中的指令載入到編輯表單中
 * @param command - 要編輯的指令物件
 */
function openEdit(command: CommandItem) {
  editingCommand.value = {
    id: command.id,
    title: command.title,
    description: command.description,
    isCompany: command.isCompany,
  };
  isEditModalOpen.value = true;
  menuOpenId.value = null;
}

/**
 * 關閉指令編輯 modal 並清空編輯狀態
 */
function closeEditModal() {
  isEditModalOpen.value = false;
  editingCommand.value = null;
}

/**
 * 儲存指令（新增或更新）
 * - 驗證使用者登入狀態
 * - 檢查標題與描述不可為空
 * - 呼叫 Supabase 執行 INSERT（新增）或 UPDATE（更新）
 * - 成功後重新載入指令列表並關閉 modal
 * @param payload - 指令數據物件，包含 id（編輯時）、title、description、isCompany
 */
async function handleSave(payload: {
  id?: string;
  title: string;
  description: string;
  isCompany: boolean;
}) {
  if (!userId.value) {
    notifyWarning("請先登入後再儲存指令");
    return;
  }

  const normalized = {
    title: payload.title.trim(),
    description: payload.description.trim(),
    is_company: payload.isCompany,
  };

  if (!normalized.title || !normalized.description) {
    notifyWarning("指令標題與描述不可為空");
    return;
  }

  try {
    const timestamp = new Date().toISOString();
    if (payload.id) {
      const { error } = await supabase
        .from("commands")
        .update({
          ...normalized,
          last_updated: timestamp,
        })
        .eq("id", payload.id)
        .eq("user_id", userId.value);
      if (error) throw error;
      success("指令內容已更新");
    } else {
      const { error } = await supabase.from("commands").insert({
        ...normalized,
        user_id: userId.value,
        is_open: true,
        last_updated: timestamp,
      });
      if (error) throw error;
      success("已新增指令");
    }
    await loadCommands();
    closeEditModal();
  } catch (error: any) {
    console.error("Failed to save command", error);
    notifyError(error?.message || "儲存指令失敗，請稍後再試");
  }
}

/**
 * 刪除指令
 * - 需使用者確認（二次確認對話）
 * - 驗證登入狀態
 * - 呼叫 Supabase DELETE
 * - 成功後重新載入指令列表
 * @param command - 要刪除的指令物件
 */
async function handleDelete(command: CommandItem) {
  menuOpenId.value = null;
  const confirmed = await confirm({
    title: "刪除指令",
    message: `確定要刪除「${command.title}」嗎？此操作無法復原。`,
    confirmText: "刪除",
    confirmColor: "danger",
  });
  if (!confirmed) return;
  if (!userId.value) {
    notifyWarning("請先登入後再進行操作");
    return;
  }
  const { error } = await supabase
    .from("commands")
    .delete()
    .eq("id", command.id)
    .eq("user_id", userId.value);
  if (error) {
    console.error("Failed to delete command", error);
    notifyError("刪除指令失敗，請稍後再試");
    return;
  }
  await loadCommands();
  success("指令已刪除");
}

/**
 * 建立新指令：初始化編輯表單並打開 modal
 * - 清空編輯表單的所有欄位
 * - 設定預設值（企業 DNA 類型為 false）
 * - 打開編輯 modal
 */
function handleCreateCommand() {
  editingCommand.value = {
    title: "",
    description: "",
    isCompany: false,
  };
  isEditModalOpen.value = true;
}

/**
 * 啟動指令初始化流程
 * - 取得當前登入使用者的 ID
 * - 載入使用者的指令列表
 * - 若發生錯誤，顯示通知
 */
async function bootstrapCommands() {
  try {
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser();
    if (error) throw error;
    userId.value = user?.id || null;
    await loadCommands();
  } catch (error: any) {
    console.error("Failed to initialize commands", error);
    notifyError("無法取得指令資料，請稍後再試");
  }
}

/**
 * 從 Supabase 載入當前使用者的指令列表
 * - 若使用者未登入，返回空列表
 * - 按最近更新時間排序（降序）
 * - 若清單為空且尚未 seed，則自動建立預設指令
 * - 將 Supabase 的 snake_case 欄位轉換為前端使用的格式
 * - 設定載入狀態與錯誤訊息
 */
async function loadCommands() {
  if (!userId.value) {
    commands.value = [];
    return;
  }
  isLoadingCommands.value = true;
  try {
    const { data, error } = await supabase
      .from("commands")
      .select("*")
      .eq("user_id", userId.value)
      .order("last_updated", { ascending: false });
    if (error) throw error;
    if (!data || data.length === 0) {
      if (!hasSeededDefaults) {
        await seedDefaultCommands();
        hasSeededDefaults = true;
        await loadCommands();
        return;
      }
    }
    hasSeededDefaults = false;
    commands.value = (data || []).map(mapCommandRow);
  } catch (error: any) {
    console.error("Failed to load commands", error);
    notifyError("載入指令列表失敗，請稍後再試");
  } finally {
    isLoadingCommands.value = false;
  }
}

/**
 * 為新使用者自動建立預設指令集
 * - 建立一組常用的系統規則與企業 DNA 指令範本
 * - 預設狀態為停用（is_open: false），使用者可後續啟用
 * - 記錄建立時間戳
 * - 若建立失敗，拋出錯誤
 */
async function seedDefaultCommands() {
  if (!userId.value) {
    return;
  }
  const timestamp = new Date().toISOString();
  const payload = DEFAULT_COMMANDS.map((item) => ({
    title: item.title,
    description: "",
    user_id: userId.value,
    is_open: false,
    is_company: item.isCompany,
    last_updated: timestamp,
  }));
  const { error } = await supabase.from("commands").insert(payload);
  if (error) {
    throw error;
  }
}

/**
 * 將 Supabase 的指令記錄轉換為前端使用的 CommandItem 格式
 * - 轉換欄位命名（snake_case → camelCase）
 * - 格式化時間戳為台灣時區格式
 * - 保持所有必要的業務邏輯資料
 * @param row - Supabase 指令記錄
 * @returns 轉換後的前端指令物件
 */
function mapCommandRow(row: SupabaseCommandRow): CommandItem {
  return {
    id: row.id,
    title: row.title,
    description: row.description,
    lastUpdated: formatTimestamp(row.last_updated),
    isOpen: row.is_open,
    isCompany: row.is_company,
    userId: row.user_id,
  };
}

/**
 * 格式化時間戳為台灣時區的可讀格式
 * - 若輸入為空，返回 '-'
 * - 若日期無效，返回原始值
 * - 否則返回 'YYYY/MM/DD HH:MM:SS' 格式
 * @param value - ISO 格式的時間戳或 null
 * @returns 格式化後的日期時間字串
 */
function formatTimestamp(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-TW", { hour12: false });
}

/**
 * 切換指令的啟用/停用狀態
 * - 驗證使用者登入
 * - 若要啟用，檢查標題與描述不可為空，否則打開編輯 modal
 * - 呼叫 Supabase 更新 is_open 狀態
 * - 更新本地狀態與最後更新時間
 * - 成功後顯示通知
 * @param commandId - 指令的 ID
 */
async function handleToggle(commandId: string) {
  if (!userId.value) {
    notifyWarning("請先登入後再進行操作");
    return;
  }
  const target = commands.value.find((item) => item.id === commandId);
  if (!target) return;
  const nextState = !target.isOpen;

  // If enabling, ensure the command has non-empty title and description
  if (nextState) {
    const title = (target.title || "").trim();
    const desc = (target.description || "").trim();
    if (!title || !desc) {
      notifyWarning("無法啟用空白的指令內容，請先編輯並填寫標題與描述");
      // Open edit modal so user can fill required fields
      openEdit(target);
      return;
    }
  }

  const timestamp = new Date().toISOString();
  const { error } = await supabase
    .from("commands")
    .update({ is_open: nextState, last_updated: timestamp })
    .eq("id", commandId)
    .eq("user_id", userId.value);
  if (error) {
    console.error("Failed to toggle command", error);
    notifyError("切換指令狀態失敗，請稍後再試");
    return;
  }
  target.isOpen = nextState;
  target.lastUpdated = formatTimestamp(timestamp);
  info(nextState ? "已啟用此指令" : "已停用此指令");
}

/**
 * 點擊文件任意處時關閉任何打開的操作選單
 * - 用於實現「點選外部關閉」功能
 */
const handleDocumentClick = () => {
  menuOpenId.value = null;
};

// 初始化：加上全域點擊監聽並載入指令資料
onMounted(async () => {
  document.addEventListener("click", handleDocumentClick);
  await bootstrapCommands();
});

// 清理監聽器
onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
});
</script>
