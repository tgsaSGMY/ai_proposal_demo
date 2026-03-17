<!-- 模板表單彈窗 -->
<template>
  <div
    v-if="isVisible"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40"
  >
    <section
      class="bg-white rounded-2xl shadow p-5 sm:p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto space-y-4"
    >
      <div class="flex flex-wrap items-center justify-between gap-3 mb-2">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">
            {{ templateFormMode === "create" ? "新增模板" : "編輯模板" }}
          </h2>
          <p class="text-xs text-slate-500">設定模板基本資訊與視覺元素</p>
        </div>
        <button
          type="button"
          class="text-2xl font-bold text-slate-400 hover:text-slate-600"
          @click="emit('cancel')"
        >
          ×
        </button>
      </div>
      <form class="grid gap-4 md:grid-cols-2" @submit.prevent="emit('submit')">
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700">隸屬主題</span>
          <select
            v-model="templateForm.grant_id"
            :disabled="templateFormMode === 'edit'"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400 disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed"
          >
            <option value="" disabled>請先選擇</option>
            <option
              v-for="option in grantOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }} ({{ option.value }})
            </option>
          </select>
        </label>
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700"
            >模板ID（只能包含英文字母、數字和底線）</span
          >
          <input
            v-model="templateForm.id"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="例如：imdp"
            :readonly="templateFormMode === 'edit'"
          />
        </label>
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700">模板名稱</span>
          <input
            v-model="templateForm.name"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="例如：IMDP"
          />
        </label>
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700">副標</span>
          <input
            v-model="templateForm.subtitle"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="簡短描述"
          />
        </label>
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700">付費方案限制</span>
          <select
            v-model="templateForm.requires_paid_plan"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
          >
            <option :value="true">需要付費方案</option>
            <option :value="false">不需要</option>
          </select>
        </label>
        <label class="block space-y-1">
          <span class="text-sm font-medium text-slate-700">送件截止日期</span>
          <input
            v-model="templateForm.submission_deadline"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="例如：2026/12/31"
          />
        </label>
        <label class="block space-y-1 md:col-span-2">
          <span class="text-sm font-medium text-slate-700">最高補助額</span>
          <input
            v-model="templateForm.subsidy_amount"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="例如：最高新台幣 200 萬元"
          />
        </label>
        <label class="block space-y-1 md:col-span-2">
          <span class="text-sm font-medium text-slate-700">描述</span>
          <textarea
            v-model="templateForm.description"
            rows="3"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
            placeholder="補助計畫說明"
          ></textarea>
        </label>
        <div class="md:col-span-2 space-y-2">
          <div
            class="flex items-center justify-between text-sm font-medium text-slate-700"
          >
            <span>Logo 圖片</span>
            <span class="text-xs font-normal text-slate-400">
              支援 PNG / JPG，建議 1MB 內
            </span>
          </div>
          <div
            class="relative rounded-2xl border-2 border-dashed px-4 py-6 text-center transition-colors"
            :class="{
              'border-rose-300 bg-rose-50/70': isDraggingLogo,
              'border-slate-200 bg-slate-50': !isDraggingLogo,
            }"
            @dragover.prevent="handleLogoDrag(true)"
            @dragleave.prevent="handleLogoDrag(false)"
            @drop.prevent="onLogoDrop"
          >
            <input
              ref="fileInputRef"
              type="file"
              accept="image/png,image/jpeg"
              class="hidden"
              @change="onLogoFileChange"
            />
            <template v-if="true">
              <div
                v-if="localLogoPreview"
                class="mx-auto mb-4 flex h-24 w-24 items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-white"
              >
                <img
                  v-if="activeLogoPreview"
                  :src="activeLogoPreview"
                  alt="Logo 預覽"
                  class="h-full w-full object-contain"
                  loading="lazy"
                />
              </div>
              <p class="text-xs text-slate-500">
                拖拽檔案到此處，或
                <button
                  type="button"
                  class="font-semibold text-rose-500 underline-offset-2 hover:underline"
                  @click="openFilePicker"
                >
                  選擇檔案
                </button>
                ，僅接受 PNG / JPG / JPEG
              </p>
              <p class="pt-2 text-[11px] text-slate-400">
                建議使用透明背景、500px 以內的小圖示，以維持載入速度。
              </p>
            </template>
          </div>
        </div>
        <label class="block space-y-2 md:col-span-2">
          <span class="text-sm font-medium text-slate-700">Logo 背景色</span>
          <div
            class="flex flex-col gap-3 rounded-xl border border-slate-200 p-4"
          >
            <div class="flex flex-wrap items-center gap-2">
              <input
                v-model="templateForm.iconBg"
                type="text"
                class="flex-1 min-w-[180px] rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-rose-400"
                placeholder="#fef3f2"
              />
              <span
                class="h-10 w-10 rounded-xl border"
                :style="{ backgroundColor: templateForm.iconBg || '#F8FAFC' }"
              ></span>
            </div>
            <color-picker-block
              v-model="templateForm.iconBg"
              with-hex-input
              :with-colors-history="6"
              class="rounded-xl bg-white"
            />
          </div>
        </label>
        <label
          class="flex items-center gap-2 text-sm font-medium text-slate-700"
        >
          <input
            type="checkbox"
            v-model="templateForm.isOpen"
            class="h-4 w-4 rounded border-slate-300"
          />
          顯示於前臺
        </label>
        <div class="md:col-span-2">
          <div class="flex gap-3 pt-4">
            <button
              type="button"
              class="flex-1 rounded-xl bg-slate-200 text-slate-700 py-2 text-sm font-semibold hover:bg-slate-300"
              @click="emit('cancel')"
            >
              取消
            </button>
            <button
              type="submit"
              class="flex-1 rounded-xl bg-rose-500 text-white py-2 text-sm font-semibold tracking-wide disabled:opacity-50"
              :disabled="templateSaving || !templateForm.grant_id"
            >
              {{ templateFormMode === "create" ? "新增" : "更新" }}
            </button>
          </div>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch, type PropType } from "vue";
