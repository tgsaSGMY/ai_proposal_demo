/**
 * ========================================
 * 动态输入字段 Schema 定义和工具函数
 * ========================================
 *
 * 此模块管理整个应用的动态字段结构，包括：
 * - 静态字段定义（不依赖运行时配置）
 * - 复合键（composite key）生成和管理
 * - UI 视图模型（ViewModel）构建
 * - 字段值映射和验证
 * - 远程 Schema 加载和缓存
 *
 * 核心概念：
 *   - DynamicValueKey: 字段的唯一标识符（格式：section::field）
 *   - DynamicValueMap: 字段值的映射表（键值对存储）
 *   - DynamicSchemaSection: Schema 中的章节定义
 *   - DynamicSectionViewModel: 前端渲染用的视图模型
 */

// ===== 导入依赖库 =====
// 导入 Supabase 数据库客户端（用于 RPC 调用）

// ===== 类型定义部分 =====

/**
 * 动态字段值的键类型
 *
 * 格式说明：
 *   - 由章节 ID 和字段 Key 用 "::" 分隔组成
 *   - 例如："二、研發動機::市場規模"
 *   - 用于在 DynamicValueMap 中唯一标识一个字段
 */
export type DynamicValueKey = string;

/**
 * 动态字段值的映射表
 *
 * 结构说明：
 *   - 键：复合键字符串（DynamicValueKey）
 *   - 值：字段内容（通常是用户输入的文本）
 *
 * 用途：
 *   - 存储用户在表单中填入的数据
 *   - 支持跨组件的数据共享
 *   - 便于序列化和持久化
 *
 * 示例：
 *   {
 *     "二、研發動機::核心問題": "开发 AI 模型...",
 *     "二、研發動機::市場規模": "目标市场是...",
 *   }
 */
export type DynamicValueMap = Record<DynamicValueKey, string>;

import { supabase } from "~/utils/supabaseClient";

// ===== Schema 属性定义 =====
/**
 * Schema 中单个属性（字段）的定义
 *
 * 属性说明：
 *   - key: 字段的编程识别符（例如："核心問題"）
 *   - title: 字段在 UI 中显示的标题（例如："1.技術或服務的核心問題是甚麼?"）
 *   - description: 字段的详细说明文字（例如："要解決什麼核心技術問題?"）
 */
export interface DynamicSchemaProperty {
  key: string; // 字段的唯一标识符
  title: string; // 显示给用户的字段标题
  description: string; // 字段的帮助文本/说明
}

/**
 * Schema 中章节（Section）的定义
 *
 * 属性说明：
 *   - id: 章节的唯一标识符（例如："二、研發動機"）
 *   - title: 章节的显示名称
 *   - properties: 该章节包含的所有字段
 *   - templateId: 可选的模板 ID（用于区分不同模板）
 *   - templateGrantId: 可选的补助金 ID（用于区分不同补助金）
 *
 * 注意：
 *   - templateId 和 templateGrantId 用于支持多个模板时的字段过滤
 */
export interface DynamicSchemaSection {
  id: string; // 章节唯一标识符
  title: string; // 章节显示名称
  properties: DynamicSchemaProperty[]; // 该章节的所有字段
  templateId?: string | null; // 所属模板 ID（可选）
  templateGrantId?: string | null; // 所属补助金 ID（可选）
}

/**
 * 前端 UI 展示用的章节视图模型
 *
 * 说明：
 *   - 这是为前端渲染优化的数据结构
 *   - 相比 DynamicSchemaSection，增加了用户输入的数值
 *   - 每个字段都包含渲染所需的完整信息
 *
 * 用途：
 *   - 直接传给 Vue 组件进行渲染
 *   - 包含 UI 所需的所有字段（值、占位符等）
 */
export interface DynamicSectionViewModel {
  sectionId: string; // 章节 ID
  sectionName: string; // 章节显示名称
  fields: DynamicFieldViewModel[]; // 该章节的所有字段的视图模型
}

/**
 * 前端 UI 展示用的字段视图模型
 *
 * 说明：
 *   - 包含单个字段在前端渲染所需的完整信息
 *   - 是 DynamicSchemaProperty + 用户值 + UI 辅助信息 的组合
 *
 * 属性说明：
 *   - propertyKey: 字段的编程标识符
 *   - title: 字段标题（用户可见）
 *   - description: 字段说明（帮助文本）
 *   - compositeKey: 复合键（用于数据映射）
 *   - placeholder: 输入框占位符文本
 *   - value: 该字段当前的值（用户输入的内容）
 */
