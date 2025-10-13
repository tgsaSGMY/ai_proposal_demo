<!-- components/DatasetEditModal.vue -->
<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black bg-opacity-50 z-40 flex justify-center items-center"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col"
    >
      <header class="p-4 border-b">
        <h2 class="text-xl font-bold text-gray-800">
          編輯數據點 #{{ dataset.id }}
        </h2>
      </header>

      <main class="p-6 space-y-4 overflow-y-auto">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >Prompt (用戶輸入)</label
          >
          <textarea
            v-model="editableData.prompt"
            rows="6"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          ></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >Final Answer (JSON 格式)</label
          >
          <textarea
            v-model="editableData.final_answer_str"
            rows="12"
            class="w-full font-mono text-sm bg-gray-50 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            :class="{ 'border-red-500 ring-red-500': jsonError }"
          ></textarea>
          <p v-if="jsonError" class="mt-1 text-xs text-red-600">
            {{ jsonError }}
          </p>
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
          class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-indigo-300 flex items-center gap-2"
        >
          {{ isSaving ? "保存中..." : "保存更改" }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, reactive } from "vue";

const props = defineProps({
  show: Boolean,
  dataset: { type: Object, default: () => null },
  isSaving: Boolean,
});

const emit = defineEmits(["close", "save"]);

const editableData = reactive({
  id: null,
  prompt: "",
  final_answer_str: "",
});
const jsonError = ref(null);

watch(
  () => props.dataset,
  (newVal) => {
    if (newVal) {
      console.log(newVal);
      editableData.id = newVal.id;
      editableData.prompt = newVal.prompt || "";
      editableData.final_answer_str = JSON.stringify(
        newVal.final_answer,
        null,
        2
      );
      jsonError.value = null;
    }
  },
  { immediate: true, deep: true }
);

function handleSave() {
  let parsedJson;
  try {
    parsedJson = JSON.parse(editableData.final_answer_str);
    jsonError.value = null;
  } catch (error) {
    jsonError.value = "JSON 格式無效，請檢查。";
    return;
  }

  emit("save", {
    id: editableData.id,
    prompt: editableData.prompt,
    final_answer: parsedJson,
  });
}
</script>
