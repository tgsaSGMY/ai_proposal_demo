import { Document, Packer, AlignmentType } from "docx";
import type { ContentRenderer } from "../contentRenderer";
import { DocxRenderer } from "../contentRenderer";

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
  return nameSwitchMap[key] ?? key;
}

// --- 核心：遞歸渲染內容的函數 ---
function renderSectionContent(
  data: any,
  schema: any,
  renderer: ContentRenderer<any>
) {
  if (!data || typeof data !== "object") {
    if (data) renderer.addParagraph(String(data));
    return;
  }

  const schemaProperties = schema?.properties || {};

  for (const key in schemaProperties) {
    if (Object.prototype.hasOwnProperty.call(data, key)) {
      const value = data[key];
      const propInfo = schemaProperties[key];
      const title = propInfo.description || propInfo.title || keyToTitle(key);

      if (value === null || value === "") continue;

      if (Array.isArray(value)) {
        if (value.length > 0) {
          renderer.addArrayTitle(title);

          value.forEach((item, index) => {
            const numberingIndex = index + 1;
            if (typeof item === "object" && item !== null) {
              const itemSchema = propInfo.items?.properties;
              const usedKeys = new Set<string>();

              const titleKey = Object.keys(item).find((k) =>
                k.includes("title")
              );
              const descKey = Object.keys(item).find(
                (k) => k.includes("description") || k.includes("explanation")
              );

              if (titleKey && descKey && item[titleKey] && item[descKey]) {
                renderer.addNumberedListItem(numberingIndex, {
                  title: String(item[titleKey]),
                  description: String(item[descKey]),
                });
                usedKeys.add(titleKey).add(descKey);
              }

              for (const itemKey in itemSchema) {
                if (
                  usedKeys.has(itemKey) ||
                  !Object.prototype.hasOwnProperty.call(item, itemKey)
                )
                  continue;

                const fieldValue = String(item[itemKey] ?? "").trim();
                if (!fieldValue) continue;

                const itemPropInfo = itemSchema[itemKey];
                const itemTitle = nameSwitching(
                  itemPropInfo.description ||
                    itemPropInfo.title ||
                    keyToTitle(itemKey)
                );

                if (usedKeys.size === 0) {
                  renderer.addNumberedListItem(numberingIndex, fieldValue);
                } else {
                  renderer.addIndentedListItem(itemTitle, fieldValue);
                }
                usedKeys.add(itemKey);
              }
            } else {
              renderer.addNumberedListItem(numberingIndex, String(item ?? ""));
            }
          });
        }
      } else if (typeof value === "object" && value !== null) {
        renderer.addArrayTitle(title);
        renderSectionContent(value, propInfo, renderer);
      } else {
        if (
          key.toLowerCase().includes("paragraph") ||
          key.toLowerCase().includes("description")
        ) {
          renderer.addParagraph(String(value));
        } else {
          renderer.addKeyValue(title, String(value));
        }
      }
    }
  }
}

export async function exportPlanToWordCentralPhase2(
  sections: { id: string; name: string; json_schema: any }[],
  planContent: Record<string, any>,
  projectTitle?: string
) {
  const docxRenderer = new DocxRenderer();

  for (const section of sections) {
    const sectionData = planContent[section.id]?.content;

    docxRenderer.addSectionTitle(section.name);

    if (!sectionData) {
      docxRenderer.addEmptyContentMessage();
      continue;
    }

    renderSectionContent(sectionData, section.json_schema, docxRenderer);
  }

  const paragraphs = docxRenderer.getResult();
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
            size: 26,
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
            size: 22,
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
            size: 22,
          },
          paragraph: {
            spacing: { line: 276 },
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
  link.download = projectTitle ? `${projectTitle}.docx` : "計劃書草稿.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
