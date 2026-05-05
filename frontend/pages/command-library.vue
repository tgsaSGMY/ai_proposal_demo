<template>
  <div class="min-h-screen bg-gray-50 px-4 py-6 md:px-10">
    <div class="mx-auto max-w-6xl space-y-6">
      <header class="space-y-3">
        <!-- 頁首區：顯示導覽路徑與頁面統計（已啟用 / 全部指令） -->
        <div
          class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-gray-400"
        >
          <NuxtLink to="/" class="hover:text-gray-600">首頁</NuxtLink>
          <span class="text-gray-300">></span>
          <span class="text-gray-600">我的背景資料</span>
        </div>
        <div
          class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
        >
          <div class="space-y-2">
            <h1 class="text-3xl font-semibold text-gray-900">
              公司背景資料與常用設定
            </h1>
            <p class="text-sm text-gray-500">
              在這裡補充公司資訊與回覆習慣，讓 AI 產出的內容更符合您的需求
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
                全部資料
              </p>
              <p class="text-2xl font-semibold text-gray-900">
                {{ stats.total }}
              </p>
            </div>
          </div>
        </div>
      </header>

      <!-- 搜尋區：可搜尋背景資料（單一輸入框，無外層卡片） -->
      <div class="relative w-full md:max-w-2xl">
        <span
          class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke="currentColor"
            class="h-5 w-5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M21 21l-4.35-4.35m0 0A7.5 7.5 0 105.25 5.25a7.5 7.5 0 0011.4 11.4z"
            />
          </svg>
        </span>
        <input
          v-model="searchTerm"
          type="text"
          aria-label="搜尋背景資料"
          class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 pl-11 pr-11 text-sm text-gray-700 shadow-sm outline-none transition placeholder:text-gray-400 hover:border-gray-300 focus:border-rose-400 focus:ring-2 focus:ring-rose-100"
          placeholder="搜尋背景資料..."
        />
          <button
            v-if="searchTerm"
            type="button"
            aria-label="清除搜尋"
            class="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-700"
            @click="searchTerm = ''"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              class="h-4 w-4"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

      <!-- 💡 提示：使用前需開啟下方卡片的「啟用」開關，AI 才會自動代入背景資料 -->
      <div
        class="flex items-start gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800"
        role="note"
      >
        <span class="text-sm leading-none">💡</span>
        <p class="flex-1 leading-relaxed">
          提示：請確認已開啟下方資料卡的【啟用】開關。只有處於啟用狀態的內容，AI 才會在撰寫計劃書時自動代入您的企業背景資料。
        </p>
      </div>

      <p
        v-if="isLoadingCommands"
        class="text-xs font-semibold uppercase tracking-wide text-gray-400"
      >
        正在同步指令...
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
                  isSystemDefault(command)
                    ? 'bg-sky-50 text-sky-600'
                    : 'bg-emerald-50 text-emerald-600'
                "
              >
                {{ isSystemDefault(command) ? "系統預設" : "自定義" }}
              </span>
              <h3 class="text-lg font-semibold text-gray-900">
                {{ command.title }}
              </h3>
              <div class="text-sm text-gray-500 h-[60px] overflow-hidden">
                {{ command.description }}
              </div>
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
          <span class="text-base font-semibold text-gray-600">新增</span>
          <span class="mt-3 text-sm text-gray-400">
            新增背景資料，讓計畫書更符合您的企業需求。
          </span>
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
import CommandEditModal from "~/components/commands/CommandEditModal.vue";
import { useConfirm } from "~/composables/useConfirm";
import { useCurrentUser } from "~/composables/useCurrentUser";
import { useNotifications } from "~/composables/useNotifications";
import { authenticatedFetch } from "~/composables/useAppAuth";
// 引入：modal、確認與通知工具、以及 Supabase 用於指令的 CRUD 操作

definePageMeta({
  middleware: "auth",
  ssr: false,
});

