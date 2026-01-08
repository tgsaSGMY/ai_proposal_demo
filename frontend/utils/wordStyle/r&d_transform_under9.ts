import {
  Document,
  Packer,
  AlignmentType,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
} from "docx";
import type { ContentRenderer } from "../contentRenderer";
import { DocxRenderer } from "../contentRenderer";

export async function exportPlanToWordRdTransformUnder9(
  sections: { id: string; name: string; json_schema: any }[],
  planContent: Record<string, any>,
  projectTitle?: string
) {
  const docxRenderer = new DocxRenderer();

  // 按照原計劃書順序渲染各個section
  for (const section of sections) {
    const sectionData = planContent[section.id]?.content;

    if (!sectionData) {
      continue;
    }

    // 根據section ID進行特殊處理
    switch (section.id) {
      case "company_overview_rt_s":
        renderCompanyOverview(sectionData, docxRenderer, projectTitle);
        break;
      case "plan_content_and_implementation_rt_s":
        renderPlanContentAndImplementation(sectionData, docxRenderer);
        break;
      case "expected_benefits_rt_s":
        renderExpectedBenefits(sectionData, docxRenderer);
        break;
    }
  }

  const paragraphs = docxRenderer.getResult();

  const doc = new Document({
    styles: {
      paragraphStyles: [
        {
          id: "Title",
          name: "Title",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: {
            font: "DFKai-SB",
            size: 36,
            bold: true,
            color: "000000",
          },
          paragraph: {
            spacing: { before: 0, after: 200, line: 200 },
            alignment: AlignmentType.CENTER,
          },
        },
        {
          id: "SectionHeading",
          name: "Section Heading",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: {
            font: "PMingLiU",
            size: 32,
            bold: true,
            color: "5a78ac",
          },
          paragraph: {
            spacing: { before: 240, after: 120, line: 200 },
          },
        },
        {
          id: "SubSectionHeading",
          name: "Sub Section Heading",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: {
            font: "DFKai-SB",
            size: 24,
            bold: true,
            color: "000000",
          },
          paragraph: {
            spacing: { before: 120, after: 100, line: 200 },
          },
        },
        {
          id: "Normal",
          name: "Normal",
          basedOn: "Normal",
          quickFormat: true,
          run: {
            font: "DFKai-SB",
            size: 24,
          },
          paragraph: {
            spacing: { line: 200, after: 120 },
          },
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
  link.download = projectTitle
    ? `${projectTitle}.docx`
    : "九人以下轉型計劃書.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// 公司概況
function renderCompanyOverview(
  data: any,
  renderer: ContentRenderer<any>,
  projectTitle?: string
) {
  const title = projectTitle || "完整内容";
  const titleParagraph = new Paragraph({
    children: [
      new TextRun({
        text: title,
        font: "DFKai-SB",
        size: 36,
        bold: true,
      }),
    ],
    spacing: { before: 100, after: 100, line: 200 },
    alignment: AlignmentType.CENTER,
  });
  renderer.addCustomParagraph(titleParagraph);
  renderer.addSectionTitle("壹、公司概況");

  if (data.公司概況) {
    renderTextWithLineBreaks(data.公司概況, renderer);
  }
}

// 計畫內容與實施方式
function renderPlanContentAndImplementation(
  data: any,
  renderer: ContentRenderer<any>
) {
  renderer.addSectionTitle("貳、計畫內容與實施方式");

  // 升級轉型動機
  if (data.升級轉型動機) {
    renderer.addArrayTitle("升級轉型動機");

    // 市場趨勢分析
    if (data.升級轉型動機.市場趨勢分析) {
      renderer.addArrayTitle("市場趨勢分析");
      renderTextWithLineBreaks(data.升級轉型動機.市場趨勢分析, renderer);
    }

    // 現況與相應問題
    if (data.升級轉型動機.現況與相應問題) {
      renderer.addArrayTitle("現況與相應問題");
      renderTextWithLineBreaks(data.升級轉型動機.現況與相應問題, renderer);
    }

    // 升級前後效益比較表
    if (data.升級轉型動機.升級前後效益比較表) {
      renderer.addArrayTitle("升級前後效益比較表");
      const tableData = data.升級轉型動機.升級前後效益比較表;
      if (Array.isArray(tableData)) {
        const headers = ["差異項目", "現況問題", "升級轉型重點", "改善重點"];
        const rows = tableData.map((item: any) => [
          item.差異項目 || "",
          item.現況問題 || "",
          item.升級轉型重點 || "",
          item.改善重點 || "",
        ]);
        renderer.addTable(headers, rows);
      }
    }

    // 產品服務介紹
    if (data.升級轉型動機.產品服務介紹) {
      renderer.addArrayTitle("產品服務介紹");
      renderTextWithLineBreaks(data.升級轉型動機.產品服務介紹, renderer);
    }
  }

  // 實施方式
  if (data.實施方式 && data.實施方式.分項計畫) {
    renderer.addArrayTitle("實施方式");
    const items = data.實施方式.分項計畫;
    if (Array.isArray(items)) {
      // 按分項計劃名 group
      const groupedByPlanName: Record<string, typeof items> = {};
      items.forEach((item: any) => {
        const planName = item.分項計劃名 || "未命名";
        if (!groupedByPlanName[planName]) {
          groupedByPlanName[planName] = [];
        }
        groupedByPlanName[planName].push(item);
      });

      // 為每個分項計劃建立表格
      Object.entries(groupedByPlanName).forEach(([planName, planItems]) => {
        // 分項計劃名作為標題
        renderer.addArrayTitle(planName);

        const headers = [
          "工作項目",
          "推動辦法",
          "查核項目",
          "完成日期",
          "權重",
        ];
        const rows = planItems.map((item: any) => [
          item.工作項目 || "",
          item.推動辦法 || "",
          item.查核項目 || "",
          item.完成日期 || "",
          item.權重 || "",
        ]);
        renderer.addTable(headers, rows);
      });
    }
  }
}

// 預期效益
function renderExpectedBenefits(data: any, renderer: ContentRenderer<any>) {
  renderer.addSectionTitle("參、預期效益");

  // 第一部分：量化效益（表格展示）
  const quantitativeBenefits = [
    "增加產值",
    "發明專利",
    "降低成本",
    "促成投資額",
    "成立新公司",
    "增加就業人數",
    "投入研發費用",
    "新型新式樣專利",
    "產出新產品或服務",
    "衍生商品或服務數",
  ];

  // 構建量化效益表格（4*3 的表格，每個單元格包含 項目 + 效應）
  renderer.addArrayTitle("一、量化效益");

  // 準備10個量化效益項目的數據
  const quantTableData: Array<{ 項目: string; 效應: string }> = [];
  for (const key of quantitativeBenefits) {
    if (data[key]) {
      const benefit = data[key];
      quantTableData.push({
        項目: key,
        效應: benefit.效應 || "",
      });
    }
  }

  // 構建 4*3 表格（4 行 3 列）
  // 先填充到 12 個項目（4*3）
  while (quantTableData.length < 12) {
    quantTableData.push({ 項目: "", 效應: "" });
  }

  const quantTableRows: string[][] = [];

  // 分成 4 行，每行 3 個單元格
  for (let i = 0; i < 4; i++) {
    const row: string[] = [];
    for (let j = 0; j < 3; j++) {
      const index = i * 3 + j;
      if (index < quantTableData.length) {
        const cellData = quantTableData[index];
        // 項目和效應合在一起
        if (cellData) {
          row.push(`${index + 1}. ${cellData.項目}\n${cellData.效應}`);
        } else {
          row.push("");
        }
      } else {
        row.push("");
      }
    }
    quantTableRows.push(row);
  }

  if (quantTableRows.length > 0) {
    // 直接創建不帶 header 的表格
    renderSimpleTable(quantTableRows, renderer);
  }

  // 量化效益下的詳細說明
  for (const key of quantitativeBenefits) {
    if (data[key] && data[key].附註說明) {
      renderer.addArrayTitle(key);
      renderTextWithLineBreaks(data[key].附註說明, renderer);
    }
  }

  // 第二部分：技術效益
  renderer.addArrayTitle("二、技術效益（低碳化或智慧化效益指標至少2項）");

  // （一）低碳化
  renderer.addArrayTitle("（一）低碳化");
  const lowCarbonBenefits = ["減少用電量", "減少碳排放量"];
  const lowCarbonTableHeaders = ["項目", "效益", "備註"];
  const lowCarbonTableRows: string[][] = [];

  for (const key of lowCarbonBenefits) {
    if (data[key]) {
      const benefit = data[key];
      lowCarbonTableRows.push([key, benefit.效益 || "", benefit.備註 || ""]);
    }
  }

  if (lowCarbonTableRows.length > 0) {
    renderer.addTable(lowCarbonTableHeaders, lowCarbonTableRows);
  }

  // 低碳化詳細說明
  // for (const key of lowCarbonBenefits) {
  //   if (data[key] && data[key].備註) {
  //     renderer.addArrayTitle(key);
  //     renderTextWithLineBreaks(data[key].備註, renderer);
  //   }
  // }

  // （二）智慧化
  renderer.addArrayTitle("（二）智慧化");
  const smartBenefits = [
    "整體設備效率OEE",
    "提升生產良率",
    "減少產線人力",
    "產品達交率",
  ];
  const smartTableHeaders = ["項目", "效益", "備註"];
  const smartTableRows: string[][] = [];

  for (const key of smartBenefits) {
    if (data[key]) {
      const benefit = data[key];
      smartTableRows.push([key, benefit.效益 || "", benefit.備註 || ""]);
    }
  }

  if (smartTableRows.length > 0) {
    renderer.addTable(smartTableHeaders, smartTableRows);
  }

  // 智慧化詳細說明
  // for (const key of smartBenefits) {
  //   if (data[key] && data[key].備註) {
  //     renderer.addArrayTitle(key);
  //     renderTextWithLineBreaks(data[key].備註, renderer);
  //   }
  // }
}

// ============ Helper Functions ============

/**
 * Render text with line breaks support
 * Single \n = separate line, Multiple \n = paragraph break
 */
function renderTextWithLineBreaks(
  text: string,
  renderer: ContentRenderer<any>
): void {
  if (!text) return;

  // Normalize multiple newlines to double
  let normalized = text.replace(/\n{2,}/g, "\n\n");

  // Split by double newlines (paragraph breaks)
  const segments = normalized.split("\n\n");

  segments.forEach((segment) => {
    if (!segment.trim()) return;

    // Split by single newlines (individual lines within paragraph)
    const lines = segment.split("\n");
    lines.forEach((line) => {
      const trimmed = line.trim();
      if (trimmed) {
        renderTextWithHighlightedImages(trimmed, renderer);
      }
    });
  });
}

/**
 * Render text with image placeholders highlighted in yellow
 * Image placeholder format: 【圖：...】
 */
function renderTextWithHighlightedImages(
  text: string,
  renderer: ContentRenderer<any>
): void {
  if (!text) return;

  const imagePattern = /【圖：[^】]+】/g;
  const parts: Array<{ text: string; isImage: boolean }> = [];
  let lastIndex = 0;
  let match;

  // Reset regex lastIndex
  imagePattern.lastIndex = 0;

  // Extract all image placeholders and their positions
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

  // If no images found, just add paragraph
  if (parts.length === 0 || parts.every((p) => !p.isImage)) {
    renderer.addParagraph(text);
    return;
  }

  // Create TextRun array with highlights
  const textRuns: TextRun[] = parts.map(
    (part) =>
      new TextRun({
        text: part.text,
        font: "DFKai-SB",
        size: 24,
        highlight: part.isImage ? "yellow" : undefined,
      })
  );

  renderer.addCustomParagraph(
    new Paragraph({
      children: textRuns,
      spacing: { line: 200, after: 120 },
    })
  );
}

/**
 * 創建不帶 header 的簡單表格（4*3 格式）
 */
function renderSimpleTable(
  rows: string[][],
  renderer: ContentRenderer<any>
): void {
  const tableRows: TableRow[] = [];

  rows.forEach((row) => {
    tableRows.push(
      new TableRow({
        children: row.map(
          (cell) =>
            new TableCell({
              children: [
                new Paragraph({
                  children: [
                    new TextRun({
                      text: cell,
                      font: "DFKai-SB",
                      size: 24,
                    }),
                  ],
                  spacing: { line: 200, after: 120 },
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

  renderer.addCustomParagraph(table as any);
}
