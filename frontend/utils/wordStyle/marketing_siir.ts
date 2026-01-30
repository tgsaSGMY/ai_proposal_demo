import {
  Document,
  Packer,
  AlignmentType,
  Paragraph,
  TextRun,
  Footer,
  PageNumber,
} from "docx";
import type { ContentRenderer } from "../contentRenderer";
import { DocxRenderer } from "../contentRenderer";
import { chineseNumbers, getParenthesizedNumber } from "../chineseNumbers";

export async function exportPlanToWordMarketingSiir(
  sections: { id: string; name: string; json_schema: any }[],
  planContent: Record<string, any>,
  projectTitle?: string,
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
      case "company_overview_domestic":
        renderCompanyOverview(sectionData, docxRenderer, projectTitle);
        break;
      case "randd_content_domestic":
        renderRdContent(sectionData, docxRenderer);
        break;
      case "project_objectives_domestic":
        renderProjectObjectives(sectionData, docxRenderer);
        break;
      case "innovation_and_validation_domestic":
        renderInnovationContent(sectionData, docxRenderer);
        break;
      case "feasibility_analysis_domestic":
        renderFeasibilityAnalysis(sectionData, docxRenderer);
        break;
      case "expected_benefits_domestic":
        renderBenefitsContent(sectionData, docxRenderer);
        break;
      case "execution_plan_and_checkpoints_transform":
        renderExecutionPlan(sectionData, docxRenderer);
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
            font: "Times New Roman",
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
            font: "Times New Roman",
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
            font: "Times New Roman",
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
            font: "Times New Roman",
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
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [
                  new TextRun({
                    children: [
                      PageNumber.CURRENT,
                      " / ",
                      PageNumber.TOTAL_PAGES,
                    ],
                  }),
                ],
              }),
            ],
          }),
        },
      },
    ],
  });

  const blob = await Packer.toBlob(doc);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = projectTitle ? `${projectTitle}.docx` : "SIIR計劃書.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// 公司概況
function renderCompanyOverview(
  data: any,
  renderer: ContentRenderer<any>,
  projectTitle?: string,
) {
  const title = projectTitle || "完整内容";
  const titleParagraph = new Paragraph({
    children: [
      new TextRun({
        text: title,
        font: "Times New Roman",
        size: 36,
        bold: true,
      }),
    ],
    spacing: { before: 100, after: 100, line: 200 },
    alignment: AlignmentType.CENTER,
  });
  renderer.addCustomParagraph(titleParagraph);
  renderer.addSectionTitle("壹、公司概況");

  if (data.公司概況敘述) {
    const text = data.公司概況敘述;
    renderTextWithLineBreaks(text, renderer);
  }
} // R&D 內容
function renderRdContent(data: any, renderer: ContentRenderer<any>) {
  renderer.addSectionTitle("貳、研發內容與執行說明");

  // 市場需求
  if (data.市場需求) {
    if (data.市場需求.標題) {
      renderer.addArrayTitle("一、" + data.市場需求.標題);
    }
    if (data.市場需求.文字敘述) {
      const text = data.市場需求.文字敘述;
      renderTextWithLineBreaks(text, renderer);
    }
  }

  // 動機
  if (data.動機 && Array.isArray(data.動機)) {
    renderer.addArrayTitle("二、動機");
    data.動機.forEach((item: any, index: number) => {
      renderer.addArrayTitle(`${index + 1}. ${item.標題}`);
      if (item.文字敘述) {
        renderTextWithLineBreaks(item.文字敘述, renderer);
      }
    });
  }
}

// 計劃目標
function renderProjectObjectives(data: any, renderer: ContentRenderer<any>) {
  renderer.addSectionTitle("參、計劃目標");

  if (data.導語) {
    renderTextWithLineBreaks(data.導語, renderer);
  }

  if (data.目標列表 && Array.isArray(data.目標列表)) {
    data.目標列表.forEach((item: any, index: number) => {
      const numberLabel = chineseNumbers[index] || "十";
      renderer.addArrayTitle(`${numberLabel}、${item.標題}`);
      if (item.敘述) {
        renderTextWithLineBreaks(item.敘述, renderer);
      }
    });
  }
}

// 創新技術與方案
function renderInnovationContent(data: any, renderer: ContentRenderer<any>) {
  renderer.addSectionTitle("肆、創新性及市場驗證規劃");

  if (data.導語) {
    renderTextWithLineBreaks(data.導語, renderer);
  }

  // 創新點
  if (data.創新點 && Array.isArray(data.創新點)) {
    renderer.addArrayTitle("一、創新技術");
    data.創新點.forEach((item: any, index: number) => {
      renderer.addArrayTitle(`${index + 1}. ${item.標題}`);
      if (item.敘述) {
        renderTextWithLineBreaks(item.敘述, renderer);
      }
    });
  }

  // 計畫導入前後對比
  if (data.計劃導入前後差異說明 && Array.isArray(data.計劃導入前後差異說明)) {
    renderer.addArrayTitle("二、計畫導入前後對比");
    const headers = ["目標項目", "現況", "創新計畫完成後現況"];
    const rows = data.計劃導入前後差異說明.map((item: any) => [
      item.目標項目,
      item.現況,
      item.創新計劃完成後現況,
    ]);
    renderer.addTable(headers, rows);
  }
}

