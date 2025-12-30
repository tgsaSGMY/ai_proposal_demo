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
 * 格式：section::property::subfield
 * 例如："二、研發動機::市場規模::reply"
 */
export type DynamicValueKey = string;

/**
 * 動態字段值的映射表
 * 鍵是複合鍵字符串，值是字段內容（通常是文本）
 */
export type DynamicValueMap = Record<DynamicValueKey, string>;

/**
 * 子字段定義接口
 * 每個字段可能有多個子字段（如：回覆、驗收方式等）
 * 目前只使用 "reply"，其他子字段類型已預留
 */
export interface DynamicSubFieldDefinition {
  key: DynamicSubFieldKey;
  label: string;
}

/**
 * 子字段鍵類型
 * - reply: 主要回覆內容
 * - primary_issue: 第一層問題（保留）
 * - secondary_issue: 第二層問題（保留）
 * - tertiary_issue: 第三層問題（保留）
 * - acceptance: 驗收方式（保留）
 */
export type DynamicSubFieldKey =
  | "reply"
  | "primary_issue"
  | "secondary_issue"
  | "tertiary_issue"
  | "acceptance";

/**
 * Schema 中字段的屬性定義
 * 對應 RAW_DYNAMIC_SCHEMA 中的屬性信息
 */
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
 * 包含字段的完整信息和其子字段
 */
export interface DynamicFieldViewModel {
  propertyKey: string;
  title: string;
  description: string;
  subFields: DynamicSubFieldViewModel[];
}

/**
 * UI 展示用的子字段視圖模型
 * 包含所有渲染和數據綁定所需的信息
 */
export interface DynamicSubFieldViewModel {
  id: string;
  compositeKey: string; // 複合鍵用於數據存儲
  key: DynamicSubFieldKey; // 子字段類型
  label: string; // 長標籤（用於 AI 輸入）
  shortLabel: string; // 短標籤（用於 UI 顯示）
  placeholder: string; // 輸入框提示文本
  description: string; // 字段描述
  value: string; // 當前值
}

