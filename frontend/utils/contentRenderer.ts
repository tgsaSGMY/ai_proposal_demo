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
    content: string | { title: string; description: string }
  ): void;
  addIndentedListItem(key: string, value: string): void;
  addTable(headers: string[], rows: string[][]): void;
  addCustomParagraph(paragraph: Paragraph): void;
  // 取得最終結果
  getResult(): T;
}

export class DocxRenderer implements ContentRenderer<(Paragraph | Table)[]> {
  private paragraphs: (Paragraph | Table)[] = [];

  addSectionTitle(text: string): void {
    this.paragraphs.push(
      new Paragraph({
        text: text,
        heading: HeadingLevel.HEADING_2,
        spacing: { before: 400, after: 200, line: 200 },
        style: "SectionHeading",
        run: {
          font: "Times New Roman",
          size: 32,
          bold: true,
        },
      })
    );
  }

  addArrayTitle(text: string): void {
    this.paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: text,
            font: "Times New Roman",
            size: 24,
            bold: true,
          }),
        ],
        spacing: { before: 200, after: 100, line: 200 },
        style: "SubSectionHeading",
      })
    );
  }

  addKeyValue(key: string, value: string): void {
    // 检查 value 是否是 array of objects
    try {
      const parsed = typeof value === "string" ? JSON.parse(value) : value;
      if (Array.isArray(parsed) && parsed.length > 0) {
        const firstItem = parsed[0];
        if (typeof firstItem === "object" && firstItem !== null) {
          this.addArrayTitle(key);
          this.addObjectsTable(parsed);
          return;
        }
      }
    } catch (e) {
      // 如果不是 JSON，继续正常处理
    }

    this.paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({ text: `${key}: `, bold: true }),
          new TextRun(value),
        ],
        spacing: { after: 100 },
      })
    );
  }

  addParagraph(text: string): void {
    this.paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: text,
            font: "Times New Roman",
            size: 24,
          }),
        ],
        spacing: { after: 120, line: 200 },
      })
    );
  }

  addImagePlaceholder(text: string): void {
    this.paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: text,
            font: "Times New Roman",
            size: 24,
            highlight: "yellow",
          }),
        ],
        spacing: { before: 100, after: 100, line: 200 },
      })
    );
  }

  addNumberedListItem(
    index: number,
    content: string | { title: string; description: string }
  ): void {
    let children: TextRun[];
    if (typeof content === "object") {
      children = [
        new TextRun({ text: `${index}. ${content.title}：`, bold: true }),
        new TextRun({ text: content.description, break: 1 }),
      ];
    } else {
      children = [new TextRun({ text: `${index}. ` }), new TextRun(content)];
    }
    this.paragraphs.push(new Paragraph({ children }));
  }

  addIndentedListItem(key: string, value: string): void {
    // 如果 value 包含 [object Object]，跳过显示
    if (value.includes("[object Object]")) {
      return;
    }

    this.paragraphs.push(
      new Paragraph({
        indent: { left: 720 }, // 約 0.5 inch 縮排
        children: [new TextRun({ text: `→${key}: ${value}` })],
      })
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
                    new TextRun({
                      text: header,
                      bold: true,
                      font: "Times New Roman",
                      size: 20,
                    }),
                  ],
                  alignment: AlignmentType.CENTER,
                }),
              ],
              shading: { fill: "D3D3D3" },
            })
        ),
      })
    );

    // 表格行
    rows.forEach((row, rowIndex) => {
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
              Boolean(isSecondaryHeader)
            );

            return new TableCell({
              children: cellParagraphs,
              shading: isSecondaryHeader ? { fill: "D3D3D3" } : undefined,
            });
          }),
        })
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
      })
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

      lines.forEach((line: string, lineIndex: number) => {
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
              if (parts[i]) {
                children.push(
                  new TextRun({
                    text: parts[i],
                    font: "Times New Roman",
                    size: 20,
                    bold: isHeader,
                  })
                );
              }
              if (i < images.length) {
                children.push(
                  new TextRun({
                    text: images[i],
                    font: "Times New Roman",
                    size: 20,
                    highlight: "yellow",
                    bold: isHeader,
                  })
                );
              }
            }

            paragraphs.push(
              new Paragraph({
                children: children,
                spacing: { after: 100, line: 200 },
                alignment: isHeader ? AlignmentType.CENTER : undefined,
              })
            );
          } else {
            // 沒有圖片，直接創建段落
            paragraphs.push(
              new Paragraph({
                children: [
                  new TextRun({
                    text: line,
                    font: "Times New Roman",
                    size: 20,
                    bold: isHeader,
                  }),
                ],
                spacing: { after: 100, line: 200 },
                alignment: isHeader ? AlignmentType.CENTER : undefined,
              })
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
          ([key]) => key === "title" || key === "name"
        );

        // 优先显示 title 作为编号列表项
        const title = titleEntry ? String(titleEntry[1]) : "";
        this.paragraphs.push(
          new Paragraph({
            children: [
              new TextRun({
                text: `${numberingIndex}. ${title}`,
                font: "Times New Roman",
                size: 24,
                bold: true,
              }),
            ],
            spacing: { after: 120, line: 200 },
          })
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
                    children: [
                      new TextRun({
                        text: key,
                        font: "Times New Roman",
                        size: 22,
                        bold: true,
                      }),
                    ],
                    indent: { left: 720 },
                    spacing: { after: 80, line: 200 },
                  })
                );
                this.addObjectsTable(value);
              } else {
                // 普通数组，作为文本显示
                const displayValue = JSON.stringify(value);
                this.paragraphs.push(
                  new Paragraph({
                    children: [
                      new TextRun({
                        text: `${key}: ${displayValue}`,
                        font: "Times New Roman",
                        size: 22,
                      }),
                    ],
                    indent: { left: 720 },
                    spacing: { after: 80, line: 200 },
                  })
                );
              }
            } else if (typeof value === "object" && value !== null) {
              // 如果是对象，递归调用 addNestedObject
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
                  indent: { left: 720 },
                  spacing: { after: 80, line: 200 },
                })
              );
              this.addNestedObject(value);
            } else {
              // 基本类型，直接显示
              this.paragraphs.push(
                new Paragraph({
                  children: [
                    new TextRun({
                      text: `${key}: ${String(value)}`,
                      font: "Times New Roman",
                      size: 22,
                    }),
                  ],
                  indent: { left: 720 },
                  spacing: { after: 80, line: 200 },
                })
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
      items.forEach((item) => {
        const title = item.title || item.name || "";
        if (title) {
          this.paragraphs.push(
            new Paragraph({
              children: [
                new TextRun({
                  text: String(title),
                  font: "Times New Roman",
                  size: 24,
                }),
              ],
              spacing: { after: 120, line: 200 },
            })
          );
        }
      });
      return;
    }

    const hasDescField = items.some(
      (item) => item.title || item.description || item.explanation
    );
    if (hasDescField) {
      items.forEach((item) => {
        const desc = item.title || item.description || item.explanation || "";
        if (desc) {
          this.paragraphs.push(
            new Paragraph({
              children: [
                new TextRun({
                  text: String(desc),
                  font: "Times New Roman",
                  size: 24,
                }),
              ],
              spacing: { after: 120, line: 200 },
            })
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
                    new TextRun({
                      text: header,
                      bold: true,
                      font: "Times New Roman",
                      size: 20,
                    }),
                  ],
                  alignment: AlignmentType.CENTER,
                }),
              ],
              shading: { fill: "D3D3D3" },
            })
        ),
      })
    );

    // 表格行
    items.forEach((row) => {
      tableRows.push(
        new TableRow({
          children: headers.map(
            (header) =>
              new TableCell({
                children: [
                  new Paragraph({
                    children: [
                      new TextRun({
                        text: String(row[header] ?? ""),
                        font: "Times New Roman",
                        size: 20,
                      }),
                    ],
                  }),
                ],
              })
          ),
        })
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
      })
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
            })
          );
          this.addObjectsTable(value);
        } else {
          // 普通数组，作为文本显示
          const displayValue = JSON.stringify(value);
          this.paragraphs.push(
            new Paragraph({
              children: [
                new TextRun({
                  text: `${key}: ${displayValue}`,
                  font: "Times New Roman",
                  size: 22,
                }),
              ],
              indent: { left: 1440 },
              spacing: { after: 80, line: 200 },
            })
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
          })
        );
        this.addNestedObject(value);
      } else {
        // 基本类型，直接显示
        this.paragraphs.push(
          new Paragraph({
            children: [
              new TextRun({
                text: `${key}: ${String(value)}`,
                font: "Times New Roman",
                size: 22,
              }),
            ],
            indent: { left: 1440 },
            spacing: { after: 80, line: 200 },
          })
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
      })
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

