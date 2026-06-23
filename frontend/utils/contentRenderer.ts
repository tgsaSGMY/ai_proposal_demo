// 用於 Word 檔案，將內容渲染成 docx 的段落和表格結構

import {
  Paragraph,
  TextRun,
  HeadingLevel,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
  AlignmentType,
} from "docx";

type StyleKey = "sectionHeading" | "subHeading" | "body";

interface TextRunStyle {
  font: string;
  size: number;
  bold?: boolean;
}

export type DocxRendererOptions = Partial<
  Record<StyleKey, Partial<TextRunStyle>>
>;

const DEFAULT_RENDERER_STYLES: Record<StyleKey, TextRunStyle> = {
  sectionHeading: { font: "Times New Roman", size: 32, bold: true },
  subHeading: { font: "Times New Roman", size: 24, bold: true },
  body: { font: "Times New Roman", size: 24 },
};

// 渲染器的通用介面
export interface ContentRenderer<T> {
  addSectionTitle(text: string): void;
  addArrayTitle(text: string): void;
  addKeyValue(key: string, value: string): void;
  addParagraph(text: string): void;
  addImagePlaceholder(text: string): void;
  // 處理數組項目，可以是簡單字串或 title/desc 物件
  addNumberedListItem(
    index: number,
    content: string | { title: string; description: string },
  ): void;
  addIndentedListItem(key: string, value: string): void;
  addTable(headers: string[], rows: string[][]): void;
  addCustomParagraph(paragraph: Paragraph): void;
  // 取得最終結果
  getResult(): T;
}

export class DocxRenderer implements ContentRenderer<(Paragraph | Table)[]> {
  private paragraphs: (Paragraph | Table)[] = [];

  constructor(private readonly options: DocxRendererOptions = {}) {}

  private resolveStyle(key: StyleKey): TextRunStyle {
    return {
      ...DEFAULT_RENDERER_STYLES[key],
      ...(this.options[key] || {}),
    } as TextRunStyle;
  }

  private createRun(
    text: string,
    key: StyleKey,
    extras: Record<string, any> = {},
  ): TextRun {
    const style = this.resolveStyle(key);
    const base: Record<string, any> = {
      text,
      font: style.font,
      size: style.size,
    };
    if (
      typeof style.bold !== "undefined" &&
      typeof extras.bold === "undefined"
    ) {
      base.bold = style.bold;
    }
    return new TextRun({ ...base, ...extras });
  }

  addSectionTitle(text: string): void {
    this.paragraphs.push(
      new Paragraph({
        children: [this.createRun(text, "sectionHeading")],
        heading: HeadingLevel.HEADING_2,
        spacing: { before: 400, after: 200, line: 200 },
        style: "SectionHeading",
      }),
    );
  }

  addArrayTitle(text: string): void {
    this.paragraphs.push(
      new Paragraph({
        children: [this.createRun(text, "subHeading")],
        spacing: { before: 200, after: 100, line: 200 },
        style: "SubSectionHeading",
      }),
    );
  }

  addKeyValue(key: string, value: string): void {
    // 检查 value 是否是 array of objects
    try {
      const parsed = typeof value === "string" ? JSON.parse(value) : value;
      if (Array.isArray(parsed) && parsed.length > 0) {
        const firstItem = parsed[0];
        if (typeof firstItem === "object" && firstItem !== null) {
          // Note: addArrayTitle is already called by renderSectionContent
          // before addKeyValue, so we skip it here to avoid duplication.
          this.addObjectsTable(parsed);
          return;
        }
      }
    } catch (e) {
      // 如果不是 JSON，继续正常处理
    }

    const baseStyle = this.resolveStyle("body");
    this.paragraphs.push(
      new Paragraph({
        children: [
          this.createRun(`${key}: `, "body", { bold: true }),
          ...parseMarkdownToTextRuns(String(value), baseStyle),
        ],
        spacing: { after: 100 },
      }),
    );
  }

  addParagraph(text: string): void {
    // 检查 text 是否是 array of objects
    try {
      const parsed = typeof text === "string" ? JSON.parse(text) : text;
      if (Array.isArray(parsed) && parsed.length > 0) {
        const firstItem = parsed[0];
        if (typeof firstItem === "object" && firstItem !== null) {
          this.addObjectsTable(parsed);
          return;
        }
      }
    } catch (e) {
      // 如果不是 JSON，继续正常处理
    }

    const baseStyle = this.resolveStyle("body");
    this.paragraphs.push(
      new Paragraph({
        children: parseMarkdownToTextRuns(String(text), baseStyle),
        spacing: { after: 120, line: 200 },
      }),
    );
  }

