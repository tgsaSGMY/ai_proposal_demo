// ===== 导入依赖库 =====
// 导入 XLSX 库用于读取和处理 Excel 文件
import * as XLSX from "xlsx";
// 导入动态 Schema 类型定义
import type { DynamicSectionViewModel } from "~/utils/dynamicSchema";

// ===== 数据类型定义 =====

/**
 * Excel 导入行的数据接口
 *
 * 说明：
 *   - 代表 Excel 工作表中的一行数据
 *   - 是一个通用的键值对对象（keys 来自 Excel 表头）
 *
 * 示例：
 *   {
 *     "章節": "二、研發動機",
 *     "項目": "1.技術或服務的核心問題是甚麼?",
 *     "回答": "开发人工智能模型..."
 *   }
 */
export interface ExcelImportRow extends Record<string, unknown> {}

/**
 * Excel 导入目标信息接口
 *
 * 说明：
 *   - 描述 Excel 数据应该填充到的目标位置
 *   - 用于 Excel 列与动态字段的映射
 */
export interface ExcelReplyTarget {
  sectionId: string; // 目标章节 ID
  propertyKey: string; // 目标字段 Key
}

/**
 * Excel 应用选项接口
 *
 * 说明：
 *   - 配置如何将 Excel 数据应用到动态字段
 */
export interface ExcelApplyOptions {
  rows: ExcelImportRow[]; // Excel 工作表的所有行
  dynamicSections: DynamicSectionViewModel[]; // 当前的动态字段结构
  replyTargetMap?: Map<string, ExcelReplyTarget>; // 预计算的映射表（可选优化）
  onFill: (sectionId: string, propertyKey: string, value: string) => void; // 填充回调函数
}

/**
 * Excel 应用结果接口
 *
 * 说明：
 *   - 描述 Excel 导入操作的结果统计
 */
export interface ExcelApplyResult {
  appliedCount: number; // 成功应用的行数
  skippedCount: number; // 跳过的行数（无法映射）
  summaryText: string; // 从 Excel 摘要部分提取的企劃名称和摘要
}

// ===== 公共导出函数 =====

/**
 * 从 Excel 文件中提取所有数据行
 *
 * 功能：
 *   1. 读取 Excel 文件的二进制内容
 *   2. 解析为工作簿对象
 *   3. 获取第一个工作表
 *   4. 将工作表转换为行数组
 *   5. 对合并单元格的列进行前向填充（复制上面的值）
 *
 * 参数：
 *   - buffer: Excel 文件的 ArrayBuffer
 *
 * 返回值：
 *   - ExcelImportRow[]: 包含所有数据行的数组
 *
 * 错误处理：
 *   - 如果 Excel 文件没有工作表：抛出错误
 *   - 如果无法读取第一个工作表：抛出错误
 *
 * 说明：
 *   - 自动将空行排除（不包含任何数据的行）
 *   - 对 "章節"、"Section" 等列进行前向填充（处理合并单元格）
 */
export function extractExcelRows(buffer: ArrayBuffer): ExcelImportRow[] {
  // 读取 Excel 文件为工作簿对象
  const workbook = XLSX.read(buffer, { type: "array" });
  // 检查工作簿是否有工作表
  if (!workbook.SheetNames || workbook.SheetNames.length === 0) {
    throw new Error("Excel 檔案未包含任何工作表");
  }
  // 获取第一个工作表的名称
  const sheetName = workbook.SheetNames[0]!;
  // 获取工作表对象
  const worksheet = workbook.Sheets[sheetName];
  if (!worksheet) {
    throw new Error("無法讀取第一個工作表");
  }
  // 将工作表转换为行数组（JSON 格式）
  const rows = XLSX.utils.sheet_to_json<ExcelImportRow>(worksheet, {
    defval: "", // 空单元格默认为空字符串
    raw: false, // 不使用原始格式（保持字符串形式）
    blankrows: false, // 排除完全空白的行
  });
  // 确保 rows 是数组
  const result = Array.isArray(rows) ? rows : [];
  // 对合并单元格列进行前向填充（复制上面单元格的值到空单元格）
  forwardFillMergedColumns(result, ["章節", "Section", "section", "章節名稱"]);
  return result;
}

