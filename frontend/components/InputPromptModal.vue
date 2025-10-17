<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40"
  >
    <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-sm">
      <h2 class="text-lg font-semibold mb-2">{{ title }}</h2>
      <p v-if="message" class="mb-4 text-gray-600">{{ message }}</p>
      <input
        v-model="inputValue"
        :placeholder="placeholder"
        class="w-full border border-gray-300 rounded px-3 py-2 mb-4 focus:outline-none focus:ring"
        @keyup.enter="submit"
        autofocus
      />
      <div class="flex justify-end gap-2">
        <button @click="cancel" class="btn-secondary">取消</button>
        <button @click="submit" class="btn-primary">确定</button>
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

watch(
  () => props.defaultValue,
  (val) => {
    inputValue.value = val || "";
  }
);

function submit() {
  emits("submit", inputValue.value);
}
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
