<!-- JSON Schema 表单组件：根据 Schema 动态生成表单输入框,/modal裏的章節編輯，system prompt渲染的組件 -->
<template>
  <div class="space-y-4 sm:space-y-6">
    <div v-for="(propInfo, key) in schema.properties || {}" :key="key">
      <label
        class="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2"
      >
        {{ propInfo.title || key }}
      </label>

      <template v-if="propInfo.type === 'string'">
        <textarea
          :value="modelValue[key]"
          @input="updateValue(key, $event.target.value)"
          :disabled="props.readonly"
          rows="5"
          class="p-2 w-full font-mono text-xs sm:text-sm bg-gray-100 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 transition disabled:opacity-60 disabled:cursor-not-allowed"
        ></textarea>
      </template>

      <template v-else-if="propInfo.type === 'number'">
        <input
          type="number"
          :value="modelValue[key]"
          @input="updateValue(key, parseFloat($event.target.value))"
          :disabled="props.readonly"
          class="p-2 w-full font-mono text-xs sm:text-sm bg-gray-100 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 transition disabled:opacity-60 disabled:cursor-not-allowed"
        />
      </template>

      <!-- 渲染 Object 類型的字段 -->
      <template v-else-if="propInfo.type === 'object' && propInfo.properties">
        <div class="border border-gray-200 rounded-lg bg-gray-50">
          <button
            type="button"
            :disabled="props.readonly"
            class="w-full flex items-center justify-between px-3 sm:px-4 py-2 text-left text-xs sm:text-sm font-medium text-gray-700 hover:bg-indigo-50 transition disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:bg-gray-50"
            @click="toggleCollapse(makeBlockKey('object', key))"
          >
            <span class="italic text-gray-400 text-sm">詳細設定</span>
            <svg
              class="w-4 h-4 text-gray-500 transition-transform duration-200"
              :class="{
                'rotate-90': !isCollapsed(makeBlockKey('object', key)),
              }"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>
          <transition name="fade">
            <div
              v-if="!isCollapsed(makeBlockKey('object', key))"
              class="px-3 sm:px-4 pb-4 pt-2"
            >
              <JsonSchemaForm
                :schema="propInfo"
                :modelValue="getObjectModel(key)"
                :readonly="props.readonly"
                @update:modelValue="(val) => updateValue(key, val)"
              />
            </div>
          </transition>
        </div>
      </template>

      <!-- 渲染 Array 類型的字段 -->
      <template
        v-else-if="
          propInfo.type === 'array' && propInfo.items.type === 'object'
        "
      >
        <div class="border border-gray-200 rounded-lg bg-gray-50">
          <button
            type="button"
            :disabled="props.readonly"
            class="w-full flex items-center justify-between px-3 sm:px-4 py-2 text-left text-xs sm:text-sm font-medium text-gray-700 hover:bg-indigo-50 transition disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:bg-gray-50"
            @click="toggleCollapse(makeBlockKey('array', key))"
          >
            <span class="italic text-gray-400 text-sm">列表內容</span>
            <svg
              class="w-4 h-4 text-gray-500 transition-transform duration-200"
              :class="{ 'rotate-90': !isCollapsed(makeBlockKey('array', key)) }"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>
          <transition name="fade">
            <div
              v-if="!isCollapsed(makeBlockKey('array', key))"
              class="space-y-2 sm:space-y-4 p-3 sm:p-4 pt-0"
            >
              <div
                v-for="(item, index) in modelValue[key] || []"
                :key="index"
                class="border border-dashed border-gray-300 rounded-lg"
              >
                <button
                  type="button"
                  :disabled="props.readonly"
                  class="w-full flex items-center justify-between px-3 sm:px-4 py-2 text-left text-xs sm:text-sm font-medium text-gray-600 hover:bg-indigo-100 transition disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:bg-gray-50"
                  @click="
                    toggleCollapse(
                      makeBlockKey('array-item', `${key}-${index}`),
                    )
                  "
                >
                  <span class="italic text-gray-400 text-sm"
                    >項目 #{{ index + 1 }}</span
                  >
                  <svg
                    class="w-4 h-4 text-gray-500 transition-transform duration-200"
                    :class="{
                      'rotate-90': !isCollapsed(
                        makeBlockKey('array-item', `${key}-${index}`),
                      ),
                    }"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>
                <transition name="fade">
                  <div
                    v-if="
                      !isCollapsed(
                        makeBlockKey('array-item', `${key}-${index}`),
                      )
                    "
                    class="p-3 sm:p-4 pt-0 relative"
                  >
                    <JsonSchemaForm
                      :schema="propInfo.items"
                      :modelValue="item"
                      :readonly="props.readonly"
                      @update:modelValue="updateArrayItem(key, index, $event)"
                    />
                    <button
                      v-if="!props.readonly"
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
                </transition>
              </div>
              <button
                v-if="!props.readonly"
                @click="addArrayItem(key, propInfo.items.properties)"
                class="text-xs sm:text-sm font-medium text-indigo-600 hover:text-indigo-800"
              >
                + 新增項目
              </button>
            </div>
          </transition>
        </div>
      </template>

      <!-- Array（項目為 String） -->
      <template
        v-else-if="
          propInfo.type === 'array' && propInfo.items.type === 'string'
        "
      >
        <div class="border border-gray-200 rounded-lg bg-gray-50">
          <button
            type="button"
            :disabled="props.readonly"
            class="w-full flex items-center justify-between px-3 sm:px-4 py-2 text-left text-xs sm:text-sm font-medium text-gray-700 hover:bg-indigo-50 transition disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:bg-gray-50"
            @click="toggleCollapse(makeBlockKey('array', key))"
          >
            <span class="italic text-gray-400 text-sm">詳細設定</span>
            <svg
              class="w-4 h-4 text-gray-500 transition-transform duration-200"
              :class="{ 'rotate-90': !isCollapsed(makeBlockKey('array', key)) }"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>
          <transition name="fade">
            <div
              v-if="!isCollapsed(makeBlockKey('array', key))"
              class="space-y-2 sm:space-y-3 p-3 sm:p-4 pt-0"
            >
              <div
                v-for="(item, index) in modelValue[key] || []"
                :key="index"
                class="flex items-start space-x-1 sm:space-x-2"
              >
                <textarea
                  :value="item"
                  @input="updateArrayItem(key, index, $event.target.value)"
                  :disabled="props.readonly"
                  rows="3"
                  class="flex-1 p-2 font-mono text-xs sm:text-sm bg-gray-100 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 transition disabled:opacity-60 disabled:cursor-not-allowed"
                ></textarea>
                <button
                  v-if="!props.readonly"
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
                v-if="!props.readonly"
                @click="addArrayStringItem(key)"
                class="text-xs sm:text-sm font-medium text-indigo-600 hover:text-indigo-800"
              >
                + 新增文字項目
              </button>
            </div>
          </transition>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";

