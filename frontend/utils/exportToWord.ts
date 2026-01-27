// frontend/utils/exportToWord.ts

import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  AlignmentType,
  Table,
  TableRow,
  TableCell,
  convertInchesToTwip,
} from "docx";
import { useRuntimeConfig } from "#imports";
import type { ContentRenderer } from "./contentRenderer";
import { DocxRenderer, HtmlRenderer } from "./contentRenderer";
import type {
  WordDocumentNode,
  WordDocumentStyle,
  WordExportTemplateConfig,
  WordListStyle,
} from "~/types/wordExport";

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
  renderer: ContentRenderer<any>, // 接收任何一種渲染器
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
            (item) => typeof item === "object" && item !== null,
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
                  k.includes("title"),
                );
                const descKey = Object.keys(item).find(
                  (k) => k.includes("description") || k.includes("explanation"),
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
                      keyToTitle(itemKey),
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
                  String(item ?? ""),
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

type HeadingCounterState = Record<number, number>;

const DEFAULT_DOCUMENT_STYLE: Required<WordDocumentStyle> = {
  headingFont: "Times New Roman",
  headingSizePt: 18,
  headingBold: true,
  subHeadingFont: "Times New Roman",
  subHeadingSizePt: 14,
  subHeadingBold: true,
  bodyFont: "Times New Roman",
  bodySizePt: 12,
  bodyBold: false,
};

function resolveDocumentStyle(style?: WordDocumentStyle) {
  return {
    ...DEFAULT_DOCUMENT_STYLE,
    ...(style || {}),
  } as Required<WordDocumentStyle>;
}

function createHeadingCounterState(): HeadingCounterState {
  return {};
}

function resetHeadingCounters(state: HeadingCounterState) {
  Object.keys(state).forEach((key) => delete state[Number(key)]);
}

function formatChineseNumeral(value: number): string {
  if (value <= 0) return "";
  const digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"];
  if (value <= 10) {
    return value === 10 ? "十" : digits[value] || "";
  }
  if (value < 20) {
    return `十${digits[value - 10]}`;
  }
  if (value < 100) {
    const tens = Math.floor(value / 10);
    const units = value % 10;
    let result = `${digits[tens]}十`;
    if (units !== 0) {
      result += digits[units];
    }
    return result;
  }
  return String(value);
}

function formatHeadingPrefix(
  level: number | undefined,
  state: HeadingCounterState,
): string {
  if (!level) return "";
  state[level] = (state[level] ?? 0) + 1;
  Object.keys(state).forEach((key) => {
    const currentLevel = Number(key);
    if (currentLevel > level) {
      delete state[currentLevel];
    }
  });

  const count = state[level];
  switch (level) {
    case 2:
      return `${formatChineseNumeral(count)}、`;
    case 3:
      return `${count}. `;
    case 4:
      return `（${count}）`;
    default:
      return "";
  }
}

function getListBulletLabel(
  style: WordListStyle | undefined,
  index: number,
): string {
  switch (style) {
    case "chineseNumber":
    case "chineseComma":
      return `${formatChineseNumeral(index + 1)}、`;
    case "arabicNumber":
    case "numberedDot":
      return `${index + 1}.`;
    case "parenNumbered":
      return `（${index + 1}）`;
    default:
      return "•";
  }
}

function getAlignmentType(
  alignment?: string,
): (typeof AlignmentType)[keyof typeof AlignmentType] {
  switch (alignment) {
    case "center":
      return AlignmentType.CENTER;
    case "right":
      return AlignmentType.RIGHT;
    case "left":
    default:
      return AlignmentType.LEFT;
  }
}

function getValueByPath(
  obj: Record<string, any> | null | undefined,
  path?: string,
): any {
  if (!path || !obj) return obj;
  const parts = path.split(".");
  let current: any = obj;
  for (const part of parts) {
    if (current && typeof current === "object") {
      current = current[part];
    } else {
      return null;
    }
  }
  return current;
}

/**
 * 从 backend 获取 plan template 的 word export config
 */
async function fetchWordExportConfig(
  grantId?: string,
  templateId?: string,
): Promise<WordExportTemplateConfig | null> {
  if (!grantId || !templateId) return null;

  try {
    const config = useRuntimeConfig();
    const baseUrl = config.public?.apiBaseUrl || "";
    const normalizedBase = baseUrl.endsWith("/")
      ? baseUrl.slice(0, -1)
      : baseUrl;
    const endpoint = `/api/template-manager/templates/${grantId}/${templateId}`;
    const requestUrl = normalizedBase
      ? `${normalizedBase}${endpoint}`
      : endpoint;

    const response = await fetch(requestUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    });

    if (!response.ok) {
      if (response.status === 404) {
        console.log(`Word export config not found for template ${templateId}`);
      } else {
        console.warn(
          `Failed to fetch word export config (${response.status}) from ${requestUrl}`,
        );
      }
      return null;
    }

    const data = await response.json();

    if (!data) {
      console.log(`Template ${templateId} not found`);
      return null;
    }

    // 获取最新的 word export config 版本
    const configs = data.word_export_config as Array<{
      id: string;
      createdAt: string;
      config: WordExportTemplateConfig;
    }> | null;

    if (!configs || configs.length === 0) {
      console.log("No word export config available for this template");
      return null;
    }

    // 按时间排序，返回最新的配置
    const sorted = [...configs].sort(
      (a, b) =>
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    );

    console.log("Successfully loaded word export config from backend");
    return sorted[0]?.config || null;
  } catch (error: any) {
    console.warn("Error fetching word export config:", error?.message || error);
    return null;
  }
}