/**
 * 构建 Excel 回复目标映射表
 *
 * 功能：
 *   - 创建一个查找表，将 Excel 中的章节和项目名称映射到实际的字段位置
 *   - 这样可以快速查找 Excel 某一行应该填充到哪个字段
 *
 * 工作流程：
 *   1. 遍历所有动态章节和字段
 *   2. 对每个字段生成多个变体（去除排序数字、标点等）
 *   3. 创建查找表条目
 *
 * 参数：
 *   - sections: 动态字段结构（从 buildDynamicSections 获得）
 *
 * 返回值：
 *   - Map<string, ExcelReplyTarget>: 从 "章節名::项目名" 到字段位置的映射
 *
 * 说明：
 *   - 映射表支持模糊匹配（处理不同的文本变体）
 *   - 可以提高 Excel 导入的匹配成功率
 */
export function buildExcelReplyTargetMap(
  sections: DynamicSectionViewModel[],
): Map<string, ExcelReplyTarget> {
  const map = new Map<string, ExcelReplyTarget>();
  // 遍历每个章节
  sections.forEach((section) => {
    // 规范化章节名称（去除空格、标点等）
    const normalizedSection = normalizeExcelText(section.sectionName);
    // 遍历章节中的每个字段
    section.fields.forEach((field) => {
      // 规范化字段标题
      const normalizedItem = normalizeExcelText(field.title);
      // 创建目标信息对象
      const target: ExcelReplyTarget = {
        sectionId: section.sectionId,
        propertyKey: field.propertyKey,
      };
      // 对字段名称生成多个变体（去除排序、标点等）
      buildExcelItemVariants(normalizedItem).forEach((variant) => {
        // 为每个变体注册查找表条目
        registerExcelLookup(map, normalizedSection, variant, target);
      });
    });
  });
  return map;
}

/**
 * 将 Excel 行数据应用到动态字段
 *
 * 功能：
 *   1. 解析 Excel 行数据（章节、项目、回答）
 *   2. 对每一行进行验证和规范化
 *   3. 使用映射表查找目标字段
 *   4. 调用回调函数填充数据
 *   5. 统计应用结果
 *   6. 提取企劃名称和摘要
 *
 * 工作流程：
 *   1. 检查行数据有效性
 *   2. 构建/使用提供的映射表
 *   3. 定义摘要部分的匹配规则
 *   4. 遍历每一行：
 *      - 提取章节、项目、回答
 *      - 规范化文本
 *      - 特殊处理摘要部分（企劃名称、摘要）
 *      - 查找映射关系
 *      - 调用 onFill 回调填充数据
 *   5. 生成摘要文本
 *
 * 参数：
 *   - options: 应用选项（包含行数据、字段结构、回调函数等）
 *
 * 返回值：
 *   - ExcelApplyResult: 包含应用统计信息的结果对象
 *
 * 说明：
 *   - 自动处理多个可能的列名变体（"回答"、"回覆"、"Answer" 等）
 *   - 摘要部分（一、摘要）的数据不填充到字段，而是返回为文本
 *   - 无法映射的行会被记为 skippedCount
 */
