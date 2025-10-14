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
          <div
            @click="mode !== 'generator' && openSettingsModal(groupIndex)"
            :class="{ 'cursor-pointer': mode !== 'generator' }"
            class="group flex items-center justify-between border-b pb-2"
          >
            <h4
              class="text-md font-semibold text-gray-800 transition-colors"
              :class="{ 'group-hover:text-indigo-600 ': mode !== 'generator' }"
            >
              {{ group.sectionName }}
            </h4>
            <span
              v-if="mode !== 'generator'"
              class="text-xs text-gray-400 group-hover:text-indigo-500 transition-colors flex items-center gap-1"
            >
              <svg
                class="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              編輯設定
            </span>
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
    <SectionSettingsModal
      :show="isModalVisible"
      :sectionData="currentEditingSection"
      :is-saving="isSaving"
      @close="closeSettingsModal"
      @save="handleSaveSettings"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from "vue";
import { useNotifications } from "~/composables/useNotifications";
const { success, error: errorNotification } = useNotifications();

const props = defineProps({
  allConfigs: { type: Array, required: true },
  userInput: { type: String, required: true },
  isGenerating: { type: Boolean, default: false },
  dynamicInputs: { type: Array, required: true },
  mode: { type: String, required: true },
  initialGrantId: { type: String, default: "" }, // 新 prop
  initialTemplateId: { type: String, default: "" },
});

const emit = defineEmits([
  "update:userInput",
  "selectionChange",
  "generatePlan",
  "generateUserInput",
  "update:dynamicInputs",
]);

// 內部狀態（僅用於選擇器）
const isModalVisible = ref(false);
const isSaving = ref(false);
const currentEditingSection = ref(null);
const currentEditingIndex = ref(-1);

const selectedGrantId = ref(props.initialGrantId);
const selectedTemplateId = ref(props.initialTemplateId);
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

watch(
  () => props.initialGrantId,
  (newVal) => {
    if (selectedGrantId.value !== newVal) {
      selectedGrantId.value = newVal;
    }
  }
);

watch(
  () => props.initialTemplateId,
  (newVal) => {
    // 检查内部状态是否与 prop 不同步，如果是，则更新它
    if (selectedTemplateId.value !== newVal) {
      console.log(
        `子组件检测到 templateId prop 变化，从 '${selectedTemplateId.value}' 更新为 '${newVal}'`
      );
      selectedTemplateId.value = newVal;
    }
    console.log(selectedTemplateId.value);
  }
);

// 計算屬性（模板和章節）
const availableTemplates = computed(() => {
  if (!selectedGrantId.value) return [];
  const grant = props.allConfigs.find((g) => g.id === selectedGrantId.value);
  return grant ? grant.templates : [];
});

const isReadyToGenerate = computed(() => {
  return selectedTemplateId.value && props.userInput.trim();
});

watch([selectedGrantId, selectedTemplateId], () => {
  // 检查是否是由于 props 更新导致的 watch 触发，避免无限循环
  // 只有当内部状态与 props 不同时，才认为是用户操作
  console.log(selectedTemplateId.value, props.initialTemplateId);
  if (
    selectedGrantId.value !== props.initialGrantId ||
    selectedTemplateId.value !== props.initialTemplateId
  ) {
    console.log("trigger");
    emit("selectionChange", {
      grantId: selectedGrantId.value,
      templateId: selectedTemplateId.value,
    });
  }
});

// 當用戶在動態輸入框中輸入時，通知父組件更新
function updateDynamicInput(groupIndex, inputIndex, value) {
  const newInputs = [...props.dynamicInputs];
  newInputs[groupIndex].inputs[inputIndex].value = value;
  emit("update:dynamicInputs", newInputs);
}

// onGrantChange 和 emitGeneratePlan 保持不變
const onGrantChange = () => {
  const isIncluded = availableTemplates.value.some(
    (t) => t.id === selectedTemplateId.value
  );

  if (!isIncluded) {
    selectedTemplateId.value = "";
  }
};

const emitGeneratePlan = () => {
  if (!isReadyToGenerate.value) return;
  emit("generatePlan");
};

function openSettingsModal(index) {
  currentEditingIndex.value = index;
  currentEditingSection.value = props.dynamicInputs[index];
  isModalVisible.value = true;
}

function closeSettingsModal() {
  isModalVisible.value = false;
  currentEditingSection.value = null;
  currentEditingIndex.value = -1;
}

async function handleSaveSettings(updatedSettings) {
  if (currentEditingIndex.value === -1 || !currentEditingSection.value) return;

  isSaving.value = true;
  const sectionId = currentEditingSection.value.sectionId;

  try {
    const response = await fetch(
      `${API_BASE_URL}/sections/${sectionId}/prompts`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedSettings),
      }
    );
    if (!response.ok) {
      throw new Error("保存設定失敗");
    }

    // 更新本地狀態並通知父組件
    const newInputs = JSON.parse(JSON.stringify(props.dynamicInputs));
    newInputs[currentEditingIndex.value].system_prompt =
      updatedSettings.system_prompt;
    newInputs[currentEditingIndex.value].custom_prompt_list =
      updatedSettings.prompts;
    emit("update:dynamicInputs", newInputs);

    success("章節設定已成功保存！");
    closeSettingsModal();
  } catch (err) {
    showError(err.message);
  } finally {
    isSaving.value = false;
  }
}
</script>