import { supabase } from "~/utils/supabaseClient";
import { useNotifications } from "~/composables/useNotifications";

// 模板表單資料模型，對應前端可編輯欄位。
interface TemplateFormState {
  id: string;
  grant_id: string;
  name: string;
  requires_paid_plan: boolean;
  submission_deadline: string;
  subsidy_amount: string;
  subtitle: string;
  description: string;
  logo_storage_path: string;
  iconBg: string;
  isOpen: boolean;
}

// 主題下拉選項型別。
interface GrantOption {
  label: string;
  value: string;
}

// 接收彈窗顯示、主題選項、模式與儲存狀態。
const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false,
  },
  grantOptions: {
    type: Array as PropType<GrantOption[]>,
    default: () => [],
  },
  templateFormMode: {
    type: String as PropType<"create" | "edit">,
    default: "create",
  },
  templateSaving: {
    type: Boolean,
    default: false,
  },
});

// 與父層雙向綁定模板表單。
const templateForm = defineModel<TemplateFormState>("templateForm", {
  required: true,
});

// 對外派發提交與取消事件。
const emit = defineEmits<{
  (e: "submit"): void;
  (e: "cancel"): void;
}>();

// 通知與 Supabase 相關設定。
const { success, error: notifyError } = useNotifications();
const runtimeConfig = useRuntimeConfig();
const supabaseUrl = runtimeConfig.public.supabaseUrl;

// Logo 上傳互動狀態：檔案輸入、拖曳中、暫存預覽、待上傳檔案。
const fileInputRef = ref<HTMLInputElement | null>(null);
const isDraggingLogo = ref(false);
const localLogoPreview = ref<string | null>(null);
const selectedLogoFile = ref<File | null>(null);

// Logo 上傳允許副檔名與儲存 bucket。
const ACCEPTED_EXTENSIONS = ["png", "jpg", "jpeg"];
const LOGO_BUCKET = "logos";

// 取得遠端 Logo 預覽位址；若已是完整網址則直接使用。
const remoteLogoPreview = computed(() => {
  const path = templateForm.value.logo_storage_path?.trim();
  if (!path) return "";
  if (path.startsWith("http")) {
    return path;
  }
  if (!supabaseUrl) {
    return "";
  }
  return `${supabaseUrl}/storage/v1/object/${path}`;
});

// 優先使用本地預覽，若無則顯示遠端已儲存圖檔。
const activeLogoPreview = computed(
  () => localLogoPreview.value || remoteLogoPreview.value,
);

// 顯示預估儲存路徑，便於使用者理解最終檔名。
const displayStoragePath = computed(() => {
  if (templateForm.value.logo_storage_path) {
    return templateForm.value.logo_storage_path;
  }
  if (!templateForm.value.id) {
    return "尚未上傳";
  }
  const normalized = sanitizeTemplateId(templateForm.value.id);
  return normalized ? `logos/${normalized}_logo` : "尚未上傳";
});

