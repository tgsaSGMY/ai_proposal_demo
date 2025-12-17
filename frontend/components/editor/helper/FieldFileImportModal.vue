<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="isOpenModel"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 py-6 overflow-y-auto"
        @click.self="handleClose"
      >
        <div
          class="w-full max-w-4xl bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden flex flex-col my-8"
          style="max-height: calc(100vh - 4rem)"
        >
          <header
            class="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5 bg-gradient-to-r from-rose-50 to-amber-50"
          >
            <div class="space-y-1">
              <p
                class="text-xs font-semibold tracking-widest text-rose-500 uppercase"
              >
                匯入檔案輔助填寫
              </p>
              <h2 class="text-2xl font-bold text-slate-900">
                {{ fieldTitle }}
              </h2>
              <p class="text-sm text-slate-600 whitespace-pre-line">
                {{ fieldDescription || "此欄位將根據檔案內容補強敘述" }}
              </p>
            </div>
            <button
              type="button"
              class="text-slate-500 hover:text-slate-700 transition"
              @click="handleClose"
            >
              <span class="sr-only">關閉</span>
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

          <div class="flex-1 overflow-y-auto px-6 py-6 space-y-6">
            <section
              class="rounded-2xl border-2 border-dashed"
              :class="[
                dragActive
                  ? 'border-rose-400 bg-rose-50/60'
                  : 'border-slate-200 bg-slate-50/60',
              ]"
              @dragover.prevent="handleDragOver"
              @dragleave.prevent="handleDragLeave"
              @drop.prevent="handleDrop"
            >
              <div
                class="flex flex-col items-center justify-center gap-4 px-6 py-8 text-center"
              >
                <div class="p-3 rounded-full bg-white shadow-sm text-rose-500">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-7 w-7"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="1.5"
                      d="M3 15.75A4.5 4.5 0 007.5 20.25h9A4.5 4.5 0 0021 15.75 4.5 4.5 0 0016.5 11.25h-.878a2.25 2.25 0 01-1.591-.659l-2.12-2.121a2.25 2.25 0 00-1.591-.659H7.5A4.5 4.5 0 003 11.25"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="1.5"
                      d="M9 15l3-3 3 3m-3-3v6"
                    />
                  </svg>
                </div>
                <div>
                  <p class="text-base font-semibold text-slate-900">
                    拖曳 PDF / TXT 檔案至此
                  </p>
                  <p class="text-sm text-slate-500">
                    或
                    <button
                      type="button"
                      class="text-rose-600 font-semibold underline underline-offset-4"
                      @click="triggerFilePicker"
                    >
                      探索檔案
                    </button>
                    從裝置上傳（最多 5 個檔案）
                  </p>
                </div>
                <p class="text-xs text-slate-500">
                  支援含圖片的檔案，會自動 OCR（最大
                  20MB）。資料僅用於本次分析，完成後即刪除。
                </p>
                <input
                  ref="fileInputRef"
                  type="file"
                  class="hidden"
                  accept=".pdf,.txt"
                  multiple
                  @change="handleFileChange"
                />
                <div
                  v-if="selectedFiles.length > 0"
                  class="w-full space-y-2"
                >
                  <div
                    v-for="(file, idx) in selectedFiles"
                    :key="idx"
                    class="rounded-xl border border-slate-200 bg-white px-4 py-3 text-left shadow-sm flex items-start justify-between"
                  >
                    <div>
                      <p class="text-sm font-semibold text-slate-800">
                        {{ file.name }}
                      </p>
                      <p class="text-xs text-slate-500">
                        {{ formatFileSize(file.size) }} ·
                        {{ file.type || "未知類型" }}
                      </p>
                    </div>
                    <button
                      type="button"
                      class="text-xs text-rose-500 hover:text-rose-600 flex-shrink-0"
                      @click="removeFile(idx)"
                    >
                      移除
                    </button>
                  </div>
                  <button
                    type="button"
                    class="mt-2 text-xs text-slate-600 hover:text-slate-700"
                    @click="clearAllFiles"
                  >
                    清除全部
                  </button>
                </div>
              </div>
            </section>

            <div
              class="flex flex-col gap-4 rounded-2xl border border-slate-100 bg-white/60 px-4 py-4"
            >
              <div>
                <p class="text-xs font-semibold text-slate-500 uppercase">
                  子欄位標籤
                </p>
                <p class="text-base font-semibold text-slate-900">
                  {{ subFieldLabel || fieldTitle }}
                </p>
              </div>
              <div>
                <p class="text-xs font-semibold text-slate-500 uppercase">
                  原始輸入
                </p>
                <p
                  class="mt-1 rounded-xl bg-slate-100/70 p-3 text-sm text-slate-700 whitespace-pre-wrap min-h-[64px]"
                >
                  {{ subFieldValue || "目前尚未填寫" }}
                </p>
              </div>
            </div>

            <section v-if="analysisResult" class="space-y-4">
              <div
                class="rounded-2xl border border-rose-100 bg-white/80 p-4 shadow"
              >
                <div class="flex items-center justify-between">
                  <p class="text-xs font-semibold text-rose-500 uppercase">
                    新的欄位內容
                  </p>
                  <span class="text-xs text-slate-400">AI 會保留原始輸入</span>
                </div>
                <textarea
                  v-model="editableValue"
                  rows="8"
                  class="mt-3 w-full rounded-xl border border-rose-200 bg-rose-50/30 p-3 text-sm text-slate-800 focus:border-rose-400 focus:ring-2 focus:ring-rose-200"
                ></textarea>
              </div>
            </section>

            <p v-if="errorMessage" class="text-sm text-rose-600">
              {{ errorMessage }}
            </p>
          </div>

          <footer
            class="flex flex-col gap-3 border-t border-slate-100 bg-white px-6 py-5 sm:flex-row sm:items-center sm:justify-between"
          >
            <div class="text-xs text-slate-500">
              完成分析後可再微調內容，確認後會覆蓋原欄位數值。
            </div>
            <div class="flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                class="rounded-xl border border-slate-300 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                @click="handleClose"
              >
                取消
              </button>
              <button
                type="button"
                class="rounded-xl bg-slate-900 px-5 py-2 text-sm font-semibold text-white shadow-sm disabled:cursor-not-allowed disabled:opacity-50"
                :disabled="selectedFiles.length === 0 || isAnalyzing"
                @click="analyzeFile"
              >
                <span v-if="isAnalyzing">分析中...</span>
                <span v-else>分析檔案</span>
              </button>
              <button
                type="button"
                class="rounded-xl bg-gradient-to-r from-rose-500 to-amber-500 px-6 py-2 text-sm font-semibold text-white shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="!canConfirm"
                @click="emitConfirm"
              >
                套用結果
              </button>
            </div>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useNotifications } from "~/composables/useNotifications";

