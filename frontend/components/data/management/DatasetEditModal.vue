<!-- 数据集管理裏面的編輯功能 -->

<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 flex justify-center items-center p-4 sm:p-6"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white rounded-2xl shadow-2xl w-full max-w-6xl flex flex-col overflow-hidden border border-gray-200"
      :class="isMaskMode ? 'max-h-[96vh]' : 'max-h-[90vh]'"
    >
      <!-- Header -->
      <header
        class="p-4 sm:p-5 border-b bg-gradient-to-r from-indigo-50 to-white flex items-center justify-between flex-shrink-0"
      >
        <div>
          <h2
            class="text-lg sm:text-xl font-bold text-gray-800 flex items-center gap-2"
          >
            <span>📝 編輯數據點</span>
            <span
              class="px-2 py-0.5 rounded-md bg-gray-100 text-xs text-gray-500 font-mono"
              >#{{ dataset.id }}</span
            >
          </h2>
          <p class="text-xs text-gray-400 mt-1">
            可修改數據來源分類、用戶輸入 (Prompt) 及輸出內容
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
        <div
          v-if="!isMaskMode"
          class="p-4 sm:p-6 bg-white border-b border-gray-100 flex-shrink-0"
        >
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

          <div
            v-if="isAiReference"
            class="mt-4 pt-4 border-t border-gray-100 flex items-center"
          >
            <label
              class="inline-flex items-center gap-2 cursor-pointer select-none"
            >
              <input
                type="checkbox"
                :checked="isGoldenSample"
                @change="toggleGoldenSample"
                class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span class="text-sm text-gray-700">設為黃金樣本</span>
            </label>
          </div>
        </div>

        <!-- Bottom: Split View -->
        <div
          v-if="!isMaskMode"
          class="flex-1 flex flex-col md:flex-row overflow-hidden"
        >
          <!-- Left: User Input (Prompt) -->
          <div
            class="flex-1 flex flex-col border-b md:border-b-0 md:border-r border-gray-200 min-h-0"
          >
            <div class="px-6 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
              <span
                class="text-xs font-bold text-indigo-600 uppercase tracking-wider"
                >用戶輸入 (Prompt)</span
              >
              <button
                type="button"
                @click="isEditingPrompt = !isEditingPrompt"
                class="px-2 py-1 text-xs font-medium rounded-md transition"
                :class="isEditingPrompt
                  ? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
              >
                {{ isEditingPrompt ? '完成編輯' : '編輯' }}
              </button>
            </div>
            <div class="flex-1 overflow-y-auto p-6 bg-white">
              <!-- Editing mode: textarea -->
              <textarea
                v-if="isEditingPrompt"
                v-model="editableData.prompt"
                class="w-full h-full min-h-[200px] text-sm text-gray-700 leading-relaxed font-sans border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                placeholder="輸入用戶 Prompt..."
              ></textarea>
              <!-- Read mode: plain text -->
              <div
                v-else
                class="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed font-sans"
              >
                {{ editableData.prompt || "無輸入內容" }}
              </div>
            </div>
          </div>

          <!-- Right: User Output (Preview / Edit tabs) -->
          <div class="flex-1 flex flex-col min-h-0">
            <div
              class="px-6 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between gap-3"
            >
              <!-- Tab buttons -->
              <div class="flex items-center gap-1">
                <button
                  type="button"
                  @click="isEditingContent = false"
                  class="px-3 py-1.5 text-xs font-semibold rounded-md transition"
                  :class="!isEditingContent
                    ? 'bg-emerald-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
                >
                  預覽
                </button>
                <button
                  type="button"
                  @click="isEditingContent = true"
                  :disabled="!sectionConfig"
                  class="px-3 py-1.5 text-xs font-semibold rounded-md transition"
                  :class="[
                    isEditingContent
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200',
                    !sectionConfig ? 'opacity-50 cursor-not-allowed' : ''
                  ]"
                >
                  編輯內容
                </button>
              </div>
              <button
                v-if="!isEditingContent"
                type="button"
                @click="enterMaskMode"
                class="px-3 py-1.5 text-xs font-semibold rounded-md bg-emerald-600 text-white hover:bg-emerald-700 transition"
              >
                進入脫敏界面
              </button>
            </div>
            <div class="flex-1 overflow-y-auto p-6 bg-white relative">
              <!-- Edit mode: JsonSchemaForm -->
              <template v-if="isEditingContent">
                <!-- Schema found: show form editor -->
                <div v-if="sectionConfig && sectionConfig.json_schema">
                  <div class="mb-3 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
                    <p class="text-xs text-blue-700">
                      正在編輯章節: <strong>{{ sectionConfig.name }}</strong>
                      — 修改後可切換至「預覽」查看效果
                    </p>
                  </div>
                  <JsonSchemaForm
                    :schema="sectionConfig.json_schema"
                    :modelValue="editableData.final_answer_obj"
                    @update:modelValue="editableData.final_answer_obj = $event"
                  />
                </div>
                <!-- Schema not found: warning -->
                <div
                  v-else
                  class="flex h-full flex-col items-center justify-center text-amber-600"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mb-2 opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <p class="text-sm font-medium">無法載入章節 Schema</p>
                  <p class="text-xs text-amber-500 mt-1">請確認該章節是否仍然存在於模板配置中</p>
                </div>
              </template>

              <!-- Preview mode: rendered HTML -->
              <template v-else>
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
              </template>
            </div>
          </div>
        </div>

        <!-- Mask Mode: Three Columns (Terms / Before / After) -->
        <div v-else class="flex-1 flex flex-col overflow-hidden">
          <div
            class="px-6 py-3 bg-amber-50 border-b border-amber-100 flex items-center justify-between"
          >
            <div
              class="text-xs font-bold text-amber-700 uppercase tracking-wider"
            >
              脫敏模式
            </div>
            <button
              type="button"
              @click="isMaskMode = false"
              class="px-3 py-1.5 text-xs font-semibold rounded-md bg-white border border-amber-200 text-amber-700 hover:bg-amber-100 transition"
            >
              返回檢視
            </button>
          </div>

          <div class="flex-1 min-h-0 flex flex-col lg:flex-row overflow-hidden">
            <div
              class="w-full lg:w-[320px] min-h-0 flex flex-col border-b lg:border-b-0 lg:border-r border-gray-200 bg-white"
            >
              <div
                class="px-4 py-2 bg-gray-50 border-b border-gray-100 text-xs font-semibold text-gray-600"
              >
                敏感詞列表
              </div>

              <div class="p-3 border-b border-gray-100 space-y-2">
                <div class="flex items-center gap-2">
                  <input
                    v-model.trim="newSensitiveTerm"
                    type="text"
                    placeholder="新增敏感詞"
                    class="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    @keyup.enter="addSensitiveTerm"
                  />
                  <button
                    type="button"
                    @click="addSensitiveTerm"
                    class="px-3 py-2 text-sm rounded-md bg-white border border-gray-300 hover:bg-gray-50"
                  >
                    新增
                  </button>
                </div>
                <button
                  type="button"
                  @click="suggestSensitiveTermsByAi"
                  :disabled="isSuggestingTerms"
                  class="w-full px-3 py-2 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-400"
                >
                  {{ isSuggestingTerms ? "建議中..." : "AI 建議敏感詞" }}
                </button>
              </div>

              <div class="flex-1 overflow-y-auto p-2">
                <div
                  v-if="sensitiveTerms.length === 0"
                  class="text-sm text-gray-400 px-2 py-3"
                >
                  尚無敏感詞，請手動新增或使用 AI 建議。
                </div>
                <label
                  v-for="term in sensitiveTerms"
                  :key="term"
                  class="flex items-center justify-between gap-2 px-2 py-1.5 rounded hover:bg-gray-50"
                >
                  <span class="inline-flex items-center gap-2 min-w-0 flex-1">
                    <input
                      type="checkbox"
                      :checked="selectedTerms.includes(term)"
                      @change="toggleTermSelection(term, $event)"
                      class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span class="text-sm text-gray-700 truncate">{{
                      term
                    }}</span>
                  </span>
                  <button
                    type="button"
                    @click="removeSensitiveTerm(term)"
                    class="text-xs text-red-500 hover:text-red-700 whitespace-nowrap shrink-0 min-w-[2.5rem] text-right"
                  >
                    刪除
                  </button>
                </label>
              </div>

              <div
                class="px-3 py-2 border-t border-gray-100 text-xs text-gray-500"
              >
                已選擇 {{ selectedTerms.length }} 個詞
              </div>
            </div>

            <div
              class="flex-1 min-h-0 flex flex-col border-b lg:border-b-0 lg:border-r border-gray-200"
            >
              <div
                class="px-6 py-2 bg-gray-50 border-b border-gray-100 text-xs font-semibold text-gray-600"
              >
                脫敏前
              </div>
              <div class="flex-1 overflow-y-auto p-6 bg-white">
                <div
                  v-if="renderedHtml"
                  class="prose prose-sm prose-slate max-w-none"
                >
                  <div v-html="highlightedBeforeHtml"></div>
                </div>
                <div v-else class="text-sm text-gray-400">無可預覽內容</div>
              </div>
            </div>

            <div class="flex-1 min-h-0 flex flex-col">
              <div
                class="px-6 py-2 bg-gray-50 border-b border-gray-100 text-xs font-semibold text-emerald-700"
              >
                脫敏後
              </div>
              <div class="flex-1 overflow-y-auto p-6 bg-white">
                <div
                  v-if="maskedRenderedHtml"
                  class="prose prose-sm prose-slate max-w-none"
                >
                  <div v-html="maskedRenderedHtml"></div>
                </div>
                <div v-else class="text-sm text-gray-400">尚未產生脫敏結果</div>
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
          v-if="isMaskMode"
          type="button"
          @click="applyMaskToCurrentData"
          class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm font-medium transition shadow-sm"
        >
          套用脫敏
        </button>
        <button
          v-if="!isMaskMode"
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
import { watch, reactive, computed, ref } from "vue";
import { useSensitiveMasking } from "~/composables/useSensitiveMasking";
import { authenticatedFetch } from "~/composables/useAppAuth";
import { renderPlanToHtml } from "~/utils/exportToWord";
import JsonSchemaForm from "~/components/data/model/JsonSchemaForm.vue";

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;
const { success, error: errorNotification } = useNotifications();