// 關閉彈窗時清理預覽 URL 與拖曳狀態，避免記憶體殘留。
watch(
  () => props.isVisible,
  (visible) => {
    if (!visible) {
      resetLocalPreview();
      isDraggingLogo.value = false;
    }
  },
);

// 開啟原生檔案選擇器。
function openFilePicker() {
  fileInputRef.value?.click();
}

// 更新拖曳進入/離開狀態，控制拖曳提示樣式。
function handleLogoDrag(state: boolean) {
  isDraggingLogo.value = state;
}

// 處理拖放上傳：取第一個檔案進入驗證流程。
function onLogoDrop(event: DragEvent) {
  event.preventDefault();
  isDraggingLogo.value = false;
  const file = event.dataTransfer?.files?.[0];
  if (file) {
    handleLogoSelection(file);
  }
}

// 處理檔案選擇器變更，並在處理後清空 input 值。
function onLogoFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0] || null;
  if (file) {
    handleLogoSelection(file);
  }
  target.value = "";
}

// 驗證副檔名後設定待上傳檔案與本地預覽。
function handleLogoSelection(file: File) {
  const extension = resolveFileExtension(file);
  if (!ACCEPTED_EXTENSIONS.includes(extension)) {
    notifyError("僅支援 PNG、JPG、JPEG 圖片");
    return;
  }

  selectedLogoFile.value = file;
  setLocalPreview(file);
}

// 將模板 ID 標準化為可用於檔名的安全字串。
function sanitizeTemplateId(rawId: string) {
  return rawId
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9-_]/g, "-");
}

// 優先用檔名判斷副檔名，必要時退回 MIME type 判斷。
function resolveFileExtension(file: File): string {
  const extensionFromName = file.name.split(".").pop()?.toLowerCase();
  if (extensionFromName && ACCEPTED_EXTENSIONS.includes(extensionFromName)) {
    return extensionFromName;
  }
  if (file.type === "image/png") {
    return "png";
  }
  return "jpg";
}

// 上傳目前選取的 Logo 至 Supabase，成功後回寫公開路徑。
async function uploadLogoFile(): Promise<boolean> {
  if (!selectedLogoFile.value) {
    return true; // 沒有選擇檔案就不需要上傳。
  }

  const templateId = templateForm.value.id?.trim();
  if (!templateId) {
    notifyError("請先填寫模板 ID，再上傳 Logo 圖片");
    return false;
  }

  const file = selectedLogoFile.value;
  const extension = resolveFileExtension(file);
  const normalizedId = sanitizeTemplateId(templateId);

  if (!normalizedId) {
    notifyError("模板 ID 需為英數字與 -/_ 組成");
    return false;
  }

  try {
    const objectPath = `${normalizedId}_logo.${extension}`;
    const { error } = await supabase.storage
      .from(LOGO_BUCKET)
      .upload(objectPath, file, {
        upsert: true,
        contentType: file.type || `image/${extension}`,
        cacheControl: "3600",
      });

    if (error) {
      throw error;
    }

    const { data: publicUrlData } = supabase.storage
      .from(LOGO_BUCKET)
      .getPublicUrl(objectPath);

    const storageValue =
      publicUrlData?.publicUrl || `${LOGO_BUCKET}/${objectPath}`;
    templateForm.value.logo_storage_path = storageValue;
    return true;
  } catch (uploadError: any) {
    console.error("Failed to upload logo", uploadError);
    notifyError(uploadError?.message || "Logo 上傳失敗，請稍後再試");
    return false;
  }
}

// 提供給父層取得目前暫存的 Logo 檔案。
function getSelectedLogoFile(): File | null {
  return selectedLogoFile.value;
}

// 建立本地預覽 URL 前先釋放舊 URL，避免記憶體洩漏。
function setLocalPreview(file: File) {
  resetLocalPreview();
  localLogoPreview.value = URL.createObjectURL(file);
}

// 釋放本地預覽 URL。
function resetLocalPreview() {
  if (localLogoPreview.value) {
    URL.revokeObjectURL(localLogoPreview.value);
    localLogoPreview.value = null;
  }
}

// 元件卸載時回收本地預覽 URL。
onBeforeUnmount(() => {
  resetLocalPreview();
});

// 暴露方法給父層主動讀取待上傳檔案。
defineExpose({
  getSelectedLogoFile,
});

// 提供元件名稱，方便 Vue DevTools 與錯誤追蹤辨識。
defineOptions({ name: "TemplateFormModal" });
</script>
