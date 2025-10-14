<!-- components/DatasetEditModal.vue -->
<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 flex justify-center items-center"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden border border-gray-200"
    >
      <!-- Header -->
      <header
        class="p-5 border-b bg-gradient-to-r from-indigo-50 to-white flex items-center justify-between"
      >
        <h2 class="text-lg font-semibold text-gray-800">
          ✏️ 編輯數據點 #{{ dataset.id }}
        </h2>
      </header>

      <!-- Main content -->
      <main class="p-6 space-y-5 overflow-y-auto text-gray-700 bg-gray-50/60">
        <!-- Source Type -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >數據來源 (Source Type)</label
          >
          <select
            v-model="editableData.source_type"
            class="w-full rounded-xl border-gray-300 bg-white shadow-sm hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-300 transition-all duration-150"
          >
            <option value="golden_samples">黃金樣本</option>
            <option value="synthetic_data">合成資料</option>
            <option value="external_direct">外部直接</option>
          </select>
        </div>

        <!-- Prompt -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >Prompt (用戶輸入)</label
          >
          <textarea
            v-model="editableData.prompt"
            rows="6"
            class="w-full rounded-xl border-gray-300 bg-white shadow-sm hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-300 transition-all duration-150"
          ></textarea>
        </div>

        <!-- Final Answer -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >Final Answer (JSON 格式)</label
          >
          <textarea
            v-model="editableData.final_answer_str"
            rows="12"
            class="w-full font-mono text-sm rounded-xl border-gray-300 bg-white shadow-sm hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-300 transition-all duration-150"
            :class="{ 'border-red-500 ring-2 ring-red-400': jsonError }"
          ></textarea>
          <p v-if="jsonError" class="mt-1 text-xs text-red-600">
            {{ jsonError }}
          </p>
        </div>
      </main>

      <!-- Footer -->
      <footer
        class="flex-shrink-0 p-4 bg-gradient-to-r from-gray-100 to-gray-50 border-t flex justify-end gap-3"
      >
        <button
          @click="$emit('close')"
          class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-all duration-150"
        >
          取消
        </button>
        <button
          @click="handleSave"
          :disabled="isSaving"
          class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300 flex items-center gap-2 transition-all duration-150 shadow-sm"
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
  source_type: "synthetic_data",
});
const jsonError = ref(null);

watch(
  () => props.dataset,
  (newVal) => {
    if (newVal) {
      editableData.id = newVal.id;
      editableData.prompt = newVal.prompt || "";
      editableData.final_answer_str = JSON.stringify(
        newVal.final_answer,
        null,
        2
      );
      editableData.source_type = newVal.source_type || "synthetic_data";
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
    source_type: editableData.source_type,
  });
}
</script>
