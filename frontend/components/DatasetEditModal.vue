<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 flex justify-center items-center p-2 sm:p-0"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white rounded-2xl shadow-2xl w-full max-w-xs sm:max-w-2xl max-h-[92vh] flex flex-col overflow-hidden border border-gray-200"
    >
      <!-- Header -->
      <header
        class="p-3 sm:p-5 border-b bg-gradient-to-r from-indigo-50 to-white flex items-center justify-between"
      >
        <h2
          class="text-base sm:text-lg font-semibold text-gray-800 break-words max-w-[70vw] sm:max-w-none"
        >
          ✏️ 編輯數據點 #{{ dataset.id }}
        </h2>
      </header>

      <!-- Main content -->
      <main
        class="p-3 sm:p-6 space-y-3 sm:space-y-5 overflow-y-auto text-gray-700 bg-gray-50/60"
      >
        <!-- Source Type -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >數據來源</label
          >
          <select
            v-model="editableData.source_type"
            class="border border-4 p-2 w-full rounded-xl border-gray-300 bg-white shadow-sm hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-300 text-sm sm:text-base transition-all duration-150"
          >
            <option value="golden_samples">黃金樣本</option>
            <option value="synthetic_data">合成資料</option>
            <option value="external_direct">外部資料</option>
          </select>
        </div>

        <!-- Prompt -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >用戶輸入</label
          >
          <textarea
            v-model="editableData.prompt"
            rows="4"
            class="border border-4 p-2 w-full rounded-xl border-gray-300 bg-white shadow-sm hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-300 text-sm sm:text-base transition-all duration-150"
          ></textarea>
        </div>

        <!-- Final Answer -->
        <div>
          <div class="flex justify-between items-center mb-2">
            <label class="block text-sm font-medium text-gray-700"
              >輸出結果</label
            >
            <!-- 模式切換按鈕 -->
            <button
              @click="toggleEditMode"
              class="px-2 py-1 text-xs bg-gray-200 rounded-md hover:bg-gray-300 transition"
            >
              {{ isRawJsonMode ? "切換為欄位模式" : "切換為原始 JSON" }}
            </button>
          </div>

          <!-- 原始 JSON 模式 -->
          <div v-if="isRawJsonMode">
            <textarea
              v-model="editableData.final_answer_str"
              rows="8"
              class="border border-4 p-2 w-full font-mono text-xs sm:text-sm rounded-xl border-gray-300 bg-white shadow-sm hover:border-indigo-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-300 transition-all duration-150"
              :class="{ 'border-red-500 ring-2 ring-red-400': jsonError }"
            ></textarea>
          </div>

          <!-- 欄位模式 -->
          <div
            v-else
            class="border p-1 sm:p-3 rounded-xl bg-white/50 max-h-[50vh] overflow-y-auto"
          >
            <PlanOutputPanel
              v-if="computedSections.length > 0"
              :sections="computedSections"
              :plan-content="computedPlanContent"
              mode="dataset-edit"
              :is-loading="false"
              @update:content="handlePlanUpdate"
            />
            <p v-else class="text-center text-sm text-gray-500 p-4">
              找不到此數據點對應的 Schema，無法渲染表單。
            </p>
          </div>

          <p v-if="jsonError" class="mt-1 text-xs text-red-600">
            {{ jsonError }}
          </p>
        </div>
      </main>

      <!-- Footer -->
      <footer
        class="flex-shrink-0 p-3 sm:p-4 bg-gradient-to-r from-gray-100 to-gray-50 border-t flex flex-col sm:flex-row justify-end gap-2 sm:gap-3"
      >
        <button
          @click="$emit('close')"
          class="px-3 sm:px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm sm:text-base transition-all duration-150"
        >
          取消
        </button>
        <button
          @click="handleSave"
          :disabled="isSaving"
          class="px-3 sm:px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300 flex items-center gap-2 text-sm sm:text-base transition-all duration-150 shadow-sm"
        >
          {{ isSaving ? "保存中..." : "保存更改" }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, reactive } from "vue";
