// frontend/utils/exportToWord.ts

import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
} from "docx";
import type { ContentRenderer } from "./contentRenderer";
import { DocxRenderer, HtmlRenderer } from "./contentRenderer";

// --- 輔助函數：將 schema 的 key 轉換為更易讀的標題 ---
function keyToTitle(key: string): string {
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

const nameSwitchMap: Record<string, string> = {
  風險的因應對策: "因應",
};

function nameSwitching(key: string): string {
  return nameSwitchMap[key] ?? key; // 如果找不到對應，就回傳原本的 key
}

// --- 核心：遞歸渲染內容的函數 ---
function renderSectionContent(
  data: any,
  schema: any, // 傳入對應的 schema
  renderer: ContentRenderer<any> // 接收任何一種渲染器
) {
  if (!data || typeof data !== "object") {
    if (data) renderer.addParagraph(String(data));
    return;
  }

  const schemaProperties = schema?.properties || {};

  for (const key in schemaProperties) {
    if (Object.prototype.hasOwnProperty.call(data, key)) {
      const value = data[key];
      const propInfo = schemaProperties[key];
      const title = propInfo.title || "" || keyToTitle(key);

      if (value === null || value === "") continue;

      if (Array.isArray(value)) {
        if (value.length > 0) {
          renderer.addArrayTitle(title);

          // 檢查是否所有項都是物件（array of objects）
          const allObjectItems = value.every(
            (item) => typeof item === "object" && item !== null
          );

          if (allObjectItems && value.length > 0) {
            // 如果是 array of objects，直接传递 JSON 字符串给渲染器
            renderer.addKeyValue(title, JSON.stringify(value));
          } else {
            // 原有的逐项处理逻辑
            value.forEach((item, index) => {
              const numberingIndex = index + 1;
              if (typeof item === "object" && item !== null) {
                const itemSchema = propInfo.items?.properties;
                const usedKeys = new Set<string>();

                // 優先處理 title/description 成對情況
                const titleKey = Object.keys(item).find((k) =>
                  k.includes("title")
                );
                const descKey = Object.keys(item).find(
                  (k) => k.includes("description") || k.includes("explanation")
                );

                if (titleKey && descKey && item[titleKey] && item[descKey]) {
                  renderer.addNumberedListItem(numberingIndex, {
                    title: String(item[titleKey]),
                    description: String(item[descKey]),
                  });
                  usedKeys.add(titleKey).add(descKey);
                }

                // 處理剩餘字段
                for (const itemKey in itemSchema) {
                  if (
                    usedKeys.has(itemKey) ||
                    !Object.prototype.hasOwnProperty.call(item, itemKey)
                  )
                    continue;

                  const fieldValue = String(item[itemKey] ?? "").trim();
                  if (!fieldValue) continue;

                  const itemPropInfo = itemSchema[itemKey];
                  const itemTitle = nameSwitching(
                    itemPropInfo.title ||
                      itemPropInfo.description ||
                      keyToTitle(itemKey)
                  );

                  // 如果是第一個被渲染的項目，且不是成對的項目，則加上編號
                  if (usedKeys.size === 0) {
                    renderer.addNumberedListItem(numberingIndex, fieldValue);
                  } else {
                    renderer.addIndentedListItem(itemTitle, fieldValue);
                  }
                  usedKeys.add(itemKey);
                }
              } else {
                renderer.addNumberedListItem(
                  numberingIndex,
                  String(item ?? "")
                );
              }
            });
          }
        }
      } else if (typeof value === "object" && value !== null) {
        // 遞歸處理嵌套對象
        renderer.addArrayTitle(title);
        renderSectionContent(value, propInfo, renderer);
      } else {
        // 處理簡單的鍵值對或段落
        if (
          key.toLowerCase().includes("paragraph") ||
          key.toLowerCase().includes("description")
        ) {
          renderer.addParagraph(String(value));
        } else {
          renderer.addKeyValue(title, String(value));
        }
      }
    }
  }
}

type ExportableSection = { id: string; name: string; json_schema?: any };

export async function exportPlanToWord(
  sections: ExportableSection[],
  planContent: Record<string, any>,
  grantId?: string,
  templateId?: string
) {
  // 根據 grant 和 template 分發到對應的 grant template 函數
  const grantTemplateKey = `${grantId}_${templateId}`;

  // 動態導入對應的 grant template 函數
  try {
    let exportFn: any;

    // 根據 grantId 和 templateId 映射到對應的導出函數
    switch (grantTemplateKey) {
      case "central_phase1":
        const { exportPlanToWordCentralPhase1 } = await import(
          "./wordStyle/central_phase1"
        );
        exportFn = exportPlanToWordCentralPhase1;
        break;
      case "central_phase2":
        const { exportPlanToWordCentralPhase2 } = await import(
          "./wordStyle/central_phase2"
        );
        exportFn = exportPlanToWordCentralPhase2;
        break;
      case "local_standard":
        const { exportPlanToWordLocalStandard } = await import(
          "./wordStyle/local_standard"
        );
        exportFn = exportPlanToWordLocalStandard;
        break;
      case "marketing_imdp":
        const { exportPlanToWordMarketingImdp } = await import(
          "./wordStyle/marketing_imdp"
        );
        exportFn = exportPlanToWordMarketingImdp;
        break;
      case "marketing_siir":
        const { exportPlanToWordMarketingSiir } = await import(
          "./wordStyle/marketing_siir"
        );
        exportFn = exportPlanToWordMarketingSiir;
        break;
      case "r&d_standard":
        const { exportPlanToWordRdStandard } = await import(
          "./wordStyle/r&d_standard"
        );
        exportFn = exportPlanToWordRdStandard;
        break;
      case "r&d_transform_over_10":
        const { exportPlanToWordRdTransformOver10 } = await import(
          "./wordStyle/r&d_transform_over_10"
        );
        exportFn = exportPlanToWordRdTransformOver10;
        break;
      case "r&d_transform_under_9":
        const { exportPlanToWordRdTransformUnder9 } = await import(
          "./wordStyle/r&d_transform_under9"
        );
        exportFn = exportPlanToWordRdTransformUnder9;
        break;
      default:
        // 默認使用 exportPlanToWordDefault
        exportFn = exportPlanToWordDefault;
    }

    return await exportFn(sections, planContent);
  } catch (error) {
    console.error(
      `Failed to export using template ${grantTemplateKey}:`,
      error
    );
    // 降級到默認導出
    return exportPlanToWordDefault(sections, planContent);
  }
}

// 默認導出函數（保留原有邏輯）
async function exportPlanToWordDefault(
  sections: ExportableSection[],
  planContent: Record<string, any>
) {
  const docxRenderer = new DocxRenderer();

  for (const section of sections) {
    const sectionData = planContent[section.id]?.content;

    docxRenderer.addSectionTitle(section.name);

    if (!sectionData) {
      docxRenderer.addEmptyContentMessage();
      continue;
    }

    renderSectionContent(sectionData, section.json_schema, docxRenderer);
  }

  const paragraphs = docxRenderer.getResult();
  // === 定義文件樣式 ===
  const doc = new Document({
    styles: {
      paragraphStyles: [
        {
          id: "SectionHeading",
          name: "Section Heading",
          basedOn: "Heading2",
          next: "NormalText",
          quickFormat: true,
          run: {
            font: "MS Gothic",
            size: 26, // 13pt
            bold: true,
          },
          paragraph: {
            spacing: { after: 200 },
          },
        },
        {
          id: "SubSectionHeading",
          name: "Subsection Heading",
          basedOn: "Heading3",
          next: "NormalText",
          quickFormat: true,
          run: {
            font: "MS Gothic",
            size: 22, // 11pt
            bold: true,
          },
          paragraph: {
            spacing: { after: 100 },
          },
        },
        {
          id: "NormalText",
          name: "Normal Text",
          basedOn: "Normal",
          quickFormat: true,
          run: {
            font: "MS Mincho",
            size: 22, // 11pt
          },
          paragraph: {
            spacing: { line: 276 }, // 約 1.15 倍行距
          },
        },
      ],
    },

    numbering: {
      config: [
        {
          reference: "my-numbering-style",
          levels: [
            {
              level: 0,
              format: "decimal",
              text: "%1.",
              alignment: AlignmentType.LEFT,
            },
          ],
        },
      ],
    },

    sections: [
      {
        children: paragraphs,
      },
    ],
  });

  const blob = await Packer.toBlob(doc);

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "計劃書草稿.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function renderPlanToHtml(
  sections: ExportableSection[],
  planContent: Record<string, any>
): string {
  const htmlRenderer = new HtmlRenderer();

  for (const section of sections) {
    const sectionData = planContent[section.id]?.content;

    htmlRenderer.addSectionTitle(section.name);

    if (!sectionData) {
      htmlRenderer.addEmptyContentMessage();
      continue;
    }

    renderSectionContent(sectionData, section.json_schema, htmlRenderer);
  }

  return htmlRenderer.getResult();
}
