import mammoth from "mammoth";

/**
 * 從 Word 檔案中提取文本
 */
export async function extractTextFromWord(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer });
  return result.value;
}

/**
 * 調用後端自動填充 API
 */
export async function callAutoFillApi(
  payload: {
    document_text: string;
    sections: Array<{
      section_id: string;
      section_name: string;
      json_schema: Record<string, any>;
    }>;
    user_id: string;
  },
  apiBaseUrl: string
): Promise<Record<string, any>> {
  // 在 sections 之前添加 main_idea 對象
  const mainIdea = {
    section_id: "main_idea",
    section_name: "Main Idea",
    json_schema: {
      type: "object",
      properties: {
        project_name_and_summary: {
          type: "string",
          description: "項目名稱和總結摘要",
        },
      },
      required: ["project_name_and_summary"],
    },
  };

  const updatedSections = [mainIdea, ...payload.sections];
  const updatedPayload = {
    ...payload,
    sections: updatedSections,
    prompt_mode: "word_import",
  };
  const response = await fetch(`${apiBaseUrl}/autofill_from_document`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updatedPayload),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "後端處理失敗");
  }
  return await response.json();
}

/**
 * 為動態章節構建 JSON Schema
 */
export function buildSectionSchema(section: {
  fields: Array<{
    propertyKey: string;
  }>;
}): Record<string, any> {
  const schema: {
    type: string;
    properties: { [key: string]: any };
    required: string[];
  } = {
    type: "object",
    properties: {},
    required: [],
  };

  section.fields.forEach((field) => {
    schema.properties[field.propertyKey] = {
      type: "string",
      description: field.propertyKey,
    };
    schema.required.push(field.propertyKey);
  });

  return schema;
}

/**
 * 處理後端回傳的自動填充結果
 * @param filledContent - 後端回傳的填充內容
 * @param dynamicSections - 動態章節
 * @param updateDynamicValue - 更新動態值的函數
 * @param ensureFieldExpanded - 確保欄位展開的函數
 */
export function processAutoFillResults(
  filledContent: Record<string, any>,
  dynamicSections: Array<{
    sectionId: string;
    fields: Array<{
      propertyKey: string;
    }>;
  }>,
  updateDynamicValue: (
    sectionId: string,
    propertyKey: string,
    value: string
  ) => void,
  ensureFieldExpanded: (sectionId: string, propertyKey: string) => void
): void {
  if (!filledContent || typeof filledContent !== "object") {
    throw new Error("無效的後端回應格式");
  }

  // 遍歷每個章節的填充結果
  dynamicSections.forEach((section) => {
    const sectionContent = filledContent[section.sectionId];
    if (!sectionContent || typeof sectionContent !== "object") {
      return;
    }

    // 遍歷每個欄位並填入值
    section.fields.forEach((field) => {
      const rawFieldContent = sectionContent.content[field.propertyKey];
      if (rawFieldContent === undefined || rawFieldContent === null) {
        return;
      }

      let value: string | null = null;
      if (typeof rawFieldContent === "string") {
        value = rawFieldContent;
      } else if (
        typeof rawFieldContent === "object" &&
        rawFieldContent !== null
      ) {
        if (typeof rawFieldContent.reply === "string") {
          value = rawFieldContent.reply;
        } else {
          const firstStringEntry = Object.values(rawFieldContent).find(
            (entry) => typeof entry === "string" && entry.trim() !== ""
          );
          if (typeof firstStringEntry === "string") {
            value = firstStringEntry;
          }
        }
      }

      if (value && value.trim() !== "") {
        updateDynamicValue(section.sectionId, field.propertyKey, value.trim());
        ensureFieldExpanded(section.sectionId, field.propertyKey);
      }
    });
  });
}