// 可行性分析
function renderFeasibilityAnalysis(data: any, renderer: ContentRenderer<any>) {
  renderer.addSectionTitle("伍、可行性分析");

  // 競爭優勢分析
  if (data.競爭優勢分析) {
    renderer.addArrayTitle("一、競爭優勢分析");

    // SWOT 分析 - 表格格式
    if (data.競爭優勢分析.SWOT分析) {
      const swot = data.競爭優勢分析.SWOT分析;
      renderer.addArrayTitle("1. SWOT分析");

      // SWOT 2x2 表格，第一行是 header
      const swotHeaders = ["Strength優勢", "Weakness劣勢"];
      const swotRows = [
        [swot.優勢 || "", swot.劣勢 || ""],
        ["Opportunity機會", "Threat威脅"],
        [swot.機會 || "", swot.威脅 || ""],
      ];

      renderer.addTable(swotHeaders, swotRows);
    }

    // 五力分析 - 表格格式（只有當有非空數據時才顯示）
    if (data.競爭優勢分析.五力分析) {
      const fiveForces = data.競爭優勢分析.五力分析;

      // 檢查是否有任何非空的五力分析數據
      const hasData =
        fiveForces.現有競爭者競爭強度 ||
        fiveForces.潛在競爭者議價能力 ||
        fiveForces.替代品威脅 ||
        fiveForces.買方議價能力 ||
        fiveForces.供應商議價能力;

      if (hasData) {
        renderer.addArrayTitle("2. 五力分析");

        const fiveHeaders = ["標題", "說明"];
        const fiveRows = [
          ["現有競爭者競爭強度", fiveForces.現有競爭者競爭強度 || ""],
          ["潛在競爭者議價能力", fiveForces.潛在競爭者議價能力 || ""],
          ["替代品威脅", fiveForces.替代品威脅 || ""],
          ["買方議價能力", fiveForces.買方議價能力 || ""],
          ["供應商議價能力", fiveForces.供應商議價能力 || ""],
        ];

        renderer.addTable(fiveHeaders, fiveRows);
      }
    }
  }

  // 行銷計畫
  if (data.行銷計畫 && Array.isArray(data.行銷計畫)) {
    renderer.addArrayTitle("3. 行銷推廣計畫");
    data.行銷計畫.forEach((item: any, index: number) => {
      renderer.addArrayTitle(`${getParenthesizedNumber(index)} ${item.標題}`);
      if (item.敘述) {
        renderTextWithLineBreaks(item.敘述, renderer);
      }
    });
  }

  // 可行性評估
  if (data.可行性評估 && Array.isArray(data.可行性評估)) {
    renderer.addArrayTitle("4. 通路可行性評估");
    data.可行性評估.forEach((item: any, index: number) => {
      if (item.項目.includes("分駐點")) {
        renderer.addArrayTitle(`${getParenthesizedNumber(index)} ${item.項目}`);
        // 解析門市列表
        const stores = parseStoreList(item.可行性評估);
        stores.forEach((store: string) => {
          renderer.addIndentedListItem("門市", store);
        });
      } else {
        renderer.addArrayTitle(`${getParenthesizedNumber(index)} ${item.項目}`);
        if (item.可行性評估) {
          renderTextWithLineBreaks(item.可行性評估, renderer);
        }
      }
    });
  }
}

// 預期效益
function renderBenefitsContent(data: any, renderer: ContentRenderer<any>) {
  renderer.addSectionTitle("陸、預期效益");

  // 業績性量化效益
  if (data.業績性量化效益 && Array.isArray(data.業績性量化效益)) {
    renderer.addArrayTitle("一、業績性量化效益");
    const headers = ["項目", "效益"];
    const rows = data.業績性量化效益.map((item: any) => [item.項目, item.效益]);
    renderer.addTable(headers, rows);
  }

  // 策略性量化效益
  if (data.策略性量化效益 && Array.isArray(data.策略性量化效益)) {
    renderer.addArrayTitle("二、策略性量化效益");
    const headers = ["項目", "效益"];
    const rows = data.策略性量化效益.map((item: any) => [item.項目, item.效益]);
    renderer.addTable(headers, rows);
  }

  // 質化效益
  if (data.質化效益 && Array.isArray(data.質化效益)) {
    renderer.addArrayTitle("三、質化效益");
    data.質化效益.forEach((item: any, index: number) => {
      renderer.addArrayTitle(`${index + 1}. ${item.標題}`);
      if (item.敘述) {
        renderTextWithLineBreaks(item.敘述, renderer);
      }
    });
  }

  // 風險評估與因應對策
  if (data.風險評估與因應對策 && Array.isArray(data.風險評估與因應對策)) {
    renderer.addArrayTitle("四、風險評估與因應對策");
    const headers = ["風險", "因應對策"];
    const rows = data.風險評估與因應對策.map((item: any) => [
      item.風險,
      item.因應對策,
    ]);
    renderer.addTable(headers, rows);
  }
}