  addImagePlaceholder(text: string): void {
    this.paragraphs.push(
      new Paragraph({
        children: [
          this.createRun(text, "body", {
            highlight: "yellow",
          }),
        ],
        spacing: { before: 100, after: 100, line: 200 },
      }),
    );
  }

  addNumberedListItem(
    index: number,
    content: string | { title: string; description: string },
  ): void {
    const baseStyle = this.resolveStyle("body");
    let children: TextRun[];
    if (typeof content === "object") {
      children = [
        this.createRun(`${index}. `, "body"),
        ...parseMarkdownToTextRuns(`${content.title}：`, baseStyle),
        this.createRun(content.description, "body", { break: 1 }),
      ];
    } else {
      children = [
        this.createRun(`${index}. `, "body"),
        ...parseMarkdownToTextRuns(String(content), baseStyle),
      ];
    }
    this.paragraphs.push(new Paragraph({ children }));
  }

  addIndentedListItem(key: string, value: string): void {
    // 如果 value 包含 [object Object]，跳过显示
    if (value.includes("[object Object]")) {
      return;
    }

    const baseStyle = this.resolveStyle("body");
    const children: TextRun[] = [
      this.createRun(`→${key}: `, "body"),
      ...parseMarkdownToTextRuns(String(value), baseStyle),
    ];
    this.paragraphs.push(
      new Paragraph({
        indent: { left: 720 }, // 約 0.5 inch 縮排
        children,
      }),
    );
  }

