<!-- 命令编辑模态帐组件：编辑自定义的API调用命令 (commands) -->
<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center px-4 py-8"
      >
        <div
          class="absolute inset-0 bg-gray-900/30 backdrop-blur-sm"
          @click="handleClose"
        ></div>
        <div
          class="relative w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl"
        >
          <div class="flex items-center justify-between">
            <div>
              <p
                class="text-xs font-semibold uppercase tracking-wide text-rose-400"
              >
                編輯模型指令
              </p>
              <h3 class="text-xl font-semibold text-gray-900">
                {{ command?.title || "新指令" }}
              </h3>
            </div>
            <button
              class="rounded-full p-2 text-gray-400 transition hover:bg-gray-100 hover:text-gray-700"
              @click="handleClose"
              aria-label="關閉視窗"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="1.5"
                stroke="currentColor"
                class="h-5 w-5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <form class="mt-6 space-y-5" @submit.prevent="handleSave">
            <div class="space-y-2">
              <label class="text-sm font-semibold text-gray-700"
                >指令標題</label
              >
              <input
                v-model="form.title"
                type="text"
                class="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 outline-none focus:border-rose-400 focus:bg-white"
                placeholder="輸入指令名稱"
                required
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-semibold text-gray-700"
                >指令描述</label
              >
              <textarea
                v-model="form.description"
                rows="4"
                class="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 outline-none focus:border-rose-400 focus:bg-white"
                :placeholder="computedHint"
                required
              ></textarea>
            </div>

            <div
              class="flex items-center justify-between rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3"
            >
              <div>
                <p class="text-sm font-semibold text-gray-800">企業專屬 DNA</p>
                <p class="text-xs text-gray-500">切換後會標記為企業自訂指令</p>
              </div>
              <button
                type="button"
                class="relative inline-flex h-7 w-12 items-center rounded-full transition"
                :class="form.isCompany ? 'bg-emerald-500' : 'bg-gray-300'"
                @click="form.isCompany = !form.isCompany"
              >
                <span
                  class="inline-block h-5 w-5 transform rounded-full bg-white transition"
                  :class="form.isCompany ? 'translate-x-5' : 'translate-x-1'"
                ></span>
              </button>
            </div>

            <div class="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                class="rounded-2xl border border-gray-200 px-5 py-2 text-sm font-semibold text-gray-600 transition hover:border-gray-300"
                @click="handleClose"
              >
                取消
              </button>
              <button
                type="submit"
                class="rounded-2xl bg-rose-500 px-6 py-2 text-sm font-semibold text-white shadow-md shadow-rose-200 transition hover:bg-rose-600"
              >
                儲存
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from "vue";

interface CommandPayload {
  id?: string;
  title: string;
  description: string;
  isCompany: boolean;
}

interface Props {
  modelValue: boolean;
  command: CommandPayload | null;
}

const props = defineProps<Props>();
const emit = defineEmits(["update:modelValue", "save", "close"]);

const form = reactive<CommandPayload>({
  id: undefined,
  title: "",
  description: "",
  isCompany: false,
});

// 依據卡片標題提供對應的佔位提示，讓使用者更容易理解該卡片的用途
const HINT_MAP: Record<string, string> = {
  "公司基本資料與資訊庫": "填寫公司名稱、成立年份、資本額、員工數、主要產品與服務等基本資訊",
  "公司商業策略與機會": "描述公司的核心競爭優勢、市場定位、目標客群與未來發展方向",
  "企業 ESG 規範": "說明公司在環境保護、社會責任與公司治理方面的政策與實踐成果",
  "專用名詞庫": "列出產業專有名詞及其定義，確保 AI 生成內容使用正確的術語",
  "工程師提問模組": "提供技術細節與規格說明，幫助 AI 準確描述產品的技術架構與創新點",
};

const computedHint = computed(() => {
  const title = props.command?.title?.trim();
  if (title && HINT_MAP[title]) return HINT_MAP[title];
  return "補充 AI 需要的背景、語氣或指令細節";
});

// 監聽命令 Prop 變化，自動同步表單資料到本地狀態
watch(
  () => props.command,
  (value) => {
    form.id = value?.id;
    form.title = value?.title || "";
    form.description = value?.description || "";
    form.isCompany = value?.isCompany ?? false;
  },
  { immediate: true },
);

// 關閉模態框，觸發 update:modelValue 和 close 事件
function handleClose() {
  emit("update:modelValue", false);
  emit("close");
}

// 驗證表單並發送保存事件，包含完整的命令資料（id、標題、描述、公司標籤）
function handleSave() {
  if (!form.title.trim() || !form.description.trim()) return;
  emit("save", { ...form });
}
</script>
