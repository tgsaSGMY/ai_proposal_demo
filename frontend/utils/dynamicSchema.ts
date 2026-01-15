/**
 * 動態輸入字段 Schema 定義和工具函數
 *
 * 此模塊管理整個應用的動態字段結構，包括：
 * - 靜態字段定義（不依賴運行時配置）
 * - 複合鍵（composite key）生成和管理
 * - UI 視圖模型（ViewModel）構建
 * - 字段值映射和驗證
 */

/**
 * 動態字段值的鍵類型
 * 格式：section::field
 * 例如："二、研發動機::市場規模"
 */
export type DynamicValueKey = string;

/**
 * 動態字段值的映射表
 * 鍵是複合鍵字符串，值是字段內容（通常是文本）
 */
export type DynamicValueMap = Record<DynamicValueKey, string>;

import { supabase } from "~/utils/supabaseClient";

export interface DynamicSchemaProperty {
  key: string;
  title: string;
  description: string;
}

/**
 * Schema 中章節的定義
 * 每個章節包含多個字段（屬性）
 */
export interface DynamicSchemaSection {
  id: string;
  title: string;
  properties: DynamicSchemaProperty[];
  templateId?: string | null;
  templateGrantId?: string | null;
}

/**
 * UI 展示用的章節視圖模型
 * 用於在前端渲染時提供完整的結構化數據
 */
export interface DynamicSectionViewModel {
  sectionId: string;
  sectionName: string;
  fields: DynamicFieldViewModel[];
}

/**
 * UI 展示用的字段視圖模型
 * 包含欄位在前端渲染所需的完整資訊
 */
export interface DynamicFieldViewModel {
  propertyKey: string;
  title: string;
  description: string;
  compositeKey: string;
  placeholder: string;
  value: string;
}

export interface DynamicFieldDefinition {
  sectionId: string;
  sectionTitle: string;
  propertyKey: string;
  propertyTitle: string;
  description: string;
  compositeKey: string;
  label: string;
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

interface RemoteDynamicField {
  id: string;
  section_id: string;
  field_key: string;
  title: string;
  description?: string;
  order: number;
}

interface RemoteDynamicSection {
  id: string;
  schema_id: string;
  section_key: string;
  title: string;
  order: number;
  fields: RemoteDynamicField[];
  template_id?: string | null;
  template_grant_id?: string | null;
}

const DEFAULT_SCHEMA_ID = "default";
const SCHEMA_CACHE_TTL = 1000 * 60 * 5; // 5 minutes

const FALLBACK_SCHEMA_SECTIONS: DynamicSchemaSection[] = Object.entries(
  RAW_DYNAMIC_SCHEMA
).map(([sectionKey, sectionValue]) => ({
  id: sectionKey,
  title: sectionValue.title,
  properties: Object.entries(sectionValue.properties).map(
    ([propertyKey, propertyValue]) => ({
      key: propertyKey,
      title: propertyValue.title,
      description: propertyValue.description,
    })
  ),
}));

interface SchemaCacheEntry {
  sections: DynamicSchemaSection[];
  loadedAt: number;
}

let schemaSections: DynamicSchemaSection[] = [...FALLBACK_SCHEMA_SECTIONS];
let activeTemplateId: string | null = null;
let activeTemplateGrantId: string | null = null;
const schemaCache: Record<string, SchemaCacheEntry> = {};
const schemaLoadPromises: Record<string, Promise<DynamicSchemaSection[]>> = {};

interface SchemaFilterOptions {
  templateId?: string | null;
  templateGrantId?: string | null;
}

function buildCacheKey({
  schemaId,
  templateId,
  templateGrantId,
}: {
  schemaId: string;
  templateId?: string | null;
  templateGrantId?: string | null;
}) {
  const normalizedSchema = schemaId || DEFAULT_SCHEMA_ID;
  const normalizedGrant = templateGrantId || "all-grants";
  const normalizedTemplate = templateId || "all-templates";
  return `${normalizedGrant}::${normalizedTemplate}::${normalizedSchema}`;
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
  templateGrantId?: string | null
): boolean {
  if (!templateId && !templateGrantId) {
    return true;
  }
  if (templateId && section.templateId && section.templateId !== templateId) {
    return false;
  }
  if (
    templateGrantId &&
    section.templateGrantId &&
    section.templateGrantId !== templateGrantId
  ) {
    return false;
  }
  return true;
}

function getRenderableSections(options?: SchemaFilterOptions) {
  const targetTemplateId = options?.templateId ?? activeTemplateId;
  const targetTemplateGrantId =
    options?.templateGrantId ?? activeTemplateGrantId;
  return schemaSections.filter((section) =>
    matchesTemplate(section, targetTemplateId, targetTemplateGrantId)
  );
}

function mapRemoteSections(
  sections: RemoteDynamicSection[]
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
  apiBaseUrl?: string;
}

async function fetchRemoteSchema({
  schemaId,
  templateId,
  templateGrantId,
  apiBaseUrl = "http://localhost:8000",
}: FetchRemoteSchemaOptions): Promise<DynamicSchemaSection[]> {
  const url = new URL(`${apiBaseUrl}/api/dynamic-sections`);
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
  forceRefresh?: boolean;
  apiBaseUrl?: string;
  templateId?: string | null;
  templateGrantId?: string | null;
}): Promise<DynamicSchemaSection[]> {
  const targetSchemaId = options?.schemaId || DEFAULT_SCHEMA_ID;
  const apiBaseUrl = options?.apiBaseUrl || "http://localhost:8000";
  const templateId = options?.templateId ?? null;
  const templateGrantId = options?.templateGrantId ?? null;
  const cacheKey = buildCacheKey({
    schemaId: targetSchemaId,
    templateId,
    templateGrantId,
  });
  const now = Date.now();
  activeTemplateId = templateId;
  activeTemplateGrantId = templateGrantId;

  const cachedEntry = schemaCache[cacheKey];
  if (
    !options?.forceRefresh &&
    cachedEntry &&
    now - cachedEntry.loadedAt < SCHEMA_CACHE_TTL
  ) {
    schemaSections = cachedEntry.sections;
    return cachedEntry.sections;
  }

  if (!options?.forceRefresh && schemaLoadPromises[cacheKey]) {
    return schemaLoadPromises[cacheKey];
  }

  const loadPromise = (async () => {
    try {
      const remoteSections = await fetchRemoteSchema({
        schemaId: targetSchemaId,
        templateId,
        templateGrantId,
        apiBaseUrl,
      });
      const resolvedSections =
        remoteSections.length > 0 ? remoteSections : cloneFallbackSections();
      schemaCache[cacheKey] = {
        sections: resolvedSections,
        loadedAt: Date.now(),
      };
      schemaSections = resolvedSections;
      return resolvedSections;
    } catch (error) {
      console.warn(
        "Failed to load dynamic schema from API, fallback to static definition.",
        error
      );
      const fallbackSections = cloneFallbackSections();
      schemaCache[cacheKey] = {
        sections: fallbackSections,
        loadedAt: Date.now(),
      };
      schemaSections = fallbackSections;
      return fallbackSections;
    }
  })().finally(() => {
    delete schemaLoadPromises[cacheKey];
  });

  schemaLoadPromises[cacheKey] = loadPromise;
  return loadPromise;
}