export interface DynamicFieldViewModel {
  propertyKey: string; // 字段的编程标识符
  title: string; // 显示给用户的标题
  description: string; // 字段说明/帮助文本
  compositeKey: string; // 复合键（section::field 格式）
  placeholder: string; // 输入框占位符
  value: string; // 当前的字段值
}

/**
 * 字段定义的完整描述
 *
 * 说明：
 *   - 包含字段的所有元数据（定义信息）
 *   - 用于生成字段标签、查询字段等场景
 *
 * 属性说明：
 *   - sectionId/sectionTitle: 章节信息
 *   - propertyKey/propertyTitle: 字段信息
 *   - description: 字段说明
 *   - compositeKey: 复合键
 *   - label: 组合标签（"章节名|字段名" 格式）
 */
export interface DynamicFieldDefinition {
  sectionId: string; // 所属章节 ID
  sectionTitle: string; // 所属章节标题
  propertyKey: string; // 字段编程标识符
  propertyTitle: string; // 字段显示标题
  description: string; // 字段说明
  compositeKey: string; // 复合键
  label: string; // 组合标签（用于查询和匹配）
}

const RAW_DYNAMIC_SCHEMA: Record<
  string,
  {
    title: string;
    properties: Record<string, { title: string; description: string }>;
  }
