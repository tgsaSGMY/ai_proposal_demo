export function useSensitiveMasking() {
  // 將輸入字詞正規化為可比較字串（去前後空白）。
  const normalizeTerm = (term: unknown): string => String(term || "").trim();

  // 合併多組字詞，忽略大小寫重複並過濾過短字詞。
  const mergeTerms = (...sources: unknown[][]): string[] => {
    const seen = new Set<string>();
    const merged: string[] = [];

    for (const source of sources) {
      for (const raw of source) {
        const term = normalizeTerm(raw);
        if (!term || term.length < 2) continue;

        const key = term.toLowerCase();
        if (seen.has(key)) continue;

        seen.add(key);
        merged.push(term);
      }
    }

    return merged;
  };

  // 以 JSON 方式深拷貝：適用純資料物件（不保留函式/Date/Map）。
  const deepClone = <T>(value: T): T => JSON.parse(JSON.stringify(value));

  // 將字串中的敏感詞替換為 OOO，長詞優先以降低部分重疊覆蓋問題。
  const replaceSensitiveTermsInString = (
    text: unknown,
    terms: string[],
  ): string => {
    if (!text || !terms.length) return String(text || "");

    const sortedTerms = [...terms]
      .map((term) => normalizeTerm(term))
      .filter(Boolean)
      .sort((a, b) => b.length - a.length);

    if (!sortedTerms.length) return String(text);

    const escapedTerms = sortedTerms.map((term) =>
      term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
    );
    const pattern = new RegExp(`(${escapedTerms.join("|")})`, "g");

    // 只替換 HTML 標籤之外的純文字，避免破壞結構
    return String(text)
      .split(/(<[^>]+>)/g)
      .map((chunk) => {
        if (!chunk || chunk.startsWith("<")) return chunk;
        return chunk.replace(pattern, "OOO");
      })
      .join("");
  };

  // 深度走訪物件/陣列，僅對字串與數字節點套用敏感詞遮罩。
  const maskObjectDeep = (value: unknown, terms: string[]): unknown => {
    if (Array.isArray(value)) {
      return value.map((item) => maskObjectDeep(item, terms));
    }

    if (value && typeof value === "object") {
      const next: Record<string, unknown> = {};
      Object.entries(value as Record<string, unknown>).forEach(([key, val]) => {
        next[key] = maskObjectDeep(val, terms);
      });
      return next;
    }

    if (typeof value === "string") {
      // 處理 JSON 字串：如果字串實際上是 JSON（例如陣列表格），則解析後遞迴處理，避免直接替換導致 JSON 格式損壞
      const trimmed = value.trim();
      if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || 
          (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
        try {
          const parsed = JSON.parse(trimmed);
          const maskedParsed = maskObjectDeep(parsed, terms);
          return JSON.stringify(maskedParsed);
        } catch (e) {
          // 若不是合法的 JSON 字串，則 fallback 繼續作為普通字串處理
        }
      }

      return replaceSensitiveTermsInString(value, terms);
    }

    // 處理純數字：允許遮罩數字（例如預算金額、數量等）
    if (typeof value === "number") {
      const strVal = String(value);
      const masked = replaceSensitiveTermsInString(strVal, terms);
      // 如果數字被替換了（包含了 OOO），則回傳遮罩後的字串，否則回傳原本的數字型態
      return masked !== strVal ? masked : value;
    }

    return value;
  };

  // 在 HTML 文字節點中標註敏感詞，避免破壞原始標籤結構。
  const highlightSensitiveTermsInHtml = (
    html: unknown,
    terms: string[],
  ): string => {
    if (!html || !terms?.length) return String(html || "");

    const sortedTerms = [...terms]
      .map((term) => normalizeTerm(term))
      .filter(Boolean)
      .sort((a, b) => b.length - a.length);

    if (!sortedTerms.length) return String(html);

    const escapedTerms = sortedTerms.map((term) =>
      term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
    );
    const pattern = new RegExp(`(${escapedTerms.join("|")})`, "g");

    // 只處理 HTML 標籤之外的純文字，避免重新 parse HTML 造成段落結構被修正或遺失。
    return String(html)
      .split(/(<[^>]+>)/g)
      .map((chunk) => {
        if (!chunk || chunk.startsWith("<")) return chunk;
        return chunk.replace(pattern, '<mark class="mask-highlight">$1</mark>');
      })
      .join("");
  };

  // 新增詞到「全部敏感詞」與「已選詞」兩份清單，並做去重。
  const addTermToLists = (
    term: unknown,
    sensitiveTerms: string[],
    selectedTerms: string[],
  ): { sensitiveTerms: string[]; selectedTerms: string[] } => {
    const normalized = normalizeTerm(term);
    if (!normalized) {
      return { sensitiveTerms, selectedTerms };
    }

    return {
      sensitiveTerms: mergeTerms(sensitiveTerms, [normalized]),
      selectedTerms: mergeTerms(selectedTerms, [normalized]),
    };
  };

  // 從兩份清單同步移除指定詞。
  const removeTermFromLists = (
    termToRemove: string,
    sensitiveTerms: string[],
    selectedTerms: string[],
  ): { sensitiveTerms: string[]; selectedTerms: string[] } => {
    return {
      sensitiveTerms: sensitiveTerms.filter((term) => term !== termToRemove),
      selectedTerms: selectedTerms.filter((term) => term !== termToRemove),
    };
  };

  // 切換詞彙勾選狀態：勾選則加入，取消則移除。
  const toggleSelectionInList = (
    term: string,
    checked: boolean,
    selectedTerms: string[],
  ): string[] => {
    if (checked) {
      return mergeTerms(selectedTerms, [term]);
    }
    return selectedTerms.filter((item) => item !== term);
  };

  // 對外暴露遮罩與清單操作工具。
  return {
    mergeTerms,
    deepClone,
    maskObjectDeep,
    highlightSensitiveTermsInHtml,
    addTermToLists,
    removeTermFromLists,
    toggleSelectionInList,
  };
}