/**
 * 生成複合鍵，作為欄位的唯一識別
 *
 * 格式：section::field
 * 例如："二、研發動機::市場規模"
 */
export function makeCompositeKey(
  sectionId: string,
  propertyKey: string
): string {
  return `${sectionId}::${propertyKey}`;
}

function normalizeLabel(label: string): string {
  return label.replace(/\s+/g, "").toLowerCase();
}

function buildFieldLabel(sectionTitle: string, propertyTitle: string): string {
  return `${sectionTitle}｜${propertyTitle}`;
}

function buildPlaceholder(fieldTitle: string, description: string): string {
  const base = `請填寫「${fieldTitle}」的內容`;
  if (!description) {
    return base;
  }
  return `${base}\n提示: ${description}`;
}

/**
 * 創建一個空的動態字段值映射
 * 所有字段初始值都是空字符串
 *
 * 用途：初始化新草稿或重置字段
 * @returns 包含所有字段的空值映射
 */
export function createEmptyDynamicValues(
  options?: SchemaFilterOptions
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
 * 構建 UI 視圖模型（ViewModel）
 * 將平面的值映射轉換為樹狀結構的 ViewModel，用於前端渲染
 *
 * 流程：RAW_DYNAMIC_SCHEMA -> 遍歷結構 -> 注入值 -> ViewModel
 *
 * 用途：提供給 Vue 組件使用，完整包含 UI 渲染所需的所有信息
 * @param values - 動態字段的值映射
 * @returns 視圖模型數組，可直接用於模板渲染
 */
export function buildDynamicSections(
  values: DynamicValueMap = {},
  options?: SchemaFilterOptions
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
  options?: SchemaFilterOptions
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
  options?: SchemaFilterOptions
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
    }))
  );
}

export function getDynamicFieldLabels(options?: SchemaFilterOptions): string[] {
  return getDynamicFieldDefinitions(options).map(
    (definition) => definition.label
  );
}

export function getCompositeKeyFromLabel(label?: string | null): string | null {
  if (!label) {
    return null;
  }
  const normalizedTarget = normalizeLabel(label);
  const definitions = getDynamicFieldDefinitions();

  const exactMatch = definitions.find(
    (definition) => normalizeLabel(definition.label) === normalizedTarget
  );
  if (exactMatch) {
    return exactMatch.compositeKey;
  }

  const titleMatch = definitions.find(
    (definition) =>
      normalizeLabel(definition.propertyTitle) === normalizedTarget
  );
  if (titleMatch) {
    return titleMatch.compositeKey;
  }

  const partialMatch = definitions.find((definition) =>
    normalizedTarget.includes(normalizeLabel(definition.propertyTitle))
  );
  return partialMatch ? partialMatch.compositeKey : null;
}

export function getAllCompositeKeys(options?: SchemaFilterOptions): string[] {
  return getRenderableSections(options).flatMap((section) =>
    section.properties.map((property) =>
      makeCompositeKey(section.id, property.key)
    )
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
