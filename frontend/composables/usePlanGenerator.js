import { ref, computed, watch, onMounted } from "vue";

// 这是一个 Composable 函数
export function usePlanGenerator() {
  const config = useRuntimeConfig();
  const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

  // --- 响应式状态 ---
  const allConfigs = ref([]);
  const selectedGrantId = ref("");
  const selectedTemplateId = ref("");
  const userInput = ref("");
  const dynamicInputs = ref([]);
  const planContent = ref({});

  // --- Computed Properties ---

  const availableTemplates = computed(() => {
    if (!selectedGrantId.value) return [];
    const grant = allConfigs.value.find((g) => g.id === selectedGrantId.value);
    return grant ? grant.templates : [];
  });

  const currentSections = computed(() => {
    if (!selectedTemplateId.value) return [];
    const template = availableTemplates.value.find(
      (t) => t.id === selectedTemplateId.value
    );
    return template ? template.sections : [];
  });

  const currentGrant = computed(() => {
    if (!selectedGrantId.value) return null;
    return allConfigs.value.find((g) => g.id === selectedGrantId.value);
  });

  const currentTemplate = computed(() => {
    if (!selectedTemplateId.value) return null;
    return availableTemplates.value.find(
      (t) => t.id === selectedTemplateId.value
    );
  });

  // --- Methods ---
  const fetchAllConfigs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/config`);
      if (!response.ok) throw new Error("Network response was not ok");
      allConfigs.value = await response.json();
    } catch (error) {
      console.error("Failed to load config:", error);
      // 让调用方处理通知
      throw error;
    }
  };

  const buildFinalUserInput = (summaries = []) => {
    let finalInput = `核心想法: ${userInput.value}\n\n`;
    const additionalDetails = dynamicInputs.value
      .flatMap((group) => group.inputs)
      .filter((input) => input.value && input.value.trim() !== "")
      .map((input) => `關於“${input.label}”的補充信息:\n${input.value}`)
      .join("\n\n");

    if (additionalDetails) {
      finalInput += `--- 詳細補充信息 ---\n${additionalDetails}`;
    }

    if (summaries && summaries.length > 0) {
      const summariesText = summaries.join("\n\n---\n\n");
      finalInput += `\n\n--- 額外參考資料重點 ---\n${summariesText}`;
    }

    return finalInput;
  };

  const onSelectionChange = (selection) => {
    selectedGrantId.value = selection.grantId;
    selectedTemplateId.value = selection.templateId;
    planContent.value = {}; // 重置
  };

  // --- Watchers ---
  watch(
    currentSections,
    (newSections) => {
      const groupedInputs = [];
      if (newSections && newSections.length > 0) {
        newSections.forEach((section) => {
          const sectionInputs = [];
          const prompts = section.custom_prompt_list || [];
          if (section.json_schema && section.json_schema.properties) {
            Object.entries(section.json_schema.properties).forEach(
              ([key, prop]) => {
                sectionInputs.push({
                  id: `${section.id}-${key}`,
                  key: key,
                  label: prop.description || key.replace("_", " "),
                  value: "",
                });
              }
            );
          }
          if (sectionInputs.length > 0 || prompts.length > 0) {
            groupedInputs.push({
              sectionId: section.id,
              sectionName: section.name,
              inputs: sectionInputs,
              custom_prompt_list: prompts,
              system_prompt: section.system_prompt || "",
            });
          }
        });
      }
      dynamicInputs.value = groupedInputs;
    },
    { deep: true }
  );

  // 自动选择唯一的模板
  watch(availableTemplates, (newTemplates) => {
    if (
      newTemplates &&
      newTemplates.length === 1 &&
      !selectedTemplateId.value
    ) {
      selectedTemplateId.value = newTemplates[0].id;
    }
  });

  onMounted(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/config`);

      if (!response.ok) throw new Error("Network response was not ok");
      allConfigs.value = await response.json();
    } catch (error) {
      console.error("Failed to load config:", error);
      errorNotification("無法加載應用配置，請檢查後端服務是否運行。");
    }
  });

  // 返回所有需要暴露给组件的状态和方法
  return {
    // State
    allConfigs,
    selectedGrantId,
    selectedTemplateId,
    userInput,
    dynamicInputs,
    planContent,

    // Computed
    availableTemplates,
    currentSections,
    currentGrant,
    currentTemplate,

    // Methods
    buildFinalUserInput,
    onSelectionChange,
    fetchAllConfigs, // 也暴露出来，以防需要手动刷新
  };
}