export class HtmlRenderer implements ContentRenderer<string> {
  private html: string = "";

  addSectionTitle(text: string): void {
    this.html += `<h2 class="text-2xl font-bold mt-6 mb-3">${escapeHtml(
      text
    )}</h2>`;
  }

  addArrayTitle(text: string): void {
    this.html += `<h3 class="text-lg font-semibold mt-4 mb-2">${escapeHtml(
      text
    )}</h3>`;
  }

  addKeyValue(key: string, value: string): void {
    // 检查 value 是否是 array of objects
    try {
      const parsed = typeof value === "string" ? JSON.parse(value) : value;
      if (Array.isArray(parsed) && parsed.length > 0) {
        const firstItem = parsed[0];
        if (typeof firstItem === "object" && firstItem !== null) {
          // this.html += `<div class="my-2"><span class="font-semibold">${escapeHtml(
          //   key
          // )}:</span>`;
          this.renderArrayOfObjects(parsed);
          this.html += "</div>";
          return;
        }
      }
    } catch (e) {
      // 如果不是 JSON，继续正常处理
    }

    this.html += `<p><strong class="font-semibold">${escapeHtml(
      key
    )}:</strong> ${escapeHtml(value)}</p>`;
  }

  addParagraph(text: string): void {
    // 检查是否是 array of objects
    try {
      const parsed = JSON.parse(text);
      if (Array.isArray(parsed) && parsed.length > 0) {
        const firstItem = parsed[0];
        if (typeof firstItem === "object" && firstItem !== null) {
          this.renderArrayOfObjects(parsed);
          return;
        }
      }
    } catch (e) {
      // 如果不是 JSON，继续正常处理
    }

    this.html += `<p class="my-2">${escapeHtml(text)}</p>`;
  }

