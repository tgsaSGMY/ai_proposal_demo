<!-- /components/BatchSyntheticModal.vue -->
<template>
  <div
    v-if="visible"
    @click.self="close"
    class="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center"
  >
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
      <h2 class="text-xl font-bold text-gray-800 mb-4">批量生成 AI 企划</h2>
      <p class="text-sm text-gray-600 mb-6">
        选择主题和模板，然后设定要生成的企划数量。系统将在后台为您生成多个独特的项目想法。
      </p>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700"
            >主题 (Grant)</label
          >
          <select v-model="selectedGrantId" class="select-class mt-1">
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
          <label class="block text-sm font-medium text-gray-700"
            >模板 (Template)</label
          >
          <select
            v-model="selectedTemplateId"
            :disabled="!selectedGrantId"
            class="select-class mt-1 disabled:bg-gray-50"
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
          <label class="block text-sm font-medium text-gray-700"
            >生成数量: {{ count }}</label
          >
          <input
            type="range"
            v-model.number="count"
            min="1"
            max="20"
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer mt-2"
          />
        </div>
      </div>

      <div class="mt-8 flex justify-end gap-3">
        <button @click="close" class="btn-secondary">取消</button>
        <button
          @click="startBatch"
          :disabled="!selectedTemplateId"
          class="btn-primary"
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
  });
  close();
}
</script>
