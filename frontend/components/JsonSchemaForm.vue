<template>
  <div class="space-y-4 sm:space-y-6">
    <div v-for="(propInfo, key) in schema.properties" :key="key">
      <label class="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2">
        {{ propInfo.description || propInfo.title || key }}
      </label>

      <!-- 渲染 String 類型的字段 -->
      <template v-if="propInfo.type === 'string'">
        <textarea
          :value="modelValue[key]"
          @input="updateValue(key, $event.target.value)"
          rows="5"
          class="p-2 w-full font-mono text-xs sm:text-sm bg-gray-100 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 transition"
        ></textarea>
      </template>

      <template v-else-if="propInfo.type === 'number'">
        <input
          type="number"
          :value="modelValue[key]"
          @input="updateValue(key, parseFloat($event.target.value))"
          class="p-2 w-full font-mono text-xs sm:text-sm bg-gray-100 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 transition"
        />
      </template>

      <!-- 渲染 Array 類型的字段 -->
      <template
        v-else-if="
          propInfo.type === 'array' && propInfo.items.type === 'object'
        "
      >
  <div class="space-y-2 sm:space-y-4 p-3 sm:p-4 border border-gray-200 rounded-lg bg-gray-50">
          <div
            v-for="(item, index) in modelValue[key]"
            :key="index"
            class="p-2 sm:p-4 border border-dashed border-gray-300 rounded-lg relative"
          >
            <h4 class="font-semibold mb-2 sm:mb-3 text-xs sm:text-sm text-gray-600">
              項目 #{{ index + 1 }}
            </h4>
            <!-- 遞歸渲染數組內對象的表單 -->
            <JsonSchemaForm
              :schema="propInfo.items"
              :modelValue="item"
              @update:modelValue="updateArrayItem(key, index, $event)"
            />
            <button
              @click="removeArrayItem(key, index)"
              class="absolute top-2 right-2 text-red-500 hover:text-red-700 p-1 rounded-full bg-red-100 hover:bg-red-200 text-xs sm:text-base"
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <button
            @click="addArrayItem(key, propInfo.items.properties)"
            class="text-xs sm:text-sm font-medium text-indigo-600 hover:text-indigo-800"
          >
            + 新增項目
          </button>
        </div>
      </template>

      <!-- Array（項目為 String） -->
      <template
        v-else-if="
          propInfo.type === 'array' && propInfo.items.type === 'string'
        "
      >
  <div class="space-y-2 sm:space-y-3 p-3 sm:p-4 border border-gray-200 rounded-lg bg-gray-50">
          <div
            v-for="(item, index) in modelValue[key]"
            :key="index"
            class="flex items-start space-x-1 sm:space-x-2"
          >
            <textarea
              :value="item"
              @input="updateArrayItem(key, index, $event.target.value)"
              rows="3"
              class="flex-1 p-2 font-mono text-xs sm:text-sm bg-gray-100 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 transition"
            ></textarea>
            <button
              @click="removeArrayItem(key, index)"
              class="text-red-500 hover:text-red-700 p-1 rounded-full bg-red-100 hover:bg-red-200 text-xs sm:text-base"
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <button
            @click="addArrayStringItem(key)"
            class="text-xs sm:text-sm font-medium text-indigo-600 hover:text-indigo-800"
          >
            + 新增文字項目
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
defineOptions({
  name: "JsonSchemaForm",
});

const props = defineProps({
  schema: { type: Object, required: true },
  modelValue: { type: Object, required: true },
});

const emit = defineEmits(["update:modelValue"]);

function updateValue(key, value) {
  const newValue = { ...props.modelValue, [key]: value };
  emit("update:modelValue", newValue);
}

function updateArrayItem(key, index, itemValue) {
  const newArray = [...props.modelValue[key]];
  newArray[index] = itemValue;
  updateValue(key, newArray);
}

function addArrayItem(key, itemSchemaProperties) {
  const newArray = props.modelValue[key] ? [...props.modelValue[key]] : [];
  const newItem = {};
  for (const propKey in itemSchemaProperties) {
    newItem[propKey] = "";
  }
  newArray.push(newItem);
  updateValue(key, newArray);
}

function addArrayStringItem(key) {
  const newArray = props.modelValue[key] ? [...props.modelValue[key]] : [];
  newArray.push("");
  updateValue(key, newArray);
}

function removeArrayItem(key, index) {
  const newArray = [...props.modelValue[key]];
  newArray.splice(index, 1);
  updateValue(key, newArray);
}
</script>