const props = defineProps({
  fieldTitle: { type: String, default: "" },
  fieldDescription: { type: String, default: "" },
  subFieldLabel: { type: String, default: "" },
  subFieldValue: { type: String, default: "" },
});

const emit = defineEmits<{ (e: "confirm", value: string): void }>();

const isOpenModel = defineModel("isOpen", { type: Boolean, default: false });

const { success: notifySuccess, error: notifyError } = useNotifications();
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const ACCEPTED_EXTENSIONS = ["pdf", "txt"];
const MAX_SIZE_BYTES = 20 * 1024 * 1024;

const fileInputRef = ref<HTMLInputElement | null>(null);
const selectedFiles = ref<File[]>([]);
const dragActive = ref(false);
const isAnalyzing = ref(false);
const analysisResult = ref<{
  enhancedValue: string;
} | null>(null);
const editableValue = ref("");
const errorMessage = ref("");

watch(
  () => isOpenModel.value,
  (isOpen) => {
    if (isOpen) {
      editableValue.value = props.subFieldValue || "";
      errorMessage.value = "";
    } else {
      resetState();
    }
  }
);

watch(
  () => props.subFieldValue,
  (val) => {
    if (isOpenModel.value && !analysisResult.value) {
      editableValue.value = val || "";
    }
  }
);

