<template>
  <div class="space-y-3">
    <div
      v-for="(value, key) in fields"
      :key="key"
      class="space-y-1.5 p-2.5 bg-white rounded-lg border border-gray-200"
    >
      <!-- Key 显示 (不可修改) -->
      <div class="flex items-center justify-between">
        <label class="text-xs sm:text-sm font-medium text-gray-700">
          {{ key }}
        </label>
      </div>

      <!-- 根据 value 类型递归渲染 -->
      <div v-if="isString(value)" class="space-y-1">
        <textarea
          :value="value"
          @input="updateValue(key, $event.target.value)"
          rows="3"
          placeholder="輸入說明..."
          class="w-full border border-gray-300 rounded-lg px-2 sm:px-3 py-1.5 sm:py-2 text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none bg-white"
        ></textarea>
      </div>

      <!-- 如果是 Object，递归编辑子属性 -->
      <div
        v-else-if="isObject(value) && !isArray(value)"
        class="ml-2 sm:ml-3 space-y-2"
      >
        <JsonSchemaEditor
          :fields="value"
          @update="(k, v) => updateNestedValue(key, k, v)"
          :depth="(depth || 0) + 1"
        />
      </div>

      <!-- 如果是 Array，处理数组元素 -->
      <div v-else-if="isArray(value)" class="ml-2 sm:ml-3 space-y-2">
        <div
          v-for="(item, index) in value"
          :key="index"
          class="p-2 bg-gray-50 rounded border border-gray-200 space-y-1.5"
        >
          <div class="text-xs text-gray-500 font-medium">
            項目 {{ index + 1 }}
          </div>

          <!-- 数组中的字符串 -->
          <textarea
            v-if="isString(item)"
            :value="item"
            @input="updateArrayItem(key, index, $event.target.value)"
            rows="4"
            placeholder="輸入說明..."
            class="w-full border border-gray-300 rounded-lg px-2 sm:px-3 py-1.5 sm:py-2 text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none bg-white"
          ></textarea>

          <!-- 数组中的对象 -->
          <div v-else-if="isObject(item)" class="space-y-1.5">
            <JsonSchemaEditor
              :fields="item"
              @update="(k, v) => updateNestedArrayValue(key, index, k, v)"
              :depth="(depth || 0) + 2"
            />
          </div>
        </div>
      </div>

      <!-- 如果是其他类型（数字、布尔值等），显示为 JSON -->
      <div v-else class="text-xs text-gray-500 p-2 bg-gray-100 rounded">
        {{ JSON.stringify(value) }}
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  fields: {
    type: Object,
    required: true,
  },
  depth: {
    type: Number,
    default: 0,
  },
});

const emit = defineEmits(["update"]);

// 类型判断函数
function isString(val) {
  return typeof val === "string";
}

function isObject(val) {
  return val !== null && typeof val === "object" && !Array.isArray(val);
}

function isArray(val) {
  return Array.isArray(val);
}

// 更新顶层值
function updateValue(key, newValue) {
  emit("update", key, newValue);
}

// 更新嵌套对象的值
function updateNestedValue(parentKey, childKey, newValue) {
  const updated = { ...props.fields[parentKey], [childKey]: newValue };
  emit("update", parentKey, updated);
}

// 更新数组中的字符串项
function updateArrayItem(key, index, newValue) {
  const updated = [...props.fields[key]];
  updated[index] = newValue;
  emit("update", key, updated);
}

// 更新数组中的对象项的子属性
function updateNestedArrayValue(parentKey, arrayIndex, childKey, newValue) {
  const updated = [...props.fields[parentKey]];
  updated[arrayIndex] = { ...updated[arrayIndex], [childKey]: newValue };
  emit("update", parentKey, updated);
}
</script>
