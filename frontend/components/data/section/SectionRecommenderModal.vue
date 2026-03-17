<!-- 章节推荐模态帐组件：为用户推荐应该填写的章节 （AI推薦） -->
<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
  >
    <div
      class="w-[80vw] h-[80vh] max-w-6xl bg-white rounded-2xl shadow-2xl p-6 sm:p-8 flex flex-col"
    >
      <!-- Header -->
      <div class="flex items-center justify-between mb-6 flex-shrink-0">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">章節智能推薦</h2>
          <p class="text-sm text-gray-500 mt-1">
            上傳 Word 文件，AI 將分析您的內容並建議應該如何調整章節和欄位結構
          </p>
        </div>
        <button
          @click="closeModal"
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
      </div>

      <!-- Main Content: Two-column layout -->
      <div class="grid grid-cols-2 gap-6 flex-1 mb-6 min-h-0">
        <!-- Left Column: File Upload & Current Schema -->
        <div class="flex flex-col gap-6 h-full min-h-0">
          <!-- File Upload -->
          <div class="flex-shrink-0">
            <label class="block text-sm font-semibold text-gray-700 mb-3">
              選擇 Word 檔案
            </label>
            <div
              @click="fileInputRef?.click()"
              class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-indigo-500 hover:bg-indigo-50 transition"
            >
              <input
                ref="fileInputRef"
                type="file"
                accept=".doc,.docx"
                hidden
                @change="handleFileSelect"
              />
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-10 w-10 mx-auto text-gray-400 mb-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <p class="text-gray-700 font-medium text-sm">
                {{ selectedFile ? selectedFile.name : "點擊上傳或拖入" }}
              </p>
              <p class="text-xs text-gray-500 mt-1">支援 .doc 和 .docx</p>
            </div>
          </div>

          <!-- Current Schema Info -->
          <div
            class="bg-gray-50 rounded-lg p-4 flex-1 overflow-hidden flex flex-col"
          >
            <h3 class="text-sm font-semibold text-gray-700 mb-3">
              當前 Schema 結構
            </h3>
            <div class="text-xs text-gray-600 space-y-1 overflow-y-auto flex-1">
              <div
                v-for="section in currentSections"
                :key="section.id || section.section_key"
                class="mb-2"
              >
                <span class="font-semibold text-gray-700">{{
                  section.title
                }}</span>
                <div class="ml-2 text-gray-500">
                  <span
                    v-for="field in section.fields || section.properties || []"
                    :key="field.field_key || field.key || field.title"
                    class="block text-xs mb-1"
                  >
                    <span class="font-medium text-gray-600"
                      >• {{ field.title }}</span
                    >
                    <span
                      v-if="field.description"
                      class="block text-[11px] text-gray-500 ml-3"
                    >
                      說明：{{ field.description }}
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Loading State & Recommendations -->
        <div
          class="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 flex flex-col items-center justify-center overflow-hidden h-full min-h-0"
        >
          <!-- Loading State -->
          <div
            v-if="isLoading"
            class="text-center py-8 w-full flex flex-col items-center justify-center"
          >
            <div class="inline-block animate-spin mb-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-10 w-10 text-indigo-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </div>
            <p class="text-gray-600 font-medium">分析中...</p>
          </div>

          <!-- Recommendations -->
          <div
            v-else-if="recommendations"
            class="w-full h-full bg-blue-50 border border-blue-200 rounded-lg px-4 pb-4 overflow-y-auto"
          >
            <h3
              class="pt-2 text-sm font-semibold text-blue-900 mb-3 sticky top-0 bg-blue-50 pb-2"
            >
              AI 建議
            </h3>
            <div
              class="text-sm text-blue-800 whitespace-pre-wrap mt-2"
              v-html="formatRecommendations(recommendations || '')"
            ></div>
          </div>

          <!-- Empty State -->
          <div v-else class="text-center text-gray-500">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-12 w-12 mx-auto text-gray-400 mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p class="text-sm font-medium">選擇檔案並點擊分析</p>
            <p class="text-xs text-gray-400 mt-1">結果將顯示在此</p>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-3 justify-end flex-shrink-0">
        <button
          @click="closeModal"
          class="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 transition"
        >
          取消
        </button>
        <button
          @click="analyzeFile"
          :disabled="!selectedFile || isLoading"
          class="px-4 py-2 text-sm font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          分析內容
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useNotifications } from "~/composables/useNotifications";
import { extractTextFromWord } from "~/utils/wordImport";

type FieldDefinition = {
  key?: string;
  field_key?: string;
  title: string;
  description?: string;
};

type SectionDefinition = {
  id?: string;
  section_key?: string;
  title: string;
  fields?: FieldDefinition[];
  properties?: FieldDefinition[];
};

interface Props {
  modelValue: boolean;
  currentSections: SectionDefinition[];
}

interface Emits {
  (e: "update:modelValue", value: boolean): void;
  (e: "close"): void;
}

const props = defineProps<Props>();

const emit = defineEmits<Emits>();

const fileInputRef = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const isLoading = ref(false);
const recommendations = ref<string | null>(null);

const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const { success, error: errorNotification } = useNotifications();

// 将Markdown格式的**加粗**转换为HTML的<strong>标签
function formatRecommendations(text: string): string {
  return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
}

// 关闭模态框并重置所有状态
function closeModal() {
  emit("update:modelValue", false);
  emit("close");
  selectedFile.value = null;
  recommendations.value = null;
}

// 处理用户选择的Word文件
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  const files = target.files;
  if (files && files.length > 0 && files[0]) {
    selectedFile.value = files[0];
    recommendations.value = null;
  }
}

// 解析上传的Word文件内容，调用后端API获取AI建议
async function analyzeFile() {
  if (!selectedFile.value) {
    errorNotification("請先選擇檔案");
    return;
  }

  isLoading.value = true;
  try {
    const documentText = await extractTextFromWord(selectedFile.value);
    if (!documentText || !documentText.trim()) {
      throw new Error("無法從檔案讀取到文字內容");
    }

    const schemaInfo = {
      sections: (props.currentSections || []).map((section) => ({
        key: section.section_key || section.id || "",
        title: section.title,
        fields: (section.fields || section.properties || []).map((field) => ({
          key: field.field_key || field.key || "",
          title: field.title,
          description: field.description || "",
        })),
      })),
    };

    const response = await fetch(`${API_BASE_URL}/section-recommender`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        document_text: documentText,
        schema_info: schemaInfo,
      }),
    });

    if (!response.ok) {
      throw new Error(`API 錯誤: ${response.status}`);
    }

    const data = await response.json();
    recommendations.value = data.recommendations || "無法生成建議";
    success("分析完成");
  } catch (error: any) {
    console.error("Failed to analyze file", error);
    errorNotification(error?.message || "分析失敗，請稍後重試");
  } finally {
    isLoading.value = false;
  }
}
</script>
