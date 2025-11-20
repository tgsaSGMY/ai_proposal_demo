<template>
  <div
    class="space-y-3 sm:space-y-4 p-3 sm:p-4 border border-gray-200 rounded-lg bg-gray-50"
  >
    <label class="block text-xs sm:text-sm font-medium text-gray-700"
      >智能參考資料</label
    >
    <div
      v-for="(link, index) in links"
      :key="index"
      class="flex flex-col gap-2"
    >
      <!-- URL 和操作按鈕 -->
      <div class="flex items-center gap-2">
        <!-- 狀態指示器 -->
        <div
          class="flex-shrink-0 w-4 h-4 rounded-full"
          :class="getStatusClass(link.status)"
          :title="getStatusTitle(link.status)"
        ></div>

        <!-- URL 輸入框 -->
        <input
          type="url"
          :value="link.url"
          @input="updateLink(index, 'url', $event.target.value)"
          placeholder="https://example.com"
          class="flex-grow rounded-md border-gray-300 shadow-sm text-xs sm:text-sm px-2 py-1"
          :disabled="link.status === 'loading'"
        />

        <!-- 操作按鈕 -->
        <div class="flex-shrink-0 flex items-center gap-1 mt-1 xs:mt-0">
          <!-- 搜索按鈕 -->
          <button
            @click="$emit('analyze', index)"
            :disabled="!link.url || link.status === 'loading'"
            class="p-1.5 sm:p-2 text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:bg-indigo-300 text-xs sm:text-base"
          >
            <svg
              v-if="link.status === 'loading'"
              class="animate-spin h-4 w-4"
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
                d="M4 12a8 8 0 018-8V4a4 4 0 00-4 4H4z"
              ></path>
            </svg>
            <svg
              v-else
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
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </button>

          <!-- 查看重點按鈕 -->
          <button
            v-if="link.status === 'completed'"
            @click="$emit('view-summary', index)"
            class="p-1.5 sm:p-2 text-gray-600 bg-yellow-300 rounded-md hover:bg-yellow-400 text-xs sm:text-base"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"
                clip-rule="evenodd"
              />
            </svg>
          </button>

          <!-- 刪除按鈕 -->
          <button
            @click="$emit('remove', index)"
            class="p-1.5 sm:p-2 text-red-500 hover:bg-red-100 rounded-md text-xs sm:text-base"
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

      <!-- 欄位選擇 Dropdown (僅在pending且URL存在時顯示) -->
      <div
        v-if="
          link.status === 'pending' && link.url && availableFields.length > 0
        "
        class="ml-6 px-3 py-2 bg-white border border-gray-300 rounded-md"
      >
        <label class="text-xs text-gray-600 block mb-2">
          選擇要填入的欄位 (可複選)
        </label>
        <div class="flex flex-col gap-2 max-h-40 overflow-y-auto">
          <label
            v-for="field in availableFields"
            :key="field.label"
            class="flex items-center gap-2 cursor-pointer"
          >
            <input
              type="checkbox"
              :checked="(link.selectedFields || []).includes(field.label)"
              @change="
                updateSelectedFields(index, field.label, $event.target.checked)
              "
              class="rounded"
            />
            <span class="text-xs text-gray-700">{{ field.label }}</span>
          </label>
        </div>
      </div>
    </div>

    <button
      @click="$emit('add')"
      class="text-xs sm:text-sm font-medium text-indigo-600 hover:text-indigo-800"
    >
      + 新增參考連結
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  links: {
    type: Array,
    default: () => [],
  },
  availableFields: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits([
  "add",
  "remove",
  "update",
  "analyze",
  "view-summary",
]);

function updateLink(index, field, value) {
  emit("update", { index, field, value });
}

function updateSelectedFields(index, fieldLabel, isChecked) {
  const link = props.links[index];
  const currentSelected = link.selectedFields || [];
  let newSelected;

  if (isChecked) {
    newSelected = [...currentSelected, fieldLabel];
  } else {
    newSelected = currentSelected.filter((f) => f !== fieldLabel);
  }

  emit("update", {
    index,
    field: "selectedFields",
    value: newSelected,
  });
}

function getStatusClass(status) {
  switch (status) {
    case "loading":
      return "bg-blue-500 animate-pulse";
    case "completed":
      return "bg-green-500";
    case "error":
      return "bg-red-500";
    default:
      return "bg-gray-400";
  }
}

function getStatusTitle(status) {
  switch (status) {
    case "loading":
      return "分析中...";
    case "completed":
      return "分析完成";
    case "error":
      return "分析失敗";
    default:
      return "待處理";
  }
}
</script>