  addImagePlaceholder(text: string): void {
    this.html += `<p class="my-2 bg-yellow-300 p-2">${escapeHtml(text)}</p>`;
  }

  addNumberedListItem(
    index: number,
    content: string | { title: string; description: string }
  ): void {
    if (typeof content === "object") {
      this.html += `<p><span class="mr-2">${index}.</span><strong>${escapeHtml(
        content.title
      )}</strong></p>`;
    } else {
      // 检查是否是 array of objects
      try {
        const parsed = JSON.parse(content);
        if (Array.isArray(parsed) && parsed.length > 0) {
          const firstItem = parsed[0];
          if (typeof firstItem === "object" && firstItem !== null) {
            this.html += `<div class="my-2"><span class="mr-2">${index}.</span>`;
            this.renderArrayOfObjects(parsed);
            this.html += "</div>";
            return;
          }
        }
      } catch (e) {
        // 如果不是 JSON，继续正常处理
      }

      this.html += `<p><span class="mr-2">${index}.</span>${escapeHtml(
        content
      )}</p>`;
    }
  }

  addIndentedListItem(key: string, value: string): void {
    // 首先检查 value 是否包含 [object Object] 字符串
    if (value.includes("[object Object]")) {
      // 跳过显示这个项，因为数据不完整
      return;
    }

    // 检查 value 是否是 array of objects
    try {
      const parsed = typeof value === "string" ? JSON.parse(value) : value;
      if (Array.isArray(parsed) && parsed.length > 0) {
        const firstItem = parsed[0];
        if (typeof firstItem === "object" && firstItem !== null) {
          this.html += `<div class="ml-4 my-2"><span class="font-semibold text-gray-800">${escapeHtml(
            key
          )}:</span>`;
          this.renderArrayOfObjects(parsed);
          this.html += "</div>";
          return;
        }
      }
    } catch (e) {
      // 如果不是 JSON，继续正常处理
    }

    this.html += `<p class="ml-8 text-gray-700"><span class="font-semibold">${escapeHtml(
      key
    )}:</span> ${escapeHtml(value)}</p>`;
  }

