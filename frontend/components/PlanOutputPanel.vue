<template>
  <div class="bg-white shadow-xl rounded-2xl p-4 sm:p-6 md:p-8 h-full flex flex-col">
    <h2 class="text-lg sm:text-2xl font-bold text-gray-800 mb-4">生成結果 (可編輯)</h2>
    <div class="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
      <!-- 從文件載入 -->
      <button
        v-if="mode === 'golden'"
        @click="handleFileLoadClick"
        :disabled="isLoading"
        class="flex items-center justify-center gap-2 bg-blue-600 text-white font-medium py-2 px-3 sm:py-2.5 sm:px-4 rounded-xl shadow-sm hover:bg-blue-700 active:scale-[0.98] transition-all duration-200 disabled:bg-blue-300 disabled:cursor-not-allowed disabled:shadow-none text-sm sm:text-base"
      >
        <svg
          v-if="!isLoading"
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
        {{ isLoading ? "處理中..." : "從文件載入" }}
      </button>

      <!-- 反推 User Input -->
      <button
        v-if="mode === 'golden'"
        @click="$emit('generateUserInput')"
        class="flex items-center justify-center gap-2 bg-emerald-600 text-white font-medium py-2 px-3 sm:py-2.5 sm:px-4 rounded-xl shadow-sm hover:bg-emerald-700 active:scale-[0.98] transition-all duration-200 text-sm sm:text-base"
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
            d="M4 4v6h6M20 20v-6h-6"
          />
        </svg>
        反推 User Input
      </button>

      <!-- 隱藏文件輸入 -->
      <input
        type="file"
        ref="fileInput"
        @change="handleFileSelected"
        class="hidden"
        accept=".docx,.pdf"
      />

      <!-- 導出 Word -->
      <button
        @click="handleExportToWord"
        class="flex items-center justify-center gap-2 bg-purple-600 text-white font-medium py-2 px-3 sm:py-2.5 sm:px-4 rounded-xl shadow-sm hover:bg-purple-700 active:scale-[0.98] transition-all duration-200 text-sm sm:text-base"
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
  <div v-else class="flex-grow space-y-6 sm:space-y-8 overflow-y-auto pr-1 sm:pr-2">
      <div v-for="section in sections" :key="section.id">
        <div class="p-3 sm:p-4 border-l-4 border-indigo-500 bg-indigo-50 rounded-r-lg">
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
          />
          <!-- 等待生成狀態 -->
          <div v-else class="text-gray-400 italic p-2 sm:p-3 text-sm sm:text-base">
            等待生成或內容無效...
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import JsonSchemaForm from "./JsonSchemaForm.vue";
import mammoth from "mammoth";
import { exportPlanToWord } from "@/utils/exportToWord";

const props = defineProps({
  planContent: { type: Object, required: true },
  sections: { type: Array, default: () => [] },
  mode: { type: String, required: true },
  isLoading: { type: Boolean, default: false },
});

const fileInput = ref(null);
import { useLoading } from "~/composables/useLoading";
import { useNotifications } from "~/composables/useNotifications";
const { error: errorNotification } = useNotifications();
const { isLoading } = useLoading();

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

let pdfjsLib = null;
onMounted(async () => {
  try {
    // 動態導入模塊
    const pdfjsModule = await import("pdfjs-dist/build/pdf");
    pdfjsLib = pdfjsModule;
    // 設置 worker 路徑
    pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
  } catch (e) {
    console.error("Failed to load pdf.js library:", e);
  }
});

const emit = defineEmits([
  "update:content",
  "generateUserInput",
  "autoFillComplete",
]);

// 直接返回對象
function getSectionContent(sectionId) {
  const content = props.planContent[sectionId]?.content;
  // 確保返回的是一個對象
  return typeof content === "object" && content !== null ? content : {};
}

function getSectionError(sectionId) {
  return props.planContent[sectionId]?.error;
}

async function handleExportToWord() {
  if (!props.sections.length) {
    errorNotification("請先選擇模板");
    return;
  }
  await exportPlanToWord(props.sections, props.planContent);
}

// 接收對象
function updateSectionContent(sectionId, newContentObject) {
  emit("update:content", { sectionId, content: newContentObject });
}

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

  isLoading.value = true;
  try {
    const extractedText = await extractTextFromFile(file);

    // 準備傳送給後端的資料
    const payload = {
      document_text: extractedText,
      sections: props.sections.map((s) => ({
        section_id: s.id,
        section_name: s.name,
        json_schema: s.json_schema,
      })),
    };

    const filledContent = await callAutoFillApi(payload);

    // 觸發事件，讓父元件更新整個 planContent
    emit("autoFillComplete", filledContent);
  } catch (error) {
    console.error("處理檔案時發生錯誤:", error);
    errorNotification(`處理檔案失敗: ${error.message}`);
  } finally {
    isLoading.value = false;
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
      "PDF library is not loaded yet. Please try again in a moment."
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