import PlanOutputPanel from "./PlanOutputPanel.vue";

const props = defineProps({
  show: Boolean,
  dataset: { type: Object, default: () => null },
  isSaving: Boolean,
  allConfigs: { type: Array, required: true },
});

const emit = defineEmits(["close", "save"]);

const editableData = reactive({
  id: null,
  prompt: "",
  final_answer_str: "",
  source_type: "synthetic_data",
  final_answer_obj: {},
});
const jsonError = ref(null);
const isRawJsonMode = ref(false);

watch(
  () => props.dataset,
  (newVal) => {
    if (newVal) {
      editableData.id = newVal.id;
      editableData.prompt = newVal.prompt || "";
      editableData.source_type = newVal.source_type || "synthetic_data";
      editableData.final_answer_str = JSON.stringify(
        newVal.final_answer,
        null,
        2
      );
      // 做一個淺拷貝，避免直接修改 props 裡的物件
      editableData.final_answer_obj = { ...(newVal.final_answer || {}) };

      jsonError.value = null;
      isRawJsonMode.value = false;
    }
  },
  { immediate: true, deep: true }
);

const computedSections = computed(() => {
  if (!props.dataset || !props.allConfigs) return [];

  const { grant_id, template_id, section_id } = props.dataset;
  if (!grant_id || !template_id || !section_id) return [];

  const grant = props.allConfigs.find((g) => g.id === grant_id);
  const template = grant?.templates.find((t) => t.id === template_id);
  const section = template?.sections.find((s) => s.id === section_id);

  if (section) {
    // 返回 PlanOutputPanel 期望的格式
    return [section];
  }
  return [];
});

const computedPlanContent = computed(() => {
  if (!props.dataset || !props.dataset.section_id) return {};

  // 返回 PlanOutputPanel 期望的格式
  return {
    [props.dataset.section_id]: {
      content: editableData.final_answer_obj,
      // 如果有錯誤也可以傳遞
      // error: null
    },
  };
});

// 3. 創建事件處理函數
function handlePlanUpdate({ sectionId, content }) {
  // 當 PlanOutputPanel 內部更新時，同步回我們的 editableData
  if (sectionId === props.dataset.section_id) {
    editableData.final_answer_obj = content;
  }
}

function toggleEditMode() {
  jsonError.value = null; // 切換時清除舊錯誤

  if (isRawJsonMode.value) {
    // ---- 從「原始 JSON」切換到「欄位」 ----
    try {
      const parsed = JSON.parse(editableData.final_answer_str);
      // 確保解析出來的是一個物件，而不是陣列或純文字
      if (
        typeof parsed === "object" &&
        parsed !== null &&
        !Array.isArray(parsed)
      ) {
        editableData.final_answer_obj = parsed;
        isRawJsonMode.value = false; // 切換成功
      } else {
        jsonError.value = "必須是一個有效的 JSON 物件才能切換到欄位模式。";
      }
    } catch (error) {
      jsonError.value = "JSON 格式無效，請修正後再切換模式。";
    }
  } else {
    // ---- 從「欄位」切換到「原始 JSON」 ----
    // 這個方向總是安全的
    editableData.final_answer_str = JSON.stringify(
      editableData.final_answer_obj,
      null,
      2
    );
    isRawJsonMode.value = true;
  }
}

function handleSave() {
  let finalAnswerObject;

  if (isRawJsonMode.value) {
    // 如果在原始模式，需要解析
    try {
      finalAnswerObject = JSON.parse(editableData.final_answer_str);
      jsonError.value = null;
    } catch (error) {
      jsonError.value = "JSON 格式無效，請檢查。";
      return; // 中斷保存
    }
  } else {
    // 如果在欄位模式，物件已經是最新且有效的
    finalAnswerObject = editableData.final_answer_obj;
  }

  // 發送的資料結構不變
  emit("save", {
    id: editableData.id,
    prompt: editableData.prompt,
    final_answer: finalAnswerObject, // 使用最終確定的物件
    source_type: editableData.source_type,
  });
}
</script>