/**
 * 创建文档段落/表格的辅助函数（参考 WordEditorForm 的 buildParagraphsFromNode）
 */
function buildParagraphFromNode(
  node: WordDocumentNode,
  sectionDataMap: Record<string, Record<string, any>>,
  options: {
    documentStyle?: WordDocumentStyle;
    headingCounters: HeadingCounterState;
  },
): Array<Paragraph | Table> {
  const elements: Array<Paragraph | Table> = [];
  if (!node) return elements;

  const resolvedStyle = resolveDocumentStyle(options.documentStyle);

  const headingCounters = options.headingCounters;

  const headingSize = resolvedStyle.headingSizePt * 2;
  const subHeadingSize = resolvedStyle.subHeadingSizePt * 2;
  const bodySize = resolvedStyle.bodySizePt * 2;

  if (node.type === "sectionTitle") {
    resetHeadingCounters(headingCounters);
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: node.label || "章節標題",
            bold: resolvedStyle.headingBold,
            size: headingSize,
            font: resolvedStyle.headingFont,
          }),
        ],
        spacing: { before: 200, after: 120 },
      }),
    );
  } else if (node.type === "subHeading") {
    const prefix = formatHeadingPrefix(node.level, headingCounters);
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: `${prefix}${node.label || "次標題"}`,
            bold: resolvedStyle.subHeadingBold,
            size: subHeadingSize,
            font: resolvedStyle.subHeadingFont,
          }),
        ],
        spacing: { before: 120, after: 80 },
      }),
    );
  } else if (node.type === "paragraph") {
    const sectionData = node.sectionId ? sectionDataMap[node.sectionId] : null;
    const value = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : `${node.label || "段落內容"}`;
    const displayValue = node.label
      ? `${node.label}: ${value ?? ""}`
      : String(value ?? "");

    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: displayValue,
            size: bodySize,
            font: resolvedStyle.bodyFont,
            bold: resolvedStyle.bodyBold,
          }),
        ],
        spacing: { after: 60 },
        alignment: node.style?.alignment
          ? getAlignmentType(node.style.alignment)
          : AlignmentType.LEFT,
      }),
    );
  } else if (node.type === "table") {
    const sectionData = node.sectionId ? sectionDataMap[node.sectionId] : null;
    const tableData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const rows = Array.isArray(tableData) ? tableData : [];
    const columns = node.table?.columns || [];

    if (columns.length > 0) {
      const headerCells = columns.map(
        (col) =>
          new TableCell({
            children: [
              new Paragraph({
                children: [
                  new TextRun({
                    text: col.label || col.key,
                    bold: true,
                    size: bodySize,
                    font: resolvedStyle.bodyFont,
                  }),
                ],
              }),
            ],
          }),
      );

      const dataRows = rows.map(
        (row) =>
          new TableRow({
            children: columns.map(
              (col) =>
                new TableCell({
                  children: [
                    new Paragraph({
                      children: [
                        new TextRun({
                          text: String(
                            typeof row === "object" && row !== null
                              ? (getValueByPath(row, col.key) ?? "")
                              : (row ?? ""),
                          ),
                          size: bodySize,
                          font: resolvedStyle.bodyFont,
                        }),
                      ],
                    }),
                  ],
                }),
            ),
          }),
      );

      elements.push(
        new Table({
          rows: [new TableRow({ children: headerCells }), ...dataRows],
          width: { size: 100, type: "pct" },
        }),
      );
    }
  } else if (node.type === "list") {
    const sectionData = node.sectionId ? sectionDataMap[node.sectionId] : null;
    const listData = sectionData
      ? getValueByPath(sectionData, node.dataPath)
      : [];
    const items = Array.isArray(listData) ? listData : [listData];

    // 根據節點層級決定是否使用有序列表
    const isNumbered = node.list?.numbering || (node.level && node.level > 1);

    if (
      node.list?.itemConfig?.useSubNodes &&
      items.length > 0 &&
      typeof items[0] === "object" &&
      items[0] !== null &&
      !Array.isArray(items[0]) &&
      node.children?.length
    ) {
      // 對於每個數據項，將其子節點展開為嵌套列表
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const itemDataMap: Record<string, Record<string, any>> = {};
        if (node.sectionId) {
          itemDataMap[node.sectionId] = item as Record<string, any>;
        }

        // 主項編號
        const bullet = isNumbered
          ? getListBulletLabel(node.list?.style, i)
          : "•";

        // 處理所有子節點
        node.children.forEach((childNode, childIndex) => {
          if (!childNode) return;

          let adjustedChildNode = { ...childNode };
          if (node.dataPath && childNode.dataPath) {
            const parentPathPrefix = node.dataPath + ".";
            if (childNode.dataPath.startsWith(parentPathPrefix)) {
              adjustedChildNode = {
                ...childNode,
                dataPath: childNode.dataPath.substring(parentPathPrefix.length),
              };
            }
          }

          // 如果是 paragraph 類型的子節點
          if (adjustedChildNode.type === "paragraph") {
            const childSectionData = adjustedChildNode.sectionId
              ? itemDataMap[adjustedChildNode.sectionId]
              : null;
            let value: any = null;

            if (childSectionData && adjustedChildNode.dataPath) {
              value = getValueByPath(
                childSectionData,
                adjustedChildNode.dataPath,
              );
            }

            let displayValue: string;
            if (value === null || value === undefined) {
              displayValue = adjustedChildNode.label
                ? `${adjustedChildNode.label} (無資料)`
                : "段落內容 (無資料)";
            } else if (typeof value === "object" && !Array.isArray(value)) {
              displayValue = JSON.stringify(value);
            } else if (Array.isArray(value)) {
              displayValue = value.join(", ");
            } else {
              displayValue = String(value);
            }

            // 如果是第一個子節點，前面加上編號；否則加上 bullet
            const prefixText = childIndex === 0 ? `${bullet} ` : "";
            const isLastChild = childIndex === node.children!.length - 1;
            const isLastItem = i === items.length - 1;

            elements.push(
              new Paragraph({
                children: [
                  new TextRun({
                    text: prefixText + displayValue,
                    size: bodySize,
                    font: resolvedStyle.bodyFont,
                  }),
                ],
                spacing: { after: isLastChild && isLastItem ? 120 : 40 },
                indent: { left: 0 },
              }),
            );
          } else {
            // 其他類型的子節點，遞歸構建
            const childElements = buildParagraphFromNode(
              adjustedChildNode,
              itemDataMap,
              { documentStyle: resolvedStyle, headingCounters },
            );
            childElements.forEach((element, idx) => {
              if (element instanceof Paragraph) {
                (element as any).indent = { left: 0 };
              }
            });
            elements.push(...childElements);
          }
        });
      }
    } else {
      // 簡單列表模式：遍歷每個 item 直接顯示
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const displayValue =
          typeof item === "object" && item !== null
            ? JSON.stringify(item)
            : String(item ?? "");

        const bullet = isNumbered
          ? getListBulletLabel(node.list?.style, i)
          : "•";

        elements.push(
          new Paragraph({
            children: [
              new TextRun({
                text: `${bullet} ${displayValue}`,
                size: bodySize,
                font: resolvedStyle.bodyFont,
              }),
            ],
            spacing: { after: 40 },
            indent: { left: 0 },
          }),
        );
      }
    }
  } else if (node.type === "customText") {
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: node.template || "自訂文字",
            size: bodySize,
            font: resolvedStyle.bodyFont,
          }),
        ],
        spacing: { after: 60 },
      }),
    );
  } else if (node.type === "imagePlaceholder") {
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: node.label || "【圖：請插入圖片】",
            size: bodySize,
            font: resolvedStyle.bodyFont,
            highlight: "yellow",
          }),
        ],
        spacing: { after: 80 },
      }),
    );
  }

  if (node.children && node.children.length > 0 && node.type !== "list") {
    for (const child of node.children) {
      const childElements = buildParagraphFromNode(child, sectionDataMap, {
        documentStyle: resolvedStyle,
        headingCounters,
      });
      elements.push(...childElements);
    }
  }

  return elements;
}

