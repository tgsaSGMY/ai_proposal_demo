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
  | "customTable"
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

// 清單項渲染配置
export interface WordDocumentNodeListItemConfig {
  // 當清單項是對象時，使用子節點定義如何渲染
  useSubNodes?: boolean; // 是否使用子節點渲染對象
  itemTemplate?: string; // 模板語法，如 "{{title}}: {{description}}"
  displayField?: string; // 簡單模式：只顯示某個字段
}

// 表格固定布局單元格配置
export interface WordTableFixedLayoutCell {
  row: number;
  col: number;
  rowSpan?: number;
  colSpan?: number;
  dataPath?: string; // 數據路徑，如 "strength.items"
  label?: string; // 固定標籤（如 "Strength 優勢"）
  isHeader?: boolean; // 是否為標題單元格
}

// 表格固定布局配置
export interface WordTableFixedLayout {
  rows: number;
  cols: number;
  cells: WordTableFixedLayoutCell[];
}

export interface WordDocumentNodeTableConfig {
  title?: string;
  columns: WordTableColumn[];
  groupBy?: string;
  sortBy?: WordNodeSortConfig[];
  layout?: "auto" | "grid" | "fixed"; // 新增 fixed 布局模式
  // 固定布局配置
  fixedLayout?: WordTableFixedLayout;
  // 允許自定義列標題
  customHeaders?: boolean; // 是否啟用自定義標題
  // 倒置表格：列與欄互換（預設 false）
  transpose?: boolean;
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
  itemConfig?: WordDocumentNodeListItemConfig; // 新增：清單項配置
}

export type WordCustomTableCellContentType = "text" | "field";

export interface WordCustomTableCellContent {
  id: string;
  type: WordCustomTableCellContentType;
  text?: string;
  dataPath?: string;
}

export interface WordCustomTableCell {
  id: string;
  row: number;
  col: number;
  type: WordCustomTableCellContentType;
  text?: string;
  dataPath?: string;
  contents?: WordCustomTableCellContent[];
}

export interface WordCustomTableConfig {
  rows: number;
  cols: number;
  cells: WordCustomTableCell[];
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
  customTable?: WordCustomTableConfig;
  list?: WordDocumentNodeListConfig;
  style?: WordDocumentNodeStyleOverrides;
  level?: number;
  children?: WordDocumentNode[];
  paragraphNumbering?: boolean;
  paragraphNumberStyle?: WordListStyle;
  // 章節分組相關字段
  chapterMarker?: boolean; // 是否為手動添加的章節標記
  chapterTitle?: string; // 手動章節標記的標題
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
  section_versions?: Record<string, number>;
}