const props = defineProps({
  show: Boolean,
  dataset: { type: Object, default: () => null },
  isSaving: Boolean,
  allConfigs: { type: Array, required: true },
});

const emit = defineEmits(["close", "save"]);
const AI_REFERENCE_TYPES = ["golden_samples", "synthetic_data"];

const editableData = reactive({
  id: null,
  prompt: "",
  source_type: "synthetic_data",
  final_answer_obj: {},
});

const isMaskMode = ref(false);
const isEditingPrompt = ref(false);
const isEditingContent = ref(false);
const isSuggestingTerms = ref(false);
const newSensitiveTerm = ref("");
const sensitiveTerms = ref([]);
const selectedTerms = ref([]);

const {
  mergeTerms,
  deepClone,
  maskObjectDeep,
  highlightSensitiveTermsInHtml,
  addTermToLists,
  removeTermFromLists,
  toggleSelectionInList,
} = useSensitiveMasking();

function resetEditorState() {
  isMaskMode.value = false;
  isEditingPrompt.value = false;
  isEditingContent.value = false;
  newSensitiveTerm.value = "";
  sensitiveTerms.value = [];
  selectedTerms.value = [];
}

// Resolve the section's json_schema from allConfigs for JsonSchemaForm
const sectionConfig = computed(() => getSectionConfigForDataset());