export const DYNAMIC_SUB_FIELD_DEFINITIONS: DynamicSubFieldDefinition[] = [
  { key: "reply", label: "回覆" },
];

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
  "三、解決辦法": {
    title: "三、解決辦法",
    properties: {
      產品內容: {
        title: "1.具體說明你的產品或服務是什麼?",
        description: "請清楚具體說明，你要研發或設計的服務是什麼?",
      },
      關鍵技術: {
        title: "2.關鍵技術為何",
        description:
          "關鍵環節詳細說明\nex1: 研發上最困難的地方在哪裡?或是花最多時間的項目、印象最深刻的地方?\nex2: 目前流程最卡的地方在哪?解決關鍵的痛點",
      },
      商業模式運作流程: {
        title: "3.商業模式運作流程",
        description: "舉例：客戶登入→使用平台→取得反饋→改良產品→行銷推廣",
      },
    },
  },
  "四、創新性分析與驗收方式": {
    title: "四、創新性分析與驗收方式",
    properties: {
      既有流程說明: {
        title: "1.技術或服務的創新性?既有流程說明",
        description: "既有流程 vs 改善後的流程\n過去與現在的作業差異說明",
      },
      自行測試方式: {
        title: "1.公司自行測試方式為何?",
        description: "公司與客戶間如何確認品質?",
      },
      第三方檢測方式: {
        title: "2.第三方檢測方式為何?",
        description: "如:委託SGS等單位",
      },
    },
  },
  "五、競爭力分析": {
    title: "五、競爭力分析",
    properties: {
      競爭者介紹: {
        title: "1.目前貴司在業界生態中的競爭者介紹",
        description: "你認為的競爭對手有誰?為什麼是他? 建議2-3家",
      },
      差異性: {
        title: "2.這些競爭者與本產品/服務的差異在哪?",
        description:
          "你的競爭優勢是什麼? 客戶買你產品的關鍵原因是什麼?\n價格? 產品更好用? 品質比客人好?",
      },
    },
  },
  "六、計畫目標、效益": {
    title: "六、計畫目標、效益",
    properties: {
      查核點量化數值: {
        title: "1.具體查核點量化數值",
        description:
          "(如:研發可產出的具體量化指標，例如產品(尺寸、規格)、功能測試(通過SGS抗衝擊測試等)",
      },
      量化效益: {
        title: "3.量化效益",
        description:
          "此依據為計劃標準格式:\n(1)增加產值 元\n(2)產出新產品或服務共 項\n(3)衍生商品或服務數共 項\n(4)促成投資額 元(新購設備)\n(5)降低成本 元\n(6)增加就業人數 人\n(7)成立新公司 家\n(8)發明專利共 件\n(9)新型、新式樣專利共 件",
      },
    },
  },
  "七、可行性分析": {
    title: "七、可行性分析",
    properties: {
      過往研究成果: {
        title: "1.過往研究成果",
        description:
          "(例:是否有過往研發紀錄影像、照片、樣品、討論會議側錄等已在申請前就以佈局研發?)",
      },
      商業化接軌可行性: {
        title: "2.商業化接軌可行性",
        description: "(例:本標的是否已有潛在客戶、已簽mou客戶之清單?)",
      },
      參展獲獎紀錄: {
        title: "3.有無過往參展、獲獎、活動之紀錄證明?",
        description: "(例：獎項得獎，若有公司簡介\n請上傳公司簡介)",
      },
      公司背景: {
        title: "4.公司本身詳細介紹其背景(包含人才陣容及團隊經驗)",
        description:
          "(例:技術、優勢、規模、人員、據點布局等\n強調以在該產業有多年深耕)",
      },
      檢測與背書: {
        title: "5.是否已完成檢測?有無他人背書?",
        description: "(例:標的使用的原料、樣品是否有SGS檢測、學院檢測...)",
      },
    },
  },
  "八、功能規格": {
    title: "八、功能規格(計畫可驗收指標)",
    properties: {
      非硬體標的規格: {
        title: "1.非硬體標的規格",
        description: "(例:平台功能、相容性、辨識度...)",
      },
      硬體標的規格: {
        title: "2.硬體標的規格",
        description: "(例:機械強度、耐磨、防水等級...)",
      },
    },
  },
  "九、智財分析": {
    title: "九、智財分析",
    properties: {
      專利申請狀況: {
        title: "1.是否已有完成專利申請?",
        description:
          "(1)例:委託專利事務所紀錄、申請送出紀錄、完成申請公文、多國專利等\n(2)後續如何進行智財佈局規劃?專利主張為何?是否會與其他業者專利有衝突?",
      },
      // 測試檢驗規劃: {
      //   title: "2.將進行那些測試.檢驗",
      //   description: "",
      // },
    },
  },
  // "十、經費": {
  //   title: "十、經費",
  //   properties: {
  //     人事費: {
  //       title: "1.每月人事費(公司人事費)",
  //       description: "目前貴司的人事費用情況",
  //     },
  //     材料費: {
  //       title: "2.每月研發材料費【研發所需材料費用，品項名稱必須相符】",
  //       description:
  //         "目前貴司過往會採買的材料清單\n**可獨立運行非材料費**\n(計畫中須能配合開發票出來核銷)\n業務說明編列方式及注意事項",
  //     },
  //     委外單位費: {
  //       title: "3.每月委外單位費(例如SGS檢驗)",
  //       description:
  //         "例如：本專案預計檢測、開發、設計、行銷，委外單位?合作單位在該計畫中負責項目?花多少錢?",
  //     },
  //   },
  // },
};