> = {
  "二、研發動機": {
    title: "二、研發動機",
    properties: {
      核心問題: {
        title: "1.技術或服務的核心問題是甚麼?",
        description: "要解決什麼核心技術問題?",
      },
      市場規模: {
        title: "2.目標客戶與目標市場?",
        description: "說明：你要賣給誰?越明確越好。",
      },
    },
  },
  // "三、解決辦法": {
  //   title: "三、解決辦法",
  //   properties: {
  //     產品內容: {
  //       title: "1.具體說明你的產品或服務是什麼?",
  //       description: "請清楚具體說明，你要研發或設計的服務是什麼?",
  //     },
  //     關鍵技術: {
  //       title: "2.關鍵技術為何",
  //       description:
  //         "關鍵環節詳細說明\nex1: 研發上最困難的地方在哪裡?或是花最多時間的項目、印象最深刻的地方?\nex2: 目前流程最卡的地方在哪?解決關鍵的痛點",
  //     },
  //     商業模式運作流程: {
  //       title: "3.商業模式運作流程",
  //       description: "舉例：客戶登入→使用平台→取得反饋→改良產品→行銷推廣",
  //     },
  //   },
  // },
  // "四、創新性分析與驗收方式": {
  //   title: "四、創新性分析與驗收方式",
  //   properties: {
  //     既有流程說明: {
  //       title: "1.技術或服務的創新性?既有流程說明",
  //       description: "現在的作業流程説明\n不需要包含痛點",
  //     },
  //     測試與檢測方式: {
  //       title: "2.公司自行測試與第三方檢測方式為何?",
  //       description:
  //         "請說明公司與客戶間如何確認品質（自行測試方式），以及是否委託第三方檢測（例如 SGS）及其範圍與標準。",
  //     },
  //   },
  // },
  // "五、競爭力分析": {
  //   title: "五、競爭力分析",
  //   properties: {
  //     競爭者介紹: {
  //       title: "1.目前貴司在業界生態中的競爭者介紹",
  //       description: "你認為的競爭對手有誰?為什麼是他? 建議2-3家",
  //     },
  //     差異性: {
  //       title: "2.這些競爭者與本產品/服務的差異在哪?",
  //       description:
  //         "你的競爭優勢是什麼? 客戶買你產品的關鍵原因是什麼?\n價格? 產品更好用? 品質比客人好?",
  //     },
  //   },
  // },
  // "六、計畫目標、效益": {
  //   title: "六、計畫目標、效益",
  //   properties: {
  //     查核點量化數值: {
  //       title: "1.具體查核點量化數值",
  //       description:
  //         "(如:研發可產出的具體量化指標，例如產品(尺寸、規格)、功能測試(通過SGS抗衝擊測試等)",
  //     },
  //     量化效益: {
  //       title: "3.量化效益",
  //       description:
  //         "此依據為計劃標準格式:\n(1)增加產值 元\n(2)產出新產品或服務共 項\n(3)衍生商品或服務數共 項\n(4)促成投資額 元(新購設備)\n(5)降低成本 元\n(6)增加就業人數 人\n(7)成立新公司 家\n(8)發明專利共 件\n(9)新型、新式樣專利共 件",
  //     },
  //   },
  // },
  // "七、可行性分析": {
  //   title: "七、可行性分析",
  //   properties: {
  //     過往研究成果: {
  //       title: "1.過往研究成果",
  //       description:
  //         "(例:是否有過往研發紀錄影像、照片、樣品、討論會議側錄等已在申請前就以佈局研發?)",
  //     },
  //     公司背景: {
  //       title: "2.公司背景、商業化與參展紀錄",
  //       description:
  //         "請敘述公司背景（技術、優勢、規模、團隊經驗等），並說明商業化接軌情況（例如是否已有潛在客戶或 MOU）以及歷年參展或得獎紀錄。",
  //     },
  //   },
  // },
  // "八、功能規格": {
  //   title: "八、功能規格(計畫可驗收指標)",
  //   properties: {
  //     非硬體標的規格: {
  //       title: "1.非硬體標的規格",
  //       description: "(例:平台功能、相容性、辨識度...)",
  //     },
  //     硬體標的規格: {
  //       title: "2.硬體標的規格",
  //       description: "(例:機械強度、耐磨、防水等級...)",
  //     },
  //   },
  // },
  // "九、智財分析": {
  //   title: "九、智財分析",
  //   properties: {
  //     專利申請狀況: {
  //       title: "1.是否已有完成專利申請?",
  //       description:
  //         "(1)例:委託專利事務所紀錄、申請送出紀錄、完成申請公文、多國專利等\n(2)後續如何進行智財佈局規劃?專利主張為何?是否會與其他業者專利有衝突?",
  //     },
  //     // 測試檢驗規劃: {
  //     //   title: "2.將進行那些測試.檢驗",
  //     //   description: "",
  //     // },
  //   },
  // },
  // // "十、經費": {
  // //   title: "十、經費",
  // //   properties: {
  // //     人事費: {
  // //       title: "1.每月人事費(公司人事費)",
  // //       description: "目前貴司的人事費用情況",
  // //     },
  // //     材料費: {
  // //       title: "2.每月研發材料費【研發所需材料費用，品項名稱必須相符】",
  // //       description:
  // //         "目前貴司過往會採買的材料清單\n**可獨立運行非材料費**\n(計畫中須能配合開發票出來核銷)\n業務說明編列方式及注意事項",
  // //     },
  // //     委外單位費: {
  // //       title: "3.每月委外單位費(例如SGS檢驗)",
  // //       description:
  // //         "例如：本專案預計檢測、開發、設計、行銷，委外單位?合作單位在該計畫中負責項目?花多少錢?",
  // //     },
  // //   },
  // // },
};

// ===== 远程 API 数据接口 =====
/**
 * 从后端 API 返回的字段定义（远程格式）
 *
 * 说明：
 *   - 这是后端数据库中的字段定义格式
 *   - 与本地的 DynamicSchemaProperty 对应
 *   - 包含数据库 ID 和排序信息
 */
interface RemoteDynamicField {
  id: string; // 数据库中的字段 ID
  section_id: string; // 所属章节 ID
  field_key: string; // 字段编程标识符
  title: string; // 字段显示标题
  description?: string; // 字段说明（可选）
  order: number; // 字段排序顺序
}

/**
 * 从后端 API 返回的章节定义（远程格式）
 *
 * 说明：
 *   - 这是后端数据库中的章节定义格式
 *   - 与本地的 DynamicSchemaSection 对应
 *   - 包含该章节的所有字段
 */
interface RemoteDynamicSection {
  id: string; // 数据库中的章节 ID
  schema_id: string; // 所属 Schema ID
  section_key: string; // 章节编程标识符
  title: string; // 章节显示标题
  order: number; // 章节排序顺序
  fields: RemoteDynamicField[]; // 该章节的所有字段
  template_id?: string | null; // 所属模板 ID（可选）
  template_grant_id?: string | null; // 所属补助金 ID（可选）
}

// ===== 缓存和状态管理常量 =====
// 默认 Schema ID（当没有指定时使用）
const DEFAULT_SCHEMA_ID = "default";

