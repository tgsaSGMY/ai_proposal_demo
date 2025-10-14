<template>
  <Transition
    enter-active-class="transition-opacity duration-300 ease-out"
    leave-active-class="transition-opacity duration-200 ease-in"
  >
    <div
      v-if="show && sectionData"
      class="fixed inset-0 z-40 flex justify-center items-center bg-gray-900 bg-opacity-60"
      @click.self="$emit('close')"
    >
      <div
        class="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col"
      >
        <header class="p-4 border-b flex justify-between items-center">
          <h2 class="text-xl font-bold text-gray-800">
            編輯章節設定: {{ sectionData.sectionName }}
          </h2>
          <button
            @click="$emit('close')"
            class="p-1 rounded-full hover:bg-gray-200"
          >
            <svg
              class="h-6 w-6 text-gray-600"
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

        <main class="p-6 space-y-6 overflow-y-auto">
          <!-- System Prompt 編輯區 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2"
              >系統提示 (System Prompt)</label
            >
            <textarea
              v-model="editableData.system_prompt"
              rows="8"
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            ></textarea>
          </div>

          <!-- Custom Prompts 編輯區 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2"
              >客製化指令 (Custom Prompts)</label
            >
            <div
              class="p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-3"
            >
              <div
                v-if="
                  editableData.custom_prompt_list &&
                  editableData.custom_prompt_list.length > 0
                "
                class="space-y-2"
              >
                <div
                  v-for="(prompt, index) in editableData.custom_prompt_list"
                  :key="index"
                  class="flex items-center gap-2"
                >
                  <input
                    type="text"
                    v-model="editableData.custom_prompt_list[index]"
                    placeholder="輸入指令..."
                    class="flex-grow w-full rounded-md border-gray-300 shadow-sm sm:text-sm p-2"
                  />
                  <button
                    @click="deletePrompt(index)"
                    class="p-1.5 text-red-500 hover:bg-red-100 rounded-full"
                  ></button>
                </div>
              </div>
              <button
                @click="addPrompt"
                class="text-sm font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
              >
                新增指令
              </button>
            </div>
          </div>
        </main>

        <footer class="flex-shrink-0 p-4 bg-gray-50 flex justify-end gap-3">
          <button
            @click="$emit('close')"
            class="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
          >
            取消
          </button>
          <button
            @click="handleSave"
            :disabled="isSaving"
            class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-indigo-300"
          >
            {{ isSaving ? "保存中..." : "保存設定" }}
          </button>
        </footer>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch, reactive } from "vue";

const props = defineProps({
  show: Boolean,
  sectionData: { type: Object, default: null },
  isSaving: Boolean,
});

const emit = defineEmits(["close", "save"]);

const editableData = reactive({
  system_prompt: "",
  custom_prompt_list: [],
});

watch(
  () => props.sectionData,
  (newVal) => {
    if (newVal) {
      // 使用深拷貝，避免直接修改 prop
      editableData.system_prompt = newVal.system_prompt || "";
      editableData.custom_prompt_list = JSON.parse(
        JSON.stringify(newVal.custom_prompt_list || [])
      );
    }
  },
  { immediate: true, deep: true }
);

function addPrompt() {
  editableData.custom_prompt_list.push("");
}

function deletePrompt(index) {
  editableData.custom_prompt_list.splice(index, 1);
}

function handleSave() {
  // 過濾掉空的 custom prompts
  const finalPrompts = editableData.custom_prompt_list.filter(
    (p) => p && p.trim() !== ""
  );
  emit("save", {
    system_prompt: editableData.system_prompt,
    prompts: finalPrompts,
  });
}
</script>
