// frontend/utils/exportToWord.ts

import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  Numbering,
  Indent,
} from "docx";

// --- 輔助函數：將 schema 的 key 轉換為更易讀的標題 ---
function keyToTitle(key: string): string {
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

const nameSwitchMap: Record<string, string> = {
  風險的因應對策: "因應",
};

function nameSwitching(key: string): string {
  return nameSwitchMap[key] ?? key; // 如果找不到對應，就回傳原本的 key
}

// --- 核心：遞歸渲染內容的函數 ---
function renderSectionContent(
  data: any,
  schema: any, // 傳入對應的 schema
  paragraphs: Paragraph[]
) {
  if (!data || typeof data !== "object") {
    // 如果數據不是對象，直接作為段落添加
    paragraphs.push(new Paragraph({ text: String(data ?? "") }));
    return;
  }

  // 遍歷 schema 的 properties，以確保輸出的順序和 schema 定義的一致
  const schemaProperties = schema?.properties || {};

  for (const key in schemaProperties) {
    if (Object.prototype.hasOwnProperty.call(data, key)) {
      const value = data[key];
      const propInfo = schemaProperties[key];
      const title = propInfo.description || propInfo.title || keyToTitle(key);

      if (value === null || value === "") continue; // 跳過空值
      let numberingIndex = 0;

      if (Array.isArray(value)) {
        // --- 處理數組 ---
        if (value.length > 0) {
          // 添加數組的小標題 (例如 "Risk Assessment:")
          paragraphs.push(
            new Paragraph({
              children: [new TextRun({ text: title })],
              spacing: { before: 200, after: 100 },
              style: "SubSectionHeading",
            })
          );

          value.forEach((item, index) => {
            numberingIndex++;
            if (typeof item === "object" && item !== null) {
              const itemSchema = propInfo.items?.properties;
              let isFirstField = true;

              // 收集標題+描述成對組
              const usedKeys = new Set<string>();

              for (const itemKey in itemSchema) {
                if (!Object.prototype.hasOwnProperty.call(item, itemKey))
                  continue;

                const fieldValue = String(item[itemKey] ?? "").trim();
                if (!fieldValue) continue;

                const itemPropInfo = itemSchema[itemKey];
                const itemTitle = nameSwitching(
                  itemPropInfo.description ||
                    itemPropInfo.title ||
                    keyToTitle(itemKey)
                );

                // 處理 title/description 成對情況
                if (itemKey.includes("title")) {
                  // 找出同一 object 裡包含 'description' 或 'explanation' 的 key
                  const descKey = Object.keys(item).find((k) =>
                    k.includes("description")
                  );
                  const expKey = Object.keys(item).find((k) =>
                    k.includes("explanation")
                  );

                  const descValue = String(
                    (descKey && item[descKey]) || (expKey && item[expKey]) || ""
                  ).trim();

                  if (descValue.length > 0) {
                    paragraphs.push(
                      new Paragraph({
                        children: [
                          new TextRun({
                            text: `${numberingIndex}. `,
                          }),
                          new TextRun({
                            text: `${fieldValue}：${descValue}`,
                          }),
                        ],
                      })
                    );
                    usedKeys.add(itemKey);
                    if (descKey) usedKeys.add(descKey);
                    if (expKey) usedKeys.add(expKey);
                    isFirstField = false;
                    continue;
                  }
                }
                if (usedKeys.has(itemKey)) continue;

                if (isFirstField) {
                  // 第一個欄位顯示編號
                  paragraphs.push(
                    new Paragraph({
                      children: [
                        new TextRun({
                          text: `${numberingIndex}. `,
                        }),
                        new TextRun({
                          text: fieldValue,
                        }),
                      ],
                    })
                  );
                  isFirstField = false;
                } else {
                  // 後續欄位縮排顯示
                  paragraphs.push(
                    new Paragraph({
                      indent: { left: 720 }, // 約 0.5 inch 縮排
                      children: [
                        new TextRun({
                          text: "→" + itemTitle + ": " + fieldValue,
                        }),
                      ],
                    })
                  );
                }
              }
            } else {
              paragraphs.push(
                new Paragraph({
                  children: [
                    new TextRun({
                      text: `${numberingIndex}. `,
                    }),
                    new TextRun({
                      text: String(item ?? ""),
                    }),
                  ],
                })
              );
            }
          });
        }
      } else if (typeof value === "object" && value !== null) {
        // --- 遞歸處理嵌套對象 (如果有的話) ---
        paragraphs.push(
          new Paragraph({
            children: [new TextRun({ text: title, bold: true })],
            spacing: { before: 200, after: 100 },
          })
        );
        // 遞歸調用，傳入子對象和子 schema
        renderSectionContent(value, propInfo, paragraphs);
      } else {
        // --- 處理簡單的字符串/段落 ---
        // 檢查 schema 是否暗示這是一個長文本段落
        if (
          key.toLowerCase().includes("paragraph") ||
          key.toLowerCase().includes("description")
        ) {
          // 如果是段落，則直接輸出內容，不帶標題
          paragraphs.push(
            new Paragraph({
              text: String(value),
              spacing: { after: 200 },
            })
          );
        } else {
          // 否則，作為 "標題: 內容" 格式
          paragraphs.push(
            new Paragraph({
              children: [
                new TextRun({ text: `${title}: `, bold: true }),
                new TextRun(String(value)),
              ],
              spacing: { after: 100 },
            })
          );
        }
      }
    }
  }
}

/**
 * 將 sections + planContent 輸出成更自然的 Word 文檔
 */
// export async function exportPlanToWord(
//   sections: { id: string; name: string; json_schema: any }[],
//   planContent: Record<string, any>
// ) {
//   const paragraphs: Paragraph[] = [];

//   for (const section of sections) {
//     const sectionData = planContent[section.id]?.content;

//     // 添加章節大標題 (例如 "一、計畫背景與目標")
//     paragraphs.push(
//       new Paragraph({
//         text: section.name,
//         heading: HeadingLevel.HEADING_1,
//         spacing: { before: 400, after: 200 },
//       })
//     );

//     if (!sectionData) {
//       paragraphs.push(
//         new Paragraph({
//           children: [new TextRun({ text: "（無內容）", italics: true })],
//           spacing: { after: 400 },
//         })
//       );
//       continue;
//     }

//     // 使用新的渲染函數來處理章節內容
//     renderSectionContent(sectionData, section.json_schema, paragraphs);
//   }

//   const doc = new Document({
//     // 預定義編號樣式，用於處理數組
//     numbering: {
//       config: [
//         {
//           reference: "my-numbering-style",
//           levels: [
//             {
//               level: 0,
//               format: "decimal", // 1, 2, 3...
//               text: "%1.",
//               alignment: AlignmentType.LEFT,
//             },
//           ],
//         },
//       ],
//     },
//     sections: [
//       {
//         children: paragraphs,
//       },
//     ],
//   });

//   const blob = await Packer.toBlob(doc);

//   // 下載邏輯不變
//   const url = URL.createObjectURL(blob);
//   const link = document.createElement("a");
//   link.href = url;
//   link.download = "計劃書草稿.docx";
//   document.body.appendChild(link);
//   link.click();
//   document.body.removeChild(link);
//   URL.revokeObjectURL(url);
// }

export async function exportPlanToWord(
  sections: { id: string; name: string; json_schema: any }[],
  planContent: Record<string, any>
) {
  const paragraphs: Paragraph[] = [];

  for (const section of sections) {
    const sectionData = planContent[section.id]?.content;

    // === Section Title (HEADING 2) ===
    paragraphs.push(
      new Paragraph({
        text: section.name,
        heading: HeadingLevel.HEADING_2,
        spacing: { before: 400, after: 200 },
        style: "SectionHeading",
      })
    );

    if (!sectionData) {
      paragraphs.push(
        new Paragraph({
          children: [new TextRun({ text: "（無內容）", italics: true })],
          spacing: { after: 400 },
          style: "NormalText",
        })
      );
      continue;
    }

    // 使用你的內容渲染函數
    renderSectionContent(sectionData, section.json_schema, paragraphs);
  }

  // === 定義文件樣式 ===
  const doc = new Document({
    styles: {
      paragraphStyles: [
        {
          id: "SectionHeading",
          name: "Section Heading",
          basedOn: "Heading2",
          next: "NormalText",
          quickFormat: true,
          run: {
            font: "MS Gothic",
            size: 26, // 13pt
            bold: true,
          },
          paragraph: {
            spacing: { after: 200 },
          },
        },
        {
          id: "SubSectionHeading",
          name: "Subsection Heading",
          basedOn: "Heading3",
          next: "NormalText",
          quickFormat: true,
          run: {
            font: "MS Gothic",
            size: 22, // 11pt
            bold: true,
          },
          paragraph: {
            spacing: { after: 100 },
          },
        },
        {
          id: "NormalText",
          name: "Normal Text",
          basedOn: "Normal",
          quickFormat: true,
          run: {
            font: "MS Mincho",
            size: 22, // 11pt
          },
          paragraph: {
            spacing: { line: 276 }, // 約 1.15 倍行距
          },
        },
      ],
    },

    numbering: {
      config: [
        {
          reference: "my-numbering-style",
          levels: [
            {
              level: 0,
              format: "decimal",
              text: "%1.",
              alignment: AlignmentType.LEFT,
            },
          ],
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
  link.download = "計劃書草稿.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
