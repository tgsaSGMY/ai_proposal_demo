<!-- 编辑器方案输出面板组件：显示编辑方案的最终输出 -->
<template>
  <div
    class="bg-white shadow-xl rounded-2xl p-4 sm:p-6 md:p-8 h-full flex flex-col"
  >
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-6 mb-4 sm:mb-6">
      <div>
        <h2 class="text-lg sm:text-2xl font-bold text-gray-800 mb-3">
          生成結果
        </h2>
        <!-- 版本選擇 Dropdown -->
        <div
          v-if="props.savedPlanVersions && props.savedPlanVersions.length >= 1"
          class="max-w-xs"
        >
          <label
            class="block text-xs sm:text-sm font-medium text-gray-700 mb-2"
          >
            選擇版本:
          </label>
          <select
            v-model.number="selectedVersionIndex"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-white focus:border-rose-500 focus:outline-none focus:ring-1 focus:ring-rose-500"
          >
            <option
              v-for="(version, idx) in props.savedPlanVersions"
              :key="idx"
              :value="idx"
              class="text-gray-700"
            >
              {{ version.title }} ({{ version.timestamp }})
            </option>
          </select>
        </div>
      </div>
      <button
        @click="handleExportToWord"
        class="flex items-center justify-center gap-2 bg-rose-600 text-white font-medium sm:py-2.5 sm:px-4 rounded-xl shadow-sm hover:bg-rose-700 active:scale-[0.98] transition-all duration-200 text-sm sm:text-base h-fit"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 4v16m8-8H4"
          />
        </svg>
        導出為 Word
      </button>
    </div>

    <div
      v-if="isLoading"
      class="flex-grow space-y-6 sm:space-y-8 overflow-y-auto pr-1 sm:pr-2 animate-pulse"
    >
      <div v-for="i in 3" :key="i" class="space-y-2 sm:space-y-4">
        <div class="h-5 sm:h-6 bg-gray-200 rounded w-1/2 sm:w-1/3"></div>
        <div class="h-10 sm:h-16 bg-gray-200 rounded w-full"></div>
      </div>
    </div>

    <div
      v-if="!sections || sections.length === 0"
      class="flex-grow flex items-center justify-center text-gray-500 text-sm sm:text-base"
    >
      請在左側選擇模板以查看章節。
    </div>
    <div
      v-else
      class="flex-grow space-y-6 sm:space-y-8 overflow-y-auto pr-1 sm:pr-2"
    >
      <div v-for="section in sections" :key="section.id">
        <div
          class="p-3 sm:p-4 border-l-4 border-rose-400 bg-rose-50 rounded-r-lg"
        >
          <h3 class="text-base sm:text-lg font-semibold text-gray-800">
            {{ section.name }}
          </h3>
        </div>

        <div class="mt-3 sm:mt-4 pl-1 sm:pl-2">
          <!-- 錯誤狀態顯示 -->
          <div
            v-if="getSectionError(section.id)"
            class="text-red-600 bg-red-50 p-2 sm:p-3 rounded-lg text-sm sm:text-base"
          >
            <strong>錯誤:</strong> {{ getSectionError(section.id) }}
          </div>
          <!-- 成功狀態，渲染動態表單 -->
          <JsonSchemaForm
            v-else-if="section.json_schema && getSectionContent(section.id)"
            :schema="section.json_schema"
            :modelValue="getSectionContent(section.id)"
            @update:modelValue="updateSectionContent(section.id, $event)"
            readonly
          />
          <!-- 等待生成狀態 -->
          <div
            v-else
            class="text-gray-400 italic p-2 sm:p-3 text-sm sm:text-base"
          >
            等待生成或內容無效...
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import JsonSchemaForm from "~/components/JsonSchemaForm.vue";
import mammoth from "mammoth";
import { exportPlanToWord } from "@/utils/exportToWord";
import { useLoading } from "~/composables/useLoading";
import { useNotifications } from "~/composables/useNotifications";
import { useCurrentUser } from "~/composables/useCurrentUser";

const props = defineProps({
  planContent: { type: Object, required: true },
  sections: { type: Array, default: () => [] },
  mode: { type: String, required: true },
  isLoading: { type: Boolean, default: false },
  grantId: { type: String, required: false },
  templateId: { type: String, required: false },
  savedPlanVersions: { type: Array, default: () => [] },
  projectCreatedAt: { type: String, required: false },
});

const fileInput = ref(null);
const selectedVersionIndex = ref(-1); // -1表示最新版本
const { error: errorNotification } = useNotifications();
const { isLoading } = useLoading();
const { userId: currentUserId, refreshUser } = useCurrentUser();

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

