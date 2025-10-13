<template>
  <div class="bg-white shadow-xl rounded-2xl p-8 h-full flex flex-col">
    <!-- 第一层：主题 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2"
          >1. 選擇主題</label
        >
        <select
          v-model="selectedGrantId"
          @change="onGrantChange"
          class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition"
        >
          <option disabled value="">請選擇</option>
          <option v-for="grant in allConfigs" :key="grant.id" :value="grant.id">
            {{ grant.name }}
          </option>
        </select>
      </div>
      <div>
        <!-- 第二层：模板 -->
        <label class="block text-sm font-medium text-gray-700 mb-2"
          >2. 選擇模板</label
        >
        <select
          v-model="selectedTemplateId"
          :disabled="!selectedGrantId"
          class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition disabled:bg-gray-100"
        >
          <option disabled value="">請選擇</option>
          <option
            v-for="template in availableTemplates"
            :key="template.id"
            :value="template.id"
          >
            {{ template.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- 第三层： 用户输入 + 辅助输入框 -->
    <div class="mb-6 space-y-6 flex-grow flex flex-col min-h-0">
      <!-- 主想法输入框 -->
      <div class="flex-shrink-0">
        <div class="flex justify-between items-center mb-2">
          <label class="block text-sm font-medium text-gray-700"
            >3. 描述你的核心項目／想法</label
          >
          <button
            v-if="mode === 'synthetic'"
            @click="$emit('generateUserInput')"
            class="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-lg hover:bg-gray-200 transition-colors"
            title="讓 AI 生成一個創新的項目想法"
          >
            ✨ 隨機生成想法
          </button>
        </div>
        <textarea
          :value="userInput"
          @input="$emit('update:userInput', $event.target.value)"
          placeholder="例如：一個利用 AI 分析使用者評論，自動生成產品優化建議的 SaaS 平台..."
          rows="8"
          class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition resize-y p-2"
        ></textarea>
      </div>

      <!-- 根据grants & template 动态生成的辅助输入框区域 -->
      <div
        v-if="dynamicInputs.length > 0"
        class="space-y-6 border-t border-gray-200 pt-6 flex-grow overflow-y-auto pr-2"
      >
        <div class="p-4 bg-indigo-50 border border-indigo-200 rounded-lg mb-6">
          <p class="text-sm text-indigo-700">
            <span class="font-semibold">專業提示：</span> 填寫以下細節能讓 AI
            生成更精準、更出色的內容！
          </p>
        </div>

        <!-- 外層 v-for 遍歷 section 分組 -->
        <div
          v-for="(group, groupIndex) in dynamicInputs"
          :key="group.sectionId"
          class="space-y-4"
        >
          <!-- 顯示 Section 標題 -->
          <h4 class="text-md font-semibold text-gray-800 border-b pb-2">
            {{ group.sectionName }}
          </h4>

          <div
            class="p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-3"
          >
            <label class="block text-sm font-medium text-gray-700"
              >客製化指令 (Custom Prompts)</label
            >

            <!-- 列表顯示現有指令 -->
            <div
              v-if="
                group.custom_prompt_list && group.custom_prompt_list.length > 0
              "
              class="space-y-2"
            >
              <div
                v-for="(prompt, promptIndex) in group.custom_prompt_list"
                :key="promptIndex"
                class="flex items-center gap-2"
              >
                <input
                  type="text"
                  :value="prompt"
                  @input="
                    handlePromptInput(
                      groupIndex,
                      promptIndex,
                      $event.target.value
                    )
                  "
                  placeholder="輸入指令..."
                  class="flex-grow w-full rounded-md border-gray-300 shadow-sm sm:text-sm p-2"
                />
                <button
                  @click="deletePrompt(groupIndex, promptIndex)"
                  class="p-1.5 text-red-500 hover:bg-red-100 rounded-full"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>
            </div>

            <!-- 新增按鈕 -->
            <button
              @click="addPrompt(groupIndex)"
              class="text-sm font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z"
                  clip-rule="evenodd"
                />
              </svg>
              新增指令
            </button>
          </div>

          <!-- 內層 v-for 遍歷該分組內的 inputs -->
          <div v-for="(input, inputIndex) in group.inputs" :key="input.id">
            <label
              :for="input.id"
              class="block text-sm font-medium text-gray-600 mb-2"
            >
              {{ input.label }}
            </label>
            <textarea
              :id="input.id"
              :value="input.value"
              @input="
                updateDynamicInput(groupIndex, inputIndex, $event.target.value)
              "
              :placeholder="`關於「${input.label}」的更多細節...`"
              rows="3"
              class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition resize-y p-2"
            ></textarea>
          </div>
        </div>
      </div>
    </div>

    <!-- 生成机会按钮 -->
    <button
      @click="emitGeneratePlan"
      :disabled="isGenerating || mode === 'golden' || !isReadyToGenerate"
      class="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-3 rounded-lg shadow-md hover:bg-indigo-700 disabled:bg-indigo-300 disabled:cursor-not-allowed transition-all duration-300"
    >
      <svg
        v-if="isGenerating"
        class="animate-spin h-5 w-5 text-white"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        ></circle>
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
        ></path>
      </svg>
      {{ isGenerating ? "正在生成..." : "生成完整計劃書" }}
      <span v-if="mode === 'golden'" class="text-xs font-normal opacity-75"
        >(在 Golden Sample 模式下禁用)</span
      >
    </button>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from "vue";

const props = defineProps({
  allConfigs: { type: Array, required: true },
  userInput: { type: String, required: true },
  isGenerating: { type: Boolean, default: false },
  dynamicInputs: { type: Array, required: true },
  mode: { type: String, required: true },
});

const emit = defineEmits([
  "update:userInput",
  "selectionChange",
  "generatePlan",
  "generateUserInput",
  "update:dynamicInputs",
]);

// 內部狀態（僅用於選擇器）
const selectedGrantId = ref("");
const selectedTemplateId = ref("");
const API_BASE_URL = "http://127.0.0.1:8000/api";
const debounceTimers = ref({});
const isSavingPrompts = ref({});

// 計算屬性（模板和章節）
const availableTemplates = computed(() => {
  if (!selectedGrantId.value) return [];
  const grant = props.allConfigs.find((g) => g.id === selectedGrantId.value);
  return grant ? grant.templates : [];
});

const isReadyToGenerate = computed(() => {
  return selectedTemplateId.value && props.userInput.trim();
});

// 當選擇變化時，通知父組件
watch([selectedGrantId, selectedTemplateId], () => {
  emit("selectionChange", {
    grantId: selectedGrantId.value,
    templateId: selectedTemplateId.value,
  });
});

// 當用戶在動態輸入框中輸入時，通知父組件更新
function updateDynamicInput(groupIndex, inputIndex, value) {
  const newInputs = [...props.dynamicInputs];
  newInputs[groupIndex].inputs[inputIndex].value = value;
  emit("update:dynamicInputs", newInputs);
}

// onGrantChange 和 emitGeneratePlan 保持不變
const onGrantChange = () => {
  selectedTemplateId.value = "";
};

const emitGeneratePlan = () => {
  if (!isReadyToGenerate.value) return;
  emit("generatePlan");
};

async function savePrompts(sectionId, promptsToSave) {
  // 檢查是否已在保存中，如果是，則忽略此次調用
  if (isSavingPrompts.value[sectionId]) {
    return;
  }

  // 設置鎖定
  isSavingPrompts.value[sectionId] = true;

  // 過濾掉所有空的指令
  const filteredPrompts = promptsToSave.filter((p) => p && p.trim() !== "");

  try {
    const response = await fetch(
      `${API_BASE_URL}/sections/${sectionId}/prompts`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompts: filteredPrompts }),
      }
    );
    if (!response.ok) {
      throw new Error("Failed to save prompts");
    }

    // 保存成功後，將最終的、經過過濾的數據同步回父組件
    const newInputs = JSON.parse(JSON.stringify(props.dynamicInputs));
    const groupIndex = newInputs.findIndex((g) => g.sectionId === sectionId);
    if (groupIndex !== -1) {
      newInputs[groupIndex].custom_prompt_list = filteredPrompts;
      emit("update:dynamicInputs", newInputs);
    }
  } catch (error) {
    console.error("Error saving prompts:", error);
    alert("保存自定義指令失敗！");
    // 可選：在這裡可以做數據回滾
  } finally {
    // 解除鎖定
    isSavingPrompts.value[sectionId] = false;
  }
}
// --- 新增: 處理 @input 事件的函數 ---
function handlePromptInput(groupIndex, promptIndex, value) {
  // 1. 立即更新本地 UI 狀態
  const newInputs = JSON.parse(JSON.stringify(props.dynamicInputs));
  const sectionId = newInputs[groupIndex].sectionId;
  newInputs[groupIndex].custom_prompt_list[promptIndex] = value;
  emit("update:dynamicInputs", newInputs);

  // 2. 設置防抖計時器
  if (debounceTimers.value[sectionId]) {
    clearTimeout(debounceTimers.value[sectionId]);
  }

  // 延遲調用時，傳遞當前最新的 prompt 列表
  const promptsToSaveOnDebounce = newInputs[groupIndex].custom_prompt_list;
  debounceTimers.value[sectionId] = setTimeout(() => {
    savePrompts(sectionId, promptsToSaveOnDebounce);
  }, 800);
}