// ===== 静态 Schema 初始化 =====
/**
 * 从静态定义生成回退 Schema 章节数组
 *
 * 说明：
 *   - 将 RAW_DYNAMIC_SCHEMA（硬编码的字段定义）转换为 DynamicSchemaSection 格式
 *   - 当后端 API 加载失败时，使用此静态定义作为回退方案
 *   - 这样即使网络问题也能保证应用继续工作
 */
const FALLBACK_SCHEMA_SECTIONS: DynamicSchemaSection[] = Object.entries(
  RAW_DYNAMIC_SCHEMA,
).map(([sectionKey, sectionValue]) => ({
  id: sectionKey,
  title: sectionValue.title,
  properties: Object.entries(sectionValue.properties).map(
    ([propertyKey, propertyValue]) => ({
      key: propertyKey,
      title: propertyValue.title,
      description: propertyValue.description,
    }),
  ),
}));

// ===== 全局状态管理 =====
// 当前活跃的 Schema 章节（内存中的副本）
let schemaSections: DynamicSchemaSection[] = [...FALLBACK_SCHEMA_SECTIONS];
// 当前活跃的模板 ID（用于字段过滤）
let activeTemplateId: string | null = null;
// 当前活跃的补助金 ID（用于字段过滤）
let activeTemplateGrantId: string | null = null;

interface SchemaFilterOptions {
  templateId?: string | null;
  templateGrantId?: string | null;
}

function cloneFallbackSections(): DynamicSchemaSection[] {
  return FALLBACK_SCHEMA_SECTIONS.map((section) => ({
    ...section,
    properties: section.properties.map((property) => ({ ...property })),
  }));
}

function matchesTemplate(
  section: DynamicSchemaSection,
  templateId?: string | null,
  templateGrantId?: string | null,
): boolean {
  if (!templateId && !templateGrantId) {
    return true;
  }
  if (templateId && section.templateId !== templateId) {
    return false;
  }
  if (templateGrantId && section.templateGrantId !== templateGrantId) {
    return false;
  }
  return Boolean(
    (!templateId || section.templateId === templateId) &&
    (!templateGrantId || section.templateGrantId === templateGrantId),
  );
}

function getRenderableSections(options?: SchemaFilterOptions) {
  const targetTemplateId = options?.templateId ?? activeTemplateId;
  const targetTemplateGrantId =
    options?.templateGrantId ?? activeTemplateGrantId;

  return schemaSections.filter((section) =>
    matchesTemplate(section, targetTemplateId, targetTemplateGrantId),
  );
}

function mapRemoteSections(
  sections: RemoteDynamicSection[],
): DynamicSchemaSection[] {
  return sections
    .slice()
    .sort((a, b) => (a.order || 0) - (b.order || 0))
    .map((section) => ({
      id: section.section_key,
      title: section.title,
      properties: (section.fields || [])
        .slice()
        .sort((a, b) => (a.order || 0) - (b.order || 0))
        .map((field) => ({
          key: field.field_key,
          title: field.title,
          description: field.description || "",
        })),
      templateId: section.template_id || null,
      templateGrantId: section.template_grant_id || null,
    }));
}

interface FetchRemoteSchemaOptions {
  schemaId: string;
  templateId?: string | null;
  templateGrantId?: string | null;
}

async function fetchRemoteSchema({
  schemaId,
  templateId,
  templateGrantId,
}: FetchRemoteSchemaOptions): Promise<DynamicSchemaSection[]> {
  const config = useRuntimeConfig();
  console.log("API Base URL:", config.public.apiBaseUrl);
  let baseUrl = config.public.apiBaseUrl || "";
  console.log("Resolved API Base URL:", baseUrl);

  // // Handle empty string -> current origin
  // if (!baseUrl) {
  //   if (typeof window !== "undefined") {
  //     baseUrl = window.location.origin;
  //   } else {
  //     baseUrl = "http://localhost:8000";
  //   }
  // }
  // // Handle relative path (starting with /)
  // else if (baseUrl.startsWith("/")) {
  //   if (typeof window !== "undefined") {
  //     baseUrl = window.location.origin + baseUrl;
  //   } else {
  //     baseUrl = "http://localhost:8000" + baseUrl;
  //   }
  // }

  // // Ensure no trailing slash to avoid double slash issues
  // if (baseUrl.endsWith("/")) {
  //   baseUrl = baseUrl.slice(0, -1);
  // }

  const url = new URL(`${baseUrl}/api/dynamic-sections`);

  if (templateId) {
    url.searchParams.set("template_id", templateId);
    if (templateGrantId) {
      url.searchParams.set("template_grant_id", templateGrantId);
    }
  } else {
    url.searchParams.set("schema_id", schemaId);
  }

  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error(`Failed to fetch remote schema: ${response.status}`);
  }

  const payload: RemoteDynamicSection[] = await response.json();
  if (!Array.isArray(payload) || payload.length === 0) {
    return [];
  }

  return mapRemoteSections(payload);
}

