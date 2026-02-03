// ===== 导入依赖库 =====
// 导入 Vue 响应式 API
import { ref, computed, watch, onMounted } from "vue";
// 导入 Vue 类型定义
import type { Ref, ComputedRef } from "vue";
// 导入动态字段生成相关的工具函数
import {
  buildDynamicSections,
  createEmptyDynamicValues,
  ensureDynamicSchemaLoaded,
  type DynamicValueMap,
} from "~/utils/dynamicSchema";

// ===== 类型定义 =====
/**
 * 补助金/方案配置对象
 * 包含补助金的基本信息和该补助金下的所有模板
 */
interface Config {
  id: string; // 配置/补助金的唯一标识符
  name: string; // 配置/补助金的显示名称
  templates: Template[]; // 该补助金下的所有方案模板
}

/**
 * 方案模板对象
 * 代表一个完整的方案模板，包含多个部分(Section)
 */
interface Template {
  id: string; // 模板的唯一标识符
  name: string; // 模板的显示名称
  sections: Section[]; // 模板中的各个部分/章节
}

/**
 * 方案的一个部分/章节
 * 代表方案中的一个主要部分，可能包含多个字段和自定义提示
 */
interface Section {
  id: string; // 部分的唯一标识符
  name: string; // 部分的显示名称
  json_schema?: {
    // JSON Schema 定义该部分的输入字段结构
    properties: Record<string, { description?: string }>;
  };
  custom_prompt_list?: string[]; // 自定义提示词列表（用于 AI 生成）
  system_prompt?: string; // 系统提示词（用于 AI 生成）
}

/**
 * 用户的选择对象
 * 当用户选择一个补助金和相应的模板时使用
 */
interface Selection {
  grantId: string; // 选中的补助金 ID
  templateId: string; // 选中的模板 ID
}

/**
 * 方案内容对象
 * 存储生成的方案各部分的内容或错误信息
 */
interface PlanContent {
  [key: string]: {
    // key 通常是部分 ID
    content?: string; // 生成的方案内容
    error?: string; // 生成过程中的错误信息（如果有）
  };
}

// ===== 方案生成组合式函数 =====
/**
 * 管理方案生成的整个流程
 * 包括配置加载、选择管理、用户输入、方案生成等
 *
 * 功能：
 *   - 加载所有可用的补助金配置和模板
 *   - 管理用户的选择（补助金、模板）
 *   - 管理用户输入和动态字段值
 *   - 构建最终的用户输入提示词
 *   - 生成并存储方案内容
 */
