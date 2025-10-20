import { Paragraph, TextRun, HeadingLevel } from "docx";

// 渲染器的通用介面
export interface ContentRenderer<T> {
  addSectionTitle(text: string): void;
  addArrayTitle(text: string): void;
  addKeyValue(key: string, value: string): void;
  addParagraph(text: string): void;
  // 處理數組項目，可以是簡單字串或 title/desc 物件
  addNumberedListItem(
    index: number,
    content: string | { title: string; description: string }
  ): void;
  addIndentedListItem(key: string, value: string): void;
  // 取得最終結果
  getResult(): T;
}

export class DocxRenderer implements ContentRenderer<Paragraph[]> {
  private paragraphs: Paragraph[] = [];

  addSectionTitle(text: string): void {
    this.paragraphs.push(
      new Paragraph({
        text: text,
        heading: HeadingLevel.HEADING_2,
        spacing: { before: 400, after: 200 },
        style: "SectionHeading",
      })
    );
  }

  addArrayTitle(text: string): void {
    this.paragraphs.push(
      new Paragraph({
        children: [new TextRun({ text })],
        spacing: { before: 200, after: 100 },
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
        text: text,
        spacing: { after: 200 },
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
        new TextRun({ text: `${index}. ` }),
        new TextRun({ text: `${content.title}：${content.description}` }),
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

  getResult(): Paragraph[] {
    return this.paragraphs;
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

  getResult(): string {
    return this.html;
  }

  // HtmlRenderer 特有的方法
  addEmptyContentMessage(): void {
    this.html += `<p class="text-gray-500 italic my-4">（無內容）</p>`;
  }
}
