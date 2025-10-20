<!-- /components/BatchSyntheticModal.vue -->
<template>
  <div
    v-if="visible"
    @click.self="close"
    class="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center p-2 sm:p-0"
  >
    <div
      class="bg-white rounded-lg shadow-xl w-full max-w-xs sm:max-w-md p-3 sm:p-6"
    >
      <h2 class="text-lg sm:text-xl font-bold text-gray-800 mb-2 sm:mb-4">
        批量生成 AI 企划
      </h2>
      <p class="text-xs sm:text-sm text-gray-600 mb-4 sm:mb-6">
        选择主题和模板，然后设定要生成的企划数量。系统将在后台为您生成多个独特的项目想法。
      </p>

      <div class="space-y-3 sm:space-y-4">
        <div>
          <label class="block text-xs sm:text-sm font-medium text-gray-700"
            >主题 (Grant)</label
          >
          <select
            v-model="selectedGrantId"
            class="select-class mt-1 text-xs sm:text-sm"
          >
            <option disabled value="">请选择主题</option>
            <option
              v-for="grant in allConfigs"
              :key="grant.id"
              :value="grant.id"
            >
              {{ grant.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-xs sm:text-sm font-medium text-gray-700"
            >模板 (Template)</label
          >
          <select
            v-model="selectedTemplateId"
            :disabled="!selectedGrantId"
            class="select-class mt-1 disabled:bg-gray-50 text-xs sm:text-sm"
          >
            <option disabled value="">请选择模板</option>
            <option
              v-for="template in availableTemplates"
              :key="template.id"
              :value="template.id"
            >
              {{ template.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-xs sm:text-sm font-medium text-gray-700"
            >生成数量: {{ count }}</label
          >
          <input
            type="range"
            v-model.number="count"
            min="1"
            max="20"
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer mt-1 sm:mt-2"
          />
        </div>
      </div>

      <div class="mt-6 sm:mt-8 flex justify-end gap-2 sm:gap-3">
        <button
          @click="close"
          class="btn-secondary text-xs sm:text-base px-3 sm:px-4 py-1.5 sm:py-2"
        >
          取消
        </button>
        <button
          @click="startBatch"
          :disabled="!selectedTemplateId"
          class="btn-primary text-xs sm:text-base px-3 sm:px-4 py-1.5 sm:py-2"
        >
          开始生成
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  visible: Boolean,
  allConfigs: Array,
});
const emit = defineEmits(["close", "start"]);

const count = ref(5);
const selectedGrantId = ref("");
const selectedTemplateId = ref("");

const availableTemplates = computed(() => {
  if (!selectedGrantId.value) return [];
  const grant = props.allConfigs.find((g) => g.id === selectedGrantId.value);
  return grant ? grant.templates : [];
});

watch(
  () => props.visible,
  (newVal) => {
    if (!newVal) {
      selectedGrantId.value = "";
      selectedTemplateId.value = "";
      count.value = 5;
    }
  }
);

function close() {
  emit("close");
}

function startBatch() {
  emit("start", {
    count: count.value,
    grant_id: selectedGrantId.value,
    template_id: selectedTemplateId.value,
    user_id: "dba4dabc-a24d-4e1a-aa2b-b239d06a8cf5",
  });
  close();
}
</script>
