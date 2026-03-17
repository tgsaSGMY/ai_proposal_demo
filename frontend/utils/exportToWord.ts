// 這個檔案包含了從後端獲取 Word Export 配置、根據配置渲染內容，以及導出 Word 文件的核心邏輯

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
  WordCustomTableCell,
  WordCustomTableCellContent,
} from "~/types/wordExport";
import {
  createHeadingCounterState,
  formatHeadingPrefix,
  getImplicitLevelFromStyle,
  getListBulletLabel,
  resetHeadingCounters,
  shouldUseParagraphSubHeadingStyle,
  type HeadingCounterState,
} from "~/composables/template-manager/useWordNumbering";

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
      const title = propInfo.title || keyToTitle(key);

      if (value === null || value === "") continue;

      if (Array.isArray(value)) {
        if (value.length > 0) {
          renderer.addArrayTitle(title);

          // 檢查是否所有項都是物件（array of objects）
          const allObjectItems = value.every(
            (item) => typeof item === "object" && item !== null,
          );

          if (allObjectItems) {
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

const DEFAULT_EAST_ASIA_FONT = "Microsoft JhengHei";

function resolveRunFont(font?: string) {
  const normalizedFont =
    (font || "Times New Roman").trim() || "Times New Roman";
  const eastAsiaFont = /^[\x00-\x7F\s]+$/.test(normalizedFont)
    ? DEFAULT_EAST_ASIA_FONT
    : normalizedFont;

  return {
    ascii: normalizedFont,
    hAnsi: normalizedFont,
    cs: normalizedFont,
    eastAsia: eastAsiaFont,
  };
}

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
  const normalize = (value?: string) =>
    value
      ?.split(".")
      .map((segment) => segment.trim())
      .filter(Boolean)
      .join(".") || "";

  const normalizedBase = normalize(basePath);
  const normalizedPath = normalize(relativePath);

  if (!normalizedPath) return normalizedBase || undefined;
  if (!normalizedBase) return normalizedPath;

  const basePrefix = `${normalizedBase}.`;
  if (
    normalizedPath === normalizedBase ||
    normalizedPath.startsWith(basePrefix)
  ) {
    return normalizedPath;
  }

  const marker = `.${basePrefix}`;
  const markerIndex = normalizedPath.indexOf(marker);
  if (markerIndex >= 0) {
    return normalizedPath.slice(markerIndex + 1);
  }

  return `${normalizedBase}.${normalizedPath}`;
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

function parseTimestamp(value?: string | Date | null): number | null {
  if (!value) return null;
  const timestamp = new Date(value).getTime();
  return Number.isNaN(timestamp) ? null : timestamp;
}

function checkVersionsCompatible(
  configVersions?: Record<string, number>,
  projectVersions?: Record<string, number>,
): boolean {
  if (!projectVersions || !configVersions) {
    return true; // 如果其中任一为空，视为兼容
  }

  // 检查 configVersions 中的所有值是否都 <= projectVersions 对应的值
  // 这样旧的项目不会套用新的模板
  for (const sectionId in projectVersions) {
    const projectVersion = projectVersions[sectionId];
    const configVersion = configVersions[sectionId];

    // 如果 config 中缺少该 section，或版本号大于 project，则不兼容
    if (
      configVersion === undefined ||
      projectVersion === undefined ||
      configVersion > projectVersion
    ) {
      return false;
    }
  }

  return true;
}

function selectConfigByVersionAndTime(
  configs: Array<{
    id: string;
    createdAt: string;
    config: WordExportTemplateConfig;
    section_versions?: Record<string, number>;
  }>,
  projectSectionVersions?: Record<string, number>,
  projectCreatedAt?: string | Date,
): WordExportTemplateConfig | null {
  if (!configs.length) {
    return null;
  }

  const sortedByTime = [...configs].sort((a, b) => {
    const aTime = parseTimestamp(a.createdAt) ?? -Infinity;
    const bTime = parseTimestamp(b.createdAt) ?? -Infinity;
    return aTime - bTime;
  });

  // 首先根据 section_versions 筛选兼容的配置
  const versionCompatible = sortedByTime.filter((entry) =>
    checkVersionsCompatible(entry.section_versions, projectSectionVersions),
  );

  if (versionCompatible.length > 0) {
    // 如果有兼容的版本，选择其中最新的
    return versionCompatible[versionCompatible.length - 1]?.config ?? null;
  }

  // Fallback：如果没有版本兼容的配置，使用原来的按时间对比逻辑
  const projectTime = parseTimestamp(projectCreatedAt);

  if (projectTime != null) {
    const timeEligible = sortedByTime.filter((entry) => {
      const entryTime = parseTimestamp(entry.createdAt);
      return entryTime != null && entryTime <= projectTime;
    });

    if (timeEligible.length) {
      return timeEligible[timeEligible.length - 1]?.config ?? null;
    }

    // 沒有早於專案建立時間的版本時，回退到最早的設定
    return sortedByTime[0]?.config ?? null;
  }

  // 若沒有專案建立時間，使用最新的設定
  return sortedByTime[sortedByTime.length - 1]?.config ?? null;
}

/**
 * 从 backend 获取 plan template 的 word export config
 */
async function fetchWordExportConfig(
  grantId?: string,
  templateId?: string,
  projectCreatedAt?: string | Date,
  projectSectionVersions?: Record<string, number>,
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
      section_versions?: Record<string, number>;
    }> | null;

    if (!configs || configs.length === 0) {
      console.log("No word export config available for this template");
      return null;
    }

    const selectedConfig = selectConfigByVersionAndTime(
      configs,
      projectSectionVersions,
      projectCreatedAt,
    );

    if (selectedConfig) {
      console.log("Successfully loaded word export config from backend");
    }
    return selectedConfig;
  } catch (error: any) {
    console.warn("Error fetching word export config:", error?.message || error);
    return null;
  }
}

/**
 * 根据文本中的干线符渲染一行，处理图片占位符高亮和Markdown粗体格式
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
  const boldPattern = /\*\*(.+?)\*\*/g;

  // 收集所有匹配项（图片和粗体）
  const matches: Array<{
    index: number;
    endIndex: number;
    type: "image" | "bold";
    text: string;
  }> = [];

  // 收集图片占位符
  let match;
  while ((match = imagePattern.exec(text)) !== null) {
    matches.push({
      index: match.index,
      endIndex: match.index + match[0].length,
      type: "image",
      text: match[0],
    });
  }

  // 收集粗体格式
  const boldPatternGlobal = /\*\*(.+?)\*\*/g;
  let boldMatch: RegExpExecArray | null;
  while ((boldMatch = boldPatternGlobal.exec(text)) !== null) {
    matches.push({
      index: boldMatch.index,
      endIndex: boldMatch.index + boldMatch[0].length,
      type: "bold",
      text: boldMatch[1] ?? "",
    });
  }

  // 按索引排序
  matches.sort((a, b) => a.index - b.index);

  // 如果没有匹配项，直接创建段落
  if (matches.length === 0) {
    elements.push(
      new Paragraph({
        children: [
          new TextRun({
            text: text,
            size: size,
            font: resolveRunFont(font),
            bold: bold,
          }),
        ],
        spacing: { after: 60 },
        alignment: alignment,
      }),
    );
    return;
  }

  // 构建文本片段
  const textRuns: TextRun[] = [];
  let lastIndex = 0;

  for (const match of matches) {
    // 添加匹配前的普通文本
    if (lastIndex < match.index) {
      textRuns.push(
        new TextRun({
          text: text.substring(lastIndex, match.index),
          size: size,
          font: resolveRunFont(font),
          bold: bold,
        }),
      );
    }

    // 添加匹配的文本（图片或粗体）
    if (match.type === "image") {
      textRuns.push(
        new TextRun({
          text: match.text,
          size: size,
          font: resolveRunFont(font),
          bold: bold,
          highlight: "yellow",
        }),
      );
    } else if (match.type === "bold") {
      textRuns.push(
        new TextRun({
          text: match.text ?? "",
          size: size,
          font: resolveRunFont(font),
          bold: true,
        }),
      );
    }

    lastIndex = match.endIndex;
  }

  // 添加剩余的文本
  if (lastIndex < text.length) {
    textRuns.push(
      new TextRun({
        text: text.substring(lastIndex),
        size: size,
        font: resolveRunFont(font),
        bold: bold,
      }),
    );
  }

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

  // 规范化：统一各种换行符，再将多个连续换行符压缩为双换行
  const normalized = text
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/[\u2028\u2029]/g, "\n")
    .replace(/\n{2,}/g, "\n\n");
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

