import type {
  WordCustomTableCell,
  WordDocumentNode,
  WordDocumentNodeType,
} from "~/types/wordExport";

interface SchemaField {
  title?: string;
  type?: string;
  properties?: Record<string, SchemaField>;
  items?: {
    properties?: Record<string, SchemaField>;
  };
}

interface PreviewSectionRecord {
  id: string;
  json_schema?: {
    properties?: Record<string, SchemaField>;
  } | null;
}

function normalizePath(path?: string): string | null {
  if (!path) return null;
  const normalized = path
    .split(".")
    .map((segment) => segment.trim())
    .filter(Boolean)
    .join(".");
  return normalized.length > 0 ? normalized : null;
}

function setValueByPath(root: Record<string, any>, path: string, value: any) {
  const segments = path
    .split(".")
    .map((segment) => segment.trim())
    .filter(Boolean);
  if (!segments.length) return;

  const cloneValue = (input: any): any => {
    if (Array.isArray(input)) {
      return input.map((item): any => cloneValue(item));
    }
    if (input && typeof input === "object") {
      return Object.fromEntries(
        Object.entries(input).map(([k, v]): [string, any] => [
          k,
          cloneValue(v),
        ]),
      );
    }
    return input;
  };

  const assign = (current: any, segmentIndex: number) => {
    if (current === null || current === undefined) return;

    if (Array.isArray(current)) {
      current.forEach((item) => assign(item, segmentIndex));
      return;
    }

    if (typeof current !== "object") return;

    const key = segments[segmentIndex];
    if (!key) return;
    const isLeaf = segmentIndex === segments.length - 1;

    if (isLeaf) {
      if (current[key] === undefined || current[key] === null) {
        current[key] = cloneValue(value);
      }
      return;
    }

    const next = current[key];
    if (Array.isArray(next)) {
      assign(next, segmentIndex + 1);
      return;
    }

    if (!next || typeof next !== "object") {
      current[key] = {};
    }

    assign(current[key], segmentIndex + 1);
  };

  assign(root, 0);
}

function generateSampleValue(
  path: string,
  nodeType: WordDocumentNodeType,
): string {
  const key = path.split(".").pop() || "欄位";
  if (nodeType === "paragraph") {
    return `${key} 的示例內容`;
  }
  if (nodeType === "customTable") {
    return `${key} 欄位值`;
  }
  return `${key} 示例值`;
}

function generateValueFromSchema(field: SchemaField, fieldKey: string): any {
  if (field.type === "array") {
    const items: any[] = [];
    if (field.items?.properties) {
      for (let index = 0; index < 2; index++) {
        const item: Record<string, any> = {};
        for (const [key, subField] of Object.entries(field.items.properties)) {
          item[key] = generateValueFromSchema(subField, key);
        }
        items.push(item);
      }
    } else {
      items.push(`範例${fieldKey}數據1`, `範例${fieldKey}數據2`);
    }
    return items;
  }

  if (field.type === "object" && field.properties) {
    const result: Record<string, any> = {};
    for (const [key, subField] of Object.entries(field.properties)) {
      result[key] = generateValueFromSchema(subField, key);
    }
    return result;
  }

  if (
    field.type === "number" ||
    fieldKey.includes("金額") ||
    fieldKey.includes("數量")
  ) {
    return 1000;
  }

  return `${field.title || fieldKey}的示例內容`;
}

function generateSectionSchemaSample(
  section: PreviewSectionRecord,
): Record<string, any> {
  const schemaProperties = section.json_schema?.properties;
  if (!schemaProperties) return {};

  const sample: Record<string, any> = {};
  for (const [key, field] of Object.entries(schemaProperties)) {
    sample[key] = generateValueFromSchema(field, key);
  }
  return sample;
}

function toRelativePath(
  parentPath: string | undefined,
  childPath: string | undefined,
): string | null {
  const child = normalizePath(childPath);
  if (!child) return null;

  const parent = normalizePath(parentPath);
  if (!parent) return child;

  const prefix = `${parent}.`;
  if (child.startsWith(prefix)) {
    return child.slice(prefix.length);
  }

  const index = child.indexOf(prefix);
  if (index >= 0) {
    return child.slice(index + prefix.length);
  }

  return child;
}

