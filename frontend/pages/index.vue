<template>
  <div class="py-10 px-4 flex justify-center">
    <div class="w-full max-w-3xl bg-white shadow-xl rounded-2xl p-8">
      <h1 class="text-3xl font-bold text-gray-800 text-center mb-8">
        AI 計劃書生成器 <span class="text-indigo-600">v1.0</span>
      </h1>

      <!-- 第一层：主题 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >1. 選擇主題</label
          >
          <select
            v-model="selectedGrantId"
            @change="onGrantChange"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition"
          >
            <option disabled value="">請選擇</option>
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
          <!-- 第二层：模板 -->
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >2. 选择模板</label
          >
          <select
            v-model="selectedTemplateId"
            :disabled="!selectedGrantId"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition disabled:bg-gray-100"
          >
            <option disabled value="">请选择</option>
            <option
              v-for="template in availableTemplates"
              :key="template.id"
              :value="template.id"
            >
              {{ template.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- 第三层： 用户输入 + 辅助输入框 -->
      <div class="mb-6 space-y-6">
        <!-- 主想法输入框 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2"
            >3. 描述你的核心項目／想法</label
          >
          <textarea
            v-model="userInput"
            placeholder="例如：一個利用 AI 分析使用者評論，自動生成產品優化建議的 SaaS 平台..."
            rows="5"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition resize-y"
          ></textarea>
        </div>

        <!-- 根据grants & template 动态生成的辅助输入框区域 -->
        <div
          v-if="dynamicInputs.length > 0"
          class="space-y-4 border-t border-gray-200 pt-6"
        >
          <div class="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
            <p class="text-sm text-indigo-700">
              <span class="font-semibold">專業提示：</span> 填寫以下細節能讓 AI
              生成更精準、更出色的內容！
            </p>
          </div>
          <div v-for="(input, index) in dynamicInputs" :key="index">
            <label
              :for="input.id"
              class="block text-sm font-medium text-gray-600 mb-2"
            >
              {{ input.label }}
            </label>
            <textarea
              :id="input.id"
              v-model="input.value"
              :placeholder="`關於「${input.label}」的更多細節...`"
              rows="3"
              class="w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 transition resize-y"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- 生成机会按钮 + loading state -->
      <button
        @click="handleGeneratePlan"
        :disabled="isLoading || !selectedTemplateId || !userInput.trim()"
        class="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-3 rounded-lg shadow-md hover:bg-indigo-700 disabled:bg-indigo-300 disabled:cursor-not-allowed transition-all duration-300"
      >
        <svg
          v-if="isLoading"
          class="animate-spin h-5 w-5 text-white"
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
            d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
          ></path>
        </svg>
        {{ isLoading ? "正在生成完整計劃書..." : "生成完整計劃書" }}
      </button>

      <!-- 生成结果 -->
      <div v-if="Object.keys(planContent).length > 0" class="mt-10 space-y-8">
        <h2
          class="text-2xl font-bold text-gray-800 border-b border-gray-300 pb-3"
        >
          計劃書草稿
        </h2>
        <div v-for="section in currentSections" :key="section.id">
          <h3 class="text-xl font-semibold text-gray-700 mb-4">
            {{ section.name }}
          </h3>
          <div
            class="bg-gray-50 border border-gray-200 rounded-lg p-6 text-gray-800 leading-relaxed shadow-inner"
          >
            <div
              v-if="planContent[section.id]?.content"
              class="prose max-w-none whitespace-pre-wrap"
              v-html="formatContent(planContent[section.id].content)"
            ></div>
            <div
              v-else-if="planContent[section.id]?.error"
              class="text-red-600 font-medium"
            >
              <p><strong>生成失敗：</strong></p>
              <p class="mt-2 text-sm">{{ planContent[section.id].error }}</p>
            </div>
            <div v-else class="text-gray-400 italic">等待生成...</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from "vue";

// 状态
const allConfigs = ref([]); // 所有 grants, template, section
const selectedGrantId = ref(""); // 当前grant
const selectedTemplateId = ref(""); //当前template
const userInput = ref(""); //当前主想法
import { useLoading } from "~/composables/useLoading";
import { useNotifications } from "~/composables/useNotifications";
const { success, error: errorNotification } = useNotifications();
const { isLoading } = useLoading();
const planContent = ref({}); //生成结果
const dynamicInputs = ref([]); //根据section动态输入

// 根据Config和Grant生成模板
const availableTemplates = computed(() => {
  if (!selectedGrantId.value) return [];
  const selectedGrant = allConfigs.value.find(
    (g) => g.id === selectedGrantId.value
  );
  return selectedGrant ? selectedGrant.templates : [];
});

// 根据Config和Template生成模板
const currentSections = computed(() => {
  if (!selectedTemplateId.value) return [];
  const template = availableTemplates.value.find(
    (t) => t.id === selectedTemplateId.value
  );
  return template ? template.sections : [];
});

// 监听选择
watch(
  currentSections,
  (newSections) => {
    dynamicInputs.value = []; // 当模板改变时，重置动态输入框
    if (newSections && newSections.length > 0) {
      const inputs = [];
      newSections.forEach((section) => {
        if (section.json_schema && section.json_schema.properties) {
          Object.entries(section.json_schema.properties).forEach(
            ([key, prop]) => {
              // 避免重复添加相同的问题
              if (!inputs.some((input) => input.label === prop.description)) {
                inputs.push({
                  id: `${section.id}-${key}`,
                  label: prop.description || key.replace("_", " "), // 使用 description 作为 label
                  value: "", // 用户输入的值
                });
              }
            }
          );
        }
      });
      dynamicInputs.value = inputs;
    }
  },
  { deep: true }
);

// --- Mounted的时候拿完整Config （grants, template, section） ---
onMounted(async () => {
  try {
    const response = await fetch("http://127.0.0.1:8000/api/config");
    if (!response.ok) throw new Error("Network response was not ok");
    allConfigs.value = await response.json();
  } catch (error) {
    console.error("Failed to load config:", error);
    errorNotification("无法加载应用配置，请检查后端服务是否运行。");
  }
});

// 当主题改变时，重置模板选项
const onGrantChange = () => {
  selectedTemplateId.value = ""; // 当主题改变时，重置模板选项
  planContent.value = {}; // 清空旧生成计划书内容
};

// 替换 **text** 为 <strong>text</strong>，并处理换行
const formatContent = (text) => {
  if (!text) return "";
  return text
    .replace(
      /\*\*(.*?)\*\*/g,
      '<strong class="font-semibold text-gray-900">$1</strong>'
    )
    .replace(/\n/g, "<br>");
};

// final user input 就是所有user input concat在一起
const buildFinalUserInput = () => {
  let finalInput = `核心想法: ${userInput.value}\n\n`;
  const additionalDetails = dynamicInputs.value
    .filter((input) => input.value.trim() !== "")
    .map((input) => `关于“${input.label}”的补充信息:\n${input.value}`)
    .join("\n\n");

  if (additionalDetails) {
    finalInput += `--- 详细补充信息 ---\n${additionalDetails}`;
  }
  return finalInput;
};

// 生成企划
const handleGeneratePlan = async () => {
  if (!selectedTemplateId.value || !userInput.value.trim()) {
    errorNotification("请选择完整的主题、模板，并输入您的核心项目描述");
    return;
  }

  isLoading.value = true;
  planContent.value = {};

  const finalUserInput = buildFinalUserInput();

  try {
    const sectionsToGenerate = currentSections.value.map((s) => ({
      section_id: s.id,
    }));

    const response = await fetch("http://127.0.0.1:8000/api/generate_plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "31847807-e04f-4a41-947b-60c5c60034ad", // Dummy User ID
        grant: selectedGrantId.value,
        template: selectedTemplateId.value,
        sections: sectionsToGenerate,
        user_input: finalUserInput, // 发送拼接后的详细输入
      }),
    });

    if (!response.ok) {
      const errorDetail = await response.text();
      throw new Error(`服务器错误 (${response.status}): ${errorDetail}`);
    }

    const data = await response.json();
    planContent.value = data;
  } catch (error) {
    console.error("Error:", error);
    errorNotification(`生成失败: ${error.message}`);
  } finally {
    isLoading.value = false;
  }
};
</script>
