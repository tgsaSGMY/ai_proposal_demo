import { ref, computed, watch, onMounted } from "vue";
import type { Ref, ComputedRef } from "vue";

// 類型定義
interface Config {
  id: string;
  name: string;
  templates: Template[];
}

interface Template {
  id: string;
  name: string;
  sections: Section[];
}

interface Section {
  id: string;
  name: string;
  json_schema?: {
    properties: Record<string, { description?: string }>;
  };
  custom_prompt_list?: string[];
  system_prompt?: string;
}

interface DynamicInput {
  id: string;
  key: string;
  label: string;
  value: string;
}

interface DynamicInputGroup {
  sectionId: string;
  sectionName: string;
  inputs: DynamicInput[];
  custom_prompt_list: string[];
  system_prompt: string;
}

interface Selection {
  grantId: string;
  templateId: string;
}

interface PlanContent {
  [key: string]: {
    content?: string;
    error?: string;
  };
}

// 这是一个 Composable 函数
export function usePlanGenerator() {
  const config = useRuntimeConfig();
  const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

  // --- 响应式状态 ---
  const allConfigs: Ref<Config[]> = ref([]);
  const selectedGrantId: Ref<string> = ref("");
  const selectedTemplateId: Ref<string> = ref("");
  const userInput: Ref<string> = ref("");
  const dynamicInputs: Ref<DynamicInputGroup[]> = ref([]);
  const planContent: Ref<PlanContent> = ref({});

  // --- Computed Properties ---

  const availableTemplates: ComputedRef<Template[]> = computed(() => {
    if (!selectedGrantId.value) return [];
    const grant = allConfigs.value.find((g) => g.id === selectedGrantId.value);
    return grant ? grant.templates : [];
  });

  const currentSections: ComputedRef<Section[]> = computed(() => {
    if (!selectedTemplateId.value) return [];
    const template = availableTemplates.value.find(
      (t) => t.id === selectedTemplateId.value
    );
    return template ? template.sections : [];
  });

  const currentGrant: ComputedRef<Config | null> = computed(() => {
    if (!selectedGrantId.value) return null;
    return allConfigs.value.find((g) => g.id === selectedGrantId.value) || null;
  });

  const currentTemplate: ComputedRef<Template | null> = computed(() => {
    if (!selectedTemplateId.value) return null;
    return (
      availableTemplates.value.find((t) => t.id === selectedTemplateId.value) ||
      null
    );
  });

  // --- Methods ---
  const fetchAllConfigs = async (): Promise<void> => {
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

  const buildFinalUserInput = (summaries: string[] = []): string => {
    let finalInput = `核心想法: ${userInput.value}\n\n`;
    const additionalDetails = dynamicInputs.value
      .flatMap((group) => group.inputs)
      .filter((input) => input.value && input.value.trim() !== "")
      .map((input) => `關於"${input.label}"的補充信息:\n${input.value}`)
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

  const onSelectionChange = (selection: Selection): void => {
    selectedGrantId.value = selection.grantId;
    selectedTemplateId.value = selection.templateId;
    planContent.value = {}; // 重置
  };

  // --- Watchers ---
  watch(
    currentSections,
    (newSections) => {
      const groupedInputs: DynamicInputGroup[] = [];
      if (newSections && newSections.length > 0) {
        newSections.forEach((section) => {
          const sectionInputs: DynamicInput[] = [];
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
      !selectedTemplateId.value &&
      newTemplates[0]
    ) {
      selectedTemplateId.value = newTemplates[0].id;
    }
  });

  onMounted(async () => {
    if (allConfigs.value.length === 0) {
      await fetchAllConfigs();
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
    fetchAllConfigs,
  };
}

// import { ref, computed, watch, onMounted } from "vue";

// // 这是一个 Composable 函数
// export function usePlanGenerator() {
//   const config = useRuntimeConfig();
//   const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

//   // --- 响应式状态 ---
//   const allConfigs = ref([]);
//   const selectedGrantId = ref("");
//   const selectedTemplateId = ref("");
//   const userInput = ref("");
//   const dynamicInputs = ref([]);
//   const planContent = ref({});

//   // --- Computed Properties ---

//   const availableTemplates = computed(() => {
//     if (!selectedGrantId.value) return [];
//     const grant = allConfigs.value.find((g) => g.id === selectedGrantId.value);
//     return grant ? grant.templates : [];
//   });

//   const currentSections = computed(() => {
//     if (!selectedTemplateId.value) return [];
//     const template = availableTemplates.value.find(
//       (t) => t.id === selectedTemplateId.value
//     );
//     return template ? template.sections : [];
//   });

//   const currentGrant = computed(() => {
//     if (!selectedGrantId.value) return null;
//     return allConfigs.value.find((g) => g.id === selectedGrantId.value);
//   });

//   const currentTemplate = computed(() => {
//     if (!selectedTemplateId.value) return null;
//     return availableTemplates.value.find(
//       (t) => t.id === selectedTemplateId.value
//     );
//   });

//   // --- Methods ---
//   const fetchAllConfigs = async () => {
//     try {
//       const response = await fetch(`${API_BASE_URL}/config`);
//       if (!response.ok) throw new Error("Network response was not ok");
//       allConfigs.value = await response.json();
//     } catch (error) {
//       console.error("Failed to load config:", error);
//       // 让调用方处理通知
//       throw error;
//     }
//   };

//   const buildFinalUserInput = (summaries = []) => {
//     let finalInput = `核心想法: ${userInput.value}\n\n`;
//     const additionalDetails = dynamicInputs.value
//       .flatMap((group) => group.inputs)
//       .filter((input) => input.value && input.value.trim() !== "")
//       .map((input) => `關於“${input.label}”的補充信息:\n${input.value}`)
//       .join("\n\n");

//     if (additionalDetails) {
//       finalInput += `--- 詳細補充信息 ---\n${additionalDetails}`;
//     }

//     if (summaries && summaries.length > 0) {
//       const summariesText = summaries.join("\n\n---\n\n");
//       finalInput += `\n\n--- 額外參考資料重點 ---\n${summariesText}`;
//     }

//     return finalInput;
//   };

//   const onSelectionChange = (selection) => {
//     selectedGrantId.value = selection.grantId;
//     selectedTemplateId.value = selection.templateId;
//     planContent.value = {}; // 重置
//   };

//   // --- Watchers ---
//   watch(
//     currentSections,
//     (newSections) => {
//       const groupedInputs = [];
//       if (newSections && newSections.length > 0) {
//         newSections.forEach((section) => {
//           const sectionInputs = [];
//           const prompts = section.custom_prompt_list || [];
//           if (section.json_schema && section.json_schema.properties) {
//             Object.entries(section.json_schema.properties).forEach(
//               ([key, prop]) => {
//                 sectionInputs.push({
//                   id: `${section.id}-${key}`,
//                   key: key,
//                   label: prop.description || key.replace("_", " "),
//                   value: "",
//                 });
//               }
//             );
//           }
//           if (sectionInputs.length > 0 || prompts.length > 0) {
//             groupedInputs.push({
//               sectionId: section.id,
//               sectionName: section.name,
//               inputs: sectionInputs,
//               custom_prompt_list: prompts,
//               system_prompt: section.system_prompt || "",
//             });
//           }
//         });
//       }
//       dynamicInputs.value = groupedInputs;
//     },
//     { deep: true }
//   );

//   // 自动选择唯一的模板
//   watch(availableTemplates, (newTemplates) => {
//     if (
//       newTemplates &&
//       newTemplates.length === 1 &&
//       !selectedTemplateId.value
//     ) {
//       selectedTemplateId.value = newTemplates[0].id;
//     }
//   });

//   onMounted(async () => {
//     if (allConfigs.value.length === 0) {
//       await fetchAllConfigs();
//     }
//   });

//   // 返回所有需要暴露给组件的状态和方法
//   return {
//     // State
//     allConfigs,
//     selectedGrantId,
//     selectedTemplateId,
//     userInput,
//     dynamicInputs,
//     planContent,

//     // Computed
//     availableTemplates,
//     currentSections,
//     currentGrant,
//     currentTemplate,

//     // Methods
//     buildFinalUserInput,
//     onSelectionChange,
//     fetchAllConfigs,
//   };
// }