/**
 * 使用 word export config 生成文档
 */
async function exportPlanUsingWordConfig(
  config: WordExportTemplateConfig,
  sections: ExportableSection[],
  planContent: Record<string, any>,
  projectTitle?: string,
): Promise<void> {
  try {
    // 使用实际的 plan content 作为数据源
    const sectionDataMap: Record<string, Record<string, any>> = {};
    for (const section of sections) {
      sectionDataMap[section.id] = planContent[section.id]?.content || {};
    }

    // 构建文档元素
    const documentElements: Array<Paragraph | Table> = [];
    const headingCounters = createHeadingCounterState();

    // 在文档最上面添加标题
    if (projectTitle) {
      documentElements.push(
        new Paragraph({
          children: [
            new TextRun({
              text: projectTitle,
              bold: true,
              size: 36,
            }),
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 240 },
        }),
      );
    }

    if (config.nodes && config.nodes.length > 0) {
      for (const node of config.nodes) {
        const elements = buildParagraphFromNode(node, sectionDataMap, {
          documentStyle: config.documentStyle,
          headingCounters,
        });
        documentElements.push(...elements);
      }
    } else {
      documentElements.push(
        new Paragraph({
          children: [
            new TextRun({
              text: "尚未設定任何節點。",
              color: "999999",
              size: 22,
            }),
          ],
        }),
      );
    }

    // 创建文档
    const doc = new Document({
      sections: [
        {
          properties: {
            page: {
              margin: {
                top: convertInchesToTwip(1),
                right: convertInchesToTwip(1),
                bottom: convertInchesToTwip(1),
                left: convertInchesToTwip(1),
              },
            },
          },
          children: documentElements,
        },
      ],
    });

    // 生成 blob 并下载
    const blob = await Packer.toBlob(doc);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${projectTitle || "文檔"}.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Error exporting with word config:", error);
    throw error;
  }
}