export function usePlanGenerator() {
  // ===== 配置初始化 =====
  // 获取运行时配置
  const config = useRuntimeConfig();
  // API 基础 URL
  const API_BASE_URL = `${config.public.apiBaseUrl}/api`;

  // ===== 响应式状态变量 =====
  // 所有加载的补助金配置和模板
  const allConfigs: Ref<Config[]> = ref([]);
  // 用户选中的补助金 ID
  const selectedGrantId: Ref<string> = ref("");
  // 用户选中的模板 ID
  const selectedTemplateId: Ref<string> = ref("");
  // 用户输入的核心想法/描述
  const userInput: Ref<string> = ref("");
  // 动态字段（JSON Schema 定义的输入字段）的值
  const dynamicFieldValues: Ref<DynamicValueMap> = ref(
    createEmptyDynamicValues({
      templateId: selectedTemplateId.value,
      templateGrantId: selectedGrantId.value,
    }),
  );
  // 存储生成的方案内容（按部分存储）
  const planContent: Ref<PlanContent> = ref({});

  // ===== 计算属性：相关数据 =====

  /**
   * 根据选中的补助金，计算可用的模板列表
   * 当补助金改变时自动更新
   */
  const availableTemplates: ComputedRef<Template[]> = computed(() => {
    // 如果未选择补助金，返回空数组
    if (!selectedGrantId.value) return [];
    // 查找选中补助金对应的配置
    const grant = allConfigs.value.find((g) => g.id === selectedGrantId.value);
    // 返回该补助金下的所有模板，如果未找到则返回空数组
    return grant ? grant.templates : [];
  });

  /**
   * 根据选中的模板，计算该模板的所有部分/章节
   * 当模板改变时自动更新
   */
  const currentSections: ComputedRef<Section[]> = computed(() => {
    // 如果未选择模板，返回空数组
    if (!selectedTemplateId.value) return [];
    // 查找选中模板对应的对象
    const template = availableTemplates.value.find(
      (t) => t.id === selectedTemplateId.value,
    );
    // 返回该模板的所有部分，如果未找到则返回空数组
    return template ? template.sections : [];
  });

  /**
   * 获取当前选中的补助金对象（完整数据）
   * 用于获取补助金的详细信息
   */
  const currentGrant: ComputedRef<Config | null> = computed(() => {
    // 如果未选择补助金，返回 null
    if (!selectedGrantId.value) return null;
    // 查找并返回选中的补助金对象
    return allConfigs.value.find((g) => g.id === selectedGrantId.value) || null;
  });

  /**
   * 获取当前选中的模板对象（完整数据）
   * 用于获取模板的详细信息
   */
  const currentTemplate: ComputedRef<Template | null> = computed(() => {
    // 如果未选择模板，返回 null
    if (!selectedTemplateId.value) return null;
    // 查找并返回选中的模板对象
    return (
      availableTemplates.value.find((t) => t.id === selectedTemplateId.value) ||
      null
    );
  });

  // ===== 方法 =====

  /**
   * 从 API 加载所有补助金配置和模板
   * 同时加载当前选中模板的动态 JSON Schema
   */
  const fetchAllConfigs = async (): Promise<void> => {
    try {
      // 确保当前选中模板的 JSON Schema 已加载
      // 这样可以在 UI 中显示动态表单字段
      await ensureDynamicSchemaLoaded({
        apiBaseUrl: config.public.apiBaseUrl,
        templateId: selectedTemplateId.value,
        templateGrantId: selectedGrantId.value,
      });
      // 调用 API 获取所有补助金配置和模板
      const response = await fetch(`${API_BASE_URL}/config`);
      // 检查 HTTP 响应是否成功
      if (!response.ok) throw new Error("Network response was not ok");
      // 解析 JSON 响应并保存到状态
      allConfigs.value = await response.json();
    } catch (error) {
      // 记录错误信息
      console.error("Failed to load config:", error);
      // 抛出错误，让调用方处理（通常显示通知）
      throw error;
    }
  };

  /**
   * 构建最终的用户输入提示词
   * 用于发送给 AI 模型生成方案
   *
   * 参数：
   *   - summaries: 额外的参考资料摘要（可选）
   *
   * 返回值：
   *   - 格式化的完整输入提示词（包含核心想法和详细补充信息）
   */
  const buildFinalUserInput = (summaries: string[] = []): string => {
    // 第 1 部分：用户的核心想法
    let finalInput = `核心想法: ${userInput.value}\n\n`;

    // 第 2 部分：根据动态字段值构建详细补充信息
    const sections = buildDynamicSections(dynamicFieldValues.value, {
      templateId: selectedTemplateId.value,
      templateGrantId: selectedGrantId.value,
    });

    // 将每个部分的用户输入格式化成文字
    const additionalDetails = sections
      .map((section) => {
        // 获取该部分中已填写的字段
        const filledFields = section.fields
          .map((field) => {
            // 获取字段值并去除空格
            const value = field.value?.trim();
            // 如果字段为空，跳过它
            if (!value) {
              return null;
            }
            // 如果字段有描述，添加描述信息
            const description = field.description
              ? `說明: ${field.description}\n`
              : "";
            // 格式化字段：【字段名】\n说明\n字段值
            return `【${field.title}】\n${description}${value}`;
          })
          // 过滤掉 null 值，只保留有实际内容的字段
          .filter((item): item is string => Boolean(item));

        // 如果该部分没有填写任何字段，跳过这个部分
        if (filledFields.length === 0) {
          return null;
        }

        // 将部分名称和所有填写的字段拼接在一起
        return `${section.sectionName}\n${filledFields.join("\n\n")}`;
      })
      // 过滤掉 null 值，只保留有内容的部分
      .filter((item): item is string => Boolean(item))
      // 用双换行符分隔各部分
      .join("\n\n");

    // 如果有详细补充信息，添加到最终输入中
    if (additionalDetails) {
      finalInput += `\n\n${additionalDetails}`;
    }

    // 第 3 部分：添加额外的参考资料摘要（如果有的话）
    if (summaries && summaries.length > 0) {
      const summariesText = summaries.join("\n\n---\n\n");
      finalInput += `\n\n--- 額外參考資料重點 ---\n${summariesText}`;
    }

    // 返回完整的格式化输入
    return finalInput;
  };

  /**
   * 处理用户的选择变化
   * 当用户选择不同的补助金或模板时调用
   *
   * 参数：
   *   - selection: 包含 grantId 和 templateId 的选择对象
   *
   * 效果：
   *   1. 更新选中的补助金和模板 ID
   *   2. 清空之前生成的方案内容
   *   3. 重置动态字段值
   *   4. 异步加载新模板的 JSON Schema
   */
  const onSelectionChange = (selection: Selection): void => {
    // 更新选中的补助金 ID
    selectedGrantId.value = selection.grantId;
    // 更新选中的模板 ID
    selectedTemplateId.value = selection.templateId;
    // 清空之前生成的方案内容
    planContent.value = {};
    // 创建新模板的空动态字段值
    dynamicFieldValues.value = createEmptyDynamicValues({
      templateId: selection.templateId,
      templateGrantId: selection.grantId,
    });
    // 异步加载新模板的 JSON Schema
    // 不用等待，在后台加载（不阻塞 UI）
    ensureDynamicSchemaLoaded({
      apiBaseUrl: config.public.apiBaseUrl,
      templateId: selection.templateId,
      templateGrantId: selection.grantId,
    }).catch((error) => {
      // 如果加载失败，打印错误但不中断程序流程
      console.error("Failed to load schema for selected template:", error);
    });
  };

  // ===== 监听器和生命周期 =====

  /**
   * 自动选择模板：当补助金改变且只有一个模板时，自动选择该模板
   * 这样可以简化用户操作（不用手动选择模板）
   */
  watch(availableTemplates, (newTemplates) => {
    // 如果新的可用模板列表有内容，且当前未选择模板，且列表中只有一个模板
    if (
      newTemplates &&
      newTemplates.length === 1 &&
      !selectedTemplateId.value &&
      newTemplates[0]
    ) {
      // 自动选择那唯一的模板
      selectedTemplateId.value = newTemplates[0].id;
    }
  });

  /**
   * 组件挂载时的初始化
   * 如果还没有加载配置，则加载所有补助金配置和模板
   */
  onMounted(async () => {
    // 检查是否已加载配置
    if (allConfigs.value.length === 0) {
      // 如果未加载，则从 API 加载
      await fetchAllConfigs();
    }
  });

  // ===== 导出公共 API =====
  // 返回所有需要暴露给组件的状态、计算属性和方法
  return {
    // ===== 响应式状态 =====
    allConfigs, // 所有补助金配置和模板
    selectedGrantId, // 选中的补助金 ID
    selectedTemplateId, // 选中的模板 ID
    userInput, // 用户输入的核心想法
    dynamicFieldValues, // 动态字段的值
    planContent, // 生成的方案内容

    // ===== 计算属性 =====
    availableTemplates, // 当前补助金下可用的模板列表
    currentSections, // 当前模板的所有部分/章节
    currentGrant, // 当前选中的补助金对象
    currentTemplate, // 当前选中的模板对象

    // ===== 方法 =====
    buildFinalUserInput, // 构建最终用户输入提示词
    onSelectionChange, // 处理用户选择变化
    fetchAllConfigs, // 加载所有配置和模板
  };
}
