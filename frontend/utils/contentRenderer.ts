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
          font: "PMingLiU",
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
            font: "DFKai-SB",
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
            font: "DFKai-SB",
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
            font: "DFKai-SB",
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
                      font: "微軟正黑體",
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

    if (!text) {
      paragraphs.push(new Paragraph({ text: "" }));
      return paragraphs;
    }

    // 先將多個換行符（2個以上）統一替換為雙換行符
    const normalizedText = text.replace(/\n{2,}/g, "\n\n");
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
          const imagePattern = /【圖：[^】]+】/g;
          if (imagePattern.test(line)) {
            // 重置正則表達式
            imagePattern.lastIndex = 0;
            const parts = line.split(/【圖：[^】]+】/);
            const images = line.match(/【圖：[^】]+】/g) || [];

            // 構建混合段落
            const children: TextRun[] = [];
            for (let i = 0; i < parts.length; i++) {
              if (parts[i]) {
                children.push(
                  new TextRun({
                    text: parts[i],
                    font: "微軟正黑體",
                    size: 20,
                    bold: isHeader,
                  })
                );
              }
              if (i < images.length) {
                children.push(
                  new TextRun({
                    text: images[i],
                    font: "微軟正黑體",
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
                    font: "微軟正黑體",
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
    this.html += `<p><strong class="font-semibold">${escapeHtml(
      key
    )}:</strong> ${escapeHtml(value)}</p>`;
  }

  addParagraph(text: string): void {
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
      )}：</strong>${escapeHtml(content.description)}</p>`;
    } else {
      this.html += `<p><span class="mr-2">${index}.</span>${escapeHtml(
        content
      )}</p>`;
    }
  }

  addIndentedListItem(key: string, value: string): void {
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
