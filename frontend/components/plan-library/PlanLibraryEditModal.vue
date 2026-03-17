<!-- 方案库编辑模态帐组件：编辑保存在个人或企业库中的方案 -->
<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-gray-900/60 px-4 py-8"
      >
        <div class="absolute inset-0" @click="handleClose"></div>
        <Transition
          enter-active-class="transition duration-300 transform"
          enter-from-class="translate-y-8 opacity-0"
          enter-to-class="translate-y-0 opacity-100"
          leave-active-class="transition duration-200 transform"
          leave-from-class="translate-y-0 opacity-100"
          leave-to-class="translate-y-4 opacity-0"
        >
          <div
            v-if="visible"
            class="relative w-full max-w-xl rounded-3xl bg-white shadow-2xl ring-1 ring-gray-100"
          >
            <div class="flex items-start gap-4 px-6 pt-6">
              <div
                class="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-50 text-rose-500"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke-width="1.8"
                  stroke="currentColor"
                  class="h-6 w-6"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M12 20h9"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M16.5 3.5l4 4-12 12H4.5v-4z"
                  />
                </svg>
              </div>
              <div>
                <p
                  class="text-sm font-semibold uppercase tracking-wide text-rose-500"
                >
                  編輯計畫案
                </p>
                <h2 class="text-2xl font-bold text-gray-900 leading-tight mt-1">
                  {{ currentProject?.title || "專案資訊" }}
                </h2>
                <p class="text-sm text-gray-500 mt-1">
                  更新專案名稱與描述，讓團隊成員能即時掌握最新內容。
                </p>
              </div>
            </div>

            <div class="px-6 py-6 space-y-5">
              <label class="block text-sm font-medium text-gray-700">
                計畫名稱
                <input
                  v-model="formState.title"
                  type="text"
                  class="mt-2 w-full rounded-2xl border border-gray-200 bg-gray-50/80 px-4 py-3 text-gray-900 focus:border-rose-400 focus:ring-rose-200"
                  placeholder="輸入計畫名稱"
                />
              </label>
              <label class="block text-sm font-medium text-gray-700">
                計畫描述
                <textarea
                  v-model="formState.description"
                  rows="4"
                  class="mt-2 w-full rounded-2xl border border-gray-200 bg-gray-50/80 px-4 py-3 text-gray-900 focus:border-rose-400 focus:ring-rose-200"
                  placeholder="簡述目標、運作內容或交付成果"
                ></textarea>
              </label>
            </div>

            <div
              class="flex flex-col-reverse gap-3 border-t border-gray-100 bg-gray-50/80 px-6 py-5 md:flex-row md:justify-end"
            >
              <button
                type="button"
                class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-600 hover:bg-gray-100 md:w-auto"
                @click="handleClose"
              >
                取消
              </button>
              <button
                type="button"
                class="w-full rounded-2xl bg-rose-500 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-rose-600 disabled:opacity-50 md:w-auto"
                :disabled="!canSubmit"
                @click="handleSave"
              >
                儲存變更
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from "vue";

interface EditableProject {
  id?: string;
  title: string;
  description: string;
}

const props = defineProps<{
  modelValue: boolean;
  project: EditableProject | null;
}>();
const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "save", payload: EditableProject): void;
  (e: "close"): void;
}>();

const visible = computed(() => props.modelValue);
const currentProject = computed(() => props.project);

const formState = reactive({
  title: "",
  description: "",
});

// 监听项目属性变化，更新表单状态
watch(
  () => props.project,
  (project) => {
    formState.title = project?.title ?? "";
    formState.description = project?.description ?? "";
  },
  { immediate: true }
);

// 检查表单是否可以提交，需要标题和描述都不为空
const canSubmit = computed(
  () =>
    formState.title.trim().length > 0 && formState.description.trim().length > 0
);

// 关闭模态框并发送关闭事件
function handleClose() {
  emit("update:modelValue", false);
  emit("close");
}

// 保存表单变更，验证数据后发送保存事件
function handleSave() {
  if (!props.project || !canSubmit.value) return;
  emit("save", {
    id: props.project.id,
    title: formState.title.trim(),
    description: formState.description.trim(),
  });
}
</script>
