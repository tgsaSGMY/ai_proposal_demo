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
  Footer,
  PageNumber,
} from "docx";
import { DocxRenderer } from "../contentRenderer";

export async function exportPlanToWordRdStandard(
  sections: { id: string; name: string; json_schema: any }[],
  planContent: Record<string, any>,
  projectTitle?: string
) {
  const docxRenderer = new DocxRenderer();

  // 添加project title在最上面
  if (projectTitle) {
    const titleParagraph = new Paragraph({
      children: [
        new TextRun({
          text: projectTitle,
          font: "Times New Roman",
          size: 36,
          bold: true,
        }),
      ],
      spacing: { before: 100, after: 100, line: 200 },
      alignment: AlignmentType.CENTER,
    });
    docxRenderer.addCustomParagraph(titleParagraph);
  }

  for (const section of sections) {
    const sectionData = planContent[section.id]?.content;

    if (!sectionData) {
      continue;
    }

    switch (section.id) {
      case "company_overview":
        renderCompanyOverviewRD(sectionData);
        break;
      case "rd_content_and_execution_description":
        renderRDContent(sectionData);
        break;
      case "feasibility_analysis":
        renderFeasibilityAnalysis(sectionData);
        break;
      case "objectives_innovation_specs":
        renderObjectivesAndInnovation(sectionData);
        break;
      case "execution_plan":
        renderExecutionPlan(sectionData);
        break;
      case "expected_benefits":
        renderExpectedBenefits(sectionData);
        break;
      default:
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
  link.download = projectTitle ? `${projectTitle}.docx` : "研發計畫書.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  function renderCompanyOverviewRD(data: any) {
    docxRenderer.addSectionTitle("壹、公司研發概況");

    // 企業現況
    if (data.企業現況) {
      docxRenderer.addArrayTitle("一、企業現況");
      renderTextWithLineBreaks(data.企業現況);
    }

    // 研發成果
    if (data.研發成果) {
      const rd = data.研發成果;
      if (
        (Array.isArray(rd.獎項) && rd.獎項.length > 0) ||
        (Array.isArray(rd.專利) && rd.專利.length > 0)
      ) {
        docxRenderer.addArrayTitle("二、研發成果");
      }

      const rdRows: string[][] = [];

      // 獎項
      if (Array.isArray(rd.獎項) && rd.獎項.length > 0) {
        rdRows.push(["獎項", "", `年度`, `獎項名稱`]);

        rd.獎項.forEach((item: any, awardIndex: number) => {
          const itemNum = String(awardIndex + 1);
          rdRows.push([
            "",
            itemNum,
            `${safeText(item?.年度)}`,
            `${safeText(item?.獎項名稱)}`,
          ]);
        });
      }

      // 專利
      if (Array.isArray(rd.專利) && rd.專利.length > 0) {
        rdRows.push(["專利", "", `國別/年度/類型/專利編號`, `專利名稱或內容`]);
        rd.專利.forEach((item: any, patentIndex: number) => {
          const itemNum = String(patentIndex + 1);
          const patentDetail = `${safeText(item?.國別)}/${safeText(
            item?.年度
          )}/${safeText(item?.類型)}/${safeText(item?.專利編號)}`;
          rdRows.push([
            "",
            itemNum,
            patentDetail,
            `${safeText(item?.專利名稱或內容)}`,
          ]);
        });
      }

      if (rdRows.length > 0) {
        const rdHeaders = ["項目", "", "成果項目", "成果細項說明"];
        docxRenderer.addTable(rdHeaders, rdRows);
      }
    }
  }

  function renderRDContent(data: any) {
    docxRenderer.addSectionTitle("貳、研發內容與執行說明");

    // 研發動機與說明
    if (data.研發動機與說明) {
      docxRenderer.addArrayTitle("一、研發動機與說明");
      renderTextWithLineBreaks(data.研發動機與說明);
    }
  }

  function renderFeasibilityAnalysis(data: any) {
    docxRenderer.addSectionTitle("參、可行性分析");

    // 創新研發標的
    if (data.創新研發標的) {
      docxRenderer.addArrayTitle("一、 創新研發標的");
      renderTextWithLineBreaks(data.創新研發標的);
    }

    // 競爭對手分析
    if (Array.isArray(data.競爭對手分析) && data.競爭對手分析.length > 0) {
      docxRenderer.addArrayTitle("二、 競爭對手分析");

      // 轉置表格：公司作為column，比較項目作為row
      const comparisonItems = [
        { key: "價格(單位：台幣)", label: "1. 價格(單位：台幣)" },
        { key: "產品/服務上市時間", label: "2. 產品/服務上市時間" },
        { key: "市場佔有率(%)", label: "3. 市場佔有率(%)" },
        { key: "市場區隔", label: "4. 市場區隔" },
        { key: "行銷通路", label: "5. 行銷通路" },
        { key: "技術或服務優勢", label: "6. 技術或服務優勢" },
      ];

      // Header: 比較項目 + 各公司名字
      const competitorHeaders = ["比較項目"].concat(
        data.競爭對手分析.map((item: any) => safeText(item?.競爭對手名稱))
      );

      // Rows: 每一行是一個比較項目，每列是一家公司的數據
      const competitorRows = comparisonItems.map((compItem) => {
        const row = [compItem.label];
        data.競爭對手分析.forEach((company: any) => {
          row.push(safeText(company?.[compItem.key]));
        });
        return row;
      });

      docxRenderer.addTable(competitorHeaders, competitorRows);
    }

    // 技術可行性
    if (data.技術可行性) {
      docxRenderer.addArrayTitle("三、 技術可行性");
      renderTextWithLineBreaks(data.技術可行性);
    }

    // 市場可行性
    if (data.市場可行性) {
      docxRenderer.addArrayTitle("四、 市場可行性");
      renderTextWithLineBreaks(data.市場可行性);
    }

    // 智慧財產權管理
    if (data.智慧財產權管理) {
      const ip = data.智慧財產權管理;
      docxRenderer.addArrayTitle("五、 智慧財產權管理");

      if (ip.說明) {
        docxRenderer.addArrayTitle("智慧財產權檢索與管理策略");
        renderTextWithLineBreaks(ip.說明);
      }

      if (
        Array.isArray(ip.智慧財產權檢索結果表) &&
        ip.智慧財產權檢索結果表.length > 0
      ) {
        docxRenderer.addArrayTitle("六、智慧財產權檢索結果表");
        const ipHeaders = ["專利號或關鍵字", "摘要", "差異分析"];
        const ipRows = ip.智慧財產權檢索結果表.map((item: any) => [
          safeText(item?.專利號或關鍵字),
          safeText(item?.摘要),
          safeText(item?.差異分析),
        ]);
        docxRenderer.addTable(ipHeaders, ipRows);
      }
    }

    // 風險評估與對策
    if (Array.isArray(data.風險評估與對策) && data.風險評估與對策.length > 0) {
      docxRenderer.addArrayTitle("七、風險評估與對策");
      const riskHeaders = ["風險描述", "因應對策"];
      const riskRows = data.風險評估與對策.map((item: any) => [
        safeText(item?.風險描述),
        safeText(item?.因應對策),
      ]);
      docxRenderer.addTable(riskHeaders, riskRows);
    }
  }

  function renderObjectivesAndInnovation(data: any) {
    docxRenderer.addSectionTitle("肆、目標、創新性與規格");

    // 研發目標
    if (Array.isArray(data.研發目標) && data.研發目標.length > 0) {
      docxRenderer.addArrayTitle("一、研發目標");
      const targetHeaders = ["比較面向", "導入前狀況", "導入後狀況"];
      const targetRows = data.研發目標.map((item: any) => [
        safeText(item?.比較面向),
        safeText(item?.導入前狀況),
        safeText(item?.導入後狀況),
      ]);
      docxRenderer.addTable(targetHeaders, targetRows);
    }

    // 創新性說明
    if (Array.isArray(data.創新性說明) && data.創新性說明.length > 0) {
      docxRenderer.addArrayTitle("二、創新性說明");
      data.創新性說明.forEach((item: any, index: number) => {
        const numbering = index + 1;
        const title = item?.標題 || `創新項目 ${numbering}`;
        docxRenderer.addArrayTitle(`${numbering}. ${title}`);
        renderTextWithLineBreaks(item?.說明 || "");
      });
    }

    // 功能規格與服務模式
    if (
      Array.isArray(data.功能規格與服務模式) &&
      data.功能規格與服務模式.length > 0
    ) {
      docxRenderer.addArrayTitle("三、功能規格與服務模式");
      const specHeaders = ["技術指標", "說明"];
      const specRows = data.功能規格與服務模式.map((item: any) => [
        safeText(item?.指標名稱),
        safeText(item?.指標值或說明),
      ]);
      docxRenderer.addTable(specHeaders, specRows);
    }
  }

  function renderExecutionPlan(data: any) {
    docxRenderer.addSectionTitle("伍、執行方式");

    if (!Array.isArray(data.分項計畫列表) || data.分項計畫列表.length === 0) {
      return;
    }

    // （一）推動架構
    docxRenderer.addArrayTitle("一、推動架構：請以樹狀圖展竄");

    data.分項計畫列表.forEach((item: any, itemIndex: number) => {
      const planName = safeText(item?.分項計畫名);
      const planLabel = String.fromCharCode(65 + itemIndex); // A, B, C, ...
      const subItems = item?.細項 || [];

      // 計算此分項下所有細項的權重總和
      let totalWeight = 0;
      if (Array.isArray(subItems)) {
        subItems.forEach((subItem: any) => {
          const weightStr = safeText(subItem?.權重).replace("%", "");
          const weight = parseFloat(weightStr) || 0;
          totalWeight += weight;
        });
      }

      const weightDisplay = totalWeight > 0 ? `（${totalWeight}%）` : "";
      // 主分項標題 - 加粗
      const bulletTextRuns: TextRun[] = [
        // new TextRun({
        //   text: `• ${planLabel}. `,
        //   font: "DFKai-SB",
        //   size: 24,
        // }),
        new TextRun({
          text: `${planName}`,
          font: "Times New Roman",
          size: 24,
          bold: true,
        }),
        new TextRun({
          text: ` ${weightDisplay}`,
          font: "Times New Roman",
          size: 24,
        }),
      ];
      docxRenderer.addCustomParagraph(
        new Paragraph({
          children: bulletTextRuns,
          spacing: { line: 200, after: 120 },
        })
      );

      // 細項列表（子項目）
      if (Array.isArray(subItems) && subItems.length > 0) {
        subItems.forEach((subItem: any, subIndex: number) => {
          const subItemName = safeText(subItem?.細項名稱);
          const subItemWeight = safeText(subItem?.權重);
          const subLabel = `${planLabel}${subIndex + 1}`;
          const subBulletText = `  ◦ ${subLabel}. ${subItemName} （${subItemWeight}）`;
          docxRenderer.addParagraph(subBulletText);
        });
      }
    });

    // （二）執行計畫、時程及執行進度
    docxRenderer.addArrayTitle("二、執行計畫、時程及執行進度：");

    data.分項計畫列表.forEach((item: any, itemIndex: number) => {
      const planName = safeText(item?.分項計畫名);
      const planLabel = String.fromCharCode(65 + itemIndex); // A, B, C, ...

      // 分項名稱標題
      docxRenderer.addArrayTitle(`${planName}`);

      // （1）工作重點表
      if (Array.isArray(item?.細項) && item.細項.length > 0) {
        docxRenderer.addArrayTitle("1. 工作重點");

        const itemHeaders = ["工作項目", "推動作法", "權重", "查核項目"];
        const itemRows = item.細項.map((subItem: any, subIndex: number) => {
          const subLabel = `${planLabel}${subIndex + 1}`;
          return [
            `${subLabel}. ${safeText(subItem?.細項名稱)}`,
            safeText(subItem?.推動作法),
            safeText(subItem?.權重),
            safeText(subItem?.["查核項目或完成日期"]),
          ];
        });
        docxRenderer.addTable(itemHeaders, itemRows);
      }

      // （2）詳細說明
      if (item?.詳細說明) {
        docxRenderer.addArrayTitle("2. 詳細說明");
        renderTextWithLineBreaks(item.詳細說明);
      }
    });
  }

  function renderExpectedBenefits(data: any) {
    docxRenderer.addSectionTitle("陸、預期效益");

    // 量化效益
    if (data.量化效益) {
      const quantitative = data.量化效益;
      docxRenderer.addArrayTitle("一、量化效益");

      if (quantitative.摘要表) {
        const summary = quantitative.摘要表;

        const benefitItems = [
          { key: "增加產值_千元", label: "增加產值", unit: "千元" },
          {
            key: "產出新產品或服務數量",
            label: "產出新產品或服務數量",
            unit: "個",
          },
          {
            key: "衍生商品或服務數量",
            label: "衍生商品或服務數量",
            unit: "個",
          },
          { key: "投入研發費用_千元", label: "投入研發費用", unit: "千元" },
          { key: "促成投資額_千元", label: "促成投資額", unit: "千元" },
          { key: "降低成本_千元", label: "降低成本", unit: "千元" },
          { key: "增加就業人數", label: "增加就業人數", unit: "人" },
          { key: "成立新公司數量", label: "成立新公司數量", unit: "家" },
          { key: "發明專利數量", label: "發明專利數量", unit: "件" },
          {
            key: "新型或新式樣專利數量",
            label: "新型或新式樣專利數量",
            unit: "件",
          },
        ];

        // 準備表格數據
        const quantTableData: Array<{
          項目: string;
          數值: string;
          說明: string;
        }> = [];
        for (const item of benefitItems) {
          if (summary[item.key]) {
            const benefit = summary[item.key];
            quantTableData.push({
              項目: item.label,
              數值:
                safeText(benefit?.數值) + (item.unit ? ` ${item.unit}` : ""),
              說明: safeText(benefit?.說明),
            });
          }
        }

        // 構建 4*3 表格（4 行 3 列）
        while (quantTableData.length < 12) {
          quantTableData.push({ 項目: "", 數值: "", 說明: "" });
        }

        const quantTableRows: string[][] = [];

        // 分成 4 行，每行 3 個單元格
        for (let i = 0; i < 4; i++) {
          const row: string[] = [];
          for (let j = 0; j < 3; j++) {
            const index = i * 3 + j;
            const cellData = quantTableData[index];
            if (cellData && cellData.項目) {
              row.push(
                `${index + 1}. ${cellData.項目}\n${cellData.數值}
                `
              );
            } else {
              row.push("");
            }
          }
          quantTableRows.push(row);
        }

        if (quantTableRows.length > 0) {
          renderSimpleTable(quantTableRows);
        }

        // 量化效益下的詳細說明
        for (const item of benefitItems) {
          if (summary[item.key] && summary[item.key].說明) {
            docxRenderer.addArrayTitle(item.label);
            renderTextWithLineBreaks(summary[item.key].說明);
          }
        }
      }
    }

    // 質化效益
    if (Array.isArray(data.質化效益) && data.質化效益.length > 0) {
      docxRenderer.addArrayTitle("二、質化效益");
      data.質化效益.forEach((item: any, index: number) => {
        const numbering = index + 1;
        const title = item?.標題 || "質化效益";
        docxRenderer.addArrayTitle(`${numbering}. ${title}`);
        renderTextWithLineBreaks(item?.說明 || "");
      });
    }
  }

  function renderTextWithLineBreaks(text: string) {
    if (!text) return;

    const normalized = text.replace(/\n{2,}/g, "\n\n");
    const segments = normalized.split("\n\n");

    segments.forEach((segment) => {
      if (!segment.trim()) return;

      const lines = segment.split("\n");
      lines.forEach((line) => {
        const trimmed = line.trim();
        if (trimmed) {
          renderTextWithHighlightedImages(trimmed);
        }
      });
    });
  }

  function renderTextWithHighlightedImages(text: string) {
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
      docxRenderer.addParagraph(text);
      return;
    }

    const textRuns: TextRun[] = parts.map(
      (part) =>
        new TextRun({
          text: part.text,
          font: "Times New Roman",
          size: 24,
          highlight: part.isImage ? "yellow" : undefined,
        })
    );

    docxRenderer.addCustomParagraph(
      new Paragraph({
        children: textRuns,
        spacing: { line: 200, after: 120 },
      })
    );
  }

  /**
   * 創建不帶 header 的簡單表格（4*3 格式）
   */
  function renderSimpleTable(rows: string[][]): void {
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
                        font: "Times New Roman",
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

    docxRenderer.addCustomParagraph(table as any);
  }

  function safeText(value: any): string {
    if (value === null || value === undefined) {
      return "";
    }
    return String(value).trim();
  }
}
