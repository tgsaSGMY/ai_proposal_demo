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
            <!-- 內部模型標籤 -->
            <button
              @click="activeTab = 'internal'"
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
              外部模型
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
        <div
          class="max-h-80 overflow-y-auto pr-1 sm:pr-2 space-y-2 sm:space-y-3"
        >
          <!-- 內部模型列表 -->
          <div v-if="activeTab === 'internal'">
            <div
              v-for="model in internalModels"
              :key="model.id"
              @click="selectedInternalModelId = model.id"
              :class="[
                'p-3 sm:p-4 border rounded-lg cursor-pointer transition-all',
                selectedInternalModelId === model.id
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
                  v-if="selectedInternalModelId === model.id"
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

          <!-- 外部模型列表 -->
          <div v-if="activeTab === 'external'">
            <div
              v-for="model in externalModels"
              :key="model.id"
              @click="selectedExternalModelId = model.id"
              :class="[
                'p-3 sm:p-4 border rounded-lg cursor-pointer transition-all',
                selectedExternalModelId === model.id
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
                  v-if="selectedExternalModelId === model.id"
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

          <!-- 章節編輯 -->
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
import { supabase } from "~/utils/supabaseClient";
import SectionSettingsPanel from "~/components/SectionSettingsPanel.vue";

const props = defineProps({
  section: { type: Object, required: true },
  models: { type: Array, required: true },
  currentInternalRule: { type: Object, default: null },
  currentExternalRule: { type: Object, default: null },
  routingRules: { type: Array, required: true },
  templateId: { type: String, default: null },
  grantId: { type: String, default: null },
});

const emit = defineEmits(["close", "save", "settings-updated", "delete"]);

const isSavingSettings = ref(false);
const config = useRuntimeConfig();
const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

const activeTab = ref("external");
const selectedInternalModelId = ref(null);
const selectedExternalModelId = ref(null);
const settingsPanelRef = ref(null);

// 計算當前規則應用的模型ID
const currentInternalModelId = computed(
  () => props.currentInternalRule?.model_id
);
const currentExternalModelId = computed(
  () => props.currentExternalRule?.model_id
);

// 所有模型在兩個標籤頁中都可用
const internalModels = computed(() => props.models);
const externalModels = computed(() => props.models);

// 初始化
onMounted(() => {
  // 初始化內部模型選擇
  if (currentInternalModelId.value) {
    selectedInternalModelId.value = currentInternalModelId.value;
  }

  // 初始化外部模型選擇
  if (currentExternalModelId.value) {
    selectedExternalModelId.value = currentExternalModelId.value;
  } else {
    // 如果沒有外部模型規則，預設為第一個可用的模型
    if (props.models.length > 0) {
      selectedExternalModelId.value = props.models[0].id;
    }
  }
});

async function saveChanges() {
  try {
    // 處理內部模型規則
    if (
      selectedInternalModelId.value &&
      selectedInternalModelId.value !== currentInternalModelId.value
    ) {
      const internalPayload = {
        grant_id: props.grantId || null,
        template_id: props.templateId || null,
        section_id: props.section.id,
        model_id: selectedInternalModelId.value,
        priority: 20,
        description: `內部模型配置`,
        is_external: false,
      };
      emit("save", internalPayload);
    }

    // 處理外部模型規則
    if (
      selectedExternalModelId.value &&
      selectedExternalModelId.value !== currentExternalModelId.value
    ) {
      const externalPayload = {
        grant_id: props.grantId || null,
        template_id: props.templateId || null,
        section_id: props.section.id,
        model_id: selectedExternalModelId.value,
        priority: 20,
        description: `外部模型配置`,
        is_external: true,
      };
      emit("save", externalPayload);
    }

    // 如果在 prompt 編輯頁面或者有可能編輯過 prompt，儲存 prompt 設定
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
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) throw new Error("請先登入");

    const response = await fetch(
      `${API_BASE_URL}/sections/${props.section.id}/prompts`,
      {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
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
    const { success } = useNotifications();
    success("Prompt 設定已成功保存！");
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
