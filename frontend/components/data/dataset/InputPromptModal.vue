<!-- 模擬數據生產工作室裏面的輸入計劃名稱功能 -->
<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40"
  >
    <div
      class="bg-white rounded-lg shadow-lg p-4 sm:p-6 w-full max-w-xs sm:max-w-sm"
    >
      <h2 class="text-base sm:text-lg font-semibold mb-2">{{ title }}</h2>
      <p v-if="message" class="mb-2 sm:mb-4 text-gray-600 text-xs sm:text-base">
        {{ message }}
      </p>
      <input
        v-model="inputValue"
        :placeholder="placeholder"
        class="w-full border border-gray-300 rounded px-2 sm:px-3 py-1.5 sm:py-2 mb-3 sm:mb-4 focus:outline-none focus:ring text-xs sm:text-base"
        @keyup.enter="submit"
        autofocus
      />
      <div class="flex justify-end gap-1 sm:gap-2">
        <button @click="cancel" class="btn-secondary text-xs sm:text-base">
          取消
        </button>
        <button @click="submit" class="btn-primary text-xs sm:text-base">
          确定
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  visible: Boolean,
  title: { type: String, default: "请输入" },
  message: String,
  placeholder: String,
  defaultValue: String,
});
const emits = defineEmits(["submit", "cancel"]);

const inputValue = ref(props.defaultValue || "");

// 监听默认值变化，更新输入框内容
watch(
  () => props.defaultValue,
  (val) => {
    inputValue.value = val || "";
  },
);

// 提交输入值，发送给父组件
function submit() {
  emits("submit", inputValue.value);
}

// 取消输入，发送取消事件
function cancel() {
  emits("cancel");
}
</script>

<style scoped>
.btn-primary {
  @apply bg-indigo-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300;
}
.btn-secondary {
  @apply bg-gray-200 text-gray-700 font-semibold py-2 px-4 rounded-lg hover:bg-gray-300;
}
</style>
