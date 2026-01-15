<!-- 数据集编辑模态帐组件：管理方案使用的数据集 -->
<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 flex justify-center items-center p-4 sm:p-6"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden border border-gray-200"
    >
      <!-- Header -->
      <header
        class="p-4 sm:p-5 border-b bg-gradient-to-r from-indigo-50 to-white flex items-center justify-between flex-shrink-0"
      >
        <div>
          <h2
            class="text-lg sm:text-xl font-bold text-gray-800 flex items-center gap-2"
          >
            <span>👁️ 檢視數據點</span>
            <span
              class="px-2 py-0.5 rounded-md bg-gray-100 text-xs text-gray-500 font-mono"
              >#{{ dataset.id }}</span
            >
          </h2>
          <p class="text-xs text-gray-400 mt-1">
            此模式下僅允許修改數據來源分類
          </p>
        </div>
        <button
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-600 transition"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </header>

      <!-- Main content -->
      <main class="flex-1 flex flex-col min-h-0 bg-gray-50/50">
        <!-- Top: Source Type Selection -->
        <div class="p-4 sm:p-6 bg-white border-b border-gray-100 flex-shrink-0">
          <label
            class="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3"
          >
            數據來源設定
          </label>

          <div class="flex items-center gap-4">
            <!-- Label Left -->
            <span
              class="text-sm font-medium transition-colors"
              :class="!isAiReference ? 'text-gray-900' : 'text-gray-400'"
            >
              不作為 AI 參考
              <span class="block text-[10px] text-gray-400 font-normal"
                >(外部資料)</span
              >
            </span>

            <!-- Toggle Button -->
            <button
              type="button"
              @click="toggleSourceType"
              :disabled="isGoldenSample"
              class="relative inline-flex h-7 w-12 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2"
              :class="[
                isAiReference ? 'bg-indigo-600' : 'bg-gray-200',
                isGoldenSample ? 'opacity-60 cursor-not-allowed' : '',
              ]"
            >
              <span class="sr-only">切換 AI 參考狀態</span>
              <!-- Knob -->
              <span
                aria-hidden="true"
                class="pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out flex items-center justify-center"
                :class="isAiReference ? 'translate-x-5' : 'translate-x-0'"
              >
                <!-- Lock Icon for Golden Sample -->
                <svg
                  v-if="isGoldenSample"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  class="w-3 h-3 text-gray-400"
                >
                  <path
                    fill-rule="evenodd"
                    d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z"
                    clip-rule="evenodd"
                  />
                </svg>
              </span>
            </button>

            <!-- Label Right -->
            <span
              class="text-sm font-medium transition-colors"
              :class="isAiReference ? 'text-indigo-700' : 'text-gray-400'"
            >
              作為 AI 參考
              <span
                class="block text-[10px] font-normal"
                :class="isAiReference ? 'text-indigo-500' : 'text-gray-400'"
              >
                <span v-if="isGoldenSample">✨ 黃金樣本 (鎖定)</span>
                <span v-else>(生成資料)</span>
              </span>
            </span>
          </div>
        </div>

        <!-- Bottom: Split View -->
        <div class="flex-1 flex flex-col md:flex-row overflow-hidden">
          <!-- Left: User Input (Prompt) -->
          <div
            class="flex-1 flex flex-col border-b md:border-b-0 md:border-r border-gray-200 min-h-0"
          >
            <div class="px-6 py-3 bg-gray-50 border-b border-gray-100">
              <span
                class="text-xs font-bold text-indigo-600 uppercase tracking-wider"
                >用戶輸入 (Prompt)</span
              >
            </div>
            <div class="flex-1 overflow-y-auto p-6 bg-white">
              <div
                class="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed font-sans"
              >
                {{ editableData.prompt || "無輸入內容" }}
              </div>
            </div>
          </div>

          <!-- Right: User Output (Rendered HTML) -->
          <div class="flex-1 flex flex-col min-h-0">
            <div class="px-6 py-3 bg-gray-50 border-b border-gray-100">
              <span
                class="text-xs font-bold text-emerald-600 uppercase tracking-wider"
                >輸出結果 (Preview)</span
              >
            </div>
            <div class="flex-1 overflow-y-auto p-6 bg-white relative">
              <!-- 渲染內容 -->
              <div
                v-if="renderedHtml"
                class="prose prose-sm prose-slate max-w-none"
              >
                <div v-html="renderedHtml"></div>
              </div>

              <!-- 錯誤或空狀態提示 -->
              <div
                v-else
                class="flex h-full flex-col items-center justify-center text-gray-400"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-10 w-10 mb-2 opacity-50"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <p class="text-sm">無法預覽內容 (缺少 Schema 或數據)</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      <!-- Footer -->
      <footer
        class="flex-shrink-0 p-4 bg-gray-50 border-t flex justify-end gap-3"
      >
        <button
          @click="$emit('close')"
          class="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium transition shadow-sm"
        >
          取消
        </button>
        <button
          @click="handleSave"
          :disabled="isSaving"
          class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-indigo-400 text-sm font-medium transition shadow-sm flex items-center gap-2"
        >
          <svg
            v-if="isSaving"
            class="animate-spin h-4 w-4 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          {{ isSaving ? "保存中..." : "確認修改" }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { watch, reactive, computed } from "vue";
