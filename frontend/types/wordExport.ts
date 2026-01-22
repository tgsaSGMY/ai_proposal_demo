export type WordSectionLayoutMode = "auto" | "table";

export interface WordTableColumn {
  key: string;
  label: string;
}

export type WordDocumentNodeType =
  | "sectionTitle"
  | "subHeading"
  | "paragraph"
  | "table"
  | "list"
  | "customText"
  | "imagePlaceholder";

export type WordNodeConditionOperator = "exists" | "equals" | "notEmpty";

export interface WordDocumentNodeCondition {
  path: string;
  operator: WordNodeConditionOperator;
  value?: string;
}

export interface WordNodeSortConfig {
  path: string;
  direction?: "asc" | "desc";
}

export interface WordDocumentNodeTableConfig {
  title?: string;
  columns: WordTableColumn[];
  groupBy?: string;
  sortBy?: WordNodeSortConfig[];
  layout?: "auto" | "grid";
}

export type WordListStyle =
  | "chineseComma"
  | "numberedDot"
  | "parenNumbered"
  | "bullet"
  | "chineseNumber"
  | "arabicNumber";

export interface WordDocumentNodeListConfig {
  numbering?: boolean;
  style?: WordListStyle;
  divider?: string;
}

export interface WordDocumentNodeStyleOverrides extends Partial<WordDocumentStyle> {
  alignment?: "left" | "center" | "right";
  highlightPattern?: string;
}

export interface WordDocumentNode {
  id: string;
  label?: string;
  type: WordDocumentNodeType;
  sectionId?: string;
  dataPath?: string;
  template?: string;
  condition?: WordDocumentNodeCondition;
  table?: WordDocumentNodeTableConfig;
  list?: WordDocumentNodeListConfig;
  style?: WordDocumentNodeStyleOverrides;
  level?: number;
  children?: WordDocumentNode[];
}

export interface WordDocumentStyle {
  headingFont?: string;
  headingSizePt?: number;
  headingBold?: boolean;
  subHeadingFont?: string;
  subHeadingSizePt?: number;
  subHeadingBold?: boolean;
  bodyFont?: string;
  bodySizePt?: number;
  bodyBold?: boolean;
}

export interface WordSectionLayout {
  sectionId: string;
  sectionName?: string;
  mode: WordSectionLayoutMode;
  dataPath?: string;
  tableTitle?: string;
  tableColumns?: WordTableColumn[];
}

export interface WordExportTemplateConfig {
  documentStyle: WordDocumentStyle;
  sectionLayouts: WordSectionLayout[];
  nodes?: WordDocumentNode[];
}

export interface WordExportConfigEntry {
  id: string;
  createdAt: string;
  createdBy?: string;
  config: WordExportTemplateConfig;
}
