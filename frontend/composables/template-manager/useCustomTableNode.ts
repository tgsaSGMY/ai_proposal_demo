import type {
  WordCustomTableCell,
  WordCustomTableCellContent,
  WordCustomTableCellContentType,
  WordCustomTableConfig,
  WordDocumentNode,
} from "~/types/wordExport";

export function resolveNodeScopedPath(
  node: Pick<WordDocumentNode, "dataPath">,
  relativePath?: string,
): string | undefined {
  const normalize = (value?: string) =>
    value
      ?.split(".")
      .map((segment) => segment.trim())
      .filter(Boolean)
      .join(".") || "";

  const basePath = normalize(node.dataPath);
  const path = normalize(relativePath);

  if (!path) return basePath || undefined;
  if (!basePath) return path;

  const basePrefix = `${basePath}.`;
  if (path === basePath || path.startsWith(basePrefix)) {
    return path;
  }

  // Handle full schema paths in list-item context, e.g.
  // basePath="工作重點", path="分項計劃.工作重點.工作項目" => "工作重點.工作項目"
  const marker = `.${basePrefix}`;
  const markerIndex = path.indexOf(marker);
  if (markerIndex >= 0) {
    return path.slice(markerIndex + 1);
  }

  return `${basePath}.${path}`;
}