import { renderPlanToHtml } from "~/utils/exportToWord"; // 確保這個路徑正確

const props = defineProps({
  show: Boolean,
  dataset: { type: Object, default: () => null },
  isSaving: Boolean,
  allConfigs: { type: Array, required: true },
});

const emit = defineEmits(["close", "save"]);

const editableData = reactive({
  id: null,
  prompt: "",
  source_type: "synthetic_data",
  final_answer_obj: {}, // 這是唯讀的，用於渲染
});

// 當 dataset 改變時更新本地數據
watch(
  () => props.dataset,
  (newVal) => {
    if (newVal) {
      editableData.id = newVal.id;
      editableData.prompt = newVal.prompt || "";
      editableData.source_type = newVal.source_type || "synthetic_data";
      // 深拷貝以防萬一，雖然我們不編輯它
      editableData.final_answer_obj = newVal.final_answer
        ? JSON.parse(JSON.stringify(newVal.final_answer))
        : {};
    }
  },
  { immediate: true, deep: true }
);

// 計算渲染後的 HTML
const renderedHtml = computed(() => {
  if (!props.dataset || !props.allConfigs) return "";

  const { grant_id, template_id, section_id } = props.dataset;
  if (!grant_id || !template_id || !section_id) return "";

  // 1. 查找對應的 Schema Config
  const grant = props.allConfigs.find((g) => g.id === grant_id);
  const template = grant?.templates.find((t) => t.id === template_id);
  const section = template?.sections.find((s) => s.id === section_id);

  if (!section) return "";

  try {
    // 2. 使用 exportToWord 中的 renderPlanToHtml 進行渲染
    // 參數1: 章節定義陣列
    // 參數2: 數據內容 (Key 是 section_id)
    return renderPlanToHtml(
      [
        {
          id: section.id,
          name: section.name || "預覽內容",
          json_schema: section.json_schema,
        },
      ],
      {
        [section.id]: {
          content: editableData.final_answer_obj || "",
        },
      }
    );
  } catch (error) {
    console.error("HTML Render Error:", error);
    return `<div class="text-red-500 text-sm">渲染錯誤: ${error.message}</div>`;
  }
});

function handleSave() {
  // 只回傳可能被修改的 source_type，以及必要的 id
  // prompt 和 final_answer 保持原樣回傳，或者後端不更新它們
  emit("save", {
    id: editableData.id,
    prompt: editableData.prompt, // 雖不編輯但保持數據完整性
    final_answer: editableData.final_answer_obj, // 雖不編輯但保持數據完整性
    source_type: editableData.source_type, // 這是主要修改的欄位
  });
}

// 判斷目前是否屬於「作為 AI 參考」的類別
const isAiReference = computed(() => {
  return ["golden_samples", "synthetic_data"].includes(
    editableData.source_type
  );
});

// 判斷是否為黃金樣本 (鎖定狀態)
const isGoldenSample = computed(() => {
  return editableData.source_type === "golden_samples";
});

// 切換邏輯
function toggleSourceType() {
  // 如果是黃金樣本，禁止切換
  if (isGoldenSample.value) return;

  if (isAiReference.value) {
    // 當前是 AI 參考 (synthetic_data) -> 切換為 不參考 (external_direct)
    editableData.source_type = "external_direct";
  } else {
    // 當前是不參考 (external_direct) -> 切換為 AI 參考 (synthetic_data)
    editableData.source_type = "synthetic_data";
  }
}
</script>

<style scoped>
/* 確保渲染出的 HTML 樣式正確 */
.prose {
  max-width: none;
  font-size: 0.95rem;
  line-height: 1.6;
}
.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: 600;
  color: #1f2937;
}
.prose :deep(p) {
  margin-bottom: 0.75em;
}
.prose :deep(ul) {
  list-style-type: disc;
  padding-left: 1.5em;
}
.prose :deep(ol) {
  list-style-type: decimal;
  padding-left: 1.5em;
}
</style>