  addTable(headers: string[], rows: string[][]): void {
    const tableRows: TableRow[] = [];

    // 表頭
    tableRows.push(
      new TableRow({
        children: headers.map(
          (header) =>
            new TableCell({
              children: [
                new Paragraph({
                  children: [
                    this.createRun(header, "body", {
                      bold: true,
                      size: this.resolveStyle("body").size - 4,
                    }),
                  ],
                  alignment: AlignmentType.CENTER,
                }),
              ],
              shading: { fill: "D3D3D3" },
            }),
        ),
      }),
    );

    // 表格行
    rows.forEach((row) => {
      // 檢查是否是 SWOT 表格的 secondary header 行
      // 只有當整行都是「Opportunity機會」和「Threat威脅」時，才是 secondary header
      const isSecondaryHeader =
        row.length === 2 &&
        ((row[0] === "Opportunity機會" && row[1] === "Threat威脅") ||
          (row[0] &&
            row[0].includes("Opportunity") &&
            row[1] &&
            row[1].includes("Threat")));

      tableRows.push(
        new TableRow({
          children: row.map((cell) => {
            // 處理單元格內容：支持分行和圖片高亮
            const cellParagraphs = this.createCellParagraphs(
              cell,
              Boolean(isSecondaryHeader),
            );

            return new TableCell({
              children: cellParagraphs,
              shading: isSecondaryHeader ? { fill: "D3D3D3" } : undefined,
            });
          }),
        }),
      );
    });

    const table = new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      rows: tableRows,
      borders: {
        top: { style: BorderStyle.SINGLE, size: 1, color: "000000" },
        bottom: { style: BorderStyle.SINGLE, size: 1, color: "000000" },
        left: { style: BorderStyle.SINGLE, size: 1, color: "000000" },
        right: { style: BorderStyle.SINGLE, size: 1, color: "000000" },
        insideHorizontal: {
          style: BorderStyle.SINGLE,
          size: 1,
          color: "000000",
        },
        insideVertical: {
          style: BorderStyle.SINGLE,
          size: 1,
          color: "000000",
        },
      },
    });

    this.paragraphs.push(table);
    this.paragraphs.push(
      new Paragraph({
        text: "",
        spacing: { after: 200 },
      }),
    );
  }

  // 為表格單元格創建段落，支持分行和圖片高亮
  private createCellParagraphs(text: string, isHeader: boolean): Paragraph[] {
    const paragraphs: Paragraph[] = [];

    // 確保 text 是字符串，如果不是則轉換或返回空
    if (!text) {
      paragraphs.push(new Paragraph({ text: "" }));
      return paragraphs;
    }

    // 將任何非字符串類型轉換為字符串
    const textStr = typeof text === "string" ? text : String(text);

    // 先將多個換行符（2個以上）統一替換為雙換行符
    const normalizedText = textStr.replace(/\n{2,}/g, "\n\n");
    // 按雙換行符分段
    const segments = normalizedText
      .split(/\n\n+/)
      .filter((s: string) => s.trim());

    segments.forEach((segment: string) => {
      // 保留單個換行符，將每行作為獨立段落
      const lines = segment
        .split("\n")
        .map((line: string) => line.trim())
        .filter((line: string) => line);

      lines.forEach((line: string) => {
        if (line) {
          // 檢測圖片占位符，在原地 highlight
          const imagePattern = /【圖[:：][^】]+】/g;
          if (imagePattern.test(line)) {
            // 重置正則表達式
            imagePattern.lastIndex = 0;
            const parts = line.split(/【圖[:：][^】]+】/);
            const images = line.match(/【圖[:：][^】]+】/g) || [];

            // 構建混合段落
            const children: TextRun[] = [];
            for (let i = 0; i < parts.length; i++) {
              const partText = parts[i];
              if (partText) {
                children.push(
                  this.createRun(partText, "body", {
                    size: this.resolveStyle("body").size - 4,
                    bold: isHeader,
                  }),
                );
              }
              const imageText = images[i];
              if (imageText) {
                children.push(
                  this.createRun(imageText, "body", {
                    size: this.resolveStyle("body").size - 4,
                    highlight: "yellow",
                    bold: isHeader,
                  }),
                );
              }
            }

            paragraphs.push(
              new Paragraph({
                children: children,
                spacing: { after: 100, line: 200 },
                alignment: isHeader ? AlignmentType.CENTER : undefined,
              }),
            );
          } else {
            // 沒有圖片，直接創建段落
            paragraphs.push(
              new Paragraph({
                children: [
                  this.createRun(line, "body", {
                    size: this.resolveStyle("body").size - 4,
                    bold: isHeader,
                  }),
                ],
                spacing: { after: 100, line: 200 },
                alignment: isHeader ? AlignmentType.CENTER : undefined,
              }),
            );
          }
        }
      });
    });

    return paragraphs.length > 0 ? paragraphs : [new Paragraph({ text: "" })];
  }

  getResult(): (Paragraph | Table)[] {
    return this.paragraphs;
  }

  addCustomParagraph(paragraph: Paragraph): void {
    this.paragraphs.push(paragraph);
  }

  // 为 array of objects 创建表格
  private addObjectsTable(items: any[]): void {
    if (!Array.isArray(items) || items.length === 0) return;

    const firstItem = items[0];
    if (typeof firstItem !== "object" || firstItem === null) return;

    // 检查是否是简单对象（所有值都是基本类型）
    const isSimpleObject = items.every((item) => {
      return Object.values(item).every((val) => {
        return (
          typeof val === "string" ||
          typeof val === "number" ||
          typeof val === "boolean" ||
          val === null
        );
      });
    });

    // 如果不是简单对象，作为编号列表显示，并递归处理
    if (!isSimpleObject) {
      items.forEach((item, index) => {
        const numberingIndex = index + 1;
        const titleEntry = Object.entries(item).find(
          ([key]) => key === "title" || key === "name",
        );

        // 优先显示 title 作为编号列表项
        const title = titleEntry ? String(titleEntry[1]) : "";
        const baseStyle = this.resolveStyle("body");
        this.paragraphs.push(
          new Paragraph({
            children: [
              this.createRun(`${numberingIndex}. `, "body"),
              ...parseMarkdownToTextRuns(title, baseStyle),
            ],
            spacing: { after: 120, line: 200 },
          }),
        );

        // 显示其他字段，递归处理嵌套的对象或数组
        Object.entries(item).forEach(([key, value]) => {
          if (key !== "title" && key !== "name") {
            if (Array.isArray(value)) {
              // 如果是数组，检查是否是 array of objects
              if (
                value.length > 0 &&
                typeof value[0] === "object" &&
                value[0] !== null
              ) {
                // 是 array of objects，添加标题后递归调用
                this.paragraphs.push(
                  new Paragraph({
                    children: [this.createRun(key, "body", { bold: true })],
                    indent: { left: 720 },
                    spacing: { after: 80, line: 200 },
                  }),
                );
                this.addObjectsTable(value);
              } else {
                // 普通数组，作为文本显示
                const displayValue = JSON.stringify(value);
                const baseStyle = this.resolveStyle("body");
                this.paragraphs.push(
                  new Paragraph({
                    children: [
                      this.createRun(`${key}: `, "body"),
                      ...parseMarkdownToTextRuns(displayValue, baseStyle),
                    ],
                    indent: { left: 720 },
                    spacing: { after: 80, line: 200 },
                  }),
                );
              }
            } else if (typeof value === "object" && value !== null) {
              // 如果是对象，递归调用 addNestedObject
              this.paragraphs.push(
                new Paragraph({
                  children: [this.createRun(key, "body", { bold: true })],
                  indent: { left: 720 },
                  spacing: { after: 80, line: 200 },
                }),
              );
              this.addNestedObject(value);
            } else {
              // 基本类型，直接显示
              const baseStyle = this.resolveStyle("body");
              this.paragraphs.push(
                new Paragraph({
                  children: [
                    this.createRun(`${key}: `, "body"),
                    ...parseMarkdownToTextRuns(String(value), baseStyle),
                  ],
                  indent: { left: 720 },
                  spacing: { after: 80, line: 200 },
                }),
              );
            }
          }
        });
      });
      return;
    }

    // 优先检查是否有 title 或 name 字段
    const hasTitleField = items.some((item) => item.title || item.name);
    if (hasTitleField) {
      // 只显示 title 字段
      const baseStyle = this.resolveStyle("body");
      items.forEach((item) => {
        const title = item.title || item.name || "";
        if (title) {
          this.paragraphs.push(
            new Paragraph({
              children: parseMarkdownToTextRuns(String(title), baseStyle),
              spacing: { after: 120, line: 200 },
            }),
          );
        }
      });
      return;
    }

    const hasDescField = items.some(
      (item) => item.title || item.description || item.explanation,
    );
    if (hasDescField) {
      const baseStyle = this.resolveStyle("body");
      items.forEach((item) => {
        const desc = item.title || item.description || item.explanation || "";
        if (desc) {
          this.paragraphs.push(
            new Paragraph({
              children: parseMarkdownToTextRuns(String(desc), baseStyle),
              spacing: { after: 120, line: 200 },
            }),
          );
        }
      });
      return;
    }

    // 提取所有可能的键
    const allKeys = new Set<string>();
    items.forEach((item) => {
      Object.keys(item).forEach((key) => allKeys.add(key));
    });
    const headers = Array.from(allKeys);

    // 创建表格行
    const tableRows: TableRow[] = [];

    // 表頭
    tableRows.push(
      new TableRow({
        children: headers.map(
          (header) =>
            new TableCell({
              children: [
                new Paragraph({
                  children: [
                    this.createRun(header, "body", {
                      bold: true,
                      size: this.resolveStyle("body").size - 4,
                    }),
                  ],
                  alignment: AlignmentType.CENTER,
                }),
              ],
              shading: { fill: "D3D3D3" },
            }),
        ),
      }),
    );

    // 表格行
    items.forEach((row) => {
      tableRows.push(
        new TableRow({
          children: headers.map((header) => {
            const cellValue = String(row[header] ?? "");
            const baseStyle = this.resolveStyle("body");
            const cellRuns = parseMarkdownToTextRuns(cellValue, baseStyle).map(
              (run) =>
                new TextRun({
                  text: (run as any).text,
                  font: (run as any).font,
                  size:
                    ((run as any).size ? (run as any).size : baseStyle.size) -
                    4,
                  bold: (run as any).bold,
                  italics: (run as any).italics,
                  strike: (run as any).strike,
                }),
            );
            return new TableCell({
              children: [
                new Paragraph({
                  children: cellRuns,
                }),
              ],
            });
          }),
        }),
      );
    });

    const table = new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      rows: tableRows,
      borders: {
        top: { style: BorderStyle.SINGLE, size: 1, color: "000000" },
        bottom: { style: BorderStyle.SINGLE, size: 1, color: "000000" },
        left: { style: BorderStyle.SINGLE, size: 1, color: "000000" },
        right: { style: BorderStyle.SINGLE, size: 1, color: "000000" },
        insideHorizontal: {
          style: BorderStyle.SINGLE,
          size: 1,
          color: "000000",
        },
        insideVertical: {
          style: BorderStyle.SINGLE,
          size: 1,
          color: "000000",
        },
      },
    });

    this.paragraphs.push(table);
    this.paragraphs.push(
      new Paragraph({
        text: "",
        spacing: { after: 200 },
      }),
    );
  }

  // 递归处理嵌套的单个对象
  private addNestedObject(obj: any): void {
    if (!obj || typeof obj !== "object") return;

    Object.entries(obj).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        // 如果是数组，检查是否是 array of objects
        if (
          value.length > 0 &&
          typeof value[0] === "object" &&
          value[0] !== null
        ) {
          // 是 array of objects，添加标题后递归调用
          this.paragraphs.push(
            new Paragraph({
              children: [
                new TextRun({
                  text: key,
                  font: "Times New Roman",
                  size: 22,
                  bold: true,
                }),
              ],
              indent: { left: 1440 },
              spacing: { after: 80, line: 200 },
            }),
          );
          this.addObjectsTable(value);
        } else {
          // 普通数组，作为文本显示
          const displayValue = JSON.stringify(value);
          const baseStyle = this.resolveStyle("body");
          this.paragraphs.push(
            new Paragraph({
              children: [
                new TextRun({
                  text: `${key}: `,
                  font: "Times New Roman",
                  size: 22,
                }),
                ...parseMarkdownToTextRuns(displayValue, baseStyle),
              ],
              indent: { left: 1440 },
              spacing: { after: 80, line: 200 },
            }),
          );
        }
      } else if (typeof value === "object" && value !== null) {
        // 如果是对象，继续递归
        this.paragraphs.push(
          new Paragraph({
            children: [
              new TextRun({
                text: key,
                font: "Times New Roman",
                size: 22,
                bold: true,
              }),
            ],
            indent: { left: 1440 },
            spacing: { after: 80, line: 200 },
          }),
        );
        this.addNestedObject(value);
      } else {
        // 基本类型，直接显示
        const baseStyle = this.resolveStyle("body");
        this.paragraphs.push(
          new Paragraph({
            children: [
              new TextRun({
                text: `${key}: `,
                font: "Times New Roman",
                size: 22,
              }),
              ...parseMarkdownToTextRuns(String(value), baseStyle),
            ],
            indent: { left: 1440 },
            spacing: { after: 80, line: 200 },
          }),
        );
      }
    });
  }

  // DocxRenderer 特有的方法
  addEmptyContentMessage(): void {
    this.paragraphs.push(
      new Paragraph({
        children: [new TextRun({ text: "（無內容）", italics: true })],
        spacing: { after: 400 },
        style: "NormalText",
      }),
    );
  }
}

