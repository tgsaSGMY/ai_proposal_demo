<template>
  <div class="space-y-6 sm:space-y-8">
    <!-- System Prompt 編輯區 -->
    <div>
      <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2"
        >系統提示 (System Prompt)</label
      >
      <textarea
        v-model="editableData.system_prompt"
        rows="8"
        class="w-full border border-gray-300 rounded-lg px-2 sm:px-3 py-1.5 sm:py-2 text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none bg-white [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      ></textarea>
    </div>
    <!-- Custom Prompts 編輯區 -->
    <div>
      <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2"
        >客製化指令 (Custom Prompts)</label
      >
      <div class="p-3 sm:p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-2 sm:space-y-3">
        <div
          v-if="
            editableData.custom_prompt_list &&
            editableData.custom_prompt_list.length > 0
          "
          class="space-y-1 sm:space-y-2"
        >
          <div
            v-for="(prompt, index) in editableData.custom_prompt_list"
            :key="index"
            class="flex items-center gap-1 sm:gap-2"
          >
            <input
              type="text"
              v-model="editableData.custom_prompt_list[index]"
              placeholder="輸入指令..."
              class="flex-grow border border-gray-300 rounded-lg px-2 sm:px-3 py-1.5 sm:py-2 text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
            />
            <button
              @click="deletePrompt(index)"
              class="p-1.5 sm:p-2 text-red-500 hover:bg-red-100 rounded-lg transition text-xs sm:text-base"
            >
              刪除
            </button>
          </div>
        </div>
        <button
          @click="addPrompt"
          class="text-xs sm:text-sm font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1 transition"
        >
          新增指令
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from "vue";
const props = defineProps({
  sectionData: { type: Object, default: null },
  isSaving: Boolean,
});

const emit = defineEmits(["save"]);

const editableData = reactive({
  system_prompt: "",
  custom_prompt_list: [],
});
watch(
  () => props.sectionData,
  (newVal) => {
    if (newVal) {
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

// 提供一個方法讓父組件獲取當前的資料
function getEditableData() {
  const finalPrompts = editableData.custom_prompt_list.filter(
    (p) => p && p.trim() !== ""
  );
  return {
    system_prompt: editableData.system_prompt,
    custom_prompt_list: finalPrompts,
  };
}

// 將方法暴露給父組件
defineExpose({
  getEditableData,
});
</script>