function getSectionConfigForDataset() {
  if (!props.dataset || !props.allConfigs) return null;
  const { grant_id, template_id, section_id } = props.dataset;
  if (!grant_id || !template_id || !section_id) return null;

  const grant = props.allConfigs.find((g) => g.id === grant_id);
  const template = grant?.templates.find((t) => t.id === template_id);
  return template?.sections.find((s) => s.id === section_id) || null;
}

function renderAnswerObjToHtml(answerObj) {
  const section = getSectionConfigForDataset();
  if (!section) return "";

  try {
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
          content: answerObj || "",
        },
      },
    );
  } catch (error) {
    console.error("HTML Render Error:", error);
    return `<div class="text-red-500 text-sm">渲染錯誤: ${error.message}</div>`;
  }
}

// 當 dataset 改變時更新本地數據
watch(
  () => props.dataset,
  (newVal) => {
    if (newVal) {
      editableData.id = newVal.id;
      editableData.prompt = newVal.prompt || "";
      editableData.source_type = newVal.source_type || "synthetic_data";
      editableData.final_answer_obj = newVal.final_answer
        ? JSON.parse(JSON.stringify(newVal.final_answer))
        : {};
      resetEditorState();
    }
  },
  { immediate: true, deep: true },
);

// 計算渲染後的 HTML
const renderedHtml = computed(() => {
  return renderAnswerObjToHtml(editableData.final_answer_obj);
});

