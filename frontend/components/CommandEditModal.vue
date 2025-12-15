<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center px-4 py-8"
      >
        <div
          class="absolute inset-0 bg-gray-900/30 backdrop-blur-sm"
          @click="handleClose"
        ></div>
        <div
          class="relative w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl"
        >
          <div class="flex items-center justify-between">
            <div>
              <p
                class="text-xs font-semibold uppercase tracking-wide text-rose-400"
              >
                編輯模型指令
              </p>
              <h3 class="text-xl font-semibold text-gray-900">
                {{ command?.title || "新指令" }}
              </h3>
            </div>
            <button
              class="rounded-full p-2 text-gray-400 transition hover:bg-gray-100 hover:text-gray-700"
              @click="handleClose"
              aria-label="關閉視窗"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="1.5"
                stroke="currentColor"
                class="h-5 w-5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <form class="mt-6 space-y-5" @submit.prevent="handleSave">
            <div class="space-y-2">
              <label class="text-sm font-semibold text-gray-700"
                >指令標題</label
              >
              <input
                v-model="form.title"
                type="text"
                class="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 outline-none focus:border-rose-400 focus:bg-white"
                placeholder="輸入指令名稱"
                required
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-semibold text-gray-700"
                >指令描述</label
              >
              <textarea
                v-model="form.description"
                rows="4"
                class="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 outline-none focus:border-rose-400 focus:bg-white"
                placeholder="補充 AI 需要的背景、語氣或指令細節"
                required
              ></textarea>
            </div>

            <div
              class="flex items-center justify-between rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3"
            >
              <div>
                <p class="text-sm font-semibold text-gray-800">企業專屬 DNA</p>
                <p class="text-xs text-gray-500">切換後會標記為企業自訂指令</p>
              </div>
              <button
                type="button"
                class="relative inline-flex h-7 w-12 items-center rounded-full transition"
                :class="form.isCompany ? 'bg-emerald-500' : 'bg-gray-300'"
                @click="form.isCompany = !form.isCompany"
              >
                <span
                  class="inline-block h-5 w-5 transform rounded-full bg-white transition"
                  :class="form.isCompany ? 'translate-x-5' : 'translate-x-1'"
                ></span>
              </button>
            </div>

            <div class="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                class="rounded-2xl border border-gray-200 px-5 py-2 text-sm font-semibold text-gray-600 transition hover:border-gray-300"
                @click="handleClose"
              >
                取消
              </button>
              <button
                type="submit"
                class="rounded-2xl bg-rose-500 px-6 py-2 text-sm font-semibold text-white shadow-md shadow-rose-200 transition hover:bg-rose-600"
              >
                儲存
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";

interface CommandPayload {
  id?: string;
  title: string;
  description: string;
  isCompany: boolean;
}

interface Props {
  modelValue: boolean;
  command: CommandPayload | null;
}

const props = defineProps<Props>();
const emit = defineEmits(["update:modelValue", "save", "close"]);

const form = reactive<CommandPayload>({
  id: undefined,
  title: "",
  description: "",
  isCompany: false,
});

watch(
  () => props.command,
  (value) => {
    form.id = value?.id;
    form.title = value?.title || "";
    form.description = value?.description || "";
    form.isCompany = value?.isCompany ?? false;
  },
  { immediate: true }
);

function handleClose() {
  emit("update:modelValue", false);
  emit("close");
}

function handleSave() {
  if (!form.title.trim() || !form.description.trim()) return;
  emit("save", { ...form });
}
</script>
