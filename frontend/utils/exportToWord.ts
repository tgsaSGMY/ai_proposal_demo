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
  WordCustomTableCell,
  WordCustomTableCellContent,
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

const PARAGRAPH_SUB_HEADING_MAX_LEVEL = 3;

function resolveParagraphEffectiveLevel(node: WordDocumentNode): number {
  if (node.paragraphNumberStyle) {
    return getImplicitLevelFromStyle(node.paragraphNumberStyle);
  }
  return node.level ?? 3;
}

function shouldUseParagraphSubHeadingStyle(node: WordDocumentNode): boolean {
  return (
    node.type === "paragraph" &&
    node.paragraphNumbering === true &&
    resolveParagraphEffectiveLevel(node) <= PARAGRAPH_SUB_HEADING_MAX_LEVEL
  );
}

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

/**
 * 根據列表樣式決定有效層級
 * 這樣可以確保相同樣式的列表共享同一個計數器
 */
function getImplicitLevelFromStyle(style: WordListStyle | undefined): number {
  switch (style) {
    case "chineseNumber": // 一、二、三、
    case "chineseComma":
      return 2; // 強制視為第二層
    case "arabicNumber": // 1. 2. 3.
    case "numberedDot":
      return 3; // 強制視為第三層
    case "parenNumbered": // (1) (2) (3)
      return 4; // 強制視為第四層
    default:
      return 3; // 預設值
  }
}

function formatHeadingPrefix(
  level: number | undefined,
  state: HeadingCounterState,
  style?: WordListStyle,
): string {
  // 1. 決定「有效層級 (Effective Level)」
  // 如果有傳入樣式，優先使用樣式對應的層級來計數 (例如選了「一、二、」就強制用 Level 2 計數器)
  // 如果沒有樣式，才退回使用節點原本的 level
  const rawLevel = level || 2;
  const effectiveLevel = style ? getImplicitLevelFromStyle(style) : rawLevel;

  // 2. 針對「有效層級」進行計數 (關鍵修正：這裡不再使用 rawLevel)
  state[effectiveLevel] = (state[effectiveLevel] ?? 0) + 1;

  // 3. 重置所有比「有效層級」更深的計數器
  // 例如：現在數到「五、」(Level 2)，底下的 (1) (Level 4) 必須歸零
  Object.keys(state).forEach((key) => {
    const keyNum = Number(key);
    if (keyNum > effectiveLevel) {
      delete state[keyNum];
    }
  });

  const count = state[effectiveLevel];

  // 4. 根據樣式或層級回傳格式化字串
  if (style) {
    switch (style) {
      case "chineseNumber":
      case "chineseComma":
        return `${formatChineseNumeral(count)}、`;
      case "arabicNumber":
      case "numberedDot":
        return `${count}. `;
      case "parenNumbered":
        return `（${count}）`;
      case "bullet":
        return "";
      default:
        break;
    }
  }

  // Fallback: 如果沒有指定樣式，依據層級給預設格式
  switch (effectiveLevel) {
    case 2:
      return `${formatChineseNumeral(count)}、`;
    case 3:
      return `${count}. `;
    case 4:
      return `（${count}）`;
    default:
      return `${count}. `;
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
  if (!path || obj == null) return obj;
  const parts = path.split(".").filter((segment) => segment.length > 0);

  const traverse = (current: any, remaining: string[]): any => {
    if (!remaining.length) {
      return current;
    }

    if (Array.isArray(current)) {
      const aggregated: any[] = [];
      current.forEach((item) => {
        const value = traverse(item, remaining);
        if (Array.isArray(value)) {
          aggregated.push(...value);
        } else if (value !== undefined && value !== null) {
          aggregated.push(value);
        }
      });
      return aggregated.length ? aggregated : null;
    }

    if (!current || typeof current !== "object") {
      return null;
    }

    const [segment, ...rest] = remaining;
    if (segment === undefined || !(segment in current)) {
      return null;
    }
    return traverse(current[segment], rest);
  };

  return traverse(obj, parts);
}

function resolveScopedPath(
  basePath?: string,
  relativePath?: string,
): string | undefined {
  if (!relativePath || !relativePath.trim()) {
    return basePath;
  }
  if (!basePath || !basePath.trim()) {
    return relativePath;
  }
  const trimmedRelative = relativePath.trim();
  const basePrefix = `${basePath}.`;
  if (trimmedRelative.startsWith(basePrefix)) {
    return trimmedRelative;
  }
  return `${basePath}.${trimmedRelative}`;
}

function ensureExportCellContents(
  cell: WordCustomTableCell,
): WordCustomTableCellContent[] {
  if (Array.isArray(cell.contents) && cell.contents.length > 0) {
    cell.contents = cell.contents.map((content, index) => ({
      id: content.id || `${cell.id || "cell"}-content-${index}`,
      type: content.type ?? "text",
      text: content.type === "text" ? (content.text ?? "") : undefined,
      dataPath: content.type === "field" ? (content.dataPath ?? "") : undefined,
    }));
    return cell.contents;
  }

  const fallbackType = cell.type ?? "text";
  const fallbackContent: WordCustomTableCellContent = {
    id: `${cell.id || "cell"}-content-0`,
    type: fallbackType,
    text: fallbackType === "text" ? (cell.text ?? "") : undefined,
    dataPath: fallbackType === "field" ? (cell.dataPath ?? "") : undefined,
  };
  cell.contents = [fallbackContent];
  return cell.contents;
}

function formatCustomTableCellContent(
  content: WordCustomTableCellContent,
  sectionData: Record<string, any> | null,
  basePath?: string,
): string {
  if (content.type === "text") {
    return content.text ?? "";
  }
  if (!sectionData || !content.dataPath) {
    return "";
  }
  const scopedPath = resolveScopedPath(basePath, content.dataPath);
  if (!scopedPath) {
    return "";
  }
  const value = getValueByPath(sectionData, scopedPath);
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (item === null || item === undefined) return "";
        if (typeof item === "object") {
          try {
            return JSON.stringify(item);
          } catch (error) {
            console.warn("Failed to stringify array item", error);
            return String(item);
          }
        }
        return String(item);
      })
      .filter((text) => text.length > 0)
      .join(", ");
  }
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch (error) {
      console.warn("Failed to stringify cell value", error);
      return String(value);
    }
  }
  return String(value);
}