function ensureTableRowSample(
  data: Record<string, any>,
  node: WordDocumentNode,
) {
  const path = normalizePath(node.dataPath);
  if (!path) return;

  const columns = node.table?.columns || [];
  const row: Record<string, any> = {};
  columns.forEach((column) => {
    if (!column.key) return;
    setValueByPath(row, column.key, generateSampleValue(column.key, "table"));
  });

  setValueByPath(data, path, [row, { ...row }]);
}

function ensureListSample(data: Record<string, any>, node: WordDocumentNode) {
  const path = normalizePath(node.dataPath);
  if (!path) return;

  if (node.list?.itemConfig?.useSubNodes && node.children?.length) {
    const itemA: Record<string, any> = {};
    const itemB: Record<string, any> = {};

    node.children.forEach((child) => {
      const relativePath = toRelativePath(node.dataPath, child.dataPath);
      if (!relativePath) return;

      const sampleA = generateSampleValue(relativePath, child.type);
      const sampleB = `${sampleA} 2`;
      setValueByPath(itemA, relativePath, sampleA);
      setValueByPath(itemB, relativePath, sampleB);
    });

    setValueByPath(data, path, [itemA, itemB]);
    return;
  }

  const key = path.split(".").pop() || "項目";
  setValueByPath(data, path, [`${key} 示例一`, `${key} 示例二`]);
}

function readCellContents(cell: WordCustomTableCell) {
  if (Array.isArray(cell.contents) && cell.contents.length) {
    return cell.contents;
  }

  return [
    {
      type: cell.type ?? "text",
      text: cell.text,
      dataPath: cell.dataPath,
    },
  ];
}

function ensureCustomTableSample(
  data: Record<string, any>,
  node: WordDocumentNode,
) {
  const cells = node.customTable?.cells || [];
  cells.forEach((cell) => {
    readCellContents(cell).forEach((content) => {
      if (content.type !== "field" || !content.dataPath) return;
      const relativePath = toRelativePath(node.dataPath, content.dataPath);
      if (!relativePath) return;

      const scopedPath = normalizePath(node.dataPath)
        ? `${normalizePath(node.dataPath)}.${relativePath}`
        : relativePath;
      if (!scopedPath) return;

      setValueByPath(
        data,
        scopedPath,
        generateSampleValue(scopedPath, "customTable"),
      );
    });
  });
}

function ensureParagraphSample(
  data: Record<string, any>,
  node: WordDocumentNode,
) {
  const path = normalizePath(node.dataPath);
  if (!path) return;
  setValueByPath(data, path, generateSampleValue(path, "paragraph"));
}

function walkNodes(
  nodes: WordDocumentNode[] | undefined,
  callback: (node: WordDocumentNode, parent?: WordDocumentNode) => void,
  parent?: WordDocumentNode,
) {
  if (!nodes) return;
  for (const node of nodes) {
    if (!node) continue;
    callback(node, parent);
    if (node.children?.length) {
      walkNodes(node.children, callback, node);
    }
  }
}

export function buildPreviewSectionDataMap(
  sections: PreviewSectionRecord[],
  nodes: WordDocumentNode[] | undefined,
): Record<string, Record<string, any>> {
  const dataMap: Record<string, Record<string, any>> = Object.fromEntries(
    sections.map((section) => [
      section.id,
      generateSectionSchemaSample(section),
    ]),
  );

  walkNodes(nodes, (node, parent) => {
    const sectionId = node.sectionId;
    if (!sectionId) return;

    if (!dataMap[sectionId]) {
      dataMap[sectionId] = {};
    }

    const sectionData = dataMap[sectionId];
    if (!sectionData) return;

    if (
      parent?.type === "list" &&
      parent.list?.itemConfig?.useSubNodes &&
      node.type === "paragraph"
    ) {
      return;
    }

    switch (node.type) {
      case "paragraph":
        ensureParagraphSample(sectionData, node);
        break;
      case "list":
        ensureListSample(sectionData, node);
        break;
      case "table":
        ensureTableRowSample(sectionData, node);
        break;
      case "customTable":
        ensureCustomTableSample(sectionData, node);
        break;
      default:
        break;
    }
  });

  return dataMap;
}