let pdfjsLib = null;
onMounted(async () => {
  await refreshUser();
  try {
    // 動態導入模塊
    const pdfjsModule = await import("pdfjs-dist/build/pdf");
    pdfjsLib = pdfjsModule;
    // 設置 worker 路徑
    pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
  } catch (e) {
    console.error("Failed to load pdf.js library:", e);
  }

  // 初始化时选择最新版本
  if (props.savedPlanVersions && props.savedPlanVersions.length > 0) {
    selectedVersionIndex.value = props.savedPlanVersions.length - 1;
  } else {
    selectedVersionIndex.value = -1;
  }
});

// 监听 savedPlanVersions 变化，自动选择最新版本
watch(
  () => props.savedPlanVersions,
  (newVersions) => {
    if (newVersions && newVersions.length > 0) {
      // 始终选择最新版本（最后一个）
      selectedVersionIndex.value = newVersions.length - 1;
    } else {
      selectedVersionIndex.value = -1;
    }
  },
  { deep: true },
);

const emit = defineEmits([
  "update:content",
  "generateUserInput",
  "autoFillComplete",
]);

async function getUserIdOrNotify() {
  const userId = currentUserId.value || (await refreshUser());
  if (!userId) {
    errorNotification("無法取得使用者資訊，請重新登入後再試。");
  }
  return userId;
}

// 從選定版本獲取指定章節的內容（唯讀模式）
function getSectionContent(sectionId) {
  let content;

  // 从选定的版本获取内容
  const version = props.savedPlanVersions[selectedVersionIndex.value];
  if (version?.data) {
    content = version.data[sectionId]?.content;
  }

  // 確保返回的是一個對象
  return typeof content === "object" && content !== null ? content : {};
}

// 獲取指定章節的錯誤信息
function getSectionError(sectionId) {
  return props.planContent[sectionId]?.error;
}
// 導出當前選定版本為Word文檔

async function handleExportToWord() {
  if (!props.sections.length) {
    errorNotification("請先選擇模板");
    return;
  }
  await exportPlanToWord(
    props.sections,
    props.savedPlanVersions[selectedVersionIndex.value]
      ? props.savedPlanVersions[selectedVersionIndex.value].data
      : "",
    props.grantId,
    props.templateId,
    undefined,
    props.projectCreatedAt || undefined,
  );
}
// 禁止所有编辑
function updateSectionContent(sectionId, newContentObject) {
  errorNotification("已保存版本不能編輯，請返回當前版本進行修改");
  return;
}
// 觸發文件選擇對話框用於自動填充

function handleFileLoadClick() {
  if (props.sections.length === 0) {
    errorNotification("請先在左側選擇一個模板，以便我們知道要填充哪些欄位。");
    return;
  }
  fileInput.value.click();
}

// 處理選擇的檔案
async function handleFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  const { show: showLoading, hide: hideLoading } = useLoading();
  showLoading("正在從 Word 檔案中提取內容...", true);
  try {
    const extractedText = await extractTextFromFile(file);
    const userId = await getUserIdOrNotify();
    if (!userId) {
      return;
    }

    // 準備傳送給後端的資料
    const payload = {
      document_text: extractedText,
      sections: props.sections.map((s) => ({
        section_id: s.id,
        section_name: s.name,
        json_schema: s.json_schema,
      })),
      user_id: userId,
    };

    const filledContent = await callAutoFillApi(payload);

    // 觸發事件，讓父元件更新整個 planContent
    emit("autoFillComplete", filledContent);
  } catch (error) {
    console.error("處理檔案時發生錯誤:", error);
    errorNotification(`處理檔案失敗: ${error.message}`);
  } finally {
    hideLoading();
    event.target.value = null; // 重設 input，以便能再次選擇同一個檔案
  }
}

// 調用後端自動填充 API
async function callAutoFillApi(payload) {
  const response = await fetch(`${API_BASE_URL}/autofill_from_document`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "後端處理失敗");
  }
  return await response.json();
}

// 從 Word 或 PDF 檔案中提取文字的輔助函數
async function extractTextFromFile(file) {
  if (file.type === "application/pdf" && !pdfjsLib) {
    throw new Error(
      "PDF library is not loaded yet. Please try again in a moment.",
    );
  }
  if (file.type === "application/pdf") {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
    let textContent = "";
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const text = await page.getTextContent();
      textContent += text.items.map((item) => item.str).join(" ") + "\n\n"; // 頁之間加換行
    }
    return textContent;
  } else if (
    file.type ===
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  ) {
    const arrayBuffer = await file.arrayBuffer();
    const result = await mammoth.extractRawText({ arrayBuffer });
    return result.value;
  } else {
    throw new Error("不支援的檔案格式，請選擇 Word (.docx) 或 PDF 檔案。");
  }
}
</script>