export async function ensureDynamicSchemaLoaded(options?: {
  schemaId?: string;
  templateId?: string | null;
  templateGrantId?: string | null;
}): Promise<DynamicSchemaSection[]> {
  const targetSchemaId = options?.schemaId || DEFAULT_SCHEMA_ID;
  const templateId = options?.templateId ?? null;
  const templateGrantId = options?.templateGrantId ?? null;
  activeTemplateId = templateId;
  activeTemplateGrantId = templateGrantId;

  try {
    const remoteSections = await fetchRemoteSchema({
      schemaId: targetSchemaId,
      templateId,
      templateGrantId,
    });
    const resolvedSections =
      remoteSections.length > 0 ? remoteSections : cloneFallbackSections();
    schemaSections = resolvedSections;
    return resolvedSections;
  } catch (error) {
    console.warn(
      "Failed to load dynamic schema from API, fallback to static definition.",
      error,
    );
    const fallbackSections = cloneFallbackSections();
    schemaSections = fallbackSections;
    return fallbackSections;
  }
}
/**
 * 生成複合鍵，作為欄位的唯一識別
 *
 * 格式：section::field
 * 例如："二、研發動機::市場規模"
 */
export function makeCompositeKey(
  sectionId: string,
  propertyKey: string,
): string {
  return `${sectionId}::${propertyKey}`;
}

function normalizeLabel(label: string): string {
  return label.replace(/\s+/g, "").toLowerCase();
}

function buildFieldLabel(sectionTitle: string, propertyTitle: string): string {
  return `${sectionTitle}｜${propertyTitle}`;
}
// ===== 占位符生成工具 =====
/**
 * 构建输入框占位符文本
 *
 * 说明：
 *   - 组合字段标题和描述生成占位符
 *   - 优化用户输入体验
 *
 * 参数：
 *   - fieldTitle: 字段标题
 *   - description: 字段描述
 *
 * 返回值：格式化的占位符文本
 */
function buildPlaceholder(fieldTitle: string, description: string): string {
  const base = `請填寫「${fieldTitle}」的內容`;
  if (!description) {
    return base;
  }
  return `${base}\n提示: ${description}`;
}

// ===== 导出的公共 API 函数 =====

/**
 * 创建空的动态字段值映射
 *
 * 功能：
 *   - 为所有定义的字段创建空值映射
 *   - 每个字段初始值都是空字符串
 *
 * 用途：
 *   - 初始化新的草稿或项目
 *   - 重置表单所有字段
 *   - 作为合并操作的基础
 *
 * 参数：
 *   - options?: 过滤选项（可选，指定模板/补助金）
 *
 * 返回值：
 *   - DynamicValueMap: 包含所有字段的空值映射
 *     例如：{
 *       "二、研發動機::核心問題": "",
 *       "二、研發動機::市場規模": "",
 *       ...
 *     }
 */
export function createEmptyDynamicValues(
  options?: SchemaFilterOptions,
): DynamicValueMap {
  const values: DynamicValueMap = {};
  const sections = getRenderableSections(options);
  sections.forEach((section) => {
    section.properties.forEach((property) => {
      const key = makeCompositeKey(section.id, property.key);
      values[key] = "";
    });
  });
  return values;
}