defineOptions({
  name: "JsonSchemaForm",
});

const props = defineProps({
  schema: { type: Object, required: true },
  modelValue: { type: Object, required: true },
  readonly: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue"]);

const collapsedKeys = ref(new Set());

// 监听schema变化，当schema改变时清空折叠状态
watch(
  () => props.schema,
  () => {
    collapsedKeys.value = new Set();
  },
  { deep: true },
);

// 更新指定键的值，发送更新事件给父组件
function updateValue(key, value) {
  const newValue = { ...props.modelValue, [key]: value };
  emit("update:modelValue", newValue);
}

// 更新数组中指定索引的项值
function updateArrayItem(key, index, itemValue) {
  const newArray = props.modelValue[key] ? [...props.modelValue[key]] : [];
  newArray[index] = itemValue;
  updateValue(key, newArray);
}

// 为数组添加新的对象项，初始化所有属性为空字符串
function addArrayItem(key, itemSchemaProperties) {
  const newArray = props.modelValue[key] ? [...props.modelValue[key]] : [];
  const newItem = {};
  for (const propKey in itemSchemaProperties) {
    newItem[propKey] = "";
  }
  newArray.push(newItem);
  updateValue(key, newArray);
}

// 为字符串数组添加新的空字符串项
function addArrayStringItem(key) {
  const newArray = props.modelValue[key] ? [...props.modelValue[key]] : [];
  newArray.push("");
  updateValue(key, newArray);
}

// 删除数组中指定索引的项
function removeArrayItem(key, index) {
  const newArray = props.modelValue[key] ? [...props.modelValue[key]] : [];
  newArray.splice(index, 1);
  updateValue(key, newArray);
}

// 生成区块的唯一键，用于标识折叠状态
function makeBlockKey(prefix, key, index = null) {
  return index !== null ? `${prefix}:${key}:${index}` : `${prefix}:${key}`;
}

// 切换指定区块的折叠/展开状态
function toggleCollapse(blockKey) {
  const next = new Set(collapsedKeys.value);
  if (next.has(blockKey)) {
    next.delete(blockKey);
  } else {
    next.add(blockKey);
  }
  collapsedKeys.value = next;
}

// 检查指定区块是否处于折叠状态
function isCollapsed(blockKey) {
  return collapsedKeys.value.has(blockKey);
}

// 获取对象类型字段的值，确保返回对象格式
function getObjectModel(key) {
  const value = props.modelValue[key];
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value;
  }
  return {};
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