function insertTableSeparators(
  elements: Array<Paragraph | Table>,
): Array<Paragraph | Table> {
  if (!elements.length) return elements;

  const separated: Array<Paragraph | Table> = [];

  for (const element of elements) {
    const previous = separated[separated.length - 1];
    const isPreviousTable = previous instanceof Table;
    const isCurrentTable = element instanceof Table;

    if (isPreviousTable && isCurrentTable) {
      separated.push(
        new Paragraph({
          children: [new TextRun({ text: "", size: 2 })],
          spacing: { before: 80, after: 80 },
        }),
      );
    }

    separated.push(element);
  }

  return separated;
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
            font: resolveRunFont(resolvedStyle.headingFont),
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
            font: resolveRunFont(resolvedStyle.subHeadingFont),
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
    const transpose = node.table?.transpose === true;

    if (columns.length > 0) {
      let headerCells: TableCell[];
      let dataRows: TableRow[];

      if (transpose) {
        // 倒置：表頭 = 欄位 + 原資料列序號
        headerCells = [
          new TableCell({
            children: [
              new Paragraph({
                children: [
                  new TextRun({
                    text: "欄位",
                    bold: true,
                    size: bodySize,
                    font: resolveRunFont(resolvedStyle.bodyFont),
                  }),
                ],
              }),
            ],
          }),
          ...rows.map(
            (_, r) =>
              new TableCell({
                children: [
                  new Paragraph({
                    children: [
                      new TextRun({
                        text: String(r + 1),
                        bold: true,
                        size: bodySize,
                        font: resolveRunFont(resolvedStyle.bodyFont),
                      }),
                    ],
                  }),
                ],
              }),
          ),
        ];
        // 倒置：每一列 = 原欄位標題 + 各資料列在該欄位的值
        dataRows = columns.map(
          (col) =>
            new TableRow({
              children: [
                new TableCell({
                  children: [
                    new Paragraph({
                      children: [
                        new TextRun({
                          text: col.label || col.key,
                          bold: true,
                          size: bodySize,
                          font: resolveRunFont(resolvedStyle.bodyFont),
                        }),
                      ],
                    }),
                  ],
                }),
                ...rows.map(
                  (row) =>
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
                              font: resolveRunFont(resolvedStyle.bodyFont),
                            }),
                          ],
                        }),
                      ],
                    }),
                ),
              ],
            }),
        );
      } else {
        // 正常：表頭 = 欄位標題
        headerCells = columns.map(
          (col) =>
            new TableCell({
              children: [
                new Paragraph({
                  children: [
                    new TextRun({
                      text: col.label || col.key,
                      bold: true,
                      size: bodySize,
                      font: resolveRunFont(resolvedStyle.bodyFont),
                    }),
                  ],
                }),
              ],
            }),
        );
        // 正常：數據行
        dataRows =
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
                                font: resolveRunFont(resolvedStyle.bodyFont),
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
                                      font: resolveRunFont(
                                        resolvedStyle.bodyFont,
                                      ),
                                    }),
                                  ],
                                }),
                              ],
                      });
                    }),
                  }),
              );
      }

      const tableRows = transpose
        ? dataRows
        : [new TableRow({ children: headerCells }), ...dataRows];

      elements.push(
        new Table({
          rows: tableRows,
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
              font: resolveRunFont(resolvedStyle.bodyFont),
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
                            font: resolveRunFont(resolvedStyle.bodyFont),
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

    // 清單內為對象且使用子節點時：依每個 list item 逐項渲染，每項用 itemDataMap 渲染所有 children（含段落與內層清單），與 WordEditorForm 預覽一致
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
        const mergedSectionDataMap: Record<string, Record<string, any>> = {
          ...sectionDataMap,
          ...itemDataMap,
        };

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
            } else if (childNode.dataPath.includes(parentPathPrefix)) {
              // 子節點為完整路徑（如 執行步驟及方法.細分方法.細分名稱）時，取 list 項相對路徑
              const after =
                childNode.dataPath.indexOf(parentPathPrefix) +
                parentPathPrefix.length;
              adjustedChildNode = {
                ...childNode,
                dataPath: childNode.dataPath.substring(after),
              };
            }
          }

          // 如果是 paragraph 類型的子節點
          if (adjustedChildNode.type === "paragraph") {
            const childSectionData = adjustedChildNode.sectionId
              ? mergedSectionDataMap[adjustedChildNode.sectionId]
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
                    font: resolveRunFont(resolvedStyle.bodyFont),
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
                      font: resolveRunFont(resolvedStyle.subHeadingFont),
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
                    mergedSectionDataMap,
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
                mergedSectionDataMap,
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
                font: resolveRunFont(resolvedStyle.bodyFont),
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
            font: resolveRunFont(resolvedStyle.bodyFont),
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
export async function exportPlanUsingWordConfig(
  config: WordExportTemplateConfig,
  sections: ExportableSection[],
  planContent: Record<string, any>,
  projectTitle?: string,
  options?: { autoDownload?: boolean },
): Promise<Blob> {
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
              font: resolveRunFont(config.documentStyle?.headingFont),
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
              font: resolveRunFont(config.documentStyle?.bodyFont),
            }),
          ],
        }),
      );
    }

    const normalizedDocumentElements = insertTableSeparators(documentElements);

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
          children: normalizedDocumentElements,
        },
      ],
    });

    // 生成 blob
    const blob = await Packer.toBlob(doc);
    const shouldAutoDownload = options?.autoDownload !== false;

    if (shouldAutoDownload) {
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${projectTitle || "文檔"}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }

    return blob;
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
  projectCreatedAt?: string | Date,
  projectSectionVersions?: Record<string, number>,
) {
  // 第一優先級：嘗試從 backend 獲取 word export config
  if (grantId && templateId) {
    try {
      const wordConfig = await fetchWordExportConfig(
        grantId,
        templateId,
        projectCreatedAt,
        projectSectionVersions,
      );
      if (wordConfig) {
        console.log("Using word export config from backend");
        return await exportPlanUsingWordConfig(
          wordConfig,
          sections,
          planContent,
          projectTitle,
          { autoDownload: true },
        );
      }
    } catch (error) {
      console.warn("Failed to use word export config, falling back:", error);
      // 继续到 fallback 逻辑
    }
  }
  return exportPlanToWordDefault(sections, planContent, projectTitle);
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
  link.download = projectTitle ? `${projectTitle}.docx` : "計畫書草稿.docx";
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
