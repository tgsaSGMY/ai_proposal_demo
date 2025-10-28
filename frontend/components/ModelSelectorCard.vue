<template>
  <div
    class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 transition-opacity"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white rounded-2xl shadow-xl w-full max-w-sm sm:max-w-lg md:max-w-2xl transform transition-all"
    >
      <div class="p-4 sm:p-6 border-b border-gray-200">
        <h3 class="text-base sm:text-xl font-semibold text-gray-800">
          為「{{ section.name }}」配置模型
        </h3>
        <p class="text-xs sm:text-sm text-gray-500 mt-1">
          選擇一個模型來處理這個章節的生成任務。
        </p>
      </div>

      <div class="p-4 sm:p-6">
        <!-- 內/外部模型切換 Bar -->
        <div class="mb-4 sm:mb-6 flex justify-center">
          <div class="bg-gray-100 p-1 rounded-lg flex space-x-1">
            <!-- 注意：内部模型暫時關閉，等未來擁有足夠多的數據在訓練模型 -->
            <button
              @click="activeTab = 'internal'"
              v-if="false"
              :class="[
                'px-4 sm:px-6 py-2 text-xs sm:text-sm font-medium rounded-md transition',
                activeTab === 'internal'
                  ? 'bg-white shadow text-indigo-600'
                  : 'text-gray-600 hover:bg-gray-200',
              ]"
            >
              內部模型
            </button>
            <button
              @click="activeTab = 'external'"
              :class="[
                'px-4 sm:px-6 py-2 text-xs sm:text-sm font-medium rounded-md transition',
                activeTab === 'external'
                  ? 'bg-white shadow text-indigo-600'
                  : 'text-gray-600 hover:bg-gray-200',
              ]"
            >
              模型選擇
            </button>
            <button
              @click="activeTab = 'prompt'"
              :class="[
                'px-4 sm:px-6 py-2 text-xs sm:text-sm font-medium rounded-md transition',
                activeTab === 'prompt'
                  ? 'bg-white shadow text-indigo-600'
                  : 'text-gray-600 hover:bg-gray-200',
              ]"
            >
              章節編輯
            </button>
          </div>
        </div>

        <!-- 模型列表 -->
        <!-- 注意：内部模型暫時關閉，等未來擁有足夠多的數據在訓練模型 -->
        <div
          class="max-h-80 overflow-y-auto pr-1 sm:pr-2 space-y-2 sm:space-y-3"
        >
          <div v-if="false && activeTab === 'internal'">
            <div
              v-for="model in internalModels"
              :key="model.id"
              @click="selectedModelId = model.id"
              :class="[
                'p-3 sm:p-4 border rounded-lg cursor-pointer transition-all',
                selectedModelId === model.id
                  ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-300'
                  : 'border-gray-200 hover:border-indigo-400 hover:bg-indigo-50',
              ]"
            >
              <div class="flex justify-between items-center">
                <div>
                  <p class="font-semibold text-xs sm:text-base text-gray-800">
                    {{ model.display_name }}
                  </p>
                  <p class="text-[10px] sm:text-xs text-gray-500 mt-1">
                    {{ model.description }}
                  </p>
                </div>
                <svg
                  v-if="selectedModelId === model.id"
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-6 w-6 text-indigo-600"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
            </div>
            <p
              v-if="!internalModels.length"
              class="text-center text-gray-500 py-6 text-xs sm:text-sm"
            >
              暫無內部模型
            </p>
          </div>

          <div v-if="activeTab === 'external'">
            <div
              v-for="model in externalModels"
              :key="model.id"
              @click="selectedModelId = model.id"
              :class="[
                'p-3 sm:p-4 border rounded-lg cursor-pointer transition-all',
                selectedModelId === model.id
                  ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-300'
                  : 'border-gray-200 hover:border-indigo-400 hover:bg-indigo-50',
              ]"
            >
              <div class="flex justify-between items-center">
                <div>
                  <p class="font-semibold text-xs sm:text-base text-gray-800">
                    {{ model.display_name }}
                  </p>
                  <p class="text-[10px] sm:text-xs text-gray-500 mt-1">
                    {{ model.description }}
                  </p>
                </div>
                <svg
                  v-if="selectedModelId === model.id"
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-6 w-6 text-indigo-600"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
            </div>
            <p
              v-if="!externalModels.length"
              class="text-center text-gray-500 py-6 text-xs sm:text-sm"
            >
              暫無外部模型
            </p>
          </div>
          <div v-if="activeTab === 'prompt'">
            <SectionSettingsPanel
              ref="settingsPanelRef"
              :sectionData="{
                sectionName: section.name,
                system_prompt: section.system_prompt,
                custom_prompt_list: section.custom_prompt_list,
              }"
              :is-saving="isSavingSettings"
            />
          </div>
        </div>
      </div>

      <div
        class="p-4 sm:p-6 bg-gray-50 rounded-b-2xl flex flex-col sm:flex-row justify-end items-stretch sm:items-center gap-2 sm:gap-4"
      >
        <button
          @click="$emit('close')"
          class="px-4 sm:px-6 py-2 text-xs sm:text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          取消
        </button>
        <button
          @click="saveChanges"
          class="px-4 sm:px-6 py-2 text-xs sm:text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300"
        >
          儲存變更
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import SectionSettingsPanel from "~/components/SectionSettingsPanel.vue";