const schemaSections: DynamicSchemaSection[] = Object.entries(
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

const subFieldDefinitionMap = new Map<DynamicSubFieldKey, string>(
  DYNAMIC_SUB_FIELD_DEFINITIONS.map((def) => [def.key, def.label])
);

/**
 * ============================================================
 * 核心公開函數
 * ============================================================
 */

/**
 * 獲取所有動態字段的標籤清單
 * 返回格式：[{ label: "1.技術或服務的核心問題是甚麼? - 回覆" }, ...]
 *
 * 用途：批量操作時發送給後端 API
 * @returns 所有字段的標籤列表
 */
export function getAllCompositeKeys(): Array<{ label: string }> {
  const keys: Array<{ label: string }> = [];
  schemaSections.forEach((section) => {
    section.properties.forEach((property) => {
      DYNAMIC_SUB_FIELD_DEFINITIONS.forEach((subField) => {
        const compositeKey = makeCompositeKey(
          section.id,
          property.key,
          subField.key
        );
        keys.push({ label: compositeKey });
      });
    });
  });
  return keys;
}

/**
 * 生成複合鍵
 * 複合鍵是字段的唯一標識，用於數據存儲和檢索
 *
 * 格式：section::property::subfield
 * 例如："二、研發動機::市場規模::reply"
 *
 * @param sectionId - 章節 ID
 * @param propertyKey - 字段鍵
 * @param subFieldKey - 子字段鍵
 * @returns 複合鍵字符串
 */
export function makeCompositeKey(
  sectionId: string,
  propertyKey: string,
  subFieldKey: DynamicSubFieldKey
): string {
  return `${sectionId}::${propertyKey}::${subFieldKey}`;
}

/**
 * 根據子字段類型獲取其標籤
 * @param subKey - 子字段類型
 * @returns 子字段的中文標籤
 */
function resolveSubFieldLabel(subKey: DynamicSubFieldKey): string {
  return subFieldDefinitionMap.get(subKey) || subKey;
}

/**
 * 生成輸入框的提示文本
 * @param fieldTitle - 字段標題
 * @param subLabel - 子字段標籤
 * @param description - 字段描述
 * @returns 格式化的提示文本
 */
function buildPlaceholder(
  fieldTitle: string,
  subLabel: string,
  description: string
): string {
  const base = `請填寫「${fieldTitle}」的${subLabel}`;
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
export function createEmptyDynamicValues(): DynamicValueMap {
  const values: DynamicValueMap = {};
  schemaSections.forEach((section) => {
    section.properties.forEach((property) => {
      DYNAMIC_SUB_FIELD_DEFINITIONS.forEach((subField) => {
        const key = makeCompositeKey(section.id, property.key, subField.key);
        values[key] = "";
      });
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
  values: DynamicValueMap = {}
): DynamicSectionViewModel[] {
  return schemaSections.map((section) => ({
    sectionId: section.id,
    sectionName: section.title,
    fields: section.properties.map((property) => ({
      propertyKey: property.key,
      title: property.title,
      description: property.description,
      subFields: DYNAMIC_SUB_FIELD_DEFINITIONS.map((subField) => {
        const compositeKey = makeCompositeKey(
          section.id,
          property.key,
          subField.key
        );
        const value = values[compositeKey] ?? "";
        const label = `${property.title} - ${resolveSubFieldLabel(
          subField.key
        )}`;
        return {
          id: compositeKey,
          compositeKey,
          key: subField.key,
          label,
          shortLabel: resolveSubFieldLabel(subField.key),
          placeholder: buildPlaceholder(
            property.title,
            resolveSubFieldLabel(subField.key),
            property.description
          ),
          description: property.description,
          value,
        };
      }),
    })),
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
  values: DynamicValueMap | undefined
): DynamicValueMap {
  const merged = createEmptyDynamicValues();
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

export function extractFilledSubFields(values: DynamicValueMap): {
  sectionId: string;
  sectionName: string;
  propertyKey: string;
  propertyTitle: string;
  subFieldKey: DynamicSubFieldKey;
  label: string;
  value: string;
}[] {
  const sections = buildDynamicSections(values);
  const entries: {
    sectionId: string;
    sectionName: string;
    propertyKey: string;
    propertyTitle: string;
    subFieldKey: DynamicSubFieldKey;
    label: string;
    value: string;
  }[] = [];

  sections.forEach((section) => {
    section.fields.forEach((field) => {
      field.subFields.forEach((subField) => {
        if (subField.value && subField.value.trim() !== "") {
          entries.push({
            sectionId: section.sectionId,
            sectionName: section.sectionName,
            propertyKey: field.propertyKey,
            propertyTitle: field.title,
            subFieldKey: subField.key,
            label: subField.label,
            value: subField.value,
          });
        }
      });
    });
  });

  return entries;
}

/**
 * 獲取所有動態字段的標籤清單（用於 AI 提示）
 * 返回所有字段的完整標籤，用於向 AI 模型描述可用的字段
 *
 * 用途：生成合成輸入時傳給後端 API
 * @returns 字段標籤的字符串數組
 */
export function getDynamicFieldLabels(): string[] {
  return buildDynamicSections().flatMap((section) =>
    section.fields.flatMap((field) => field.subFields.map((sub) => sub.label))
  );
}

/**
 * 根據標籤查找複合鍵
 * 反向查詢函數，從可讀的標籤獲取存儲用的複合鍵
 *
 * 用途：
 * 1. 處理 AI 生成的內容時，將 AI 返回的標籤映射回複合鍵
 * 2. 處理 Excel 導入時的字段匹配
 *
 * @param label - 字段的完整標籤（如 "1.技術或服務的核心問題是甚麼? - 回覆"）
 * @returns 對應的複合鍵字符串，或 undefined 如果未找到
 */
export function getCompositeKeyFromLabel(label: string): string | undefined {
  const sections = buildDynamicSections();
  for (const section of sections) {
    for (const field of section.fields) {
      for (const sub of field.subFields) {
        if (sub.label === label) {
          return sub.compositeKey;
        }
      }
    }
  }
  return undefined;
}

export { schemaSections as STATIC_DYNAMIC_SCHEMA };
