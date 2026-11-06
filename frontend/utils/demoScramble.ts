// Demo：把鎖定章節（例如 company）的文字換成亂碼，供預覽時遮蔽內容（註冊後才可完整檢視）。
// 與 HtmlRenderer.processText 使用相同的替換規則，只是改為對資料本身處理，
// 讓與 Word 相同版面的預覽（PlanDocumentPreview）也能遮蔽指定章節。

const SCRAMBLE_POOL =
  "的是我在有和人這中大們國個產實研發創製技計專新合資作程時理業主部地得法生分可行市產主經化學";

export function scrambleText(text: string): string {
  if (!text) return text;
  return text
    .split("")
    .map((char) => {
      if (/[一-龥]/.test(char)) {
        return SCRAMBLE_POOL[Math.floor(Math.random() * SCRAMBLE_POOL.length)];
      }
      if (/[a-zA-Z0-9]/.test(char)) {
        return Math.floor(Math.random() * 10).toString();
      }
      return char;
    })
    .join("");
}

// 只替換字串值，物件鍵（欄位名稱）保持不變，版面結構才不會改變
export function scrambleDeep<T>(value: T): T {
  if (typeof value === "string") {
    return scrambleText(value) as unknown as T;
  }
  if (Array.isArray(value)) {
    return value.map((item) => scrambleDeep(item)) as unknown as T;
  }
  if (value && typeof value === "object") {
    const result: Record<string, any> = {};
    for (const [key, item] of Object.entries(value as Record<string, any>)) {
      result[key] = scrambleDeep(item);
    }
    return result as T;
  }
  return value;
}

// 回傳新的 planData：lockedSectionIds 內的章節內容被換成亂碼，其餘章節不變
export function scramblePlanSections(
  planData: Record<string, any> | null | undefined,
  lockedSectionIds: string[] = [],
): Record<string, any> | null | undefined {
  if (!planData || !lockedSectionIds.length) return planData;
  const result: Record<string, any> = { ...planData };
  for (const sectionId of lockedSectionIds) {
    if (result[sectionId] !== undefined) {
      result[sectionId] = scrambleDeep(result[sectionId]);
    }
  }
  return result;
}
