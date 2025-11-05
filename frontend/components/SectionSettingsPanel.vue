<template>
  <div class="space-y-6 sm:space-y-8">
    <!-- System Prompt 編輯區 -->
    <div>
      <label
        class="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2"
        >系統提示 (System Prompt)</label
      >
      <div class="space-y-3">
        <!-- JSON Schema 編輯模式 -->
        <div
          v-if="isJsonSchema"
          class="p-3 sm:p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3"
        >
          <JsonSchemaEditor
            :fields="schemaFields"
            @update="updateSchemaFields"
          />
        </div>
        <!-- 純文本模式 -->
        <textarea
          v-else
          v-model="editableData.system_prompt"
          rows="8"
          class="w-full border border-gray-300 rounded-lg px-2 sm:px-3 py-1.5 sm:py-2 text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none bg-white [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        ></textarea>
      </div>
    </div>
    <!-- Custom Prompts 編輯區 -->
    <div>
      <label
        class="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2"
        >客製化指令 (Custom Prompts)</label
      >
      <div
        class="p-3 sm:p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-2 sm:space-y-3"
      >
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
import { reactive, watch, ref } from "vue";
import JsonSchemaEditor from "~/components/JsonSchemaEditor.vue";

const props = defineProps({
  sectionData: { type: Object, default: null },
  isSaving: Boolean,
});

const emit = defineEmits(["save"]);

const editableData = reactive({
  system_prompt: "",
  custom_prompt_list: [],
});

const schemaFields = ref({});
const isJsonSchema = ref(false);
const basePrompt = ref("");

// 檢測 System Prompt 是否為 JSON Schema 格式
function parseSystemPrompt(prompt) {
  if (!prompt) return false;

  try {
    // 支援不同換行與空白情況
    const jsonMatch = prompt.match(/```json\s*([\s\S]*?)```/i);
    if (jsonMatch && jsonMatch[1]) {
      const jsonText = jsonMatch[1].trim();
      const jsonObj = JSON.parse(jsonText);
      schemaFields.value = { ...jsonObj };
      basePrompt.value = prompt.split(/```json\s*/i)[0].trim();
      return true;
    }
  } catch (e) {
    console.error("parseSystemPrompt error:", e);
    return false;
  }

  return false;
}

// 當 System Prompt 改變時，檢查是否為 JSON Schema
watch(
  () => editableData.system_prompt,
  (newVal) => {
    isJsonSchema.value = parseSystemPrompt(newVal);
  }
);

watch(
  () => props.sectionData,
  (newVal) => {
    if (newVal) {
      editableData.system_prompt = newVal.system_prompt || "";
      editableData.custom_prompt_list = JSON.parse(
        JSON.stringify(newVal.custom_prompt_list || [])
      );
      // 初始化時檢查是否為 JSON Schema
      isJsonSchema.value = parseSystemPrompt(editableData.system_prompt);
    }
  },
  { immediate: true, deep: true }
);

// 處理 JSON Schema 編輯器的更新
function updateSchemaFields(key, newValue) {
  schemaFields.value[key] = newValue;
}

function addPrompt() {
  editableData.custom_prompt_list.push("");
}

function deletePrompt(index) {
  editableData.custom_prompt_list.splice(index, 1);
}

// 深度克隆對象
function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

// 提供一個方法讓父組件獲取當前的資料
function getEditableData() {
  const finalPrompts = editableData.custom_prompt_list.filter(
    (p) => p && p.trim() !== ""
  );

  let finalSystemPrompt = editableData.system_prompt;

  // 如果是 JSON Schema 模式，需要重新組合完整的 System Prompt
  if (isJsonSchema.value) {
    const jsonSchema = deepClone(schemaFields.value);

    finalSystemPrompt =
      basePrompt.value +
      "\n\n```json\n" +
      JSON.stringify(jsonSchema, null, 2) +
      "\n```";
  }

  return {
    system_prompt: finalSystemPrompt,
    custom_prompt_list: finalPrompts,
  };
}

// 將方法暴露給父組件
defineExpose({
  getEditableData,
});
</script>