export function applyExcelRows({
  rows,
  dynamicSections,
  replyTargetMap,
  onFill,
}: ExcelApplyOptions): ExcelApplyResult {
  // 验证行数据有效性
  if (!Array.isArray(rows) || rows.length === 0) {
    return { appliedCount: 0, skippedCount: 0, summaryText: "" };
  }

  // 构建或使用提供的映射表
  const targetMap = replyTargetMap ?? buildExcelReplyTargetMap(dynamicSections);

  // ===== 摘要部分配置 =====
  // 定义摘要部分（一、摘要）的规范化名称
  const summarySectionKey = normalizeExcelText("一、摘要");
  // 企劃名称字段的可能列名变体
  const summaryNameKey = normalizeExcelText("1.計畫暫定名稱");
  const summaryNameAltKey = normalizeExcelText("1.計劃暫定名稱");
  // 摘要内容字段的可能列名变体
  const summaryContentKey = normalizeExcelText("3.計畫摘要");
  const summaryContentAltKey = normalizeExcelText("3.計劃摘要");

  // 合并所有可能的企劃名称匹配项
  const summaryNameCandidates = Array.from(
    new Set([
      ...buildExcelItemVariants(summaryNameKey),
      ...buildExcelItemVariants(summaryNameAltKey),
    ]),
  ).filter(Boolean);

  // 合并所有可能的摘要内容匹配项
  const summaryContentCandidates = Array.from(
    new Set([
      ...buildExcelItemVariants(summaryContentKey),
      ...buildExcelItemVariants(summaryContentAltKey),
    ]),
  ).filter(Boolean);

  // 初始化统计变量
  let planName = ""; // 提取的企劃名称
  let planSummary = ""; // 提取的企劃摘要
  let appliedCount = 0; // 成功应用的行数
  let skippedCount = 0; // 跳过的行数

  // ===== 处理每一行 =====
  rows.forEach((row) => {
    // 提取行中的关键字段
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

    // 规范化回答内容
    const answer = normalizeExcelAnswer(answerRaw);
    if (!answer) {
      return; // 空回答直接跳过
    }

    // 规范化章节和项目名称
    const normalizedSection = normalizeExcelText(sectionLabelRaw);
    const normalizedItem = normalizeExcelText(itemLabelRaw);

    // 验证必需字段
    if (!normalizedSection || !normalizedItem) {
      skippedCount += 1;
      return;
    }

    // ===== 特殊处理：摘要部分 =====
    // 如果这行是摘要部分的数据
    if (normalizedSection.startsWith(summarySectionKey)) {
      // 检查是否是企劃名称
      if (matchesAnyPrefix(normalizedItem, summaryNameCandidates)) {
        planName = answer;
        return;
      }
      // 检查是否是企劃摘要
      if (matchesAnyPrefix(normalizedItem, summaryContentCandidates)) {
        planSummary = answer;
      }
      return;
    }

    // ===== 处理普通字段 =====
    // 在映射表中查找目标字段
    const target = findExcelReplyTarget(
      normalizedSection,
      normalizedItem,
      targetMap,
    );

    // 如果找不到映射关系，则跳过
    if (!target) {
      skippedCount += 1;
      return;
    }

    // 调用回调函数填充数据
    onFill(target.sectionId, target.propertyKey, answer);
    appliedCount += 1;
  });

  // ===== 生成摘要文本 =====
  const summaryParts: string[] = [];
  if (planName) {
    summaryParts.push(`計畫暫定名稱：${planName}`);
  }
  if (planSummary) {
    summaryParts.push(`計畫摘要：${planSummary}`);
  }

  const summaryText = summaryParts.join("\n\n").trim();

  // ===== 返回应用结果 =====
  return {
    appliedCount,
    skippedCount,
    summaryText,
  };
}

// ===== 辅助函数：数据提取和规范化 =====

/**
 * 从 Excel 行中提取指定列的值
 * 尝试从多个可能的列名中获取值，返回第一个找到的非空值
 */
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

/**
 * 规范化 Excel 回答内容（将任意类型转换为字符串）
 */
function normalizeExcelAnswer(value: unknown): string {
  if (value === undefined || value === null) {
    return "";
  }
  if (typeof value === "number") {
    return String(value);
  }
  return String(value).trim();
}

/**
 * 规范化 Excel 文本（章节名、项目名等）
 * 统一格式便于字符串匹配：去除空格、标点、排序数字，转换为小写
 */
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

/**
 * 构建 Excel 查找键（格式："章節名::项目名"）
 * 用于在映射表中快速查找字段位置
 */
function buildExcelLookupKey(sectionLabel: string, itemLabel: string): string {
  return `${sectionLabel}::${itemLabel}`;
}

function stripLeadingOrdering(value: string): string {
  return value.replace(
    /^(?:[0-9]+|[一二三四五六七八九十百千]+)(?:[\.．、:：]*)?/,
    "",
  );
}

function stripTrailingPunctuation(value: string): string {
  return value.replace(
    /[?？!！。，．,\.、；;（）()\[\]{}【】<>《》"“”'‘’]+$/g,
    "",
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
  target: ExcelReplyTarget,
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
  map: Map<string, ExcelReplyTarget>,
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
    (candidate) => candidate && value.startsWith(candidate),
  );
}

function forwardFillMergedColumns(
  rows: ExcelImportRow[],
  candidateKeys: string[],
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
      Object.prototype.hasOwnProperty.call(row, key),
    );
    if (targetKey) {
      row[targetKey] = lastValue;
    } else if (candidateKeys[0]) {
      row[candidateKeys[0]] = lastValue;
    }
  });
}