function formatCustomTableCellValue(
  cell: WordCustomTableCell,
  sectionData: Record<string, any> | null,
  basePath?: string,
): string {
  if (!cell) return "";
  const contents = ensureExportCellContents(cell);
  return contents
    .map((content) =>
      formatCustomTableCellContent(content, sectionData, basePath),
    )
    .join("");
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
 * 根据文本中的干线符渲染一行，处理图片占位符高亮
 * 仿照 local_standard.ts 中 renderTextWithHighlightedImages 的逻辑
 */
function renderTextWithHighlightedImages(
  text: string,
  elements: Array<Paragraph | Table>,
  size: number,
  font: string,
  bold: boolean,
  alignment: (typeof AlignmentType)[keyof typeof AlignmentType],
): void {
  if (!text) return;

  const imagePattern = /【圖[:：][^】]+】/g;
  const parts: Array<{ text: string; isImage: boolean }> = [];
  let lastIndex = 0;
  let match;

  imagePattern.lastIndex = 0;

  while ((match = imagePattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({
        text: text.substring(lastIndex, match.index),
        isImage: false,
      });
    }
    parts.push({ text: match[0], isImage: true });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push({ text: text.substring(lastIndex), isImage: false });
  }

  if (parts.length === 0 || parts.every((p) => !p.isImage)) {
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: text,
            size: size,
            font: font,
            bold: bold,
          }),
        ],
        spacing: { after: 60 },
        alignment: alignment,
      }),
    );
    return;
  }

  const textRuns: TextRun[] = parts.map(
    (part) =>
      new TextRun({
        text: part.text,
        size: size,
        font: font,
        bold: bold,
        highlight: part.isImage ? "yellow" : undefined,
      }),
  );

  elements.push(
    new Paragraph({
      children: textRuns,
      spacing: { after: 60 },
      alignment: alignment,
    }),
  );
}

/**
 * 根据文本中的换行符创建多个 Paragraph 元素
 * 仿照 marketing_imdp.ts 中 renderTextWithLineBreaks 的逻辑
 * 保留空行和多行文本的格式
 */