export async function exportPlanToWord(
  sections: ExportableSection[],
  planContent: Record<string, any>,
  grantId?: string,
  templateId?: string,
  projectTitle?: string,
) {
  // 第一優先級：嘗試從 backend 獲取 word export config
  if (grantId && templateId) {
    try {
      const wordConfig = await fetchWordExportConfig(grantId, templateId);
      if (wordConfig) {
        console.log("Using word export config from backend");
        return await exportPlanUsingWordConfig(
          wordConfig,
          sections,
          planContent,
          projectTitle,
        );
      }
    } catch (error) {
      console.warn("Failed to use word export config, falling back:", error);
      // 继续到 fallback 逻辑
    }
  }

  // 第二優先級：使用動態導入的 grant template 函數（原有邏輯）
  const grantTemplateKey = `${grantId}_${templateId}`;

  try {
    let exportFn: any;

    // 根據 grantId 和 templateId 映射到對應的導出函數
    switch (grantTemplateKey) {
      case "central_phase1":
        const { exportPlanToWordCentralPhase1 } =
          await import("./wordStyle/central_phase1");
        exportFn = exportPlanToWordCentralPhase1;
        break;
      case "central_phase2":
        const { exportPlanToWordCentralPhase2 } =
          await import("./wordStyle/central_phase2");
        exportFn = exportPlanToWordCentralPhase2;
        break;
      case "local_standard":
        const { exportPlanToWordLocalStandard } =
          await import("./wordStyle/local_standard");
        exportFn = exportPlanToWordLocalStandard;
        break;
      case "marketing_imdp":
        const { exportPlanToWordMarketingImdp } =
          await import("./wordStyle/marketing_imdp");
        exportFn = exportPlanToWordMarketingImdp;
        break;
      case "marketing_siir":
        const { exportPlanToWordMarketingSiir } =
          await import("./wordStyle/marketing_siir");
        exportFn = exportPlanToWordMarketingSiir;
        break;
      case "r&d_standard":
        const { exportPlanToWordRdStandard } =
          await import("./wordStyle/r&d_standard");
        exportFn = exportPlanToWordRdStandard;
        break;
      case "r&d_transform_over_10":
        const { exportPlanToWordRdTransformOver10 } =
          await import("./wordStyle/r&d_transform_over_10");
        exportFn = exportPlanToWordRdTransformOver10;
        break;
      case "r&d_transform_under_9":
        const { exportPlanToWordRdTransformUnder9 } =
          await import("./wordStyle/r&d_transform_under9");
        exportFn = exportPlanToWordRdTransformUnder9;
        break;
      default:
        // 默認使用 exportPlanToWordDefault
        exportFn = exportPlanToWordDefault;
    }

    return await exportFn(sections, planContent, projectTitle);
  } catch (error) {
    console.error(
      `Failed to export using template ${grantTemplateKey}:`,
      error,
    );
    // 降級到默認導出
    return exportPlanToWordDefault(sections, planContent, projectTitle);
  }
}

// 默認導出函數（保留原有邏輯）
async function exportPlanToWordDefault(
  sections: ExportableSection[],
  planContent: Record<string, any>,
  projectTitle?: string,
) {
  const docxRenderer = new DocxRenderer();

  // 在文檔最上面添加標題
  if (projectTitle) {
    docxRenderer.addSectionTitle(projectTitle);
  }

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
            font: "Times New Roman",
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
            font: "Times New Roman",
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
            font: "Times New Roman",
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
  link.download = projectTitle ? `${projectTitle}.docx` : "計劃書草稿.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function renderPlanToHtml(
  sections: ExportableSection[],
  planContent: Record<string, any>,
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