const formattedFileSize = computed(() => {
  const total = selectedFiles.value.reduce((sum, f) => sum + f.size, 0);
  if (total === 0) return "";
  if (total >= 1024 * 1024) {
    return `${(total / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${(total / 1024).toFixed(1)} KB`;
});

const canConfirm = computed(() => {
  return Boolean(
    analysisResult.value && editableValue.value.trim() && !isAnalyzing.value
  );
});

function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function resetState() {
  selectedFiles.value = [];
  analysisResult.value = null;
  editableValue.value = "";
  errorMessage.value = "";
  dragActive.value = false;
}

function triggerFilePicker() {
  fileInputRef.value?.click();
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement | null;
  const files = target?.files;
  if (files) {
    addFiles(Array.from(files));
  }
  if (target) {
    target.value = "";
  }
}

function handleDragOver() {
  dragActive.value = true;
}

function handleDragLeave() {
  dragActive.value = false;
}

function handleDrop(event: DragEvent) {
  dragActive.value = false;
  const files = event.dataTransfer?.files;
  if (files) {
    addFiles(Array.from(files));
  }
}

function addFiles(files: File[]) {
  if (selectedFiles.value.length + files.length > 5) {
    notifyError("最多只能選擇 5 個檔案。");
    return;
  }

  const newFiles = files.filter((file) => {
    const ext = file.name.split(".").pop()?.toLowerCase() || "";
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      notifyError(`檔案 ${file.name} 不支援的格式（僅支援 PDF / TXT）。`);
      return false;
    }
    if (file.size > MAX_SIZE_BYTES) {
      notifyError(`檔案 ${file.name} 過大，請控制在 20MB 以內。`);
      return false;
    }
    return true;
  });

  selectedFiles.value.push(...newFiles);
  analysisResult.value = null;
  editableValue.value = props.subFieldValue || "";
  errorMessage.value = "";
}

function removeFile(idx: number) {
  selectedFiles.value.splice(idx, 1);
}

function clearAllFiles() {
  selectedFiles.value = [];
  analysisResult.value = null;
}

async function analyzeFile() {
  if (selectedFiles.value.length === 0) {
    notifyError("請先選擇要分析的檔案。");
    return;
  }

  isAnalyzing.value = true;
  errorMessage.value = "";

  const formData = new FormData();
  selectedFiles.value.forEach((file) => {
    formData.append("files", file);
  });
  formData.append("field_title", props.fieldTitle);
  formData.append("field_description", props.fieldDescription || "");
  formData.append("subfield_label", props.subFieldLabel || "");
  formData.append("current_value", props.subFieldValue || "");

  try {
    const response = await fetch(`${API_BASE_URL}/field_file_analysis`, {
      method: "POST",
      body: formData,
    });

    const payload = await response.json().catch(() => null);

    if (!response.ok) {
      const detail = payload?.detail || "分析服務暫時無法使用";
      throw new Error(detail);
    }

    analysisResult.value = {
      enhancedValue: payload?.value || props.subFieldValue || "",
    };
    editableValue.value = analysisResult.value.enhancedValue;
    notifySuccess(`檔案分析完成（已分析 ${selectedFiles.value.length} 個檔案）。`);
  } catch (error) {
    const message = error instanceof Error ? error.message : "分析失敗";
    errorMessage.value = message;
    notifyError(`分析失敗：${message}`);
  } finally {
    isAnalyzing.value = false;
  }
}

function emitConfirm() {
  if (!analysisResult.value || !editableValue.value.trim()) {
    return;
  }
  emit("confirm", editableValue.value.trim());
  handleClose();
}

function handleClose() {
  isOpenModel.value = false;
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
