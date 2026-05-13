import type { WordDocumentNode, WordListStyle } from "~/types/wordExport";

export type HeadingCounterState = Record<number, number>;

const PARAGRAPH_SUB_HEADING_MAX_LEVEL = 3;

export function createHeadingCounterState(): HeadingCounterState {
  return {};
}

export function resetHeadingCounters(state: HeadingCounterState) {
  Object.keys(state).forEach((key) => delete state[Number(key)]);
}

export function formatChineseNumeral(value: number): string {
  if (value <= 0) return "";
  const digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"];
  if (value <= 10) {
    return value === 10 ? "十" : digits[value] || "";
  }
  if (value < 20) {
    return `十${digits[value - 10]}`;
  }
  if (value < 100) {
    const tens = Math.floor(value / 10);
    const units = value % 10;
    let result = `${digits[tens]}十`;
    if (units !== 0) {
      result += digits[units];
    }
    return result;
  }
  return String(value);
}

export function getImplicitLevelFromStyle(
  style: WordListStyle | undefined,
): number {
  switch (style) {
    case "chineseNumber":
    case "chineseComma":
      return 2;
    case "arabicNumber":
    case "numberedDot":
      return 3;
    case "parenNumbered":
      return 4;
    default:
      return 3;
  }
}

export function formatHeadingPrefix(
  level: number | undefined,
  state: HeadingCounterState,
  style?: WordListStyle,
): string {
  const rawLevel = level || 2;
  const effectiveLevel = style ? getImplicitLevelFromStyle(style) : rawLevel;

  state[effectiveLevel] = (state[effectiveLevel] ?? 0) + 1;

  Object.keys(state).forEach((key) => {
    const keyNum = Number(key);
    if (keyNum > effectiveLevel) {
      delete state[keyNum];
    }
  });

  const count = state[effectiveLevel];

  if (style) {
    switch (style) {
      case "chineseNumber":
      case "chineseComma":
        return `${formatChineseNumeral(count)}、`;
      case "arabicNumber":
      case "numberedDot":
        return `${count}. `;
      case "parenNumbered":
        return `（${count}）`;
      case "bullet":
        return "";
      default:
        break;
    }
  }

  switch (effectiveLevel) {
    case 2:
      return `${formatChineseNumeral(count)}、`;
    case 3:
      return `${count}. `;
    case 4:
      return `（${count}）`;
    default:
      return `${count}. `;
  }
}

export function getListBulletLabel(
  style: WordListStyle | undefined,
  index: number,
): string {
  switch (style) {
    case "chineseNumber":
    case "chineseComma":
      return `${formatChineseNumeral(index + 1)}、`;
    case "arabicNumber":
    case "numberedDot":
      return `${index + 1}.`;
    case "parenNumbered":
      return `（${index + 1}）`;
    default:
      return "•";
  }
}

export function resolveParagraphEffectiveLevel(node: WordDocumentNode): number {
  if (node.paragraphNumberStyle) {
    return getImplicitLevelFromStyle(node.paragraphNumberStyle);
  }
  return node.level ?? 3;
}

export function shouldUseParagraphSubHeadingStyle(
  node: WordDocumentNode,
  maxLevel = PARAGRAPH_SUB_HEADING_MAX_LEVEL,
): boolean {
  if (node.type !== "paragraph") return false;
  if (node.paragraphNumbering !== true) return false;
  return resolveParagraphEffectiveLevel(node) <= maxLevel;
}