// 執行計劃與查核點
function renderExecutionPlan(data: any, renderer: ContentRenderer<any>) {
  renderer.addSectionTitle("柒、執行計畫：計畫架構預定查核點");

  // 計畫架構
  if (data.計畫架構 && Array.isArray(data.計畫架構)) {
    renderer.addArrayTitle("一、計畫架構：");
    const headers = ["分項代碼", "分項計畫", "執行單位", "計畫權重"];
    const rows = data.計畫架構.map((item: any) => [
      item.分項代碼,
      item.分項計畫,
      item.執行單位,
      item.計畫權重,
    ]);
    renderer.addTable(headers, rows);
  }

  // 查核點
  const checkpoints = data.預定查核點說明;
  if (checkpoints) {
    // 期中查核點
    if (checkpoints.期中查核點 && Array.isArray(checkpoints.期中查核點)) {
      renderer.addArrayTitle(
        "二、預定查核點說明(工作項目請依計畫內容自行增列)",
      );
      renderer.addArrayTitle("1. 年度結案期中查核點");
      const headers = ["查核點編號", "預定完成時間", "查核點內容", "權重(%)"];
      const rows = checkpoints.期中查核點.map((item: any) => [
        item.查核點編號,
        item.預定完成時間,
        item.查核點內容 || "",
        item.權重,
      ]);
      renderer.addTable(headers, rows);
    }

    // 期末查核點
    if (checkpoints.期末查核點 && Array.isArray(checkpoints.期末查核點)) {
      renderer.addArrayTitle("2. 年度結案期末查核點");
      const headers = ["查核點編號", "預定完成時間", "查核點內容", "權重(%)"];
      const rows = checkpoints.期末查核點.map((item: any) => [
        item.查核點編號,
        item.預定完成時間,
        item.查核點內容 || "",
        item.權重,
      ]);
      renderer.addTable(headers, rows);
    }
  }
}

// 輔助函數

function cleanLongText(text: string, maxLength: number): string {
  if (text.length > maxLength) {
    return text.substring(0, maxLength).replace(/\n/g, " ") + "...";
  }
  return text.replace(/\n/g, " ");
}

// 統一分行方法：單個\n分一行，多個\n統一分成兩行
function renderTextWithLineBreaks(
  text: string,
  renderer: ContentRenderer<any>,
): void {
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
    lines.forEach((line: string) => {
      if (line) {
        renderTextWithHighlightedImages(line, renderer);
      }
    });
  });
}

function renderTextWithHighlightedImages(
  text: string,
  renderer: ContentRenderer<any>,
): void {
  // 檢測圖片占位符，在原地highlight
  const imagePattern = /【圖[:：][^】]+】/g;
  if (imagePattern.test(text)) {
    // 重置正則表達式
    imagePattern.lastIndex = 0;
    const parts = text.split(/【圖[:：][^】]+】/);
    const images = text.match(/【圖[:：][^】]+】/g) || [];

    // 構建混合段落
    const children: TextRun[] = [];
    for (let i = 0; i < parts.length; i++) {
      if (parts[i]) {
        children.push(
          new TextRun({
            text: parts[i],
            font: "Times New Roman",
            size: 24,
          }),
        );
      }
      if (i < images.length) {
        children.push(
          new TextRun({
            text: images[i],
            font: "Times New Roman",
            size: 24,
            highlight: "yellow",
          }),
        );
      }
    }

    const mixedParagraph = new Paragraph({
      children: children,
      spacing: { after: 120, line: 200 },
    });
    renderer.addCustomParagraph(mixedParagraph);
  } else {
    renderer.addParagraph(text);
  }
}

function parseStoreList(text: string): string[] {
  // 分行店鋪信息通常包含：地址、電話等
  const lines = text.split("\n");
  const stores: string[] = [];
  let currentStore = "";

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // 如果是門市名稱或地址行
    if (
      trimmed.includes("地址") ||
      trimmed.includes("電話") ||
      trimmed.includes("門市") ||
      trimmed.includes("店")
    ) {
      if (currentStore) {
        stores.push(currentStore);
      }
      currentStore = trimmed;
    } else if (currentStore) {
      currentStore += " " + trimmed;
    }
  }

  if (currentStore) {
    stores.push(currentStore);
  }

  return stores.length > 0 ? stores : [text];
}
