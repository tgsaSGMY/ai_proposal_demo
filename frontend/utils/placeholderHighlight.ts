// 答案佔位符標示工具：把「待決定」「待補」（含包住它的括號，如〔待補：元／月〕）切成獨立片段，
// 讓畫面以 <span> 標示。只影響顯示，已儲存的答案原文不變（Word 輸出不受影響）。

export interface PlaceholderSegment {
  text: string;
  hit: boolean;
}

const OPENERS = "〔【［\\[「『（(";
const CLOSERS = "〕】］\\]」』）)";

// 括號內含佔位符（前後最多 20 字）就整組標示；否則只標示佔位符本身
const PLACEHOLDER_PATTERN = new RegExp(
  `[${OPENERS}][^${OPENERS}${CLOSERS}\\n]{0,20}?(?:待決定|待補)[^${OPENERS}${CLOSERS}\\n]{0,20}[${CLOSERS}]|待決定|待補`,
  "g",
);

// 切成連續片段；所有片段的 text 串接後與原文完全相同
export function splitPlaceholders(text: string): PlaceholderSegment[] {
  const source = text || "";
  const segments: PlaceholderSegment[] = [];
  let lastIndex = 0;
  for (const match of source.matchAll(PLACEHOLDER_PATTERN)) {
    const start = match.index ?? 0;
    if (start > lastIndex) {
      segments.push({ text: source.slice(lastIndex, start), hit: false });
    }
    segments.push({ text: match[0], hit: true });
    lastIndex = start + match[0].length;
  }
  if (lastIndex < source.length) {
    segments.push({ text: source.slice(lastIndex), hit: false });
  }
  return segments;
}

export function countPlaceholders(text: string): number {
  return Array.from((text || "").matchAll(PLACEHOLDER_PATTERN)).length;
}
