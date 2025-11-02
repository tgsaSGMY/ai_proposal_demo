import { Document, Packer, AlignmentType, Paragraph, TextRun } from "docx";
import { DocxRenderer } from "../contentRenderer";

export async function exportPlanToWordMarketingImdp(
  sections: { id: string; name: string; json_schema: any }[],
  planContent: Record<string, any>
) {
  const docxRenderer = new DocxRenderer();

  for (const section of sections) {
    const sectionData = planContent[section.id]?.content;

    if (!sectionData) {
      continue;
    }

    switch (section.id) {
      case "company_overview_imdp":
        renderCompanyOverview(sectionData);
        break;
      case "plan_content_and_implementation":
        renderPlanContentAndImplementation(sectionData);
        break;
      case "feasibility_analysis":
        renderFeasibilityAnalysis(sectionData);
        break;
      case "project_objectives":
        renderProjectObjectives(sectionData);
        break;
      case "execution_schedule_and_checkpoints":
        renderExecutionSchedule(sectionData);
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
  link.download = "海外市場開發計劃書.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  function renderCompanyOverview(data: any) {
    const titleParagraph = new Paragraph({
      children: [
        new TextRun({
          text: "完整內容",
          font: "DFKai-SB",
          size: 36,
          bold: true,
        }),
      ],
      spacing: { before: 100, after: 100, line: 200 },
      alignment: AlignmentType.CENTER,
    });
    docxRenderer.addCustomParagraph(titleParagraph);
    docxRenderer.addSectionTitle("壹、公司概況");

    if (data.公司簡介) {
      renderTextWithLineBreaks(data.公司簡介);
    }

    if (data.布建海外通路策略) {
      docxRenderer.addArrayTitle("布建海外通路策略");
      const strategy = data.布建海外通路策略;
      if (strategy.海外通路據點及分佈) {
        docxRenderer.addArrayTitle("海外通路據點及分佈");
        renderTextWithLineBreaks(strategy.海外通路據點及分佈);
      }
      if (strategy.過去布建海外通路策略) {
        docxRenderer.addArrayTitle("過去布建海外通路策略");
        renderTextWithLineBreaks(strategy.過去布建海外通路策略);
      }
    }
  }

  function renderPlanContentAndImplementation(data: any) {
    docxRenderer.addSectionTitle("貳、計畫內容與實施方法");

    if (Array.isArray(data.計畫背景說明) && data.計畫背景說明.length > 0) {
      docxRenderer.addArrayTitle("計畫背景說明");
      data.計畫背景說明.forEach((item: any, index: number) => {
        const title = item?.標題
          ? `${index + 1}. ${item.標題}`
          : `項目 ${index + 1}`;
        docxRenderer.addArrayTitle(title);
        renderTextWithLineBreaks(item?.文字敘述 || "");
      });
    }

    if (data.解決方案 && data.解決方案.敘述) {
      docxRenderer.addArrayTitle("營銷策略");
      if (data.解決方案.敘述) {
        renderTextWithLineBreaks(data.解決方案.敘述);
      }

      const projects = data.解決方案.項目;
      if (Array.isArray(projects) && projects.length > 0) {
        docxRenderer.addArrayTitle("具體方案項目");
        projects.forEach((item: any, index: number) => {
          const label = item?.項目
            ? `${index + 1}. ${item.項目}`
            : `項目 ${index + 1}`;
          docxRenderer.addArrayTitle(label);
          renderTextWithLineBreaks(item?.文字敘述 || "");
        });
      }
    }
  }

  function renderFeasibilityAnalysis(data: any) {
    docxRenderer.addSectionTitle("參、可行性分析");

    if (Array.isArray(data.計劃可行性分析) && data.計劃可行性分析.length > 0) {
      docxRenderer.addArrayTitle("計劃可行性分析");
      data.計劃可行性分析.forEach((item: any, index: number) => {
        const title = item?.標題
          ? `${index + 1}. ${item.標題}`
          : `項目 ${index + 1}`;
        docxRenderer.addArrayTitle(title);
        renderTextWithLineBreaks(item?.文字敘述 || "");
      });
    }

    if (data.SWOT分析) {
      const swot = data.SWOT分析;
      docxRenderer.addArrayTitle("SWOT分析");

      // SWOT 2x2 表格
      const swotHeaders = ["Strength優勢", "Weakness劣勢"];
      const swotRows = [
        [safeText(swot.優勢) || "", safeText(swot.劣勢) || ""],
        ["Opportunity機會", "Threat威脅"],
        [safeText(swot.機會) || "", safeText(swot.威脅) || ""],
      ];

      docxRenderer.addTable(swotHeaders, swotRows);
    }

    if (data.五力分析) {
      const fiveForces = data.五力分析;
      docxRenderer.addArrayTitle("五力分析");
      const fiveForceRows = [
        ["潛在競爭者威脅", safeText(fiveForces.潛在競爭者威脅)],
        ["供應商議價能力", safeText(fiveForces.供應商議價能力)],
        ["現有競爭者競爭強度", safeText(fiveForces.現有競爭者競爭強度)],
        ["買方議價能力", safeText(fiveForces.買方議價能力)],
        ["替代品威脅", safeText(fiveForces.替代品威脅)],
      ];
      docxRenderer.addTable(["分析面向", "說明"], fiveForceRows);
    }
  }

  function renderProjectObjectives(data: any) {
    docxRenderer.addSectionTitle("肆、計畫目標");

    // 說明文字
    docxRenderer.addParagraph(
      "說明透過本補助案之執行，欲達成之長短期目標，及可連結效益之目標。"
    );

    // 短期目標和長期目標表格
    if (
      (data.短期目標 && data.短期目標.目標) ||
      (data.長期目標 && data.長期目標.目標)
    ) {
      const headers = [
        "目標",
        "目標（根據實際執行情境以下為範例）",
        "連結策略",
      ];
      const rows: string[][] = [];

      // 短期目標行
      if (data.短期目標) {
        rows.push([
          "短期目標",
          safeText(data.短期目標.目標),
          safeText(data.短期目標.連結策略),
        ]);
      }

      // 長期目標行
      if (data.長期目標) {
        rows.push([
          "長期目標",
          safeText(data.長期目標.目標),
          safeText(data.長期目標.連結策略),
        ]);
      }

      docxRenderer.addTable(headers, rows);
    }

    if (data.實施策略與實施方法) {
      const execution = data.實施策略與實施方法;
      docxRenderer.addArrayTitle("實施策略與實施方法");

      // 第一部分：計劃架構表格（含策略重點）
      docxRenderer.addArrayTitle(
        "（一）計畫架構：請用樹狀圖表達，並依申請類別別填寫適用架構"
      );
      if (Array.isArray(execution.分項計劃) && execution.分項計劃.length > 0) {
        renderPlanArchitectureTree(execution.分項計劃, execution.計劃名字);

        docxRenderer.addArrayTitle(
          "(二)分項計畫：請依計畫架構之分項計畫說明其策略重點"
        );

        const planHeaders = ["編號", "分項計劃", "策略重點"];
        const planRows = execution.分項計劃.map(
          (plan: any, planIndex: number) => {
            const planNumber = String(planIndex + 1);
            const planName = safeText(plan?.分項計劃名字);
            const baseLabel = String.fromCharCode(65 + planIndex); // A, B, C ...
            let strategyLines: string[] = [];

            if (Array.isArray(plan?.細項) && plan.細項.length > 0) {
              strategyLines = plan.細項.map(
                (detail: any, detailIndex: number) => {
                  const detailLabel = `${baseLabel}${detailIndex + 1}`;
                  const detailName = safeText(detail?.細項名字);
                  const detailStrategy = safeText(detail?.策略重點);

                  const namePart = detailName ? ` ${detailName}` : "";
                  const strategyPart = detailStrategy
                    ? `\n${detailStrategy}`
                    : "";
                  return `${detailLabel}${namePart}${strategyPart}`.trim();
                }
              );
            }

            return [planNumber, planName, strategyLines.join("\n\n")];
          }
        );

        docxRenderer.addTable(planHeaders, planRows);

        // 新增工作項目表格
        docxRenderer.addArrayTitle(
          "（三）工作項目：請依計畫架構之工作項目說明其具體作法"
        );

        const workHeaders = ["編號", "工作項目", "具體作法"];
        const workRows: string[][] = [];

        execution.分項計劃.forEach((plan: any, planIndex: number) => {
          const baseLabel = String.fromCharCode(65 + planIndex);
          if (Array.isArray(plan?.細項) && plan.細項.length > 0) {
            plan.細項.forEach((detail: any, detailIndex: number) => {
              const detailLabel = `${baseLabel}${detailIndex + 1}`;
              workRows.push([
                detailLabel,
                safeText(detail?.細項名字),
                safeText(detail?.具體作法),
              ]);
            });
          }
        });

        if (workRows.length > 0) {
          docxRenderer.addTable(workHeaders, workRows);
        }
      }

      docxRenderer.addSectionTitle("伍、計畫執行時程及查核點");
      if (Array.isArray(execution.分項計劃) && execution.分項計劃.length > 0) {
        docxRenderer.addArrayTitle("(一)預定進度表及預定查核點說明");
        const workcheckHeaders = [
          "編號",
          "工作項目",
          "計畫權重%",
          "預定開始時間",
          "預定完成時間",
          "查核點內容及數量",
        ];
        const workcheckRows: string[][] = [];

        execution.分項計劃.forEach((plan: any, planIndex: number) => {
          const baseLabel = String.fromCharCode(65 + planIndex);
          if (Array.isArray(plan?.細項) && plan.細項.length > 0) {
            plan.細項.forEach((detail: any, detailIndex: number) => {
              const detailLabel = `${baseLabel}${detailIndex + 1}`;
              workcheckRows.push([
                detailLabel,
                safeText(detail?.細項名字),
                safeText(detail?.占比),
                safeText(detail?.預定開始時間),
                safeText(detail?.預定完成時間),
                safeText(detail?.查核點內容及數量),
              ]);
            });
          }
        });

        if (workcheckRows.length > 0) {
          docxRenderer.addTable(workcheckHeaders, workcheckRows);
        }
      }
    }

    function renderPlanArchitectureTree(plans: any[], rootName?: string) {
      // 生成樹狀圖文字表示
      const treeLines: string[] = [];

      // 主計劃名稱（根）
      treeLines.push(rootName ? safeText(rootName) : "計劃根名");

      plans.forEach((plan: any, planIndex: number) => {
        const planLabel = String.fromCharCode(65 + planIndex); // A, B, C, D...
        const planName = plan?.分項計劃名字 || `${planLabel} 分項計劃`;

        // 主分項（一級）
        treeLines.push(`├─ ${planLabel} 分項計劃 ${planName}`);

        // 細項（二級）
        if (Array.isArray(plan?.細項)) {
          plan.細項.forEach((detail: any, detailIndex: number) => {
            const detailLabel = `${planLabel}${detailIndex + 1}`; // A1, A2, B1...
            const detailName = detail?.細項名字 || `細項 ${detailIndex + 1}`;
            const ratio = detail?.占比 ? `（${detail.占比}）` : "";
            const isLast =
              detailIndex === plan.細項.length - 1 &&
              planIndex === plans.length - 1;

            if (detailIndex === plan.細項.length - 1) {
              treeLines.push(`│  └─ ${detailLabel} ${detailName}${ratio}`);
            } else {
              treeLines.push(`│  ├─ ${detailLabel} ${detailName}${ratio}`);
            }
          });
        }

        // 主分項之間的連接線
        if (planIndex < plans.length - 1) {
          treeLines.push("│");
        }
      });

      // 渲染為段落
      treeLines.forEach((line) => {
        docxRenderer.addParagraph(line);
      });
    }
  }

  function renderExecutionSchedule(data: any) {
    if (Array.isArray(data.海外據點規劃表) && data.海外據點規劃表.length > 0) {
      docxRenderer.addArrayTitle("(二)海外據點規劃表");
      const headers = ["據點名稱", "設立月份", "國家", "城市", "簡述", "經費"];
      const rows = data.海外據點規劃表.map((item: any) => [
        safeText(item?.據點名稱),
        safeText(item?.設立月份),
        safeText(item?.地點?.國家),
        safeText(item?.地點?.城市),
        safeText(item?.簡述),
        safeText(item?.經費),
      ]);
      docxRenderer.addTable(headers, rows);
    }

    if (Array.isArray(data.海外活動規劃表) && data.海外活動規劃表.length > 0) {
      docxRenderer.addArrayTitle("(三)海外活動規劃表");
      const headers = ["活動名稱", "舉辦月份", "國家", "城市", "簡述", "經費"];
      const rows = data.海外活動規劃表.map((item: any) => [
        safeText(item?.活動名稱),
        safeText(item?.舉辦月份),
        safeText(item?.地點?.國家),
        safeText(item?.地點?.城市),
        safeText(item?.簡述),
        safeText(item?.經費),
      ]);
      docxRenderer.addTable(headers, rows);
    }
  }

  function renderExpectedBenefits(data: any) {
    docxRenderer.addSectionTitle("陸、預期效益");

    if (data.量化效益) {
      docxRenderer.addArrayTitle("量化效益");
      renderTextWithLineBreaks(data.量化效益);
    }

    if (Array.isArray(data.質化效益) && data.質化效益.length > 0) {
      docxRenderer.addArrayTitle("質化效益");
      const qualHeaders = ["項目", "說明"];
      const qualRows = data.質化效益.map((item: any, index: number) => [
        safeText(item?.項目) || `項目 ${index + 1}`,
        safeText(item?.說明),
      ]);
      docxRenderer.addTable(qualHeaders, qualRows);
    }

    if (
      Array.isArray(data.風險評估與因應對策) &&
      data.風險評估與因應對策.length > 0
    ) {
      docxRenderer.addArrayTitle("風險評估與因應對策");
      const headers = ["風險内容", "因應對策"];
      const rows = data.風險評估與因應對策.map((item: any) => [
        safeText(item?.風險評估),
        safeText(item?.因應對策),
      ]);
      docxRenderer.addTable(headers, rows);
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
          font: "DFKai-SB",
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

  function safeText(value: any): string {
    if (value === null || value === undefined) {
      return "";
    }
    return String(value).trim();
  }
}