function deletePrompt(groupIndex, promptIndex) {
  if (!confirm("確定要刪除這條指令嗎？")) return;

  const newInputs = JSON.parse(JSON.stringify(props.dynamicInputs));
  const group = newInputs[groupIndex];
  const sectionId = group.sectionId;

  // 1. 清除任何待處理的保存操作，這是最關鍵的一步
  if (debounceTimers.value[sectionId]) {
    clearTimeout(debounceTimers.value[sectionId]);
    debounceTimers.value[sectionId] = null; // 清空 timer id
  }

  // 2. 從本地數組中移除 prompt
  group.custom_prompt_list.splice(promptIndex, 1);

  // 3. 立即更新 UI，讓用戶看到刪除效果
  emit("update:dynamicInputs", newInputs);

  // 4. 直接調用 savePrompts，傳遞刪除後的新數組
  savePrompts(sectionId, group.custom_prompt_list);
}

function addPrompt(groupIndex) {
  const newInputs = JSON.parse(JSON.stringify(props.dynamicInputs));
  if (!newInputs[groupIndex].custom_prompt_list) {
    newInputs[groupIndex].custom_prompt_list = [];
  }
  newInputs[groupIndex].custom_prompt_list.push("");
  emit("update:dynamicInputs", newInputs);
}
</script>
