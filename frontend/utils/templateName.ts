/**
 * Utility for parsing plan template display names.
 *
 * Some template names follow the convention:
 *   "<MainTitle>【<BracketedTitle>】"
 * e.g. "地方型SBIR【在地產業補助】"
 *
 * The home page renders the bracketed portion on its own row beneath the main
 * title for clearer visual hierarchy. This utility centralizes the parsing
 * logic so it can be reused (e.g. plan-library, breadcrumbs) and so the data
 * source can later be swapped out (e.g. dedicated DB column) without touching
 * the render layer.
 */

export interface SplitTemplateName {
  /** Title with any trailing 【...】 segment removed. */
  mainTitle: string;
  /**
   * The text inside the trailing 【...】 segment, without the brackets
   * themselves. Empty string when the name has no trailing bracketed segment.
   */
  bracketedTitle: string;
}

// End-anchored: only split when the 【...】 segment is at the tail of the name.
// This avoids accidentally splitting names that legitimately use brackets
// in the middle, e.g. "中央型【副標】SBIR".
const TRAILING_BRACKET_PATTERN = /^(.*?)\s*【(.+?)】\s*$/;

/**
 * Split a plan template name into its main title and trailing bracketed title.
 *
 * Examples:
 *   splitTemplateName("地方型SBIR【在地產業補助】")
 *     → { mainTitle: "地方型SBIR", bracketedTitle: "在地產業補助" }
 *   splitTemplateName("IMDP（製造業創新）")
 *     → { mainTitle: "IMDP（製造業創新）", bracketedTitle: "" }
 *   splitTemplateName("中央型【副標】SBIR")
 *     → { mainTitle: "中央型【副標】SBIR", bracketedTitle: "" }
 *   splitTemplateName(null)
 *     → { mainTitle: "", bracketedTitle: "" }
 */
export function splitTemplateName(
  name: string | null | undefined,
): SplitTemplateName {
  const raw = (name ?? "").trim();
  if (!raw) {
    return { mainTitle: "", bracketedTitle: "" };
  }
  const match = raw.match(TRAILING_BRACKET_PATTERN);
  if (!match) {
    return { mainTitle: raw, bracketedTitle: "" };
  }
  return {
    mainTitle: match[1].trim(),
    bracketedTitle: match[2].trim(),
  };
}
