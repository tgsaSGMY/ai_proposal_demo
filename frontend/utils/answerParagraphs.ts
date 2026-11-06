// 答案顯示用分段工具：只影響畫面排版，已儲存的答案原文不變（Word 輸出不受影響）。
// - splitAnswerParagraphs：「展開」模態框顯示用的段落清單
// - answerToEditText / editTextToAnswer：編輯模態框用；自動補的換段以零寬字元標記，
//   送出前只移除這些標記換段，使用者自己輸入或原文已有的換行都完整保留。

const PARAGRAPH_TARGET_LENGTH = 120; // 累積到約此長度就換段
const LONG_BLOCK_LENGTH = 150; // 超過此長度的段落才需要再切
const SHORT_TAIL_LENGTH = 40; // 太短的尾段併回上一段

const OPEN_BRACKETS = "（(「『";
const CLOSE_BRACKETS = "）)」』";
const SENTENCE_ENDS = "。！？";

// 自動補的換段：空白行內放一個零寬空格，畫面上看起來就是空行
const ZWSP = "​";
const INSERTED_BREAK = `\n${ZWSP}\n`;

// 依句末標點切句；括號／引號內的句號不算句末。切出的片段串接後與原文完全相同。
function splitSentences(block: string): string[] {
  const sentences: string[] = [];
  let depth = 0;
  let current = "";
  for (const ch of block) {
    current += ch;
    if (OPEN_BRACKETS.includes(ch)) {
      depth += 1;
    } else if (CLOSE_BRACKETS.includes(ch)) {
      depth = Math.max(0, depth - 1);
    } else if (depth === 0 && SENTENCE_ENDS.includes(ch)) {
      sentences.push(current);
      current = "";
    }
  }
  if (current) {
    sentences.push(current);
  }
  return sentences;
}

// 將句子累積成約 PARAGRAPH_TARGET_LENGTH 字的段落（不修剪空白，以便還原原文）
function groupSentences(sentences: string[]): string[] {
  const groups: string[] = [];
  let current = "";
  for (const sentence of sentences) {
    current += sentence;
    if (current.length >= PARAGRAPH_TARGET_LENGTH) {
      groups.push(current);
      current = "";
    }
  }
  if (current) {
    if (groups.length && current.trim().length < SHORT_TAIL_LENGTH) {
      groups[groups.length - 1] += current;
    } else {
      groups.push(current);
    }
  }
  return groups;
}

// 單行文字（不含換行）切成段落：【標題】前換段，過長的段落再依句號切
function splitLine(line: string): string[] {
  return line
    .split(/(?=【)/)
    .filter((part) => part.length > 0)
    .flatMap((part) =>
      part.trim().length > LONG_BLOCK_LENGTH
        ? groupSentences(splitSentences(part))
        : [part],
    );
}

function normalizeNewlines(text: string): string {
  return (text || "").replace(/\r\n?/g, "\n");
}

// 「展開」模態框用：回傳要逐段顯示的段落
export function splitAnswerParagraphs(answer: string): string[] {
  const text = normalizeNewlines(answer).trim();
  if (!text) return [];
  return text
    .split(/\n+/)
    .flatMap(splitLine)
    .map((para) => para.trim())
    .filter(Boolean);
}

// 編輯模態框用：原文換行保持不變，只在自動換段處插入標記換段
export function answerToEditText(answer: string): string {
  return normalizeNewlines(answer)
    .split(/(\n+)/)
    .map((part) =>
      part.startsWith("\n") ? part : splitLine(part).join(INSERTED_BREAK),
    )
    .join("");
}

// 送出前：移除標記換段（含其前後各一個換行），其餘換行原樣保留
export function editTextToAnswer(text: string): string {
  return normalizeNewlines(text).replace(/\n?​\n?/g, "");
}
