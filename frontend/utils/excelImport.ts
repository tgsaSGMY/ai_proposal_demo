import * as XLSX from "xlsx";
import type { DynamicSectionViewModel } from "~/utils/dynamicSchema";

export interface ExcelImportRow extends Record<string, unknown> {}

export interface ExcelReplyTarget {
  sectionId: string;
  propertyKey: string;
}

export interface ExcelApplyOptions {
  rows: ExcelImportRow[];
  dynamicSections: DynamicSectionViewModel[];
  replyTargetMap?: Map<string, ExcelReplyTarget>;
  onFill: (sectionId: string, propertyKey: string, value: string) => void;
}

export interface ExcelApplyResult {
  appliedCount: number;
  skippedCount: number;
  summaryText: string;
}

export function extractExcelRows(buffer: ArrayBuffer): ExcelImportRow[] {
  const workbook = XLSX.read(buffer, { type: "array" });
  if (!workbook.SheetNames || workbook.SheetNames.length === 0) {
    throw new Error("Excel 檔案未包含任何工作表");
  }
  const sheetName = workbook.SheetNames[0]!;
  const worksheet = workbook.Sheets[sheetName];
  if (!worksheet) {
    throw new Error("無法讀取第一個工作表");
  }
  const rows = XLSX.utils.sheet_to_json<ExcelImportRow>(worksheet, {
    defval: "",
    raw: false,
    blankrows: false,
  });
  const result = Array.isArray(rows) ? rows : [];
  forwardFillMergedColumns(result, ["章節", "Section", "section", "章節名稱"]);
  return result;
}

export function buildExcelReplyTargetMap(
  sections: DynamicSectionViewModel[]
): Map<string, ExcelReplyTarget> {
  const map = new Map<string, ExcelReplyTarget>();
  sections.forEach((section) => {
    const normalizedSection = normalizeExcelText(section.sectionName);
    section.fields.forEach((field) => {
      const normalizedItem = normalizeExcelText(field.title);
      const target: ExcelReplyTarget = {
        sectionId: section.sectionId,
        propertyKey: field.propertyKey,
      };
      buildExcelItemVariants(normalizedItem).forEach((variant) => {
        registerExcelLookup(map, normalizedSection, variant, target);
      });
    });
  });
  return map;
}

export function applyExcelRows({
  rows,
  dynamicSections,
  replyTargetMap,
  onFill,
}: ExcelApplyOptions): ExcelApplyResult {
  if (!Array.isArray(rows) || rows.length === 0) {
    return { appliedCount: 0, skippedCount: 0, summaryText: "" };
  }

  const targetMap = replyTargetMap ?? buildExcelReplyTargetMap(dynamicSections);

  const summarySectionKey = normalizeExcelText("一、摘要");
  const summaryNameKey = normalizeExcelText("1.計畫暫定名稱");
  const summaryNameAltKey = normalizeExcelText("1.計劃暫定名稱");
  const summaryContentKey = normalizeExcelText("3.計畫摘要");
  const summaryContentAltKey = normalizeExcelText("3.計劃摘要");

  const summaryNameCandidates = Array.from(
    new Set([
      ...buildExcelItemVariants(summaryNameKey),
      ...buildExcelItemVariants(summaryNameAltKey),
    ])
  ).filter(Boolean);

  const summaryContentCandidates = Array.from(
    new Set([
      ...buildExcelItemVariants(summaryContentKey),
      ...buildExcelItemVariants(summaryContentAltKey),
    ])
  ).filter(Boolean);

  let planName = "";
  let planSummary = "";
  let appliedCount = 0;
  let skippedCount = 0;

  rows.forEach((row) => {
    const sectionLabelRaw = pickRowValue(row, [
      "章節",
      "Section",
      "section",
      "章節名稱",
    ]);
    const itemLabelRaw = pickRowValue(row, [
      "項目",
      "Item",
      "item",
      "題目",
      "項目名稱",
      "問題",
    ]);
    const answerRaw = pickRowValue(row, [
      "回答",
      "回覆",
      "Answer",
      "answer",
      "內容",
      "回應",
      "Response",
      "response",
    ]);

    const answer = normalizeExcelAnswer(answerRaw);
    if (!answer) {
      return;
    }

    const normalizedSection = normalizeExcelText(sectionLabelRaw);
    const normalizedItem = normalizeExcelText(itemLabelRaw);

    if (!normalizedSection || !normalizedItem) {
      skippedCount += 1;
      return;
    }

    if (normalizedSection.startsWith(summarySectionKey)) {
      if (matchesAnyPrefix(normalizedItem, summaryNameCandidates)) {
        planName = answer;
        return;
      }
      if (matchesAnyPrefix(normalizedItem, summaryContentCandidates)) {
        planSummary = answer;
      }
      return;
    }

    const target = findExcelReplyTarget(
      normalizedSection,
      normalizedItem,
      targetMap
    );

    if (!target) {
      skippedCount += 1;
      return;
    }

    onFill(target.sectionId, target.propertyKey, answer);
    appliedCount += 1;
  });

  const summaryParts: string[] = [];
  if (planName) {
    summaryParts.push(`計畫暫定名稱：${planName}`);
  }
  if (planSummary) {
    summaryParts.push(`計畫摘要：${planSummary}`);
  }

  const summaryText = summaryParts.join("\n\n").trim();

  return {
    appliedCount,
    skippedCount,
    summaryText,
  };
}

