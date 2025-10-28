import { ref, computed, watch, onMounted } from "vue";
import type { Ref, ComputedRef } from "vue";
import {
  buildDynamicSections,
  createEmptyDynamicValues,
  type DynamicValueMap,
} from "~/utils/dynamicSchema";

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
  const dynamicFieldValues: Ref<DynamicValueMap> = ref(
    createEmptyDynamicValues()
  );
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
    const sections = buildDynamicSections(dynamicFieldValues.value);

    const additionalDetails = sections
      .map((section) => {
        const filledFields = section.fields
          .map((field) => {
            const filledSubFields = field.subFields
              .filter((sub) => sub.value && sub.value.trim() !== "")
              .map((sub) => `${sub.shortLabel}: ${sub.value}`);
            if (filledSubFields.length === 0) {
              return null;
            }
            const description = field.description
              ? `說明: ${field.description}\n`
              : "";
            return `【${field.title}】\n${description}${filledSubFields.join(
              "\n"
            )}`;
          })
          .filter((item): item is string => Boolean(item));

        if (filledFields.length === 0) {
          return null;
        }

        return `◆ ${section.sectionName}\n${filledFields.join("\n\n")}`;
      })
      .filter((item): item is string => Boolean(item))
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
    dynamicFieldValues.value = createEmptyDynamicValues();
  };

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
    dynamicFieldValues,
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