function escapeHtml(unsafe: string): string {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// 解析 Markdown 格式的文本，返回 TextRun 数组用于 Word 文档
function parseMarkdownToTextRuns(
  text: string,
  baseStyle: TextRunStyle,
): TextRun[] {
  const runs: TextRun[] = [];

  // 支持的格式：**bold**、__bold__、*italic*、_italic_、~~strikethrough~~
  const patterns = [
    { regex: /\*\*(.+?)\*\*/g, format: "bold" },
    { regex: /__(.+?)__/g, format: "bold" },
    { regex: /\*(.+?)\*/g, format: "italic" },
    { regex: /_(.+?)_/g, format: "italic" },
    { regex: /~~(.+?)~~/g, format: "strikethrough" },
  ];

  let lastIndex = 0;
  let matches: Array<{
    index: number;
    endIndex: number;
    format: string;
    text: string;
  }> = [];

  // 收集所有匹配项
  patterns.forEach(({ regex, format }) => {
    let match;
    while ((match = regex.exec(text)) !== null) {
      matches.push({
        index: match.index,
        endIndex: match.index + match[0].length,
        format,
        text: match[1] || "",
      });
    }
  });

  // 按索引排序并处理
  matches.sort((a, b) => a.index - b.index);

  for (const match of matches) {
    // 添加匹配前的普通文本
    if (lastIndex < match.index) {
      runs.push(
        new TextRun({
          text: text.substring(lastIndex, match.index),
          font: baseStyle.font,
          size: baseStyle.size,
          bold: baseStyle.bold,
        }),
      );
    }

    // 添加格式化的文本
    const runConfig: any = {
      text: match.text,
      font: baseStyle.font,
      size: baseStyle.size,
    };

    if (match.format === "bold") {
      runConfig.bold = true;
    } else if (match.format === "italic") {
      runConfig.italics = true;
    } else if (match.format === "strikethrough") {
      runConfig.strike = true;
    }

    runs.push(new TextRun(runConfig));
    lastIndex = match.endIndex;
  }

  // 添加剩余的文本
  if (lastIndex < text.length) {
    runs.push(
      new TextRun({
        text: text.substring(lastIndex),
        font: baseStyle.font,
        size: baseStyle.size,
        bold: baseStyle.bold,
      }),
    );
  }

  // 如果没有找到任何格式，返回单个 TextRun
  if (runs.length === 0) {
    runs.push(
      new TextRun({
        text,
        font: baseStyle.font,
        size: baseStyle.size,
        bold: baseStyle.bold,
      }),
    );
  }

  return runs;
}

// 解析 Markdown 格式的文本，处理粗体字、斜体、删除线等（用于 HTML）
function renderMarkdownToHtml(text: string): string {
  let html = escapeHtml(text);
  // 处理 **bold** 格式的粗体字
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // 处理 __bold__ 格式的粗体字
  html = html.replace(/__(.+?)__/g, "<strong>$1</strong>");
  // 处理 *italic* 格式的斜体字
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  // 处理 _italic_ 格式的斜体字
  html = html.replace(/_(.+?)_/g, "<em>$1</em>");
  // 处理 ~~strikethrough~~ 格式的删除线
  html = html.replace(/~~(.+?)~~/g, "<del>$1</del>");
  return html;
}

export class HtmlRenderer implements ContentRenderer<string> {
  private html: string = "";
  private isScrambled: boolean = false;

  constructor(isScrambled: boolean = false) {
    this.isScrambled = isScrambled;
  }

  setScrambled(scramble: boolean): void {
    this.isScrambled = scramble;
  }

  private processText(text: string): string {
    if (!this.isScrambled || !text) return text;
    const pool = "的是我在有和人這中大們國個產實研發創製技計專新合資作程時理業主部地得法生分可行市產主經化學";
    return text.split("").map(char => {
      if (/[\u4e00-\u9fa5]/.test(char)) {
        return pool[Math.floor(Math.random() * pool.length)];
      }
      if (/[a-zA-Z0-9]/.test(char)) {
        return Math.floor(Math.random() * 10).toString();
      }
      return char;
    }).join("");
  }

  addSectionTitle(text: string): void {
    this.html += `<h2 class="text-2xl font-bold mt-6 mb-3">${escapeHtml(
      text,
    )}</h2>`;
  }

  addArrayTitle(text: string): void {
    this.html += `<h3 class="text-lg font-semibold mt-4 mb-2">${escapeHtml(
      text,
    )}</h3>`;
  }

  addKeyValue(key: string, value: string): void {
    const isTargetSection = key === "二、預定進度及查核點";
    const blurClass = (this.isScrambled || isTargetSection) ? "filter blur-[5px] select-none pointer-events-none" : "";
    // 检查 value 是否是 array of objects
    try {
      const parsed = typeof value === "string" ? JSON.parse(value) : value;
      if (Array.isArray(parsed) && parsed.length > 0) {
        const firstItem = parsed[0];
        if (typeof firstItem === "object" && firstItem !== null) {
          if (isTargetSection) {
            // 1. 保持標題 "二、預定進度及查核點:" 清晰不模糊
            this.html += `<div class="my-2"><strong class="font-semibold">${escapeHtml(key)}:</strong>`;
            // 2. 一次性模糊整個子表格容器
            this.html += `<div class="${blurClass}">`;
            this.renderArrayOfObjects(parsed);
            this.html += "</div></div>";
          } else {
            // 其他普通的物件陣列，保持容器不模糊，讓內部處理各自的單元格模糊
            this.html += `<div class="my-2"><strong class="font-semibold">${escapeHtml(key)}:</strong>`;
            this.renderArrayOfObjects(parsed);
            this.html += "</div>";
          }
          return;
        }
      }
    } catch (e) {
      // 如果不是 JSON，继续正常处理
    }

    const processedValue = this.processText(value);
    // 保持 Key 清晰不模糊，只模糊包裝 Value 的 span 區塊
    this.html += `<p class="my-2"><strong class="font-semibold">${escapeHtml(
      key,
    )}:</strong> <span class="${blurClass}">${renderMarkdownToHtml(processedValue)}</span></p>`;
  }

  addParagraph(text: string): void {
    const blurClass = this.isScrambled ? "filter blur-[5px] select-none pointer-events-none" : "";
    // 检查是否是 array of objects
    try {
      const parsed = JSON.parse(text);
      if (Array.isArray(parsed) && parsed.length > 0) {
        const firstItem = parsed[0];
        if (typeof firstItem === "object" && firstItem !== null) {
          // 對於物件陣列，保持容器不模糊，讓 renderArrayOfObjects 自己做單元格精確模糊
          this.html += `<div>`;
          this.renderArrayOfObjects(parsed);
          this.html += "</div>";
          return;
        }
      }
    } catch (e) {
      // 如果不是 JSON，继续正常处理
    }

    const processedText = this.processText(text);
    this.html += `<p class="my-2 ${blurClass}">${renderMarkdownToHtml(processedText)}</p>`;
  }

  addImagePlaceholder(text: string): void {
    this.html += `<p class="my-2 bg-yellow-300 p-2">${escapeHtml(text)}</p>`;
  }

  addNumberedListItem(
    index: number,
    content: string | { title: string; description: string },
  ): void {
    const blurClass = this.isScrambled ? "filter blur-[5px] select-none pointer-events-none" : "";
    if (typeof content === "object") {
      const processedTitle = this.processText(content.title);
      // 保持編號 1. 2. 清晰不模糊，只模糊內容文字
      this.html += `<p class="my-1"><span class="mr-2">${index}.</span><strong><span class="${blurClass}">${renderMarkdownToHtml(
        processedTitle,
      )}</span></strong></p>`;
    } else {
      // 检查是否是 array of objects
      try {
        const parsed = JSON.parse(content);
        if (Array.isArray(parsed) && parsed.length > 0) {
          const firstItem = parsed[0];
          if (typeof firstItem === "object" && firstItem !== null) {
            // 保持編號清晰
            this.html += `<div class="my-2"><span class="mr-2">${index}.</span>`;
            this.renderArrayOfObjects(parsed);
            this.html += "</div>";
            return;
          }
        }
      } catch (e) {
        // 如果不是 JSON，继续正常处理
      }

      const processedContent = this.processText(content);
      this.html += `<p class="my-1"><span class="mr-2">${index}.</span><span class="${blurClass}">${renderMarkdownToHtml(
        processedContent,
      )}</span></p>`;
    }
  }

  addIndentedListItem(key: string, value: string): void {
    // 首先检查 value 是否包含 [object Object] 字符串
    if (value.includes("[object Object]")) {
      // 跳過顯示這個項，因為數據不完整
      return;
    }

    const blurClass = this.isScrambled ? "filter blur-[5px] select-none pointer-events-none" : "";
    // 檢查 value 是否是 array of objects
    try {
      const parsed = typeof value === "string" ? JSON.parse(value) : value;
      if (Array.isArray(parsed) && parsed.length > 0) {
        const firstItem = parsed[0];
        if (typeof firstItem === "object" && firstItem !== null) {
          // 保持 Key 清晰
          this.html += `<div class="ml-4 my-2"><span class="font-semibold text-gray-800">${escapeHtml(
            key,
          )}:</span>`;
          this.renderArrayOfObjects(parsed);
          this.html += "</div>";
          return;
        }
      }
    } catch (e) {
      // 如果不是 JSON，繼續正常處理
    }

    const processedValue = this.processText(value);
    // 保持 Key 粗體清晰
    this.html += `<p class="ml-8 text-gray-700"><span class="font-semibold">${escapeHtml(
      key,
    )}:</span> <span class="${blurClass}">${renderMarkdownToHtml(processedValue)}</span></p>`;
  }

  addTable(headers: string[], rows: string[][]): void {
    const blurClass = this.isScrambled ? "filter blur-[4px] select-none pointer-events-none" : "";
    // 保持 Table 邊框線清晰，不要在 <table> 加 blur 類
    this.html +=
      `<table class="border-collapse border border-gray-400 w-full my-4"><thead><tr>`;
    headers.forEach((header) => {
      // 保持表頭 <th> 文字清晰不模糊
      this.html += `<th class="border border-gray-400 bg-gray-300 p-2 font-semibold text-sm">${escapeHtml(
        header,
      )}</th>`;
    });
    this.html += "</tr></thead><tbody>";
    rows.forEach((row) => {
      this.html += "<tr>";
      row.forEach((cell) => {
        const processedCell = this.processText(cell);
        // 只模糊單元格 <td> 內部的文字內容
        this.html += `<td class="border border-gray-400 p-2 text-sm"><span class="${blurClass}">${renderMarkdownToHtml(
          processedCell,
        )}</span></td>`;
      });
      this.html += "</tr>";
    });
    this.html += "</tbody></table>";
  }

  // 处理 array of objects 的方法
  private renderArrayOfObjects(items: any[]): void {
    if (!Array.isArray(items) || items.length === 0) return;

    const blurClass = this.isScrambled ? "filter blur-[5px] select-none pointer-events-none" : "";
    const firstItem = items[0];
    if (typeof firstItem !== "object" || firstItem === null) return;

    // 检查是否所有项都是对象
    const allObjects = items.every(
      (item) => typeof item === "object" && item !== null,
    );
    if (!allObjects) return;

    // 检查是否是简单对象（所有值都是基本类型）
    const isSimpleObject = items.every((item) => {
      return Object.values(item).every((val) => {
        return (
          typeof val === "string" ||
          typeof val === "number" ||
          typeof val === "boolean" ||
          val === null
        );
      });
    });

    // 如果是简单对象，生成表格
    if (isSimpleObject) {
      // 优先检查是否有 title 或 name 字段
      const hasTitleField = items.some((item) => item.title || item.name);
      if (hasTitleField) {
        // 只显示 title 字段
        items.forEach((item) => {
          const title = item.title || item.name || "";
          if (title) {
            this.html += `<div class="my-2 p-2 bg-gray-50 rounded border-l-4 border-blue-500"><strong>${renderMarkdownToHtml(
              String(title),
            )}</strong></div>`;
          }
        });
        return;
      }

      const hasDescField = items.some(
        (item) => item.title || item.description || item.explanation,
      );
      if (hasDescField) {
        items.forEach((item) => {
          const desc = item.title || item.description || item.explanation || "";
          if (desc) {
            this.html += `<div class="my-2 p-2 bg-gray-50 rounded border-l-4 border-blue-500">${renderMarkdownToHtml(
              String(desc),
            )}</div>`;
          }
        });
        return;
      }

      // 提取所有可能的键
      const allKeys = new Set<string>();
      items.forEach((item) => {
        Object.keys(item).forEach((key) => allKeys.add(key));
      });
      const headers = Array.from(allKeys);

      // 生成表格
      this.html +=
        '<table class="border-collapse border border-gray-400 w-full my-3"><thead><tr>';
      headers.forEach((header) => {
        this.html += `<th class="border border-gray-400 bg-gray-300 p-2 font-semibold text-sm">${escapeHtml(
          header,
        )}</th>`;
      });
      this.html += "</tr></thead><tbody>";

      items.forEach((row) => {
        this.html += "<tr>";
        headers.forEach((header) => {
          const value = row[header];
          const displayValue =
            value === null || value === undefined ? "" : String(value);
          const processedValue = this.processText(displayValue);
          // 僅模糊單元格 <td> 內部的文字內容
          this.html += `<td class="border border-gray-400 p-2 text-sm"><span class="${blurClass}">${renderMarkdownToHtml(
            processedValue,
          )}</span></td>`;
        });
        this.html += "</tr>";
      });
      this.html += "</tbody></table>";;
    } else {
      // 如果对象中包含嵌套的对象或数组，用编号列表显示，并递归处理
      items.forEach((item, index) => {
        const numberingIndex = index + 1;
        // 优先显示 title 字段作为编号列表项的主标题
        const title = item.title || item.name || "";
        if (title) {
          this.html += `<div class="my-2"><span class="mr-2 font-semibold">${numberingIndex}.</span><strong>${renderMarkdownToHtml(
            String(title),
          )}</strong></div>`;
        } else {
          this.html += `<div class="my-2"><span class="mr-2 font-semibold">${numberingIndex}.</span></div>`;
        }

        // 显示其他字段，递归处理嵌套的对象或数组
        Object.entries(item).forEach(([key, value]) => {
          if (key !== "title" && key !== "name") {
            if (Array.isArray(value)) {
              // 如果是数组，检查是否是 array of objects
              if (
                value.length > 0 &&
                typeof value[0] === "object" &&
                value[0] !== null
              ) {
                // 是 array of objects，递归调用 renderArrayOfObjects
                this.html += `<div class="ml-8"><strong>${escapeHtml(
                  key,
                )}:</strong></div>`;
                this.renderArrayOfObjects(value);
              } else {
                // 普通数组，作为文本显示
                this.html += `<div class="ml-8"><strong>${escapeHtml(
                  key,
                )}:</strong> ${renderMarkdownToHtml(JSON.stringify(value))}</div>`;
              }
            } else if (typeof value === "object" && value !== null) {
              // 如果是对象，递归调用 renderNestedObject
              this.html += `<div class="ml-8"><strong>${escapeHtml(
                key,
              )}:</strong></div>`;
              this.renderNestedObject(value);
            } else {
              // 基本类型，直接显示
              this.html += `<div class="ml-8"><strong>${escapeHtml(
                key,
              )}:</strong> ${renderMarkdownToHtml(String(value))}</div>`;
            }
          }
        });
      });
    }
  }

  // 递归处理嵌套的单个对象
  private renderNestedObject(obj: any): void {
    if (!obj || typeof obj !== "object") return;

    Object.entries(obj).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        // 如果是数组，检查是否是 array of objects
        if (
          value.length > 0 &&
          typeof value[0] === "object" &&
          value[0] !== null
        ) {
          // 是 array of objects，递归调用 renderArrayOfObjects
          this.html += `<div class="ml-12"><strong>${escapeHtml(
            key,
          )}:</strong></div>`;
          this.renderArrayOfObjects(value);
        } else {
          // 普通数组，作为文本显示
          this.html += `<div class="ml-12"><strong>${escapeHtml(
            key,
          )}:</strong> ${renderMarkdownToHtml(JSON.stringify(value))}</div>`;
        }
      } else if (typeof value === "object" && value !== null) {
        // 如果是对象，继续递归
        this.html += `<div class="ml-12"><strong>${escapeHtml(
          key,
        )}:</strong></div>`;
        this.renderNestedObject(value);
      } else {
        // 基本类型，直接显示
        this.html += `<div class="ml-12"><strong>${escapeHtml(
          key,
        )}:</strong> ${renderMarkdownToHtml(String(value))}</div>`;
      }
    });
  }

  getResult(): string {
    return this.html;
  }

  addCustomParagraph(paragraph: Paragraph): void {
    // For HTML rendering, we can't directly use Paragraph object
    // This is a no-op for HtmlRenderer
  }

  // HtmlRenderer 特有的方法
  addEmptyContentMessage(): void {
    this.html += `<p class="text-gray-500 italic my-4">（無內容）</p>`;
  }
}
