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

    const sortedTerms = [...terms].sort((a, b) => b.length - a.length);
    let result = String(text);

    for (const term of sortedTerms) {
      if (!term) continue;
      result = result.split(term).join("OOO");
    }

    return result;
  };

  // 深度走訪物件/陣列，僅對字串節點套用敏感詞遮罩。
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
      return replaceSensitiveTermsInString(value, terms);
    }

    return value;
  };

  // 在 HTML 文字節點中標註敏感詞，避免破壞原始標籤結構。
  const highlightSensitiveTermsInHtml = (
    html: unknown,
    terms: string[],
  ): string => {
    if (!html || !terms?.length) return String(html || "");
    if (typeof window === "undefined" || typeof DOMParser === "undefined") {
      return String(html);
    }

    const sortedTerms = [...terms]
      .map((term) => normalizeTerm(term))
      .filter(Boolean)
      .sort((a, b) => b.length - a.length);

    if (!sortedTerms.length) return String(html);

    const parser = new DOMParser();
    const doc = parser.parseFromString(
      `<div id="hl-root">${String(html)}</div>`,
      "text/html",
    );
    const root = doc.getElementById("hl-root");
    if (!root) return String(html);

    const skipTags = new Set([
      "MARK",
      "STRONG",
      "B",
      "H1",
      "H2",
      "H3",
      "H4",
      "H5",
      "H6",
      "TH",
    ]);

    const walker = doc.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const textNodes: Node[] = [];
    let node = walker.nextNode();
    while (node) {
      textNodes.push(node);
      node = walker.nextNode();
    }

    for (const textNode of textNodes) {
      const parent = (textNode as ChildNode).parentElement;
      if (!parent || skipTags.has(parent.tagName)) continue;

      const text = textNode.nodeValue || "";
      if (!text.trim()) continue;

      const fragment = doc.createDocumentFragment();
      let cursor = 0;
      let changed = false;

      while (cursor < text.length) {
        let matchedTerm = "";
        let matchedIndex = -1;

        for (const term of sortedTerms) {
          const index = text.indexOf(term, cursor);
          if (index === -1) continue;
          if (matchedIndex === -1 || index < matchedIndex) {
            matchedIndex = index;
            matchedTerm = term;
          }
        }

        if (matchedIndex === -1) {
          fragment.appendChild(doc.createTextNode(text.slice(cursor)));
          break;
        }

        if (matchedIndex > cursor) {
          fragment.appendChild(
            doc.createTextNode(text.slice(cursor, matchedIndex)),
          );
        }

        const mark = doc.createElement("mark");
        mark.className = "mask-highlight";
        mark.textContent = matchedTerm;
        fragment.appendChild(mark);

        cursor = matchedIndex + matchedTerm.length;
        changed = true;
      }

      if (changed) {
        parent.replaceChild(fragment, textNode as ChildNode);
      }
    }

    return root.innerHTML;
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
