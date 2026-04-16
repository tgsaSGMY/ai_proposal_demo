// 用途：提供章節 Schema 編輯器的資料模型、轉換與驗證工具函式。
export type SchemaNodeType =
  | "object"
  | "array"
  | "string"
  | "number"
  | "integer"
  | "boolean";

export interface SchemaNode {
  id: string;
  key: string;
  title: string;
  description: string;
  type: SchemaNodeType;
  required: boolean;
  children: SchemaNode[];
  items: SchemaNode | null;
  isArrayItem: boolean;
}

export interface SchemaParseResult {
  title: string;
  description: string;
  nodes: SchemaNode[];
}

// 本地遞增計數器，搭配時間戳產生節點唯一 ID。
let nodeIdCounter = 0;

// 建立編輯器節點 ID。
function nextNodeId(): string {
  nodeIdCounter += 1;
  return `schema-node-${Date.now()}-${nodeIdCounter}`;
}

// 深拷貝單一節點（包含 children 與 items）。
export function cloneNode(node: SchemaNode): SchemaNode {
  return {
    ...node,
    children: node.children.map(cloneNode),
    items: node.items ? cloneNode(node.items) : null,
  };
}

// 深拷貝節點陣列，避免直接修改來源資料。
export function cloneNodes(nodes: SchemaNode[]): SchemaNode[] {
  return nodes.map(cloneNode);
}

// 建立空白節點，並依型別補上 object/array 預設結構。
export function createEmptyNode(
  type: SchemaNodeType,
  overrides: Partial<SchemaNode> = {},
): SchemaNode {
  const base: SchemaNode = {
    id: nextNodeId(),
    key: "",
    title: "",
    description: "",
    type,
    required: false,
    children: [],
    items: null,
    isArrayItem: Boolean(overrides.isArrayItem),
  };

  if (type === "object") {
    base.children = [];
  }

  if (type === "array") {
    base.items = overrides.items?.type
      ? cloneNode({ ...overrides.items, isArrayItem: true })
      : createEmptyNode("string", {
          key: "項目內容",
          title: "項目內容",
          isArrayItem: true,
        });
  }

  return {
    ...base,
    ...overrides,
    children: overrides.children
      ? overrides.children.map(cloneNode)
      : base.children,
    items: overrides.items
      ? cloneNode({ ...overrides.items, isArrayItem: true })
      : base.items,
  };
}

// 將 JSON Schema 轉成編輯器可用的樹狀資料。
export function parseSchemaToEditorState(
  schema?: Record<string, any> | null,
): SchemaParseResult {
  if (!schema || schema.type !== "object") {
    return { title: "", description: "", nodes: [] };
  }

  const requiredSet = new Set<string>(schema.required ?? []);
  const properties = schema.properties ?? {};
  const nodes = Object.entries(properties).map(([key, value]) =>
    parseSchemaNode(key, value as Record<string, any>, requiredSet.has(key)),
  );

  return {
    title: schema.title ?? "",
    description: schema.description ?? "",
    nodes,
  };
}

// 遞迴解析單一 schema 節點為編輯器節點。
function parseSchemaNode(
  key: string,
  schema: Record<string, any>,
  required: boolean,
  isArrayItem = false,
): SchemaNode {
  const type = (schema.type as SchemaNodeType) || "string";
  const node: SchemaNode = {
    id: nextNodeId(),
    key,
    title: schema.title ?? key,
    description: schema.description ?? "",
    type,
    required: isArrayItem ? false : required,
    children: [],
    items: null,
    isArrayItem,
  };

  if (type === "object") {
    const childRequired = new Set<string>(schema.required ?? []);
    const childProps = schema.properties ?? {};
    node.children = Object.entries(childProps).map(([childKey, childSchema]) =>
      parseSchemaNode(
        childKey,
        childSchema as Record<string, any>,
        childRequired.has(childKey),
      ),
    );
  } else if (type === "array") {
    if (schema.items) {
      const itemKey = schema.items.title ?? `${key} 項目`;
      node.items = parseSchemaNode(
        itemKey,
        schema.items as Record<string, any>,
        false,
        true,
      );
    } else {
      node.items = createEmptyNode("string", {
        key: `${key} 項目`,
        title: `${key} 項目`,
        isArrayItem: true,
      });
    }
  }

  return node;
}

// 將編輯器節點樹轉回 JSON Schema。
export function buildSchemaFromEditorState(
  nodes: SchemaNode[],
  options: { id: string; title?: string; description?: string },
): Record<string, any> {
  const schema: Record<string, any> = {
    id: options.id,
    type: "object",
    properties: buildProperties(nodes),
  };

  const trimmedTitle = options.title?.trim();
  const trimmedDescription = options.description?.trim();
  if (trimmedTitle) {
    schema.title = trimmedTitle;
  }
  if (trimmedDescription) {
    schema.description = trimmedDescription;
  }

  const requiredKeys = nodes
    .filter((node) => node.required && node.key.trim())
    .map((node) => node.key.trim());
  if (requiredKeys.length) {
    schema.required = requiredKeys;
  }

  return schema;
}

// 由節點陣列建立 properties 物件。
function buildProperties(nodes: SchemaNode[]): Record<string, any> {
  return nodes.reduce<Record<string, any>>((acc, node) => {
    const key = node.key.trim();
    if (!key) {
      return acc;
    }
    acc[key] = buildSchemaNode(node);
    return acc;
  }, {});
}

// 依節點型別組裝對應的 schema 片段。
function buildSchemaNode(node: SchemaNode): Record<string, any> {
  const base: Record<string, any> = {
    type: node.type,
  };
  if (node.title?.trim()) {
    base.title = node.title.trim();
  }
  if (node.description?.trim()) {
    base.description = node.description.trim();
  }

  if (node.type === "object") {
    const properties = buildProperties(node.children);
    base.properties = properties;
    const requiredKeys = node.children
      .filter((child) => child.required && child.key.trim())
      .map((child) => child.key.trim());
    if (requiredKeys.length) {
      base.required = requiredKeys;
    }
  } else if (node.type === "array") {
    base.items = node.items
      ? buildSchemaNode({ ...node.items, required: false })
      : { type: "string" };
  }

  return base;
}

// 驗證節點結構是否合法，回傳第一個錯誤訊息或 null。
// 同時將 title 同步為 key，因為編輯器 UI 不提供 title 獨立編輯，
// 避免使用者修改 key 後 title 仍殘留舊值導致下游顯示錯誤。
export function validateSchemaNodes(nodes: SchemaNode[]): string | null {
  const queue: SchemaNode[] = [...nodes];
  while (queue.length) {
    const current = queue.shift();
    if (!current) {
      continue;
    }
    if (!current.isArrayItem && !current.key.trim()) {
      return "章節結構中的欄位需要設定欄位代號";
    }
    // 始終將 title 同步為 key，確保 key 變更後 title 不會殘留舊值。
    // title 欄位在 SchemaNodeEditor 中不開放使用者獨立編輯，
    // 因此直接以 key 為準即可避免 key/title 不一致的問題。
    if (current.key.trim()) {
      current.title = current.key.trim();
    }
    if (current.type === "object") {
      current.children.forEach((child) => queue.push(child));
    } else if (current.type === "array" && current.items) {
      queue.push(current.items);
    }
  }
  return null;
}

// 建立空白 schema 編輯狀態。
export function createEmptySchemaState(): SchemaParseResult {
  return {
    title: "",
    description: "",
    nodes: [],
  };
}