export function createCustomTableNodeHelpers(generateNodeId: () => string) {
  function syncLegacyCustomTableCellFields(cell: WordCustomTableCell) {
    const primary = cell.contents?.[0];
    if (!primary) {
      cell.type = "text";
      cell.text = "";
      cell.dataPath = "";
      return;
    }

    cell.type = primary.type;
    if (primary.type === "text") {
      cell.text = primary.text ?? "";
      cell.dataPath = "";
    } else {
      cell.dataPath = primary.dataPath ?? "";
      cell.text = "";
    }
  }

  function ensureCustomTableCellContents(cell: WordCustomTableCell) {
    const buildContent = (
      base?: Partial<WordCustomTableCellContent> & {
        type?: WordCustomTableCellContentType;
      },
    ): WordCustomTableCellContent => {
      const resolvedType = base?.type ?? "text";
      return {
        id: base?.id || generateNodeId(),
        type: resolvedType,
        text: resolvedType === "text" ? (base?.text ?? "") : undefined,
        dataPath: resolvedType === "field" ? (base?.dataPath ?? "") : undefined,
      };
    };

    if (!Array.isArray(cell.contents) || cell.contents.length === 0) {
      const fallbackType = cell.type ?? "text";
      cell.contents = [
        buildContent({
          type: fallbackType,
          text: cell.text,
          dataPath: cell.dataPath,
        }),
      ];
    } else {
      cell.contents = cell.contents.map((content) =>
        buildContent({
          id: content.id,
          type: content.type,
          text: content.text,
          dataPath: content.dataPath,
        }),
      );
    }

    syncLegacyCustomTableCellFields(cell);
    return cell.contents;
  }

  function normalizeCustomTableCells(config: WordCustomTableConfig) {
    const rows = Math.min(Math.max(Math.floor(config.rows || 1), 1), 20);
    const cols = Math.min(Math.max(Math.floor(config.cols || 1), 1), 20);
    const expectedCellCount = rows * cols;
    const existingCells = Array.isArray(config.cells) ? config.cells : [];
    let needsRebuild =
      !Array.isArray(config.cells) ||
      existingCells.length !== expectedCellCount;

    const seenKeys = new Set<string>();
    if (!needsRebuild) {
      for (const cell of existingCells) {
        const rowValid =
          typeof cell.row === "number" && cell.row >= 0 && cell.row < rows;
        const colValid =
          typeof cell.col === "number" && cell.col >= 0 && cell.col < cols;
        if (!rowValid || !colValid) {
          needsRebuild = true;
          break;
        }
        const key = `${cell.row}-${cell.col}`;
        if (seenKeys.has(key)) {
          needsRebuild = true;
          break;
        }
        seenKeys.add(key);
      }
    }

    const finalizeCell = (cell: WordCustomTableCell) => {
      if (!cell.id) {
        cell.id = generateNodeId();
      }
      ensureCustomTableCellContents(cell);
      return cell;
    };

    if (!needsRebuild) {
      existingCells.forEach(finalizeCell);
      config.rows = rows;
      config.cols = cols;
      return;
    }

    const existing = new Map<string, WordCustomTableCell>();
    for (const cell of existingCells) {
      if (
        typeof cell.row !== "number" ||
        typeof cell.col !== "number" ||
        cell.row < 0 ||
        cell.col < 0
      ) {
        continue;
      }
      const key = `${cell.row}-${cell.col}`;
      if (!existing.has(key)) {
        existing.set(key, cell);
      }
    }

    const cells: WordCustomTableCell[] = [];
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const key = `${row}-${col}`;
        const cell = existing.get(key) ?? {
          id: generateNodeId(),
          row,
          col,
          type: "text",
          text: "",
          dataPath: "",
        };
        cell.row = row;
        cell.col = col;
        cells.push(finalizeCell(cell));
      }
    }

    config.rows = rows;
    config.cols = cols;
    config.cells = cells;
  }

  function ensureCustomTableConfig(node: WordDocumentNode) {
    if (!node.customTable) {
      node.customTable = {
        rows: 2,
        cols: 2,
        cells: [],
      };
    }
    normalizeCustomTableCells(node.customTable);
    return node.customTable;
  }

  function getCustomTableRowCells(node: WordDocumentNode, rowIndex: number) {
    if (!node.customTable?.cells) {
      return [];
    }
    return node.customTable.cells
      .filter((cell) => cell.row === rowIndex)
      .sort((a, b) => a.col - b.col);
  }

  function addCustomTableCellContent(
    cell: WordCustomTableCell,
    type: WordCustomTableCellContentType,
  ) {
    if (!cell.contents) {
      cell.contents = [];
    }
    cell.contents.push({
      id: generateNodeId(),
      type,
      text: type === "text" ? "" : undefined,
      dataPath: type === "field" ? "" : undefined,
    });
    ensureCustomTableCellContents(cell);
  }

  function removeCustomTableCellContent(
    cell: WordCustomTableCell,
    contentId: string,
  ) {
    if (!cell.contents || cell.contents.length === 0) {
      cell.contents = [
        {
          id: generateNodeId(),
          type: "text",
          text: "",
        },
      ];
    }
    if (cell.contents.length === 1) {
      const first = cell.contents[0];
      if (first) {
        first.type = "text";
        first.text = "";
        first.dataPath = "";
      }
      syncLegacyCustomTableCellFields(cell);
      return;
    }
    cell.contents = cell.contents.filter((content) => content.id !== contentId);
    if (!cell.contents.length) {
      cell.contents = [
        {
          id: generateNodeId(),
          type: "text",
          text: "",
        },
      ];
    }
    ensureCustomTableCellContents(cell);
  }

  function moveCustomTableCellContent(
    cell: WordCustomTableCell,
    contentIndex: number,
    direction: "up" | "down",
  ) {
    if (!cell.contents || cell.contents.length < 2) return;
    const newIndex = direction === "up" ? contentIndex - 1 : contentIndex + 1;
    if (newIndex < 0 || newIndex >= cell.contents.length) return;
    const current = cell.contents[contentIndex];
    const target = cell.contents[newIndex];
    if (!current || !target) return;
    cell.contents[contentIndex] = target;
    cell.contents[newIndex] = current;
    ensureCustomTableCellContents(cell);
  }

  function handleCustomTableCellContentTypeChange(
    cell: WordCustomTableCell,
    content: WordCustomTableCellContent,
  ) {
    if (content.type === "text") {
      content.text = content.text ?? "";
      content.dataPath = "";
    } else {
      content.dataPath = content.dataPath ?? "";
      content.text = "";
    }
    ensureCustomTableCellContents(cell);
  }

  return {
    syncLegacyCustomTableCellFields,
    ensureCustomTableCellContents,
    normalizeCustomTableCells,
    ensureCustomTableConfig,
    getCustomTableRowCells,
    addCustomTableCellContent,
    removeCustomTableCellContent,
    moveCustomTableCellContent,
    handleCustomTableCellContentTypeChange,
  };
}