/**
 * 构建前端 UI 视图模型（ViewModel）
 *
 * 功能：
 *   - 将平面的值映射（DynamicValueMap）转换为树状结构
 *   - 注入用户输入的值到 Schema 定义
 *   - 添加 UI 渲染所需的辅助信息（占位符、复合键等）
 *
 * 工作流程：
 *   1. 获取可渲染的 Schema 章节（应用过滤）
 *   2. 遍历每个章节和其字段
 *   3. 从值映射中查找当前字段的值
 *   4. 构建完整的字段视图模型（包含标题、描述、值、占位符等）
 *   5. 返回树状结构
 *
 * 用途：
 *   - 提供给 Vue 组件进行模板渲染
 *   - 完整包含 UI 渲染所需的所有信息
 *   - 支持多个模板的字段过滤
 *
 * 参数：
 *   - values: 动态字段的值映射（默认为空映射）
 *   - options: 过滤选项（指定模板/补助金）
 *
 * 返回值：
 *   - DynamicSectionViewModel[]: 视图模型数组，可直接用于模板渲染
 *     每个章节包含所有字段的完整信息（标题、值、占位符等）
 *
 * 示例：
 *   const sections = buildDynamicSections(
 *     {"二、研發動機::核心問題": "开发 AI 模型..."},
 *     {templateId: "template1"}
 *   );
 *   // 结果用于 v-for 遍历和表单渲染
 */
export function buildDynamicSections(
  values: DynamicValueMap = {},
  options?: SchemaFilterOptions,
): DynamicSectionViewModel[] {
  const sections = getRenderableSections(options);
  return sections.map((section) => ({
    sectionId: section.id,
    sectionName: section.title,
    fields: section.properties.map((property) => {
      const compositeKey = makeCompositeKey(section.id, property.key);
      return {
        propertyKey: property.key,
        title: property.title,
        description: property.description,
        compositeKey,
        placeholder: buildPlaceholder(property.title, property.description),
        value: values[compositeKey] ?? "",
      };
    }),
  }));
}

/**
 * 合併值映射和空值
 * 確保返回的映射包含所有定義的字段，缺失的字段填充為空字符串
 *
 * 用途：處理部分更新時，保留其他字段的原值，同時補充新增字段
 * @param values - 輸入的值映射
 * @returns 合併後的完整值映射
 */
export function mergeIntoEmptyValues(
  values: DynamicValueMap | undefined,
  options?: SchemaFilterOptions,
): DynamicValueMap {
  const merged = createEmptyDynamicValues(options);
  if (!values) {
    return merged;
  }
  Object.entries(values).forEach(([key, value]) => {
    if (merged[key] !== undefined) {
      merged[key] = value ?? "";
    }
  });
  return merged;
}

export function getDynamicFieldDefinitions(
  options?: SchemaFilterOptions,
): DynamicFieldDefinition[] {
  return getRenderableSections(options).flatMap((section) =>
    section.properties.map((property) => ({
      sectionId: section.id,
      sectionTitle: section.title,
      propertyKey: property.key,
      propertyTitle: property.title,
      description: property.description,
      compositeKey: makeCompositeKey(section.id, property.key),
      label: buildFieldLabel(section.title, property.title),
    })),
  );
}

export function getDynamicFieldLabels(options?: SchemaFilterOptions): string[] {
  return getDynamicFieldDefinitions(options).map(
    (definition) => definition.label,
  );
}

export function getCompositeKeyFromLabel(
  label?: string | null,
  options?: SchemaFilterOptions,
): string | null {
  if (!label) {
    return null;
  }
  const normalizedTarget = normalizeLabel(label);
  const definitions = getDynamicFieldDefinitions(options);

  const exactMatch = definitions.find(
    (definition) => normalizeLabel(definition.label) === normalizedTarget,
  );
  if (exactMatch) {
    return exactMatch.compositeKey;
  }

  const titleMatch = definitions.find(
    (definition) =>
      normalizeLabel(definition.propertyTitle) === normalizedTarget,
  );
  if (titleMatch) {
    return titleMatch.compositeKey;
  }

  const partialMatch = definitions.find((definition) =>
    normalizedTarget.includes(normalizeLabel(definition.propertyTitle)),
  );
  return partialMatch ? partialMatch.compositeKey : null;
}

export function getAllCompositeKeys(options?: SchemaFilterOptions): string[] {
  return getRenderableSections(options).flatMap((section) =>
    section.properties.map((property) =>
      makeCompositeKey(section.id, property.key),
    ),
  );
}

/**
 * 獲取所有動態字段的標籤清單（用於 AI 提示）
 * 返回所有字段的完整標籤，用於向 AI 模型描述可用的字段
 *
 * 用途：生成合成輸入時傳給後端 API
 * @returns 字段標籤的字符串數組
 */
export { schemaSections as STATIC_DYNAMIC_SCHEMA };