const maskedPreviewObj = computed(() => {
  return maskObjectDeep(editableData.final_answer_obj, selectedTerms.value);
});

const maskedRenderedHtml = computed(() => {
  return renderAnswerObjToHtml(maskedPreviewObj.value);
});

const highlightedBeforeHtml = computed(() => {
  return highlightSensitiveTermsInHtml(renderedHtml.value, selectedTerms.value);
});

function enterMaskMode() {
  isMaskMode.value = true;
}

function addSensitiveTerm() {
  const next = addTermToLists(
    newSensitiveTerm.value,
    sensitiveTerms.value,
    selectedTerms.value,
  );
  sensitiveTerms.value = next.sensitiveTerms;
  selectedTerms.value = next.selectedTerms;
  newSensitiveTerm.value = "";
}

function removeSensitiveTerm(termToRemove) {
  const next = removeTermFromLists(
    termToRemove,
    sensitiveTerms.value,
    selectedTerms.value,
  );
  sensitiveTerms.value = next.sensitiveTerms;
  selectedTerms.value = next.selectedTerms;
}

function toggleTermSelection(term, event) {
  const checked = event?.target?.checked;
  selectedTerms.value = toggleSelectionInList(
    term,
    Boolean(checked),
    selectedTerms.value,
  );
}

async function suggestSensitiveTermsByAi() {
  isSuggestingTerms.value = true;
  try {
    const response = await authenticatedFetch(
      `${API_BASE_URL}/datasets/sensitive-terms/suggest`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: editableData.prompt,
          final_answer: editableData.final_answer_obj,
          existing_terms: sensitiveTerms.value,
        }),
      },
    );

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "AI 建議失敗");
    }

    const data = await response.json();
    const suggested = Array.isArray(data.terms) ? data.terms : [];
    sensitiveTerms.value = mergeTerms(sensitiveTerms.value, suggested);
    selectedTerms.value = mergeTerms(selectedTerms.value, suggested);
    success(`已加入 ${suggested.length} 個 AI 建議詞`);
  } catch (error) {
    errorNotification(`AI 建議失敗: ${error.message}`);
  } finally {
    isSuggestingTerms.value = false;
  }
}

function applyMaskToCurrentData() {
  if (selectedTerms.value.length === 0) {
    errorNotification("請至少勾選一個敏感詞");
    return;
  }
  editableData.final_answer_obj = deepClone(maskedPreviewObj.value);
  isMaskMode.value = false;
  success("已套用脫敏結果");
}

function handleSave() {
  emit("save", {
    id: editableData.id,
    prompt: editableData.prompt,
    final_answer: editableData.final_answer_obj,
    source_type: editableData.source_type,
  });
}

// 判斷目前是否屬於「作為 AI 參考」的類別
const isAiReference = computed(() => {
  return AI_REFERENCE_TYPES.includes(editableData.source_type);
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

function toggleGoldenSample(event) {
  const checked = event?.target?.checked;
  editableData.source_type = checked ? "golden_samples" : "synthetic_data";
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

.prose :deep(mark.mask-highlight) {
  background-color: #fde68a;
  color: #7c2d12;
  padding: 0 0.1em;
  border-radius: 0.2em;
}
</style>
