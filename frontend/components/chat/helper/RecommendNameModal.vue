<!-- 推荐名称组件：根據計畫書大綱生成建議標題 -->
<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="isOpenModel"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 overflow-y-auto"
        @click.self="handleClose"
      >
        <div
          class="w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden flex flex-col my-8"
        >
          <header
            class="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5 bg-gradient-to-r from-rose-50 to-amber-50"
          >
            <div class="space-y-1">
              <p
                class="text-xs font-semibold tracking-widest text-slate-500 uppercase"
              >
                推薦名稱
              </p>
              <h2 class="text-2xl font-bold text-slate-900">
                請從以下候選名稱中選擇
              </h2>
              <p class="text-sm text-slate-500">
                系統依據已填內容建議 5 個名稱；也可使用原本名稱。
              </p>
            </div>
            <button
              type="button"
              class="text-slate-500 hover:text-slate-700"
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

          <div class="flex-1 overflow-y-auto px-6 py-6">
            <div v-if="loading" class="flex items-center justify-center py-12">
              <div class="text-sm text-slate-500">正在產生建議名稱...</div>
            </div>
            <div v-else>
              <div v-if="options && options.length" class="grid gap-3">
                <div v-for="(opt, idx) in options" :key="`opt-${idx}`">
                  <label
                    :for="`opt-${idx}`"
                    class="flex items-center justify-between gap-3 rounded-lg border px-3 py-2 hover:shadow-sm transition-shadow cursor-pointer"
                    :class="
                      selected === opt
                        ? 'border-rose-400 bg-rose-50 shadow-md'
                        : 'border-slate-200 bg-white'
                    "
                  >
                    <div class="flex items-center gap-3">
                      <input
                        type="radio"
                        :id="`opt-${idx}`"
                        :value="opt"
                        v-model="selected"
                        class="hidden"
                      />
                      <div
                        class="flex h-6 w-6 items-center justify-center rounded-full border"
                        :class="
                          selected === opt
                            ? 'bg-rose-500 border-rose-500 text-white'
                            : 'bg-white border-slate-200 text-slate-400'
                        "
                      >
                        <svg
                          v-if="selected === opt"
                          xmlns="http://www.w3.org/2000/svg"
                          class="h-3 w-3"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                        <svg
                          v-else
                          xmlns="http://www.w3.org/2000/svg"
                          class="h-3 w-3"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="1.5"
                        >
                          <circle cx="12" cy="12" r="6" />
                        </svg>
                      </div>
                      <div class="text-sm text-slate-800">{{ opt }}</div>
                    </div>
                    <div
                      v-if="selected === opt"
                      class="text-xs text-rose-600 font-semibold"
                    >
                      已選
                    </div>
                  </label>
                </div>
              </div>

              <div class="pt-3">
                <label
                  for="original"
                  class="flex items-center gap-2 cursor-pointer rounded-lg border px-3 py-2 hover:shadow-sm transition-shadow"
                  :class="
                    selected === originalName
                      ? 'border-rose-400 bg-rose-50'
                      : 'border-slate-200 bg-white'
                  "
                >
                  <input
                    type="radio"
                    id="original"
                    :value="originalName"
                    v-model="selected"
                    class="hidden"
                  />
                  <div class="flex items-center gap-2">
                    <div
                      class="flex h-6 w-6 items-center justify-center rounded-full border"
                      :class="
                        selected === originalName
                          ? 'bg-rose-500 border-rose-500 text-white'
                          : 'bg-white border-slate-200 text-slate-400'
                      "
                    >
                      <svg
                        v-if="selected === originalName"
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-3 w-3"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      <svg
                        v-else
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-3 w-3"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.5"
                      >
                        <circle cx="12" cy="12" r="6" />
                      </svg>
                    </div>
                    <div class="text-sm text-slate-700">
                      使用原本名稱：<span class="font-medium">{{
                        originalName || "（未命名）"
                      }}</span>
                    </div>
                  </div>
                </label>
              </div>

              <!-- custom name input -->
              <div class="pt-3">
                <label
                  for="custom"
                  class="flex items-start gap-2 cursor-pointer rounded-lg border px-3 py-2 hover:shadow-sm transition-shadow"
                  :class="
                    selected === customName
                      ? 'border-rose-400 bg-rose-50'
                      : 'border-slate-200 bg-white'
                  "
                >
                  <input
                    type="radio"
                    id="custom"
                    :value="customName"
                    v-model="selected"
                    class="hidden"
                  />
                  <div class="flex-1">
                    <div class="text-sm text-slate-700 font-medium mb-1">
                      自訂名稱
                    </div>
                    <input
                      v-model="customName"
                      @input="onCustomInput"
                      placeholder="輸入自訂名稱（例如：我的專案名）"
                      class="w-full rounded-md border px-3 py-2 text-sm"
                    />
                  </div>
                </label>
              </div>
            </div>
          </div>

          <footer
            class="flex flex-col gap-3 border-t border-slate-100 bg-white px-6 py-5 sm:flex-row sm:items-center sm:justify-between"
          >
            <div></div>
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
                class="rounded-xl bg-gradient-to-r from-rose-500 to-amber-500 px-6 py-2 text-sm font-semibold text-white shadow-lg"
                :disabled="!selected || selected.length === 0"
                @click="confirmSelection"
              >
                確定選擇
              </button>
            </div>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

const props = defineProps({
  originalName: { type: String, default: "" },
  suggestions: { type: Array as () => string[], default: () => [] },
  loading: { type: Boolean, default: false },
});
const emit = defineEmits<{ (e: "confirm", value: string): void }>();
const isOpenModel = defineModel("isOpen", { type: Boolean, default: false });

const options = ref<string[]>(props.suggestions || []);
const selected = ref(props.originalName || "");
const customName = ref("");

// 監聽建議列表和原始名稱的變化，更新選擇項
watch(
  () => props.suggestions,
  (s) => {
    options.value = s || [];
  },
);
watch(
  () => props.originalName,
  (v) => {
    if (!selected.value) selected.value = v || "";
  },
);

// 輸入自定義名稱時自動選中
function onCustomInput() {
  const v = (customName.value || "").trim();
  if (v) {
    selected.value = v;
  }
}

// 當選擇變化時，如果選中的是建議項或原始名稱，清除自定義輸入框
watch(selected, (v) => {
  if (!v) return;
  if (options.value.includes(v) || v === props.originalName) {
    if (customName.value) customName.value = "";
  } else {
    if (customName.value !== v) customName.value = v;
  }
});

// 確認選擇並發送事件，關閉模態框
function confirmSelection() {
  const pick = (selected.value || "").trim();
  if (!pick) return;
  emit("confirm", pick);
  isOpenModel.value = false;
}
function handleClose() {
  isOpenModel.value = false;
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