  addTable(headers: string[], rows: string[][]): void {
    this.html +=
      '<table class="border-collapse border border-gray-400 w-full my-4"><thead><tr>';
    headers.forEach((header) => {
      this.html += `<th class="border border-gray-400 bg-gray-300 p-2 font-semibold">${escapeHtml(
        header
      )}</th>`;
    });
    this.html += "</tr></thead><tbody>";
    rows.forEach((row) => {
      this.html += "<tr>";
      row.forEach((cell) => {
        this.html += `<td class="border border-gray-400 p-2">${escapeHtml(
          cell
        )}</td>`;
      });
      this.html += "</tr>";
    });
    this.html += "</tbody></table>";
  }

  // 处理 array of objects 的方法
  private renderArrayOfObjects(items: any[]): void {
    if (!Array.isArray(items) || items.length === 0) return;

    const firstItem = items[0];
    if (typeof firstItem !== "object" || firstItem === null) return;

    // 检查是否所有项都是对象
    const allObjects = items.every(
      (item) => typeof item === "object" && item !== null
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
            this.html += `<div class="my-2 p-2 bg-gray-50 rounded border-l-4 border-blue-500"><strong>${escapeHtml(
              String(title)
            )}</strong></div>`;
          }
        });
        return;
      }

      const hasDescField = items.some(
        (item) => item.title || item.description || item.explanation
      );
      if (hasDescField) {
        items.forEach((item) => {
          const desc = item.title || item.description || item.explanation || "";
          if (desc) {
            this.html += `<div class="my-2 p-2 bg-gray-50 rounded border-l-4 border-blue-500">${escapeHtml(
              String(desc)
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
          header
        )}</th>`;
      });
      this.html += "</tr></thead><tbody>";

      items.forEach((row) => {
        this.html += "<tr>";
        headers.forEach((header) => {
          const value = row[header];
          const displayValue =
            value === null || value === undefined ? "" : String(value);
          this.html += `<td class="border border-gray-400 p-2 text-sm">${escapeHtml(
            displayValue
          )}</td>`;
        });
        this.html += "</tr>";
      });
      this.html += "</tbody></table>";
    } else {
      // 如果对象中包含嵌套的对象或数组，用编号列表显示，并递归处理
      items.forEach((item, index) => {
        const numberingIndex = index + 1;
        // 优先显示 title 字段作为编号列表项的主标题
        const title = item.title || item.name || "";
        if (title) {
          this.html += `<div class="my-2"><span class="mr-2 font-semibold">${numberingIndex}.</span><strong>${escapeHtml(
            String(title)
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
                  key
                )}:</strong></div>`;
                this.renderArrayOfObjects(value);
              } else {
                // 普通数组，作为文本显示
                this.html += `<div class="ml-8"><strong>${escapeHtml(
                  key
                )}:</strong> ${escapeHtml(JSON.stringify(value))}</div>`;
              }
            } else if (typeof value === "object" && value !== null) {
              // 如果是对象，递归调用 renderNestedObject
              this.html += `<div class="ml-8"><strong>${escapeHtml(
                key
              )}:</strong></div>`;
              this.renderNestedObject(value);
            } else {
              // 基本类型，直接显示
              this.html += `<div class="ml-8"><strong>${escapeHtml(
                key
              )}:</strong> ${escapeHtml(String(value))}</div>`;
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
            key
          )}:</strong></div>`;
          this.renderArrayOfObjects(value);
        } else {
          // 普通数组，作为文本显示
          this.html += `<div class="ml-12"><strong>${escapeHtml(
            key
          )}:</strong> ${escapeHtml(JSON.stringify(value))}</div>`;
        }
      } else if (typeof value === "object" && value !== null) {
        // 如果是对象，继续递归
        this.html += `<div class="ml-12"><strong>${escapeHtml(
          key
        )}:</strong></div>`;
        this.renderNestedObject(value);
      } else {
        // 基本类型，直接显示
        this.html += `<div class="ml-12"><strong>${escapeHtml(
          key
        )}:</strong> ${escapeHtml(String(value))}</div>`;
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
