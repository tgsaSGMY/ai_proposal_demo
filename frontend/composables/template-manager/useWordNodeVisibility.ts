import type { WordDocumentNode } from "~/types/wordExport";

export function shouldShowTemplateInput(node: WordDocumentNode): boolean {
  return node.type === "customText";
}

export function shouldShowNodeLabel(node: WordDocumentNode): boolean {
  return !["paragraph", "table", "customTable", "list", "customText"].includes(
    node.type,
  );
}

export function shouldShowSectionSelectors(node: WordDocumentNode): boolean {
  return !["sectionTitle", "subHeading", "customText"].includes(node.type);
}
