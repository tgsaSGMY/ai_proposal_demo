import { Document, Packer, AlignmentType, Paragraph, TextRun } from "docx";
import { DocxRenderer } from "../contentRenderer";

export async function exportPlanToWordLocalStandard(
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
      case "company_overview_local":
        renderCompanyOverview(sectionData);
        break;
      case "plan_content_and_methodology_local":
        renderPlanContent(sectionData);
        break;
      case "feasibility_analysis_local":
        renderFeasibilityAnalysis(sectionData);
        break;
      case "project_objectives_local":
        renderProjectObjectives(sectionData);
        break;
      case "schedule_and_checkpoints_local":
        renderScheduleAndCheckpoints(sectionData);
        break;
      case "expected_benefits_local":
        renderExpectedBenefits(sectionData);
        break;
      case "ip_analysis_local":
        renderIPAnalysis(sectionData);
        break;
      default:
        break;
    }
  }

  // 計畫執行查核點說明 - 使用 schedule_and_checkpoints_local 的數據
  const scheduleData = planContent["schedule_and_checkpoints_local"]?.content;
  if (scheduleData) {
    renderCheckpointsSummary(scheduleData);
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
  link.download = "地方型計畫書.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  function renderCompanyOverview(data: any) {
    docxRenderer.addSectionTitle("壹、公司概況");

    if (data.企業現況) {
      docxRenderer.addArrayTitle("企業現況");
      renderTextWithLineBreaks(data.企業現況);
    }

    if (data.經營理念) {
      docxRenderer.addArrayTitle("經營理念");
      renderTextWithLineBreaks(data.經營理念);
    }

    if (data.未來展望) {
      docxRenderer.addArrayTitle("未來展望");
      renderTextWithLineBreaks(data.未來展望);
    }

    // 研發成果
    if (data.研發成果) {
      const rd = data.研發成果;
      docxRenderer.addArrayTitle("研發成果");

      const rdRows: string[][] = [];
      let itemIndex = 1;

      // 獎項
      if (Array.isArray(rd.獎項) && rd.獎項.length > 0) {
        rdRows.push(["獎項", "", `年度`, `獎項名稱`]);

        rd.獎項.forEach((item: any, awardIndex: number) => {
          const itemNum = awardIndex === 0 ? String(itemIndex) : "";
          rdRows.push([
            "",
            itemNum,
            `${safeText(item?.年度)}`,
            `${safeText(item?.獎項名稱)}`,
          ]);
        });
        itemIndex++;
      }

      // 專利
      rdRows.push(["專利", "", `國別/年度/類型/專利編號`, `專利名稱或內容`]);
      if (Array.isArray(rd.專利) && rd.專利.length > 0) {
        rd.專利.forEach((item: any, patentIndex: number) => {
          const itemNum = patentIndex === 0 ? String(itemIndex) : "";
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

    // 曾經參與政府相關研發計畫之實績
    if (
      Array.isArray(data.曾經參與政府相關研發計畫之實績) &&
      data.曾經參與政府相關研發計畫之實績.length > 0
    ) {
      docxRenderer.addArrayTitle("曾經參與政府相關研發計畫之實績");
      const govHeaders = [
        "計畫類別",
        "計畫名稱",
        "執行期間",
        "政府補助款",
        "廠商自籌款",
        "計畫研發重點",
        "計畫投入人力",
        "預期績效(千元/人)",
        "實際達成績效(千元/人)",
      ];
      const govRows = data.曾經參與政府相關研發計畫之實績.map((item: any) => [
        safeText(item?.計畫類別),
        safeText(item?.計畫名稱),
        safeText(item?.執行期間),
        safeText(item?.政府補助款),
        safeText(item?.廠商自籌款),
        safeText(item?.計畫研發重點),
        safeText(item?.計畫投入人力),
        safeText(item?.["預期績效(千元/人)"]),
        safeText(item?.["實際達成績效(千元/人)"]),
      ]);
      docxRenderer.addTable(govHeaders, govRows);
    }
  }

  function renderPlanContent(data: any) {
    docxRenderer.addSectionTitle("貳、計畫內容與實施方法");

    // 研發動機
    if (data.研發動機) {
      const motivation = data.研發動機;
      docxRenderer.addArrayTitle("研發動機");

      if (motivation.文字敘述) {
        renderTextWithLineBreaks(motivation.文字敘述);
      }

      if (
        Array.isArray(motivation.痛點分析) &&
        motivation.痛點分析.length > 0
      ) {
        docxRenderer.addArrayTitle("痛點分析");
        motivation.痛點分析.forEach((item: any, index: number) => {
          const title = item?.標題
            ? `${index + 1}. ${item.標題}`
            : `項目 ${index + 1}`;
          docxRenderer.addArrayTitle(title);
          renderTextWithLineBreaks(item?.敘述 || "");
        });
      }

      if (motivation.解決方案服務) {
        docxRenderer.addArrayTitle("解決方案/自身服務");
        renderTextWithLineBreaks(motivation.解決方案服務);
      }
    }

    // 競爭力分析
    if (Array.isArray(data.競爭力分析) && data.競爭力分析.length > 0) {
      docxRenderer.addArrayTitle("競爭力分析");

      // 轉置表格：公司作為column，比較項目作為row
      const comparisonItems = [
        { key: "公司國家", label: "1. 公司國家" },
        { key: "價格結構", label: "2. 價格結構" },
        { key: "產品服務上綫時間", label: "3. 產品服務上綫時間" },
        { key: "市場占有率估計", label: "4. 市場占有率估計" },
        { key: "市場區隔", label: "5. 市場區隔" },
        { key: "行銷管道", label: "6. 行銷管道" },
        { key: "技術或服務優勢", label: "7. 技術或服務優勢" },
      ];

      // Header: 比較項目 + 各公司名字
      const competitorHeaders = ["比較項目"].concat(
        data.競爭力分析.map((item: any) => safeText(item?.公司名稱))
      );

      // Rows: 每一行是一個比較項目，每列是一家公司的數據
      const competitorRows = comparisonItems.map((compItem) => {
        const row = [compItem.label];
        data.競爭力分析.forEach((company: any) => {
          row.push(safeText(company?.[compItem.key]));
        });
        return row;
      });

      docxRenderer.addTable(competitorHeaders, competitorRows);
    }
  }

  function renderFeasibilityAnalysis(data: any) {
    docxRenderer.addSectionTitle("參、可行性分析");

    if (data.市場可行性) {
      docxRenderer.addArrayTitle("1. 市場可行性");
      renderTextWithLineBreaks(data.市場可行性);
    }

    if (data.技術與設計可行性) {
      docxRenderer.addArrayTitle("2. 技術與設計可行性");
      renderTextWithLineBreaks(data.技術與設計可行性);
    }

    if (data.執行能力可行性) {
      docxRenderer.addArrayTitle("3. 執行能力可行性");
      renderTextWithLineBreaks(data.執行能力可行性);
    }
  }

  function renderProjectObjectives(data: any) {
    docxRenderer.addSectionTitle("肆、計畫目標與規格");

    // 計畫目標
    if (Array.isArray(data.計畫目標) && data.計畫目標.length > 0) {
      docxRenderer.addArrayTitle("計畫目標");
      const targetHeaders = ["目標項目", "計劃前狀況", "計劃後狀況"];
      const targetRows = data.計畫目標.map((item: any, index: number) => [
        `${index + 1}. ${safeText(item?.目標項目)}`,
        safeText(item?.計劃前狀況),
        safeText(item?.計劃後狀況),
      ]);
      docxRenderer.addTable(targetHeaders, targetRows);
    }

    // 創新型說明
    if (Array.isArray(data.創新型說明) && data.創新型說明.length > 0) {
      docxRenderer.addArrayTitle("創新型說明");
      data.創新型說明.forEach((item: any, index: number) => {
        const title = item?.標題
          ? `${index + 1}. ${item.標題}`
          : `項目 ${index + 1}`;
        docxRenderer.addArrayTitle(title);
        renderTextWithLineBreaks(item?.說明 || "");
      });
    }

    // 功能規格/服務模式
    if (
      Array.isArray(data.功能規格_服務模式) &&
      data.功能規格_服務模式.length > 0
    ) {
      docxRenderer.addArrayTitle("功能規格/服務模式");
      const specHeaders = ["項目", "指標或規格", "功能與應用"];
      const specRows = data.功能規格_服務模式.map((item: any) => [
        safeText(item?.項目),
        safeText(item?.指標或規格),
        safeText(item?.功能與應用),
      ]);
      docxRenderer.addTable(specHeaders, specRows);
    }

    // 主要關鍵技術或服務、零組件及其來源
    if (
      Array.isArray(data.主要關鍵技術或服務_零組件及其來源) &&
      data.主要關鍵技術或服務_零組件及其來源.length > 0
    ) {
      docxRenderer.addArrayTitle("主要關鍵技術或服務、零組件及其來源");
      const techHeaders = ["主要關鍵技術或服務項目", "技術來源", "執行方式"];
      const techRows = data.主要關鍵技術或服務_零組件及其來源.map(
        (item: any) => [
          safeText(item?.主要關鍵技術或服務項目),
          safeText(item?.技術來源),
          safeText(item?.執行方式),
        ]
      );
      docxRenderer.addTable(techHeaders, techRows);
    }

    // 技術或服務應用範圍
    if (data.技術或服務應用範圍) {
      docxRenderer.addArrayTitle("技術或服務應用範圍");
      renderTextWithLineBreaks(data.技術或服務應用範圍);
    }

    // 衍生產品或服務
    if (Array.isArray(data.衍生產品或服務) && data.衍生產品或服務.length > 0) {
      docxRenderer.addArrayTitle("衍生產品或服務");
      const derivedHeaders = ["衍生產品類型", "說明"];
      const derivedRows = data.衍生產品或服務.map((item: any) => [
        safeText(item?.衍生產品類型),
        safeText(item?.說明),
      ]);
      docxRenderer.addTable(derivedHeaders, derivedRows);
    }
  }

  function renderScheduleAndCheckpoints(data: any) {
    docxRenderer.addSectionTitle("伍、計畫執行時程及查核點");

    // 執行步驟及方法
    if (Array.isArray(data.執行步驟及方法) && data.執行步驟及方法.length > 0) {
      docxRenderer.addArrayTitle("執行步驟及方法");
      const stepLabels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];

      data.執行步驟及方法.forEach((step: any, stepIndex: number) => {
        const stepTitle = step?.步驟名稱 || `步驟 ${stepIndex + 1}`;

        // 收集細分方法的執行單位
        const executionUnits: string[] = [];
        if (Array.isArray(step?.細分方法) && step.細分方法.length > 0) {
          step.細分方法.forEach((method: any) => {
            const unit = safeText(method?.執行單位);
            if (unit && !executionUnits.includes(unit)) {
              executionUnits.push(unit);
            }
          });
        }

        const unitText =
          executionUnits.length > 0 ? `(${executionUnits.join("+")})` : "";
        const stepLabel = stepLabels[stepIndex] || String(stepIndex + 1);
        docxRenderer.addArrayTitle(`${stepLabel}.${stepTitle}${unitText}`);

        // 細分方法以 bullet point 顯示
        if (Array.isArray(step?.細分方法) && step.細分方法.length > 0) {
          step.細分方法.forEach((method: any, methodIndex: number) => {
            const methodName = safeText(method?.細分名稱);
            const methodDesc = safeText(method?.說明);
            const bulletText = `${methodIndex + 1}. ${methodName}${
              methodDesc ? `：${methodDesc}` : ""
            }`;
            docxRenderer.addParagraph(bulletText);
          });
        }
      });
    }

    // 技術及智慧財產權說明
    if (
      Array.isArray(data.技術及智慧財產權說明) &&
      data.技術及智慧財產權說明.length > 0
    ) {
      docxRenderer.addArrayTitle("技術及智慧財產權說明");

      // 1. 技術及智慧財產權來源對象背景
      docxRenderer.addArrayTitle("1.技術及智慧財產權來源對象背景：");
      data.技術及智慧財產權說明.forEach((item: any) => {
        const 對象 = safeText(item?.對象);
        const 背景 = safeText(item?.背景);
        if (對象) {
          docxRenderer.addArrayTitle(`${對象}：`);
          if (背景) {
            renderTextWithLineBreaks(背景);
          }
        }
      });

      // 2. 技術來源對象之技術及智慧財產權能力
      docxRenderer.addArrayTitle("2.技術來源對象之技術及智慧財產權能力：");
      data.技術及智慧財產權說明.forEach((item: any) => {
        const 對象 = safeText(item?.對象);
        const 能力 = safeText(item?.能力);
        if (對象) {
          docxRenderer.addArrayTitle(`${對象}：`);
          if (能力) {
            renderTextWithLineBreaks(能力);
          }
        }
      });

      // 3. 於計畫工作執行項目與執行方法
      docxRenderer.addArrayTitle("3.於計畫工作執行項目與執行方法：");
      data.技術及智慧財產權說明.forEach((item: any) => {
        const 對象 = safeText(item?.對象);
        const 執行方法 = safeText(item?.執行方法);
        if (對象) {
          docxRenderer.addArrayTitle(`${對象}：`);
          if (執行方法) {
            renderTextWithLineBreaks(執行方法);
          }
        }
      });
    }
  }

  function renderExpectedBenefits(data: any) {
    docxRenderer.addSectionTitle("陸、預期效益");

    // 行銷策略
    if (data.行銷策略) {
      const marketing = data.行銷策略;
      docxRenderer.addArrayTitle("行銷策略");

      const marketingData: string[][] = [];
      if (marketing.產品)
        marketingData.push(["產品 (Product)", safeText(marketing.產品)]);
      if (marketing.價格)
        marketingData.push(["價格 (Price)", safeText(marketing.價格)]);
      if (marketing.通路)
        marketingData.push(["通路 (Place)", safeText(marketing.通路)]);
      if (marketing.推廣)
        marketingData.push(["推廣 (Promotion)", safeText(marketing.推廣)]);

      if (marketingData.length > 0) {
        docxRenderer.addTable(["項目", "說明"], marketingData);
      }
    }

    // 預期效益
    if (data.預期效益) {
      const benefits = data.預期效益;
      docxRenderer.addArrayTitle("預期效益");

      const benefitRows: string[][] = [];

      const benefitItems = [
        { key: "增加產值_千元", label: "產值", unit: "千元" },
        { key: "產出新產品或服務_項", label: "產出新產品或服務", unit: "項" },
        {
          key: "衍生商品或服務數共_項",
          label: "衍生商品或服務數共",
          unit: "項",
        },
        { key: "投入研發費用_千元", label: "投入研發費用", unit: "千元" },
        { key: "降低投資額_千元", label: "降低投資額", unit: "千元" },
        { key: "降低成本_千元", label: "降低成本", unit: "千元" },
        { key: "增加就業人數_人", label: "增加就業人數", unit: "人" },
        { key: "成立新公司_家", label: "成立新公司", unit: "家" },
        { key: "發明專利共_件", label: "發明專利共", unit: "件" },
        { key: "新增或新技術專利_件", label: "新增或新技術專利", unit: "件" },
        {
          key: "申請國內外研發或設計相關獎項_件",
          label: "申請國內外研發或設計相關獎項",
          unit: "件",
        },
        { key: "其他", label: "其他", unit: "" },
      ];

      benefitItems.forEach((item) => {
        if (benefits[item.key]) {
          const benefit = benefits[item.key];
          const 效益值 = safeText(benefit?.效益);
          const 說明值 = safeText(benefit?.說明);

          // 組合標題：標籤 + 效益值 + 單位
          const titleLabel = 效益值
            ? `${item.label}${效益值}${item.unit}`
            : `${item.label} ${item.unit}`;

          benefitRows.push([titleLabel, 說明值]);
        }
      });

      if (benefitRows.length > 0) {
        docxRenderer.addTable(["預期效益項目", "說明"], benefitRows);
      }
    }
  }

  function renderIPAnalysis(data: any) {
    docxRenderer.addSectionTitle("柒、智財分析");

    if (data.是否涉及他人智慧財產權) {
      docxRenderer.addArrayTitle("是否涉及他人智慧財產權");
      renderTextWithLineBreaks(data.是否涉及他人智慧財產權);
    }

    if (data.是否已掌握關鍵智慧財產權) {
      docxRenderer.addArrayTitle("是否已掌握關鍵智慧財產權");
      renderTextWithLineBreaks(data.是否已掌握關鍵智慧財產權);
    }
  }

  function renderCheckpointsSummary(data: any) {
    docxRenderer.addSectionTitle("捌、計畫執行查核點說明");

    // 預定進度表
    if (Array.isArray(data.執行步驟及方法) && data.執行步驟及方法.length > 0) {
      docxRenderer.addArrayTitle("預定進度表");

      const stepLabels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];
      const scheduleRows: string[][] = [];

      data.執行步驟及方法.forEach((step: any, stepIndex: number) => {
        if (Array.isArray(step?.細分方法) && step.細分方法.length > 0) {
          step.細分方法.forEach((method: any, methodIndex: number) => {
            const stepLabel = stepLabels[stepIndex] || String(stepIndex + 1);
            const detailedLabel = `${stepLabel}${methodIndex + 1}`;
            scheduleRows.push([
              detailedLabel,
              safeText(method?.細分名稱),
              safeText(method?.計劃權重),
              safeText(method?.預定投入人月),
              safeText(method?.預定開始時間),
              safeText(method?.預定結束時間),
            ]);
          });
        }
      });

      if (scheduleRows.length > 0) {
        const scheduleHeaders = [
          "步驟",
          "工作項目",
          "計劃權重%",
          "預定投入人月",
          "預定開始時間",
          "預定結束時間",
        ];
        docxRenderer.addTable(scheduleHeaders, scheduleRows);
      }
    }

    // 預定查核點說明
    if (Array.isArray(data.執行步驟及方法) && data.執行步驟及方法.length > 0) {
      docxRenderer.addArrayTitle("預定查核點說明");

      const stepLabels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];
      const checkpointRows: string[][] = [];

      data.執行步驟及方法.forEach((step: any, stepIndex: number) => {
        if (Array.isArray(step?.細分方法) && step.細分方法.length > 0) {
          step.細分方法.forEach((method: any, methodIndex: number) => {
            const stepLabel = stepLabels[stepIndex] || String(stepIndex + 1);
            const detailedLabel = `${stepLabel}${methodIndex + 1}`;
            checkpointRows.push([
              detailedLabel,
              safeText(method?.細分名稱),
              safeText(method?.查核點内容),
              safeText(method?.執行單位),
            ]);
          });
        }
      });

      if (checkpointRows.length > 0) {
        const checkpointHeaders = [
          "查核點編號",
          "預定查核點名稱",
          "查核點內容",
          "執行單位",
        ];
        docxRenderer.addTable(checkpointHeaders, checkpointRows);
      }
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