function renderTextWithLineBreaksToParagraphs(
  text: string,
  elements: Array<Paragraph | Table>,
  size: number,
  font: string,
  bold: boolean,
  alignment: (typeof AlignmentType)[keyof typeof AlignmentType],
): void {
  if (!text) return;

  // 规范化：将多个连续换行符替换为双换行符
  const normalized = text.replace(/\n{2,}/g, "\n\n");
  const segments = normalized.split("\n\n");

  segments.forEach((segment) => {
    if (!segment.trim()) return;

    const lines = segment.split("\n");
    lines.forEach((line) => {
      const trimmed = line.trim();
      if (trimmed) {
        renderTextWithHighlightedImages(
          trimmed,
          elements,
          size,
          font,
          bold,
          alignment,
        );
      }
    });
  });
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
    const showNumbering = node.list?.numbering !== false;
    const prefix = showNumbering
      ? formatHeadingPrefix(node.level, headingCounters, node.list?.style)
      : "";
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
      : node.label || "";
    const textValue = String(value ?? "");
    const numberingEnabled = node.paragraphNumbering === true;
    let finalText = textValue;
    if (numberingEnabled) {
      const numberingStyle = node.paragraphNumberStyle || "arabicNumber";
      const prefix = formatHeadingPrefix(
        node.level ?? 3,
        headingCounters,
        numberingStyle,
      );
      finalText = `${prefix}${textValue}`;
    }

    if (finalText) {
      const useSubHeadingTypography = shouldUseParagraphSubHeadingStyle(node);
      const paragraphSize = useSubHeadingTypography
        ? (resolvedStyle.subHeadingSizePt ?? 14) * 2
        : bodySize;
      const paragraphFont = useSubHeadingTypography
        ? resolvedStyle.subHeadingFont
        : resolvedStyle.bodyFont;
      const paragraphBold = useSubHeadingTypography
        ? resolvedStyle.subHeadingBold
        : (node.style?.bodyBold ?? resolvedStyle.bodyBold);
      renderTextWithLineBreaksToParagraphs(
        finalText,
        elements,
        paragraphSize,
        paragraphFont,
        paragraphBold,
        node.style?.alignment
          ? getAlignmentType(node.style.alignment)
          : AlignmentType.LEFT,
      );
    }
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

      let dataRows =
        rows.length === 0
          ? [
              new TableRow({
                children: columns.map(
                  () =>
                    new TableCell({
                      children: [
                        new Paragraph({
                          children: [
                            new TextRun({
                              text: "無",
                              size: bodySize,
                              font: resolvedStyle.bodyFont,
                            }),
                          ],
                        }),
                      ],
                    }),
                ),
              }),
            ]
          : rows.map(
              (row) =>
                new TableRow({
                  children: columns.map((col) => {
                    const cellValue = String(
                      typeof row === "object" && row !== null
                        ? (getValueByPath(row, col.key) ?? "")
                        : (row ?? ""),
                    );

                    // 使用 line break helper 處理單元格內容
                    const cellElements: Array<Paragraph | Table> = [];
                    renderTextWithLineBreaksToParagraphs(
                      cellValue,
                      cellElements,
                      bodySize,
                      resolvedStyle.bodyFont,
                      false,
                      AlignmentType.LEFT,
                    );

                    return new TableCell({
                      children:
                        cellElements.length > 0
                          ? (cellElements.filter(
                              (e) => e instanceof Paragraph,
                            ) as Paragraph[])
                          : [
                              new Paragraph({
                                children: [
                                  new TextRun({
                                    text: cellValue,
                                    size: bodySize,
                                    font: resolvedStyle.bodyFont,
                                  }),
                                ],
                              }),
                            ],
                    });
                  }),
                }),
            );

      elements.push(
        new Table({
          rows: [new TableRow({ children: headerCells }), ...dataRows],
          width: { size: 100, type: "pct" },
        }),
      );
    }
  } else if (node.type === "customTable") {
    const customTable = node.customTable;
    const sectionData = node.sectionId
      ? (sectionDataMap[node.sectionId] ?? null)
      : null;
    const rows = Math.max(0, customTable?.rows ?? 0);
    const cols = Math.max(0, customTable?.cols ?? 0);

    if (!customTable || !rows || !cols) {
      elements.push(
        new Paragraph({
          children: [
            new TextRun({
              text: node.label?.length
                ? `${node.label}（自訂表格尚未設定）`
                : "自訂表格尚未設定",
              italics: true,
              color: "999999",
              size: bodySize,
              font: resolvedStyle.bodyFont,
            }),
          ],
          spacing: { after: 80 },
        }),
      );
    } else {
      const cellMap = new Map<string, WordCustomTableCell>();
      for (const cell of customTable.cells ?? []) {
        if (!cell) continue;
        cellMap.set(`${cell.row}-${cell.col}`, cell);
      }

      const docxRows: TableRow[] = [];
      for (let rowIndex = 0; rowIndex < rows; rowIndex++) {
        const docxCells: TableCell[] = [];
        for (let colIndex = 0; colIndex < cols; colIndex++) {
          const cellKey = `${rowIndex}-${colIndex}`;
          const configCell = cellMap.get(cellKey);
          const displayValue = configCell
            ? formatCustomTableCellValue(configCell, sectionData, node.dataPath)
            : "";

          // 使用 line break helper 處理單元格內容
          const cellElements: Array<Paragraph | Table> = [];
          renderTextWithLineBreaksToParagraphs(
            displayValue,
            cellElements,
            bodySize,
            resolvedStyle.bodyFont,
            false,
            AlignmentType.LEFT,
          );

          docxCells.push(
            new TableCell({
              children:
                cellElements.length > 0
                  ? (cellElements.filter(
                      (e) => e instanceof Paragraph,
                    ) as Paragraph[])
                  : [
                      new Paragraph({
                        children: [
                          new TextRun({
                            text: displayValue,
                            size: bodySize,
                            font: resolvedStyle.bodyFont,
                          }),
                        ],
                      }),
                    ],
            }),
          );
        }
        docxRows.push(new TableRow({ children: docxCells }));
      }

      elements.push(
        new Table({
          rows: docxRows,
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

    // 依據清單設定決定是否使用有序列表（預設啟用）
    const isNumbered = node.list?.numbering !== false;

    // 如果有嵌套列表（children中有list类型），先处理它们
    if (
      node.children?.length &&
      node.children.some((child) => child?.type === "list")
    ) {
      // 嵌套列表模式：递归处理嵌套列表
      for (const childNode of node.children) {
        if (!childNode) continue;
        const childElements = buildParagraphFromNode(
          childNode,
          sectionDataMap,
          {
            documentStyle: resolvedStyle,
            headingCounters,
          },
        );
        elements.push(...childElements);
      }
    } else if (
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
          : "";

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
            const prefixText =
              childIndex === 0 ? (bullet ? `${bullet} ` : "") : "";
            const isLastChild = childIndex === node.children!.length - 1;
            const isLastItem = i === items.length - 1;
            const childBold =
              adjustedChildNode.style?.bodyBold ?? resolvedStyle.bodyBold;

            elements.push(
              new Paragraph({
                children: [
                  new TextRun({
                    text: prefixText + displayValue,
                    size: bodySize,
                    font: resolvedStyle.bodyFont,
                    bold: childBold,
                  }),
                ],
                spacing: { after: isLastChild && isLastItem ? 120 : 40 },
                indent: { left: 0 },
              }),
            );
          } else {
            // 其他類型的子節點，遞歸構建
            // 如果是 subHeading，使用列表樣式決定層級
            let childElements: Array<Paragraph | Table> = [];

            if (adjustedChildNode.type === "subHeading" && node.list?.style) {
              // 特殊處理：list 中的 subHeading，根據列表樣式決定編號層級
              const showNumbering = node.list?.numbering !== false;
              const styleLevel = getImplicitLevelFromStyle(node.list.style);
              const prefix = showNumbering
                ? formatHeadingPrefix(
                    styleLevel,
                    headingCounters,
                    node.list.style,
                  )
                : "";

              childElements.push(
                new Paragraph({
                  children: [
                    new TextRun({
                      text: `${prefix}${adjustedChildNode.label || "次標題"}`,
                      bold: resolvedStyle.subHeadingBold,
                      size: subHeadingSize,
                      font: resolvedStyle.subHeadingFont,
                    }),
                  ],
                  spacing: { before: 120, after: 80 },
                }),
              );

              // 遞歸處理該 subHeading 的子節點（如果有）
              if (adjustedChildNode.children?.length) {
                for (const subChild of adjustedChildNode.children) {
                  const subElements = buildParagraphFromNode(
                    subChild,
                    itemDataMap,
                    {
                      documentStyle: resolvedStyle,
                      headingCounters,
                    },
                  );
                  childElements.push(...subElements);
                }
              }
            } else {
              childElements = buildParagraphFromNode(
                adjustedChildNode,
                itemDataMap,
                { documentStyle: resolvedStyle, headingCounters },
              );
            }

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
          : "";

        const displayText = bullet ? `${bullet} ${displayValue}` : displayValue;

        elements.push(
          new Paragraph({
            children: [
              new TextRun({
                text: displayText,
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
    const textValue = node.template || "";
    if (textValue) {
      renderTextWithLineBreaksToParagraphs(
        textValue,
        elements,
        bodySize,
        resolvedStyle.bodyFont,
        node.style?.bodyBold ?? resolvedStyle.bodyBold,
        AlignmentType.LEFT,
      );
    }
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

  // 处理剩余的children（list类型已在上面处理过）
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
