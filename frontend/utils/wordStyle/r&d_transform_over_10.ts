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

export async function exportPlanToWordRdTransformOver10(
  sections: { id: string; name: string; json_schema: any }[],
  planContent: Record<string, any>
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
      case "applicant_intro_rt_l":
        renderApplicantIntro(sectionData, docxRenderer);
        break;
      case "transformation_motivation_rt_l":
        renderTransformationMotivation(sectionData, docxRenderer);
        break;
      case "carbon_reduction_and_intelligence_status_rt_l":
        renderCarbonAndIntelligenceStatus(sectionData, docxRenderer);
        break;
      case "implementation_method_rt_l":
        renderImplementationMethod(sectionData, docxRenderer);
        break;
      case "equipment_plan_rt_l":
        renderEquipmentPlan(sectionData, docxRenderer);
        break;
      case "expected_benefits_rt_l":
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
  link.download = "十人以上轉型計劃書.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// 壹、申請業者簡介
function renderApplicantIntro(data: any, renderer: ContentRenderer<any>) {
  const title = "完整內容";
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
  renderer.addSectionTitle("壹、申請業者簡介");

  if (data.申請業者簡介) {
    renderTextWithLineBreaks(data.申請業者簡介, renderer);
  }
}

// 貳、升級轉型動機
function renderTransformationMotivation(
  data: any,
  renderer: ContentRenderer<any>
) {
  renderer.addSectionTitle("貳、升級轉型動機");

  if (data.升級轉型背景) {
    renderer.addArrayTitle("升級轉型背景");
    renderTextWithLineBreaks(data.升級轉型背景, renderer);
  }

  if (data.現況闡述) {
    renderer.addArrayTitle("現況闡述");
    renderTextWithLineBreaks(data.現況闡述, renderer);
  }

  if (data.改善方向與規劃) {
    renderer.addArrayTitle("改善方向與規劃");
    renderTextWithLineBreaks(data.改善方向與規劃, renderer);
  }

  if (data.預期效益) {
    renderer.addArrayTitle("預期效益");
    renderTextWithLineBreaks(data.預期效益, renderer);
  }
}

// 參、低碳化或智慧化現況
function renderCarbonAndIntelligenceStatus(
  data: any,
  renderer: ContentRenderer<any>
) {
  renderer.addSectionTitle("參、低碳化或智慧化現況");

  if (data.低碳化或智慧化現況) {
    renderTextWithLineBreaks(data.低碳化或智慧化現況, renderer);
  }
}

// 肆、推動作法
function renderImplementationMethod(data: any, renderer: ContentRenderer<any>) {
  renderer.addSectionTitle("肆、推動作法");

  // 構建主表格數據
  if (data.分項計劃 && Array.isArray(data.分項計劃)) {
    data.分項計劃.forEach((plan: any, planIndex: number) => {
      // 分項計劃標題 - 使用計劃名稱
      const planName =
        plan.分項計劃名 || `第${String.fromCharCode(64 + planIndex + 1)}項計畫`;
      renderer.addArrayTitle(`${planName}- 分項計畫`);

      const headers = ["工作項目", "推動作法", "權重", "查核項目/完成日期"];
      const rows: string[][] = [];

      if (plan.工作重點 && Array.isArray(plan.工作重點)) {
        plan.工作重點.forEach((work: any) => {
          // 嘗試多種 key 名稱組合
          const weight = work["權重(%)"] || work.權重 || work["权重"] || "";
          const checkpoint =
            work["查核項目/完成日期"] ||
            work.查核項目完成日期 ||
            work["查核项目完成日期"] ||
            "";

          rows.push([
            work.工作項目 || "",
            work.推動作法 || "",
            weight ? `${weight}%` : "",
            checkpoint || "",
          ]);
        });
      }

      if (rows.length > 0) {
        renderer.addTable(headers, rows);
      }

      // 詳細說明
      if (plan.詳細說明) {
        renderer.addArrayTitle("詳細說明");
        renderTextWithLineBreaks(plan.詳細說明, renderer);
      }
    });
  }

  // 預期成果表格
  if (data.預期成果 && Array.isArray(data.預期成果)) {
    renderer.addArrayTitle("預期成果");
    const headers = ["改善前(現況)", "改善後(結案)"];
    const rows = data.預期成果.map((item: any) => [
      item["改善前(現況)"] || item["改善前（現況）"] || "",
      item["改善後(結案)"] || item["改善後（結案）"] || "",
    ]);
    renderer.addTable(headers, rows);
  }
}

// 伍、設備購置或改善規劃
function renderEquipmentPlan(data: any, renderer: ContentRenderer<any>) {
  renderer.addSectionTitle("伍、設備購置或改善規劃");

  // 一、全新設備購置
  if (data.全新設備購置 && Array.isArray(data.全新設備購置)) {
    renderer.addArrayTitle("一、全新設備購置");
    const headers = [
      "設備名稱(含品牌、型號)",
      "用途/規格(含智慧或低碳化效能)",
      "預估費用(千元)(不含稅)",
      "採購對象/產地",
    ];
    const rows = data.全新設備購置.map((equipment: any) => [
      equipment.設備名稱 || "",
      equipment["用途/規格"] || "",
      equipment["預估費用(千元)"] || "",
      equipment["採購對象/產地"] || "",
    ]);
    if (rows.length > 0) {
      renderer.addTable(headers, rows);
    }
  }

  // 二、既有設備改善
  if (data.既有設備改善 && Array.isArray(data.既有設備改善)) {
    renderer.addArrayTitle("二、既有設備改善");
    const headers = ["設備名稱", "改善重點", "預估費用", "委託對象"];
    const rows = data.既有設備改善.map((equipment: any) => [
      equipment.設備名稱 || "",
      equipment.改善重點 || "",
      equipment.預估費用 || "",
      equipment.委託對象 || "",
    ]);
    if (rows.length > 0) {
      renderer.addTable(headers, rows);
    }
  }

  // 三、材料費
  if (data.材料費 && Array.isArray(data.材料費)) {
    renderer.addArrayTitle("三、材料費");
    const headers = [
      "項目",
      "單位",
      "預估需求數量",
      "預估單價(千元)",
      "預估費用(千元)",
    ];
    const rows = data.材料費.map((item: any) => [
      item.項目 || "",
      item.單位 || "",
      item.預估需求數量 || "",
      item["預估單價(千元)"] || "",
      item["預估費用(千元)"] || "",
    ]);
    if (rows.length > 0) {
      renderer.addTable(headers, rows);
    }
  }
}

// 陸、預期效益
function renderExpectedBenefits(data: any, renderer: ContentRenderer<any>) {
  renderer.addSectionTitle("陸、預期效益");

  // 第一部分：經濟效益
  renderer.addArrayTitle("一、經濟效益");
  const economicBenefits = ["新增投資", "降低成本", "增加就業人數", "增加產值"];
  const economicTableHeaders = ["項目", "效益"];
  const economicTableRows: string[][] = [];

  for (const key of economicBenefits) {
    if (data[key]) {
      const benefit = data[key];
      let benefitValue = benefit.效益 ? String(benefit.效益) : "";

      // 為特定項目添加單位
      if (key === "增加就業人數") {
        if (benefitValue && !benefitValue.includes("人")) {
          benefitValue = benefitValue + "人";
        }
      } else if (["新增投資", "降低成本", "增加產值"].includes(key)) {
        if (benefitValue && !benefitValue.includes("千元")) {
          benefitValue = benefitValue + "千元";
        }
      }

      economicTableRows.push([key, benefitValue]);
    }
  }

  if (economicTableRows.length > 0) {
    renderer.addTable(economicTableHeaders, economicTableRows);
  }

  // 經濟效益詳細解釋
  for (const key of economicBenefits) {
    if (data[key] && data[key].解釋) {
      renderer.addArrayTitle(key);
      renderTextWithLineBreaks(data[key].解釋, renderer);
    }
  }

  // 第二部分：技術效益
  renderer.addArrayTitle("二、技術效益");

  // （一）低碳化
  renderer.addArrayTitle("（一）低碳化");
  const lowCarbonBenefits = [
    "減少碳排放量",
    "減少用電量",
    "減少用水量",
    "減少天然氣用量",
  ];
  const lowCarbonTableHeaders = ["項目", "效益"];
  const lowCarbonTableRows: string[][] = [];

  for (const key of lowCarbonBenefits) {
    if (data[key]) {
      const benefit = data[key];
      lowCarbonTableRows.push([key, benefit.效益 ? String(benefit.效益) : ""]);
    }
  }

  if (lowCarbonTableRows.length > 0) {
    renderer.addTable(lowCarbonTableHeaders, lowCarbonTableRows);
  }

  // 低碳化詳細解釋
  for (const key of lowCarbonBenefits) {
    if (data[key] && data[key].解釋) {
      renderer.addArrayTitle(key);
      renderTextWithLineBreaks(data[key].解釋, renderer);
    }
  }

  // （二）智慧化
  renderer.addArrayTitle("（二）智慧化");
  const smartBenefits = [
    "整體設備效率OEE",
    "提升生產良率",
    "減少產線人力",
    "產品達交率",
  ];
  const smartTableHeaders = ["項目", "效益"];
  const smartTableRows: string[][] = [];

  for (const key of smartBenefits) {
    if (data[key]) {
      const benefit = data[key];
      smartTableRows.push([key, benefit.效益 ? String(benefit.效益) : ""]);
    }
  }

  if (smartTableRows.length > 0) {
    renderer.addTable(smartTableHeaders, smartTableRows);
  }

  // 智慧化詳細解釋
  for (const key of smartBenefits) {
    if (data[key] && data[key].解釋) {
      renderer.addArrayTitle(key);
      renderTextWithLineBreaks(data[key].解釋, renderer);
    }
  }
}

/**
 * 確保表格行中的所有值都是字符串
 */
function ensureStringArray(row: any[]): string[] {
  return row.map((cell) => (cell ? String(cell).trim() : ""));
}

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
