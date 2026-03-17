<!-- 模板列表裏的名稱推薦 -->
<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="isVisible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 py-8"
      >
        <div
          class="w-full max-w-3xl rounded-[32px] bg-white shadow-2xl ring-1 ring-black/5"
        >
          <header
            class="flex flex-col gap-3 border-b border-slate-100 px-8 py-6 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p
                class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-400"
              >
                Template / Name Recommend
              </p>
              <h2 class="text-2xl font-bold text-slate-900">
                {{ template?.name || "尚未選擇模板" }}
              </h2>
              <p class="text-xs text-slate-500">
                Grant: {{ template?.grant_id || "—" }} · Template ID:
                {{ template?.id || "—" }}
              </p>
            </div>
            <button
              type="button"
              class="text-sm font-semibold text-slate-500 hover:text-slate-900"
              @click="emitClose"
            >
              關閉
            </button>
          </header>

          <section class="space-y-6 px-8 py-6">
            <div class="space-y-2">
              <label class="text-sm font-semibold text-slate-800">
                計畫名稱特性說明
              </label>
              <p class="text-xs text-slate-500">
                描述該模板命名時必須突出的語氣、領域或限制，會附加在系統提示中。
              </p>
              <textarea
                v-model="traits"
                rows="4"
                class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none focus:border-rose-400 focus:bg-white"
                placeholder="例如：需強調永續轉型、跨國市場拓展與 AI 應用"
              ></textarea>
            </div>

            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-semibold text-slate-800">
                    範例 (最多 {{ MAX_EXAMPLES }} 筆)
                  </p>
                  <p class="text-xs text-slate-500">
                    這些名稱會放進提示中，協助模型模仿命名風格。
                  </p>
                </div>
                <button
                  type="button"
                  class="rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-600 shadow-sm hover:border-rose-200 hover:text-rose-500 disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="exampleInputs.length >= MAX_EXAMPLES"
                  @click="addExample"
                >
                  新增範例
                </button>
              </div>

              <div class="space-y-3">
                <div
                  v-for="(value, index) in exampleInputs"
                  :key="`example-${index}`"
                  class="flex items-start gap-2"
                >
                  <input
                    v-model="exampleInputs[index]"
                    type="text"
                    class="flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-800 outline-none focus:border-rose-400 focus:bg-white"
                    :placeholder="`範例名稱 ${index + 1}`"
                  />
                  <button
                    type="button"
                    class="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-500 hover:border-rose-200 hover:text-rose-500"
                    @click="removeExample(index)"
                  >
                    移除
                  </button>
                </div>
                <p v-if="!exampleInputs.length" class="text-xs text-slate-400">
                  尚未新增範例，請點擊「新增範例」補充。
                </p>
              </div>
            </div>
          </section>

          <footer
            class="flex flex-wrap items-center justify-end gap-3 border-t border-slate-100 px-8 py-6"
          >
            <button
              type="button"
              class="rounded-2xl border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-500"
              @click="emitClose"
            >
              取消
            </button>
            <button
              type="button"
              class="rounded-2xl bg-rose-500 px-6 py-2 text-sm font-semibold text-white shadow-lg shadow-rose-200 transition hover:-translate-y-0.5 hover:bg-rose-600 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="saving"
              @click="handleSave"
            >
              {{ saving ? "儲存中..." : "儲存命名設定" }}
            </button>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import type { PropType } from "vue";
import {
  MAX_NAME_RECOMMEND_EXAMPLES as MAX_EXAMPLES,
  normalizeNameRecommendConfig,
  type NameRecommendConfig,
} from "~/types/nameRecommend";

// 模板摘要資訊，僅保留本元件會使用到的欄位。
interface TemplateSummary {
  id: string;
  grant_id: string;
  name: string;
  name_recommend_config?: NameRecommendConfig | null;
}

// 接收彈窗狀態、目前模板與儲存中狀態。
const props = defineProps({
  isVisible: { type: Boolean, default: false },
  template: {
    type: Object as PropType<TemplateSummary | null>,
    default: null,
  },
  saving: { type: Boolean, default: false },
});

// 對外事件：關閉彈窗、送出命名設定。
const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", config: NameRecommendConfig): void;
}>();

// 命名特性文字與範例輸入欄位（可動態增減）。
const traits = ref("");
const exampleInputs = ref<string[]>([]);

// 當彈窗開啟或切換模板時，同步載入模板既有設定。
watch(
  () => [props.template, props.isVisible] as const,
  ([template, visible]) => {
    if (visible) {
      syncFromTemplate(template);
    }
  },
  { immediate: true },
);

// 讀取模板設定並正規化，限制範例數量不超過上限。
function syncFromTemplate(template = props.template) {
  const normalized = normalizeNameRecommendConfig(
    template?.name_recommend_config ?? null,
  );
  traits.value = normalized.traits || "";
  exampleInputs.value = normalized.examples.length
    ? [...normalized.examples].slice(0, MAX_EXAMPLES)
    : [""];
}

// 新增一個空白範例輸入欄，達上限後不再新增。
function addExample() {
  if (exampleInputs.value.length >= MAX_EXAMPLES) return;
  exampleInputs.value.push("");
}

// 移除指定範例；若全空則保留一個空白欄位維持可編輯體驗。
function removeExample(index: number) {
  exampleInputs.value.splice(index, 1);
  if (!exampleInputs.value.length) {
    exampleInputs.value.push("");
  }
}

// 清理輸入內容（去空白、去重複、套用上限）後再送出。
function handleSave() {
  const sanitizedExamples = exampleInputs.value
    .map((item) => item.trim())
    .filter((item, idx, arr) => {
      if (!item) {
        return false;
      }
      // 避免重複項，且保留第一次出現的順序。
      return arr.indexOf(item) === idx;
    })
    .slice(0, MAX_EXAMPLES);

  const payload: NameRecommendConfig = {
    traits: traits.value.trim(),
    examples: sanitizedExamples,
  };

  emit("save", payload);
}

// 統一關閉事件出口，供多個按鈕共用。
function emitClose() {
  emit("close");
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
