<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="isOpenModel"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4 py-6 overflow-y-auto"
        @click.self="handleClose"
      >
        <div
          class="w-full max-w-2xl bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden flex flex-col my-8"
        >
          <header
            class="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5 bg-white"
          >
            <div class="space-y-1">
              <p
                class="text-xs font-semibold tracking-widest text-slate-500 uppercase"
              >
                {{ title || "編輯欄位" }}
              </p>
              <h2 class="text-2xl font-bold text-slate-900">{{ label }}</h2>
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
            <div class="space-y-4">
              <p class="text-xs text-slate-500">
                請編輯以下欄位內容，確認後會直接送出更新指令。
              </p>
              <textarea
                ref="textareaRef"
                v-model="value"
                rows="8"
                class="w-full rounded-xl border border-slate-200 p-3 text-sm text-slate-800 focus:border-rose-400 focus:ring-2 focus:ring-rose-100"
              ></textarea>
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
                :disabled="!value || value.trim().length === 0"
                @click="emitConfirm"
              >
                確定修改並送出
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
  title: { type: String, default: "" },
  label: { type: String, default: "" },
  initialValue: { type: String, default: "" },
});

const emit = defineEmits<{ (e: "confirm", value: string): void }>();
const isOpenModel = defineModel("isOpen", { type: Boolean, default: false });

const value = ref(props.initialValue || "");
const textareaRef = ref<HTMLTextAreaElement | null>(null);

watch(
  () => isOpenModel.value,
  (open) => {
    if (open) {
      value.value = props.initialValue || "";
      // focus textarea on open
      setTimeout(() => {
        textareaRef.value?.focus();
      }, 50);
    } else {
      value.value = props.initialValue || "";
    }
  }
);

watch(
  () => props.initialValue,
  (v) => {
    if (isOpenModel.value) {
      value.value = v || "";
    }
  }
);

function emitConfirm() {
  emit("confirm", (value.value || "").trim());
  handleClose();
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
