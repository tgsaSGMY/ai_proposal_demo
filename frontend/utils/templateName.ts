/**
 * Utility for parsing plan template display names.
 *
 * Some template names follow the convention:
 *   "<MainTitle>【<BracketedTitle>】"
 * e.g. "中央型SBIR-Phase 1【先期研究】"
 *
 * The home page renders the bracketed portion on its own row beneath the main
 * title for clearer visual hierarchy. This utility centralizes the parsing
 * logic so it can be reused (e.g. plan-library, breadcrumbs) and so the data
 * source can later be swapped out (e.g. dedicated DB column) without touching
 * the render layer.
 *
 * IMPORTANT: The bottom-row treatment is intentionally restricted to a small
 * allow-list of templates (see BOTTOM_ROW_TITLE_PREFIXES below). Even if a
 * template name contains a trailing 【...】 segment, it will NOT be split
 * unless its name starts with one of the allow-listed prefixes. This keeps
 * the home-page UI predictable and avoids coupling layout to an implicit
 * naming convention.
 */

export interface SplitTemplateName {
  /** Title with any trailing 【...】 segment removed (allow-listed only). */
  mainTitle: string;
  /**
   * The text inside the trailing 【...】 segment, without the brackets
   * themselves. Empty string when the template is not allow-listed or when
   * the name has no trailing bracketed segment.
   */
  bracketedTitle: string;
}

/**
 * Templates whose names should be split into a main row + bracketed second
 * row on the home-page card. All other templates render their full name as
 * a single row, even if the name happens to contain 【...】.
 *
 * Match is by `startsWith` against the trimmed `template.name`. This is
 * resilient to the text inside 【...】 changing (e.g. 【先期研究】 today,
 * 【初創研發補助】 tomorrow) — only the prefix needs to stay stable.
 *
 * Strict ASCII hyphen — if any data source ever stores a full-width "－" or
 * em-dash "—", add the variant prefix(es) to this list.
 *
 * To enable the bottom-row treatment for a new template, add its prefix here.
 */
const BOTTOM_ROW_TITLE_PREFIXES = [
  "中央型SBIR-Phase 1",
  "中央型SBIR-Phase 2",
] as const;

// End-anchored: only split when the 【...】 segment is at the tail of the name.
// This avoids accidentally splitting names that legitimately use brackets
// in the middle, e.g. "中央型【副標】SBIR".
const TRAILING_BRACKET_PATTERN = /^(.*?)\s*【(.+?)】\s*$/;

/**
 * Split a plan template name into its main title and trailing bracketed title.
 *
 * The split only runs for allow-listed templates (see
 * BOTTOM_ROW_TITLE_PREFIXES). Non-allow-listed names are returned as-is in
 * `mainTitle` with an empty `bracketedTitle`.
 *
 * Examples (assuming the current allow-list):
 *   splitTemplateName("中央型SBIR-Phase 1【先期研究】")
 *     → { mainTitle: "中央型SBIR-Phase 1", bracketedTitle: "先期研究" }
 *   splitTemplateName("中央型SBIR-Phase 2【研究開發】")
 *     → { mainTitle: "中央型SBIR-Phase 2", bracketedTitle: "研究開發" }
 *   splitTemplateName("地方型SBIR【在地產業補助】")
 *     → { mainTitle: "地方型SBIR【在地產業補助】", bracketedTitle: "" }
 *       (not allow-listed — single-row rendering)
 *   splitTemplateName("IMDP（製造業創新）")
 *     → { mainTitle: "IMDP（製造業創新）", bracketedTitle: "" }
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

  // Gate: only allow-listed templates get the bottom-row split.
  const isAllowed = BOTTOM_ROW_TITLE_PREFIXES.some((prefix) =>
    raw.startsWith(prefix),
  );
  if (!isAllowed) {
    return { mainTitle: raw, bracketedTitle: "" };
  }

  const match = raw.match(TRAILING_BRACKET_PATTERN);
  if (!match) {
    // Allow-listed but no trailing 【...】 — render as single row.
    return { mainTitle: raw, bracketedTitle: "" };
  }
  return {
    mainTitle: match[1].trim(),
    bracketedTitle: match[2].trim(),
  };
}