const props = defineProps({
  section: { type: Object, required: true },
  models: { type: Array, required: true },
  currentRule: { type: Object, default: null },
  defaultModelId: { type: String, default: null },
  templateId: { type: String, default: null },
  grantId: { type: String, default: null },
});

const emit = defineEmits(["close", "save", "settings-updated", "delete"]);

const isSavingSettings = ref(false);
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const activeTab = ref("internal");
const selectedModelId = ref(null);
const settingsPanelRef = ref(null);
const defaultModelId = ref(null);

// 計算當前規則應用的模型ID
const currentModelId = computed(() => props.currentRule?.model_id);

// 計算默認模型ID（通過 props 傳入的 defaultModel）
const computedDefaultModelId = computed(
  () => props.defaultModelId || defaultModelId.value
);

// 分離內部和外部模型
const internalModels = computed(() =>
  props.models.filter((m) => m.type === "internal")
);
const externalModels = computed(() =>
  props.models.filter((m) => m.type === "external")
);

// 初始化
onMounted(() => {
  if (currentModelId.value) {
    selectedModelId.value = currentModelId.value;
    const currentModel = props.models.find(
      (m) => m.id === currentModelId.value
    );
    if (currentModel) {
      activeTab.value = currentModel.type;
    }
  } else if (internalModels.value.length > 0) {
    activeTab.value = "internal";
  } else {
    activeTab.value = "external";
  }
});

async function saveChanges() {
  try {
    // 1. 如果有模型選擇變更，判斷是否需要儲存或刪除
    if (
      selectedModelId.value &&
      selectedModelId.value !== currentModelId.value
    ) {
      if (
        computedDefaultModelId.value &&
        selectedModelId.value === computedDefaultModelId.value
      ) {
        // 發出刪除事件，由父組件處理刪除
        if (props.currentRule?.id) {
          emit("delete", props.currentRule.id);
        }
      } else {
        // 否則，創建新規則
        const newRulePayload = {
          grant_id: props.grantId || null,
          template_id: props.templateId || null,
          section_id: props.section.id,
          model_id: selectedModelId.value,
          priority: 20,
          description: `特定模型配置`,
        };
        emit("save", newRulePayload);
      }
    }

    // 2. 如果在 prompt 編輯頁面或者有可能編輯過 prompt，儲存 prompt 設定
    if (settingsPanelRef.value) {
      const updatedSettings = settingsPanelRef.value.getEditableData();
      await handleSaveSettings(updatedSettings);
    }

    emit("close");
  } catch (error) {
    console.error("保存過程中發生錯誤:", error);
  }
}

// ---處理 Prompt 保存的新函數 ---
async function handleSaveSettings(updatedSettings) {
  if (!updatedSettings) return;

  isSavingSettings.value = true;
  try {
    const response = await fetch(
      `${API_BASE_URL}/sections/${props.section.id}/prompts`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...updatedSettings,
          grant_id: props.grantId,
          template_id: props.templateId,
        }),
      }
    );
    if (!response.ok) {
      throw new Error("保存 Prompt 設定失敗");
    }

    // 通知父組件(model.vue)數據已更新，以便刷新列表
    emit("settings-updated", {
      sectionId: props.section.id,
      ...updatedSettings,
    });
  } catch (err) {
    console.error("保存 Prompt 設定錯誤:", err);
    const { error } = useNotifications();
    error(err.message);
  } finally {
    isSavingSettings.value = false;
  }
}
</script>