function pickRowValue(row: ExcelImportRow, possibleKeys: string[]): string {
  if (!row) {
    return "";
  }
  for (const key of possibleKeys) {
    if (Object.prototype.hasOwnProperty.call(row, key)) {
      const value = row[key];
      if (value !== undefined && value !== null && `${value}`.trim() !== "") {
        return String(value);
      }
    }
  }
  return "";
}

function normalizeExcelAnswer(value: unknown): string {
  if (value === undefined || value === null) {
    return "";
  }
  if (typeof value === "number") {
    return String(value);
  }
  return String(value).trim();
}

function normalizeExcelText(value: unknown): string {
  if (value === undefined || value === null) {
    return "";
  }
  return String(value)
    .trim()
    .normalize("NFKC")
    .replace(/計劃/g, "計畫")
    .replace(/[\s\u3000]/g, "")
    .replace(/[:：]/g, "")
    .replace(/[?？!！。，．,\.、；;（）()\[\]{}【】<>《》"“”'‘’]/g, "")
    .toLowerCase();
}

function buildExcelLookupKey(sectionLabel: string, itemLabel: string): string {
  return `${sectionLabel}::${itemLabel}`;
}

function stripLeadingOrdering(value: string): string {
  return value.replace(
    /^(?:[0-9]+|[一二三四五六七八九十百千]+)(?:[\.．、:：]*)?/,
    ""
  );
}

function stripTrailingPunctuation(value: string): string {
  return value.replace(
    /[?？!！。，．,\.、；;（）()\[\]{}【】<>《》"“”'‘’]+$/g,
    ""
  );
}

function buildExcelItemVariants(value: string): string[] {
  const variants = [value];
  const withoutLeading = stripLeadingOrdering(value);
  const withoutTrailing = stripTrailingPunctuation(value);
  const cleaned = stripTrailingPunctuation(withoutLeading);
  [withoutLeading, withoutTrailing, cleaned].forEach((variant) => {
    if (variant && !variants.includes(variant)) {
      variants.push(variant);
    }
  });
  return variants.filter((variant) => variant && variant.trim() !== "");
}

function registerExcelLookup(
  map: Map<string, ExcelReplyTarget>,
  sectionLabel: string,
  itemLabel: string,
  target: ExcelReplyTarget
): void {
  if (!itemLabel) {
    return;
  }
  const key = buildExcelLookupKey(sectionLabel, itemLabel);
  if (!map.has(key)) {
    map.set(key, target);
  }
}

function findExcelReplyTarget(
  sectionLabel: string,
  itemLabel: string,
  map: Map<string, ExcelReplyTarget>
): ExcelReplyTarget | null {
  const variants = buildExcelItemVariants(itemLabel);
  for (const variant of variants) {
    const key = buildExcelLookupKey(sectionLabel, variant);
    const candidate = map.get(key);
    if (candidate) {
      return candidate;
    }
  }
  return null;
}

function matchesAnyPrefix(value: string, candidates: string[]): boolean {
  return candidates.some(
    (candidate) => candidate && value.startsWith(candidate)
  );
}

function forwardFillMergedColumns(
  rows: ExcelImportRow[],
  candidateKeys: string[]
): void {
  let lastValue = "";
  rows.forEach((row) => {
    let currentValue = "";
    for (const key of candidateKeys) {
      if (!Object.prototype.hasOwnProperty.call(row, key)) {
        continue;
      }
      const raw = row[key];
      const normalized = normalizeExcelAnswer(raw);
      if (normalized) {
        currentValue = normalized;
        row[key] = normalized;
        break;
      }
    }

    if (currentValue) {
      lastValue = currentValue;
      return;
    }

    if (!lastValue) {
      return;
    }

    const targetKey = candidateKeys.find((key) =>
      Object.prototype.hasOwnProperty.call(row, key)
    );
    if (targetKey) {
      row[targetKey] = lastValue;
    } else if (candidateKeys[0]) {
      row[candidateKeys[0]] = lastValue;
    }
  });
}