// 本頁需驗證（登入）後才可存取與編輯指令
useHead({
  title: "我的背景資料 - TGSA 補助引擎",
  meta: [
    // SEO 與分享資訊：說明該頁面的用途與關鍵字，改善搜尋結果顯示
    {
      name: "description",
      content:
        "定義您的企業 DNA、公司實績與邏輯偏好，讓 AI 成為最懂你的專業顧問。管理系統規則和企業專屬指令。",
    },
    {
      name: "keywords",
      content: "背景資料, 模型參數, AI 配置, 企業 DNA, 提示詞管理",
    },
    {
      property: "og:title",
      content: "我的背景資料 - 模型參數與配置管理 - TGSA 補助引擎",
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

// 預設指令：若使用者尚未建立任何指令，系統會 seed 一組預設項目供快速開始
const DEFAULT_COMMANDS = [
  { title: "公司基本資料與資訊庫", isCompany: true },
  { title: "公司商業策略與機會", isCompany: true },
  { title: "企業 ESG 規範", isCompany: false },
  { title: "專用名詞庫", isCompany: false },
] as const;

const DEFAULT_TITLES = new Set(
  DEFAULT_COMMANDS.map((item) => item.title)
);

function isSystemDefault(command: CommandItem): boolean {
  return DEFAULT_TITLES.has(command.title);
}

// 資料與 UI 狀態變數
const commands = ref<CommandItem[]>([]); // 指令列表
const searchTerm = ref(""); // 搜尋關鍵字
const menuOpenId = ref<string | null>(null); // 打開的卡片操作選單 id
const isEditModalOpen = ref(false); // 編輯 modal 顯示狀態
const editingCommand = ref<{
  id?: string;
  title: string;
  description: string;
} | null>(null); // 正在編輯的指令
const pendingEnableCommandId = ref<string | null>(null); // 由啟用流程觸發編輯時，儲存後需自動啟用的指令 id
const { confirm } = useConfirm();
const {
  success,
  info,
  error: notifyError,
  warning: notifyWarning,
} = useNotifications();
const userId = ref<string | null>(null); // 當前使用者 id
const { refreshUser } = useCurrentUser();
const isLoadingCommands = ref(false); // 載入狀態
let hasSeededDefaults = false; // 是否已經 seed 過預設指令
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await authenticatedFetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Command API request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

const stats = computed(() => ({
  active: commands.value.filter((item) => item.isOpen).length,
  total: commands.value.length,
}));

const filteredCommands = computed(() => {
  return commands.value.filter((command) => {
    const keyword = searchTerm.value.trim().toLowerCase();
    return !keyword || command.title.toLowerCase().includes(keyword);
  });
});

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
function openEdit(
  command: CommandItem,
  options?: { enableAfterSave?: boolean },
) {
  editingCommand.value = {
    id: command.id,
    title: command.title,
    description: command.description,
  };
  pendingEnableCommandId.value = options?.enableAfterSave ? command.id : null;
  isEditModalOpen.value = true;
  menuOpenId.value = null;
}

/**
 * 關閉指令編輯 modal 並清空編輯狀態
 */
function closeEditModal() {
  isEditModalOpen.value = false;
  editingCommand.value = null;
  pendingEnableCommandId.value = null;
}

/**
 * 儲存指令（新增或更新）
 * - 驗證使用者登入狀態
 * - 檢查標題與描述不可為空
 * - 呼叫 Supabase 執行 INSERT（新增）或 UPDATE（更新）
 * - 成功後重新載入指令列表並關閉 modal
 * @param payload - 指令數據物件，包含 id（編輯時）、title、description
 */
async function handleSave(payload: {
  id?: string;
  title: string;
  description: string;
}) {
  if (!userId.value) {
    notifyWarning("請先登入後再儲存指令");
    return;
  }

  const normalized = {
    title: payload.title.trim(),
    description: payload.description.trim(),
  };

  if (!normalized.title || !normalized.description) {
    notifyWarning("指令標題與描述不可為空");
    return;
  }

  try {
    if (payload.id) {
      const shouldEnableAfterSave = pendingEnableCommandId.value === payload.id;
      await apiRequest(`/commands/${payload.id}`, {
        method: "PUT",
        body: JSON.stringify({
          ...normalized,
          ...(shouldEnableAfterSave ? { is_open: true } : {}),
        }),
      });
      success(shouldEnableAfterSave ? "指令已更新並啟用" : "指令內容已更新");
    } else {
      await apiRequest("/commands", {
        method: "POST",
        body: JSON.stringify({
          ...normalized,
          is_open: true,
        }),
      });
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
  try {
    await apiRequest(`/commands/${command.id}`, { method: "DELETE" });
  } catch (error: any) {
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
 * - 初始化空白表單
 * - 打開編輯 modal
 */
function handleCreateCommand() {
  pendingEnableCommandId.value = null;
  editingCommand.value = {
    title: "",
    description: "",
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
    userId.value = await refreshUser();
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
    const data = await apiRequest<SupabaseCommandRow[]>("/commands", {
      method: "GET",
    });
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
  for (const item of DEFAULT_COMMANDS) {
    await apiRequest("/commands", {
      method: "POST",
      body: JSON.stringify({
        title: item.title,
        description: "",
        is_open: false,
        is_company: item.isCompany,
      }),
    });
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
      openEdit(target, { enableAfterSave: true });
      return;
    }
  }

  const timestamp = new Date().toISOString();
  try {
    await apiRequest(`/commands/${commandId}`, {
      method: "PUT",
      body: JSON.stringify({ is_open: nextState }),
    });
  } catch (error) {
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
